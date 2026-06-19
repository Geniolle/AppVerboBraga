from __future__ import annotations

import re
from pathlib import Path


####################################################################################
# (1) UTILITÁRIOS
####################################################################################

ROOT = Path(__file__).resolve().parents[1]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


####################################################################################
# (2) CORRIGIR SCRIPT DE VALIDAÇÃO PARA ENCONTRAR APPVERBO
####################################################################################

check_script_path = ROOT / "scripts" / "check_admin_subprocess_utilizador_v1.py"

check_script_content = '''\
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from appverbo.admin_subprocesses.registry import require_admin_subprocess_config
from appverbo.admin_subprocesses.runtime import build_admin_subprocess_state_from_repository
from appverbo.core import SessionLocal


####################################################################################
# (1) VALIDAR STATE NATIVO DO SUBPROCESSO UTILIZADOR
####################################################################################

def main() -> None:
    config = require_admin_subprocess_config("utilizador")

    if not config.enabled:
        raise RuntimeError("Subprocesso Utilizador não está ativo no registry.")

    if not config.repository_class:
        raise RuntimeError("Subprocesso Utilizador sem repository_class.")

    with SessionLocal() as session:
        state = build_admin_subprocess_state_from_repository(
            config=config,
            session=session,
            edit_key="",
            success="",
            error="",
            return_url="/users/new?menu=administrativo&admin_tab=utilizador",
            context={},
        )

    if state is None:
        raise RuntimeError("Não foi possível construir o state do Utilizador.")

    print("OK: state do subprocesso Utilizador criado.")
    print(f"Config: {state.config.key} - {state.config.label}")
    print(f"Ativos: {len(state.active_rows)}")
    print(f"Inativos/Pendentes/Bloqueados: {len(state.inactive_rows)}")


if __name__ == "__main__":
    main()
'''

write_text(check_script_path, check_script_content)


####################################################################################
# (3) LIGAR PAGE_HANDLER AO RUNTIME DO UTILIZADOR EM MODO SHADOW
####################################################################################

page_handler_path = ROOT / "appverbo" / "routes" / "profile" / "page_handler.py"
page_handler_content = read_text(page_handler_path)

runtime_import = (
    "from appverbo.admin_subprocesses.runtime import "
    "build_admin_subprocess_state_from_repository\n"
)

if "build_admin_subprocess_state_from_repository" not in page_handler_content:
    service_import = "from appverbo.admin_subprocesses.service import build_admin_subprocess_state\n"

    if service_import not in page_handler_content:
        raise RuntimeError("Import de build_admin_subprocess_state não encontrado no page_handler.py")

    page_handler_content = page_handler_content.replace(
        service_import,
        service_import + runtime_import,
        1,
    )

if "admin_subprocess_shadow_state_v1 = None" not in page_handler_content:
    function_index = page_handler_content.find("def new_user_page(")

    if function_index < 0:
        raise RuntimeError("Função new_user_page não encontrada no page_handler.py")

    with_index = page_handler_content.find(
        "    with SessionLocal() as session:\n",
        function_index,
    )

    if with_index < 0:
        raise RuntimeError("Bloco with SessionLocal() da new_user_page não encontrado.")

    page_handler_content = (
        page_handler_content[:with_index]
        + "    admin_subprocess_shadow_state_v1 = None\n"
        + page_handler_content[with_index:]
    )

shadow_block = '''
        # APPVERBO_ADMIN_SUBPROCESS_STATE_UTILIZADOR_SHADOW_V1_START
        # Estado nativo em paralelo para validar o subprocesso Utilizador sem trocar a tela legada.
        # Isto garante que a aba Utilizador pode evoluir para o processo único sem afetar Sessões,
        # Entidade ou o fluxo atual de criação/edição de utilizadores.
        if resolved_admin_tab == "utilizador":
            utilizador_subprocess_config_v1 = get_admin_subprocess_config("utilizador")

            if utilizador_subprocess_config_v1 is not None:
                admin_subprocess_shadow_state_v1 = build_admin_subprocess_state_from_repository(
                    config=utilizador_subprocess_config_v1,
                    session=session,
                    edit_key=clean_user_edit_id,
                    success=success or "",
                    error=error or "",
                    return_url="/users/new?menu=administrativo&admin_tab=utilizador&target=create-user-card#create-user-card",
                    context={
                        "current_user": current_user,
                        "selected_entity_id": selected_entity_id,
                        "allowed_entity_ids": entity_permissions["allowed_entity_ids"],
                        "can_manage_all_entities": entity_permissions["can_manage_all_entities"],
                    },
                )
        # APPVERBO_ADMIN_SUBPROCESS_STATE_UTILIZADOR_SHADOW_V1_END

'''

if "APPVERBO_ADMIN_SUBPROCESS_STATE_UTILIZADOR_SHADOW_V1_START" not in page_handler_content:
    user_edit_pattern = re.compile(
        r"(?P<block>        user_edit_data = get_user_edit_data\\(\\n[\\s\\S]*?        \\)\\n)",
        re.MULTILINE,
    )

    user_edit_match = user_edit_pattern.search(page_handler_content)

    if user_edit_match is None:
        raise RuntimeError("Bloco user_edit_data não encontrado para inserir shadow state.")

    insert_index = user_edit_match.end("block")

    page_handler_content = (
        page_handler_content[:insert_index]
        + "\n"
        + shadow_block
        + page_handler_content[insert_index:]
    )

if '"admin_subprocess_shadow_state": admin_subprocess_shadow_state_v1,' not in page_handler_content:
    context_line = '        "admin_subprocess_state": admin_subprocess_state_v2,\n'

    if context_line not in page_handler_content:
        raise RuntimeError("Linha admin_subprocess_state não encontrada no contexto.")

    page_handler_content = page_handler_content.replace(
        context_line,
        context_line + '        "admin_subprocess_shadow_state": admin_subprocess_shadow_state_v1,\n',
        1,
    )

write_text(page_handler_path, page_handler_content)


####################################################################################
# (4) RESULTADO
####################################################################################

print("OK: check do Utilizador corrigido e page_handler ligado ao modo shadow.")
