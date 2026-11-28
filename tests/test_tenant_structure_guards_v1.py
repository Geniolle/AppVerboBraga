"""Estrutura partilhada (menus, sessoes, entidades) so pode ser mudada pela gestora do tenant (owner).

Um utilizador com system_type 'owner' ligado so a uma entidade legado passa em is_admin_user,
mas nao tem can_manage_tenant_structure: nao pode mexer no que e de todas as entidades.
"""

from unittest.mock import patch
from urllib.parse import unquote_plus

from starlette.requests import Request

import appgenesis.routes.entities.delete_handler as entity_delete_module
import appgenesis.routes.profile.handlers.menu_subprocess as menu_module
import appgenesis.routes.profile.handlers.sidebar_sections as sections_module
import appgenesis.routes.profile.process_settings.common as settings_common

LEGACY_ADMIN = {"id": 4, "login_email": "admin@legado.test", "full_name": "Admin"}
LEGACY_PERMS = {
    "is_admin": True,
    "can_manage_tenant_structure": False,
    "can_manage_all_entities": False,
    "selected_entity_id": 1,
    "allowed_entity_ids": {1},
    "allowed_structure_entity_ids": {1},
    "allowed_data_entity_ids": {1},
}
OWNER_PERMS = {**LEGACY_PERMS, "can_manage_tenant_structure": True, "can_manage_all_entities": True}


class _Session:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _request(path: str) -> Request:
    return Request({"type": "http", "method": "POST", "path": path, "headers": []})


def _guard_patches(perms):
    return (
        patch.object(settings_common, "get_current_user", return_value=LEGACY_ADMIN),
        patch.object(settings_common, "is_admin_user", return_value=True),
        patch.object(settings_common, "get_session_entity_id", return_value=1),
        patch.object(settings_common, "get_user_entity_permissions", return_value=perms),
    )


def test_legacy_admin_cannot_create_or_delete_shared_menus():
    p1, p2, p3, p4 = _guard_patches(LEGACY_PERMS)
    with p1, p2, p3, p4, patch.object(menu_module, "SessionLocal", _Session), patch.object(
        menu_module, "get_current_user", return_value=LEGACY_ADMIN
    ), patch.object(menu_module, "create_sidebar_menu_setting") as create_mock, patch.object(
        menu_module, "delete_sidebar_menu_setting"
    ) as delete_mock:
        saved = menu_module.menu_subprocess_save_handler_v1(
            request=_request("/settings/menu/menu-save"),
            menu_label="Novo",
            subprocess_return_url="/users/new?menu=sessoes",
        )
        deleted = menu_module.menu_subprocess_delete_handler_v1(
            request=_request("/settings/menu/menu-delete"),
            menu_key="geral",
            subprocess_return_url="/users/new?menu=sessoes",
        )
    assert create_mock.call_count == 0 and delete_mock.call_count == 0
    for response in (saved, deleted):
        assert response.status_code == 303
        assert "Apenas Owner" in unquote_plus(response.headers["location"])


def test_owner_still_creates_shared_menu():
    p1, p2, p3, p4 = _guard_patches(OWNER_PERMS)
    with p1, p2, p3, p4, patch.object(menu_module, "SessionLocal", _Session), patch.object(
        menu_module, "get_current_user", return_value=LEGACY_ADMIN
    ), patch.object(menu_module, "get_session_entity_id", return_value=2), patch.object(
        menu_module, "create_sidebar_menu_setting", return_value=(True, "", "novo")
    ) as create_mock:
        response = menu_module.menu_subprocess_save_handler_v1(
            request=_request("/settings/menu/menu-save"),
            menu_label="Novo",
            subprocess_return_url="/users/new?menu=sessoes",
        )
    assert create_mock.call_count == 1
    assert "success=" in response.headers["location"]


def test_legacy_admin_cannot_delete_entity():
    with patch.object(entity_delete_module, "SessionLocal", _Session), patch.object(
        entity_delete_module, "get_current_user", return_value=LEGACY_ADMIN
    ), patch.object(entity_delete_module, "get_session_entity_id", return_value=1), patch.object(
        entity_delete_module, "is_admin_user", return_value=True
    ), patch.object(
        entity_delete_module, "get_user_entity_permissions", return_value=LEGACY_PERMS
    ):
        response = entity_delete_module.delete_entity(
            request=_request("/entities/delete"),
            entity_id="1",
            return_menu="",
            return_admin_tab="",
            return_target="",
        )
    assert response.status_code == 303
    assert "Sem permissão para eliminar esta entidade" in unquote_plus(response.headers["location"])


def test_empty_bulk_sections_submit_changes_nothing():
    with patch.object(sections_module, "SessionLocal", _Session), patch.object(
        sections_module, "get_current_user", return_value=LEGACY_ADMIN
    ), patch.object(sections_module, "is_admin_user", return_value=True), patch.object(
        sections_module, "get_session_entity_id", return_value=2
    ), patch.object(
        sections_module, "get_user_entity_permissions", return_value=OWNER_PERMS
    ), patch.object(
        sections_module, "resolve_entity_number_v1", return_value=1000
    ), patch.object(sections_module, "update_sidebar_sections_v2") as update_mock:
        response = sections_module.edit_sidebar_sections_v2(
            request=_request("/settings/menu/sidebar-sections"),
            section_key=[],
            section_label=[],
            section_visibility_scope_mode=[],
            section_status=[],
            redirect_menu="administrativo",
            redirect_target="#settings-menu-edit-card",
        )
    assert update_mock.call_count == 0
    assert "Nenhuma sess" in unquote_plus(response.headers["location"])
