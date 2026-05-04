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

from sqlalchemy import text

from appverbo.core import SessionLocal
from appverbo.services.page import get_page_data
from appverbo.services.profile import parse_member_profile_fields


####################################################################################
# (3) CONSTANTES
####################################################################################

TRIGGER_FIELD = "custom_estado_civil"
TARGET_FIELD = "custom_nome_do_conjuge"
EXPECTED_VISIBLE_VALUE = "Casado"


####################################################################################
# (4) FUNÇÕES AUXILIARES
####################################################################################

def normalize_text_v1(value: object) -> str:
    return str(value or "").strip().lower()


def should_be_visible_v1(estado_civil: str) -> bool:
    return normalize_text_v1(estado_civil) == normalize_text_v1(EXPECTED_VISIBLE_VALUE)


####################################################################################
# (5) PROCESSO PRINCIPAL
####################################################################################

def main_v1() -> None:
    with SessionLocal() as session:
        users = session.execute(
            text(
                """
                SELECT
                    users.id AS user_id,
                    users.login_email,
                    members.id AS member_id,
                    members.full_name,
                    members.profile_custom_fields
                FROM users
                JOIN members ON members.id = users.member_id
                ORDER BY users.id
                """
            )
        ).mappings().all()

        print("")
        print("===== VALIDAÇÃO DA VISIBILIDADE REAL NO PAGE DATA =====")
        print("Regra esperada: Estado civil = Casado -> mostrar Nome do conjuge")
        print("Caso contrário: Nome do conjuge não deve aparecer")

        total = 0
        ok_count = 0
        error_count = 0

        for row in users:
            profile_fields = parse_member_profile_fields(row.get("profile_custom_fields"))
            estado_civil = profile_fields.get(TRIGGER_FIELD, "")

            expected_visible = should_be_visible_v1(estado_civil)

            page_data = get_page_data(
                session,
                actor_user_id=int(row["user_id"]),
                actor_login_email=str(row["login_email"] or ""),
                selected_entity_id=None,
            )

            visible_fields = [
                str(field_key or "").strip().lower()
                for field_key in page_data.get("profile_personal_visible_fields", [])
            ]

            actual_visible = TARGET_FIELD in visible_fields
            result_ok = expected_visible == actual_visible

            total += 1

            if result_ok:
                ok_count += 1
            else:
                error_count += 1

            print("")
            print(f"Utilizador #{row['user_id']} | member_id={row['member_id']}")
            print(f"- Nome: {row['full_name']}")
            print(f"- Email: {row['login_email']}")
            print(f"- Estado civil gravado: {estado_civil or '-'}")
            print(f"- Esperado mostrar Nome do conjuge? {'SIM' if expected_visible else 'NÃO'}")
            print(f"- Page data mostra Nome do conjuge? {'SIM' if actual_visible else 'NÃO'}")
            print(f"- Resultado: {'OK' if result_ok else 'ERRO'}")

        print("")
        print("===== RESUMO =====")
        print(f"Total avaliado: {total}")
        print(f"OK: {ok_count}")
        print(f"Erros: {error_count}")

        if error_count:
            raise SystemExit("ERRO: existem casos em que a visibilidade não respeita a regra.")

        print("OK: visibilidade respeita a regra atual.")


if __name__ == "__main__":
    main_v1()
