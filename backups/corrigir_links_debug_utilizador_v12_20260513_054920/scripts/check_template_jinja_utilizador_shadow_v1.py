from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

root = Path.cwd()
env = Environment(loader=FileSystemLoader(str(root / "templates")))

env.get_template("new_user.html")
env.get_template("partials/admin_user_shadow_readonly_v1.html")

new_user_source = (root / "templates" / "new_user.html").read_text(encoding="utf-8")
partial_source = (root / "templates" / "partials" / "admin_user_shadow_readonly_v1.html").read_text(encoding="utf-8")
js_source = (root / "static" / "js" / "modules" / "admin_user_shadow_table_v1.js").read_text(encoding="utf-8")

if "render_admin_user_table_v1" in new_user_source:
    raise RuntimeError("Tabela antiga ainda está referenciada no new_user.html.")

if "partials/admin_user_table_v1.html" in new_user_source:
    raise RuntimeError("Partial antigo ainda está importado no new_user.html.")

required_partial_tokens = (
    "render_admin_user_shadow_readonly_v10",
    "render_admin_user_shadow_actions_v10",
    "href=\"{{ view_url }}\"",
    "href=\"{{ edit_url }}\"",
    "user_edit_id=",
    "user_view=1&target=edit-user-card#edit-user-card",
    "target=edit-user-card#edit-user-card",
    "data-admin-user-shadow-real-link",
)

missing_partial_tokens = [
    token
    for token in required_partial_tokens
    if token not in partial_source
]

if missing_partial_tokens:
    raise RuntimeError(
        "Tokens esperados ausentes no partial nativo do Utilizador: "
        + ", ".join(missing_partial_tokens)
    )

if "handleNativeActionClick" in js_source or "handleShadowActionClick" in js_source:
    raise RuntimeError("JS ainda intercepta clique dos botões olho/lápis.")

print("OK: templates Jinja carregados com sucesso.")
print("OK: botões olho/lápis são links HTML reais sem interceptação JS.")
