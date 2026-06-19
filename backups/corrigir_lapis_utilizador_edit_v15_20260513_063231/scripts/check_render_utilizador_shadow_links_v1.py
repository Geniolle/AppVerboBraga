from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from jinja2 import Environment, FileSystemLoader

root = Path.cwd()
env = Environment(loader=FileSystemLoader(str(root / "templates")))
template = env.get_template("partials/admin_user_shadow_readonly_v1.html")

columns = (
    SimpleNamespace(label="ID", source="id"),
    SimpleNamespace(label="NOME", source="full_name"),
    SimpleNamespace(label="EMAIL", source="login_email"),
    SimpleNamespace(label="ESTADO", source="status_label"),
)

state = SimpleNamespace(
    config=SimpleNamespace(
        active_title="Utilizadores ativos",
        inactive_title="Utilizadores inativos",
        columns=columns,
    ),
    active_rows=[
        {
            "id": 25,
            "full_name": "Teste Utilizador",
            "login_email": "teste@appverbo.local",
            "status": "active",
            "status_label": "Ativo",
        }
    ],
    inactive_rows=[],
)

html = template.module.render_admin_user_shadow_readonly_v12(state)

expected_view_href = (
    "/users/new?menu=administrativo&admin_tab=utilizador"
    "&user_edit_id=25&user_view=1&target=edit-user-card#edit-user-card"
)

expected_edit_href = (
    "/users/new?menu=administrativo&admin_tab=utilizador"
    "&user_edit_id=25&target=edit-user-card#edit-user-card"
)

required_fragments = (
    expected_view_href,
    expected_edit_href,
    'data-admin-user-shadow-real-link="view"',
    'data-admin-user-shadow-real-link="edit"',
)

missing_fragments = [
    fragment
    for fragment in required_fragments
    if fragment not in html
]

if missing_fragments:
    raise RuntimeError(
        "Links renderizados ausentes: "
        + ", ".join(missing_fragments)
    )

print("OK: href do olho renderizado corretamente.")
print("OK: href do lápis renderizado corretamente.")
