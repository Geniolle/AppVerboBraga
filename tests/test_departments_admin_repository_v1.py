from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from appgenesis.admin_subprocesses.repositories.departments_repository import DepartmentsAdminRepository
from appgenesis.models.department import Department, DepartmentMembership
from appgenesis.admin_subprocesses.registry import DEPARTAMENTOS_ADMIN_CONFIG


@pytest.fixture()
def session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Department.__table__.create(engine)
    DepartmentMembership.__table__.create(engine)
    maker = sessionmaker(bind=engine)
    with maker() as db:
        yield db


def _repo() -> DepartmentsAdminRepository:
    return DepartmentsAdminRepository(DEPARTAMENTOS_ADMIN_CONFIG)


def _payload(name: str = "Louvor", status: str = "ativo", description: str = "Ministério de louvor") -> dict:
    return {"label": name, "description": description, "status": status}


def test_create_and_list_for_entity(session):
    ok, reason, key = _repo().save_row(session, _payload(), context={"entity_id": 1})
    session.commit()
    assert (ok, reason) == (True, "saved")
    rows = _repo().list_rows(session, {"entity_id": 1})
    assert len(rows) == 1
    assert rows[0]["key"] == key
    assert rows[0]["label"] == "Louvor"
    assert rows[0]["status"] == "ativo"


def test_list_is_isolated_per_entity(session):
    _repo().save_row(session, _payload("Louvor"), context={"entity_id": 1})
    _repo().save_row(session, _payload("Diaconato"), context={"entity_id": 2})
    session.commit()
    assert [r["label"] for r in _repo().list_rows(session, {"entity_id": 1})] == ["Louvor"]
    assert [r["label"] for r in _repo().list_rows(session, {"entity_id": 2})] == ["Diaconato"]


def test_no_entity_means_no_rows_and_no_write(session):
    assert _repo().list_rows(session, {}) == []
    ok, reason, _ = _repo().save_row(session, _payload(), context={})
    assert (ok, reason) == (False, "menu_not_found")


def test_label_required(session):
    ok, reason, _ = _repo().save_row(session, _payload(name="  "), context={"entity_id": 1})
    assert (ok, reason) == (False, "label_required")


def test_duplicate_name_in_same_entity_is_refused(session):
    _repo().save_row(session, _payload("Louvor"), context={"entity_id": 1})
    session.commit()
    ok, reason, _ = _repo().save_row(session, _payload("louvor"), context={"entity_id": 1})
    assert (ok, reason) == (False, "duplicate_name")


def test_same_name_allowed_in_other_entity(session):
    _repo().save_row(session, _payload("Louvor"), context={"entity_id": 1})
    session.commit()
    ok, reason, _ = _repo().save_row(session, _payload("Louvor"), context={"entity_id": 2})
    assert (ok, reason) == (True, "saved")


def test_edit_updates_and_respects_entity(session):
    _, _, key = _repo().save_row(session, _payload("Louvor"), context={"entity_id": 1})
    session.commit()
    ok, reason, _ = _repo().save_row(
        session, _payload("Louvor Geral", status="inativo"), context={"entity_id": 2}, edit_key=key
    )
    assert (ok, reason) == (False, "not_found")
    ok, reason, _ = _repo().save_row(
        session, _payload("Louvor Geral", status="inativo"), context={"entity_id": 1}, edit_key=key
    )
    session.commit()
    assert (ok, reason) == (True, "saved")
    row = _repo().get_for_edit(session, key, {"entity_id": 1})
    assert row["label"] == "Louvor Geral"
    assert row["status"] == "inativo"


def test_delete_only_inactive_and_same_entity(session):
    _, _, key = _repo().save_row(session, _payload("Louvor"), context={"entity_id": 1})
    session.commit()
    assert _repo().delete_row(session, key, {"entity_id": 1}) == (False, "active_department")
    _repo().save_row(session, _payload("Louvor", status="inativo"), context={"entity_id": 1}, edit_key=key)
    session.commit()
    assert _repo().delete_row(session, key, {"entity_id": 2}) == (False, "not_found")
    assert _repo().delete_row(session, key, {"entity_id": 1}) == (True, "deleted")
    session.commit()
    assert _repo().list_rows(session, {"entity_id": 1}) == []
