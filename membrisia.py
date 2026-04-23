from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Optional, List

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# =========================================================
# ENUMS
# =========================================================

class MemberStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class MemberEntityStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    TRANSFERRED = "transferred"


class UserAccountStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKED = "blocked"


class DepartmentMembershipStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    TRANSFERRED = "transferred"


# =========================================================
# BASE MIXIN
# =========================================================

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


# =========================================================
# ENTITY
# =========================================================

class Entity(Base, TimestampMixin):
    __tablename__ = "entities"

    id: Mapped[int] = mapped_column(primary_key=True)
    internal_number: Mapped[Optional[int]] = mapped_column(Integer, unique=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    acronym: Mapped[Optional[str]] = mapped_column(String(30))
    tax_id: Mapped[Optional[str]] = mapped_column(String(40))
    email: Mapped[Optional[str]] = mapped_column(String(150))
    responsible_name: Mapped[Optional[str]] = mapped_column(String(200))
    door_number: Mapped[Optional[str]] = mapped_column(String(30))
    address: Mapped[Optional[str]] = mapped_column(String(255))
    freguesia: Mapped[Optional[str]] = mapped_column(String(120))
    postal_code: Mapped[Optional[str]] = mapped_column(String(30))
    country: Mapped[Optional[str]] = mapped_column(String(120))
    phone: Mapped[Optional[str]] = mapped_column(String(30))
    logo_url: Mapped[Optional[str]] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text)
    profile_scope: Mapped[str] = mapped_column(String(20), nullable=False, default="legado")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    member_links: Mapped[List["MemberEntity"]] = relationship(back_populates="entity")
    departments: Mapped[List["Department"]] = relationship(back_populates="entity")
    roles: Mapped[List["Role"]] = relationship(back_populates="entity")

    __table_args__ = (
        CheckConstraint(
            "profile_scope IN ('owner', 'legado')",
            name="ck_entities_profile_scope",
        ),
    )


# =========================================================
# MEMBER
# =========================================================

class Member(Base, TimestampMixin):
    __tablename__ = "members"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    gender: Mapped[Optional[str]] = mapped_column(String(20))
    birth_date: Mapped[Optional[date]] = mapped_column(Date)

    primary_phone: Mapped[str] = mapped_column(String(30), nullable=False)
    secondary_phone: Mapped[Optional[str]] = mapped_column(String(30))
    email: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)

    address: Mapped[Optional[str]] = mapped_column(String(255))
    city: Mapped[Optional[str]] = mapped_column(String(120))
    freguesia: Mapped[Optional[str]] = mapped_column(String(120))
    postal_code: Mapped[Optional[str]] = mapped_column(String(30))
    whatsapp_verification_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="unknown"
    )
    whatsapp_notice_opt_in: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    whatsapp_last_check_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    whatsapp_last_error: Mapped[Optional[str]] = mapped_column(Text)
    whatsapp_last_wa_id: Mapped[Optional[str]] = mapped_column(String(64))
    whatsapp_last_message_id: Mapped[Optional[str]] = mapped_column(String(128))
    training_discipulado_verbo_vida: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    training_ebvv: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    training_rhema: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    training_escola_ministerial: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    training_escola_missoes: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    training_outros: Mapped[Optional[str]] = mapped_column(String(255))
    profile_custom_fields: Mapped[Optional[str]] = mapped_column(Text)
    marital_status: Mapped[Optional[str]] = mapped_column(String(50))

    baptism_date: Mapped[Optional[date]] = mapped_column(Date)
    photo_url: Mapped[Optional[str]] = mapped_column(Text)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    spouse_name: Mapped[Optional[str]] = mapped_column(String(200))
    children: Mapped[Optional[str]] = mapped_column(Text)
    household: Mapped[Optional[str]] = mapped_column(Text)

    profession: Mapped[Optional[str]] = mapped_column(String(120))
    identification_document: Mapped[Optional[str]] = mapped_column(String(100))
    tax_number: Mapped[Optional[str]] = mapped_column(String(50))

    member_status: Mapped[str] = mapped_column(String(20), nullable=False, default=MemberStatus.ACTIVE.value)
    is_collaborator: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    first_collaboration_date: Mapped[Optional[date]] = mapped_column(Date)

    entity_links: Mapped[List["MemberEntity"]] = relationship(back_populates="member")
    user_account: Mapped[Optional["User"]] = relationship(back_populates="member", uselist=False)

    __table_args__ = (
        CheckConstraint(
            "member_status IN ('active', 'inactive')",
            name="ck_members_member_status",
        ),
    )


# =========================================================
# MEMBER x ENTITY
# =========================================================

class MemberEntity(Base, TimestampMixin):
    __tablename__ = "member_entities"

    id: Mapped[int] = mapped_column(primary_key=True)

    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"), nullable=False)
    entity_id: Mapped[int] = mapped_column(ForeignKey("entities.id"), nullable=False)

    entry_date: Mapped[Optional[date]] = mapped_column(Date)
    exit_date: Mapped[Optional[date]] = mapped_column(Date)
    exit_or_transfer_reason: Mapped[Optional[str]] = mapped_column(Text)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=MemberEntityStatus.ACTIVE.value
    )

    member: Mapped["Member"] = relationship(back_populates="entity_links")
    entity: Mapped["Entity"] = relationship(back_populates="member_links")
    department_memberships: Mapped[List["DepartmentMembership"]] = relationship(
        back_populates="member_entity"
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'inactive', 'transferred')",
            name="ck_member_entities_status",
        ),
    )


# =========================================================
# USER ACCOUNT
# =========================================================

class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"), nullable=False, unique=True)
    login_email: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)

    account_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=UserAccountStatus.PENDING.value
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_by_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))

    member: Mapped["Member"] = relationship(back_populates="user_account")
    profiles: Mapped[List["UserProfile"]] = relationship(back_populates="user")

    __table_args__ = (
        CheckConstraint(
            "account_status IN ('pending', 'active', 'inactive', 'blocked')",
            name="ck_users_account_status",
        ),
    )


# =========================================================
# GLOBAL PROFILES
# =========================================================

class Profile(Base, TimestampMixin):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    users: Mapped[List["UserProfile"]] = relationship(back_populates="profile")


class UserProfile(Base, TimestampMixin):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    profile_id: Mapped[int] = mapped_column(ForeignKey("profiles.id"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    user: Mapped["User"] = relationship(back_populates="profiles")
    profile: Mapped["Profile"] = relationship(back_populates="users")

    __table_args__ = (
        UniqueConstraint("user_id", "profile_id", name="uq_user_profiles"),
    )


# =========================================================
# DEPARTMENTS
# =========================================================

class Department(Base, TimestampMixin):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(primary_key=True)
    entity_id: Mapped[int] = mapped_column(ForeignKey("entities.id"), nullable=False)

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    entity: Mapped["Entity"] = relationship(back_populates="departments")
    memberships: Mapped[List["DepartmentMembership"]] = relationship(back_populates="department")

    __table_args__ = (
        UniqueConstraint("entity_id", "name", name="uq_departments_entity_name"),
    )


# =========================================================
# ROLES (BY ENTITY)
# =========================================================

class Role(Base, TimestampMixin):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    entity_id: Mapped[int] = mapped_column(ForeignKey("entities.id"), nullable=False)

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    entity: Mapped["Entity"] = relationship(back_populates="roles")
    role_assignments: Mapped[List["DepartmentMembershipRole"]] = relationship(
        back_populates="role"
    )

    __table_args__ = (
        UniqueConstraint("entity_id", "name", name="uq_roles_entity_name"),
    )


# =========================================================
# MEMBER x DEPARTMENT
# =========================================================

class DepartmentMembership(Base, TimestampMixin):
    __tablename__ = "department_memberships"

    id: Mapped[int] = mapped_column(primary_key=True)

    member_entity_id: Mapped[int] = mapped_column(ForeignKey("member_entities.id"), nullable=False)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"), nullable=False)

    entry_date: Mapped[Optional[date]] = mapped_column(Date)
    exit_date: Mapped[Optional[date]] = mapped_column(Date)
    exit_reason: Mapped[Optional[str]] = mapped_column(Text)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=DepartmentMembershipStatus.ACTIVE.value
    )

    direct_supervisor_member_id: Mapped[Optional[int]] = mapped_column(ForeignKey("members.id"))

    member_entity: Mapped["MemberEntity"] = relationship(back_populates="department_memberships")
    department: Mapped["Department"] = relationship(back_populates="memberships")
    operation: Mapped[Optional["DepartmentMembershipOperation"]] = relationship(
        back_populates="department_membership",
        uselist=False,
    )
    roles: Mapped[List["DepartmentMembershipRole"]] = relationship(
        back_populates="department_membership"
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'inactive', 'suspended', 'transferred')",
            name="ck_department_memberships_status",
        ),
    )


# =========================================================
# DEPARTMENT MEMBERSHIP OPERATIONAL DATA
# =========================================================

class DepartmentMembershipOperation(Base, TimestampMixin):
    __tablename__ = "department_membership_operations"

    id: Mapped[int] = mapped_column(primary_key=True)
    department_membership_id: Mapped[int] = mapped_column(
        ForeignKey("department_memberships.id"),
        nullable=False,
        unique=True,
    )

    internal_priority: Mapped[Optional[int]] = mapped_column(Integer)
    eligible_for_auto_schedule: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    leader_internal_note: Mapped[Optional[str]] = mapped_column(Text)
    last_served_date: Mapped[Optional[date]] = mapped_column(Date)
    monthly_schedule_limit: Mapped[Optional[int]] = mapped_column(Integer)
    allow_same_day_schedule: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    temporarily_blocked_for_schedule: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    temporary_block_reason: Mapped[Optional[str]] = mapped_column(Text)

    department_membership: Mapped["DepartmentMembership"] = relationship(
        back_populates="operation"
    )


# =========================================================
# MEMBER x DEPARTMENT x ROLE
# =========================================================

class DepartmentMembershipRole(Base, TimestampMixin):
    __tablename__ = "department_membership_roles"

    id: Mapped[int] = mapped_column(primary_key=True)

    department_membership_id: Mapped[int] = mapped_column(
        ForeignKey("department_memberships.id"),
        nullable=False,
    )
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False)

    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    included_in_schedule: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    monthly_role_limit: Mapped[Optional[int]] = mapped_column(Integer)

    start_date: Mapped[Optional[date]] = mapped_column(Date)
    end_date: Mapped[Optional[date]] = mapped_column(Date)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    department_membership: Mapped["DepartmentMembership"] = relationship(
        back_populates="roles"
    )
    role: Mapped["Role"] = relationship(back_populates="role_assignments")
