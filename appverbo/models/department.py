from __future__ import annotations

from datetime import date
from typing import List, Optional

from sqlalchemy import Boolean, CheckConstraint, Date, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from appverbo.models.base import Base, TimestampMixin
from appverbo.models.enums import DepartmentMembershipStatus


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

