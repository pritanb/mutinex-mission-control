"""Who may do what. `authorize` is the single entry point; it raises Forbidden with a code.

Each action combines a role check with, where needed, a relationship check: owner of the
mission, the person themselves, the mission's creator, or someone on its roster.
"""

from dataclasses import dataclass, field
from enum import StrEnum

from mission_control.domain.approvals import Approver, approver_problems
from mission_control.domain.enums import Role
from mission_control.domain.errors import Forbidden


@dataclass(frozen=True)
class Actor:
    user_id: int
    org_id: int
    role: Role
    crew_profile_id: int | None


@dataclass(frozen=True)
class Context:
    """Facts about the target that the relationship rules need. Unused fields stay None."""

    owner_id: int | None = None  # the mission's owning Lead
    created_by_id: int | None = None  # who created the mission
    target_user_id: int | None = None  # whose profile, skills or assignment this is
    rostered_user_ids: frozenset[int] = field(default_factory=frozenset)


class Action(StrEnum):
    MANAGE_ORG = "manage_org"  # settings, users, roles, initial passwords, crew profiles
    MANAGE_SKILLS = "manage_skills"
    LIST_SKILLS = "list_skills"
    CHANGE_OWN_PASSWORD = "change_own_password"
    VIEW_CREW = "view_crew"
    VIEW_ASSIGNMENT_HISTORY = "view_assignment_history"
    VIEW_UNAVAILABILITY_REASON = "view_unavailability_reason"
    EDIT_OWN_PROFILE = "edit_own_profile"  # personal details and unavailability
    SET_SKILL_LEVEL = "set_skill_level"
    VIEW_MISSION = "view_mission"  # includes its history
    CREATE_MISSION = "create_mission"
    EDIT_MISSION = "edit_mission"
    PROPOSE_CREW = "propose_crew"
    REMOVE_CREW = "remove_crew"
    APPLY_MATCH = "apply_match"
    SUBMIT = "submit"
    PREVIEW_MATCH = "preview_match"
    COMPLETE = "complete"
    CANCEL = "cancel"
    TRANSFER_OWNERSHIP = "transfer_ownership"
    APPROVE = "approve"
    REJECT = "reject"
    RESPOND_TO_ASSIGNMENT = "respond_to_assignment"  # accept, decline, withdraw


D, L, C = Role.DIRECTOR, Role.LEAD, Role.CREW
ALL = frozenset(Role)

# Which roles may attempt each action at all. Relationship rules below narrow this further.
ROLES: dict[Action, frozenset[Role]] = {
    Action.MANAGE_ORG: frozenset({D}),
    Action.MANAGE_SKILLS: frozenset({D}),
    Action.LIST_SKILLS: frozenset({D, L}),
    Action.CHANGE_OWN_PASSWORD: ALL,
    Action.VIEW_CREW: ALL,
    Action.VIEW_ASSIGNMENT_HISTORY: ALL,
    Action.VIEW_UNAVAILABILITY_REASON: ALL,
    Action.EDIT_OWN_PROFILE: ALL,
    Action.SET_SKILL_LEVEL: frozenset({D, L}),
    Action.VIEW_MISSION: ALL,
    Action.CREATE_MISSION: frozenset({D, L}),
    Action.EDIT_MISSION: frozenset({L}),
    Action.PROPOSE_CREW: frozenset({L}),
    Action.REMOVE_CREW: frozenset({L}),
    Action.APPLY_MATCH: frozenset({L}),
    Action.SUBMIT: frozenset({L}),
    Action.PREVIEW_MATCH: frozenset({D, L}),
    Action.COMPLETE: frozenset({D, L}),
    Action.CANCEL: frozenset({D, L}),
    Action.TRANSFER_OWNERSHIP: frozenset({D}),
    Action.APPROVE: frozenset({D}),
    Action.REJECT: frozenset({D}),
    Action.RESPOND_TO_ASSIGNMENT: ALL,
}

_OWNER_ONLY = {
    Action.EDIT_MISSION,
    Action.PROPOSE_CREW,
    Action.REMOVE_CREW,
    Action.APPLY_MATCH,
    Action.SUBMIT,
}
_OWNER_OR_DIRECTOR = {Action.PREVIEW_MATCH, Action.COMPLETE, Action.CANCEL}
# Crew may only see their own record; Leads and Directors may see anyone's.
_CREW_SELF_ONLY = {Action.VIEW_CREW, Action.VIEW_ASSIGNMENT_HISTORY}


# Messages. Phrases are written out so every refusal reads as a natural sentence.

_ROLE_PLURAL = {D: "Directors", L: "Leads", C: "Crew"}

# Completes "<Role plural> can't ...".
ROLE_PHRASE: dict[Action, str] = {
    Action.MANAGE_ORG: "manage the organisation",
    Action.MANAGE_SKILLS: "manage the skill catalogue",
    Action.LIST_SKILLS: "view the skill catalogue",
    Action.CHANGE_OWN_PASSWORD: "change their password",
    Action.VIEW_CREW: "view crew profiles",
    Action.VIEW_ASSIGNMENT_HISTORY: "view assignment history",
    Action.VIEW_UNAVAILABILITY_REASON: "see unavailability reasons",
    Action.EDIT_OWN_PROFILE: "edit profiles",
    Action.SET_SKILL_LEVEL: "change skill levels",
    Action.VIEW_MISSION: "view missions",
    Action.CREATE_MISSION: "create missions",
    Action.EDIT_MISSION: "edit missions",
    Action.PROPOSE_CREW: "propose crew",
    Action.REMOVE_CREW: "remove crew",
    Action.APPLY_MATCH: "apply matcher suggestions",
    Action.SUBMIT: "submit missions",
    Action.PREVIEW_MATCH: "preview matcher suggestions",
    Action.COMPLETE: "complete missions",
    Action.CANCEL: "cancel missions",
    Action.TRANSFER_OWNERSHIP: "transfer mission ownership",
    Action.APPROVE: "approve missions",
    Action.REJECT: "reject missions",
    Action.RESPOND_TO_ASSIGNMENT: "respond to assignments",
}

# Completes "Only the mission's owner can ..." / "Only the owner or a Director can ...".
_MISSION_PHRASE = {
    Action.EDIT_MISSION: "edit this mission",
    Action.PROPOSE_CREW: "propose crew for this mission",
    Action.REMOVE_CREW: "remove crew from this mission",
    Action.APPLY_MATCH: "apply matcher suggestions to this mission",
    Action.SUBMIT: "submit this mission",
    Action.PREVIEW_MATCH: "preview matching for this mission",
    Action.COMPLETE: "complete this mission",
    Action.CANCEL: "cancel this mission",
}

_SELF_ONLY_MESSAGE = {
    Action.VIEW_CREW: "Crew can only view their own profile",
    Action.VIEW_ASSIGNMENT_HISTORY: "Crew can only view their own assignment history",
    Action.EDIT_OWN_PROFILE: "You can only edit your own profile and availability",
    Action.RESPOND_TO_ASSIGNMENT: "You can only respond to your own assignments",
}


NO_CONTEXT = Context()


def authorize(actor: Actor, action: Action, ctx: Context = NO_CONTEXT) -> None:
    if actor.role not in ROLES[action]:
        raise Forbidden("role_forbidden", f"{_ROLE_PLURAL[actor.role]} can't {ROLE_PHRASE[action]}")

    is_self = ctx.target_user_id == actor.user_id
    is_owner = ctx.owner_id == actor.user_id

    if action in _OWNER_ONLY and not is_owner:
        raise Forbidden("not_owner", f"Only the mission's owner can {_MISSION_PHRASE[action]}")

    if action in _OWNER_OR_DIRECTOR and actor.role != D and not is_owner:
        raise Forbidden("not_owner", f"Only the owner or a Director can {_MISSION_PHRASE[action]}")

    if action == Action.CREATE_MISSION and actor.role == L and not is_owner:
        raise Forbidden("not_owner", "Leads can only create missions they own")

    if action in _CREW_SELF_ONLY and actor.role == C and not is_self:
        raise Forbidden("role_forbidden", _SELF_ONLY_MESSAGE[action])

    if action == Action.VIEW_UNAVAILABILITY_REASON and actor.role != D and not is_self:
        raise Forbidden(
            "role_forbidden", "Only Directors can see other people's unavailability reasons"
        )

    if (
        action == Action.VIEW_MISSION
        and actor.role == C
        and actor.user_id not in (ctx.rostered_user_ids)
    ):
        raise Forbidden("role_forbidden", "Crew can only view missions they're on")

    if action in (Action.EDIT_OWN_PROFILE, Action.RESPOND_TO_ASSIGNMENT) and not is_self:
        raise Forbidden("not_owner", _SELF_ONLY_MESSAGE[action])

    if action == Action.SET_SKILL_LEVEL and is_self:
        raise Forbidden("self_skill_edit", "You can't change your own skill levels")

    if action in (Action.APPROVE, Action.REJECT):
        # Creator and roster rules are shared with the approval module. "Already decided" is a
        # state conflict, not a permission, so it's checked by the service, not here.
        problems = approver_problems(
            Approver(actor.user_id, is_director=True, active=True),
            created_by_id=ctx.created_by_id,
            rostered_user_ids=ctx.rostered_user_ids,
            decided_this_round=set(),
        )
        if problems:
            raise Forbidden(problems[0].code, problems[0].message)


def can(actor: Actor, action: Action, ctx: Context = NO_CONTEXT) -> bool:
    try:
        authorize(actor, action, ctx)
    except Forbidden:
        return False
    return True
