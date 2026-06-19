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

required_partial_tokens = (
    "render_admin_user_shadow_readonly_v4",
    "render_admin_user_shadow_table_v4",
    "render_admin_user_shadow_actions_v3",
    "admin-user-shadow-toolbar-v1",
    "admin-user-shadow-footer-v1",
    "admin-user-shadow-page-size-label-v1",
    "admin_user_shadow_table_v1.css",
)

required_css_tokens = (
    ".admin-user-shadow-toolbar-v1",
    ".admin-user-shadow-search-wrap-v1",
    ".admin-user-shadow-footer-v1",
    ".admin-user-shadow-page-size-label-v1 select",
    ".admin-user-shadow-pagination-v1",
    ".admin-user-shadow-action-btn-v1",
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

print("OK: templates Jinja carregados com sucesso.")
print("OK: layout nativo do Utilizador validado.")
