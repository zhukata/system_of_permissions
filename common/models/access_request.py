import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, String
from common.db.base import Base
from sqlalchemy.dialects.postgresql import UUID

from common.enums import AccessAction, AccessRequestStatus


class AccessRequest(Base):
    """
    Модель заявки на доступ.
    
    ARS хранит только заявки и их статусы.
    Вся бизнес-логика (конфликты, права) - в Identity+Catalog Service.
    """
    __tablename__ = "access_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    permission_group_id = Column(UUID(as_uuid=True), nullable=False)
    action = Column(Enum(AccessAction), nullable=False)
    status = Column(
        Enum(AccessRequestStatus),
        nullable=False,
        default=AccessRequestStatus.PENDING,
        index=True,
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    # Опционально: причина отклонения
    rejection_reason = Column(String, nullable=True)
