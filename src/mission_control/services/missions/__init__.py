"""Missions: viewing them, creating them, editing their name, dates and slots, handing them to
another Lead, and completing or cancelling them.

Every change runs inside one write transaction, in this order:
1. find the mission and its slot (missing, hidden or another organisation's is NotFound);
2. check permission (Forbidden);
3. check the mission's state with `touch_for_change` (StateConflict);
4. find the other records named, such as the owner or the skills (NotFound);
5. check the input (InvalidInput, listing every mistake);
6. check the rules (RuleViolation);
7. write and audit.

Permission comes before the lookups in step 4, so a refused caller can't learn whether a user or
skill exists. A Pending mission whose dates, slots or owner change goes back to Draft and its
approval round stops counting; that return is audited with the change that caused it. A new name
alone leaves it Pending.

Modules: `queries` (list, view), `changes` (create, rename or move, transfer), `slots` (add,
edit, replace requirements, remove), `lifecycle` (complete, cancel), with `inputs`, `rules`,
`views` and `loading` behind them. Completing and cancelling don't go through `touch_for_change`:
they're allowed on an Active mission, and check their own state.
"""

from mission_control.services.missions.changes import (
    create_mission,
    transfer_ownership,
    update_mission,
)
from mission_control.services.missions.inputs import SlotInput
from mission_control.services.missions.lifecycle import cancel_mission, complete_mission
from mission_control.services.missions.queries import get_mission, list_missions
from mission_control.services.missions.slots import (
    add_slot,
    remove_slot,
    replace_requirements,
    update_slot,
)
from mission_control.services.missions.views import (
    ApprovalView,
    AssignmentView,
    MissionListItem,
    MissionView,
    SlotView,
)

__all__ = [
    "ApprovalView",
    "AssignmentView",
    "MissionListItem",
    "MissionView",
    "SlotInput",
    "SlotView",
    "add_slot",
    "cancel_mission",
    "complete_mission",
    "create_mission",
    "get_mission",
    "list_missions",
    "remove_slot",
    "replace_requirements",
    "transfer_ownership",
    "update_mission",
    "update_slot",
]
