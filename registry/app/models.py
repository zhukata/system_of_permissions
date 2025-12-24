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


class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    permission_groups = relationship("UserPermissionGroup", back_populates="user")


class PermissionGroup(Base):
    __tablename__ = "permission_groups"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    conflicts = relationship(
        "PermissionGroupConflict",
        primaryjoin="PermissionGroup.id==PermissionGroupConflict.group_id",
        back_populates="group",
    )
    reverse_conflicts = relationship(
        "PermissionGroupConflict",
        primaryjoin="PermissionGroup.id==PermissionGroupConflict.conflicts_with_id",
        back_populates="conflicts_with",
    )


class PermissionGroupConflict(Base):
    __tablename__ = "permission_group_conflicts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id = Column(UUID(as_uuid=True), ForeignKey("permission_groups.id"), nullable=False)
    conflicts_with_id = Column(UUID(as_uuid=True), ForeignKey("permission_groups.id"), nullable=False)

    group = relationship("PermissionGroup", foreign_keys=[group_id], back_populates="conflicts")
    conflicts_with = relationship(
        "PermissionGroup", foreign_keys=[conflicts_with_id], back_populates="reverse_conflicts"
    )

    __table_args__ = (
        UniqueConstraint("group_id", "conflicts_with_id", name="uq_conflict_pair"),
    )


class UserPermissionGroup(Base):
    __tablename__ = "user_permission_groups"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    group_id = Column(UUID(as_uuid=True), ForeignKey("permission_groups.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    active = Column(Boolean, default=True, nullable=False)

    user = relationship("User", back_populates="permission_groups")
    group = relationship("PermissionGroup")

    __table_args__ = (
        UniqueConstraint("user_id", "group_id", name="uq_user_group"),
    )

