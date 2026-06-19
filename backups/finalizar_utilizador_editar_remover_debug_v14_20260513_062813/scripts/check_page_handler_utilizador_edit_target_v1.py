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
    "resolved_menu == \"administrativo\"",
    "resolved_admin_tab == \"utilizador\"",
    "parsed_user_edit_id is not None",
    "initial_menu_target = \"#edit-user-card\"",
    "initial_dynamic_process_section = \"\"",
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
