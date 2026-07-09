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
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text

from appgenesis.core import SessionLocal


####################################################################################
# (3) CONSTANTES
####################################################################################
# O campo "Escopo do perfil" (entity_scope) foi removido do processo
# Perfil de autorizacao: todo perfil passa a pertencer sempre a entidade ativa,
# identificada por __numero_entidade. Este script remove as chaves legadas
# __entity_scope_mode / __entity_scope_label dos registos ja gravados,
# sem jamais atribuir uma entidade arbitraria a um registo que nao a tenha.

MENU_KEY = "perfil_de_autorizacao"
RECORDS_STORAGE_KEY = f"process_records__{MENU_KEY}"
ENTITY_NUMBER_KEY = "__numero_entidade"
LEGACY_SCOPE_MODE_KEY = "__entity_scope_mode"
LEGACY_SCOPE_LABEL_KEY = "__entity_scope_label"


####################################################################################
# (4) FUNÇÕES AUXILIARES
####################################################################################

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


def cleanup_records(records: list[Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    cleaned_records: list[dict[str, Any]] = []
    report = {
        "legacy_keys_removed": [],
        "missing_entity_number": [],
    }

    for raw_record in records:
        if not isinstance(raw_record, dict):
            continue

        raw_values = raw_record.get("values")
        values = dict(raw_values) if isinstance(raw_values, dict) else {}

        record_id = str(raw_record.get("record_id") or "").strip()
        removed_legacy_keys = []

        if LEGACY_SCOPE_MODE_KEY in values:
            values.pop(LEGACY_SCOPE_MODE_KEY, None)
            removed_legacy_keys.append(LEGACY_SCOPE_MODE_KEY)

        if LEGACY_SCOPE_LABEL_KEY in values:
            values.pop(LEGACY_SCOPE_LABEL_KEY, None)
            removed_legacy_keys.append(LEGACY_SCOPE_LABEL_KEY)

        if removed_legacy_keys:
            report["legacy_keys_removed"].append(
                {"record_id": record_id, "keys": removed_legacy_keys}
            )

        # Perfis antigos sem __numero_entidade NAO recebem uma entidade
        # arbitraria aqui; ficam apenas listados para correcao manual
        # (o repositorio ja os trata como invisiveis ate essa correcao).
        if not str(values.get(ENTITY_NUMBER_KEY) or "").strip():
            report["missing_entity_number"].append(
                {"record_id": record_id, "label": str(values.get("custom_nome_do_perfil") or values.get("custom_perfil") or "").strip()}
            )

        new_record = dict(raw_record)
        new_record["values"] = values
        cleaned_records.append(new_record)

    return cleaned_records, report


####################################################################################
# (5) PROCESSO PRINCIPAL
####################################################################################

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Aplicar limpeza na base de dados.")
    args = parser.parse_args()

    apply_changes = bool(args.apply)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_dir = PROJECT_ROOT / "backups" / "perfil_autorizacao_entity_scope_cleanup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / f"perfil_autorizacao_entity_scope_cleanup_backup_{timestamp}.json"

    with SessionLocal() as session:
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
        all_missing_entity_number: list[dict[str, Any]] = []

        for member_row in member_rows:
            profile_fields = safe_json_loads(member_row.get("profile_custom_fields"), {})
            if not isinstance(profile_fields, dict):
                continue

            raw_records_value = profile_fields.get(RECORDS_STORAGE_KEY)
            records = safe_json_loads(raw_records_value, [])
            if not isinstance(records, list) or not records:
                continue

            cleaned_records, report = cleanup_records(records)

            if report["missing_entity_number"]:
                for item in report["missing_entity_number"]:
                    all_missing_entity_number.append(
                        {
                            "member_id": int(member_row.get("id")),
                            "email": str(member_row.get("email") or ""),
                            **item,
                        }
                    )

            if not report["legacy_keys_removed"]:
                continue

            new_profile_fields = dict(profile_fields)
            new_profile_fields[RECORDS_STORAGE_KEY] = json_dumps(cleaned_records)

            member_updates.append(
                {
                    "id": int(member_row.get("id")),
                    "email": str(member_row.get("email") or ""),
                    "old_profile_custom_fields": member_row.get("profile_custom_fields"),
                    "new_profile_custom_fields": json_dumps(new_profile_fields),
                    "legacy_keys_removed": report["legacy_keys_removed"],
                }
            )

            backup_members.append(
                {
                    "id": int(member_row.get("id")),
                    "email": str(member_row.get("email") or ""),
                    "profile_custom_fields": member_row.get("profile_custom_fields"),
                }
            )

        backup_payload = {
            "created_at_utc": timestamp,
            "apply_changes": apply_changes,
            "members": backup_members,
            "member_updates_count": len(member_updates),
            "missing_entity_number_count": len(all_missing_entity_number),
            "missing_entity_number": all_missing_entity_number,
        }

        backup_path.write_text(json_dumps(backup_payload), encoding="utf-8")

        print("")
        print("===== BACKUP =====")
        print(f"Backup criado em: {backup_path}")

        print("")
        print("===== PERFIS COM CHAVES LEGADAS (__entity_scope_mode / __entity_scope_label) =====")
        if member_updates:
            for update_item in member_updates:
                print(
                    f"- member_id={update_item['id']} | email={update_item['email']} | "
                    f"registos_afetados={len(update_item['legacy_keys_removed'])}"
                )
        else:
            print("- Nenhum perfil com chaves legadas encontrado.")

        print("")
        print("===== PERFIS SEM __numero_entidade (nao alterados; requerem correção manual) =====")
        if all_missing_entity_number:
            for item in all_missing_entity_number:
                print(
                    f"- member_id={item['member_id']} | email={item['email']} | "
                    f"record_id={item['record_id']} | label={item['label']}"
                )
        else:
            print("- Nenhum perfil sem numero de entidade encontrado.")

        if not apply_changes:
            print("")
            print("MODO SIMULAÇÃO: nenhuma alteração foi aplicada.")
            print("Para aplicar, execute com --apply.")
            return

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
        print(f"Membros atualizados: {len(member_updates)}")
        print("OK: limpeza concluída com sucesso.")


if __name__ == "__main__":
    main()
