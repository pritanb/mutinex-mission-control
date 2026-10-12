"""Audit event names. Every audit event is recorded under one of these names, so a mission's
history reads the same whichever code path wrote it."""

from enum import StrEnum


class Event(StrEnum):
    MISSION_CREATED = "mission.created"
    MISSION_SUBMITTED = "mission.submitted"
    MISSION_APPROVED = "mission.approved"
    MISSION_ACTIVATED = "mission.activated"
    MISSION_COMPLETED = "mission.completed"
    USER_PASSWORD_CHANGED = "user.password_changed"
    # M10 crew
    CREW_DETAILS_UPDATED = "crew.details_updated"
    CREW_UNAVAILABILITY_ADDED = "crew.unavailability_added"
    CREW_UNAVAILABILITY_REMOVED = "crew.unavailability_removed"
    CREW_SKILL_SET = "crew.skill_set"
    CREW_SKILL_REMOVED = "crew.skill_removed"
    # M9 admin
    ORG_REQUIRED_APPROVALS_CHANGED = "org.required_approvals_changed"
    USER_CREATED = "user.created"
    USER_ROLE_CHANGED = "user.role_changed"
    USER_DEACTIVATED = "user.deactivated"
    CREW_PROFILE_CREATED = "crew_profile.created"
    SKILL_CREATED = "skill.created"
    SKILL_UPDATED = "skill.updated"
    SKILL_DELETED = "skill.deleted"
    # M11 missions
    MISSION_UPDATED = "mission.updated"
    MISSION_TRANSFERRED = "mission.transferred"
    MISSION_RETURNED_TO_DRAFT = "mission.returned_to_draft"  # data names the change that caused it
    SLOT_ADDED = "slot.added"
    SLOT_UPDATED = "slot.updated"
    SLOT_REQUIREMENTS_CHANGED = "slot.requirements_changed"
    SLOT_REMOVED = "slot.removed"
