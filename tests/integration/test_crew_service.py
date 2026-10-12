"""M10: the crew service. Viewing profiles and history, personal details, unavailability and
skill levels (PRD P2–P6, §5.7, V2, AC-16, AC-23, AC-24, AC-27–AC-29).

Seed ids (PRD §9): a crew profile's id equals its user's id. Ruth 1 · Marco 2 · Lee 4 · Ana 6 ·
Ben 7 · Chen 8 · Fay 11 · Gus 12 · Hana 13 · Sam 14 (Helix) · Kai 16 (Helix).
Skills: Piloting 1 · Leadership 2 · Systems Engineering 3 · EVA 4 · Geology 5 · Helix Piloting 7.
"""

import json
from datetime import UTC, date, datetime

import pytest

from builders import make_assignment, make_crew_profile, make_user
from mission_control.domain.enums import AssignmentStatus, MissionStatus, Role
from mission_control.domain.errors import Forbidden, InvalidInput, NotFound, RuleViolation
from mission_control.domain.permissions import Actor
from mission_control.services import crew
from mission_control.services.context import ServiceContext

NOW = datetime(2027, 1, 5, 9, 0, tzinfo=UTC)

RUTH = Actor(user_id=1, org_id=1, role=Role.DIRECTOR, crew_profile_id=None)
LEE = Actor(user_id=4, org_id=1, role=Role.LEAD, crew_profile_id=None)
ANA = Actor(user_id=6, org_id=1, role=Role.LEAD, crew_profile_id=6)
BEN = Actor(user_id=7, org_id=1, role=Role.CREW, crew_profile_id=7)
FAY = Actor(user_id=11, org_id=1, role=Role.CREW, crew_profile_id=11)
HANA = Actor(user_id=13, org_id=1, role=Role.CREW, crew_profile_id=13)
SAM = Actor(user_id=14, org_id=2, role=Role.DIRECTOR, crew_profile_id=None)
KAI = Actor(user_id=16, org_id=2, role=Role.CREW, crew_profile_id=16)

PILOTING, LEADERSHIP, SYS_ENG, EVA, GEOLOGY, HELIX_PILOTING = 1, 2, 3, 4, 5, 7
FAY_LEAVE = 1  # Fay's seeded Medical leave, 5–8 Mar 2027


def as_(conn, actor):
    return ServiceContext(conn, actor, now=NOW)


def audit_count(conn):
    return conn.execute("SELECT count(*) FROM audit_events").fetchone()[0]


def last_audit(conn):
    row = conn.execute(
        "SELECT actor_id, event, crew_profile_id, reason, data FROM audit_events"
        " ORDER BY id DESC LIMIT 1"
    ).fetchone()
    return (
        row["actor_id"],
        row["event"],
        row["crew_profile_id"],
        row["reason"],
        json.loads(row["data"]),
    )


def snapshot(conn):
    """Everything the crew service can change, to prove a refusal changed nothing."""
    return [
        conn.execute(f"SELECT * FROM {table} ORDER BY rowid").fetchall()
        for table in ("crew_profiles", "crew_skills", "unavailability", "audit_events")
    ]


def unchanged(conn, before):
    return [list(map(tuple, t)) for t in snapshot(conn)] == [list(map(tuple, t)) for t in before]


# --- Viewing profiles (§5.7, AC-24) -------------------------------------------------------


def test_ac24_lead_sees_fays_busy_dates_without_the_reason(seeded_db):
    fay = crew.view_crew(as_(seeded_db, LEE), 11)
    assert [(u.window.start, u.window.end) for u in fay.unavailability] == [
        (date(2027, 3, 5), date(2027, 3, 8))
    ]
    assert [u.reason for u in fay.unavailability] == [None]


def test_ac24_director_ruth_sees_fays_unavailability_reason(seeded_db):
    fay = crew.view_crew(as_(seeded_db, RUTH), 11)
    assert [u.reason for u in fay.unavailability] == ["Medical"]


def test_ac24_fay_sees_her_own_reason(seeded_db):
    fay = crew.view_crew(as_(seeded_db, FAY), 11)
    assert [u.reason for u in fay.unavailability] == ["Medical"]


def test_ac24_ben_cannot_view_fays_profile(seeded_db):
    with pytest.raises(NotFound) as err:
        crew.view_crew(as_(seeded_db, BEN), 11)
    assert err.value.message == "Crew member not found"


def test_ac24_ben_can_view_his_own_profile(seeded_db):
    assert crew.view_crew(as_(seeded_db, BEN), 7).name == "Ben"


def test_crew_view_includes_skills_with_names_and_personal_details(seeded_db):
    ben = crew.view_crew(as_(seeded_db, LEE), 7)
    assert (ben.crew_profile_id, ben.user_id, ben.name, ben.email, ben.active, ben.bio) == (
        7,
        7,
        "Ben",
        "ben@aurora.example",
        True,
        None,
    )
    assert [(s.skill_id, s.skill_name, s.level) for s in ben.skills] == [
        (EVA, "EVA", 3),
        (SYS_ENG, "Systems Engineering", 4),
    ]
    assert ben.unavailability == ()


def test_ac27_another_organisations_profile_is_not_found(seeded_db):
    with pytest.raises(NotFound):
        crew.view_crew(as_(seeded_db, LEE), 16)  # Kai, Helix
    with pytest.raises(NotFound):
        crew.view_crew(as_(seeded_db, SAM), 11)  # Fay, Aurora


def test_ac28_lead_lists_every_profile_in_their_organisation_only(seeded_db):
    listed = crew.list_crew(as_(seeded_db, LEE))
    assert [c.crew_profile_id for c in listed] == [2, 6, 7, 8, 9, 10, 11, 12, 13]


def test_ac24_crew_list_hides_reasons_from_leads_and_shows_them_to_directors(seeded_db):
    def fays_reasons(actor):
        listed = crew.list_crew(as_(seeded_db, actor))
        fay = next(c for c in listed if c.crew_profile_id == 11)
        return [u.reason for u in fay.unavailability]

    assert fays_reasons(LEE) == [None]
    assert fays_reasons(RUTH) == ["Medical"]


def test_ac24_crew_member_list_contains_only_themselves(seeded_db):
    assert [c.crew_profile_id for c in crew.list_crew(as_(seeded_db, BEN))] == [7]


def test_ac24_lead_lists_fays_busy_dates_without_the_reason(seeded_db):
    entries = crew.list_unavailability(as_(seeded_db, LEE), 11)
    assert [(u.id, u.window.start, u.reason) for u in entries] == [
        (FAY_LEAVE, date(2027, 3, 5), None)
    ]
    assert [u.reason for u in crew.list_unavailability(as_(seeded_db, FAY), 11)] == ["Medical"]


def test_ac24_ben_cannot_list_fays_unavailability(seeded_db):
    with pytest.raises(NotFound):
        crew.list_unavailability(as_(seeded_db, BEN), 11)


# --- Assignment history (V2) --------------------------------------------------------------


def test_v2_history_includes_missions_the_person_has_left(seeded_db):
    seeded_db.execute(
        "UPDATE assignments SET status = 'withdrawn', reason = 'Family' WHERE crew_profile_id = 7"
    )
    history = crew.assignment_history(as_(seeded_db, BEN), 7)
    assert [(h.mission_name, h.status, h.reason) for h in history] == [
        ("Deep Space Comms Upgrade", AssignmentStatus.WITHDRAWN, "Family")
    ]


def test_v2_history_lists_every_assignment_newest_first(seeded_db):
    history = crew.assignment_history(as_(seeded_db, LEE), 8)  # Chen
    assert [(h.mission_name, h.mission_status, h.slot_name, h.status) for h in history] == [
        (
            "Orbital Telescope Service",
            MissionStatus.ACTIVE,
            "Engineer",
            AssignmentStatus.ACCEPTED,
        ),
        ("Mars Analog Habitat", MissionStatus.COMPLETED, "Engineer", AssignmentStatus.COMPLETED),
    ]


def test_v2_crew_cannot_view_someone_elses_history(seeded_db):
    with pytest.raises(NotFound):
        crew.assignment_history(as_(seeded_db, BEN), 8)


def test_ac27_history_of_another_organisations_crew_is_not_found(seeded_db):
    with pytest.raises(NotFound):
        crew.assignment_history(as_(seeded_db, RUTH), 17)  # Lena, Helix


# --- Personal details (P4, AC-16, AC-23) --------------------------------------------------


def test_ac23_ben_edits_his_personal_details(seeded_db):
    updated = crew.update_details(as_(seeded_db, BEN), 7, display_name="Benji", bio="EVA nerd")
    assert (updated.display_name, updated.bio) == ("Benji", "EVA nerd")
    assert crew.view_crew(as_(seeded_db, LEE), 7).name == "Benji"
    actor, event, profile, _, data = last_audit(seeded_db)
    assert (actor, event, profile) == (7, "crew.details_updated", 7)
    assert data == {
        "crew_name": "Benji",
        "changes": {"display_name": ["Ben", "Benji"], "bio": [None, "EVA nerd"]},
    }


def test_p4_display_name_is_kept_when_only_the_bio_changes_and_bio_can_be_cleared(seeded_db):
    ctx = as_(seeded_db, ANA)  # a Lead with a crew profile
    assert crew.update_details(ctx, 6, bio="Test pilot").display_name == "Ana"
    assert last_audit(seeded_db)[4] == {
        "crew_name": "Ana",
        "changes": {"bio": [None, "Test pilot"]},
    }
    cleared = crew.update_details(ctx, 6, bio="")
    assert (cleared.display_name, cleared.bio) == ("Ana", None)
    assert last_audit(seeded_db)[4] == {
        "crew_name": "Ana",
        "changes": {"bio": ["Test pilot", None]},
    }


def test_p4_display_name_cant_be_blank(seeded_db):
    before = snapshot(seeded_db)
    with pytest.raises(crew.InvalidInput, match="Display name"):
        crew.update_details(as_(seeded_db, BEN), 7, display_name="   ")
    assert unchanged(seeded_db, before)


@pytest.mark.parametrize("actor", [LEE, RUTH], ids=["lead", "director"])
def test_p4_nobody_else_edits_personal_details(seeded_db, actor):
    before = snapshot(seeded_db)
    with pytest.raises(Forbidden) as err:
        crew.update_details(as_(seeded_db, actor), 11, display_name="Hijack")
    assert (err.value.code, err.value.message) == (
        "not_owner",
        "You can only edit your own profile and availability",
    )
    assert unchanged(seeded_db, before)


def test_p4_crew_editing_another_profile_gets_not_found(seeded_db):
    with pytest.raises(NotFound):
        crew.update_details(as_(seeded_db, BEN), 11, display_name="Hijack")


def test_ac29_editing_another_organisations_profile_is_not_found(seeded_db):
    before = snapshot(seeded_db)
    with pytest.raises(NotFound):
        crew.update_details(as_(seeded_db, KAI), 11, display_name="Hijack")
    assert unchanged(seeded_db, before)


def test_ac29_another_orgs_profile_is_not_found_before_its_values_are_checked(seeded_db):
    before = snapshot(seeded_db)
    with pytest.raises(NotFound):
        crew.update_details(as_(seeded_db, SAM), 11, display_name="   ")
    assert unchanged(seeded_db, before)


def test_p4_permission_is_checked_before_the_display_name(seeded_db):
    with pytest.raises(Forbidden) as err:
        crew.update_details(as_(seeded_db, LEE), 11, display_name="   ")
    assert err.value.code == "not_owner"


def test_p4_self_check_uses_the_profiles_user_not_the_profile_id(seeded_db):
    # Two new crew whose profile ids are swapped relative to their user ids.
    first = make_user(seeded_db, 1, "First Person")
    second = make_user(seeded_db, 1, "Second Person")
    second_profile = make_crew_profile(seeded_db, 1, second, "Second")
    first_profile = make_crew_profile(seeded_db, 1, first, "First")
    assert (first_profile, second_profile) == (second, first)
    me = Actor(user_id=first, org_id=1, role=Role.CREW, crew_profile_id=first_profile)

    assert crew.update_details(as_(seeded_db, me), first_profile, bio="Mine").bio == "Mine"
    with pytest.raises(NotFound):
        crew.update_details(as_(seeded_db, me), second_profile, bio="Not mine")


# --- Unavailability (P4–P6, AC-16, AC-17) -------------------------------------------------


def test_ac23_ben_adds_unavailability(seeded_db):
    added = crew.add_unavailability(
        as_(seeded_db, BEN), 7, date(2027, 6, 1), date(2027, 6, 3), "Training"
    )
    assert (added.window.start, added.window.end, added.reason) == (
        date(2027, 6, 1),
        date(2027, 6, 3),
        "Training",
    )
    assert [u.id for u in crew.list_unavailability(as_(seeded_db, BEN), 7)] == [added.id]
    actor, event, profile, reason, data = last_audit(seeded_db)
    assert (actor, event, profile, reason) == (7, "crew.unavailability_added", 7, None)
    assert data == {"crew_name": "Ben", "start_date": "2027-06-01", "end_date": "2027-06-03"}


def test_m2_unavailability_may_be_in_the_past(seeded_db):
    added = crew.add_unavailability(
        as_(seeded_db, FAY), 11, date(2020, 1, 1), date(2020, 1, 1), "Old leave"
    )
    assert added.window.mission_days == 1


def test_m2_unavailability_end_before_start_is_invalid(seeded_db):
    before = snapshot(seeded_db)
    with pytest.raises(InvalidInput) as err:
        crew.add_unavailability(as_(seeded_db, BEN), 7, date(2027, 6, 3), date(2027, 6, 1), "X")
    assert err.value.message == "The end date 2027-06-01 is before the start date 2027-06-03"
    assert unchanged(seeded_db, before)


def test_p5_every_unavailability_mistake_is_listed_together(seeded_db):
    before = snapshot(seeded_db)
    with pytest.raises(InvalidInput) as err:
        crew.add_unavailability(as_(seeded_db, BEN), 7, date(2027, 6, 3), date(2027, 6, 1), " ")
    assert (err.value.code, err.value.message) == ("validation_error", "Some values aren't valid")
    assert [(p.code, p.message) for p in err.value.problems] == [
        ("validation_error", "The end date 2027-06-01 is before the start date 2027-06-03"),
        ("validation_error", "Unavailability needs a reason"),
    ]
    assert unchanged(seeded_db, before)


def test_p5_unavailability_needs_a_reason(seeded_db):
    with pytest.raises(crew.InvalidInput, match="reason"):
        crew.add_unavailability(as_(seeded_db, BEN), 7, date(2027, 6, 1), date(2027, 6, 3), " ")


def test_p6_unavailability_over_an_accepted_assignment_is_refused(seeded_db):
    # Ben is accepted on Deep Space Comms Upgrade (1–20 Apr); 20 Apr is a shared boundary day.
    before = snapshot(seeded_db)
    with pytest.raises(RuleViolation) as err:
        crew.add_unavailability(
            as_(seeded_db, BEN), 7, date(2027, 4, 20), date(2027, 4, 25), "Holiday"
        )
    assert [p.code for p in err.value.problems][:1] == ["overlap"]
    assert err.value.problems[0].message == (
        "Ben has an accepted assignment on Deep Space Comms Upgrade overlapping "
        "2027-04-20 to 2027-04-20"
    )
    [problem] = err.value.problems
    assert problem.code == "overlap"
    assert dict(problem.refs) == {
        "crew_profile_id": 7,
        "mission_id": 6,
        "mission_name": "Deep Space Comms Upgrade",
    }
    assert unchanged(seeded_db, before)


def test_ac16_hana_cant_be_unavailable_during_the_active_telescope_mission(seeded_db):
    with pytest.raises(RuleViolation) as err:
        crew.add_unavailability(
            as_(seeded_db, HANA), 13, date(2027, 1, 1), date(2027, 1, 10), "Leave"
        )
    assert err.value.message == "Hana has an accepted assignment overlapping those dates"
    assert "Orbital Telescope Service" in err.value.problems[0].message


def test_ac16_every_overlapping_assignment_is_listed(seeded_db):
    # Chen accepted on Station Reboost (25 Feb – 2 Mar) as well as the Telescope (10–14 Jan).
    make_assignment(seeded_db, 1, 3, _slot_id(seeded_db, 3, "Engineer"), 8, 5, "accepted")
    with pytest.raises(RuleViolation) as err:
        crew.add_unavailability(
            as_(seeded_db, crew_actor(8)), 8, date(2027, 1, 1), date(2027, 3, 31), "Sabbatical"
        )
    assert [p.code for p in err.value.problems][:1] == ["overlap"]
    assert [p.refs["mission_name"] for p in err.value.problems] == [
        "Orbital Telescope Service",
        "Station Reboost",
    ]
    assert err.value.message == "Chen has accepted assignments overlapping those dates"


def test_p6_proposals_and_finished_missions_dont_block_unavailability(seeded_db):
    # Ben proposed (not accepted) on Lunar Gateway Resupply, 1–10 Mar.
    make_assignment(seeded_db, 1, 1, _slot_id(seeded_db, 1, "Flight Engineer"), 7, 4)
    crew.add_unavailability(as_(seeded_db, BEN), 7, date(2027, 3, 2), date(2027, 3, 3), "Course")
    # Chen's Mars Analog Habitat (May 2026) is Completed.
    crew.add_unavailability(
        as_(seeded_db, crew_actor(8)), 8, date(2026, 5, 10), date(2026, 5, 12), "Late note"
    )


@pytest.mark.parametrize("actor", [LEE, RUTH], ids=["lead", "director"])
def test_p4_nobody_else_records_unavailability(seeded_db, actor):
    before = snapshot(seeded_db)
    with pytest.raises(Forbidden) as err:
        crew.add_unavailability(
            as_(seeded_db, actor), 11, date(2027, 6, 1), date(2027, 6, 2), "Booked"
        )
    assert err.value.code == "not_owner"
    assert unchanged(seeded_db, before)


@pytest.mark.parametrize(
    ("start", "end", "reason"),
    [(date(2027, 6, 1), date(2027, 6, 2), " "), (date(2027, 6, 2), date(2027, 6, 1), "Booked")],
    ids=["blank reason", "end before start"],
)
def test_p4_permission_is_checked_before_the_unavailability_values(seeded_db, start, end, reason):
    before = snapshot(seeded_db)
    with pytest.raises(Forbidden) as err:
        crew.add_unavailability(as_(seeded_db, LEE), 11, start, end, reason)
    assert err.value.code == "not_owner"
    assert unchanged(seeded_db, before)


def test_p4_crew_recording_unavailability_for_another_gets_not_found(seeded_db):
    with pytest.raises(NotFound):
        crew.add_unavailability(as_(seeded_db, BEN), 11, date(2027, 6, 1), date(2027, 6, 2), "X")


def test_p4_fay_removes_her_own_unavailability(seeded_db):
    crew.remove_unavailability(as_(seeded_db, FAY), 11, FAY_LEAVE)
    assert crew.list_unavailability(as_(seeded_db, FAY), 11) == []
    actor, event, profile, _, data = last_audit(seeded_db)
    assert (actor, event, profile) == (11, "crew.unavailability_removed", 11)
    assert data == {"crew_name": "Fay", "start_date": "2027-03-05", "end_date": "2027-03-08"}


def test_p4_removing_someone_elses_entry_is_not_found(seeded_db):
    before = snapshot(seeded_db)
    with pytest.raises(NotFound) as err:
        crew.remove_unavailability(as_(seeded_db, BEN), 7, FAY_LEAVE)  # Fay's, under Ben
    assert err.value.message == "Unavailability not found"
    with pytest.raises(NotFound):
        crew.remove_unavailability(as_(seeded_db, BEN), 11, FAY_LEAVE)  # Fay's profile
    assert unchanged(seeded_db, before)


def test_p4_lead_cannot_remove_fays_unavailability(seeded_db):
    with pytest.raises(Forbidden) as err:
        crew.remove_unavailability(as_(seeded_db, LEE), 11, FAY_LEAVE)
    assert err.value.code == "not_owner"


def test_ac29_removing_another_organisations_unavailability_is_not_found(seeded_db):
    before = snapshot(seeded_db)
    with pytest.raises(NotFound):
        crew.remove_unavailability(as_(seeded_db, KAI), 16, FAY_LEAVE)
    with pytest.raises(NotFound):
        crew.remove_unavailability(as_(seeded_db, SAM), 11, FAY_LEAVE)
    assert unchanged(seeded_db, before)


# --- Skill levels (P2, P3, AC-23) ---------------------------------------------------------


def test_ac23_ana_cant_change_her_own_skill_levels(seeded_db):
    before = snapshot(seeded_db)
    for attempt in (
        lambda ctx: crew.set_skill_level(ctx, 6, PILOTING, 3),
        lambda ctx: crew.remove_skill_level(ctx, 6, PILOTING),
    ):
        with pytest.raises(Forbidden) as err:
            attempt(as_(seeded_db, ANA))
        assert (err.value.code, err.value.message) == (
            "self_skill_edit",
            "You can't change your own skill levels",
        )
    assert unchanged(seeded_db, before)


def test_ac23_lee_can_change_anas_skill_levels(seeded_db):
    level = crew.set_skill_level(as_(seeded_db, LEE), 6, PILOTING, 3)
    assert (level.skill_id, level.skill_name, level.level) == (PILOTING, "Piloting", 3)
    stored = seeded_db.execute(
        "SELECT level, updated_by_id FROM crew_skills WHERE crew_profile_id = 6 AND skill_id = 1"
    ).fetchone()
    assert tuple(stored) == (3, 4)
    actor, event, profile, _, data = last_audit(seeded_db)
    assert (actor, event, profile) == (4, "crew.skill_set", 6)
    assert data == {"crew_name": "Ana", "skill_name": "Piloting", "changes": {"level": [5, 3]}}


def test_ac23_ben_cant_edit_skills(seeded_db):
    before = snapshot(seeded_db)
    with pytest.raises(Forbidden) as err:
        crew.set_skill_level(as_(seeded_db, BEN), 7, EVA, 5)
    assert (err.value.code, err.value.message) == (
        "role_forbidden",
        "Crew can't change skill levels",
    )
    with pytest.raises(NotFound):  # Fay's profile isn't visible to him
        crew.set_skill_level(as_(seeded_db, BEN), 11, EVA, 5)
    assert unchanged(seeded_db, before)


def test_ac23_crew_setting_an_out_of_range_level_is_forbidden_not_invalid(seeded_db):
    before = snapshot(seeded_db)
    with pytest.raises(Forbidden) as err:
        crew.set_skill_level(as_(seeded_db, BEN), 7, EVA, 9)
    assert err.value.code == "role_forbidden"
    assert unchanged(seeded_db, before)


def test_ac29_another_orgs_skill_level_is_not_found_before_the_level_is_checked(seeded_db):
    with pytest.raises(NotFound):
        crew.set_skill_level(as_(seeded_db, SAM), 7, EVA, 9)


def test_p3_director_adds_a_new_skill_level(seeded_db):
    crew.set_skill_level(as_(seeded_db, RUTH), 11, EVA, 2)
    assert crew.view_crew(as_(seeded_db, RUTH), 11).skills[0].skill_name == "EVA"
    assert last_audit(seeded_db)[4]["changes"] == {"level": [None, 2]}


def test_p3_lead_removes_a_skill_level(seeded_db):
    crew.remove_skill_level(as_(seeded_db, LEE), 7, EVA)
    assert [s.skill_id for s in crew.view_crew(as_(seeded_db, LEE), 7).skills] == [SYS_ENG]
    actor, event, profile, _, data = last_audit(seeded_db)
    assert (actor, event, profile) == (4, "crew.skill_removed", 7)
    assert data == {"crew_name": "Ben", "skill_name": "EVA", "changes": {"level": [3, None]}}


@pytest.mark.parametrize("level", [0, 6])
def test_p2_proficiency_is_from_1_to_5(seeded_db, level):
    with pytest.raises(crew.InvalidInput, match="between 1 and 5"):
        crew.set_skill_level(as_(seeded_db, LEE), 7, EVA, level)


def test_p3_change_affecting_only_a_pending_assignment_is_allowed(seeded_db):
    # Ben's Deep Space Comms Engineer slot (Pending) needs Systems Engineering 3.
    crew.set_skill_level(as_(seeded_db, LEE), 7, SYS_ENG, 1)
    assert seeded_db.execute("SELECT status FROM missions WHERE id = 6").fetchone()[0] == (
        "pending_approval"
    )


def test_p3_change_affecting_only_a_draft_assignment_is_allowed(seeded_db):
    crew.remove_skill_level(as_(seeded_db, LEE), 12, SYS_ENG)  # Gus, Station Reboost (Draft)


def test_p3_skill_change_breaking_an_active_assignment_is_refused(seeded_db):
    before = snapshot(seeded_db)
    with pytest.raises(RuleViolation) as err:
        crew.set_skill_level(as_(seeded_db, LEE), 13, EVA, 2)  # Hana, Telescope needs EVA 3
    assert [p.code for p in err.value.problems][:1] == ["invalidates_active_assignment"]
    assert err.value.problems[0].message == (
        "Hana needs EVA 3 as EVA Specialist on active mission Orbital Telescope Service"
    )
    assert [dict(p.refs) for p in err.value.problems] == [{"mission_id": 5, "skill_id": EVA}]
    assert unchanged(seeded_db, before)


def test_p3_removing_a_skill_an_active_assignment_needs_is_refused(seeded_db):
    before = snapshot(seeded_db)
    with pytest.raises(RuleViolation) as err:
        crew.remove_skill_level(as_(seeded_db, RUTH), 13, EVA)
    assert [p.code for p in err.value.problems][:1] == ["invalidates_active_assignment"]
    assert unchanged(seeded_db, before)


def test_p3_changes_that_keep_an_active_assignment_valid_are_allowed(seeded_db):
    crew.set_skill_level(as_(seeded_db, LEE), 13, EVA, 4)  # raising
    crew.set_skill_level(as_(seeded_db, LEE), 13, GEOLOGY, 1)  # not required on the Telescope


def test_ac29_a_skill_from_another_organisations_catalogue_is_not_found(seeded_db):
    before = snapshot(seeded_db)
    with pytest.raises(NotFound) as err:
        crew.set_skill_level(as_(seeded_db, LEE), 11, HELIX_PILOTING, 3)
    assert err.value.message == "Skill not found"
    with pytest.raises(NotFound):
        crew.set_skill_level(as_(seeded_db, LEE), 11, 999, 3)
    assert unchanged(seeded_db, before)


def test_ac29_setting_skills_on_another_organisations_crew_is_not_found(seeded_db):
    before = snapshot(seeded_db)
    with pytest.raises(NotFound):
        crew.set_skill_level(as_(seeded_db, LEE), 16, PILOTING, 3)  # Kai
    with pytest.raises(NotFound):
        crew.remove_skill_level(as_(seeded_db, SAM), 6, PILOTING)  # Ana
    assert unchanged(seeded_db, before)


def test_p3_removing_a_skill_the_person_doesnt_have_is_not_found(seeded_db):
    with pytest.raises(NotFound) as err:
        crew.remove_skill_level(as_(seeded_db, LEE), 11, EVA)
    assert err.value.message == "Skill level not found"


def test_p3_self_check_uses_the_profiles_user_not_the_profile_id(seeded_db):
    # A Lead whose crew profile id equals another person's user id, and the reverse.
    lead = make_user(seeded_db, 1, "Lead Person", role="lead")
    other = make_user(seeded_db, 1, "Other Person")
    other_profile = make_crew_profile(seeded_db, 1, other, "Other")
    lead_profile = make_crew_profile(seeded_db, 1, lead, "Lead")
    assert (lead_profile, other_profile) == (other, lead)
    me = Actor(user_id=lead, org_id=1, role=Role.LEAD, crew_profile_id=lead_profile)

    with pytest.raises(Forbidden) as err:
        crew.set_skill_level(as_(seeded_db, me), lead_profile, EVA, 3)
    assert err.value.code == "self_skill_edit"
    assert crew.set_skill_level(as_(seeded_db, me), other_profile, EVA, 3).level == 3


# --- Helpers ------------------------------------------------------------------------------


def crew_actor(user_id: int) -> Actor:
    return Actor(user_id=user_id, org_id=1, role=Role.CREW, crew_profile_id=user_id)


def _slot_id(conn, mission_id: int, name: str) -> int:
    return conn.execute(
        "SELECT id FROM slots WHERE mission_id = ? AND name = ?", (mission_id, name)
    ).fetchone()[0]


# Regression (review fix 3): private unavailability reasons never reach the audit log


def test_ac24_unavailability_reason_is_not_written_to_the_audit_log(seeded_db):
    crew.add_unavailability(as_(seeded_db, BEN), 7, date(2027, 6, 1), date(2027, 6, 3), "Dentist")
    _, event, _, reason, data = last_audit(seeded_db)
    assert event == "crew.unavailability_added"
    assert reason is None
    assert "Dentist" not in json.dumps(data)
    assert "Dentist" not in "".join(
        str(tuple(r)) for r in seeded_db.execute("SELECT * FROM audit_events")
    )


# Regression (review fix 5): an update that changes nothing writes nothing


def test_p4_update_with_no_fields_writes_nothing(seeded_db):
    before = audit_count(seeded_db)
    profile = crew.update_details(as_(seeded_db, BEN), 7)
    assert (profile.display_name, profile.bio) == ("Ben", None)
    assert audit_count(seeded_db) == before


# The 422 error is the shared domain one, so the API maps a single class


def test_invalid_input_is_the_shared_domain_error(seeded_db):
    from mission_control.domain.errors import InvalidInput

    with pytest.raises(InvalidInput) as err:
        crew.set_skill_level(as_(seeded_db, LEE), 7, EVA, 6)
    assert err.value.code == "validation_error"
