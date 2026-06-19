from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

root = Path.cwd()
env = Environment(loader=FileSystemLoader(str(root / "templates")))

env.get_template("new_user.html")
env.get_template("partials/admin_user_shadow_readonly_v1.html")

page_handler_source = (root / "appverbo" / "routes" / "profile" / "page_handler.py").read_text(
    encoding="utf-8"
)
partial_source = (root / "templates" / "partials" / "admin_user_shadow_readonly_v1.html").read_text(
    encoding="utf-8"
)
js_source = (root / "static" / "js" / "modules" / "admin_user_shadow_table_v1.js").read_text(
    encoding="utf-8"
)

if "APPVERBO_UTILIZADOR_ACTION_DEBUG_V1" in page_handler_source:
    raise RuntimeError("Debug temporário V1 ainda existe no page_handler.py.")

if "APPVERBO_UTILIZADOR_ACTION_DEBUG_V2" in page_handler_source:
    raise RuntimeError("Debug temporário V2 ainda existe no page_handler.py.")

required_page_tokens = (
    "APPVERBO_PAGE_HANDLER_UTILIZADOR_EDIT_TARGET_V2_START",
    "resolved_admin_tab == \"utilizador\"",
    "parsed_user_edit_id is not None",
    "initial_menu_target = \"#edit-user-card\"",
)

required_partial_tokens = (
    "render_admin_user_shadow_readonly_v12",
    "data-admin-user-shadow-real-link=\"view\"",
    "data-admin-user-shadow-real-link=\"edit\"",
    "user_view=1&target=edit-user-card#edit-user-card",
    "user_edit_id=",
    "target=edit-user-card#edit-user-card",
    "utilizador-shadow-table-v14",
)

required_js_tokens = (
    "forceNativeActionNavigation",
    "window.location.assign",
    "focusEditUserCardFromQuery",
    "edit-user-card",
    "scrollIntoView",
    "document.addEventListener(\"click\", forceNativeActionNavigation, true)",
)

missing_page_tokens = [
    token
    for token in required_page_tokens
    if token not in page_handler_source
]

missing_partial_tokens = [
    token
    for token in required_partial_tokens
    if token not in partial_source
]

missing_js_tokens = [
    token
    for token in required_js_tokens
    if token not in js_source
]

if missing_page_tokens:
    raise RuntimeError(
        "Tokens esperados ausentes no page_handler.py: "
        + ", ".join(missing_page_tokens)
    )

if missing_partial_tokens:
    raise RuntimeError(
        "Tokens esperados ausentes no partial nativo do Utilizador: "
        + ", ".join(missing_partial_tokens)
    )

if missing_js_tokens:
    raise RuntimeError(
        "Tokens esperados ausentes no JS nativo do Utilizador: "
        + ", ".join(missing_js_tokens)
    )

print("OK: templates Jinja carregados com sucesso.")
print("OK: Utilizador nativo validado com visualizar, editar e sem debug temporário.")
