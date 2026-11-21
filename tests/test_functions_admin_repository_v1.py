from __future__ import annotations

import json

from appgenesis.admin_subprocesses.registry import FUNCTIONS_ADMIN_CONFIG
from appgenesis.admin_subprocesses.repositories.functions_repository import (
    FunctionsAdminRepository,
    build_function_key,
)


def _repo() -> FunctionsAdminRepository:
    return FunctionsAdminRepository(FUNCTIONS_ADMIN_CONFIG)


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


def _stored(session: _FakeSession) -> dict:
    return json.loads(session.menu_config)


def test_build_function_key_normalizes_label():
    assert build_function_key("Coordenador de Secretaria") == "coordenador_de_secretaria"
    assert build_function_key("   ") == "funcao"


def test_save_creates_active_function_and_lists_it():
    session = _FakeSession({})
    repo = _repo()

    ok, reason, key = repo.save_row(
        session,
        {"label": "Coordenador de Secretaria", "status": "ativo", "visibility_scope_mode": "all"},
        context={"entity_number": "1000"},
    )

    assert (ok, reason, key) == (True, "saved", "coordenador_de_secretaria")
    rows = repo.list_rows(session)
    assert len(rows) == 1
    assert rows[0]["label"] == "Coordenador de Secretaria"
    assert rows[0]["status"] == "ativo"
    assert rows[0]["entity_number"] == "1000"


def test_save_requires_label():
    ok, reason, _ = _repo().save_row(_FakeSession({}), {"label": "  "})
    assert (ok, reason) == (False, "label_required")


def test_save_edit_updates_existing_row():
    session = _FakeSession({})
    repo = _repo()
    repo.save_row(session, {"label": "Diretor", "status": "ativo"})

    ok, reason, key = repo.save_row(
        session,
        {"label": "Diretor Geral", "status": "inativo", "visibility_scope_mode": "owner"},
        edit_key="diretor",
    )

    assert (ok, reason, key) == (True, "saved", "diretor")
    row = repo.get_for_edit(session, "diretor")
    assert row["label"] == "Diretor Geral"
    assert row["status"] == "inativo"
    assert row["visibility_scope_label"] == "Owner"


def test_save_edit_unknown_key_returns_not_found():
    ok, reason, _ = _repo().save_row(
        _FakeSession({}), {"label": "X"}, edit_key="nao_existe"
    )
    assert (ok, reason) == (False, "not_found")


def test_delete_refuses_active_function():
    session = _FakeSession({})
    repo = _repo()
    repo.save_row(session, {"label": "Diretor", "status": "ativo"})

    assert repo.delete_row(session, "diretor") == (False, "active_function")
    assert len(repo.list_rows(session)) == 1


def test_delete_removes_inactive_function():
    session = _FakeSession({})
    repo = _repo()
    repo.save_row(session, {"label": "Diretor", "status": "inativo"})

    assert repo.delete_row(session, "diretor") == (True, "deleted")
    assert repo.list_rows(session) == []


def test_save_keeps_other_menu_config_keys():
    session = _FakeSession({"sidebar_sections": [{"key": "x"}]})
    _repo().save_row(session, {"label": "Diretor"})
    assert _stored(session)["sidebar_sections"] == [{"key": "x"}]
