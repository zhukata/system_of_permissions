import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class AccessAction(str, Enum):
    GRANT = "GRANT"
    REVOKE = "REVOKE"


class AccessRequestStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


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


class UserPermissionsResponse(BaseModel):
    """Схема для получения прав пользователя (read-модель)."""
    user_id: uuid.UUID
    permission_groups: list[dict]  # Будет заполняться из Identity+Catalog Service

