from fastapi import APIRouter, status

from mission_control.api.deps import Ctx
from mission_control.api.schemas.admin import (
    CrewProfileCreate,
    OrgOut,
    OrgUpdate,
    SkillCreate,
    SkillOut,
    SkillUpdate,
    UserCreate,
    UserOut,
    UserUpdate,
)
from mission_control.api.schemas.common import PathId
from mission_control.api.schemas.crew import CrewProfileOut
from mission_control.services import admin

router = APIRouter(tags=["admin"])


# Organisation


@router.get("/org")
def view_org(ctx: Ctx) -> OrgOut:
    return OrgOut.of(admin.view_organisation(ctx))


@router.patch("/org")
def update_org(body: OrgUpdate, ctx: Ctx) -> OrgOut:
    return OrgOut.of(admin.set_required_approvals(ctx, body.required_approvals))


# Users


@router.get("/users")
def list_users(ctx: Ctx) -> list[UserOut]:
    return [UserOut.of(u) for u in admin.list_users(ctx)]


@router.post("/users", status_code=status.HTTP_201_CREATED)
def create_user(body: UserCreate, ctx: Ctx) -> UserOut:
    return UserOut.of(admin.create_user(ctx, body.email, body.name, body.role, body.password))


@router.patch("/users/{user_id}")
def update_user(user_id: PathId, body: UserUpdate, ctx: Ctx) -> UserOut:
    """Change the role, or deactivate with `active: false`. With neither, the user is returned
    unchanged."""
    if body.role is not None:
        return UserOut.of(admin.change_role(ctx, user_id, body.role))
    if body.active is False:
        return UserOut.of(admin.deactivate_user(ctx, user_id))
    return UserOut.of(admin.view_user(ctx, user_id))


@router.post("/users/{user_id}/crew-profile", status_code=status.HTTP_201_CREATED)
def create_crew_profile(
    user_id: PathId, ctx: Ctx, body: CrewProfileCreate | None = None
) -> CrewProfileOut:
    display_name = body.display_name if body is not None else None
    return CrewProfileOut.of(admin.create_crew_profile(ctx, user_id, display_name))


# Skills


@router.get("/skills")
def list_skills(ctx: Ctx) -> list[SkillOut]:
    return [SkillOut.of(s) for s in admin.list_skills(ctx)]


@router.post("/skills", status_code=status.HTTP_201_CREATED)
def add_skill(body: SkillCreate, ctx: Ctx) -> SkillOut:
    return SkillOut.of(admin.add_skill(ctx, body.name, body.category))


@router.patch("/skills/{skill_id}")
def update_skill(skill_id: PathId, body: SkillUpdate, ctx: Ctx) -> SkillOut:
    if "category" in body.model_fields_set:
        skill = admin.update_skill(ctx, skill_id, name=body.name, category=body.category)
    else:
        skill = admin.update_skill(ctx, skill_id, name=body.name)
    return SkillOut.of(skill)


@router.delete("/skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_skill(skill_id: PathId, ctx: Ctx) -> None:
    admin.delete_skill(ctx, skill_id)
