"""Etapa 7: administrador de entidade legado (por funcao) gere membros, funcoes e perfis da sua entidade.

Nunca: outros administradores, perfis de administrador, nem funcoes de administrador (sem escalada).
"""

from unittest.mock import patch

import appgenesis.admin_subprocesses.repositories.functions_repository as functions_module
from appgenesis.admin_subprocesses.registry import FUNCTIONS_ADMIN_CONFIG
from appgenesis.repositories.user_repository import member_is_within_permissions
from appgenesis.services.permissions import is_entity_admin_v1
from test_scoped_users_isolation_v1 import _member_id, _seed


class _FakeSession:
    def __init__(self, system_type):
        self.system_type = system_type

    def execute(self, *args, **kwargs):
        value = self.system_type

        class _Result:
            def scalar_one_or_none(self):
                return value

        return _Result()


def _entity_admin(system_type, *, owner=False, filter_on=True, menus=("administrativo", "home")):
    with patch("appgenesis.services.auth.is_admin_user", return_value=owner), patch(
        "appgenesis.services.access_filter.access_filter_enabled", return_value=filter_on
    ), patch("appgenesis.services.access_filter.resolve_allowed_menu_keys_v1", return_value=set(menus)):
        return is_entity_admin_v1(_FakeSession(system_type), 4, "x@y.test", 1)


def test_entity_admin_rule():
    assert _entity_admin("owner", owner=True)
    assert _entity_admin("legado")
    assert not _entity_admin("legado", menus=("home",))  # sem Administrativo na funcao
    assert not _entity_admin("legado", filter_on=False)  # sem filtro por funcao nao ha admin de entidade
    assert not _entity_admin("default")  # membro com o menu continua a ser membro
    assert not _entity_admin("legado", menus=())


def test_entity_admin_manages_only_members_of_own_entity():
    session, owner, a, b = _seed()
    perms = {"selected_entity_id": a.id, "allowed_entity_ids": {a.id}, "allowed_data_entity_ids": {a.id}}
    assert member_is_within_permissions(session, _member_id(session, "a.user@t.test"), perms, target_system_type="default")
    # Outro administrador da mesma entidade: nao.
    assert not member_is_within_permissions(
        session, _member_id(session, "a.admin@t.test"), perms, target_system_type="legado"
    )
    # Membro de outra entidade: nao.
    assert not member_is_within_permissions(session, _member_id(session, "b.user@t.test"), perms, target_system_type="default")


def _functions_repo(items):
    store = {"items": [dict(i) for i in items]}

    def load(_session, _context):
        return {}, [dict(i) for i in store["items"]]

    def save(_session, _context, _menu_config, new_items):
        store["items"] = new_items
        return True

    return store, patch.object(functions_module, "_load_functions", load), patch.object(
        functions_module, "_store_functions", save
    )


ITEMS = [
    {"key": "user", "label": "USER", "status": "ativo", "system_profile": "default", "authorization_profiles": ["home"]},
    {"key": "legado", "label": "LEGADO", "status": "inativo", "system_profile": "legado", "authorization_profiles": ["home"]},
]
CTX = {"entity_id": 1, "entity_number": "1001", "allowed_profile_keys": ["home", "administrativo"], "member_profiles_only": True}


def test_entity_admin_cannot_grant_admin_functions():
    repo = functions_module.FunctionsAdminRepository(FUNCTIONS_ADMIN_CONFIG)
    store, p1, p2 = _functions_repo(ITEMS)
    with p1, p2:
        payload = {"label": "Mais acesso", "system_profile": "legado", "status": "ativo", "authorization_profiles": ["administrativo"]}
        assert repo.save_row(None, payload, context=CTX)[1] == "admin_profile_owner_only"
        payload_edit = {"label": "LEGADO", "system_profile": "default", "status": "ativo", "authorization_profiles": ["home"]}
        assert repo.save_row(None, payload_edit, context=CTX, edit_key="legado")[1] == "admin_profile_owner_only"
        assert repo.delete_row(None, "legado", context=CTX)[1] == "admin_profile_owner_only"
        # Funcao de membros: permitido.
        ok, reason, _key = repo.save_row(
            None,
            {"label": "Lideres", "system_profile": "default", "status": "ativo", "authorization_profiles": ["home"]},
            context=CTX,
        )
        assert ok, reason
    assert [i["key"] for i in store["items"]] == ["user", "legado", "lideres"]


def test_owner_still_manages_admin_functions():
    repo = functions_module.FunctionsAdminRepository(FUNCTIONS_ADMIN_CONFIG)
    _store, p1, p2 = _functions_repo(ITEMS)
    with p1, p2:
        assert repo.delete_row(None, "legado", context={**CTX, "member_profiles_only": False}) == (True, "deleted")
