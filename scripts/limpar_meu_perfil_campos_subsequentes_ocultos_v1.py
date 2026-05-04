from __future__ import annotations

####################################################################################
# (1) BOOTSTRAP DO PROJETO
####################################################################################

from pathlib import Path
import argparse
import json
import sys
from datetime import date, datetime, timezone
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


####################################################################################
# (2) IMPORTS DO PROJETO
####################################################################################

from sqlalchemy import text

from appverbo.core import SessionLocal
from appverbo.services.profile import (
    get_hidden_process_targets_from_rules,
    parse_member_profile_fields,
    serialize_member_profile_fields,
)


####################################################################################
# (3) CONSTANTES
####################################################################################

MENU_KEY = "meu_perfil"
LEGACY_MENU_KEY = "documentos"

SUBSEQUENT_KEYS_TO_CHECK = [
    "process_subsequent_fields",
    "subsequent_fields",
    "process_subsequent_rules",
]


####################################################################################
# (4) FUNÇÕES AUXILIARES
####################################################################################

def normalize_key_v1(value: Any) -> str:
    return str(value or "").strip().lower()


def safe_json_loads_v1(raw_value: Any, fallback: Any) -> Any:
    if raw_value is None:
        return fallback

    if isinstance(raw_value, (dict, list)):
        return raw_value

    clean_value = str(raw_value or "").strip()

    if not clean_value:
        return fallback

    try:
        parsed_value = json.loads(clean_value)
    except Exception:
        return fallback

    return parsed_value


def json_dumps_v1(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def format_date_value_v1(value: Any) -> str:
    if value is None:
        return ""

    if isinstance(value, (date, datetime)):
        return value.strftime("%d/%m/%Y")

    return str(value or "").strip()


def collect_subsequent_rules_v1(menu_config: dict[str, Any]) -> list[dict[str, Any]]:
    rules: list[dict[str, Any]] = []

    for storage_key in SUBSEQUENT_KEYS_TO_CHECK:
        raw_rules = menu_config.get(storage_key)

        if not isinstance(raw_rules, list):
            continue

        for raw_rule in raw_rules:
            if isinstance(raw_rule, dict):
                rules.append(raw_rule)

    return rules


def extract_visible_field_metadata_v1(menu_config: dict[str, Any]) -> dict[str, Any]:
    additional_fields_raw = menu_config.get("additional_fields", [])
    visible_fields_raw = menu_config.get("process_visible_fields", [])
    visible_rows_raw = menu_config.get("process_visible_field_rows", [])
    header_map_raw = menu_config.get("process_visible_field_header_map", {})

    if not isinstance(additional_fields_raw, list):
        additional_fields_raw = []

    if not isinstance(visible_fields_raw, list):
        visible_fields_raw = []

    if not isinstance(visible_rows_raw, list):
        visible_rows_raw = []

    if not isinstance(header_map_raw, dict):
        header_map_raw = {}

    custom_field_types: dict[str, str] = {}
    labels_by_key: dict[str, str] = {}
    header_keys: set[str] = set()

    for raw_field in additional_fields_raw:
        if not isinstance(raw_field, dict):
            continue

        field_key = normalize_key_v1(raw_field.get("key"))
        field_label = str(raw_field.get("label") or "").strip()
        field_type = normalize_key_v1(raw_field.get("field_type") or raw_field.get("type") or "text")

        if not field_key:
            continue

        custom_field_types[field_key] = field_type
        labels_by_key[field_key] = field_label or field_key

        if field_type == "header":
            header_keys.add(field_key)

    visible_field_keys: list[str] = []
    seen_visible: set[str] = set()
    header_by_field: dict[str, str] = {}

    for raw_field_key in visible_fields_raw:
        field_key = normalize_key_v1(raw_field_key)

        if field_key and field_key not in seen_visible:
            seen_visible.add(field_key)
            visible_field_keys.append(field_key)

    for raw_row in visible_rows_raw:
        if not isinstance(raw_row, dict):
            continue

        field_key = normalize_key_v1(raw_row.get("field_key"))
        header_key = normalize_key_v1(raw_row.get("header_key"))

        if field_key and field_key not in seen_visible:
            seen_visible.add(field_key)
            visible_field_keys.append(field_key)

        if field_key and header_key:
            header_by_field[field_key] = header_key

    for raw_field_key, raw_header_key in header_map_raw.items():
        field_key = normalize_key_v1(raw_field_key)
        header_key = normalize_key_v1(raw_header_key)

        if field_key and header_key:
            header_by_field[field_key] = header_key

    visible_custom_fields = [
        field_key
        for field_key in visible_field_keys
        if field_key.startswith("custom_")
        and custom_field_types.get(field_key) != "header"
    ]

    return {
        "visible_custom_fields": visible_custom_fields,
        "header_by_field": header_by_field,
        "labels_by_key": labels_by_key,
        "header_keys": header_keys,
    }


def build_values_by_field_v1(member_row: dict[str, Any], profile_values: dict[str, str]) -> dict[str, str]:
    values_by_field: dict[str, str] = dict(profile_values)

    values_by_field["nome"] = str(member_row.get("full_name") or "").strip()
    values_by_field["telefone"] = str(member_row.get("primary_phone") or "").strip()
    values_by_field["email"] = str(
        member_row.get("login_email")
        or member_row.get("email")
        or ""
    ).strip().lower()
    values_by_field["pais"] = str(member_row.get("country") or "").strip()
    values_by_field["data_nascimento"] = format_date_value_v1(member_row.get("birth_date"))

    return values_by_field


def resolve_hidden_custom_fields_v1(
    hidden_targets: set[str],
    visible_custom_fields: list[str],
    header_by_field: dict[str, str],
) -> set[str]:
    clean_hidden_targets = {
        normalize_key_v1(hidden_target)
        for hidden_target in hidden_targets
        if normalize_key_v1(hidden_target)
    }

    fields_to_clear: set[str] = set()

    for field_key in visible_custom_fields:
        clean_field_key = normalize_key_v1(field_key)
        clean_header_key = normalize_key_v1(header_by_field.get(clean_field_key))

        if clean_field_key in clean_hidden_targets:
            fields_to_clear.add(clean_field_key)
            continue

        if clean_header_key and clean_header_key in clean_hidden_targets:
            fields_to_clear.add(clean_field_key)

    return fields_to_clear


####################################################################################
# (5) PROCESSO PRINCIPAL
####################################################################################

def main_v1() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Aplicar limpeza na base.")
    args = parser.parse_args()

    apply_changes = bool(args.apply)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_dir = PROJECT_ROOT / "backups" / "meu_perfil_subsequent_cleanup"
    backup_dir.mkdir(parents=True, exist_ok=True)

    backup_path = backup_dir / f"meu_perfil_subsequent_cleanup_backup_{timestamp}.json"

    with SessionLocal() as session:
        menu_row = session.execute(
            text(
                """
                SELECT id, menu_key, menu_label, menu_config
                FROM sidebar_menu_settings
                WHERE lower(trim(menu_key)) IN (:menu_key, :legacy_menu_key)
                ORDER BY CASE WHEN lower(trim(menu_key)) = :menu_key THEN 0 ELSE 1 END
                LIMIT 1
                """
            ),
            {
                "menu_key": MENU_KEY,
                "legacy_menu_key": LEGACY_MENU_KEY,
            },
        ).mappings().first()

        if menu_row is None:
            raise SystemExit("ERRO: menu Meu perfil não encontrado.")

        menu_config = safe_json_loads_v1(menu_row.get("menu_config"), {})

        if not isinstance(menu_config, dict):
            raise SystemExit("ERRO: menu_config inválido.")

        rules = collect_subsequent_rules_v1(menu_config)
        field_metadata = extract_visible_field_metadata_v1(menu_config)

        member_rows = session.execute(
            text(
                """
                SELECT
                    members.id,
                    members.full_name,
                    members.email,
                    members.primary_phone,
                    members.country,
                    members.birth_date,
                    members.profile_custom_fields,
                    (
                        SELECT users.login_email
                        FROM users
                        WHERE users.member_id = members.id
                        ORDER BY users.id
                        LIMIT 1
                    ) AS login_email
                FROM members
                ORDER BY members.id
                """
            )
        ).mappings().all()

        updates: list[dict[str, Any]] = []

        for member_row in member_rows:
            profile_values = parse_member_profile_fields(member_row.get("profile_custom_fields"))
            values_by_field = build_values_by_field_v1(dict(member_row), profile_values)

            hidden_targets = get_hidden_process_targets_from_rules(
                rules,
                values_by_field,
            )

            fields_to_clear = resolve_hidden_custom_fields_v1(
                hidden_targets,
                field_metadata["visible_custom_fields"],
                field_metadata["header_by_field"],
            )

            existing_fields_to_clear = [
                field_key
                for field_key in sorted(fields_to_clear)
                if field_key in profile_values
            ]

            if not existing_fields_to_clear:
                continue

            cleaned_profile_values = dict(profile_values)

            for field_key in existing_fields_to_clear:
                cleaned_profile_values.pop(field_key, None)

            updates.append(
                {
                    "member_id": int(member_row.get("id")),
                    "full_name": str(member_row.get("full_name") or ""),
                    "email": str(member_row.get("email") or ""),
                    "old_profile_custom_fields": member_row.get("profile_custom_fields"),
                    "new_profile_custom_fields": serialize_member_profile_fields(cleaned_profile_values),
                    "removed_fields": existing_fields_to_clear,
                }
            )

        backup_payload = {
            "created_at_utc": timestamp,
            "apply_changes": apply_changes,
            "menu": {
                "id": int(menu_row.get("id")),
                "menu_key": str(menu_row.get("menu_key") or ""),
                "menu_label": str(menu_row.get("menu_label") or ""),
                "menu_config": menu_row.get("menu_config"),
            },
            "updates": updates,
        }

        backup_path.write_text(json_dumps_v1(backup_payload), encoding="utf-8")

        print("")
        print("===== BACKUP =====")
        print(f"Backup criado em: {backup_path}")

        print("")
        print("===== REGRAS CONSIDERADAS =====")
        print(f"Quantidade de regras: {len(rules)}")

        print("")
        print("===== CAMPOS A LIMPAR POR ESTAREM OCULTOS =====")

        if not updates:
            print("- Nenhum valor oculto encontrado para limpar.")

        for update_item in updates:
            print("")
            print(f"- member_id={update_item['member_id']}")
            print(f"  nome={update_item['full_name']}")
            print(f"  email={update_item['email']}")
            print(f"  limpar={', '.join(update_item['removed_fields'])}")

        if not apply_changes:
            print("")
            print("MODO SIMULAÇÃO: nenhuma alteração foi aplicada.")
            return

        for update_item in updates:
            session.execute(
                text(
                    """
                    UPDATE members
                    SET profile_custom_fields = :profile_custom_fields
                    WHERE id = :member_id
                    """
                ),
                {
                    "member_id": int(update_item["member_id"]),
                    "profile_custom_fields": update_item["new_profile_custom_fields"],
                },
            )

        session.commit()

        print("")
        print("===== LIMPEZA APLICADA =====")
        print(f"Membros atualizados: {len(updates)}")
        print("OK: valores ocultos removidos.")


if __name__ == "__main__":
    main_v1()
