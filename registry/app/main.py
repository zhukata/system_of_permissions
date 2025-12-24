import uuid
from typing import List

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import SessionLocal
from app import models, schemas

app = FastAPI(title=settings.app_name)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
def on_startup():
    # Простое создание схемы без Alembic для демо
    models.Base.metadata.create_all(bind=SessionLocal().bind)


# Users
@app.post("/users", response_model=schemas.UserResponse, status_code=201)
def create_user(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    user = models.User(id=payload.id or uuid.uuid4(), email=payload.email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.get("/users/{user_id}", response_model=schemas.UserResponse)
def get_user(user_id: uuid.UUID, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.get("/users/{user_id}/permission-groups", response_model=List[dict])
def get_user_permission_groups(user_id: uuid.UUID, db: Session = Depends(get_db)):
    assignments = (
        db.query(models.UserPermissionGroup)
        .filter(
            models.UserPermissionGroup.user_id == user_id,
            models.UserPermissionGroup.active.is_(True),
        )
        .all()
    )
    groups = []
    for a in assignments:
        groups.append({"id": str(a.group_id), "name": a.group.name if a.group else None})
    return groups


# Permission groups
@app.post(
    "/permission-groups",
    response_model=schemas.PermissionGroupResponse,
    status_code=201,
)
def create_permission_group(
    payload: schemas.PermissionGroupCreate, db: Session = Depends(get_db)
):
    group = models.PermissionGroup(
        id=payload.id or uuid.uuid4(),
        name=payload.name,
        description=payload.description,
    )
    db.add(group)
    db.flush()

    # Конфликты (двунаправленно)
    for conflict_id in payload.conflicts_with:
        conflict = models.PermissionGroupConflict(
            group_id=group.id,
            conflicts_with_id=conflict_id,
        )
        reverse_conflict = models.PermissionGroupConflict(
            group_id=conflict_id,
            conflicts_with_id=group.id,
        )
        db.add(conflict)
        db.add(reverse_conflict)

    db.commit()
    db.refresh(group)
    return group


@app.get("/permission-groups", response_model=List[schemas.PermissionGroupResponse])
def list_permission_groups(db: Session = Depends(get_db)):
    return db.query(models.PermissionGroup).all()


@app.post("/permission-groups/check-conflicts", response_model=schemas.ConflictCheckResponse)
def check_conflicts(payload: schemas.ConflictCheckRequest, db: Session = Depends(get_db)):
    new_group_id = payload.new_group_id
    current_ids = payload.user_current_groups

    # Ищем конфликт: есть ли запись (group_id in current_ids and conflicts_with_id = new)
    conflict = (
        db.query(models.PermissionGroupConflict)
        .filter(
            models.PermissionGroupConflict.group_id.in_(current_ids),
            models.PermissionGroupConflict.conflicts_with_id == new_group_id,
        )
        .first()
    )
    if conflict:
        return schemas.ConflictCheckResponse(
            has_conflict=True, reason="Конфликтующая группа прав"
        )
    return schemas.ConflictCheckResponse(has_conflict=False, reason=None)


# Assignments
@app.post(
    "/users/{user_id}/permission-groups/{group_id}/grant",
    response_model=schemas.PermissionGroupAssignmentResponse,
)
def grant_group(user_id: uuid.UUID, group_id: uuid.UUID, db: Session = Depends(get_db)):
    # Проверяем, есть ли уже
    existing = (
        db.query(models.UserPermissionGroup)
        .filter(
            models.UserPermissionGroup.user_id == user_id,
            models.UserPermissionGroup.group_id == group_id,
        )
        .one_or_none()
    )
    if existing:
        existing.active = True
    else:
        assignment = models.UserPermissionGroup(user_id=user_id, group_id=group_id)
        db.add(assignment)
    db.commit()
    return schemas.PermissionGroupAssignmentResponse(
        success=True, user_id=user_id, group_id=group_id
    )


@app.post(
    "/users/{user_id}/permission-groups/{group_id}/revoke",
    response_model=schemas.PermissionGroupAssignmentResponse,
)
def revoke_group(user_id: uuid.UUID, group_id: uuid.UUID, db: Session = Depends(get_db)):
    assignment = (
        db.query(models.UserPermissionGroup)
        .filter(
            models.UserPermissionGroup.user_id == user_id,
            models.UserPermissionGroup.group_id == group_id,
        )
        .one_or_none()
    )
    if assignment:
        assignment.active = False
        db.commit()
    return schemas.PermissionGroupAssignmentResponse(
        success=True, user_id=user_id, group_id=group_id
    )

