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
# (2) GARANTIR IMPORT JSON
####################################################################################

page_handler_path = ROOT / "appverbo" / "routes" / "profile" / "page_handler.py"
content = read_text(page_handler_path)

if "import json" not in content:
    if "from __future__ import annotations" in content:
        content = content.replace(
            "from __future__ import annotations\n",
            "from __future__ import annotations\n\nimport json\n",
            1,
        )
    else:
        content = "import json\n" + content


####################################################################################
# (3) ADICIONAR LOG TEMPORÁRIO PARA CLIQUE OLHO/LÁPIS DO UTILIZADOR
####################################################################################

start_marker = "    # APPVERBO_UTILIZADOR_ACTION_DEBUG_V1_START"
end_marker = "    # APPVERBO_UTILIZADOR_ACTION_DEBUG_V1_END"

debug_block = '''\
    # APPVERBO_UTILIZADOR_ACTION_DEBUG_V1_START
    if (
        resolved_menu == "administrativo"
        and resolved_admin_tab == "utilizador"
        and parsed_user_edit_id is not None
    ):
        print(
            "APPVERBO_UTILIZADOR_ACTION_DEBUG_V1 "
            + json.dumps(
                {
                    "menu": resolved_menu,
                    "admin_tab": resolved_admin_tab,
                    "raw_user_edit_id": user_edit_id,
                    "parsed_user_edit_id": parsed_user_edit_id,
                    "user_view": user_view,
                    "user_readonly_mode": user_readonly_mode,
                    "has_user_edit_data": user_edit_data is not None,
                    "user_edit_data_type": type(user_edit_data).__name__ if user_edit_data is not None else "",
                    "initial_menu_target": initial_menu_target,
                    "initial_dynamic_process_section": initial_dynamic_process_section,
                    "clean_target_from_query": clean_target_from_query,
                    "request_url": str(request.url),
                },
                ensure_ascii=False,
                default=str,
            ),
            flush=True,
        )
    # APPVERBO_UTILIZADOR_ACTION_DEBUG_V1_END

'''

if start_marker in content:
    start_index = content.index(start_marker)
    end_index = content.index(end_marker, start_index)
    line_end_index = content.find("\n", end_index)

    if line_end_index == -1:
        line_end_index = len(content)
    else:
        line_end_index += 1

    content = content[:start_index] + debug_block + content[line_end_index:]
else:
    anchors = [
        '    context = {',
        '    template_context = {',
        '    return templates.TemplateResponse(',
        '    return TemplateResponse(',
    ]

    inserted = False

    for anchor in anchors:
        if anchor in content:
            content = content.replace(anchor, debug_block + anchor, 1)
            inserted = True
            break

    if not inserted:
        raise RuntimeError(
            "Não foi possível encontrar ponto seguro para inserir debug no page_handler.py."
        )

if content.count("APPVERBO_UTILIZADOR_ACTION_DEBUG_V1_START") != 1:
    raise RuntimeError("Marcador START de debug duplicado ou ausente.")

if content.count("APPVERBO_UTILIZADOR_ACTION_DEBUG_V1_END") != 1:
    raise RuntimeError("Marcador END de debug duplicado ou ausente.")

if "APPVERBO_UTILIZADOR_ACTION_DEBUG_V1 " not in content:
    raise RuntimeError("Log APPVERBO_UTILIZADOR_ACTION_DEBUG_V1 não foi aplicado.")

write_text(page_handler_path, content)


####################################################################################
# (4) CRIAR SCRIPT DE VALIDAÇÃO DO DEBUG
####################################################################################

check_path = ROOT / "scripts" / "check_page_handler_utilizador_action_debug_v1.py"

check_content = '''\
from __future__ import annotations

from pathlib import Path


####################################################################################
# (1) VALIDAR DEBUG TEMPORÁRIO DO PAGE_HANDLER PARA UTILIZADOR
####################################################################################

ROOT = Path(__file__).resolve().parents[1]
page_handler_path = ROOT / "appverbo" / "routes" / "profile" / "page_handler.py"
content = page_handler_path.read_text(encoding="utf-8")

required_tokens = (
    "import json",
    "APPVERBO_UTILIZADOR_ACTION_DEBUG_V1_START",
    "APPVERBO_UTILIZADOR_ACTION_DEBUG_V1",
    "resolved_menu == \\"administrativo\\"",
    "resolved_admin_tab == \\"utilizador\\"",
    "parsed_user_edit_id is not None",
    "\\"raw_user_edit_id\\": user_edit_id",
    "\\"parsed_user_edit_id\\": parsed_user_edit_id",
    "\\"user_view\\": user_view",
    "\\"user_readonly_mode\\": user_readonly_mode",
    "\\"has_user_edit_data\\": user_edit_data is not None",
    "\\"initial_menu_target\\": initial_menu_target",
    "\\"request_url\\": str(request.url)",
    "APPVERBO_UTILIZADOR_ACTION_DEBUG_V1_END",
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

print("OK: debug temporário do page_handler para ações do Utilizador está ativo.")
'''

write_text(check_path, check_content)


####################################################################################
# (5) RESULTADO
####################################################################################

print("OK: debug temporário APPVERBO_UTILIZADOR_ACTION_DEBUG_V1 aplicado no page_handler.py.")
print("OK: script de validação criado.")
