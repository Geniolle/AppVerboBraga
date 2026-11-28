from __future__ import annotations

import unicodedata
from typing import Any
from urllib.parse import (
    parse_qsl,
    urlencode,
    urlsplit,
)
from fastapi import Request
from appgenesis.db.session import SessionLocal
from appgenesis.menu_settings import MENU_MEU_PERFIL_KEY
from appgenesis.services.page import build_users_new_url
from appgenesis.services.session import (
    get_current_user,
    get_session_entity_id,
)
from appgenesis.models import User

def _normalize_process_field_required(raw_required: Any) -> bool:
    if isinstance(raw_required, bool):
        return raw_required
    clean_value = str(raw_required or "").strip().lower()
    return clean_value in {"1", "true", "sim", "yes", "on"}

def _normalize_lookup_text(raw_value: Any) -> str:
    normalized = (
        unicodedata.normalize("NFKD", str(raw_value or ""))
        .encode("ascii", "ignore")
        .decode("ascii")
        .strip()
        .lower()
    )
    return " ".join(normalized.split())

def _is_absence_process(menu_key: str, process_setting: dict[str, Any] | None = None) -> bool:
    parts = [_normalize_lookup_text(menu_key)]
    if isinstance(process_setting, dict):
        parts.append(_normalize_lookup_text(process_setting.get("label")))
    joined = " ".join(part for part in parts if part)
    if not joined:
        return False
    return ("assiduidade" in joined) or ("ausencia" in joined)

def _normalize_process_state(raw_value: Any) -> str:
    clean_value = _normalize_lookup_text(raw_value)
    if clean_value in {"inativo", "inactive", "0", "false", "off"}:
        return "inativo"
    return "ativo"
# APPGENESIS_MEU_PERFIL_SUBSEQUENT_RULES_RESOLVER_V1_END


def _normalize_process_quantity_rules(raw_rules: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_rules, list):
        return []

    normalized_rules: list[dict[str, Any]] = []
    for raw_rule in raw_rules:
        if not isinstance(raw_rule, dict):
            continue
        rule_key = str(raw_rule.get("key") or "").strip().lower()
        quantity_field_key = str(raw_rule.get("quantity_field_key") or "").strip().lower()
        header_key = str(raw_rule.get("header_key") or "").strip().lower()
        item_label = str(raw_rule.get("item_label") or "").strip() or "Item"
        try:
            max_items = int(str(raw_rule.get("max_items") or "").strip())
        except (TypeError, ValueError):
            max_items = 1
        repeated_field_keys: list[str] = []
        seen_repeated_keys: set[str] = set()
        for raw_field_key in raw_rule.get("repeated_field_keys") or []:
            clean_field_key = str(raw_field_key or "").strip().lower()
            if not clean_field_key or clean_field_key in seen_repeated_keys:
                continue
            seen_repeated_keys.add(clean_field_key)
            repeated_field_keys.append(clean_field_key)
        if not rule_key or not quantity_field_key or not repeated_field_keys:
            continue
        normalized_rules.append(
            {
                "key": rule_key,
                "label": str(raw_rule.get("label") or rule_key).strip() or rule_key,
                "quantity_field_key": quantity_field_key,
                "repeated_field_keys": repeated_field_keys,
                "header_key": header_key,
                "max_items": max(1, min(max_items, 50)),
                "item_label": item_label,
            }
        )
    return normalized_rules
# APPGENESIS_RETURN_URL_POST_SAVE_V4_END


# APPGENESIS_BACKEND_RETURN_URL_POST_SAVE_V6_START
def _sanitize_users_new_return_url_post_save_v6(
    raw_return_url: Any,
    extra_params: dict[str, Any] | None = None,
) -> str:
    clean_return_url = str(raw_return_url or "").strip()

    if not clean_return_url:
        return ""

    try:
        parsed_url = urlsplit(clean_return_url)
    except Exception:
        return ""

    if parsed_url.scheme or parsed_url.netloc:
        return ""

    path = parsed_url.path or "/users/new"

    if path != "/users/new":
        return ""

    query_params = dict(parse_qsl(parsed_url.query, keep_blank_values=True))

    for raw_key, raw_value in (extra_params or {}).items():
        clean_key = str(raw_key or "").strip()
        clean_value = str(raw_value or "").strip()

        if clean_key and clean_value:
            query_params[clean_key] = clean_value

    query_params["appgenesis_after_save"] = "1"

    query_string = urlencode(query_params)
    fragment = f"#{parsed_url.fragment}" if parsed_url.fragment else ""

    return f"{path}?{query_string}{fragment}" if query_string else f"{path}{fragment}"


def _append_after_save_marker_to_users_new_url_v6(raw_url: str) -> str:
    clean_url = str(raw_url or "").strip()

    if not clean_url:
        return clean_url

    try:
        parsed_url = urlsplit(clean_url)
    except Exception:
        return clean_url

    if parsed_url.scheme or parsed_url.netloc:
        return clean_url

    path = parsed_url.path or "/users/new"

    if path != "/users/new":
        return clean_url

    query_params = dict(parse_qsl(parsed_url.query, keep_blank_values=True))
    query_params["appgenesis_after_save"] = "1"

    query_string = urlencode(query_params)
    fragment = f"#{parsed_url.fragment}" if parsed_url.fragment else ""

    return f"{path}?{query_string}{fragment}" if query_string else f"{path}{fragment}"


def _build_post_save_redirect_url_v6(
    submitted_form: Any,
    **params: Any,
) -> str:
    raw_return_url = ""

    if hasattr(submitted_form, "get"):
        raw_return_url = str(submitted_form.get("return_url") or "").strip()

    safe_return_url = _sanitize_users_new_return_url_post_save_v6(
        raw_return_url,
        params,
    )

    if safe_return_url:
        return safe_return_url

    normalized_params = dict(params)
    if hasattr(submitted_form, "get"):
        submitted_section = str(submitted_form.get("section_key") or "").strip()
        if submitted_section:
            normalized_params.setdefault("dynamic_process_section", submitted_section)
            normalized_params.setdefault("target", "#dynamic-process-card")

    has_profile_context = any(
        str(normalized_params.get(key) or "").strip()
        for key in (
            "profile_success",
            "profile_error",
            "profile_tab",
            "profile_section",
        )
    )

    if has_profile_context:
        normalized_params.setdefault("menu", MENU_MEU_PERFIL_KEY)
        normalized_params.setdefault("target", "#perfil-pessoal-card")
        normalized_params.setdefault("profile_tab", "pessoal")

    return _append_after_save_marker_to_users_new_url_v6(
        build_users_new_url(**normalized_params)
    )

def _menu_action_denied_v1(request: Request, menu_key: str, required_any: tuple[str, ...]) -> bool:
    # True quando o utilizador nao tem nenhuma das acoes exigidas no menu.
    from appgenesis.services.access_filter import resolve_menu_actions_v1

    with SessionLocal() as session:
        current_user = get_current_user(request, session)
        if current_user is None:
            return True
        user = session.get(User, current_user["id"])
        actions = resolve_menu_actions_v1(
            session,
            entity_id=get_session_entity_id(request),
            user_system_type=getattr(user, "system_type", ""),
            menu_key=menu_key,
        )
        return not any(action in actions for action in required_any)
