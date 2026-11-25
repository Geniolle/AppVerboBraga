from __future__ import annotations

import json

from appgenesis.admin_subprocesses.registry import FUNCTIONS_ADMIN_CONFIG
from appgenesis.admin_subprocesses.repositories.functions_repository import (
    FunctionsAdminRepository,
    build_function_key,
    normalize_profile_keys,
)

ALLOWED = ["teste_autorizacao", "teste_menu_origem"]
CONTEXT = {"entity_id": 1, "entity_number": "1000", "allowed_profile_keys": ALLOWED}


class _Result:
    def __init__(self, row, rowcount: int = 1):
        self._row = row
        self.rowcount = rowcount

    def fetchone(self):
        return self._row


class _FakeSession:
    """Simula sidebar_menu_settings: uma linha 'administrativo' por entity_id."""

    def __init__(self, menu_configs: dict):
        self.menus = {entity_id: json.dumps(config) for entity_id, config in menu_configs.items()}

    def execute(self, statement, params=None):
        sql = str(statement)
        entity_id = (params or {}).get("entity_id")
        if sql.strip().upper().startswith("UPDATE"):
            if entity_id not in self.menus:
                return _Result(None, rowcount=0)
            self.menus[entity_id] = params["menu_config"]
            return _Result(None, rowcount=1)
        if entity_id not in self.menus:
            return _Result(None)
        return _Result((self.menus[entity_id],))


def _repo() -> FunctionsAdminRepository:
    return FunctionsAdminRepository(FUNCTIONS_ADMIN_CONFIG)


def _stored(session: _FakeSession, entity_id: int = 1) -> dict:
    return json.loads(session.menus[entity_id])


def _payload(label: str = "Diretor", status: str = "ativo", profiles=None) -> dict:
    return {
        "label": label,
        "system_profile": "default",
        "status": status,
        "visibility_scope_mode": "all",
        "authorization_profiles": ["teste_autorizacao"] if profiles is None else profiles,
    }


def test_build_function_key_normalizes_label():
    assert build_function_key("Coordenador de Secretaria") == "coordenador_de_secretaria"
    assert build_function_key("   ") == "funcao"


def test_normalize_profile_keys_strips_and_drops_empty():
    assert normalize_profile_keys([" Teste_Autorizacao ", "", None]) == ["teste_autorizacao"]
    assert normalize_profile_keys(["  A ", "", "b"]) == ["a", "b"]
    assert normalize_profile_keys("unico") == ["unico"]
    assert normalize_profile_keys(None) == []


def test_save_creates_active_function_with_profiles():
    session = _FakeSession({1: {}})
    repo = _repo()

    ok, reason, key = repo.save_row(
        session,
        _payload("Coordenador de Secretaria", profiles=["teste_autorizacao", "teste_menu_origem"]),
        context=CONTEXT,
    )

    assert (ok, reason, key) == (True, "saved", "coordenador_de_secretaria")
    rows = repo.list_rows(session, {"entity_id": 1})
    assert len(rows) == 1
    assert rows[0]["label"] == "Coordenador de Secretaria"
    assert rows[0]["status"] == "ativo"
    assert rows[0]["entity_number"] == "1000"
    assert rows[0]["authorization_profiles"] == ["teste_autorizacao", "teste_menu_origem"]
    assert rows[0]["values"]["authorization_profiles"] == ["teste_autorizacao", "teste_menu_origem"]


def test_save_requires_label():
    ok, reason, _ = _repo().save_row(_FakeSession({1: {}}), _payload(label="  "), context=CONTEXT)
    assert (ok, reason) == (False, "label_required")


def test_save_requires_at_least_one_profile():
    ok, reason, _ = _repo().save_row(_FakeSession({1: {}}), _payload(profiles=[""]), context=CONTEXT)
    assert (ok, reason) == (False, "profile_required")


def test_save_refuses_duplicate_profiles():
    ok, reason, _ = _repo().save_row(
        _FakeSession({1: {}}),
        _payload(profiles=["teste_autorizacao", "teste_autorizacao"]),
        context=CONTEXT,
    )
    assert (ok, reason) == (False, "profile_duplicate")


def test_save_refuses_profile_not_active_or_unknown():
    ok, reason, _ = _repo().save_row(
        _FakeSession({1: {}}),
        _payload(profiles=["perfil_inativo"]),
        context=CONTEXT,
    )
    assert (ok, reason) == (False, "profile_not_found")


def test_save_edit_updates_existing_row():
    session = _FakeSession({1: {}})
    repo = _repo()
    repo.save_row(session, _payload("Diretor", "ativo"), context=CONTEXT)

    ok, reason, key = repo.save_row(
        session,
        _payload("Diretor Geral", "inativo", profiles=["teste_menu_origem"]) | {"visibility_scope_mode": "owner"},
        context=CONTEXT,
        edit_key="diretor",
    )

    assert (ok, reason, key) == (True, "saved", "diretor")
    row = repo.get_for_edit(session, "diretor", CONTEXT)
    assert row["label"] == "Diretor Geral"
    assert row["status"] == "inativo"
    assert row["visibility_scope_label"] == "Owner"
    assert row["authorization_profiles"] == ["teste_menu_origem"]


def test_save_edit_unknown_key_returns_not_found():
    ok, reason, _ = _repo().save_row(_FakeSession({1: {}}), _payload(), context=CONTEXT, edit_key="nao_existe")
    assert (ok, reason) == (False, "not_found")


def test_delete_refuses_active_function():
    session = _FakeSession({1: {}})
    repo = _repo()
    repo.save_row(session, _payload("Diretor", "ativo"), context=CONTEXT)

    assert repo.delete_row(session, "diretor", {"entity_id": 1}) == (False, "active_function")
    assert len(repo.list_rows(session, {"entity_id": 1})) == 1


def test_delete_removes_inactive_function():
    session = _FakeSession({1: {}})
    repo = _repo()
    repo.save_row(session, _payload("Diretor", "inativo"), context=CONTEXT)

    assert repo.delete_row(session, "diretor", {"entity_id": 1}) == (True, "deleted")
    assert repo.list_rows(session) == []


def test_save_keeps_other_menu_config_keys():
    session = _FakeSession({1: {"sidebar_sections": [{"key": "x"}]}})
    _repo().save_row(session, _payload("Diretor"), context=CONTEXT)
    assert _stored(session)["sidebar_sections"] == [{"key": "x"}]


def test_save_all_profiles_stores_marker():
    session = _FakeSession({1: {}})
    repo = _repo()
    ok, reason, key = repo.save_row(session, _payload("Diretor", profiles=["__all__"]), context=CONTEXT)
    assert (ok, reason, key) == (True, "saved", "diretor")
    assert repo.get_for_edit(session, "diretor", CONTEXT)["authorization_profiles"] == ["__all__"]


def test_save_all_profiles_cannot_mix_with_specific_profiles():
    ok, reason, _ = _repo().save_row(
        _FakeSession({1: {}}),
        _payload(profiles=["__all__", "teste_autorizacao"]),
        context=CONTEXT,
    )
    assert (ok, reason) == (False, "profile_all_exclusive")


def test_functions_are_isolated_per_entity():
    session = _FakeSession({1: {}, 2: {}})
    repo = _repo()
    repo.save_row(session, _payload("Diretor"), context=CONTEXT)

    assert len(repo.list_rows(session, {"entity_id": 1})) == 1
    assert repo.list_rows(session, {"entity_id": 2}) == []
    assert repo.delete_row(session, "diretor", context={"entity_id": 2}) == (False, "not_found")


def test_no_entity_means_no_functions_and_no_write():
    session = _FakeSession({1: {}})
    repo = _repo()
    assert repo.list_rows(session, {}) == []
    ok, reason, _ = repo.save_row(session, _payload("Diretor"), context={"allowed_profile_keys": ALLOWED})
    assert (ok, reason) == (False, "menu_not_found")


def test_save_without_administrativo_row_is_refused():
    session = _FakeSession({})
    ok, reason, _ = _repo().save_row(session, _payload("Diretor"), context=CONTEXT)
    assert (ok, reason) == (False, "menu_not_found")


def test_save_requires_system_profile():
    payload = _payload("Diretor")
    payload["system_profile"] = ""
    ok, reason, _ = _repo().save_row(_FakeSession({1: {}}), payload, context=CONTEXT)
    assert (ok, reason) == (False, "system_profile_required")


def test_saved_function_exposes_system_profile_label():
    session = _FakeSession({1: {}})
    payload = _payload("Diretor")
    payload["system_profile"] = "owner"
    ok, _reason, key = _repo().save_row(session, payload, context=CONTEXT)
    assert ok is True
    row = next(r for r in _repo().list_rows(session, context=CONTEXT) if r["key"] == key)
    assert row["system_profile"] == "owner"
    assert row["system_profile_label"] == "Admin"
