from types import SimpleNamespace

import pytest

from appgenesis.services import access_filter as af


class _FakeSession:
    def execute(self, *_args, **_kwargs):
        return SimpleNamespace(scalar=lambda: 1001)


FUNCTIONS = [
    {"key": "user", "status": "ativo", "system_profile": "default", "authorization_profiles": ["perfil_user"]},
    {"key": "admin", "status": "ativo", "system_profile": "owner", "authorization_profiles": ["__all__"]},
    {"key": "inativa", "status": "inativo", "system_profile": "default", "authorization_profiles": ["perfil_extra"]},
]
PROFILES = [
    {"key": "perfil_user", "status": "ativo", "menu_origin": "meu_perfil"},
    {"key": "perfil_extra", "status": "ativo", "menu_origin": "agenda"},
    {"key": "perfil_morto", "status": "inativo", "menu_origin": "membresia"},
]


@pytest.fixture
def enabled(monkeypatch):
    monkeypatch.setenv(af.ACCESS_FILTER_ENV_VAR, "1")
    monkeypatch.setattr(af.FunctionsAdminRepository, "list_rows", lambda self, session, context=None: FUNCTIONS)
    monkeypatch.setattr(af.AuthorizationProfileAdminRepository, "list_rows", lambda self, session, context=None: PROFILES)


def test_disabled_flag_means_no_filter(monkeypatch):
    monkeypatch.delenv(af.ACCESS_FILTER_ENV_VAR, raising=False)
    assert af.resolve_allowed_menu_keys_v1(_FakeSession(), entity_id=1, user_system_type="default") is None


def test_owner_is_exempt(enabled):
    assert af.resolve_allowed_menu_keys_v1(_FakeSession(), entity_id=1, user_system_type="owner") is None


def test_user_gets_menus_of_function_profiles_only(enabled):
    allowed = af.resolve_allowed_menu_keys_v1(_FakeSession(), entity_id=1, user_system_type="default")
    assert allowed == {"meu_perfil"}


def test_inactive_function_and_profile_are_ignored(enabled):
    allowed = af.resolve_allowed_menu_keys_v1(_FakeSession(), entity_id=1, user_system_type="default")
    assert "agenda" not in allowed and "membresia" not in allowed


def test_no_matching_function_gives_no_menus(enabled):
    allowed = af.resolve_allowed_menu_keys_v1(_FakeSession(), entity_id=1, user_system_type="legado")
    assert allowed == set()


def test_all_profiles_marker_gives_every_active_profile_menu(monkeypatch):
    monkeypatch.setenv(af.ACCESS_FILTER_ENV_VAR, "1")
    monkeypatch.setattr(af.FunctionsAdminRepository, "list_rows", lambda self, session, context=None: [
        {"key": "x", "status": "ativo", "system_profile": "super_user", "authorization_profiles": ["__all__"]},
    ])
    monkeypatch.setattr(af.AuthorizationProfileAdminRepository, "list_rows", lambda self, session, context=None: PROFILES)
    allowed = af.resolve_allowed_menu_keys_v1(_FakeSession(), entity_id=1, user_system_type="super_user")
    assert allowed == {"meu_perfil", "agenda"}


def test_apply_filter_keeps_only_allowed():
    assert af.apply_access_filter_to_menu_keys_v1({"home", "agenda", "x"}, {"agenda"}) == {"agenda"}
    assert af.apply_access_filter_to_menu_keys_v1({"home", "x"}, None) == {"home", "x"}
    assert af.apply_access_filter_to_menu_keys_v1({"home"}, set()) == set()


LEVEL_PROFILES = [
    {"key": "perfil_ver", "status": "ativo", "menu_origin": "meu_perfil", "authorization_level": "exibir"},
    {"key": "perfil_edit", "status": "ativo", "menu_origin": "agenda", "authorization_level": "exibir,editar,criar"},
    {"key": "perfil_legado", "status": "ativo", "menu_origin": "agenda", "authorization_level": "editar"},
]


@pytest.fixture
def levels(monkeypatch):
    monkeypatch.setenv(af.ACCESS_FILTER_ENV_VAR, "1")
    monkeypatch.setattr(af.FunctionsAdminRepository, "list_rows", lambda self, session, context=None: [
        {"key": "user", "status": "ativo", "system_profile": "default", "authorization_profiles": ["perfil_ver", "perfil_edit", "perfil_legado"]},
    ])
    monkeypatch.setattr(af.AuthorizationProfileAdminRepository, "list_rows", lambda self, session, context=None: LEVEL_PROFILES)


def test_exibir_profile_gives_only_exibir(levels):
    actions = af.resolve_menu_actions_v1(_FakeSession(), entity_id=1, user_system_type="default", menu_key="meu_perfil")
    assert actions == {"exibir"}


def test_multiple_profiles_union_actions_and_legacy_editar_is_full(levels):
    actions = af.resolve_menu_actions_v1(_FakeSession(), entity_id=1, user_system_type="default", menu_key="agenda")
    assert actions == {"exibir", "editar", "criar", "eliminar"}


def test_menu_without_profile_has_no_actions(levels):
    actions = af.resolve_menu_actions_v1(_FakeSession(), entity_id=1, user_system_type="default", menu_key="membresia")
    assert actions == frozenset()


def test_all_actions_without_filter(monkeypatch):
    monkeypatch.delenv(af.ACCESS_FILTER_ENV_VAR, raising=False)
    actions = af.resolve_menu_actions_v1(_FakeSession(), entity_id=1, user_system_type="default", menu_key="x")
    assert actions == set(af.ALL_ACTIONS)
