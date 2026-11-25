from appgenesis.admin_subprocesses.registry import AUTHORIZATION_PROFILE_CONFIG
from appgenesis.services.auth_profile_entity_scope import (
    lock_visibility_scope_field_v1,
    resolve_visibility_scope_for_entity_v1,
)


def _scope_field(config):
    return next(f for f in config.fields if f.input_name == "auth_profile_visibility_scope_mode")


def test_owner_entity_keeps_submitted_scope() -> None:
    assert resolve_visibility_scope_for_entity_v1("all", "owner") == "all"
    assert resolve_visibility_scope_for_entity_v1("owner", "owner") == "owner"


def test_legado_entity_always_creates_legado() -> None:
    assert resolve_visibility_scope_for_entity_v1("all", "legado") == "legado"
    assert resolve_visibility_scope_for_entity_v1("owner", "legado") == "legado"
    assert resolve_visibility_scope_for_entity_v1("", "legado") == "legado"


def test_legado_entity_form_field_is_locked_to_legado() -> None:
    field = _scope_field(lock_visibility_scope_field_v1(AUTHORIZATION_PROFILE_CONFIG, "legado"))
    assert field.locked is True
    assert field.default_value == "legado"
    assert [value for value, _ in field.options] == ["legado"]


def test_owner_entity_form_field_is_not_locked() -> None:
    field = _scope_field(lock_visibility_scope_field_v1(AUTHORIZATION_PROFILE_CONFIG, "owner"))
    assert field.locked is False
    assert [value for value, _ in field.options] == ["all", "owner", "legado"]


def test_legado_lock_applies_to_every_sistema_field_in_project() -> None:
    from appgenesis.admin_subprocesses.registry import (
        MENU_CONFIG,
        SESSOES_CONFIG,
        FUNCTIONS_ADMIN_CONFIG,
    )

    for config in (AUTHORIZATION_PROFILE_CONFIG, SESSOES_CONFIG, MENU_CONFIG, FUNCTIONS_ADMIN_CONFIG):
        locked = lock_visibility_scope_field_v1(config, "legado")
        scope_fields = [f for f in locked.fields if f.input_name.endswith("visibility_scope_mode") or f.input_name == "menu_visibility_scope"]
        assert scope_fields, config.key
        assert all(f.locked for f in scope_fields), config.key
