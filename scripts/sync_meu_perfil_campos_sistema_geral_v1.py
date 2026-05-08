from __future__ import annotations

####################################################################################
# (1) BOOTSTRAP DO PROJETO
####################################################################################

from pathlib import Path
import json
import sys
import unicodedata
from datetime import datetime, timezone
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

####################################################################################
# (2) IMPORTS
####################################################################################

from sqlalchemy import text

from appverbo.core import SessionLocal

####################################################################################
# (3) CONSTANTES
####################################################################################

MENU_KEY = "meu_perfil"
LEGACY_MENU_KEY = "documentos"

SYSTEM_VISIBLE_ORDER = ["nome", "email", "telefone", "pais"]

SYSTEM_LABELS = {
    "nome": "Nome",
    "email": "Email",
    "telefone": "Telefone",
    "pais": "País",
}

####################################################################################
# (4) FUNÇÕES AUXILIARES
####################################################################################

def normalize_key(value: Any) -> str:
    return str(value or "").strip().lower()


def normalize_text(value: Any) -> str:
    raw_text = str(value or "").strip().lower()
    normalized = unicodedata.normalize("NFD", raw_text)
    normalized = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    return " ".join(normalized.replace("_", " ").replace("-", " ").split())


def safe_json_loads(raw_value: Any, fallback: Any) -> Any:
    if raw_value is None:
        return fallback

    if isinstance(raw_value, (dict, list)):
        return raw_value

    clean_value = str(raw_value or "").strip()

    if not clean_value:
        return fallback

    try:
        return json.loads(clean_value)
    except Exception:
        return fallback


def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def unique_keep_order(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()

    for raw_value in values:
        clean_value = normalize_key(raw_value)

        if not clean_value or clean_value in seen:
            continue

        seen.add(clean_value)
        result.append(clean_value)

    return result


def find_dados_pessoais_header(menu_config: dict[str, Any]) -> str:
    raw_fields = menu_config.get("additional_fields", [])

    if not isinstance(raw_fields, list):
        return ""

    for raw_field in raw_fields:
        if not isinstance(raw_field, dict):
            continue

        field_type = normalize_key(raw_field.get("field_type") or raw_field.get("type"))
        field_key = normalize_key(raw_field.get("key"))
        field_label = normalize_text(raw_field.get("label"))

        if field_type == "header" and field_label == "dados pessoais" and field_key:
            return field_key

    return ""


def normalize_visible_rows(
    menu_config: dict[str, Any],
    header_key: str,
) -> list[dict[str, str]]:
    raw_rows = menu_config.get("process_visible_field_rows", [])

    if not isinstance(raw_rows, list):
        raw_rows = []

    existing_rows: list[dict[str, str]] = []
    seen_existing: set[str] = set()

    for raw_row in raw_rows:
        if not isinstance(raw_row, dict):
            continue

        field_key = normalize_key(raw_row.get("field_key"))
        row_header_key = normalize_key(raw_row.get("header_key"))

        if not field_key or field_key in seen_existing:
            continue

        seen_existing.add(field_key)

        if field_key in SYSTEM_VISIBLE_ORDER:
            continue

        existing_rows.append(
            {
                "field_key": field_key,
                "header_key": row_header_key,
            }
        )

    system_rows = [
        {
            "field_key": field_key,
            "header_key": header_key,
        }
        for field_key in SYSTEM_VISIBLE_ORDER
    ]

    return system_rows + existing_rows


def sync_menu_config(menu_config: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    updated_config = dict(menu_config)

    header_key = find_dados_pessoais_header(updated_config)

    raw_visible_fields = updated_config.get("process_visible_fields", [])

    if not isinstance(raw_visible_fields, list):
        raw_visible_fields = []

    new_visible_fields = unique_keep_order(
        SYSTEM_VISIBLE_ORDER + [normalize_key(field_key) for field_key in raw_visible_fields]
    )

    raw_header_map = updated_config.get("process_visible_field_header_map", {})

    if not isinstance(raw_header_map, dict):
        raw_header_map = {}

    new_header_map: dict[str, str] = {}

    for raw_field_key, raw_header_key in raw_header_map.items():
        field_key = normalize_key(raw_field_key)
        row_header_key = normalize_key(raw_header_key)

        if field_key and row_header_key:
            new_header_map[field_key] = row_header_key

    if header_key:
        for field_key in SYSTEM_VISIBLE_ORDER:
            new_header_map[field_key] = header_key

    updated_config["process_visible_fields"] = new_visible_fields
    updated_config["process_visible_field_rows"] = normalize_visible_rows(updated_config, header_key)
    updated_config["process_visible_field_header_map"] = new_header_map

    report = {
        "header_key_dados_pessoais": header_key,
        "system_visible_order": SYSTEM_VISIBLE_ORDER,
        "process_visible_fields": new_visible_fields,
        "process_visible_field_rows_count": len(updated_config["process_visible_field_rows"]),
    }

    return updated_config, report

####################################################################################
# (5) PROCESSO PRINCIPAL
####################################################################################

def main() -> None:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_dir = PROJECT_ROOT / "backups" / "meu_perfil_campos_sistema_geral"
    backup_dir.mkdir(parents=True, exist_ok=True)

    backup_path = backup_dir / f"backup_menu_config_{timestamp}.json"

    with SessionLocal() as session:
        menu_row = session.execute(
            text(
                """
               , report

####################################################################################
# (5) PROCESSO PRINCIPAL SELECT id, menu_key, menu_label, menu_config
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
            raise SystemExit("ERRO: menu_config do Meu perfil não é JSON válido.")

        updated_config, report = sync_menu_config(menu_config)

        backup_payload = {
            "created_at_utc": timestamp,
            "menu": {
                "id": int(menu_row.get("id")),
                "menu_key": str(menu_row.get("menu_key") or ""),
                "menu_label": str(menu_row.get("menu_label") or ""),
                "old_menu_config": menu_config,
                "new_menu_config": updated_config,
            },
            "report": report,
        }

        backup_path.write_text(json_dumps(backup_payload), encoding="utf-8")

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
                "menu_config": json_dumps(updated_config),
            },
        )

        session.commit()

    print("")
    print("===== BACKUP BD =====")
    print(f"Backup criado em: {backup_path}")

    print("")
    print("===== CAMPOS DE SISTEMA INSERIDOS NA ABA GERAL =====")
    for field_key in SYSTEM_VISIBLE_ORDER:
        print(f"- {field_key}: {SYSTEM_LABELS.get(field_key, field_key)}")

    print("")
    print("===== CABEÇALHO =====")
    print(f"Dados pessoais header_key: {report['header_key_dados_pessoais'] or '-'}")

    print("")
    print("OK: configuração do Meu perfil sincronizada.")


if __name__ == "__main__":
    main()
