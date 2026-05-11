from __future__ import annotations

from appverbo.admin_subprocesses.utilizador.common import (
    ensure_not_last_active_admin_for_member_v1,
    get_active_entity_ids_for_member_v1,
    has_other_active_admin_for_entity_v1,
    is_admin_profile_v1,
    member_is_within_permissions_v1,
    redirect_admin_users_v1,
    redirect_login_required_v1,
)
from appverbo.admin_subprocesses.utilizador.config import UTILIZADOR_CONFIG
from appverbo.admin_subprocesses.utilizador.create_service import (
    CreateUserInput,
    CreateUserOutcome,
    execute_create_user,
    normalize_create_user_input,
    normalize_create_user_input_v1,
)
from appverbo.admin_subprocesses.utilizador.delete_service import execute_delete_user_v1
from appverbo.admin_subprocesses.utilizador.resend_service import (
    execute_generate_user_invite_v1,
    execute_resend_user_invite_v1,
)
from appverbo.admin_subprocesses.utilizador.service import (
    UpdateUserInput,
    execute_update_user_v1,
    normalize_update_user_input_v1,
)


# ###################################################################################
# (1) EXPORTS OFICIAIS DO SUBPROCESSO UTILIZADOR
# ###################################################################################

__all__ = [
    "UTILIZADOR_CONFIG",
    "CreateUserInput",
    "CreateUserOutcome",
    "UpdateUserInput",
    "ensure_not_last_active_admin_for_member_v1",
    "execute_create_user",
    "execute_delete_user_v1",
    "execute_generate_user_invite_v1",
    "execute_resend_user_invite_v1",
    "execute_update_user_v1",
    "get_active_entity_ids_for_member_v1",
    "has_other_active_admin_for_entity_v1",
    "is_admin_profile_v1",
    "member_is_within_permissions_v1",
    "normalize_create_user_input",
    "normalize_create_user_input_v1",
    "normalize_update_user_input_v1",
    "redirect_admin_users_v1",
    "redirect_login_required_v1",
]