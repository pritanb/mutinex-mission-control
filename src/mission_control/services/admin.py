"""Director administration: organisation settings, users and roles, crew profiles and the skill
catalogue.

Each use case authorizes first, then loads, checks, writes and audits inside one write
transaction, so the checks see the same data the write changes. Audit `data` keeps the names
that applied at the time.
"""

from enum import Enum

from mission_control.domain.enums import Action, Role
from mission_control.domain.errors import InvalidInput, Problem, RuleViolation
from mission_control.domain.events import Event
from mission_control.domain.passwords import validate_password
from mission_control.domain.wording import join_names
from mission_control.infra import security
from mission_control.infra.repositories import Repos
from mission_control.infra.repositories.models import (
    CrewProfile,
    Mission,
    Organisation,
    Skill,
    User,
)
from mission_control.services.context import ServiceContext, check, found
from mission_control.services.inputs import invalid, refuse_input


class _Keep(Enum):
    KEEP = "keep"


KEEP = _Keep.KEEP  # update_skill: leave the category as it is


# --- Organisation settings ----------------------------------------------------------------


def view_organisation(ctx: ServiceContext) -> Organisation:
    ctx.authorize(Action.MANAGE_ORG)
    return ctx.repos.organisation.get()


def set_required_approvals(ctx: ServiceContext, n: int) -> Organisation:
    """Only missions submitted from now on use the new number: a submitted mission keeps the
    number it was submitted with."""
    ctx.authorize(Action.MANAGE_ORG)
    if n < 1:
        raise InvalidInput("At least one approval must be required")
    with ctx.write() as repos:
        current = repos.organisation.get()
        if current.required_approvals == n:
            return current
        repos.organisation.set_required_approvals(n)
        ctx.audit(
            Event.ORG_REQUIRED_APPROVALS_CHANGED,
            data={"changes": {"required_approvals": [current.required_approvals, n]}},
        )
        return repos.organisation.get()


# --- Users --------------------------------------------------------------------------------


def list_users(ctx: ServiceContext) -> list[User]:
    ctx.authorize(Action.MANAGE_ORG)
    return ctx.repos.users.list()


def view_user(ctx: ServiceContext, user_id: int) -> User:
    ctx.authorize(Action.MANAGE_ORG)
    return found(ctx.repos.users.get(user_id), "User")


def create_user(ctx: ServiceContext, email: str, name: str, role: Role, password: str) -> User:
    """A Director sets the initial password. A new Crew Member gets a crew profile straight
    away; Leads and Directors get one only on request."""
    ctx.authorize(Action.MANAGE_ORG)
    email, name = email.strip(), name.strip()
    refuse_input(_blank(email, "email address") + _blank(name, "name"))
    validate_password(password)
    password_hash = security.hash_password(password)  # slow, so before the write lock
    with ctx.write() as repos:
        # Emails are unique across every organisation, because login is by email alone.
        if security.find_login(ctx.conn, email) is not None:
            raise RuleViolation.of(
                Problem(
                    "already_exists",
                    f"The email address {email} is already in use",
                    {"email": email},
                )
            )
        user = repos.users.create(email, name, role, password_hash)
        ctx.audit(
            Event.USER_CREATED,
            data={"user_id": user.id, "user_name": user.name, "email": user.email, "role": role},
        )
        if role == Role.CREW:
            _give_crew_profile(ctx, repos, user)
    return user


def create_crew_profile(
    ctx: ServiceContext, user_id: int, display_name: str | None = None
) -> CrewProfile:
    """Give a Lead or Director a crew profile so they can take part in missions. The display
    name defaults to their first name. Profiles are never deleted."""
    ctx.authorize(Action.MANAGE_ORG)
    with ctx.write() as repos:
        user = found(repos.users.get(user_id), "User")
        if display_name is not None:
            display_name = _required(display_name, "display name")
        existing = repos.crew.by_user(user.id)
        if existing is not None:
            raise RuleViolation.of(
                Problem(
                    "already_exists",
                    f"{user.name} already has a crew profile",
                    {"user_id": user.id, "crew_profile_id": existing.id},
                )
            )
        return _give_crew_profile(ctx, repos, user, display_name)


def change_role(ctx: ServiceContext, user_id: int, role: Role) -> User:
    """A crew profile survives any role change, and becoming a Crew Member gives one to anyone
    who lacks it. A Lead who owns unfinished missions keeps the role until they're reassigned,
    and the organisation always keeps an active Director."""
    ctx.authorize(Action.MANAGE_ORG)
    with ctx.write() as repos:
        user = found(repos.users.get(user_id), "User")
        if user.role == role:
            return user
        problems: list[Problem] = []
        if user.role == Role.LEAD:
            problems += _owns_open_missions(repos, user)
        if user.role == Role.DIRECTOR:
            problems += _last_director(repos, user)
        check(problems, f"{user.name}'s role can't be changed")

        repos.users.set_role(user.id, role)
        ctx.audit(
            Event.USER_ROLE_CHANGED,
            data={
                "user_id": user.id,
                "user_name": user.name,
                "changes": {"role": [user.role, role]},
            },
        )
        if role == Role.CREW and repos.crew.by_user(user.id) is None:
            _give_crew_profile(ctx, repos, user)
        return found(repos.users.get(user.id), "User")


def deactivate_user(ctx: ServiceContext, user_id: int) -> User:
    """Deactivated users keep their history but can't sign in, and every session they have
    ends at once. Refused while they hold open assignments, own unfinished missions, or are the
    last active Director; every reason is listed together."""
    ctx.authorize(Action.MANAGE_ORG)
    with ctx.write() as repos:
        user = found(repos.users.get(user_id), "User")
        if not user.is_active:
            return user
        profile = repos.crew.by_user(user.id)
        problems: list[Problem] = []
        if profile is not None:
            problems += _has_open_assignments(repos, user, profile)
        problems += _owns_open_missions(repos, user)
        if user.role == Role.DIRECTOR:
            problems += _last_director(repos, user)
        check(problems, f"{user.name} can't be deactivated")

        repos.users.set_active(user.id, False)
        security.revoke_user_tokens(ctx.conn, user.id, ctx.now)
        ctx.audit(
            Event.USER_DEACTIVATED,
            crew_profile_id=profile.id if profile else None,
            data={"user_id": user.id, "user_name": user.name},
        )
        return found(repos.users.get(user.id), "User")


def _give_crew_profile(
    ctx: ServiceContext, repos: Repos, user: User, display_name: str | None = None
) -> CrewProfile:
    profile = repos.crew.create(user.id, display_name or user.name.split()[0])
    ctx.audit(
        Event.CREW_PROFILE_CREATED,
        crew_profile_id=profile.id,
        data={"user_id": user.id, "user_name": user.name, "display_name": profile.display_name},
    )
    return profile


def _has_open_assignments(repos: Repos, user: User, profile: CrewProfile) -> list[Problem]:
    mission_ids = {a.mission_id for a in repos.crew.open_assignments(profile.id)}
    missions = _by_date([found(repos.missions.get(i), "Mission") for i in mission_ids])
    if not missions:
        return []
    on = (
        f"an open assignment on {missions[0].name}"
        if len(missions) == 1
        else f"open assignments on {join_names(m.name for m in missions)}"
    )
    return [
        Problem(
            "has_open_assignments",
            f"{user.name} has {on}; they must withdraw or be removed first",
            {"user_id": user.id, "mission_ids": [m.id for m in missions]},
        )
    ]


def _owns_open_missions(repos: Repos, user: User) -> list[Problem]:
    missions = repos.missions.non_final_owned_by(user.id)
    if not missions:
        return []
    them = "it" if len(missions) == 1 else "them"
    return [
        Problem(
            "owns_open_missions",
            f"{user.name} still owns {join_names(m.name for m in missions)};"
            f" reassign {them} to another Lead first",
            {"user_id": user.id, "mission_ids": [m.id for m in missions]},
        )
    ]


def _last_director(repos: Repos, user: User) -> list[Problem]:
    if not user.is_active or repos.users.count_active_directors() > 1:
        return []
    return [
        Problem(
            "last_director",
            f"{user.name} is the only active Director, and the organisation must always have"
            " one; make someone else a Director first",
            {"user_id": user.id},
        )
    ]


# --- Skill catalogue ----------------------------------------------------------------------


def list_skills(ctx: ServiceContext) -> list[Skill]:
    ctx.authorize(Action.LIST_SKILLS)
    return ctx.repos.skills.list()


def add_skill(ctx: ServiceContext, name: str, category: str | None = None) -> Skill:
    """Names are unique within the organisation, ignoring case."""
    ctx.authorize(Action.MANAGE_SKILLS)
    name = _required(name, "skill name")
    category = _optional(category)
    with ctx.write() as repos:
        existing = repos.skills.by_name(name)
        if existing is not None:
            raise _name_taken(existing)
        skill = repos.skills.create(name, category)
        ctx.audit(
            Event.SKILL_CREATED,
            data={"skill_id": skill.id, "skill_name": skill.name, "category": skill.category},
        )
        return skill


def update_skill(
    ctx: ServiceContext,
    skill_id: int,
    *,
    name: str | None = None,
    category: str | None | _Keep = KEEP,
) -> Skill:
    """Rename or recategorise. The skill keeps its id, so crew levels and slot requirements
    follow it. A name left out stays as it is; so does the category unless one is given (None
    clears it)."""
    ctx.authorize(Action.MANAGE_SKILLS)
    with ctx.write() as repos:
        skill = found(repos.skills.get(skill_id), "Skill")
        to_name = _required(name, "skill name") if name is not None else skill.name
        to_category = skill.category if isinstance(category, _Keep) else _optional(category)
        if (to_name, to_category) == (skill.name, skill.category):
            return skill
        clash = repos.skills.by_name(to_name)
        if clash is not None and clash.id != skill.id:
            raise _name_taken(clash)
        changes: dict[str, list[str | None]] = {}
        if to_name != skill.name:
            changes["name"] = [skill.name, to_name]
        if to_category != skill.category:
            changes["category"] = [skill.category, to_category]
        repos.skills.update(skill.id, to_name, to_category)
        ctx.audit(
            Event.SKILL_UPDATED,
            data={"skill_id": skill.id, "skill_name": to_name, "changes": changes},
        )
        return found(repos.skills.get(skill.id), "Skill")


def delete_skill(ctx: ServiceContext, skill_id: int) -> None:
    """Only a skill that no crew member has and no slot requires can be deleted."""
    ctx.authorize(Action.MANAGE_SKILLS)
    with ctx.write() as repos:
        skill = found(repos.skills.get(skill_id), "Skill")
        holders = repos.skills.holders(skill.id)
        slots = repos.skills.required_by(skill.id)
        if holders or slots:
            reasons = []
            if holders:
                has = "has" if len(holders) == 1 else "have"
                reasons.append(f"{join_names(h.name for h in holders)} {has} it")
            if slots:
                requires = "requires" if len(slots) == 1 else "require"
                uses = join_names(f"{s.mission_name} ({s.slot_name})" for s in slots)
                reasons.append(f"{uses} {requires} it")
            raise RuleViolation.of(
                Problem(
                    "skill_in_use",
                    f"{skill.name} can't be deleted because {' and '.join(reasons)}",
                    {
                        "skill_id": skill.id,
                        "crew_profile_ids": [h.crew_profile_id for h in holders],
                        "mission_ids": list(dict.fromkeys(s.mission_id for s in slots)),
                    },
                )
            )
        repos.skills.delete(skill.id)
        ctx.audit(Event.SKILL_DELETED, data={"skill_id": skill.id, "skill_name": skill.name})


def _name_taken(existing: Skill) -> RuleViolation:
    return RuleViolation.of(
        Problem(
            "already_exists",
            f"The catalogue already has a skill called {existing.name}",
            {"skill_id": existing.id},
        )
    )


# --- Helpers ------------------------------------------------------------------------------


def _required(value: str, what: str) -> str:
    stripped = value.strip()
    refuse_input(_blank(stripped, what))
    return stripped


def _blank(value: str, what: str) -> list[Problem]:
    return [] if value.strip() else [invalid(f"The {what} can't be blank")]


def _optional(value: str | None) -> str | None:
    return (value.strip() or None) if value is not None else None


def _by_date(missions: list[Mission]) -> list[Mission]:
    return sorted(missions, key=lambda m: (m.window.start, m.id))
