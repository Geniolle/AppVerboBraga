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
js_source = (root / "static" / "js" / "modules" / "admin_user_shadow_table_v1.js?v=20260513-utilizador-view-toggle-v5").read_text(
    encoding="utf-8"
)

required_page_tokens = (
    "APPVERBO_PAGE_HANDLER_UTILIZADOR_EDIT_TARGET_V2_START",
    "resolved_admin_tab == \"utilizador\"",
    "parsed_user_edit_id is not None",
    "initial_menu_target = \"#edit-user-card\"",
)

required_partial_tokens = (
    "render_admin_user_shadow_actions_v15",
    "data-admin-user-shadow-real-link=\"view\"",
    "data-admin-user-shadow-real-link=\"edit\"",
    "data-admin-user-shadow-user-id=\"{{ user_id }}\"",
    "user_view=1&target=edit-user-card#edit-user-card",
    "user_view=0&target=edit-user-card#edit-user-card",
    "utilizador-shadow-table-v15",
)

required_js_tokens = (
    "buildUserActionUrl",
    "userViewValue = action === \"view\" ? \"1\" : \"0\"",
    "data-admin-user-shadow-user-id",
    "window.location.href = targetUrl",
    "focusEditUserCardFromQuery",
    "edit-user-card",
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
print("OK: botão lápis usa user_view=0 e navegação explícita.")
