from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

root = Path.cwd()
env = Environment(loader=FileSystemLoader(str(root / "templates")))

env.get_template("new_user.html")
env.get_template("partials/admin_user_shadow_readonly_v1.html")

partial_source = (root / "templates" / "partials" / "admin_user_shadow_readonly_v1.html").read_text(encoding="utf-8")
js_source = (root / "static" / "js" / "modules" / "admin_user_shadow_table_v1.js").read_text(encoding="utf-8")

required_partial_tokens = (
    "data-admin-user-shadow-real-link",
    "user_edit_id=",
    "target=edit-user-card#edit-user-card",
    "utilizador-shadow-table-v13",
)

required_js_tokens = (
    "forceNativeActionNavigation",
    "window.location.assign",
    "focusEditUserCardFromQuery",
    "edit-user-card",
    "scrollIntoView",
    "document.addEventListener(\"click\", forceNativeActionNavigation, true)",
)

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
print("OK: clique e foco nativo do Utilizador validados.")
