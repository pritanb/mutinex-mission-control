"""M9: Director administration (PRD §3, P1, P7–P10, A1, §5.7; AC-25, AC-26, AC-27–29)."""

import json
from datetime import UTC, datetime

import pytest

from builders import make_assignment, make_mission, make_slot, make_user
from mission_control.domain.enums import Role
from mission_control.domain.errors import (
    Forbidden,
    InvalidInput,
    NotFound,
    RuleViolation,
    Unauthenticated,
)
from mission_control.domain.passwords import PasswordTooShort
from mission_control.domain.permissions import Actor
from mission_control.infra import security
from mission_control.services import admin, auth
from mission_control.services.context import ServiceContext

NOW = datetime(2027, 1, 5, 9, 0, tzinfo=UTC)
PASSPHRASE = "correct horse battery staple"

RUTH = Actor(user_id=1, org_id=1, role=Role.DIRECTOR, crew_profile_id=None)
LEE = Actor(user_id=4, org_id=1, role=Role.LEAD, crew_profile_id=None)
BEN = Actor(user_id=7, org_id=1, role=Role.CREW, crew_profile_id=7)
SAM = Actor(user_id=14, org_id=2, role=Role.DIRECTOR, crew_profile_id=None)

# Seed ids (PRD §9, crew profile id = user id)
MARCO, INGRID, NORA, ANA, BEN_ID, CHEN, FAY, HANA = 2, 3, 5, 6, 7, 8, 11, 13
LEE_ID, KAI, PRIYA = 4, 16, 15
PILOTING, SYS_ENG, GEOLOGY, HELIX_PILOTING = 1, 3, 5, 7
GATEWAY, ASTEROID, REBOOST, MEDICAL, TELESCOPE, DEEP_SPACE = 1, 2, 3, 4, 5, 6


def ctx(conn, actor=RUTH):
    return ServiceContext(conn, actor, now=NOW)


def snapshot(conn):
    """Every row that admin use cases could touch, to prove a refusal changed nothing."""
    tables = ["organisations", "users", "crew_profiles", "skills", "auth_tokens", "audit_events"]
    return {
        t: [tuple(r) for r in conn.execute(f"SELECT * FROM {t} ORDER BY rowid")] for t in tables
    }


def audit_events(conn, since_id=0):
    rows = conn.execute(
        "SELECT actor_id, event, crew_profile_id, data FROM audit_events WHERE id > ? ORDER BY id",
        (since_id,),
    ).fetchall()
    return [(r[0], r[1], r[2], json.loads(r[3])) for r in rows]


def last_audit_id(conn):
    return conn.execute("SELECT coalesce(max(id), 0) FROM audit_events").fetchone()[0]


def refused(exc_info):
    """(code, message, problem codes) of a raised refusal."""
    e = exc_info.value
    return e.code, e.message, [p.code for p in getattr(e, "problems", ())]


# --- Organisation settings (A1) -----------------------------------------------------------


def test_a1_director_views_the_organisation_settings(seeded_db):
    org = admin.view_organisation(ctx(seeded_db))
    assert (org.id, org.name, org.required_approvals) == (1, "Aurora Space Agency", 2)


def test_a1_director_sets_the_required_approvals_and_it_is_audited(seeded_db):
    start = last_audit_id(seeded_db)
    org = admin.set_required_approvals(ctx(seeded_db), 3)
    assert org.required_approvals == 3
    assert admin.view_organisation(ctx(seeded_db)).required_approvals == 3
    assert audit_events(seeded_db, start) == [
        (1, "org.required_approvals_changed", None, {"changes": {"required_approvals": [2, 3]}}),
    ]


def test_a1_changing_the_setting_doesnt_affect_a_round_already_in_progress(seeded_db):
    admin.set_required_approvals(ctx(seeded_db), 1)
    pending = ctx(seeded_db).repos.missions.get(DEEP_SPACE)
    assert pending.approvals_required == 2


@pytest.mark.parametrize("n", [0, -1])
def test_a1_required_approvals_must_be_at_least_one(seeded_db, n):
    before = snapshot(seeded_db)
    with pytest.raises(InvalidInput):
        admin.set_required_approvals(ctx(seeded_db), n)
    assert snapshot(seeded_db) == before


def test_a1_setting_the_same_number_again_writes_nothing(seeded_db):
    before = snapshot(seeded_db)
    assert admin.set_required_approvals(ctx(seeded_db), 2).required_approvals == 2
    assert snapshot(seeded_db) == before


# --- Who may administer (AC-25, §5.7) -----------------------------------------------------

ADMIN_CALLS = {
    "view organisation": lambda c: admin.view_organisation(c),
    "set approvals": lambda c: admin.set_required_approvals(c, 1),
    "list users": lambda c: admin.list_users(c),
    "view user": lambda c: admin.view_user(c, BEN_ID),
    "create user": lambda c: admin.create_user(
        c, "new@aurora.example", "New Person", Role.CREW, PASSPHRASE
    ),
    "create crew profile": lambda c: admin.create_crew_profile(c, INGRID),
    "change role": lambda c: admin.change_role(c, FAY, Role.LEAD),
    "deactivate": lambda c: admin.deactivate_user(c, FAY),
    "add skill": lambda c: admin.add_skill(c, "Robotics"),
    "rename skill": lambda c: admin.update_skill(c, GEOLOGY, name="Planetary Geology"),
    "delete skill": lambda c: admin.delete_skill(c, GEOLOGY),
}


@pytest.mark.parametrize("actor", [LEE, BEN], ids=["lead", "crew"])
@pytest.mark.parametrize("call", ADMIN_CALLS.values(), ids=ADMIN_CALLS.keys())
def test_ac25_leads_and_crew_cant_manage_users_the_catalogue_or_the_approval_setting(
    seeded_db, actor, call, monkeypatch
):
    hashed = []
    monkeypatch.setattr(security, "hash_password", lambda p: hashed.append(p) or "never")
    before = snapshot(seeded_db)
    with pytest.raises(Forbidden) as err:
        call(ctx(seeded_db, actor))
    assert err.value.code == "role_forbidden"
    assert snapshot(seeded_db) == before
    assert hashed == []  # refused before any Argon2 work


def test_ac25_the_refusal_reads_as_a_sentence(seeded_db):
    with pytest.raises(Forbidden) as err:
        admin.set_required_approvals(ctx(seeded_db, LEE), 1)
    assert err.value.message == "Leads can't manage the organisation"


def test_p1_leads_can_list_the_catalogue_but_crew_cant(seeded_db):
    names = [s.name for s in admin.list_skills(ctx(seeded_db, LEE))]
    assert names == [
        "EVA",
        "Flight Medicine",
        "Geology",
        "Leadership",
        "Piloting",
        "Systems Engineering",
    ]
    with pytest.raises(Forbidden) as err:
        admin.list_skills(ctx(seeded_db, BEN))
    assert err.value.message == "Crew can't view the skill catalogue"


# --- Users: list, view, isolation (AC-27, AC-28, AC-29) ------------------------------------


def test_ac28_the_user_list_has_only_the_callers_organisation(seeded_db):
    assert [u.id for u in admin.list_users(ctx(seeded_db))] == list(range(1, 14))
    assert [u.name for u in admin.list_users(ctx(seeded_db, SAM))] == [
        "Sam Rivera",
        "Priya Nair",
        "Kai Tanaka",
        "Lena Fischer",
        "Omar Haddad",
        "Tess Moreno",
    ]


def test_ac27_viewing_a_user_by_id(seeded_db):
    ben = admin.view_user(ctx(seeded_db), BEN_ID)
    assert (ben.name, ben.email, ben.role, ben.is_active) == (
        "Ben Ito",
        "ben@aurora.example",
        Role.CREW,
        True,
    )


ISOLATION_CALLS = {
    "view user": lambda c: admin.view_user(c, KAI),
    "create crew profile": lambda c: admin.create_crew_profile(c, PRIYA),
    "change role": lambda c: admin.change_role(c, KAI, Role.LEAD),
    "deactivate": lambda c: admin.deactivate_user(c, KAI),
    "rename skill": lambda c: admin.update_skill(c, HELIX_PILOTING, name="Flying"),
    "delete skill": lambda c: admin.delete_skill(c, HELIX_PILOTING),
}


@pytest.mark.parametrize("call", ISOLATION_CALLS.values(), ids=ISOLATION_CALLS.keys())
def test_ac27_ac29_another_organisations_user_or_skill_is_not_found(seeded_db, call):
    before = snapshot(seeded_db)
    with pytest.raises(NotFound):
        call(ctx(seeded_db))
    assert snapshot(seeded_db) == before


def test_ac27_another_organisations_id_looks_like_a_missing_one(seeded_db):
    with pytest.raises(NotFound) as other_org:
        admin.view_user(ctx(seeded_db), KAI)
    with pytest.raises(NotFound) as missing:
        admin.view_user(ctx(seeded_db), 999)
    assert other_org.value.message == missing.value.message == "User not found"


# --- Users: create (P9, P10) --------------------------------------------------------------


def test_p10_director_creates_a_user_who_can_log_in_with_the_initial_password(seeded_db):
    user = admin.create_user(ctx(seeded_db), "zoe@aurora.example", "Zoe Lin", Role.LEAD, PASSPHRASE)
    assert (user.org_id, user.email, user.name, user.role, user.is_active) == (
        1,
        "zoe@aurora.example",
        "Zoe Lin",
        Role.LEAD,
        True,
    )
    session = auth.login(seeded_db, "zoe@aurora.example", PASSPHRASE, now=NOW)
    assert session.user == user
    stored = security.password_hash_of(seeded_db, 1, user.id)
    assert stored.startswith("$argon2id$") and PASSPHRASE not in stored


def test_p10_an_initial_password_under_15_characters_is_refused(seeded_db):
    before = snapshot(seeded_db)
    with pytest.raises(PasswordTooShort):
        admin.create_user(ctx(seeded_db), "zoe@aurora.example", "Zoe Lin", Role.CREW, "x" * 14)
    assert snapshot(seeded_db) == before
    admin.create_user(ctx(seeded_db), "zoe@aurora.example", "Zoe Lin", Role.CREW, "x" * 15)


def test_p10_the_initial_password_is_hashed_outside_the_write_transaction(seeded_db, monkeypatch):
    seen = []
    real_hash = security.hash_password
    monkeypatch.setattr(
        security, "hash_password", lambda p: seen.append(seeded_db.in_transaction) or real_hash(p)
    )
    admin.create_user(ctx(seeded_db), "zoe@aurora.example", "Zoe Lin", Role.CREW, PASSPHRASE)
    assert seen == [False]


def test_p9_a_new_crew_member_gets_a_crew_profile_named_by_first_name(seeded_db):
    start = last_audit_id(seeded_db)
    user = admin.create_user(ctx(seeded_db), "zoe@aurora.example", "Zoe Lin", Role.CREW, PASSPHRASE)
    profile = ctx(seeded_db).repos.crew.by_user(user.id)
    assert (profile.display_name, profile.bio) == ("Zoe", None)
    assert audit_events(seeded_db, start) == [
        (
            1,
            "user.created",
            None,
            {
                "user_id": user.id,
                "user_name": "Zoe Lin",
                "email": "zoe@aurora.example",
                "role": "crew",
            },
        ),
        (
            1,
            "crew_profile.created",
            profile.id,
            {"user_id": user.id, "user_name": "Zoe Lin", "display_name": "Zoe"},
        ),
    ]


@pytest.mark.parametrize("role", [Role.LEAD, Role.DIRECTOR])
def test_p9_a_new_lead_or_director_has_no_crew_profile_until_one_is_requested(seeded_db, role):
    user = admin.create_user(ctx(seeded_db), "zoe@aurora.example", "Zoe Lin", role, PASSPHRASE)
    assert ctx(seeded_db).repos.crew.by_user(user.id) is None


@pytest.mark.parametrize("email", ["ben@aurora.example", "BEN@Aurora.Example", "kai@helix.example"])
def test_p10_an_email_already_in_use_is_refused_cleanly(seeded_db, email):
    before = snapshot(seeded_db)
    with pytest.raises(RuleViolation) as err:
        admin.create_user(ctx(seeded_db), email, "Someone New", Role.CREW, PASSPHRASE)
    code, message, problems = refused(err)
    assert code == "rule_violation"
    assert problems == ["already_exists"]
    assert message == f"The email address {email} is already in use"
    assert dict(err.value.problems[0].refs) == {"email": email}  # never another org's user id
    assert snapshot(seeded_db) == before


def test_p10_names_and_emails_are_trimmed_and_blank_ones_rejected(seeded_db):
    user = admin.create_user(
        ctx(seeded_db), "  zoe@aurora.example ", "  Zoe Lin  ", Role.CREW, PASSPHRASE
    )
    assert (user.email, user.name) == ("zoe@aurora.example", "Zoe Lin")
    for email, name in [("  ", "Someone"), ("x@aurora.example", "   ")]:
        with pytest.raises(InvalidInput):
            admin.create_user(ctx(seeded_db), email, name, Role.CREW, PASSPHRASE)


def test_p10_every_blank_value_is_listed_together(seeded_db):
    before = snapshot(seeded_db)
    with pytest.raises(InvalidInput) as err:
        admin.create_user(ctx(seeded_db), " ", "  ", Role.CREW, PASSPHRASE)
    assert err.value.message == "Some values aren't valid"
    assert [(p.code, p.message) for p in err.value.problems] == [
        ("validation_error", "The email address can't be blank"),
        ("validation_error", "The name can't be blank"),
    ]
    assert snapshot(seeded_db) == before


# --- Crew profiles on request (P9) --------------------------------------------------------


def test_p9_a_director_gives_a_lead_a_crew_profile_defaulting_to_their_first_name(seeded_db):
    start = last_audit_id(seeded_db)
    profile = admin.create_crew_profile(ctx(seeded_db), LEE_ID)
    assert (profile.user_id, profile.display_name) == (LEE_ID, "Lee")
    assert audit_events(seeded_db, start) == [
        (
            1,
            "crew_profile.created",
            profile.id,
            {"user_id": LEE_ID, "user_name": "Lee Park", "display_name": "Lee"},
        ),
    ]


def test_p9_a_crew_profile_can_be_given_an_explicit_display_name(seeded_db):
    profile = admin.create_crew_profile(ctx(seeded_db), INGRID, display_name="  Dr Holm ")
    assert profile.display_name == "Dr Holm"


@pytest.mark.parametrize("user_id", [ANA, BEN_ID, MARCO])
def test_p9_someone_who_already_has_a_crew_profile_cant_get_another(seeded_db, user_id):
    before = snapshot(seeded_db)
    with pytest.raises(RuleViolation) as err:
        admin.create_crew_profile(ctx(seeded_db), user_id)
    assert refused(err)[0] == "rule_violation"
    assert refused(err)[2] == ["already_exists"]
    assert snapshot(seeded_db) == before


def test_p9_the_already_has_a_profile_refusal_names_the_person(seeded_db):
    with pytest.raises(RuleViolation) as err:
        admin.create_crew_profile(ctx(seeded_db), ANA)
    assert err.value.message == "Ana Okafor already has a crew profile"
    assert dict(err.value.problems[0].refs) == {"user_id": ANA, "crew_profile_id": ANA}


# --- Role changes (P7, P8, P9) ------------------------------------------------------------


def test_p9_a_crew_profile_survives_role_changes(seeded_db):
    admin.change_role(ctx(seeded_db), ANA, Role.DIRECTOR)
    admin.change_role(ctx(seeded_db), BEN_ID, Role.LEAD)
    crew = ctx(seeded_db).repos.crew
    assert crew.by_user(ANA).id == ANA
    assert crew.by_user(BEN_ID).id == BEN_ID
    assert crew.skills(BEN_ID) == {3: 4, 4: 3}


def test_p9_changing_someone_to_crew_gives_them_a_profile_if_missing(seeded_db):
    start = last_audit_id(seeded_db)
    user = admin.change_role(ctx(seeded_db), INGRID, Role.CREW)
    assert user.role == Role.CREW
    profile = ctx(seeded_db).repos.crew.by_user(INGRID)
    assert profile.display_name == "Ingrid"
    assert audit_events(seeded_db, start) == [
        (
            1,
            "user.role_changed",
            None,
            {
                "user_id": INGRID,
                "user_name": "Ingrid Holm",
                "changes": {"role": ["director", "crew"]},
            },
        ),
        (
            1,
            "crew_profile.created",
            profile.id,
            {"user_id": INGRID, "user_name": "Ingrid Holm", "display_name": "Ingrid"},
        ),
    ]


def test_p9_changing_someone_with_a_profile_to_crew_keeps_that_profile(seeded_db):
    admin.change_role(ctx(seeded_db), ANA, Role.CREW)
    profiles = [p for p in ctx(seeded_db).repos.crew.list() if p.user_id == ANA]
    assert [p.id for p in profiles] == [ANA]


def test_p9_the_new_role_applies_on_the_very_next_request(seeded_db):
    user = admin.create_user(ctx(seeded_db), "zoe@aurora.example", "Zoe Lin", Role.CREW, PASSPHRASE)
    token = auth.login(seeded_db, "zoe@aurora.example", PASSPHRASE, now=NOW).token
    admin.change_role(ctx(seeded_db), user.id, Role.LEAD)
    actor = auth.authenticate(seeded_db, token, now=NOW)
    profile = ctx(seeded_db).repos.crew.by_user(user.id)
    assert (actor.role, actor.crew_profile_id) == (Role.LEAD, profile.id)


@pytest.mark.parametrize("to_role", [Role.CREW, Role.DIRECTOR])
def test_p7_a_lead_who_owns_unfinished_missions_cant_change_role(seeded_db, to_role):
    before = snapshot(seeded_db)
    with pytest.raises(RuleViolation) as err:
        admin.change_role(ctx(seeded_db), NORA, to_role)
    code, message, problems = refused(err)
    assert (code, problems) == ("rule_violation", ["owns_open_missions"])
    assert err.value.problems[0].message == (
        "Nora Quinn still owns Station Reboost, Asteroid Survey, Lunar Surface Medical Study"
        " and Deep Space Comms Upgrade; reassign them to another Lead first"
    )
    assert dict(err.value.problems[0].refs) == {
        "user_id": NORA,
        "mission_ids": [REBOOST, ASTEROID, MEDICAL, DEEP_SPACE],
    }
    assert snapshot(seeded_db) == before


def test_p7_a_lead_whose_missions_are_all_finished_can_change_role(seeded_db):
    lead = make_user(seeded_db, 1, "Old Lead", role="lead")
    make_mission(seeded_db, 1, lead, name="Done", status="completed", approvals_required=2)
    make_mission(seeded_db, 1, lead, name="Dropped", status="cancelled")
    assert admin.change_role(ctx(seeded_db), lead, Role.CREW).role == Role.CREW


def test_p7_the_refusal_names_a_single_mission_in_the_singular(seeded_db):
    with pytest.raises(RuleViolation) as err:
        admin.change_role(ctx(seeded_db), LEE_ID, Role.CREW)
    assert err.value.problems[0].message == (
        "Lee Park still owns Orbital Telescope Service and Lunar Gateway Resupply;"
        " reassign them to another Lead first"
    )
    lead = make_user(seeded_db, 1, "Solo Lead", role="lead")
    make_mission(seeded_db, 1, lead, name="Only One")
    with pytest.raises(RuleViolation) as err:
        admin.change_role(ctx(seeded_db), lead, Role.CREW)
    assert err.value.message == "Solo Lead's role can't be changed"
    assert err.value.problems[0].message == (
        "Solo Lead still owns Only One; reassign it to another Lead first"
    )


def test_p8_the_last_active_director_cant_be_demoted(seeded_db):
    before = snapshot(seeded_db)
    for role in (Role.LEAD, Role.CREW):
        with pytest.raises(RuleViolation) as err:
            admin.change_role(ctx(seeded_db, SAM), SAM.user_id, role)
        code, message, problems = refused(err)
        assert (code, problems) == ("rule_violation", ["last_director"])
        assert err.value.problems[0].message == (
            "Sam Rivera is the only active Director, and the organisation must always have one;"
            " make someone else a Director first"
        )
        assert dict(err.value.problems[0].refs) == {"user_id": SAM.user_id}
    assert snapshot(seeded_db) == before


def test_p8_deactivated_directors_dont_count_towards_keeping_one(seeded_db):
    make_user(seeded_db, 2, "Former Director", role="director", is_active=False)
    with pytest.raises(RuleViolation) as err:
        admin.change_role(ctx(seeded_db, SAM), SAM.user_id, Role.LEAD)
    assert [p.code for p in err.value.problems][:1] == ["last_director"]


def test_p8_a_director_can_be_demoted_while_another_remains(seeded_db):
    assert admin.change_role(ctx(seeded_db), INGRID, Role.LEAD).role == Role.LEAD
    assert admin.change_role(ctx(seeded_db), RUTH.user_id, Role.LEAD).role == Role.LEAD
    # Marco is now the only active Director.
    with pytest.raises(RuleViolation) as err:
        admin.change_role(ctx(seeded_db, Actor(MARCO, 1, Role.DIRECTOR, MARCO)), MARCO, Role.LEAD)
    assert [p.code for p in err.value.problems][:1] == ["last_director"]


def test_p8_a_deactivated_director_can_change_role_without_affecting_the_count(seeded_db):
    former = make_user(seeded_db, 2, "Former Director", role="director", is_active=False)
    assert admin.change_role(ctx(seeded_db, SAM), former, Role.LEAD).role == Role.LEAD


def test_changing_to_the_same_role_writes_nothing(seeded_db):
    before = snapshot(seeded_db)
    assert admin.change_role(ctx(seeded_db, SAM), SAM.user_id, Role.DIRECTOR).role == Role.DIRECTOR
    assert snapshot(seeded_db) == before


def test_p9_a_role_change_is_audited_with_names(seeded_db):
    start = last_audit_id(seeded_db)
    admin.change_role(ctx(seeded_db), FAY, Role.LEAD)
    assert audit_events(seeded_db, start) == [
        (
            1,
            "user.role_changed",
            None,
            {
                "user_id": FAY,
                "user_name": "Fay Moreau",
                "changes": {"role": ["crew", "lead"]},
            },
        ),
    ]


# --- Deactivation (P7, P8, AC-26) ---------------------------------------------------------


def test_ac26_deactivating_someone_with_open_assignments_is_refused(seeded_db):
    before = snapshot(seeded_db)
    with pytest.raises(RuleViolation) as err:
        admin.deactivate_user(ctx(seeded_db), BEN_ID)
    code, message, problems = refused(err)
    assert (code, problems) == ("rule_violation", ["has_open_assignments"])
    assert err.value.problems[0].message == (
        "Ben Ito has an open assignment on Deep Space Comms Upgrade;"
        " they must withdraw or be removed first"
    )
    assert dict(err.value.problems[0].refs) == {"user_id": BEN_ID, "mission_ids": [DEEP_SPACE]}
    assert snapshot(seeded_db) == before


def test_ac26_proposals_count_as_open_assignments_and_every_mission_is_named(seeded_db):
    for mission, proposer in [(ASTEROID, NORA), (GATEWAY, LEE_ID)]:
        slot = seeded_db.execute(
            "SELECT id FROM slots WHERE mission_id = ? ORDER BY position", (mission,)
        ).fetchone()[0]
        make_assignment(seeded_db, 1, mission, slot, FAY, proposer, status="proposed")
    with pytest.raises(RuleViolation) as err:
        admin.deactivate_user(ctx(seeded_db), FAY)
    assert [p.code for p in err.value.problems][:1] == ["has_open_assignments"]
    assert err.value.problems[0].message == (
        "Fay Moreau has open assignments on Lunar Gateway Resupply and Asteroid Survey;"
        " they must withdraw or be removed first"
    )
    assert dict(err.value.problems[0].refs) == {"user_id": FAY, "mission_ids": [GATEWAY, ASTEROID]}


def test_ac26_finished_assignments_dont_block_deactivation(seeded_db):
    # Chen's Mars Analog assignment is Completed; only his open Telescope one blocks.
    with pytest.raises(RuleViolation) as err:
        admin.deactivate_user(ctx(seeded_db), CHEN)
    assert err.value.problems[0].message == (
        "Chen Wu has an open assignment on Orbital Telescope Service;"
        " they must withdraw or be removed first"
    )


def test_p7_deactivating_a_lead_who_owns_unfinished_missions_is_refused(seeded_db):
    with pytest.raises(RuleViolation) as err:
        admin.deactivate_user(ctx(seeded_db), LEE_ID)
    code, message, problems = refused(err)
    assert (code, problems) == ("rule_violation", ["owns_open_missions"])
    assert err.value.problems[0].message == (
        "Lee Park still owns Orbital Telescope Service and Lunar Gateway Resupply;"
        " reassign them to another Lead first"
    )


def test_p7_deactivation_lists_every_reason_at_once(seeded_db):
    mission = make_mission(
        seeded_db, 1, ANA, name="Ana's Mission", start="2027-08-01", end="2027-08-03"
    )
    slot = make_slot(seeded_db, 1, GATEWAY, name="Extra", position=9)
    make_assignment(seeded_db, 1, GATEWAY, slot, ANA, LEE_ID, status="accepted")
    before = snapshot(seeded_db)
    with pytest.raises(RuleViolation) as err:
        admin.deactivate_user(ctx(seeded_db), ANA)
    code, message, problems = refused(err)
    assert code == "rule_violation"
    assert message == "Ana Okafor can't be deactivated"
    assert problems == ["has_open_assignments", "owns_open_missions"]
    assert [p.message for p in err.value.problems] == [
        "Ana Okafor has an open assignment on Lunar Gateway Resupply;"
        " they must withdraw or be removed first",
        "Ana Okafor still owns Ana's Mission; reassign it to another Lead first",
    ]
    assert dict(err.value.problems[1].refs) == {"user_id": ANA, "mission_ids": [mission]}
    assert snapshot(seeded_db) == before


def test_ac26_the_last_active_director_cant_be_deactivated(seeded_db):
    before = snapshot(seeded_db)
    with pytest.raises(RuleViolation) as err:
        admin.deactivate_user(ctx(seeded_db, SAM), SAM.user_id)
    code, message, problems = refused(err)
    assert (code, problems) == ("rule_violation", ["last_director"])
    assert err.value.problems[0].message == (
        "Sam Rivera is the only active Director, and the organisation must always have one;"
        " make someone else a Director first"
    )
    assert snapshot(seeded_db) == before


def test_p8_the_last_director_with_open_assignments_gets_both_reasons(seeded_db):
    admin.change_role(ctx(seeded_db), RUTH.user_id, Role.LEAD)
    admin.change_role(ctx(seeded_db, Actor(INGRID, 1, Role.DIRECTOR, None)), INGRID, Role.LEAD)
    with pytest.raises(RuleViolation) as err:
        admin.deactivate_user(ctx(seeded_db, Actor(MARCO, 1, Role.DIRECTOR, MARCO)), MARCO)
    assert refused(err)[2] == ["has_open_assignments", "last_director"]


def test_ac26_a_deactivated_user_cant_sign_in_and_their_sessions_end(seeded_db):
    user = admin.create_user(ctx(seeded_db), "zoe@aurora.example", "Zoe Lin", Role.CREW, PASSPHRASE)
    token = auth.login(seeded_db, "zoe@aurora.example", PASSPHRASE, now=NOW).token
    assert auth.authenticate(seeded_db, token, now=NOW).user_id == user.id

    deactivated = admin.deactivate_user(ctx(seeded_db), user.id)

    assert deactivated.is_active is False
    with pytest.raises(Unauthenticated):
        auth.authenticate(seeded_db, token, now=NOW)
    with pytest.raises(Unauthenticated):
        auth.login(seeded_db, "zoe@aurora.example", PASSPHRASE, now=NOW)
    revoked = seeded_db.execute(
        "SELECT revoked_at FROM auth_tokens WHERE user_id = ?", (user.id,)
    ).fetchall()
    assert [r[0] for r in revoked] == ["2027-01-05T09:00:00.000Z"]


def test_ac26_sessions_are_revoked_in_the_same_transaction_as_the_deactivation(
    seeded_db, monkeypatch
):
    seen = []
    real = security.revoke_user_tokens

    def revoke(conn, user_id, now):
        seen.append((user_id, conn.in_transaction))
        real(conn, user_id, now)

    monkeypatch.setattr(security, "revoke_user_tokens", revoke)
    admin.deactivate_user(ctx(seeded_db), FAY)
    assert seen == [(FAY, True)]


def test_ac26_a_refused_deactivation_keeps_every_session(seeded_db):
    security.store_token(seeded_db, BEN_ID, "ben-session", NOW, datetime(2027, 1, 6, tzinfo=UTC))
    with pytest.raises(RuleViolation):
        admin.deactivate_user(ctx(seeded_db), BEN_ID)
    revoked = seeded_db.execute(
        "SELECT revoked_at FROM auth_tokens WHERE user_id = ?", (BEN_ID,)
    ).fetchone()[0]
    assert revoked is None


def test_p7_deactivation_keeps_the_user_their_profile_and_history(seeded_db):
    start = last_audit_id(seeded_db)
    admin.deactivate_user(ctx(seeded_db), FAY)
    repos = ctx(seeded_db).repos
    assert repos.users.get(FAY).is_active is False
    assert repos.crew.by_user(FAY).id == FAY
    assert [u.reason for u in repos.crew.unavailability(FAY)] == ["Medical"]
    assert audit_events(seeded_db, start) == [
        (1, "user.deactivated", FAY, {"user_id": FAY, "user_name": "Fay Moreau"}),
    ]


def test_p8_a_director_can_be_deactivated_while_another_remains(seeded_db):
    assert admin.deactivate_user(ctx(seeded_db), INGRID).is_active is False


def test_deactivating_someone_already_deactivated_writes_nothing(seeded_db):
    admin.deactivate_user(ctx(seeded_db), FAY)
    before = snapshot(seeded_db)
    assert admin.deactivate_user(ctx(seeded_db), FAY).is_active is False
    assert snapshot(seeded_db) == before


def test_p7_deactivation_without_a_crew_profile_checks_only_ownership_and_directors(seeded_db):
    lead = make_user(seeded_db, 1, "Idle Lead", role="lead")
    assert admin.deactivate_user(ctx(seeded_db), lead).is_active is False


# --- Skill catalogue (P1) -----------------------------------------------------------------


def test_p1_a_director_adds_a_skill(seeded_db):
    start = last_audit_id(seeded_db)
    skill = admin.add_skill(ctx(seeded_db), "  Robotics ", category="Engineering")
    assert (skill.org_id, skill.name, skill.category) == (1, "Robotics", "Engineering")
    assert skill in admin.list_skills(ctx(seeded_db))
    assert audit_events(seeded_db, start) == [
        (
            1,
            "skill.created",
            None,
            {"skill_id": skill.id, "skill_name": "Robotics", "category": "Engineering"},
        ),
    ]


@pytest.mark.parametrize("name", ["Piloting", "piloting", "  PILOTING  "])
def test_p1_skill_names_are_unique_per_organisation_ignoring_case(seeded_db, name):
    before = snapshot(seeded_db)
    with pytest.raises(RuleViolation) as err:
        admin.add_skill(ctx(seeded_db), name)
    code, message, problems = refused(err)
    assert (code, problems) == ("rule_violation", ["already_exists"])
    assert message == "The catalogue already has a skill called Piloting"
    assert dict(err.value.problems[0].refs) == {"skill_id": PILOTING}
    assert snapshot(seeded_db) == before


def test_p1_the_same_name_in_another_organisation_is_unrelated(seeded_db):
    skill = admin.add_skill(ctx(seeded_db), "Payload Integration")  # also in Helix's catalogue
    assert skill.org_id == 1
    helix = [s.name for s in admin.list_skills(ctx(seeded_db, SAM))]
    assert helix.count("Payload Integration") == 1


def test_p1_renaming_a_skill_keeps_its_identity(seeded_db):
    start = last_audit_id(seeded_db)
    skill = admin.update_skill(ctx(seeded_db), SYS_ENG, name="Systems Eng")
    assert (skill.id, skill.name) == (SYS_ENG, "Systems Eng")
    repos = ctx(seeded_db).repos
    assert repos.crew.skills(BEN_ID)[SYS_ENG] == 4
    flight_engineer = repos.missions.slots(GATEWAY)[0]
    assert [(r.skill_id, r.skill_name) for r in flight_engineer.requirements] == [
        (SYS_ENG, "Systems Eng")
    ]
    assert audit_events(seeded_db, start) == [
        (
            1,
            "skill.updated",
            None,
            {
                "skill_id": SYS_ENG,
                "skill_name": "Systems Eng",
                "changes": {"name": ["Systems Engineering", "Systems Eng"]},
            },
        ),
    ]


def test_p1_recategorising_a_skill_keeps_its_name_unless_one_is_given(seeded_db):
    start = last_audit_id(seeded_db)
    skill = admin.update_skill(ctx(seeded_db), GEOLOGY, category="Science")
    assert (skill.name, skill.category) == ("Geology", "Science")
    skill = admin.update_skill(ctx(seeded_db), GEOLOGY, name="Planetary Geology")
    assert (skill.name, skill.category) == ("Planetary Geology", "Science")
    skill = admin.update_skill(ctx(seeded_db), GEOLOGY, category=None)
    assert (skill.name, skill.category) == ("Planetary Geology", None)
    # Each audit event lists only what changed, as [old, new].
    assert [data for _, _, _, data in audit_events(seeded_db, start)] == [
        {"skill_id": GEOLOGY, "skill_name": "Geology", "changes": {"category": [None, "Science"]}},
        {
            "skill_id": GEOLOGY,
            "skill_name": "Planetary Geology",
            "changes": {"name": ["Geology", "Planetary Geology"]},
        },
        {
            "skill_id": GEOLOGY,
            "skill_name": "Planetary Geology",
            "changes": {"category": ["Science", None]},
        },
    ]


def test_p1_renaming_to_another_skills_name_is_refused(seeded_db):
    before = snapshot(seeded_db)
    with pytest.raises(RuleViolation) as err:
        admin.update_skill(ctx(seeded_db), GEOLOGY, name="eva")
    assert refused(err)[2] == ["already_exists"]
    assert err.value.message == "The catalogue already has a skill called EVA"
    assert snapshot(seeded_db) == before


def test_p1_a_skill_can_be_renamed_to_a_different_case_of_its_own_name(seeded_db):
    assert admin.update_skill(ctx(seeded_db), 4, name="Eva").name == "Eva"


def test_p1_an_update_that_changes_nothing_writes_nothing(seeded_db):
    before = snapshot(seeded_db)
    assert admin.update_skill(ctx(seeded_db), GEOLOGY, name="Geology").name == "Geology"
    assert admin.update_skill(ctx(seeded_db), GEOLOGY).name == "Geology"
    assert snapshot(seeded_db) == before


def test_p1_a_blank_skill_name_is_rejected(seeded_db):
    with pytest.raises(InvalidInput):
        admin.add_skill(ctx(seeded_db), "   ")
    with pytest.raises(InvalidInput):
        admin.update_skill(ctx(seeded_db), GEOLOGY, name="")


@pytest.mark.parametrize(
    ("actor", "skill_id"), [(RUTH, 999), (SAM, GEOLOGY)], ids=["missing", "other org"]
)
def test_ac29_a_skill_is_looked_up_before_its_new_name_is_checked(seeded_db, actor, skill_id):
    before = snapshot(seeded_db)
    with pytest.raises(NotFound):
        admin.update_skill(ctx(seeded_db, actor), skill_id, name="  ")
    assert snapshot(seeded_db) == before


@pytest.mark.parametrize(
    ("actor", "user_id"), [(RUTH, 999), (SAM, LEE_ID)], ids=["missing", "other org"]
)
def test_ac29_a_user_is_looked_up_before_the_display_name_is_checked(seeded_db, actor, user_id):
    before = snapshot(seeded_db)
    with pytest.raises(NotFound):
        admin.create_crew_profile(ctx(seeded_db, actor), user_id, display_name="  ")
    assert snapshot(seeded_db) == before


def test_p1_an_unused_skill_can_be_deleted(seeded_db):
    skill = admin.add_skill(ctx(seeded_db), "Robotics")
    start = last_audit_id(seeded_db)
    admin.delete_skill(ctx(seeded_db), skill.id)
    assert skill not in admin.list_skills(ctx(seeded_db))
    assert audit_events(seeded_db, start) == [
        (1, "skill.deleted", None, {"skill_id": skill.id, "skill_name": "Robotics"}),
    ]


def test_p1_a_skill_in_use_cant_be_deleted_and_the_refusal_names_who_uses_it(seeded_db):
    before = snapshot(seeded_db)
    with pytest.raises(RuleViolation) as err:
        admin.delete_skill(ctx(seeded_db), GEOLOGY)
    code, message, problems = refused(err)
    assert (code, problems) == ("rule_violation", ["skill_in_use"])
    assert err.value.problems[0].message == (
        "Geology can't be deleted because Hana Sato has it and Asteroid Survey (Geologist)"
        " requires it"
    )
    assert dict(err.value.problems[0].refs) == {
        "skill_id": GEOLOGY,
        "crew_profile_ids": [HANA],
        "mission_ids": [ASTEROID],
    }
    assert snapshot(seeded_db) == before


def test_p1_a_skill_held_by_crew_only_cant_be_deleted(seeded_db):
    with pytest.raises(RuleViolation) as err:
        admin.delete_skill(ctx(seeded_db), 2)  # Leadership: Ana, Eli, Fay; Commander slot too
    assert err.value.message == (
        "Leadership can't be deleted because Ana Okafor, Eli Novak and Fay Moreau have it"
        " and Lunar Gateway Resupply (Commander) requires it"
    )
    skill = admin.add_skill(ctx(seeded_db), "Robotics")
    seeded_db.execute(
        "INSERT INTO crew_skills(org_id, crew_profile_id, skill_id, level, updated_by_id)"
        " VALUES (1, ?, ?, 2, 1)",
        (FAY, skill.id),
    )
    with pytest.raises(RuleViolation) as err:
        admin.delete_skill(ctx(seeded_db), skill.id)
    assert err.value.message == "Robotics can't be deleted because Fay Moreau has it"


def test_p1_a_skill_required_by_a_removed_slot_still_cant_be_deleted(seeded_db):
    skill = admin.add_skill(ctx(seeded_db), "Robotics")
    slot = make_slot(seeded_db, 1, GATEWAY, name="Robot Wrangler", position=9)
    seeded_db.execute(
        "INSERT INTO slot_requirements(org_id, slot_id, skill_id, min_level) VALUES (1, ?, ?, 2)",
        (slot, skill.id),
    )
    seeded_db.execute(
        "UPDATE slots SET removed_at = '2027-01-01T00:00:00.000Z' WHERE id = ?", (slot,)
    )
    with pytest.raises(RuleViolation) as err:
        admin.delete_skill(ctx(seeded_db), skill.id)
    assert err.value.message == (
        "Robotics can't be deleted because Lunar Gateway Resupply (Robot Wrangler) requires it"
    )


def test_p1_the_refusal_names_several_slots(seeded_db):
    # Systems Engineering: Ana, Ben, Chen, Gus have it; five Aurora slots require it,
    # listed by mission start date.
    with pytest.raises(RuleViolation) as err:
        admin.delete_skill(ctx(seeded_db), SYS_ENG)
    assert err.value.message == (
        "Systems Engineering can't be deleted because Ana Okafor, Ben Ito, Chen Wu and Gus Patel"
        " have it and Mars Analog Habitat (Engineer), Orbital Telescope Service (Engineer),"
        " Station Reboost (Engineer), Lunar Gateway Resupply (Flight Engineer) and"
        " Deep Space Comms Upgrade (Engineer) require it"
    )


def test_t1_skill_usage_lookups_are_scoped_to_the_organisation(seeded_db):
    aurora, helix = ctx(seeded_db).repos.skills, ctx(seeded_db, SAM).repos.skills
    assert [h.name for h in helix.holders(HELIX_PILOTING)] == ["Kai Tanaka"]
    assert aurora.holders(HELIX_PILOTING) == []
    assert aurora.required_by(HELIX_PILOTING) == []
    assert helix.holders(PILOTING) == helix.required_by(PILOTING) == []
    assert [(r.mission_name, r.slot_name) for r in aurora.required_by(PILOTING)] == [
        ("Lunar Gateway Resupply", "Commander"),
        ("Asteroid Survey", "Pilot"),
    ]
