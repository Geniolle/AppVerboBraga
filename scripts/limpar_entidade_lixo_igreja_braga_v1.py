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

from sqlalchemy import inspect, text

from appgenesis.core import SessionLocal, engine


####################################################################################
# (3) CONSTANTES
####################################################################################

CANDIDATE_QUERY = text(
    """
    SELECT id, entity_number, name, acronym, tax_id, email, responsible_name,
           door_number, address, city, freguesia, postal_code, country, phone,
           logo_url, description, profile_scope, is_active, created_at, updated_at
    FROM entities
    WHERE entity_number IS NULL
      AND name = :name
      AND email = :email
      AND is_active IS FALSE
    ORDER BY id
    """
)

TARGET_NAME = "Igreja Braga"
TARGET_EMAIL = "consultorsapclaytonlopes@gmail.com"

# Única exceção permitida ao "nunca CASCADE": um vínculo em member_entities
# para esta entidade pode ser removido junto, mas só se o membro ligado
# tiver pelo menos outro vínculo a uma entidade diferente (nunca deixar um
# membro sem nenhuma entidade). Nenhuma outra tabela tem esta exceção.
UNLINKABLE_TABLE = "member_entities"
UNLINKABLE_COLUMN = "entity_id"


####################################################################################
# (4) FUNÇÕES AUXILIARES
####################################################################################

def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def find_foreign_keys_to_entities(inspector) -> list[dict[str, Any]]:
    references: list[dict[str, Any]] = []

    for table_name in inspector.get_table_names():
        if table_name == "entities":
            continue

        for foreign_key in inspector.get_foreign_keys(table_name):
            if foreign_key.get("referred_table") != "entities":
                continue

            constrained_columns = foreign_key.get("constrained_columns") or []

            for column_name in constrained_columns:
                references.append({"table": table_name, "column": column_name})

    return references


def count_related_rows(session, table: str, column: str, entity_id: int) -> int:
    result = session.execute(
        text(f"SELECT COUNT(*) FROM {table} WHERE {column} = :entity_id"),
        {"entity_id": entity_id},
    ).scalar_one()
    return int(result or 0)


def fetch_unlinkable_member_entities(session, entity_id: int) -> list[dict[str, Any]]:
    rows = session.execute(
        text(
            """
            SELECT me.id, me.member_id, me.status, me.entry_date, me.exit_date,
                   m.full_name, m.email
            FROM member_entities me
            JOIN members m ON m.id = me.member_id
            WHERE me.entity_id = :entity_id
            ORDER BY me.id
            """
        ),
        {"entity_id": entity_id},
    ).mappings().all()
    return [dict(row) for row in rows]


def count_other_entity_links(session, member_id: int, entity_id: int) -> int:
    result = session.execute(
        text(
            """
            SELECT COUNT(*) FROM member_entities
            WHERE member_id = :member_id AND entity_id <> :entity_id
            """
        ),
        {"member_id": member_id, "entity_id": entity_id},
    ).scalar_one()
    return int(result or 0)


####################################################################################
# (5) PROCESSO PRINCIPAL
####################################################################################

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Aplicar a remoção na base de dados.")
    args = parser.parse_args()

    apply_changes = bool(args.apply)

    with SessionLocal() as session:
        candidates = session.execute(
            CANDIDATE_QUERY,
            {"name": TARGET_NAME, "email": TARGET_EMAIL},
        ).mappings().all()

        print("")
        print("===== CANDIDATOS ENCONTRADOS =====")

        if not candidates:
            print(f"- Nenhuma entidade encontrada com name='{TARGET_NAME}', email='{TARGET_EMAIL}', "
                  "entity_number IS NULL e is_active IS FALSE.")
            print("Nada a fazer.")
            return

        for candidate in candidates:
            print(
                f"- id={candidate['id']} | name={candidate['name']} | email={candidate['email']} | "
                f"entity_number={candidate['entity_number']} | is_active={candidate['is_active']} | "
                f"created_at={candidate['created_at']}"
            )

        if len(candidates) > 1:
            print("")
            print(f"ERRO: encontradas {len(candidates)} entidades candidatas — critério não é único o suficiente.")
            print("Nenhuma alteração foi feita. Refine os critérios antes de repetir.")
            return

        candidate = candidates[0]
        entity_id = int(candidate["id"])

        inspector = inspect(engine)
        foreign_keys = find_foreign_keys_to_entities(inspector)

        print("")
        print("===== VERIFICAÇÃO DE RELAÇÕES (FKs para entities.id) =====")

        related_counts: list[dict[str, Any]] = []
        for reference in foreign_keys:
            count = count_related_rows(session, reference["table"], reference["column"], entity_id)
            related_counts.append({**reference, "count": count})
            print(f"- {reference['table']}.{reference['column']}: {count} linha(s)")

        blocking = [item for item in related_counts if item["count"] > 0]

        non_unlinkable_blocking = [
            item for item in blocking
            if not (item["table"] == UNLINKABLE_TABLE and item["column"] == UNLINKABLE_COLUMN)
        ]

        if non_unlinkable_blocking:
            print("")
            print("ERRO: existem registos relacionados com esta entidade — remoção abortada.")
            print("Nenhuma alteração foi feita. Este script nunca faz CASCADE.")
            return

        unlinkable_member_entities: list[dict[str, Any]] = []

        if blocking:
            unlinkable_member_entities = fetch_unlinkable_member_entities(session, entity_id)

            print("")
            print("===== VÍNCULOS member_entities A REMOVER (exceção controlada) =====")

            stranding_members = []
            for link in unlinkable_member_entities:
                other_links_count = count_other_entity_links(session, int(link["member_id"]), entity_id)
                link["other_entity_links_count"] = other_links_count
                print(
                    f"- member_entities.id={link['id']} | member_id={link['member_id']} | "
                    f"nome={link['full_name']} | email={link['email']} | "
                    f"outras_entidades_ligadas={other_links_count}"
                )
                if other_links_count < 1:
                    stranding_members.append(link)

            if stranding_members:
                print("")
                print("ERRO: pelo menos um membro ficaria sem nenhuma entidade se este vínculo fosse removido.")
                print("Nenhuma alteração foi feita. Este script nunca deixa um membro sem entidades.")
                return

        print("")
        print("===== ENTIDADE CANDIDATA À REMOÇÃO =====")
        for key, value in candidate.items():
            print(f"- {key}: {value}")

        if not apply_changes:
            print("")
            print("MODO SIMULAÇÃO: nenhuma alteração foi aplicada.")
            print("Para aplicar, execute com --apply.")
            return

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_dir = PROJECT_ROOT / "backups" / "entity_cleanup"
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_path = backup_dir / f"igreja_braga_entity_cleanup_{timestamp}.json"

        backup_payload = {
            "created_at_utc": timestamp,
            "entity": dict(candidate),
            "checked_foreign_keys": related_counts,
            "removed_member_entities": unlinkable_member_entities,
        }
        backup_path.write_text(json_dumps(backup_payload), encoding="utf-8")

        print("")
        print(f"Backup criado em: {backup_path}")

        try:
            for link in unlinkable_member_entities:
                session.execute(
                    text("DELETE FROM member_entities WHERE id = :link_id"),
                    {"link_id": int(link["id"])},
                )
            session.execute(text("DELETE FROM entities WHERE id = :entity_id"), {"entity_id": entity_id})
            session.commit()
        except Exception:
            session.rollback()
            raise

        print("")
        print("===== REMOÇÃO APLICADA =====")
        if unlinkable_member_entities:
            print(f"Vínculos member_entities removidos: {len(unlinkable_member_entities)}")
        print(f"OK: entidade id={entity_id} ('{candidate['name']}') removida com sucesso.")


if __name__ == "__main__":
    main()
