from __future__ import annotations

import json

from appgenesis.admin_subprocesses.registry import FUNCTIONS_ADMIN_CONFIG
from appgenesis.admin_subprocesses.repositories.functions_repository import (
    FunctionsAdminRepository,
    build_function_key,
    normalize_profile_keys,
)

ALLOWED = ["teste_autorizacao", "teste_menu_origem"]
CONTEXT = {"entity_number": "1000", "allowed_profile_keys": ALLOWED}


class _Result:
    def __init__(self, row):
        self._row = row

    def fetchone(self):
        return self._row


class _FakeSession:
    def __init__(self, menu_config: dict):
        self.menu_config = json.dumps(menu_config)

    def execute(self, statement, params=None):
        sql = str(statement)
        if sql.strip().upper().startswith("UPDATE"):
            self.menu_config = params["menu_config"]
            return _Result(None)
        return _Result((self.menu_config,))


def _repo() -> FunctionsAdminRepository:
    return FunctionsAdminRepository(FUNCTIONS_ADMIN_CONFIG)


def _stored(session: _FakeSession) -> dict:
    return json.loads(session.menu_config)


def _payload(label: str = "Diretor", status: str = "ativo", profiles=None) -> dict:
    return {
        "label": label,
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
    session = _FakeSession({})
    repo = _repo()

    ok, reason, key = repo.save_row(
        session,
        _payload("Coordenador de Secretaria", profiles=["teste_autorizacao", "teste_menu_origem"]),
        context=CONTEXT,
    )

    assert (ok, reason, key) == (True, "saved", "coordenador_de_secretaria")
    rows = repo.list_rows(session)
    assert len(rows) == 1
    assert rows[0]["label"] == "Coordenador de Secretaria"
    assert rows[0]["status"] == "ativo"
    assert rows[0]["entity_number"] == "1000"
    assert rows[0]["authorization_profiles"] == ["teste_autorizacao", "teste_menu_origem"]
    assert rows[0]["values"]["authorization_profiles"] == ["teste_autorizacao", "teste_menu_origem"]


def test_save_requires_label():
    ok, reason, _ = _repo().save_row(_FakeSession({}), _payload(label="  "), context=CONTEXT)
    assert (ok, reason) == (False, "label_required")


def test_save_requires_at_least_one_profile():
    ok, reason, _ = _repo().save_row(_FakeSession({}), _payload(profiles=[""]), context=CONTEXT)
    assert (ok, reason) == (False, "profile_required")


def test_save_refuses_duplicate_profiles():
    ok, reason, _ = _repo().save_row(
        _FakeSession({}),
        _payload(profiles=["teste_autorizacao", "teste_autorizacao"]),
        context=CONTEXT,
    )
    assert (ok, reason) == (False, "profile_duplicate")


def test_save_refuses_profile_not_active_or_unknown():
    ok, reason, _ = _repo().save_row(
        _FakeSession({}),
        _payload(profiles=["perfil_inativo"]),
        context=CONTEXT,
    )
    assert (ok, reason) == (False, "profile_not_found")


def test_save_edit_updates_existing_row():
    session = _FakeSession({})
    repo = _repo()
    repo.save_row(session, _payload("Diretor", "ativo"), context=CONTEXT)

    ok, reason, key = repo.save_row(
        session,
        _payload("Diretor Geral", "inativo", profiles=["teste_menu_origem"]) | {"visibility_scope_mode": "owner"},
        context=CONTEXT,
        edit_key="diretor",
    )

    assert (ok, reason, key) == (True, "saved", "diretor")
    row = repo.get_for_edit(session, "diretor")
    assert row["label"] == "Diretor Geral"
    assert row["status"] == "inativo"
    assert row["visibility_scope_label"] == "Owner"
    assert row["authorization_profiles"] == ["teste_menu_origem"]


def test_save_edit_unknown_key_returns_not_found():
    ok, reason, _ = _repo().save_row(_FakeSession({}), _payload(), context=CONTEXT, edit_key="nao_existe")
    assert (ok, reason) == (False, "not_found")


def test_delete_refuses_active_function():
    session = _FakeSession({})
    repo = _repo()
    repo.save_row(session, _payload("Diretor", "ativo"), context=CONTEXT)

    assert repo.delete_row(session, "diretor") == (False, "active_function")
    assert len(repo.list_rows(session)) == 1


def test_delete_removes_inactive_function():
    session = _FakeSession({})
    repo = _repo()
    repo.save_row(session, _payload("Diretor", "inativo"), context=CONTEXT)

    assert repo.delete_row(session, "diretor") == (True, "deleted")
    assert repo.list_rows(session) == []


def test_save_keeps_other_menu_config_keys():
    session = _FakeSession({"sidebar_sections": [{"key": "x"}]})
    _repo().save_row(session, _payload("Diretor"), context=CONTEXT)
    assert _stored(session)["sidebar_sections"] == [{"key": "x"}]


def test_save_all_profiles_stores_marker():
    session = _FakeSession({})
    repo = _repo()
    ok, reason, key = repo.save_row(session, _payload("Diretor", profiles=["__all__"]), context=CONTEXT)
    assert (ok, reason, key) == (True, "saved", "diretor")
    assert repo.get_for_edit(session, "diretor")["authorization_profiles"] == ["__all__"]


def test_save_all_profiles_cannot_mix_with_specific_profiles():
    ok, reason, _ = _repo().save_row(
        _FakeSession({}),
        _payload(profiles=["__all__", "teste_autorizacao"]),
        context=CONTEXT,
    )
    assert (ok, reason) == (False, "profile_all_exclusive")
