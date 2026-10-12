from mission_control.domain.events import Event


def test_event_names_are_the_stored_audit_strings():
    assert {e.name: e.value for e in Event} == {
        # Missions
        "MISSION_CREATED": "mission.created",
        "MISSION_UPDATED": "mission.updated",
        "MISSION_TRANSFERRED": "mission.transferred",
        "MISSION_RETURNED_TO_DRAFT": "mission.returned_to_draft",
        "MISSION_SUBMITTED": "mission.submitted",
        "MISSION_APPROVED": "mission.approved",
        "MISSION_REJECTED": "mission.rejected",
        "MISSION_ACTIVATED": "mission.activated",
        "MISSION_COMPLETED": "mission.completed",
        "MISSION_CANCELLED": "mission.cancelled",
        # Slots
        "SLOT_ADDED": "slot.added",
        "SLOT_UPDATED": "slot.updated",
        "SLOT_REQUIREMENTS_CHANGED": "slot.requirements_changed",
        "SLOT_REMOVED": "slot.removed",
        # Assignments
        "ASSIGNMENT_PROPOSED": "assignment.proposed",
        "ASSIGNMENT_ACCEPTED": "assignment.accepted",
        "ASSIGNMENT_DECLINED": "assignment.declined",
        "ASSIGNMENT_WITHDRAWN": "assignment.withdrawn",
        "ASSIGNMENT_REMOVED": "assignment.removed",
        "ASSIGNMENT_COMPLETED": "assignment.completed",
        "ASSIGNMENT_CANCELLED": "assignment.cancelled",
        # Crew
        "CREW_DETAILS_UPDATED": "crew.details_updated",
        "CREW_UNAVAILABILITY_ADDED": "crew.unavailability_added",
        "CREW_UNAVAILABILITY_REMOVED": "crew.unavailability_removed",
        "CREW_SKILL_SET": "crew.skill_set",
        "CREW_SKILL_REMOVED": "crew.skill_removed",
        # Organisation and users
        "ORG_REQUIRED_APPROVALS_CHANGED": "org.required_approvals_changed",
        "USER_CREATED": "user.created",
        "USER_ROLE_CHANGED": "user.role_changed",
        "USER_DEACTIVATED": "user.deactivated",
        "USER_PASSWORD_CHANGED": "user.password_changed",
        "CREW_PROFILE_CREATED": "crew_profile.created",
        # Skill catalogue
        "SKILL_CREATED": "skill.created",
        "SKILL_UPDATED": "skill.updated",
        "SKILL_DELETED": "skill.deleted",
    }
