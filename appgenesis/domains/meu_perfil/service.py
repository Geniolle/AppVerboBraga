from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from jinja2.runtime import Undefined

from appgenesis.domains.meu_perfil.constants import (
    MEU_PERFIL_MENU_ALIASES_V1,
    MEU_PERFIL_MENU_KEY_V1,
    MEU_PERFIL_TAB_MORADA_V1,
    MEU_PERFIL_TAB_PESSOAL_V1,
    MEU_PERFIL_TAB_TARGETS_V1,
    MEU_PERFIL_TAB_TREINAMENTO_V1,
    MEU_PERFIL_TABS_V1,
)


@dataclass(frozen=True)
class MeuPerfilNavigationStateV1:
    menu_key: str
    tab: str
    target: str
    section: str

    def to_dict(self) -> dict[str, str]:
        return {
            "menu_key": self.menu_key,
            "tab": self.tab,
            "target": self.target,
            "section": self.section,
        }


def normalize_meu_perfil_menu_key_v1(raw_value: Any) -> str:
    clean_value = str(raw_value or "").strip().lower()
    if not clean_value:
        return ""
    if clean_value == MEU_PERFIL_MENU_KEY_V1 or clean_value in MEU_PERFIL_MENU_ALIASES_V1:
        return MEU_PERFIL_MENU_KEY_V1
    return clean_value


def normalize_meu_perfil_tab_key_v1(raw_value: Any) -> str:
    clean_value = str(raw_value or "").strip().lower()
    if clean_value in {MEU_PERFIL_TAB_PESSOAL_V1, MEU_PERFIL_TAB_MORADA_V1, MEU_PERFIL_TAB_TREINAMENTO_V1}:
        return clean_value
    return MEU_PERFIL_TAB_PESSOAL_V1


def resolve_meu_perfil_tab_target_v1(tab_key: Any) -> str:
    clean_tab_key = normalize_meu_perfil_tab_key_v1(tab_key)
    return MEU_PERFIL_TAB_TARGETS_V1.get(clean_tab_key, MEU_PERFIL_TAB_TARGETS_V1[MEU_PERFIL_TAB_PESSOAL_V1])


def resolve_meu_perfil_personal_card_target_v1() -> str:
    return MEU_PERFIL_TAB_TARGETS_V1[MEU_PERFIL_TAB_PESSOAL_V1]


def resolve_meu_perfil_section_key_v1(raw_value: Any, default_section: str = "") -> str:
    clean_value = str(raw_value or "").strip().lower()
    if clean_value:
        return clean_value
    return str(default_section or "").strip().lower()


def _json_safe_value_v1(raw_value: Any) -> Any:
    if isinstance(raw_value, Undefined):
        return ""
    if raw_value is None or isinstance(raw_value, (str, int, float, bool)):
        return raw_value
    if isinstance(raw_value, dict):
        return {str(key): _json_safe_value_v1(value) for key, value in raw_value.items()}
    if isinstance(raw_value, (list, tuple, set)):
        return [_json_safe_value_v1(item) for item in raw_value]
    if hasattr(raw_value, "to_dict") and callable(getattr(raw_value, "to_dict")):
        return _json_safe_value_v1(raw_value.to_dict())
    return str(raw_value)


def build_meu_perfil_personal_sections_state_v1(
    *,
    profile_personal_visible_fields: list[str] | None,
    profile_personal_field_labels: dict[str, str] | None,
    profile_personal_field_types: dict[str, str] | None,
    profile_personal_field_header_map: dict[str, str] | None,
    profile_personal_custom_field_meta: dict[str, dict[str, Any]] | None,
    resolved_process_sections: list[dict[str, Any]] | None = None,
    requested_profile_section: Any = "",
    hidden_section_keys: list[str] | set[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    clean_visible_fields = [
        str(field_key or "").strip().lower()
        for field_key in (profile_personal_visible_fields or [])
        if str(field_key or "").strip()
    ]
    clean_labels = {
        str(field_key or "").strip().lower(): str(label or "").strip()
        for field_key, label in (profile_personal_field_labels or {}).items()
        if str(field_key or "").strip()
    }
    clean_types = {
        str(field_key or "").strip().lower(): str(field_type or "").strip().lower()
        for field_key, field_type in (profile_personal_field_types or {}).items()
        if str(field_key or "").strip()
    }
    clean_header_map = {
        str(field_key or "").strip().lower(): str(header_key or "").strip().lower()
        for field_key, header_key in (profile_personal_field_header_map or {}).items()
        if str(field_key or "").strip()
    }
    clean_custom_meta = profile_personal_custom_field_meta or {}
    clean_hidden_keys = {
        str(section_key or "").strip().lower()
        for section_key in (hidden_section_keys or [])
        if str(section_key or "").strip()
    }

    profile_header_field_keys = {
        clean_key
        for clean_key, meta in clean_custom_meta.items()
        if clean_key.startswith("custom_")
        and str((meta or {}).get("field_type") or "").strip().lower() == "header"
    }
    clean_resolved_sections = []
    for section in (resolved_process_sections or []):
        if not isinstance(section, dict):
            continue
        clean_section_key = str((section or {}).get("key") or "").strip().lower()
        if not clean_section_key:
            continue
        quantity_rule_keys = [
            str(raw_key or "").strip().lower()
            for raw_key in (section.get("quantity_rule_keys") or [])
            if str(raw_key or "").strip()
        ]
        if clean_section_key not in profile_header_field_keys and not quantity_rule_keys:
            continue
        clean_resolved_sections.append(
            {
                "key": clean_section_key,
                "label": str((section or {}).get("label") or "").strip(),
                "quantity_rule_keys": quantity_rule_keys,
            }
        )
    resolved_section_keys = {
        str(section["key"] or "").strip().lower()
        for section in clean_resolved_sections
        if str(section["key"] or "").strip()
    }
    resolved_section_meta_by_key = {
        str(section["key"] or "").strip().lower(): {
            "field_keys": [
                str(raw_key or "").strip().lower()
                for raw_key in (section.get("field_keys") or [])
                if str(raw_key or "").strip()
            ],
            "quantity_rule_keys": [
                str(raw_key or "").strip().lower()
                for raw_key in (section.get("quantity_rule_keys") or [])
                if str(raw_key or "").strip()
            ],
        }
        for section in clean_resolved_sections
        if str(section["key"] or "").strip()
    }

    personal_sections: list[dict[str, Any]] = []
    personal_section_order: list[str] = []
    personal_section_seen: set[str] = set()

    def append_personal_section_v1(raw_section_key: Any, raw_section_label: Any = "") -> None:
        clean_section_key = str(raw_section_key or "").strip().lower()
        if not clean_section_key or clean_section_key in personal_section_seen:
            return
        if clean_section_key in clean_hidden_keys:
            return
        if clean_section_key not in profile_header_field_keys and clean_section_key not in resolved_section_keys:
            return

        canonical_section_label = str(clean_labels.get(clean_section_key) or "").strip()
        if not canonical_section_label:
            section_meta = clean_custom_meta.get(clean_section_key) if isinstance(clean_custom_meta, dict) else None
            if isinstance(section_meta, dict):
                canonical_section_label = str(
                    section_meta.get("label")
                    or section_meta.get("field_label")
                    or section_meta.get("display_label")
                    or ""
                ).strip()
        fallback_section_label = str(raw_section_label or "").strip()

        personal_sections.append(
            {
                "key": clean_section_key,
                "label": canonical_section_label
                or fallback_section_label
                or "Aba",
                "field_keys": list(
                    resolved_section_meta_by_key.get(clean_section_key, {}).get("field_keys") or []
                ),
                "quantity_rule_keys": list(
                    resolved_section_meta_by_key.get(clean_section_key, {}).get("quantity_rule_keys") or []
                ),
                "order": len(personal_sections) + 1,
                "is_visible": True,
                "is_active": True,
            }
        )
        personal_section_order.append(clean_section_key)
        personal_section_seen.add(clean_section_key)

    for section in clean_resolved_sections:
        append_personal_section_v1(section["key"], section["label"])

    for field_key in clean_visible_fields:
        append_personal_section_v1(field_key)

    for header_key in clean_header_map.values():
        append_personal_section_v1(header_key)

    default_personal_section = personal_section_order[0] if personal_section_order else ""
    requested_personal_section = resolve_meu_perfil_section_key_v1(
        requested_profile_section,
        default_section=default_personal_section,
    )
    if requested_personal_section not in personal_section_seen:
        requested_personal_section = default_personal_section
    if requested_personal_section in clean_hidden_keys:
        requested_personal_section = default_personal_section

    personal_field_section_map: dict[str, str] = {}
    for field_key in clean_visible_fields:
        field_type = clean_types.get(field_key, "")
        if field_type == "header":
            continue

        configured_header_key = clean_header_map.get(field_key, "")
        if configured_header_key in personal_section_seen:
            personal_field_section_map[field_key] = configured_header_key
        else:
            personal_field_section_map[field_key] = default_personal_section

    return {
        "personalSections": personal_sections,
        "personalFieldSectionMap": personal_field_section_map,
        "activePersonalSection": requested_personal_section,
        "defaultPersonalSection": default_personal_section,
        "hiddenPersonalSectionKeys": sorted(clean_hidden_keys),
    }


def build_meu_perfil_navigation_state_v1(
    *,
    menu_key: Any,
    profile_tab: Any,
    profile_section: Any = "",
    target: Any = "",
) -> MeuPerfilNavigationStateV1:
    clean_menu_key = normalize_meu_perfil_menu_key_v1(menu_key) or MEU_PERFIL_MENU_KEY_V1
    clean_tab = normalize_meu_perfil_tab_key_v1(profile_tab)
    clean_target = str(target or "").strip()
    if clean_target not in set(MEU_PERFIL_TAB_TARGETS_V1.values()):
        clean_target = resolve_meu_perfil_tab_target_v1(clean_tab)
    clean_section = resolve_meu_perfil_section_key_v1(profile_section)
    return MeuPerfilNavigationStateV1(
        menu_key=clean_menu_key,
        tab=clean_tab,
        target=clean_target,
        section=clean_section,
    )


def build_meu_perfil_bootstrap_v1(
    *,
    profile_tab: Any,
    profile_section: Any,
    profile_personal_sections: list[dict[str, Any]] | None,
    profile_personal_visible_fields: list[str] | None = None,
    profile_personal_field_labels: dict[str, str] | None = None,
) -> dict[str, Any]:
    navigation_state = build_meu_perfil_navigation_state_v1(
        menu_key=MEU_PERFIL_MENU_KEY_V1,
        profile_tab=profile_tab,
        profile_section=profile_section,
    )
    clean_personal_sections = [_json_safe_value_v1(dict(item)) for item in (profile_personal_sections or [])]
    default_personal_section = ""
    if clean_personal_sections:
        default_personal_section = str(clean_personal_sections[0].get("key") or "").strip().lower()
    clean_active_personal_section = resolve_meu_perfil_section_key_v1(
        profile_section,
        default_section=default_personal_section,
    )
    if clean_active_personal_section and clean_personal_sections:
        known_section_keys = {
            str(item.get("key") or "").strip().lower()
            for item in clean_personal_sections
            if isinstance(item, dict)
        }
        if clean_active_personal_section not in known_section_keys and default_personal_section:
            clean_active_personal_section = default_personal_section
    return {
        "menuKey": navigation_state.menu_key,
        "tabs": [tab.to_dict() for tab in MEU_PERFIL_TABS_V1],
        "activeTab": navigation_state.tab,
        "activeTarget": navigation_state.target,
        "activeSection": clean_active_personal_section or navigation_state.section,
        "activePersonalSection": clean_active_personal_section or navigation_state.section,
        "personalCardTarget": resolve_meu_perfil_personal_card_target_v1(),
        "personalSections": clean_personal_sections,
        "visibleFields": [_json_safe_value_v1(item) for item in (profile_personal_visible_fields or [])],
        "fieldLabels": _json_safe_value_v1(dict(profile_personal_field_labels or {})),
    }


__all__ = [
    "MEU_PERFIL_MENU_KEY_V1",
    "MEU_PERFIL_TABS_V1",
    "build_meu_perfil_bootstrap_v1",
    "build_meu_perfil_personal_sections_state_v1",
    "build_meu_perfil_navigation_state_v1",
    "normalize_meu_perfil_menu_key_v1",
    "normalize_meu_perfil_tab_key_v1",
    "resolve_meu_perfil_personal_card_target_v1",
    "resolve_meu_perfil_section_key_v1",
    "resolve_meu_perfil_tab_target_v1",
]
