"""The full action x role x relationship table. This test is the source of truth for who may do
what (design §4). Each row: action, the relationship being tested, and the outcome for
Director, Lead and Crew. "ok" means allowed; anything else is the expected Forbidden code."""

import pytest

from mission_control.domain.enums import Role
from mission_control.domain.errors import Forbidden
from mission_control.domain.permissions import Action, Actor, Context, authorize, can

ME, OTHER, CREATOR = 1, 2, 3
D, L, C = Role.DIRECTOR, Role.LEAD, Role.CREW

# Relationship contexts, all seen from the actor ME.
NONE = Context()
SELF = Context(target_user_id=ME)
NOT_SELF = Context(target_user_id=OTHER)
OWNER = Context(owner_id=ME, created_by_id=CREATOR)
NOT_OWNER = Context(owner_id=OTHER, created_by_id=CREATOR)
ON_MISSION = Context(owner_id=OTHER, created_by_id=CREATOR, rostered_user_ids=frozenset({ME}))
CREATED_BY_ME = Context(owner_id=OTHER, created_by_id=ME)
FOR_SELF = Context(owner_id=ME)
FOR_OTHER = Context(owner_id=OTHER)

R, NO = "role_forbidden", "not_owner"

TABLE = [
    # Administration
    (Action.MANAGE_ORG, NONE, "ok", R, R),
    (Action.MANAGE_SKILLS, NONE, "ok", R, R),
    (Action.LIST_SKILLS, NONE, "ok", "ok", R),
    (Action.CHANGE_OWN_PASSWORD, NONE, "ok", "ok", "ok"),
    # Crew profiles
    (Action.VIEW_CREW, SELF, "ok", "ok", "ok"),
    (Action.VIEW_CREW, NOT_SELF, "ok", "ok", R),
    (Action.VIEW_ASSIGNMENT_HISTORY, SELF, "ok", "ok", "ok"),
    (Action.VIEW_ASSIGNMENT_HISTORY, NOT_SELF, "ok", "ok", R),
    (Action.VIEW_UNAVAILABILITY_REASON, SELF, "ok", "ok", "ok"),
    (Action.VIEW_UNAVAILABILITY_REASON, NOT_SELF, "ok", R, R),
    (Action.EDIT_OWN_PROFILE, SELF, "ok", "ok", "ok"),
    (Action.EDIT_OWN_PROFILE, NOT_SELF, NO, NO, NO),
    (Action.SET_SKILL_LEVEL, NOT_SELF, "ok", "ok", R),
    (Action.SET_SKILL_LEVEL, SELF, "self_skill_edit", "self_skill_edit", R),
    # Missions: viewing
    (Action.VIEW_MISSION, NOT_OWNER, "ok", "ok", R),
    (Action.VIEW_MISSION, ON_MISSION, "ok", "ok", "ok"),
    # Missions: creating
    (Action.CREATE_MISSION, FOR_OTHER, "ok", NO, R),
    (Action.CREATE_MISSION, FOR_SELF, "ok", "ok", R),
    # Missions: owner-only work
    (Action.EDIT_MISSION, OWNER, R, "ok", R),
    (Action.EDIT_MISSION, NOT_OWNER, R, NO, R),
    (Action.PROPOSE_CREW, OWNER, R, "ok", R),
    (Action.PROPOSE_CREW, NOT_OWNER, R, NO, R),
    (Action.REMOVE_CREW, OWNER, R, "ok", R),
    (Action.REMOVE_CREW, NOT_OWNER, R, NO, R),
    (Action.APPLY_MATCH, OWNER, R, "ok", R),
    (Action.APPLY_MATCH, NOT_OWNER, R, NO, R),
    (Action.SUBMIT, OWNER, R, "ok", R),
    (Action.SUBMIT, NOT_OWNER, R, NO, R),
    # Missions: owner or Director
    (Action.PREVIEW_MATCH, OWNER, "ok", "ok", R),
    (Action.PREVIEW_MATCH, NOT_OWNER, "ok", NO, R),
    (Action.COMPLETE, OWNER, "ok", "ok", R),
    (Action.COMPLETE, NOT_OWNER, "ok", NO, R),
    (Action.CANCEL, OWNER, "ok", "ok", R),
    (Action.CANCEL, NOT_OWNER, "ok", NO, R),
    # Missions: Director only
    (Action.TRANSFER_OWNERSHIP, NOT_OWNER, "ok", R, R),
    (Action.APPROVE, NOT_OWNER, "ok", R, R),
    (Action.APPROVE, CREATED_BY_ME, "approver_is_creator", R, R),
    (Action.APPROVE, ON_MISSION, "approver_is_rostered", R, R),
    (Action.REJECT, NOT_OWNER, "ok", R, R),
    (Action.REJECT, CREATED_BY_ME, "approver_is_creator", R, R),
    (Action.REJECT, ON_MISSION, "approver_is_rostered", R, R),
    # Assignments: only the assignee responds
    (Action.RESPOND_TO_ASSIGNMENT, SELF, "ok", "ok", "ok"),
    (Action.RESPOND_TO_ASSIGNMENT, NOT_SELF, NO, NO, NO),
]

CASES = [
    pytest.param(action, ctx, role, expected, id=f"{action.value}-{role.value}-{i}")
    for i, (action, ctx, *outcomes) in enumerate(TABLE)
    for role, expected in zip((D, L, C), outcomes, strict=True)
]


@pytest.mark.parametrize("action, ctx, role, expected", CASES)
def test_permission_table(action, ctx, role, expected):
    actor = Actor(user_id=ME, org_id=10, role=role, crew_profile_id=50)
    if expected == "ok":
        authorize(actor, action, ctx)
        assert can(actor, action, ctx)
    else:
        with pytest.raises(Forbidden) as err:
            authorize(actor, action, ctx)
        assert err.value.code == expected
        assert not can(actor, action, ctx)


def test_every_action_appears_in_the_table():
    assert {row[0] for row in TABLE} == set(Action)


def test_ac23_ana_cannot_change_her_own_skills_but_lee_can_change_hers():
    ana = Actor(user_id=6, org_id=1, role=L, crew_profile_id=6)
    lee = Actor(user_id=4, org_id=1, role=L, crew_profile_id=None)
    with pytest.raises(Forbidden):
        authorize(ana, Action.SET_SKILL_LEVEL, Context(target_user_id=6))
    authorize(lee, Action.SET_SKILL_LEVEL, Context(target_user_id=6))


def test_ac7_after_transfer_the_new_owner_can_edit_and_the_previous_owner_cannot():
    lee = Actor(user_id=4, org_id=1, role=L, crew_profile_id=None)
    nora = Actor(user_id=5, org_id=1, role=L, crew_profile_id=None)
    after = Context(owner_id=nora.user_id, created_by_id=1)
    authorize(nora, Action.EDIT_MISSION, after)
    with pytest.raises(Forbidden) as err:
        authorize(lee, Action.EDIT_MISSION, after)
    assert err.value.code == "not_owner"


def test_forbidden_carries_a_readable_message():
    crew = Actor(user_id=ME, org_id=1, role=C, crew_profile_id=1)
    with pytest.raises(Forbidden) as err:
        authorize(crew, Action.MANAGE_ORG, NONE)
    assert err.value.message


# Regression: refusal messages read as natural sentences

LEAD_OWNS_OTHER = Context(owner_id=OTHER, created_by_id=CREATOR)

MESSAGES = [
    (C, Action.SET_SKILL_LEVEL, NOT_SELF, "Crew can't change skill levels"),
    (L, Action.MANAGE_ORG, NONE, "Leads can't manage the organisation"),
    (D, Action.EDIT_MISSION, OWNER, "Directors can't edit missions"),
    (L, Action.APPROVE, NOT_OWNER, "Leads can't approve missions"),
    (C, Action.LIST_SKILLS, NONE, "Crew can't view the skill catalogue"),
    (L, Action.EDIT_MISSION, LEAD_OWNS_OTHER, "Only the mission's owner can edit this mission"),
    (L, Action.SUBMIT, LEAD_OWNS_OTHER, "Only the mission's owner can submit this mission"),
    (L, Action.CANCEL, LEAD_OWNS_OTHER, "Only the owner or a Director can cancel this mission"),
    (
        L,
        Action.PREVIEW_MATCH,
        LEAD_OWNS_OTHER,
        "Only the owner or a Director can preview matching for this mission",
    ),
    (L, Action.CREATE_MISSION, FOR_OTHER, "Leads can only create missions they own"),
    (C, Action.VIEW_CREW, NOT_SELF, "Crew can only view their own profile"),
    (
        C,
        Action.VIEW_ASSIGNMENT_HISTORY,
        NOT_SELF,
        "Crew can only view their own assignment history",
    ),
    (
        L,
        Action.VIEW_UNAVAILABILITY_REASON,
        NOT_SELF,
        "Only Directors can see other people's unavailability reasons",
    ),
    (C, Action.VIEW_MISSION, NOT_OWNER, "Crew can only view missions they're on"),
    (L, Action.EDIT_OWN_PROFILE, NOT_SELF, "You can only edit your own profile and availability"),
    (D, Action.RESPOND_TO_ASSIGNMENT, NOT_SELF, "You can only respond to your own assignments"),
    (L, Action.SET_SKILL_LEVEL, SELF, "You can't change your own skill levels"),
]


@pytest.mark.parametrize("role, action, ctx, message", MESSAGES)
def test_refusal_messages_read_naturally(role, action, ctx, message):
    with pytest.raises(Forbidden) as err:
        authorize(Actor(user_id=ME, org_id=1, role=role, crew_profile_id=1), action, ctx)
    assert err.value.message == message


def test_every_action_has_a_phrase_for_role_refusals():
    from mission_control.domain.permissions import ROLE_PHRASE

    assert set(ROLE_PHRASE) == set(Action)
