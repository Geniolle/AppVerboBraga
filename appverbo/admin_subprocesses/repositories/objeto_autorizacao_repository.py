from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import select

from appverbo.admin_subprocesses.repositories.base import BaseAdminSubprocessRepository
from appverbo.menu_settings import (
    get_menu_visibility_scope_label,
    get_menu_visibility_scope_mode,
    get_sidebar_menu_settings,
)
from appverbo.models import Member, User
from appverbo.services.profile import (
    build_menu_process_records_storage_key,
    parse_member_profile_fields,
    parse_menu_process_records,
    serialize_member_profile_fields,
    serialize_menu_process_records,
)


OBJETO_AUTORIZACAO_STORAGE_KEY = "objeto_de_autorizacao"
OBJETO_AUTORIZACAO_SECTION_KEY = "custom_objeto_de_autorizacao"
OBJETO_AUTORIZACAO_LABEL_VALUE_KEYS = ("objeto_de_autorizacao", "custom_objeto_label")
OBJETO_AUTORIZACAO_PROCESS_DISPLAY_KEYS = (
    "process_label",
    "processo_label",
    "custom_processo_label",
    "custom_nome_do_processo",
    "custom_processo",
    "processo",
)
OBJETO_AUTORIZACAO_AUTHORIZATION_DISPLAY_KEYS = (
    "authorization_label",
    "autorizacao_label",
    "custom_autorizacao_label",
    "custom_subprocesso_label",
    "custom_autorizacao",
    "custom_subprocesso",
    "authorization",
    "autorizacao",
    "subprocesso",
)
OBJETO_AUTORIZACAO_SCOPE_MODE_KEY = "__scope_mode"
OBJETO_AUTORIZACAO_SCOPE_LABEL_KEY = "__scope_label"
OBJETO_AUTORIZACAO_STATUS_KEY = "__estado"
OBJETO_AUTORIZACAO_TECHNICAL_KEY = "__key"
OBJETO_AUTORIZACAO_ENTITY_NUMBER_KEY = "__numero_entidade"

_AUTH_MENU_KEY = "perfil_de_autorizacao"


def _normalize_status(raw_value: Any) -> str:
    clean_value = str(raw_value or "").strip().lower()
    if clean_value in {"inativo", "inactive", "0", "false", "off", "no", "nao"}:
        return "inativo"
    return "ativo"


def _status_label(status_value: str) -> str:
    return "Inativo" if _normalize_status(status_value) == "inativo" else "Ativo"


def _normalize_scope_mode(raw_value: Any, fallback: str = "owner") -> str:
    clean_value = str(raw_value or "").strip().lower()
    if clean_value in {"all", "owner", "legado"}:
        return clean_value
    return fallback or "owner"


def _scope_label(scope_mode: str) -> str:
    if scope_mode == "owner":
        return "Owner"
    if scope_mode == "legado":
        return "Legado"
    return "Default"


def _normalize_lookup_slug(raw_value: Any) -> str:
    normalized = (
        unicodedata.normalize("NFKD", str(raw_value or ""))
        .encode("ascii", "ignore")
        .decode("ascii")
        .strip()
        .lower()
    )
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized)
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized or "objeto"


def build_objeto_autorizacao_key(label: Any, *, fallback: str = "") -> str:
    clean_slug = _normalize_lookup_slug(label)
    if clean_slug:
        return clean_slug
    clean_fallback = _normalize_lookup_slug(fallback)
    return clean_fallback or "objeto"


def _resolve_display_value_from_values(
    values: dict[str, Any],
    *,
    key_candidates: tuple[str, ...],
    fallback: str = "-",
) -> str:
    for raw_key in key_candidates:
        candidate = str(values.get(raw_key) or "").strip()
        if candidate:
            return candidate

    normalized_candidates = {
        _normalize_lookup_slug(raw_key)
        for raw_key in key_candidates
        if str(raw_key or "").strip()
    }
    if not normalized_candidates:
        return fallback

    for raw_key, raw_value in values.items():
        candidate = str(raw_value or "").strip()
        if not candidate:
            continue

        normalized_key = _normalize_lookup_slug(raw_key)
        if not normalized_key:
            continue

        if normalized_key in normalized_candidates:
            return candidate

        for normalized_candidate in normalized_candidates:
            if "_" not in normalized_candidate:
                continue
            if normalized_key.endswith(f"_{normalized_candidate}"):
                return candidate

    return fallback


class ObjetoAutorizacaoAdminRepository(BaseAdminSubprocessRepository):
    def _resolve_member(
        self,
        session: Any,
        context: dict[str, Any] | None = None,
    ) -> Member | None:
        ctx = context or {}
        member_id = ctx.get("member_id")
        if member_id:
            return session.get(Member, member_id)

        user_id = ctx.get("user_id")
        if not user_id:
            return None

        return session.execute(
            select(Member)
            .join(User, User.member_id == Member.id)
            .where(User.id == user_id)
            .limit(1)
        ).scalar_one_or_none()

    def _resolve_menu_scope_defaults(
        self,
        session: Any,
    ) -> tuple[str, str]:
        for row in get_sidebar_menu_settings(session):
            if str(row.get("key") or "").strip().lower() != _AUTH_MENU_KEY:
                continue
            menu_config = row.get("menu_config") if isinstance(row.get("menu_config"), dict) else {}
            scope_mode = _normalize_scope_mode(
                row.get("visibility_scope_mode") or get_menu_visibility_scope_mode(menu_config),
                fallback="owner",
            )
            scope_label = str(
                row.get("visibility_scope_label")
                or get_menu_visibility_scope_label(menu_config)
                or _scope_label(scope_mode)
            ).strip() or _scope_label(scope_mode)
            return scope_mode, scope_label
        return "owner", "Owner"

    def _load_record_bundle(
        self,
        session: Any,
        context: dict[str, Any] | None = None,
    ) -> tuple[Member | None, dict[str, str], list[dict[str, Any]], str, str]:
        member = self._resolve_member(session, context)
        if member is None:
            return None, {}, [], "owner", "Owner"

        existing_profile_fields = parse_member_profile_fields(member.profile_custom_fields)
        records_storage_key = build_menu_process_records_storage_key(OBJETO_AUTORIZACAO_STORAGE_KEY)
        existing_records = parse_menu_process_records(existing_profile_fields.get(records_storage_key))
        default_scope_mode, default_scope_label = self._resolve_menu_scope_defaults(session)

        return (
            member,
            existing_profile_fields,
            existing_records,
            default_scope_mode,
            default_scope_label,
        )

    def load_record_bundle(
        self,
        session: Any,
        context: dict[str, Any] | None = None,
    ) -> tuple[Member | None, dict[str, str], list[dict[str, Any]], str, str]:
        return self._load_record_bundle(session, context)

    def _build_rows(
        self,
        records: list[dict[str, Any]],
        *,
        default_scope_mode: str,
        default_scope_label: str,
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        seen_keys: set[str] = set()

        for raw_record in records:
            values = raw_record.get("values") if isinstance(raw_record.get("values"), dict) else {}
            if not values:
                continue

            label = ""
            for raw_key in OBJETO_AUTORIZACAO_LABEL_VALUE_KEYS:
                candidate = str(values.get(raw_key) or "").strip()
                if candidate:
                    label = candidate
                    break
            if not label:
                continue

            record_id = str(raw_record.get("record_id") or "").strip()
            stored_key = str(values.get(OBJETO_AUTORIZACAO_TECHNICAL_KEY) or "").strip().lower()
            row_key = stored_key or build_objeto_autorizacao_key(label, fallback=record_id)

            if row_key in seen_keys:
                suffix = record_id[:8] if record_id else str(len(rows) + 1)
                row_key = f"{row_key}_{suffix}"
            seen_keys.add(row_key)

            scope_mode = _normalize_scope_mode(
                values.get(OBJETO_AUTORIZACAO_SCOPE_MODE_KEY),
                fallback=default_scope_mode,
            )
            scope_label = str(values.get(OBJETO_AUTORIZACAO_SCOPE_LABEL_KEY) or "").strip() or default_scope_label
            status_value = _normalize_status(values.get(OBJETO_AUTORIZACAO_STATUS_KEY))

            rows.append(
                {
                    "key": row_key,
                    "record_id": record_id,
                    "label": label,
                    "process_label": _resolve_display_value_from_values(
                        values,
                        key_candidates=OBJETO_AUTORIZACAO_PROCESS_DISPLAY_KEYS,
                    ),
                    "authorization_label": _resolve_display_value_from_values(
                        values,
                        key_candidates=OBJETO_AUTORIZACAO_AUTHORIZATION_DISPLAY_KEYS,
                    ),
                    "visibility_scope_mode": scope_mode,
                    "visibility_scope_label": scope_label or _scope_label(scope_mode),
                    "status": status_value,
                    "status_label": _status_label(status_value),
                    "created_at": str(raw_record.get("created_at") or "").strip(),
                    "section_key": str(raw_record.get("section_key") or "").strip() or OBJETO_AUTORIZACAO_SECTION_KEY,
                    "values": dict(values),
                }
            )

        return rows

    def list_rows(self, session: Any, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        (
            _member,
            _existing_profile_fields,
            existing_records,
            default_scope_mode,
            default_scope_label,
        ) = self._load_record_bundle(session, context)
        return self._build_rows(
            existing_records,
            default_scope_mode=default_scope_mode,
            default_scope_label=default_scope_label,
        )

    def get_for_edit(
        self,
        session: Any,
        edit_key: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        clean_edit_key = str(edit_key or "").strip().lower()
        if not clean_edit_key:
            return None

        for row in self.list_rows(session, context):
            if str(row.get("key") or "").strip().lower() == clean_edit_key:
                return dict(row)
        return None

    def save_row(
        self,
        session: Any,
        payload: dict[str, Any],
        *,
        context: dict[str, Any] | None = None,
        edit_key: str = "",
    ) -> tuple[bool, str, str]:
        (
            member,
            existing_profile_fields,
            existing_records,
            default_scope_mode,
            default_scope_label,
        ) = self._load_record_bundle(session, context)

        if member is None:
            return False, "member_not_found", ""

        label = str(payload.get("label") or "").strip()
        dynamic_values: dict[str, str] = {
            str(k): str(v or "").strip()
            for k, v in (payload.get("dynamic_values") or {}).items()
            if str(k or "").strip()
        }
        if not label and dynamic_values:
            label = next((v for v in dynamic_values.values() if v), "")
        if not label:
            return False, "empty_label", ""

        scope_mode = _normalize_scope_mode(
            payload.get("visibility_scope_mode"),
            fallback=default_scope_mode,
        )
        scope_label = _scope_label(scope_mode)
        status_value = _normalize_status(payload.get("status"))
        entity_number = str((context or {}).get("entity_number") or "").strip()
        requested_edit_key = str(edit_key or "").strip().lower()

        existing_rows = self._build_rows(
            existing_records,
            default_scope_mode=default_scope_mode,
            default_scope_label=default_scope_label,
        )
        record_index_by_key = {
            str(row.get("key") or "").strip().lower(): index
            for index, row in enumerate(existing_rows)
            if str(row.get("key") or "").strip()
        }
        generated_key = build_objeto_autorizacao_key(label, fallback=requested_edit_key)

        if requested_edit_key:
            target_index = record_index_by_key.get(requested_edit_key)
            if target_index is None:
                return False, "edit_key_not_found", ""
            conflicting_index = record_index_by_key.get(generated_key)
            if conflicting_index is not None and conflicting_index != target_index:
                return False, "duplicate_key", ""
        else:
            if generated_key in record_index_by_key:
                return False, "duplicate_key", ""
            target_index = None

        if target_index is None:
            target_record = {
                "record_id": uuid4().hex,
                "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
                "section_key": OBJETO_AUTORIZACAO_SECTION_KEY,
                "values": {},
            }
            existing_records.insert(0, target_record)
        else:
            target_record = existing_records[target_index]

        target_values = (
            dict(target_record.get("values"))
            if isinstance(target_record.get("values"), dict)
            else {}
        )
        target_values[OBJETO_AUTORIZACAO_TECHNICAL_KEY] = generated_key
        for _dk, _dv in dynamic_values.items():
            if _dk and _dv:
                target_values[_dk] = _dv
        target_values["objeto_de_autorizacao"] = label
        target_values["custom_objeto_label"] = label
        target_values[OBJETO_AUTORIZACAO_SCOPE_MODE_KEY] = scope_mode
        target_values[OBJETO_AUTORIZACAO_SCOPE_LABEL_KEY] = scope_label
        target_values[OBJETO_AUTORIZACAO_STATUS_KEY] = status_value
        if entity_number:
            target_values[OBJETO_AUTORIZACAO_ENTITY_NUMBER_KEY] = entity_number
        elif OBJETO_AUTORIZACAO_ENTITY_NUMBER_KEY in target_values and not str(
            target_values.get(OBJETO_AUTORIZACAO_ENTITY_NUMBER_KEY) or ""
        ).strip():
            target_values.pop(OBJETO_AUTORIZACAO_ENTITY_NUMBER_KEY, None)

        target_record["section_key"] = str(
            target_record.get("section_key") or OBJETO_AUTORIZACAO_SECTION_KEY
        ).strip() or OBJETO_AUTORIZACAO_SECTION_KEY
        target_record["values"] = target_values

        records_storage_key = build_menu_process_records_storage_key(OBJETO_AUTORIZACAO_STORAGE_KEY)
        serialized_records = serialize_menu_process_records(existing_records[:200])
        if serialized_records:
            existing_profile_fields[records_storage_key] = serialized_records
        else:
            existing_profile_fields.pop(records_storage_key, None)

        member.profile_custom_fields = serialize_member_profile_fields(existing_profile_fields)
        return True, "saved", generated_key
