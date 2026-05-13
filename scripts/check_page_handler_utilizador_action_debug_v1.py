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
    "resolved_menu == \"administrativo\"",
    "resolved_admin_tab == \"utilizador\"",
    "parsed_user_edit_id is not None",
    "\"raw_user_edit_id\": user_edit_id",
    "\"parsed_user_edit_id\": parsed_user_edit_id",
    "\"user_view\": user_view",
    "\"user_readonly_mode\": user_readonly_mode",
    "\"has_user_edit_data\": user_edit_data is not None",
    "\"initial_menu_target\": initial_menu_target",
    "\"request_url\": str(request.url)",
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
