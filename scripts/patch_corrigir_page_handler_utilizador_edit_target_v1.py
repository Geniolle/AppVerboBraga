from __future__ import annotations

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
# (2) APLICAR GUARDA DE TARGET PARA EDITAR/VISUALIZAR UTILIZADOR
####################################################################################

page_handler_path = ROOT / "appverbo" / "routes" / "profile" / "page_handler.py"
content = read_text(page_handler_path)

start_marker = "    # APPVERBO_PAGE_HANDLER_UTILIZADOR_EDIT_TARGET_V1_START"
end_marker = "    # APPVERBO_PAGE_HANDLER_UTILIZADOR_EDIT_TARGET_V1_END"

guard_block = '''\
    # APPVERBO_PAGE_HANDLER_UTILIZADOR_EDIT_TARGET_V1_START
    # Quando a aba Utilizador recebe user_edit_id, o orquestrador deve abrir
    # diretamente o card de edição/visualização. Sem isto, a página volta para
    # o alvo padrão da aba, que é #create-user-card.
    if (
        resolved_menu == "administrativo"
        and resolved_admin_tab == "utilizador"
        and parsed_user_edit_id is not None
    ):
        initial_menu_target = "#edit-user-card"
        initial_dynamic_process_section = ""
    # APPVERBO_PAGE_HANDLER_UTILIZADOR_EDIT_TARGET_V1_END

'''

if start_marker in content:
    start_index = content.index(start_marker)
    end_index = content.index(end_marker, start_index)
    line_end_index = content.find("\n", end_index)

    if line_end_index == -1:
        line_end_index = len(content)
    else:
        line_end_index += 1

    content = content[:start_index] + guard_block + content[line_end_index:]
else:
    anchor = '''\
    if clean_target_from_query:
        initial_menu_target = clean_target_from_query

'''

    if anchor not in content:
        raise RuntimeError(
            "Ponto seguro não encontrado no page_handler.py: bloco clean_target_from_query."
        )

    content = content.replace(anchor, anchor + guard_block, 1)

if content.count("APPVERBO_PAGE_HANDLER_UTILIZADOR_EDIT_TARGET_V1_START") != 1:
    raise RuntimeError("Marcador START duplicado ou ausente.")

if content.count("APPVERBO_PAGE_HANDLER_UTILIZADOR_EDIT_TARGET_V1_END") != 1:
    raise RuntimeError("Marcador END duplicado ou ausente.")

if 'initial_menu_target = "#edit-user-card"' not in content:
    raise RuntimeError("Correção do target #edit-user-card não foi aplicada.")

write_text(page_handler_path, content)


####################################################################################
# (3) CRIAR SCRIPT DE VALIDAÇÃO ESTÁTICA
####################################################################################

check_path = ROOT / "scripts" / "check_page_handler_utilizador_edit_target_v1.py"

check_content = '''\
from __future__ import annotations

from pathlib import Path


####################################################################################
# (1) VALIDAR TARGET DE EDITAR/VISUALIZAR UTILIZADOR NO PAGE_HANDLER
####################################################################################

ROOT = Path(__file__).resolve().parents[1]
page_handler_path = ROOT / "appverbo" / "routes" / "profile" / "page_handler.py"
content = page_handler_path.read_text(encoding="utf-8")

required_tokens = (
    "APPVERBO_PAGE_HANDLER_UTILIZADOR_EDIT_TARGET_V1_START",
    "resolved_menu == \\"administrativo\\"",
    "resolved_admin_tab == \\"utilizador\\"",
    "parsed_user_edit_id is not None",
    "initial_menu_target = \\"#edit-user-card\\"",
    "initial_dynamic_process_section = \\"\\"",
    "APPVERBO_PAGE_HANDLER_UTILIZADOR_EDIT_TARGET_V1_END",
)

missing_tokens = [
    token
    for token in required_tokens
    if token not in content
]

if missing_tokens:
    raise RuntimeError(
        "Tokens esperados ausentes no page_handler.py: "
        + ", ".join(missing_tokens)
    )

print("OK: page_handler.py direciona Utilizador com user_edit_id para #edit-user-card.")
'''

write_text(check_path, check_content)


####################################################################################
# (4) RESULTADO
####################################################################################

print("OK: page_handler.py corrigido para abrir #edit-user-card quando user_edit_id existir.")
print("OK: scripts/check_page_handler_utilizador_edit_target_v1.py criado.")
