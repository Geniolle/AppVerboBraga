from typing import TYPE_CHECKING

from appgenesis.models.base import Base, TimestampMixin
from appgenesis.models.department import (
    Department,
    DepartmentMembership,
    DepartmentMembershipOperation,
    DepartmentMembershipRole,
    Role,
)
from appgenesis.models.entity import Entity
from appgenesis.models.enums import (
    DepartmentMembershipStatus,
    MemberEntityStatus,
    MemberStatus,
    UserAccountStatus,
)
from appgenesis.models.member import Member, MemberEntity
from appgenesis.models.modules import (
    AppModule,
    EntityModuleEntitlement,
    SidebarMenuItem,
)
from appgenesis.models.sidebar_menu_setting import SidebarMenuSetting
from appgenesis.models.user import User

if TYPE_CHECKING:
    from appgenesis.models.profile import Profile, UserProfile

__all__ = [
    "Base",
    "TimestampMixin",
    "Department",
    "DepartmentMembership",
    "DepartmentMembershipOperation",
    "DepartmentMembershipRole",
    "Role",
    "Entity",
    "DepartmentMembershipStatus",
    "MemberEntityStatus",
    "MemberStatus",
    "UserAccountStatus",
    "Member",
    "MemberEntity",
    "AppModule",
    "EntityModuleEntitlement",
    "SidebarMenuItem",
    "Profile",
    "UserProfile",
    "SidebarMenuSetting",
    "User",
]


def __getattr__(name: str):
    if name in {"Profile", "UserProfile"}:
        from appgenesis.models.profile import Profile, UserProfile

        return {
            "Profile": Profile,
            "UserProfile": UserProfile,
        }[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
