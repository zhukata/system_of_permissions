import uuid
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app import models, schemas

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post(
    "/permission-groups",
    response_model=schemas.PermissionGroupResponse,
    status_code=201,
)
def create_permission_group(
    payload: schemas.PermissionGroupCreate,
    db: Session = Depends(get_db),
):
    group = models.PermissionGroup(
        id=payload.id or uuid.uuid4(),
        name=payload.name,
        description=payload.description,
    )
    db.add(group)
    db.flush()

    for conflict_id in payload.conflicts_with:
        db.add(
            models.PermissionGroupConflict(
                group_id=group.id,
                conflicts_with_id=conflict_id,
            )
        )
        db.add(
            models.PermissionGroupConflict(
                group_id=conflict_id,
                conflicts_with_id=group.id,
            )
        )

    db.commit()
    db.refresh(group)
    return group


@router.get(
    "/permission-groups",
    response_model=List[schemas.PermissionGroupResponse],
)
def list_permission_groups(db: Session = Depends(get_db)):
    return db.query(models.PermissionGroup).all()
