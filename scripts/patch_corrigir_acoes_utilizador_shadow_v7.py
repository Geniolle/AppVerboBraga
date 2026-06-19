from __future__ import annotations

from pathlib import Path


####################################################################################
# (1) UTILITÁRIOS
####################################################################################

ROOT = Path(__file__).resolve().parents[1]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


####################################################################################
# (2) CORRIGIR LINKS DAS AÇÕES NO PARTIAL NATIVO
####################################################################################

partial_path = ROOT / "templates" / "partials" / "admin_user_shadow_readonly_v1.html"
partial_content = read_text(partial_path)

old_view_line = '{% set view_url = "/users/new?menu=administrativo&admin_tab=utilizador&user_edit_id=" ~ user_id ~ "&user_view=1#edit-user-card" %}'
old_edit_line = '{% set edit_url = "/users/new?menu=administrativo&admin_tab=utilizador&user_edit_id=" ~ user_id ~ "#edit-user-card" %}'

new_view_line = '{% set view_url = "/users/new?menu=administrativo&admin_tab=utilizador&user_edit_id=" ~ user_id ~ "&user_readonly=1&readonly=1&mode=view&target=edit-user-card#edit-user-card" %}'
new_edit_line = '{% set edit_url = "/users/new?menu=administrativo&admin_tab=utilizador&user_edit_id=" ~ user_id ~ "&target=edit-user-card#edit-user-card" %}'

if old_view_line not in partial_content:
    raise RuntimeError("Linha antiga view_url não encontrada no partial.")

if old_edit_line not in partial_content:
    raise RuntimeError("Linha antiga edit_url não encontrada no partial.")

partial_content = partial_content.replace(old_view_line, new_view_line, 1)
partial_content = partial_content.replace(old_edit_line, new_edit_line, 1)

partial_content = partial_content.replace(
    "{% macro render_admin_user_shadow_actions_v5(row) %}",
    "{% macro render_admin_user_shadow_actions_v6(row) %}",
    1,
)

partial_content = partial_content.replace(
    "{{ render_admin_user_shadow_actions_v5(row) }}",
    "{{ render_admin_user_shadow_actions_v6(row) }}",
)

partial_content = partial_content.replace(
    "{% macro render_admin_user_shadow_readonly_v6(state) %}",
    "{% macro render_admin_user_shadow_readonly_v7(state) %}",
    1,
)

partial_content = partial_content.replace(
    "{{ render_admin_user_shadow_readonly_v6(state) }}",
    "{{ render_admin_user_shadow_readonly_v7(state) }}",
)

if "target=edit-user-card#edit-user-card" not in partial_content:
    raise RuntimeError("target=edit-user-card não ficou aplicado.")

if "user_readonly=1&readonly=1&mode=view" not in partial_content:
    raise RuntimeError("Parâmetros de readonly/view não ficaram aplicados.")

write_text(partial_path, partial_content)


####################################################################################
# (3) ATUALIZAR NEW_USER.HTML PARA MACRO V7
####################################################################################

template_path = ROOT / "templates" / "new_user.html"
template_content = read_text(template_path)

template_content = template_content.replace(
    '{% from "partials/admin_user_shadow_readonly_v1.html" import render_admin_user_shadow_readonly_v6 %}',
    '{% from "partials/admin_user_shadow_readonly_v1.html" import render_admin_user_shadow_readonly_v7 %}',
)

template_content = template_content.replace(
    '{% from "partials/admin_user_shadow_readonly_v1.html" import render_admin_user_shadow_readonly_v5 %}',
    '{% from "partials/admin_user_shadow_readonly_v1.html" import render_admin_user_shadow_readonly_v7 %}',
)

template_content = template_content.replace(
    "render_admin_user_shadow_readonly_v6(admin_subprocess_shadow_state)",
    "render_admin_user_shadow_readonly_v7(admin_subprocess_shadow_state)",
)

template_content = template_content.replace(
    "render_admin_user_shadow_readonly_v5(admin_subprocess_shadow_state)",
    "render_admin_user_shadow_readonly_v7(admin_subprocess_shadow_state)",
)

if "render_admin_user_shadow_readonly_v7(admin_subprocess_shadow_state)" not in template_content:
    raise RuntimeError("Render V7 não encontrado no new_user.html")

write_text(template_path, template_content)


####################################################################################
# (4) ATUALIZAR VALIDAÇÃO JINJA
####################################################################################

jinja_check_path = ROOT / "scripts" / "check_template_jinja_utilizador_shadow_v1.py"

jinja_check_content = '''\
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
'''

write_text(jinja_check_path, jinja_check_content)


####################################################################################
# (5) RESULTADO
####################################################################################

print("OK: ações do bloco nativo do Utilizador corrigidas.")
print("OK: Visualizar agora envia readonly/mode/view/target.")
print("OK: Editar agora envia target=edit-user-card.")
