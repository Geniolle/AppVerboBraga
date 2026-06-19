from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

root = Path.cwd()
env = Environment(loader=FileSystemLoader(str(root / "templates")))

env.get_template("new_user.html")
env.get_template("partials/admin_user_shadow_readonly_v1.html")

partial_source = (root / "templates" / "partials" / "admin_user_shadow_readonly_v1.html").read_text(
    encoding="utf-8"
)

css_source = (root / "static" / "css" / "modules" / "admin_user_shadow_table_v1.css").read_text(
    encoding="utf-8"
)

js_source = (root / "static" / "js" / "modules" / "admin_user_shadow_table_v1.js").read_text(
    encoding="utf-8"
)

required_partial_tokens = (
    "render_admin_user_shadow_readonly_v6",
    "render_admin_user_shadow_table_v6",
    "render_admin_user_shadow_actions_v5",
    "admin-user-shadow-inactive-card",
    "table-footer admin-status-table-footer-v1",
    "data-admin-user-shadow-current-page",
)

required_css_tokens = (
    ".admin-user-shadow-footer-v1 select",
    "width: 82px",
    ".admin-user-shadow-footer-v1 .pagination button.active",
    ".admin-user-shadow-inactive-card-v1",
)

required_js_tokens = (
    "prevButton.classList.remove",
    "nextButton.classList.remove",
    "currentPageLabel.classList.add",
)

missing_partial_tokens = [
    token
    for token in required_partial_tokens
    if token not in partial_source
]

missing_css_tokens = [
    token
    for token in required_css_tokens
    if token not in css_source
]

missing_js_tokens = [
    token
    for token in required_js_tokens
    if token not in js_source
]

if missing_partial_tokens:
    raise RuntimeError(
        "Tokens esperados ausentes no partial do Utilizador: "
        + ", ".join(missing_partial_tokens)
    )

if missing_css_tokens:
    raise RuntimeError(
        "Tokens esperados ausentes no CSS do Utilizador: "
        + ", ".join(missing_css_tokens)
    )

if missing_js_tokens:
    raise RuntimeError(
        "Tokens esperados ausentes no JS do Utilizador: "
        + ", ".join(missing_js_tokens)
    )

print("OK: templates Jinja carregados com sucesso.")
print("OK: layout nativo do Utilizador com cards separados validado.")
