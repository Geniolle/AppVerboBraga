from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

root = Path.cwd()
env = Environment(loader=FileSystemLoader(str(root / "templates")))

env.get_template("new_user.html")
partial = env.get_template("partials/admin_user_shadow_readonly_v1.html")

partial_source = (root / "templates" / "partials" / "admin_user_shadow_readonly_v1.html").read_text(
    encoding="utf-8"
)

required_tokens = (
    "render_admin_user_shadow_readonly_v2",
    "render_admin_user_shadow_table_v2",
    "render_admin_user_shadow_actions_v1",
    "AÇÕES",
    "user_edit_id",
    "edit-user-card",
)

missing_tokens = [
    token
    for token in required_tokens
    if token not in partial_source
]

if missing_tokens:
    raise RuntimeError(
        "Tokens esperados ausentes no partial do Utilizador: "
        + ", ".join(missing_tokens)
    )

print("OK: templates Jinja carregados com sucesso.")
print("OK: ações nativas do Utilizador validadas.")
