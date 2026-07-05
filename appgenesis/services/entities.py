from __future__ import annotations

import re
import secrets
from pathlib import Path
from typing import Any

from fastapi import UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from appgenesis.core import (
    ALLOWED_ENTITY_LOGO_EXTENSIONS,
    ALLOWED_ENTITY_PROFILE_SCOPE,
    ENTITY_LOGOS_DIR,
    ENTITY_PROFILE_SCOPE_LEGADO,
    ENTITY_PROFILE_SCOPE_OWNER,
    LOGO_CONTENT_TYPE_EXTENSION,
    MAX_ENTITY_LOGO_SIZE_BYTES,
)
from appgenesis.models import Entity

def save_entity_logo_upload(entity_logo_file: UploadFile | None) -> tuple[str, str]:
    if entity_logo_file is None or not entity_logo_file.filename:
        return "", ""

    content_type = (entity_logo_file.content_type or "").strip().lower()
    file_ext = Path(entity_logo_file.filename).suffix.lower()
    if file_ext not in ALLOWED_ENTITY_LOGO_EXTENSIONS:
        mapped_ext = LOGO_CONTENT_TYPE_EXTENSION.get(content_type, "")
        file_ext = mapped_ext

    if file_ext not in ALLOWED_ENTITY_LOGO_EXTENSIONS:
        return "", "Formato de imagem inválido. Use PNG, JPG, WEBP, GIF ou SVG."

    stored_name = f"entity_logo_{secrets.token_hex(10)}{file_ext}"
    destination = ENTITY_LOGOS_DIR / stored_name
    total_size = 0

    try:
        with destination.open("wb") as file_handle:
            while True:
                chunk = entity_logo_file.file.read(1024 * 1024)
                if not chunk:
                    break
                total_size += len(chunk)
                if total_size > MAX_ENTITY_LOGO_SIZE_BYTES:
                    file_handle.close()
                    destination.unlink(missing_ok=True)
                    return "", "Imagem demasiado grande. Limite maximo: 5MB."
                file_handle.write(chunk)
    finally:
        entity_logo_file.file.close()

    return f"/static/entities/{stored_name}", ""

# APPGENESIS_ENTITY_FORM_REFACTOR_V1_START
ENTITY_FORM_FIELDS_V1: tuple[dict[str, Any], ...] = (
    {"key": "name", "label": "Nome da entidade", "required": True},
    {"key": "acronym", "label": "Acrónimo", "required": False},
    {"key": "tax_id", "label": "Nº Identificação Fiscal", "required": True},
    {"key": "profile_scope", "label": "Perfil da entidade", "required": True},
    {"key": "email", "label": "Email", "required": True},
    {"key": "phone", "label": "Telefone", "required": True},
    {"key": "responsible_name", "label": "Nome do responsável", "required": True},
    {"key": "address", "label": "Morada", "required": True},
    {"key": "door_number", "label": "Nº da porta", "required": True},
    {"key": "freguesia", "label": "Freguesia", "required": True},
    {"key": "postal_code", "label": "Código postal", "required": True},
    {"key": "city", "label": "Cidade", "required": True},
    {"key": "country", "label": "País", "required": True},
    {"key": "logo_url", "label": "Imagem/ícone da entidade", "required": False},
)

ENTITY_REQUIRED_FIELD_LABELS_V1: tuple[tuple[str, str], ...] = tuple(
    (str(field["key"]), str(field["label"]))
    for field in ENTITY_FORM_FIELDS_V1
    if bool(field.get("required")) and str(field.get("key")) != "profile_scope"
)

ENTITY_DATA_ASSIGNMENT_FIELDS_V1: tuple[str, ...] = (
    "name",
    "tax_id",
    "email",
    "responsible_name",
    "door_number",
    "address",
    "city",
    "freguesia",
    "postal_code",
    "country",
    "phone",
)


def normalize_entity_text_v1(value: Any) -> str:
    return str(value or "").strip()


def normalize_entity_profile_scope_v1(value: Any) -> tuple[str, bool]:
    clean_profile_scope = normalize_entity_text_v1(value).lower()
    invalid_profile_scope = clean_profile_scope not in ALLOWED_ENTITY_PROFILE_SCOPE

    if invalid_profile_scope:
        clean_profile_scope = ENTITY_PROFILE_SCOPE_LEGADO

    return clean_profile_scope, invalid_profile_scope


def clean_entity_form_data_v1(
    *,
    name: Any = "",
    acronym: Any = "",
    tax_id: Any = "",
    email: Any = "",
    responsible_name: Any = "",
    door_number: Any = "",
    address: Any = "",
    city: Any = "",
    freguesia: Any = "",
    postal_code: Any = "",
    country: Any = "",
    phone: Any = "",
    entity_profile_scope: Any = ENTITY_PROFILE_SCOPE_LEGADO,
    description: Any = None,
    created_at_text: str = "",
) -> tuple[dict[str, str], bool]:
    clean_profile_scope, invalid_profile_scope = normalize_entity_profile_scope_v1(
        entity_profile_scope
    )

    form_data = {
        "name": normalize_entity_text_v1(name),
        "acronym": normalize_entity_text_v1(acronym),
        "tax_id": normalize_entity_text_v1(tax_id),
        "email": normalize_entity_text_v1(email),
        "responsible_name": normalize_entity_text_v1(responsible_name),
        "door_number": normalize_entity_text_v1(door_number),
        "address": normalize_entity_text_v1(address),
        "city": normalize_entity_text_v1(city),
        "freguesia": normalize_entity_text_v1(freguesia),
        "postal_code": normalize_entity_text_v1(postal_code),
        "country": normalize_entity_text_v1(country),
        "phone": normalize_entity_text_v1(phone),
        "profile_scope": clean_profile_scope,
        "description": normalize_entity_text_v1(description),
        "created_at": created_at_text,
    }

    return form_data, invalid_profile_scope


def validate_entity_required_fields_v1(form_data: dict[str, str]) -> list[str]:
    missing_labels: list[str] = []

    for field_key, field_label in ENTITY_REQUIRED_FIELD_LABELS_V1:
        if not normalize_entity_text_v1(form_data.get(field_key)):
            missing_labels.append(field_label)

    return missing_labels


def apply_entity_form_data_v1(
    entity: Entity,
    form_data: dict[str, str],
    *,
    include_profile_scope: bool = True,
    include_description: bool = True,
) -> None:
    for field_key in ENTITY_DATA_ASSIGNMENT_FIELDS_V1:
        setattr(entity, field_key, normalize_entity_text_v1(form_data.get(field_key)) or None)

    entity.acronym = normalize_entity_text_v1(form_data.get("acronym")) or None

    if include_profile_scope:
        entity.profile_scope = normalize_entity_text_v1(
            form_data.get("profile_scope")
        ) or ENTITY_PROFILE_SCOPE_LEGADO

    if include_description:
        entity.description = normalize_entity_text_v1(form_data.get("description")) or None


def get_duplicate_entity_name_id_v1(
    session: Session,
    clean_name: str,
    *,
    ignore_entity_id: int | None = None,
) -> int | None:
    stmt = select(Entity.id).where(
        func.lower(Entity.name) == normalize_entity_text_v1(clean_name).lower()
    )

    if ignore_entity_id is not None:
        stmt = stmt.where(Entity.id != int(ignore_entity_id))

    raw_entity_id = session.scalar(stmt.limit(1))

    return int(raw_entity_id) if raw_entity_id is not None else None


def get_existing_owner_entity_id_v1(
    session: Session,
    *,
    ignore_entity_id: int | None = None,
) -> int | None:
    stmt = select(Entity.id).where(Entity.profile_scope == ENTITY_PROFILE_SCOPE_OWNER)

    if ignore_entity_id is not None:
        stmt = stmt.where(Entity.id != int(ignore_entity_id))

    raw_entity_id = session.scalar(stmt.limit(1))

    return int(raw_entity_id) if raw_entity_id is not None else None
# APPGENESIS_ENTITY_FORM_REFACTOR_V1_END

__all__ = [
    "save_entity_logo_upload",
    "ENTITY_FORM_FIELDS_V1",
    "ENTITY_REQUIRED_FIELD_LABELS_V1",
    "ENTITY_DATA_ASSIGNMENT_FIELDS_V1",
    "normalize_entity_text_v1",
    "normalize_entity_profile_scope_v1",
    "clean_entity_form_data_v1",
    "validate_entity_required_fields_v1",
    "apply_entity_form_data_v1",
    "get_duplicate_entity_name_id_v1",
    "get_existing_owner_entity_id_v1",
]
