import uuid
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app import models, schemas

router = APIRouter(prefix="/internal", tags=["internal"])


@router.get(
    "/users/{user_id}/permission-groups",
    response_model=List[schemas.PermissionGroupShort],
)
def get_user_permission_groups(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    rows = (
        db.query(models.UserPermissionGroup)
        .filter(
            models.UserPermissionGroup.user_id == user_id,
            models.UserPermissionGroup.active.is_(True),
        )
        .all()
    )
    return [
        schemas.PermissionGroupShort(
            id=row.group.id,
            name=row.group.name,
        )
        for row in rows
    ]


@router.post(
    "/permission-groups/check-conflicts",
    response_model=schemas.ConflictCheckResponse,
)
def check_conflicts(
    payload: schemas.ConflictCheckRequest,
    db: Session = Depends(get_db),
):
    conflict = (
        db.query(models.PermissionGroupConflict)
        .filter(
            models.PermissionGroupConflict.group_id.in_(
                payload.user_current_groups
            ),
            models.PermissionGroupConflict.conflicts_with_id
            == payload.new_group_id,
        )
        .first()
    )

    if conflict:
        return schemas.ConflictCheckResponse(
            has_conflict=True,
            reason="Permission group conflict",
        )

    return schemas.ConflictCheckResponse(has_conflict=False)


@router.post("/users/{user_id}/permission-groups/{group_id}/grant")
def grant_group(
    user_id: uuid.UUID,
    group_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    row = (
        db.query(models.UserPermissionGroup)
        .filter_by(user_id=user_id, group_id=group_id)
        .one_or_none()
    )

    if row:
        row.active = True
    else:
        db.add(
            models.UserPermissionGroup(
                user_id=user_id,
                group_id=group_id,
            )
        )

    db.commit()
    return {"success": True}


@router.post("/users/{user_id}/permission-groups/{group_id}/revoke")
def revoke_group(
    user_id: uuid.UUID,
    group_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    row = (
        db.query(models.UserPermissionGroup)
        .filter_by(user_id=user_id, group_id=group_id)
        .one_or_none()
    )

    if row:
        row.active = False
        db.commit()

    return {"success": True}
