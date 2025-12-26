import uuid
from datetime import datetime

from pydantic import BaseModel

from common.enums import AccessRequestStatus, AccessAction


class AccessRequestCreate(BaseModel):
    """Схема для создания заявки."""
    user_id: uuid.UUID
    permission_group_id: uuid.UUID
    action: AccessAction


class AccessRequestResponse(BaseModel):
    """Схема ответа с информацией о заявке."""
    id: uuid.UUID
    user_id: uuid.UUID
    permission_group_id: uuid.UUID
    action: AccessAction
    status: AccessRequestStatus
    created_at: datetime
    updated_at: datetime
    rejection_reason: str | None = None

    class Config:
        from_attributes = True


class PermissionGroupRead(BaseModel):
    id: uuid.UUID
    name: str | None = None


class UserPermissionsResponse(BaseModel):
    user_id: uuid.UUID
    permission_groups: list[PermissionGroupRead]
