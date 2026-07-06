from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import select

from appgenesis.admin_subprocesses.repositories.base import BaseAdminSubprocessRepository
from appgenesis.menu_settings import (
    get_menu_visibility_scope_label,
    get_menu_visibility_scope_mode,
    get_sidebar_menu_settings,
)
from appgenesis.models import Member, User
from appgenesis.services.auth_profile_entity_scope import (
    AUTH_PROFILE_ENTITY_SCOPE_LABEL_STORAGE_KEY,
    AUTH_PROFILE_ENTITY_SCOPE_STORAGE_KEY,
    AUTH_PROFILE_ENTITY_SCOPE_SYSTEM,
    build_auth_profile_entity_context_v1,
    normalize_auth_profile_entity_scope_v1,
    resolve_auth_profile_entity_scope_from_values_v1,
    resolve_auth_profile_entity_scope_label_v1,
)
from appgenesis.services.profile import (
    build_menu_process_records_storage_key,
    parse_member_profile_fields,
    parse_menu_process_records,
    serialize_member_profile_fields,
    serialize_menu_process_records,
)


AUTH_PROFILE_MENU_KEY = "perfil_de_autorizacao"
AUTH_PROFILE_SECTION_KEY = "custom_perfil_header"
AUTH_PROFILE_DYNAMIC_SECTION_KEY = "custom_perfil"
AUTH_PROFILE_LABEL_VALUE_KEYS = ("custom_perfil", "custom_nome_do_perfil")
AUTH_PROFILE_SCOPE_MODE_KEY = "__scope_mode"
AUTH_PROFILE_SCOPE_LABEL_KEY = "__scope_label"
AUTH_PROFILE_STATUS_KEY = "__estado"
AUTH_PROFILE_TECHNICAL_KEY = "__key"
AUTH_PROFILE_MENU_VALUE_KEY = "__menu_key"
AUTH_PROFILE_ENTITY_NUMBER_KEY = "__numero_entidade"


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
    return normalized or "perfil"


def build_auth_profile_key(label: Any, *, fallback: str = "") -> str:
    clean_slug = _normalize_lookup_slug(label)
    if clean_slug:
        return clean_slug
    clean_fallback = _normalize_lookup_slug(fallback)
    return clean_fallback or "perfil"


def _normalize_menu_key(raw_value: Any) -> str:
    return str(raw_value or "").strip().lower()


def _build_sidebar_menu_lookup(
    session: Any,
) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    menu_meta_by_key: dict[str, dict[str, Any]] = {}
    menu_key_by_label_lookup: dict[str, str] = {}

    for raw_row in get_sidebar_menu_settings(session):
        if not isinstance(raw_row, dict):
            continue

        menu_key = _normalize_menu_key(raw_row.get("key"))
        if not menu_key:
            continue

        menu_label = str(raw_row.get("label") or menu_key).strip() or menu_key
        menu_meta_by_key[menu_key] = {
            "key": menu_key,
            "label": menu_label,
            "is_active": bool(raw_row.get("is_active")),
            "is_deleted": bool(raw_row.get("is_deleted")),
        }
        menu_label_lookup = _normalize_lookup_slug(menu_label)
        if menu_label_lookup and menu_label_lookup not in menu_key_by_label_lookup:
            menu_key_by_label_lookup[menu_label_lookup] = menu_key

    return menu_meta_by_key, menu_key_by_label_lookup


def _resolve_auth_profile_field_keys(session: Any) -> list[str]:
    for raw_row in get_sidebar_menu_settings(session):
        if not isinstance(raw_row, dict):
            continue
        if _normalize_menu_key(raw_row.get("key")) != AUTH_PROFILE_MENU_KEY:
            continue

        header_candidates = {AUTH_PROFILE_DYNAMIC_SECTION_KEY, AUTH_PROFILE_SECTION_KEY}
        field_type_by_key: dict[str, str] = {}
        ordered_field_keys: list[str] = []

        for collection_key in ("process_additional_fields", "process_field_options"):
            for raw_field in (raw_row.get(collection_key) or []):
                if not isinstance(raw_field, dict):
                    continue
                field_key = _normalize_menu_key(raw_field.get("key"))
                if not field_key:
                    continue
                field_type_by_key.setdefault(
                    field_key,
                    _normalize_menu_key(raw_field.get("field_type") or raw_field.get("type")),
                )

        for raw_visible_row in (raw_row.get("process_visible_field_rows") or []):
            if not isinstance(raw_visible_row, dict):
                continue
            header_key = _normalize_menu_key(raw_visible_row.get("header_key"))
            field_key = _normalize_menu_key(raw_visible_row.get("field_key"))
            if header_key not in header_candidates or not field_key:
                continue
            if field_type_by_key.get(field_key) == "header":
                continue
            if field_key not in ordered_field_keys:
                ordered_field_keys.append(field_key)

        return ordered_field_keys

    return []


# ###################################################################################
# (1) HELPERS DE FILTRO POR ENTIDADE
# ###################################################################################
def _row_matches_entity_context_v1(
    row: dict[str, Any],
    *,
    context: dict[str, Any] | None = None,
) -> bool:
    safe_context = context or {}
    current_entity_number = str(safe_context.get("entity_number") or "").strip()
    if not current_entity_number:
        return True

    row_values = row.get("values") if isinstance(row.get("values"), dict) else {}
    row_scope_mode = resolve_auth_profile_entity_scope_from_values_v1(row_values)
    if row_scope_mode == AUTH_PROFILE_ENTITY_SCOPE_SYSTEM:
        return True

    stored_entity_number = str(row.get("entity_number") or "").strip()
    if not stored_entity_number:
        stored_entity_number = str(row_values.get(AUTH_PROFILE_ENTITY_NUMBER_KEY) or "").strip()
    if not stored_entity_number:
        return True

    return stored_entity_number == current_entity_number


def _resolve_menu_selection_value(
    values: dict[str, Any],
    *,
    profile_field_keys: list[str],
    menu_meta_by_key: dict[str, dict[str, Any]],
    menu_key_by_label_lookup: dict[str, str],
) -> tuple[str, str]:
    explicit_value_candidates = [
        values.get(AUTH_PROFILE_MENU_VALUE_KEY),
        *[values.get(field_key) for field_key in profile_field_keys],
    ]

    for raw_candidate in explicit_value_candidates:
        clean_menu_key = _normalize_menu_key(raw_candidate)
        if clean_menu_key and clean_menu_key in menu_meta_by_key:
            return clean_menu_key, str(menu_meta_by_key[clean_menu_key].get("label") or clean_menu_key)

    label_candidates = [
        *[values.get(field_key) for field_key in profile_field_keys],
        *[values.get(raw_key) for raw_key in AUTH_PROFILE_LABEL_VALUE_KEYS],
    ]
    fallback_label = ""

    for raw_candidate in label_candidates:
        clean_label = str(raw_candidate or "").strip()
        if not clean_label:
            continue
        if not fallback_label:
            fallback_label = clean_label
        resolved_key = menu_key_by_label_lookup.get(_normalize_lookup_slug(clean_label))
        if resolved_key:
            resolved_meta = menu_meta_by_key.get(resolved_key) or {}
            resolved_label = str(resolved_meta.get("label") or clean_label).strip() or clean_label
            return resolved_key, resolved_label

    return "", fallback_label


def _resolve_primary_profile_label_from_records(
    records: list[dict[str, Any]],
    *,
    menu_meta_by_key: dict[str, dict[str, Any]],
    menu_key_by_label_lookup: dict[str, str],
    profile_field_keys: list[str],
) -> str:
    for raw_record in records:
        values = raw_record.get("values") if isinstance(raw_record.get("values"), dict) else {}
        if not values:
            continue
        _menu_key, resolved_label = _resolve_menu_selection_value(
            values,
            profile_field_keys=profile_field_keys,
            menu_meta_by_key=menu_meta_by_key,
            menu_key_by_label_lookup=menu_key_by_label_lookup,
        )
        if resolved_label:
            return resolved_label
        for value_key in AUTH_PROFILE_LABEL_VALUE_KEYS:
            candidate = str(values.get(value_key) or "").strip()
            if candidate:
                return candidate
    return ""


def _sync_legacy_profile_fields_after_record_change(
    existing_profile_fields: dict[str, str],
    *,
    removed_label: str,
    remaining_label: str,
) -> None:
    legacy_field_keys = (
        "process__perfil_de_autorizacao__custom_perfil",
        "custom_perfil",
        "custom_nome_do_perfil",
    )

    for legacy_field_key in legacy_field_keys:
        current_value = str(existing_profile_fields.get(legacy_field_key) or "").strip()
        if not current_value or current_value != removed_label:
            continue
        if remaining_label:
            existing_profile_fields[legacy_field_key] = remaining_label
        else:
            existing_profile_fields.pop(legacy_field_key, None)


class AuthorizationProfileAdminRepository(BaseAdminSubprocessRepository):
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
            if str(row.get("key") or "").strip().lower() != AUTH_PROFILE_MENU_KEY:
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
        records_storage_key = build_menu_process_records_storage_key(AUTH_PROFILE_MENU_KEY)
        existing_records = parse_menu_process_records(existing_profile_fields.get(records_storage_key))
        default_scope_mode, default_scope_label = self._resolve_menu_scope_defaults(session)

        if not existing_records:
            fallback_label = str(
                existing_profile_fields.get("process__perfil_de_autorizacao__custom_perfil") or ""
            ).strip()
            if fallback_label:
                existing_records = [
                    {
                        "record_id": "",
                        "created_at": "",
                        "section_key": AUTH_PROFILE_SECTION_KEY,
                        "values": {
                            "custom_perfil": fallback_label,
                            AUTH_PROFILE_STATUS_KEY: "ativo",
                        },
                    }
                ]

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
        menu_meta_by_key: dict[str, dict[str, Any]] | None = None,
        menu_key_by_label_lookup: dict[str, str] | None = None,
        profile_field_keys: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        seen_keys: set[str] = set()
        safe_menu_meta_by_key = menu_meta_by_key or {}
        safe_menu_key_by_label_lookup = menu_key_by_label_lookup or {}
        safe_profile_field_keys = profile_field_keys or []

        for raw_record in records:
            values = raw_record.get("values") if isinstance(raw_record.get("values"), dict) else {}
            if not values:
                continue

            stored_menu_key, resolved_menu_label = _resolve_menu_selection_value(
                values,
                profile_field_keys=safe_profile_field_keys,
                menu_meta_by_key=safe_menu_meta_by_key,
                menu_key_by_label_lookup=safe_menu_key_by_label_lookup,
            )
            label = resolved_menu_label
            if not label:
                for raw_key in AUTH_PROFILE_LABEL_VALUE_KEYS:
                    candidate = str(values.get(raw_key) or "").strip()
                    if candidate:
                        label = candidate
                        break
            if not label:
                continue

            record_id = str(raw_record.get("record_id") or "").strip()
            stored_key = str(values.get(AUTH_PROFILE_TECHNICAL_KEY) or "").strip().lower()
            row_key = stored_menu_key or stored_key or build_auth_profile_key(label, fallback=record_id)

            if row_key in seen_keys:
                suffix = record_id[:8] if record_id else str(len(rows) + 1)
                row_key = f"{row_key}_{suffix}"
            seen_keys.add(row_key)

            entity_scope_mode = resolve_auth_profile_entity_scope_from_values_v1(values)
            scope_mode = _normalize_scope_mode(
                values.get(AUTH_PROFILE_SCOPE_MODE_KEY),
                fallback=default_scope_mode,
            )
            scope_label = str(values.get(AUTH_PROFILE_SCOPE_LABEL_KEY) or "").strip() or default_scope_label
            status_value = _normalize_status(values.get(AUTH_PROFILE_STATUS_KEY))
            entity_number = str(values.get(AUTH_PROFILE_ENTITY_NUMBER_KEY) or "").strip()
            row_values = dict(values)
            if stored_menu_key:
                row_values[AUTH_PROFILE_MENU_VALUE_KEY] = stored_menu_key
                for field_key in safe_profile_field_keys:
                    if not str(row_values.get(field_key) or "").strip():
                        row_values[field_key] = stored_menu_key
                        break

            rows.append(
                {
                    "key": row_key,
                    "record_id": record_id,
                    "label": label,
                    "menu_key": stored_menu_key,
                    "entity_scope": entity_scope_mode,
                    "entity_scope_label": str(
                        values.get(AUTH_PROFILE_ENTITY_SCOPE_LABEL_STORAGE_KEY) or ""
                    ).strip() or resolve_auth_profile_entity_scope_label_v1(entity_scope_mode),
                    "entity_number": entity_number,
                    "visibility_scope_mode": scope_mode,
                    "visibility_scope_label": scope_label or _scope_label(scope_mode),
                    "status": status_value,
                    "status_label": _status_label(status_value),
                    "created_at": str(raw_record.get("created_at") or "").strip(),
                    "section_key": str(raw_record.get("section_key") or "").strip() or AUTH_PROFILE_SECTION_KEY,
                    "values": row_values,
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
        menu_meta_by_key, menu_key_by_label_lookup = _build_sidebar_menu_lookup(session)
        profile_field_keys = _resolve_auth_profile_field_keys(session)
        rows = self._build_rows(
            existing_records,
            default_scope_mode=default_scope_mode,
            default_scope_label=default_scope_label,
            menu_meta_by_key=menu_meta_by_key,
            menu_key_by_label_lookup=menu_key_by_label_lookup,
            profile_field_keys=profile_field_keys,
        )
        return [
            row
            for row in rows
            if _row_matches_entity_context_v1(row, context=context)
        ]

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
        menu_meta_by_key, menu_key_by_label_lookup = _build_sidebar_menu_lookup(session)
        profile_field_keys = _resolve_auth_profile_field_keys(session)
        selected_menu_key, resolved_menu_label = _resolve_menu_selection_value(
            dynamic_values,
            profile_field_keys=profile_field_keys,
            menu_meta_by_key=menu_meta_by_key,
            menu_key_by_label_lookup=menu_key_by_label_lookup,
        )
        if resolved_menu_label:
            label = resolved_menu_label
        elif not label and dynamic_values:
            label = next((value for value in dynamic_values.values() if value), "")
        if not label:
            return False, "empty_label", ""

        entity_context = dict((context or {}).get("auth_profile_entity_context") or {})
        if not entity_context:
            entity_context = build_auth_profile_entity_context_v1(
                session,
                selected_entity_id=(context or {}).get("selected_entity_id"),
                permissions=(context or {}).get("entity_permissions"),
            )
        entity_scope_mode = normalize_auth_profile_entity_scope_v1(
            payload.get("entity_scope"),
        )
        if entity_scope_mode not in set(entity_context.get("allowed_modes") or set()):
            return False, "invalid_entity_scope", ""

        scope_mode = _normalize_scope_mode(
            payload.get("visibility_scope_mode"),
            fallback=default_scope_mode,
        )
        scope_label = _scope_label(scope_mode)
        status_value = _normalize_status(payload.get("status"))
        entity_number = str(
            entity_context.get("selected_entity_number")
            or (context or {}).get("entity_number")
            or ""
        ).strip()
        requested_edit_key = str(edit_key or "").strip().lower()

        existing_rows = self._build_rows(
            existing_records,
            default_scope_mode=default_scope_mode,
            default_scope_label=default_scope_label,
            menu_meta_by_key=menu_meta_by_key,
            menu_key_by_label_lookup=menu_key_by_label_lookup,
            profile_field_keys=profile_field_keys,
        )
        entity_scoped_context = {**(context or {}), "entity_number": entity_number}
        record_index_by_key = {
            str(row.get("key") or "").strip().lower(): index
            for index, row in enumerate(existing_rows)
            if str(row.get("key") or "").strip()
            and _row_matches_entity_context_v1(row, context=entity_scoped_context)
        }
        generated_key = selected_menu_key or build_auth_profile_key(label, fallback=requested_edit_key)

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
                "section_key": AUTH_PROFILE_SECTION_KEY,
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
        target_values[AUTH_PROFILE_TECHNICAL_KEY] = generated_key
        if selected_menu_key:
            target_values[AUTH_PROFILE_MENU_VALUE_KEY] = selected_menu_key
        else:
            target_values.pop(AUTH_PROFILE_MENU_VALUE_KEY, None)
        for _dk, _dv in dynamic_values.items():
            if _dk and _dv:
                target_values[_dk] = _dv
        if selected_menu_key and profile_field_keys:
            primary_field_key = next((field_key for field_key in profile_field_keys if field_key), "")
            if primary_field_key and not str(target_values.get(primary_field_key) or "").strip():
                target_values[primary_field_key] = selected_menu_key
        target_values["custom_perfil"] = label
        target_values["custom_nome_do_perfil"] = label
        target_values[AUTH_PROFILE_ENTITY_SCOPE_STORAGE_KEY] = entity_scope_mode
        target_values[AUTH_PROFILE_ENTITY_SCOPE_LABEL_STORAGE_KEY] = (
            resolve_auth_profile_entity_scope_label_v1(entity_scope_mode)
        )
        target_values[AUTH_PROFILE_SCOPE_MODE_KEY] = scope_mode
        target_values[AUTH_PROFILE_SCOPE_LABEL_KEY] = scope_label
        target_values[AUTH_PROFILE_STATUS_KEY] = status_value
        if entity_scope_mode != AUTH_PROFILE_ENTITY_SCOPE_SYSTEM and entity_number:
            target_values[AUTH_PROFILE_ENTITY_NUMBER_KEY] = entity_number
        elif AUTH_PROFILE_ENTITY_NUMBER_KEY in target_values:
            target_values.pop(AUTH_PROFILE_ENTITY_NUMBER_KEY, None)

        target_record["section_key"] = str(
            target_record.get("section_key") or AUTH_PROFILE_SECTION_KEY
        ).strip() or AUTH_PROFILE_SECTION_KEY
        target_record["values"] = target_values

        records_storage_key = build_menu_process_records_storage_key(AUTH_PROFILE_MENU_KEY)
        serialized_records = serialize_menu_process_records(existing_records[:200])
        if serialized_records:
            existing_profile_fields[records_storage_key] = serialized_records
        else:
            existing_profile_fields.pop(records_storage_key, None)

        existing_profile_fields["process__perfil_de_autorizacao__custom_perfil"] = label
        member.profile_custom_fields = serialize_member_profile_fields(existing_profile_fields)
        return True, "saved", generated_key

    def delete_row(
        self,
        session: Any,
        edit_key: str,
        *,
        context: dict[str, Any] | None = None,
    ) -> tuple[bool, str]:
        (
            member,
            existing_profile_fields,
            existing_records,
            default_scope_mode,
            default_scope_label,
        ) = self._load_record_bundle(session, context)

        if member is None:
            return False, "member_not_found"

        clean_edit_key = str(edit_key or "").strip().lower()
        if not clean_edit_key:
            return False, "delete_key_not_found"

        menu_meta_by_key, menu_key_by_label_lookup = _build_sidebar_menu_lookup(session)
        profile_field_keys = _resolve_auth_profile_field_keys(session)
        existing_rows = self._build_rows(
            existing_records,
            default_scope_mode=default_scope_mode,
            default_scope_label=default_scope_label,
            menu_meta_by_key=menu_meta_by_key,
            menu_key_by_label_lookup=menu_key_by_label_lookup,
            profile_field_keys=profile_field_keys,
        )
        existing_rows = [
            row
            for row in existing_rows
            if _row_matches_entity_context_v1(row, context=context)
        ]
        target_row = next(
            (
                row
                for row in existing_rows
                if str(row.get("key") or "").strip().lower() == clean_edit_key
            ),
            None,
        )
        if not isinstance(target_row, dict):
            return False, "delete_key_not_found"
        target_record_id = str(target_row.get("record_id") or "").strip()
        target_menu_key = str(target_row.get("menu_key") or "").strip().lower()
        target_technical_key = str(
            (target_row.get("values") or {}).get(AUTH_PROFILE_TECHNICAL_KEY) if isinstance(target_row.get("values"), dict) else ""
        ).strip().lower()

        filtered_records: list[dict[str, Any]] = []
        removed = False
        for raw_record in existing_records:
            record_values = raw_record.get("values") if isinstance(raw_record.get("values"), dict) else {}
            raw_record_id = str(raw_record.get("record_id") or "").strip()
            raw_menu_key = str(record_values.get(AUTH_PROFILE_MENU_VALUE_KEY) or "").strip().lower()
            raw_technical_key = str(record_values.get(AUTH_PROFILE_TECHNICAL_KEY) or "").strip().lower()

            matches_target = False
            if target_record_id and raw_record_id == target_record_id:
                matches_target = True
            elif target_menu_key and raw_menu_key == target_menu_key:
                matches_target = True
            elif target_technical_key and raw_technical_key == target_technical_key:
                matches_target = True

            if not removed and matches_target:
                removed = True
                continue

            filtered_records.append(raw_record)

        if not removed:
            return False, "delete_key_not_found"

        removed_label = str(target_row.get("label") or "").strip()
        existing_records = filtered_records

        records_storage_key = build_menu_process_records_storage_key(AUTH_PROFILE_MENU_KEY)
        serialized_records = serialize_menu_process_records(existing_records[:200])
        if serialized_records:
            existing_profile_fields[records_storage_key] = serialized_records
        else:
            existing_profile_fields.pop(records_storage_key, None)

        remaining_label = _resolve_primary_profile_label_from_records(
            existing_records,
            menu_meta_by_key=menu_meta_by_key,
            menu_key_by_label_lookup=menu_key_by_label_lookup,
            profile_field_keys=profile_field_keys,
        )
        _sync_legacy_profile_fields_after_record_change(
            existing_profile_fields,
            removed_label=removed_label,
            remaining_label=remaining_label,
        )

        member.profile_custom_fields = serialize_member_profile_fields(existing_profile_fields)
        return True, "deleted"
