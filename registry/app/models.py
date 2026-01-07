import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    Boolean,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()


class PermissionGroup(Base):
    __tablename__ = "permission_groups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    conflicts = relationship(
        "PermissionGroupConflict",
        foreign_keys="PermissionGroupConflict.group_id",
        back_populates="group",
        cascade="all, delete-orphan",
    )

    reverse_conflicts = relationship(
        "PermissionGroupConflict",
        foreign_keys="PermissionGroupConflict.conflicts_with_id",
        back_populates="conflicts_with",
        cascade="all, delete-orphan",
    )


class PermissionGroupConflict(Base):
    __tablename__ = "permission_group_conflicts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    group_id = Column(
        UUID(as_uuid=True),
        ForeignKey("permission_groups.id", ondelete="CASCADE"),
        nullable=False,
    )

    conflicts_with_id = Column(
        UUID(as_uuid=True),
        ForeignKey("permission_groups.id", ondelete="CASCADE"),
        nullable=False,
    )

    group = relationship(
        "PermissionGroup",
        foreign_keys=[group_id],
        back_populates="conflicts",
    )

    conflicts_with = relationship(
        "PermissionGroup",
        foreign_keys=[conflicts_with_id],
        back_populates="reverse_conflicts",
    )

    __table_args__ = (
        UniqueConstraint(
            "group_id",
            "conflicts_with_id",
            name="uq_permission_group_conflict",
        ),
    )


class UserPermissionGroup(Base):
    __tablename__ = "user_permission_groups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    group_id = Column(
        UUID(as_uuid=True),
        ForeignKey("permission_groups.id", ondelete="CASCADE"),
        nullable=False,
    )

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    active = Column(Boolean, default=True, nullable=False)

    group = relationship("PermissionGroup")

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "group_id",
            name="uq_user_permission_group",
        ),
    )
