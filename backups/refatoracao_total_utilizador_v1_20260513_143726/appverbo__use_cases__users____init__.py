"""User-related application use cases."""

from appverbo.use_cases.users.create_user import (
    CreateUserInput,
    CreateUserOutcome,
    normalize_create_user_input_v1,
    normalize_create_user_input,
    execute_create_user,
)
from appverbo.use_cases.users.update_user import (
    UpdateUserInput,
    normalize_update_user_input_v1,
    execute_update_user_v1,
)
from appverbo.use_cases.users.delete_user import execute_delete_user_v1
from appverbo.use_cases.users.get_user_edit_data import (
    execute_get_user_edit_data_v1,
    get_user_edit_defaults,
)
from appverbo.use_cases.users.list_admin_users import execute_list_admin_users_v1
from appverbo.use_cases.users.resolve_user_entity import execute_resolve_user_entity_v1
from appverbo.use_cases.users.user_permissions import execute_get_user_permissions_v1
from appverbo.use_cases.users.user_invites import (
    build_user_invite_token,
    build_user_invite_link,
    send_user_invite_email,
)

__all__ = [
    "CreateUserInput",
    "CreateUserOutcome",
    "normalize_create_user_input_v1",
    "normalize_create_user_input",
    "execute_create_user",
    "UpdateUserInput",
    "normalize_update_user_input_v1",
    "execute_update_user_v1",
    "execute_delete_user_v1",
    "execute_get_user_edit_data_v1",
    "get_user_edit_defaults",
    "execute_list_admin_users_v1",
    "execute_resolve_user_entity_v1",
    "execute_get_user_permissions_v1",
    "build_user_invite_token",
    "build_user_invite_link",
    "send_user_invite_email",
]
