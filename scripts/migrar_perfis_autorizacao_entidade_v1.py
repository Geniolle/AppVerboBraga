"""Copia os perfis de autorizacao guardados por membro para o armazenamento da entidade.

Uso (dry-run por defeito; --commit grava):
    python scripts/migrar_perfis_autorizacao_entidade_v1.py
    python scripts/migrar_perfis_autorizacao_entidade_v1.py --commit

Cada registo tem __numero_entidade; o registo e copiado para a entidade com esse numero.
Registos ja presentes no destino (mesmo record_id) nao sao duplicados.
Os registos no membro de origem nao sao apagados.
"""

from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import argparse

from sqlalchemy import select

from appgenesis.admin_subprocesses.repositories.auth_profile_entity_store import (
    load_entity_auth_profile_store_v1,
    save_entity_auth_profile_store_v1,
)
from appgenesis.admin_subprocesses.repositories.auth_profile_repository import (
    AUTH_PROFILE_ENTITY_NUMBER_KEY,
    AUTH_PROFILE_MENU_KEY,
)
from appgenesis.db.session import SessionLocal
from appgenesis.models import Entity, Member
from appgenesis.services.profile import (
    build_menu_process_records_storage_key,
    parse_member_profile_fields,
    parse_menu_process_records,
    serialize_member_profile_fields,
    serialize_menu_process_records,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--commit", action="store_true", help="grava as alteracoes")
    args = parser.parse_args()

    records_key = build_menu_process_records_storage_key(AUTH_PROFILE_MENU_KEY)
    with SessionLocal() as session:
        entity_id_by_number = {
            str(number): int(entity_id)
            for entity_id, number in session.execute(select(Entity.id, Entity.entity_number)).all()
            if number is not None
        }

        pending: dict[int, list[dict]] = {}
        skipped = 0
        for member in session.execute(select(Member)).scalars():
            fields = parse_member_profile_fields(member.profile_custom_fields)
            for record in parse_menu_process_records(fields.get(records_key)):
                values = record.get("values") if isinstance(record.get("values"), dict) else {}
                number = str(values.get(AUTH_PROFILE_ENTITY_NUMBER_KEY) or "").strip()
                entity_id = entity_id_by_number.get(number)
                if entity_id is None:
                    skipped += 1
                    continue
                pending.setdefault(entity_id, []).append(record)

        total = 0
        for entity_id, records in pending.items():
            store = load_entity_auth_profile_store_v1(session, entity_id)
            existing_fields = parse_member_profile_fields(store.profile_custom_fields)
            existing_records = parse_menu_process_records(existing_fields.get(records_key))
            existing_ids = {str(r.get("record_id") or "") for r in existing_records}
            new_records = []
            for record in records:
                record_id = str(record.get("record_id") or "")
                if record_id in existing_ids:
                    continue
                existing_ids.add(record_id)
                new_records.append(record)
            total += len(new_records)
            print(f"entidade_id={entity_id}: {len(new_records)} registo(s) a copiar (de {len(records)})")
            if not args.commit or not new_records:
                continue
            merged = existing_records + new_records
            existing_fields[records_key] = serialize_menu_process_records(merged[:200])
            store.profile_custom_fields = serialize_member_profile_fields(existing_fields)
            save_entity_auth_profile_store_v1(session, store)

        print(f"sem entidade correspondente (ignorados): {skipped}")
        print(f"total a copiar: {total}")
        if args.commit:
            session.commit()
            print("COMMITTED")
        else:
            session.rollback()
            print("DRY RUN (use --commit para gravar)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
