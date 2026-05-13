
from __future__ import annotations

from appverbo.repositories.member_entity_repository import get_primary_entity_for_member
from appverbo.use_cases.users.resolve_user_entity import (
    extract_email_domain_v1,
    resolve_entity_from_user_email_v1,
)
from appverbo.use_cases.users.user_permissions import (
    ensure_not_last_active_admin_for_member_v1,
    is_admin_profile_v1,
    member_is_within_permissions_v1,
)


_extract_email_domain = extract_email_domain_v1
_resolve_entity_from_user_email = resolve_entity_from_user_email_v1
_get_primary_entity_for_member = get_primary_entity_for_member
_member_is_within_permissions = member_is_within_permissions_v1
_is_admin_profile = is_admin_profile_v1
_ensure_not_last_active_admin_for_member = ensure_not_last_active_admin_for_member_v1


def _get_primary_entity_name_for_member(session, member_id: int) -> str:
    _, entity_name = get_primary_entity_for_member(session, int(member_id))
    return entity_name
