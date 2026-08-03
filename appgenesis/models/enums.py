from __future__ import annotations

from enum import Enum


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

