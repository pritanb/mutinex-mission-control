from enum import StrEnum


class MissionStatus(StrEnum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class AssignmentStatus(StrEnum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    WITHDRAWN = "withdrawn"
    REMOVED = "removed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Role(StrEnum):
    DIRECTOR = "director"
    LEAD = "lead"
    CREW = "crew"


class Action(StrEnum):
    """Everything a user can attempt. The lifecycle and permission modules share this one enum,
    so a mission or assignment action means the same member everywhere."""

    # Mission transitions
    SUBMIT = "submit"
    APPROVE = "approve"
    REJECT = "reject"
    TRANSFER = "transfer"  # hand the mission to another Lead
    COMPLETE = "complete"
    CANCEL = "cancel"
    EDIT_MISSION = "edit_mission"  # any change to dates, slots or requirements
    # Assignment actions
    PROPOSE_CREW = "propose_crew"
    REMOVE_CREW = "remove_crew"
    ACCEPT = "accept"
    DECLINE = "decline"
    WITHDRAW = "withdraw"
    # Administration, profiles and viewing
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
    APPLY_MATCH = "apply_match"
    PREVIEW_MATCH = "preview_match"
