"""Registos de processos de lista (ex.: Agenda), partilhados por entidade.

Multi-tenant: todas as operacoes exigem entity_id e filtram por ele. Um registo de uma
entidade nunca e lido ou alterado a partir de outra entidade.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from appgenesis.models.process_record import ProcessRecord

# Processos de lista cujos registos ficam na tabela process_records (partilhados por entidade).
ENTITY_RECORD_MENU_KEYS = frozenset({"agenda", "musicas", "membresia"})

STATE_ACTIVE = "ativo"
STATE_INACTIVE = "inativo"
_VALID_STATES = {STATE_ACTIVE, STATE_INACTIVE}


def _require_entity_id(entity_id: Any) -> int:
    try:
        clean_entity_id = int(entity_id)
    except (TypeError, ValueError) as error:
        raise ValueError("entity_id obrigatorio para registos de processo") from error
    if clean_entity_id <= 0:
        raise ValueError("entity_id obrigatorio para registos de processo")
    return clean_entity_id


def _normalize_menu_key(menu_key: Any) -> str:
    clean_key = str(menu_key or "").strip().lower()
    if not clean_key:
        raise ValueError("menu_key obrigatorio para registos de processo")
    return clean_key


def _normalize_values(raw_values: Any) -> dict[str, str]:
    if not isinstance(raw_values, dict):
        return {}
    clean_values: dict[str, str] = {}
    for raw_key, raw_value in raw_values.items():
        clean_key = str(raw_key or "").strip().lower()
        if not clean_key:
            continue
        clean_value = str(raw_value if raw_value is not None else "").strip()
        if clean_value:
            clean_values[clean_key] = clean_value
    return clean_values


def _normalize_state(raw_state: Any) -> str:
    clean_state = str(raw_state or STATE_ACTIVE).strip().lower()
    if clean_state not in _VALID_STATES:
        raise ValueError("estado de registo invalido")
    return clean_state


def _to_dict(row: ProcessRecord) -> dict[str, Any]:
    try:
        values = json.loads(row.values_json or "{}")
    except json.JSONDecodeError:
        values = {}
    created_at = row.created_at.isoformat() if row.created_at else ""
    return {
        "record_id": row.record_id,
        "created_at": created_at,
        "section_key": row.section_key or "",
        "state": row.state or STATE_ACTIVE,
        "values": values if isinstance(values, dict) else {},
    }


def list_process_records(
    session: Session,
    *,
    entity_id: Any,
    menu_key: Any,
    state: Optional[str] = None,
) -> list[dict[str, Any]]:
    clean_entity_id = _require_entity_id(entity_id)
    clean_menu_key = _normalize_menu_key(menu_key)
    statement = (
        select(ProcessRecord)
        .where(ProcessRecord.entity_id == clean_entity_id)
        .where(ProcessRecord.menu_key == clean_menu_key)
        .order_by(ProcessRecord.created_at.desc(), ProcessRecord.id.desc())
    )
    if state is not None:
        statement = statement.where(ProcessRecord.state == _normalize_state(state))
    return [_to_dict(row) for row in session.execute(statement).scalars().all()]


def get_process_record(
    session: Session,
    *,
    entity_id: Any,
    menu_key: Any,
    record_id: Any,
) -> Optional[dict[str, Any]]:
    row = _find_row(session, entity_id=entity_id, menu_key=menu_key, record_id=record_id)
    return _to_dict(row) if row is not None else None


def create_process_record(
    session: Session,
    *,
    entity_id: Any,
    menu_key: Any,
    values: Any,
    section_key: str = "",
    state: Any = STATE_ACTIVE,
    created_by_user_id: Optional[int] = None,
) -> str:
    clean_entity_id = _require_entity_id(entity_id)
    clean_menu_key = _normalize_menu_key(menu_key)
    clean_values = _normalize_values(values)
    if not clean_values:
        raise ValueError("registo sem valores")
    now = datetime.now(timezone.utc)
    record_id = uuid.uuid4().hex
    session.add(
        ProcessRecord(
            entity_id=clean_entity_id,
            menu_key=clean_menu_key,
            record_id=record_id,
            section_key=str(section_key or "").strip().lower(),
            state=_normalize_state(state),
            values_json=json.dumps(clean_values, ensure_ascii=False),
            created_by_user_id=created_by_user_id,
            created_at=now,
            updated_at=now,
        )
    )
    session.flush()
    return record_id


def update_process_record(
    session: Session,
    *,
    entity_id: Any,
    menu_key: Any,
    record_id: Any,
    values: Any = None,
    state: Any = None,
) -> bool:
    row = _find_row(session, entity_id=entity_id, menu_key=menu_key, record_id=record_id)
    if row is None:
        return False
    if values is not None:
        clean_values = _normalize_values(values)
        if not clean_values:
            raise ValueError("registo sem valores")
        row.values_json = json.dumps(clean_values, ensure_ascii=False)
    if state is not None:
        row.state = _normalize_state(state)
    row.updated_at = datetime.now(timezone.utc)
    session.flush()
    return True


def _find_row(session: Session, *, entity_id: Any, menu_key: Any, record_id: Any) -> Optional[ProcessRecord]:
    clean_entity_id = _require_entity_id(entity_id)
    clean_menu_key = _normalize_menu_key(menu_key)
    clean_record_id = str(record_id or "").strip()
    if not clean_record_id:
        return None
    return session.execute(
        select(ProcessRecord)
        .where(ProcessRecord.entity_id == clean_entity_id)
        .where(ProcessRecord.menu_key == clean_menu_key)
        .where(ProcessRecord.record_id == clean_record_id)
    ).scalars().first()


__all__ = [
    "ENTITY_RECORD_MENU_KEYS",
    "STATE_ACTIVE",
    "STATE_INACTIVE",
    "create_process_record",
    "get_process_record",
    "list_process_records",
    "update_process_record",
]
