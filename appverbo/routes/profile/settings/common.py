from __future__ import annotations

import re
import unicodedata


####################################################################################
# (1) NORMALIZAÇÃO GERAL
####################################################################################

def normalize_settings_text_v1(value: object) -> str:
    return str(value or "").strip()


def normalize_settings_lookup_text_v1(value: object) -> str:
    normalized = unicodedata.normalize("NFKD", str(value or ""))
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    normalized = normalized.strip().lower()
    return " ".join(normalized.split())


def slugify_settings_key_v1(value: object, fallback: str = "novo_item") -> str:
    raw_value = normalize_settings_text_v1(value).lower()
    raw_value = unicodedata.normalize("NFD", raw_value)
    raw_value = "".join(char for char in raw_value if unicodedata.category(char) != "Mn")
    raw_value = re.sub(r"[^a-z0-9]+", "_", raw_value)
    raw_value = re.sub(r"_+", "_", raw_value).strip("_")

    if raw_value and raw_value[0].isdigit():
        raw_value = f"item_{raw_value}"

    return raw_value or fallback


def normalize_settings_status_v1(value: object) -> str:
    clean_value = normalize_settings_text_v1(value).lower()

    if clean_value in {"inativo", "inactive", "0", "false", "no", "nao", "não", "off"}:
        return "inativo"

    return "ativo"


def settings_status_label_v1(value: object) -> str:
    return "Inativo" if normalize_settings_status_v1(value) == "inativo" else "Ativo"


####################################################################################
# (2) VISIBILIDADE
####################################################################################

def normalize_settings_visibility_scope_v1(value: object) -> str:
    clean_value = normalize_settings_text_v1(value).lower()

    if clean_value in {"owner", "legado"}:
        return clean_value

    return "all"


def settings_visibility_scope_to_scopes_v1(value: object) -> list[str]:
    clean_value = normalize_settings_visibility_scope_v1(value)

    if clean_value in {"owner", "legado"}:
        return [clean_value]

    return ["owner", "legado"]


def settings_visibility_scope_label_v1(value: object) -> str:
    clean_value = normalize_settings_visibility_scope_v1(value)

    if clean_value == "owner":
        return "Owner"

    if clean_value == "legado":
        return "Legado"

    return "Default"
