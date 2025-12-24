import uuid
from datetime import datetime
from pydantic import BaseModel


class UserCreate(BaseModel):
    id: uuid.UUID | None = None
    email: str | None = None


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class PermissionGroupCreate(BaseModel):
    id: uuid.UUID | None = None
    name: str
    description: str | None = None
    conflicts_with: list[uuid.UUID] = []


class PermissionGroupResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None

    class Config:
        from_attributes = True


class ConflictCheckRequest(BaseModel):
    user_current_groups: list[uuid.UUID]
    new_group_id: uuid.UUID


class ConflictCheckResponse(BaseModel):
    has_conflict: bool
    reason: str | None = None


class PermissionGroupAssignmentResponse(BaseModel):
    success: bool
    user_id: uuid.UUID
    group_id: uuid.UUID

