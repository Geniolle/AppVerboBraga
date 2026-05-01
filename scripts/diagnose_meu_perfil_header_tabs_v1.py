from __future__ import annotations

import sys
from pathlib import Path


####################################################################################
# (1) VALIDAR E INJETAR RAIZ DO PROJETO NO PYTHONPATH
####################################################################################

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


####################################################################################
# (2) IMPORTS DO PROJETO
####################################################################################

from appverbo.core import SessionLocal
from appverbo.menu_settings import get_sidebar_menu_settings


####################################################################################
# (3) DIAGNOSTICAR CABECALHOS DO PROCESSO MEU PERFIL
####################################################################################

def main() -> None:
    with SessionLocal() as session:
        sidebar_menu_settings = get_sidebar_menu_settings(session)

    meu_perfil = next(
        (
            row
            for row in sidebar_menu_settings
            if str(row.get("key") or "").strip().lower() == "meu_perfil"
        ),
        None,
    )

    if meu_perfil is None:
        print("ERRO: processo meu_perfil não encontrado.")
        raise SystemExit(1)

    additional_fields = meu_perfil.get("process_additional_fields") or []
    headers = [
        field
        for field in additional_fields
        if str(field.get("field_type") or "").strip().lower() == "header"
    ]

    print("===== PROCESSO MEU PERFIL =====")
    print(f"key={meu_perfil.get('key')}")
    print(f"label={meu_perfil.get('label')}")
    print("")
    print("===== CABECALHOS QUE DEVEM VIRAR ABAS =====")

    if not headers:
        print("Nenhum Cabeçalho configurado em Campos adicionais.")
        print("")
        print("OK: nesse caso, o Meu perfil não deve mostrar abas superiores criadas por fallback.")
        return

    for index, field in enumerate(headers, start=1):
        print(
            f"{index}. key={field.get('key')} | "
            f"label={field.get('label')} | "
            f"type={field.get('field_type')}"
        )

    print("")
    print("OK: somente estes campos do tipo header devem aparecer como abas no Meu perfil.")


####################################################################################
# (4) EXECUCAO
####################################################################################

if __name__ == "__main__":
    main()