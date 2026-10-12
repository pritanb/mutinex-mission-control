"""Crew profiles: viewing people, their skills, availability and assignment history; editing
your own personal details and unavailability; and setting other people's skill levels.

Who sees what:
- Directors and Leads see every profile; crew see only their own. A profile the caller can't
  see is reported as not found.
- Unavailability dates are visible with the profile, but the reasons only to Directors and to
  the person themselves.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date

from mission_control.domain.dates import DateRange
from mission_control.domain.eligibility import invalidated_by_skill_change
from mission_control.domain.errors import InvalidInput, Problem, RuleViolation
from mission_control.domain.events import Event
from mission_control.domain.permissions import Action, Context, can
from mission_control.infra.repositories import Repos
from mission_control.infra.repositories.models import (
    AssignmentSummary,
    CrewProfile,
    Unavailability,
    User,
)
from mission_control.services.context import ServiceContext, found

MIN_LEVEL, MAX_LEVEL = 1, 5

_CREW_MEMBER = "Crew member"


@dataclass(frozen=True)
class SkillLevel:
    skill_id: int
    skill_name: str
    level: int


@dataclass(frozen=True)
class UnavailabilityView:
    """A period someone is unavailable. `reason` is None when the viewer may not see it."""

    id: int
    window: DateRange
    reason: str | None


@dataclass(frozen=True)
class CrewView:
    """A crew profile as the caller may see it."""

    crew_profile_id: int
    user_id: int
    name: str
    email: str
    active: bool
    bio: str | None
    skills: tuple[SkillLevel, ...]  # by skill name
    unavailability: tuple[UnavailabilityView, ...]  # by start date


# Viewing


def list_crew(ctx: ServiceContext) -> list[CrewView]:
    """Every profile the caller may see: all of them for Directors and Leads, only their own
    for crew."""
    with ctx.read() as repos:
        users = {u.id: u for u in repos.users.list()}
        skill_names = _skill_names(repos)
        return [
            _view(ctx, repos, profile, users[profile.user_id], skill_names)
            for profile in repos.crew.list()
            if can(ctx.actor, Action.VIEW_CREW, _about(profile))
        ]


def view_crew(ctx: ServiceContext, crew_profile_id: int) -> CrewView:
    with ctx.read() as repos:
        profile = _visible_profile(ctx, crew_profile_id, Action.VIEW_CREW)
        user = found(repos.users.get(profile.user_id), _CREW_MEMBER)
        return _view(ctx, repos, profile, user, _skill_names(repos))


def list_unavailability(ctx: ServiceContext, crew_profile_id: int) -> list[UnavailabilityView]:
    with ctx.read() as repos:
        profile = _visible_profile(ctx, crew_profile_id, Action.VIEW_CREW)
        return list(_unavailability(ctx, repos, profile))


def assignment_history(ctx: ServiceContext, crew_profile_id: int) -> list[AssignmentSummary]:
    """Every assignment the person has held, newest first, including missions they've left.
    Each is a summary: it doesn't give access to the mission itself."""
    with ctx.read() as repos:
        profile = _visible_profile(ctx, crew_profile_id, Action.VIEW_ASSIGNMENT_HISTORY)
        return repos.crew.history(profile.id)


# Personal details and unavailability: the person themselves only


def update_details(
    ctx: ServiceContext,
    crew_profile_id: int,
    *,
    display_name: str | None = None,
    bio: str | None = None,
) -> CrewProfile:
    """Change your display name and bio. A value left as None stays as it is; a blank bio
    clears it."""
    new_name = None if display_name is None else display_name.strip()
    if new_name == "":
        raise InvalidInput("Display name can't be blank")
    if display_name is None and bio is None:
        with ctx.read():  # nothing to change: still check access, but write nothing
            return _own_profile(ctx, crew_profile_id)
    with ctx.write() as repos:
        profile = _own_profile(ctx, crew_profile_id)
        name = profile.display_name if new_name is None else new_name
        new_bio = profile.bio if bio is None else (bio.strip() or None)
        repos.crew.update(profile.id, name, new_bio)
        ctx.audit(
            Event.CREW_DETAILS_UPDATED,
            crew_profile_id=profile.id,
            data={"crew_name": name, "previous_name": profile.display_name},
        )
        return found(repos.crew.get(profile.id), _CREW_MEMBER)


def add_unavailability(
    ctx: ServiceContext, crew_profile_id: int, start: date, end: date, reason: str
) -> Unavailability:
    """Record a period you're unavailable. Past dates are allowed. Refused if it overlaps one
    of your accepted assignments on a mission that isn't finished."""
    window = DateRange(start, end)
    reason = reason.strip()
    if not reason:
        raise InvalidInput("Unavailability needs a reason")
    with ctx.write() as repos:
        profile = _own_profile(ctx, crew_profile_id)
        clashes = [
            _overlap(profile, c.mission_id, c.mission_name, c.window, window)
            for c in repos.facts.commitments(profile.id)
            if c.window.overlaps(window)
        ]
        _refuse(
            clashes,
            "overlap",
            f"{profile.display_name} has accepted assignments overlapping those dates",
        )
        added = repos.crew.add_unavailability(profile.id, window, reason)
        ctx.audit(
            Event.CREW_UNAVAILABILITY_ADDED,
            crew_profile_id=profile.id,
            data=_period(profile, window),  # the reason stays private: not in the audit log
        )
        return added


def remove_unavailability(
    ctx: ServiceContext, crew_profile_id: int, unavailability_id: int
) -> None:
    with ctx.write() as repos:
        profile = _own_profile(ctx, crew_profile_id)
        entry = found(
            next(
                (u for u in repos.crew.unavailability(profile.id) if u.id == unavailability_id),
                None,
            ),
            "Unavailability",
        )
        repos.crew.remove_unavailability(profile.id, entry.id)
        ctx.audit(
            Event.CREW_UNAVAILABILITY_REMOVED,
            crew_profile_id=profile.id,
            data=_period(profile, entry.window),
        )


# Skill levels: Leads and Directors, never on themselves


def set_skill_level(
    ctx: ServiceContext, crew_profile_id: int, skill_id: int, level: int
) -> SkillLevel:
    """Add or change someone's level in one of the organisation's skills. Refused if it would
    leave them short of a requirement on an Active mission they're on."""
    if not MIN_LEVEL <= level <= MAX_LEVEL:
        raise InvalidInput(f"Skill level must be between {MIN_LEVEL} and {MAX_LEVEL}")
    with ctx.write() as repos:
        profile, skill_name, previous = _skill_target(ctx, repos, crew_profile_id, skill_id)
        _refuse_if_active_assignment_breaks(repos, profile, skill_id, skill_name, level)
        repos.crew.set_skill(profile.id, skill_id, level, updated_by=ctx.actor.user_id)
        ctx.audit(
            Event.CREW_SKILL_SET,
            crew_profile_id=profile.id,
            data={
                "crew_name": profile.display_name,
                "skill_name": skill_name,
                "level": level,
                "previous_level": previous,
            },
        )
        return SkillLevel(skill_id, skill_name, level)


def remove_skill_level(ctx: ServiceContext, crew_profile_id: int, skill_id: int) -> None:
    with ctx.write() as repos:
        profile, skill_name, previous = _skill_target(ctx, repos, crew_profile_id, skill_id)
        found(previous, "Skill level")
        _refuse_if_active_assignment_breaks(repos, profile, skill_id, skill_name, None)
        repos.crew.remove_skill(profile.id, skill_id)
        ctx.audit(
            Event.CREW_SKILL_REMOVED,
            crew_profile_id=profile.id,
            data={
                "crew_name": profile.display_name,
                "skill_name": skill_name,
                "previous_level": previous,
            },
        )


# Helpers


def _about(profile: CrewProfile) -> Context:
    """Permission context for a profile: the person is its user, not the profile id."""
    return Context(target_user_id=profile.user_id)


def _visible_profile(ctx: ServiceContext, crew_profile_id: int, action: Action) -> CrewProfile:
    """The profile, or NotFound if it's missing, another organisation's, or hidden from the
    caller."""
    profile = found(ctx.repos.crew.get(crew_profile_id), _CREW_MEMBER)
    ctx.authorize_view(action, _about(profile), _CREW_MEMBER)
    return profile


def _own_profile(ctx: ServiceContext, crew_profile_id: int) -> CrewProfile:
    """The caller's own profile. Someone else's they can see is Forbidden."""
    profile = _visible_profile(ctx, crew_profile_id, Action.VIEW_CREW)
    ctx.authorize(Action.EDIT_OWN_PROFILE, _about(profile))
    return profile


def _skill_target(
    ctx: ServiceContext, repos: Repos, crew_profile_id: int, skill_id: int
) -> tuple[CrewProfile, str, int | None]:
    """The profile whose level is changing, the skill's name, and the current level."""
    profile = _visible_profile(ctx, crew_profile_id, Action.VIEW_CREW)
    ctx.authorize(Action.SET_SKILL_LEVEL, _about(profile))
    skill = found(repos.skills.get(skill_id), "Skill")
    return profile, skill.name, repos.crew.skills(profile.id).get(skill_id)


def _refuse_if_active_assignment_breaks(
    repos: Repos, profile: CrewProfile, skill_id: int, skill_name: str, level: int | None
) -> None:
    broken = invalidated_by_skill_change(
        profile.display_name, skill_id, level, repos.facts.active_assignments(profile.id)
    )
    _refuse(
        broken,
        "invalidates_active_assignment",
        f"Changing {profile.display_name}'s {skill_name} level would break their assignments "
        f"on active missions",
    )


def _refuse(problems: Sequence[Problem], code: str, several: str) -> None:
    """Raise a RuleViolation if there are problems: a single one gives its own code and message;
    several share `code` and the summary `several`."""
    if len(problems) == 1:
        raise RuleViolation.of(problems[0])
    if problems:
        raise RuleViolation(several, problems, code=code)


def _overlap(
    profile: CrewProfile, mission_id: int, mission_name: str, busy: DateRange, wanted: DateRange
) -> Problem:
    shared = DateRange(max(busy.start, wanted.start), min(busy.end, wanted.end))
    return Problem(
        "overlap",
        f"{profile.display_name} has an accepted assignment on {mission_name} overlapping "
        f"{shared.start.isoformat()} to {shared.end.isoformat()}",
        {"crew_profile_id": profile.id, "mission_id": mission_id, "mission_name": mission_name},
    )


def _period(profile: CrewProfile, window: DateRange) -> dict[str, str]:
    return {
        "crew_name": profile.display_name,
        "start_date": window.start.isoformat(),
        "end_date": window.end.isoformat(),
    }


def _skill_names(repos: Repos) -> dict[int, str]:
    return {s.id: s.name for s in repos.skills.list()}


def _view(
    ctx: ServiceContext,
    repos: Repos,
    profile: CrewProfile,
    user: User,
    skill_names: Mapping[int, str],
) -> CrewView:
    skills = sorted(
        (
            SkillLevel(skill_id, skill_names[skill_id], level)
            for skill_id, level in repos.crew.skills(profile.id).items()
        ),
        key=lambda s: (s.skill_name.casefold(), s.skill_id),
    )
    return CrewView(
        crew_profile_id=profile.id,
        user_id=profile.user_id,
        name=profile.display_name,
        email=user.email,
        active=user.is_active,
        bio=profile.bio,
        skills=tuple(skills),
        unavailability=_unavailability(ctx, repos, profile),
    )


def _unavailability(
    ctx: ServiceContext, repos: Repos, profile: CrewProfile
) -> tuple[UnavailabilityView, ...]:
    """Dates for anyone who can see the profile; reasons only for Directors and the person."""
    show_reason = can(ctx.actor, Action.VIEW_UNAVAILABILITY_REASON, _about(profile))
    return tuple(
        UnavailabilityView(u.id, u.window, u.reason if show_reason else None)
        for u in repos.crew.unavailability(profile.id)
    )
