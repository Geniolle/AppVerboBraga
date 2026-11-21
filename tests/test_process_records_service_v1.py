from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from appgenesis.models.process_record import ProcessRecord
from appgenesis.services.process_records_service import (
    create_process_record,
    get_process_record,
    list_process_records,
    update_process_record,
)


@pytest.fixture()
def session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    ProcessRecord.__table__.create(engine)
    maker = sessionmaker(bind=engine)
    with maker() as db:
        yield db


AGENDA_VALUES = {
    "custom_tipo_de_agendamento": "REUNIÃO",
    "custom_titulo_da_agenda": "Culto de jovens",
    "custom_data_do_agendamento": "2026-11-22",
    "custom_organizador": "Clayton",
}


def test_create_and_list_record_for_entity(session):
    record_id = create_process_record(session, entity_id=1, menu_key="agenda", values=AGENDA_VALUES)
    session.commit()

    rows = list_process_records(session, entity_id=1, menu_key="agenda")
    assert len(rows) == 1
    assert rows[0]["record_id"] == record_id
    assert rows[0]["values"]["custom_titulo_da_agenda"] == "Culto de jovens"
    assert rows[0]["state"] == "ativo"


def test_records_are_isolated_per_entity(session):
    create_process_record(session, entity_id=1, menu_key="agenda", values=AGENDA_VALUES)
    create_process_record(session, entity_id=2, menu_key="agenda", values=AGENDA_VALUES)
    session.commit()

    assert len(list_process_records(session, entity_id=1, menu_key="agenda")) == 1
    assert len(list_process_records(session, entity_id=2, menu_key="agenda")) == 1


def test_records_are_isolated_per_menu(session):
    create_process_record(session, entity_id=1, menu_key="agenda", values=AGENDA_VALUES)
    session.commit()
    assert list_process_records(session, entity_id=1, menu_key="outro") == []


def test_get_does_not_cross_entities(session):
    record_id = create_process_record(session, entity_id=1, menu_key="agenda", values=AGENDA_VALUES)
    session.commit()
    assert get_process_record(session, entity_id=2, menu_key="agenda", record_id=record_id) is None
    assert get_process_record(session, entity_id=1, menu_key="agenda", record_id=record_id) is not None


def test_update_changes_values_and_state_only_in_same_entity(session):
    record_id = create_process_record(session, entity_id=1, menu_key="agenda", values=AGENDA_VALUES)
    session.commit()

    assert update_process_record(session, entity_id=2, menu_key="agenda", record_id=record_id, state="inativo") is False
    assert update_process_record(
        session,
        entity_id=1,
        menu_key="agenda",
        record_id=record_id,
        values={"custom_titulo_da_agenda": "Reunião de liderança"},
        state="inativo",
    ) is True
    session.commit()

    row = get_process_record(session, entity_id=1, menu_key="agenda", record_id=record_id)
    assert row["state"] == "inativo"
    assert row["values"] == {"custom_titulo_da_agenda": "Reunião de liderança"}
    assert list_process_records(session, entity_id=1, menu_key="agenda", state="ativo") == []


def test_entity_is_required():
    with pytest.raises(ValueError):
        list_process_records(None, entity_id=None, menu_key="agenda")


def test_empty_values_are_refused(session):
    with pytest.raises(ValueError):
        create_process_record(session, entity_id=1, menu_key="agenda", values={"custom_x": "  "})


def test_invalid_state_is_refused(session):
    with pytest.raises(ValueError):
        create_process_record(session, entity_id=1, menu_key="agenda", values=AGENDA_VALUES, state="apagado")
