from mission_control.domain.events import Event


def test_event_names_are_the_stored_audit_strings():
    assert {e.name: e.value for e in Event} == {
        "MISSION_CREATED": "mission.created",
        "MISSION_SUBMITTED": "mission.submitted",
        "MISSION_APPROVED": "mission.approved",
        "MISSION_ACTIVATED": "mission.activated",
        "MISSION_COMPLETED": "mission.completed",
        "USER_PASSWORD_CHANGED": "user.password_changed",
        # M10 crew
        "CREW_DETAILS_UPDATED": "crew.details_updated",
        "CREW_UNAVAILABILITY_ADDED": "crew.unavailability_added",
        "CREW_UNAVAILABILITY_REMOVED": "crew.unavailability_removed",
        "CREW_SKILL_SET": "crew.skill_set",
        "CREW_SKILL_REMOVED": "crew.skill_removed",
    }
