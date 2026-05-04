from __future__ import annotations

####################################################################################
# (1) BOOTSTRAP DO PROJETO
####################################################################################

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


####################################################################################
# (2) IMPORTS
####################################################################################

import argparse
import json
import unicodedata
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text

from appverbo.core import SessionLocal


####################################################################################
# (3) CONSTANTES
####################################################################################

MENU_KEY = "meu_perfil"
LEGACY_MENU_KEY = "documentos"

SYSTEM_FIELD_LABELS = {
    "nome": "Nome",
    "telefone": "Telefone",
    "email": "Email",
    "pais": "País",
    "data_nascimento": "Data de nascimento",
    "whatsapp": "WhatsApp",
    "autorizacao_whatsapp": "Autorização para avisos por WhatsApp",
    "conta": "Conta",
    "estado_membro": "Estado de membro",
    "colaborador": "Colaborador",
    "entidades": "Entidades",
    "ultima_verificacao_whatsapp": "Última verificação WhatsApp",
    "detalhe_verificacao": "Detalhe da verificação",
}

DUPLICATE_CUSTOM_TO_SYSTEM = {
    "custom_nome": "nome",
    "custom_email": "email",
    "custom_telefone": "telefone",
    "custom_pais": "pais",
    "custom_data_de_nascimento": "data_nascimento",
}

FIELDS_TO_DELETE_EXPLICIT = {
    "custom_alocacao_extra",
    "custom_alocacoes_mensais",
    "custom_cidade",
    "custom_codigo_postal",
    "custom_data_de_nascimento",
    "custom_dia_da_semana",
    "custom_discipulado_verbo_da_vida",
    "custom_ebvv",
    "custom_email",
    "custom_escala_de_missoes_rhema",
    "custom_escola_ministerial",
    "custom_freguesia",
    "custom_morada",
    "custom_nome",
    "custom_pais",
    "custom_porta",
    "custom_rhema_brasil",
    "custom_semana_preferencial",
    "custom_telefone",
    "custom_whatsapp",
}


####################################################################################
# (4) FUNÇÕES AUXILIARES
####################################################################################

def normalize_key(value: Any) -> str:
    return str(value or "").strip().lower()


def normalize_lookup(value: Any) -> str:
    raw_text = str(value or "").strip().lower()
    normalized = unicodedata.normalize("NFD", raw_text)
    normalized = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    normalized = normalized.replace("_", " ").replace("-", " ")
    return " ".join(normalized.split())


def safe_json_loads(raw_value: Any, fallback: Any) -> Any:
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


def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def unique_keep_order(values: list[str]) -> list[str]:
    result: list[str] = []
    seen_values: set[str] = set()

    for raw_value in values:
        clean_value = normalize_key(raw_value)

        if not clean_value or clean_value in seen_values:
            continue

        seen_values.add(clean_value)
        result.append(clean_value)

    return result


def resolve_effective_field_key(field_key: Any) -> str:
    clean_field_key = normalize_key(field_key)
    return DUPLICATE_CUSTOM_TO_SYSTEM.get(clean_field_key, clean_field_key)


def is_duplicate_of_system_field(field_key: str, field_label: str) -> bool:
    clean_key = normalize_key(field_key)

    if clean_key in DUPLICATE_CUSTOM_TO_SYSTEM:
        return True

    if not clean_key.startswith("custom_"):
        return False

    lookup_values = set()

    for system_key, system_label in SYSTEM_FIELD_LABELS.items():
        lookup_values.add(normalize_lookup(system_key))
        lookup_values.add(normalize_lookup(system_label))

    custom_key_lookup = normalize_lookup(clean_key.removeprefix("custom_"))
    custom_label_lookup = normalize_lookup(field_label)

    return custom_key_lookup in lookup_values or custom_label_lookup in lookup_values


def build_valid_custom_fields(menu_config: dict[str, Any]) -> set[str]:
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

    created_fields: dict[str, dict[str, str]] = {}
    header_fields: set[str] = set()

    for raw_field in additional_fields_raw:
        if not isinstance(raw_field, dict):
            continue

        field_key = normalize_key(raw_field.get("key"))
        field_label = str(raw_field.get("label") or "").strip()
        field_type = normalize_key(raw_field.get("field_type") or raw_field.get("type") or "text")

        if not field_key:
            continue

        if is_duplicate_of_system_field(field_key, field_label):
            continue

        created_fields[field_key] = {
            "key": field_key,
            "label": field_label,
            "field_type": field_type,
        }

        if field_type == "header":
            header_fields.add(field_key)

    visible_field_keys: list[str] = []
    visible_header_by_field: dict[str, str] = {}

    for raw_key in visible_fields_raw:
        field_key = normalize_key(raw_key)

        if field_key and field_key not in visible_field_keys:
            visible_field_keys.append(field_key)

    for raw_row in visible_rows_raw:
        if not isinstance(raw_row, dict):
            continue

        field_key = normalize_key(raw_row.get("field_key"))
        header_key = normalize_key(raw_row.get("header_key"))

        if not field_key:
            continue

        if field_key not in visible_field_keys:
            visible_field_keys.append(field_key)

        if header_key:
            visible_header_by_field[field_key] = header_key

    for raw_field_key, raw_header_key in header_map_raw.items():
        field_key = normalize_key(raw_field_key)
        header_key = normalize_key(raw_header_key)

        if field_key and header_key:
            visible_header_by_field[field_key] = header_key

    valid_custom_fields: set[str] = set()

    for raw_field_key in visible_field_keys:
        field_key = normalize_key(raw_field_key)

        if not field_key.startswith("custom_"):
            continue

        created_meta = created_fields.get(field_key)

        if not created_meta:
            continue

        if created_meta.get("field_type") == "header":
            continue

        if is_duplicate_of_system_field(field_key, created_meta.get("label", "")):
            continue

        header_key = visible_header_by_field.get(field_key, "")

        if not header_key:
            continue

        if header_key not in header_fields:
            continue

        valid_custom_fields.add(field_key)

    return valid_custom_fields


####################################################################################
# (5) NORMALIZAR CONFIGURAÇÃO DO PROCESSO MEU PERFIL
####################################################################################

def cleanup_menu_config(menu_config: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    cleaned_config = dict(menu_config)
    report: dict[str, Any] = {
        "removed_additional_fields": [],
        "replaced_visible_fields": [],
        "cleaned_header_map_keys": [],
        "cleaned_rows": [],
    }

    additional_fields_raw = cleaned_config.get("additional_fields", [])

    if not isinstance(additional_fields_raw, list):
        additional_fields_raw = []

    cleaned_additional_fields: list[dict[str, Any]] = []

    for raw_field in additional_fields_raw:
        if not isinstance(raw_field, dict):
            continue

        field_key = normalize_key(raw_field.get("key"))
        field_label = str(raw_field.get("label") or "").strip()

        if field_key and is_duplicate_of_system_field(field_key, field_label):
            report["removed_additional_fields"].append(
                {
                    "field_key": field_key,
                    "label": field_label,
                    "replacement": DUPLICATE_CUSTOM_TO_SYSTEM.get(field_key, ""),
                }
            )
            continue

        cleaned_additional_fields.append(raw_field)

    cleaned_config["additional_fields"] = cleaned_additional_fields

    visible_fields_raw = cleaned_config.get("process_visible_fields", [])

    if not isinstance(visible_fields_raw, list):
        visible_fields_raw = []

    cleaned_visible_fields: list[str] = []

    for raw_field_key in visible_fields_raw:
        original_field_key = normalize_key(raw_field_key)
        effective_field_key = resolve_effective_field_key(original_field_key)

        if original_field_key != effective_field_key:
            report["replaced_visible_fields"].append(
                {
                    "from": original_field_key,
                    "to": effective_field_key,
                }
            )

        cleaned_visible_fields.append(effective_field_key)

    cleaned_config["process_visible_fields"] = unique_keep_order(cleaned_visible_fields)

    visible_rows_raw = cleaned_config.get("process_visible_field_rows", [])

    if not isinstance(visible_rows_raw, list):
        visible_rows_raw = []

    cleaned_rows: list[dict[str, str]] = []
    seen_row_fields: set[str] = set()

    for raw_row in visible_rows_raw:
        if not isinstance(raw_row, dict):
            continue

        original_field_key = normalize_key(raw_row.get("field_key"))
        effective_field_key = resolve_effective_field_key(original_field_key)
        header_key = normalize_key(raw_row.get("header_key"))

        if not effective_field_key or effective_field_key in seen_row_fields:
            continue

        seen_row_fields.add(effective_field_key)
        cleaned_rows.append(
            {
                "field_key": effective_field_key,
                "header_key": header_key,
            }
        )

        if original_field_key != effective_field_key:
            report["cleaned_rows"].append(
                {
                    "from": original_field_key,
                    "to": effective_field_key,
                    "header_key": header_key,
                }
            )

    cleaned_config["process_visible_field_rows"] = cleaned_rows

    header_map_raw = cleaned_config.get("process_visible_field_header_map", {})

    if not isinstance(header_map_raw, dict):
        header_map_raw = {}

    cleaned_header_map: dict[str, str] = {}

    for raw_field_key, raw_header_key in header_map_raw.items():
        original_field_key = normalize_key(raw_field_key)
        effective_field_key = resolve_effective_field_key(original_field_key)
        header_key = normalize_key(raw_header_key)

        if not effective_field_key or not header_key:
            continue

        cleaned_header_map[effective_field_key] = header_key

        if original_field_key != effective_field_key:
            report["cleaned_header_map_keys"].append(
                {
                    "from": original_field_key,
                    "to": effective_field_key,
                    "header_key": header_key,
                }
            )

    cleaned_config["process_visible_field_header_map"] = cleaned_header_map

    return cleaned_config, report


####################################################################################
# (6) LIMPAR members.profile_custom_fields
####################################################################################

def cleanup_member_profile_custom_fields(
    raw_profile_custom_fields: Any,
    valid_custom_fields: set[str],
) -> tuple[str | None, list[dict[str, str]]]:
    parsed_fields = safe_json_loads(raw_profile_custom_fields, {})

    if not isinstance(parsed_fields, dict):
        return None, []

    cleaned_fields: dict[str, Any] = {}
    removed_fields: list[dict[str, str]] = []

    for raw_key, raw_value in parsed_fields.items():
        field_key = normalize_key(raw_key)

        if (
            field_key.startswith("custom_")
            and (
                field_key in FIELDS_TO_DELETE_EXPLICIT
                or field_key not in valid_custom_fields
            )
        ):
            removed_fields.append(
                {
                    "field_key": field_key,
                    "value": str(raw_value or ""),
                }
            )
            continue

        cleaned_fields[field_key] = raw_value

    if not removed_fields:
        return raw_profile_custom_fields, []

    if not cleaned_fields:
        return None, removed_fields

    return json_dumps(cleaned_fields), removed_fields


####################################################################################
# (7) PROCESSO PRINCIPAL
####################################################################################

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Aplicar limpeza na base de dados.")
    args = parser.parse_args()

    apply_changes = bool(args.apply)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_dir = PROJECT_ROOT / "backups" / "meu_perfil_cleanup"
    backup_dir.mkdir(parents=True, exist_ok=True)

    backup_path = backup_dir / f"meu_perfil_cleanup_backup_{timestamp}.json"

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
            raise SystemExit("ERRO: menu Meu perfil não encontrado em sidebar_menu_settings.")

        menu_config = safe_json_loads(menu_row.get("menu_config"), {})

        if not isinstance(menu_config, dict):
            raise SystemExit("ERRO: menu_config do Meu perfil não é um JSON válido.")

        cleaned_menu_config, menu_cleanup_report = cleanup_menu_config(menu_config)
        valid_custom_fields = build_valid_custom_fields(cleaned_menu_config)

        member_rows = session.execute(
            text(
                """
                SELECT id, full_name, email, profile_custom_fields
                FROM members
                WHERE profile_custom_fields IS NOT NULL
                  AND trim(profile_custom_fields) <> ''
                ORDER BY id
                """
            )
        ).mappings().all()

        member_updates: list[dict[str, Any]] = []
        backup_members: list[dict[str, Any]] = []

        for member_row in member_rows:
            cleaned_profile_custom_fields, removed_fields = cleanup_member_profile_custom_fields(
                member_row.get("profile_custom_fields"),
                valid_custom_fields,
            )

            if not removed_fields:
                continue

            member_updates.append(
                {
                    "id": int(member_row.get("id")),
                    "full_name": str(member_row.get("full_name") or ""),
                    "email": str(member_row.get("email") or ""),
                    "old_profile_custom_fields": member_row.get("profile_custom_fields"),
                    "new_profile_custom_fields": cleaned_profile_custom_fields,
                    "removed_fields": removed_fields,
                }
            )

            backup_members.append(
                {
                    "id": int(member_row.get("id")),
                    "full_name": str(member_row.get("full_name") or ""),
                    "email": str(member_row.get("email") or ""),
                    "profile_custom_fields": member_row.get("profile_custom_fields"),
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
            "members": backup_members,
            "valid_custom_fields_after_config_cleanup": sorted(valid_custom_fields),
            "member_updates_count": len(member_updates),
            "menu_cleanup_report": menu_cleanup_report,
        }

        backup_path.write_text(json_dumps(backup_payload), encoding="utf-8")

        print("")
        print("===== BACKUP =====")
        print(f"Backup criado em: {backup_path}")

        print("")
        print("===== CONFIGURAÇÃO A NORMALIZAR =====")
        print(f"Campos adicionais duplicados removidos: {len(menu_cleanup_report['removed_additional_fields'])}")
        for item in menu_cleanup_report["removed_additional_fields"]:
            print(f"- {item['field_key']} -> {item.get('replacement') or 'remover'}")

        print("")
        print("===== CAMPOS CUSTOM_ VÁLIDOS APÓS NORMALIZAÇÃO =====")
        if valid_custom_fields:
            for field_key in sorted(valid_custom_fields):
                print(f"- {field_key}")
        else:
            print("- Nenhum campo custom_ válido encontrado.")

        print("")
        print("===== MEMBROS A ATUALIZAR =====")
        if member_updates:
            for update_item in member_updates:
                removed_keys = ", ".join(
                    sorted({item["field_key"] for item in update_item["removed_fields"]})
                )
                print(
                    f"- member_id={update_item['id']} | "
                    f"nome={update_item['full_name']} | "
                    f"email={update_item['email']} | "
                    f"remover={removed_keys}"
                )
        else:
            print("- Nenhum membro precisa de limpeza.")

        if not apply_changes:
            print("")
            print("MODO SIMULAÇÃO: nenhuma alteração foi aplicada.")
            print("Para aplicar, execute com --apply.")
            return

        session.execute(
            text(
                """
                UPDATE sidebar_menu_settings
                SET menu_config = :menu_config
                WHERE id = :menu_id
                """
            ),
            {
                "menu_id": int(menu_row.get("id")),
                "menu_config": json_dumps(cleaned_menu_config),
            },
        )

        for update_item in member_updates:
            session.execute(
                text(
                    """
                    UPDATE members
                    SET profile_custom_fields = :profile_custom_fields
                    WHERE id = :member_id
                    """
                ),
                {
                    "member_id": int(update_item["id"]),
                    "profile_custom_fields": update_item["new_profile_custom_fields"],
                },
            )

        session.commit()

        print("")
        print("===== LIMPEZA APLICADA =====")
        print(f"Configuração do menu normalizada: {menu_row.get('menu_key')}")
        print(f"Membros atualizados: {len(member_updates)}")
        print("OK: limpeza concluída com sucesso.")


if __name__ == "__main__":
    main()
