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

required_partial_tokens = (
    "render_admin_user_shadow_readonly_v7",
    "render_admin_user_shadow_actions_v6",
    "user_edit_id",
    "target=edit-user-card#edit-user-card",
    "user_readonly=1&readonly=1&mode=view",
    "table-icon-btn",
    "entity-status entity-status-active",
)

missing_partial_tokens = [
    token
    for token in required_partial_tokens
    if token not in partial_source
]

if missing_partial_tokens:
    raise RuntimeError(
        "Tokens esperados ausentes no partial do Utilizador: "
        + ", ".join(missing_partial_tokens)
    )

print("OK: templates Jinja carregados com sucesso.")
print("OK: links das ações nativas do Utilizador validados.")
