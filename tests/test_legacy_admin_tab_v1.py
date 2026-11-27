from __future__ import annotations

from appgenesis.admin_subprocesses.registry import (
    ADMIN_SISTEMA_CONFIG,
    LEGACY_ADMIN_TAB_KEY,
    UTILIZADOR_CONFIG,
)
from appgenesis.services.process_tabs import resolve_process_tabs_v1
from appgenesis.use_cases.users.create_user import normalize_create_user_input_v1


def _normalize(**overrides):
    base = dict(
        full_name="Ana",
        primary_phone="912",
        email="ana@x.pt",
        entity_id="2",
        invite_delivery="email",
        system_profile="default",
    )
    base.update(overrides)
    return normalize_create_user_input_v1(**base)


def test_legado_profile_rejected_on_normal_user_form():
    payload = _normalize(system_profile="legado")
    assert payload.clean_system_type == "default"
    assert any("Administradores do sistema" in e for e in payload.errors)


def test_legacy_admin_form_forces_legado_profile():
    payload = _normalize(system_profile="owner", legacy_admin_form=True)
    assert payload.clean_system_type == "legado"
    assert payload.errors == []


def test_owner_tab_listed_for_administrativo():
    keys = [t.key for t in resolve_process_tabs_v1("administrativo", [])]
    assert LEGACY_ADMIN_TAB_KEY in keys
    assert keys.index(LEGACY_ADMIN_TAB_KEY) == keys.index("utilizador") + 1


def test_admin_config_reuses_user_config_without_profile_column():
    assert ADMIN_SISTEMA_CONFIG.key == LEGACY_ADMIN_TAB_KEY
    assert ADMIN_SISTEMA_CONFIG.repository_name == UTILIZADOR_CONFIG.repository_name
    assert "system_profile" not in [c.key for c in ADMIN_SISTEMA_CONFIG.columns]
    assert ADMIN_SISTEMA_CONFIG.default_target == "system-admins-card"
