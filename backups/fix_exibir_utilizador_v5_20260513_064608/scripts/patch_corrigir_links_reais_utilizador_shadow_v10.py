from __future__ import annotations

import re
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
# (2) CORRIGIR PARTIAL PARA LINKS HTML REAIS
####################################################################################

partial_path = ROOT / "templates" / "partials" / "admin_user_shadow_readonly_v1.html"
partial_content = read_text(partial_path)

partial_content = re.sub(
    r'{%\s*macro\s+render_admin_user_shadow_actions_v\d+\(row\)\s*%}.*?{%\s*endmacro\s*%}',
    '''{% macro render_admin_user_shadow_actions_v10(row) %}
  {% set user_id = row.get('id', '') %}
  {% set view_url = "/users/new?menu=administrativo&admin_tab=utilizador&user_edit_id=" ~ user_id ~ "&user_view=1&target=edit-user-card#edit-user-card" %}
  {% set edit_url = "/users/new?menu=administrativo&admin_tab=utilizador&user_edit_id=" ~ user_id ~ "&target=edit-user-card#edit-user-card" %}

  <div class="table-actions">
    <a
      class="table-icon-btn"
      href="{{ view_url }}"
      title="Exibir utilizador"
      aria-label="Exibir utilizador"
      data-admin-user-shadow-real-link="view"
    >
      &#128065;
    </a>
    <a
      class="table-icon-btn"
      href="{{ edit_url }}"
      title="Modificar utilizador"
      aria-label="Modificar utilizador"
      data-admin-user-shadow-real-link="edit"
    >
      &#9998;
    </a>
  </div>
{% endmacro %}''',
    partial_content,
    count=1,
    flags=re.S,
)

partial_content = re.sub(
    r'render_admin_user_shadow_actions_v\d+\(row\)',
    'render_admin_user_shadow_actions_v10(row)',
    partial_content,
)

partial_content = re.sub(
    r'{%\s*macro\s+render_admin_user_shadow_readonly_v\d+\(state\)\s*%}',
    '{% macro render_admin_user_shadow_readonly_v10(state) %}',
    partial_content,
    count=1,
)

partial_content = re.sub(
    r'{{\s*render_admin_user_shadow_readonly_v\d+\(state\)\s*}}',
    '{{ render_admin_user_shadow_readonly_v10(state) }}',
    partial_content,
)

partial_content = re.sub(
    r'admin_user_shadow_table_v1\.js\?v=[^"]+',
    'admin_user_shadow_table_v1.js?v=20260512-utilizador-shadow-table-v10',
    partial_content,
)

partial_content = re.sub(
    r'admin_user_shadow_table_v1\.css\?v=[^"]+',
    'admin_user_shadow_table_v1.css?v=20260512-utilizador-shadow-layout-v10',
    partial_content,
)

required_tokens = (
    "render_admin_user_shadow_actions_v10",
    "render_admin_user_shadow_readonly_v10",
    "href=\"{{ view_url }}\"",
    "href=\"{{ edit_url }}\"",
    "user_edit_id=",
    "user_view=1&target=edit-user-card#edit-user-card",
    "target=edit-user-card#edit-user-card",
    "data-admin-user-shadow-real-link",
)

missing_tokens = [
    token
    for token in required_tokens
    if token not in partial_content
]

if missing_tokens:
    raise RuntimeError(
        "Tokens ausentes no partial nativo do Utilizador: "
        + ", ".join(missing_tokens)
    )

write_text(partial_path, partial_content)


####################################################################################
# (3) ATUALIZAR NEW_USER.HTML PARA MACRO V10
####################################################################################

template_path = ROOT / "templates" / "new_user.html"
template_content = read_text(template_path)

template_content = re.sub(
    r'{%\s*from\s+"partials/admin_user_shadow_readonly_v1.html"\s+import\s+render_admin_user_shadow_readonly_v\d+\s*%}',
    '{% from "partials/admin_user_shadow_readonly_v1.html" import render_admin_user_shadow_readonly_v10 %}',
    template_content,
)

template_content = re.sub(
    r'render_admin_user_shadow_readonly_v\d+\(admin_subprocess_shadow_state\)',
    'render_admin_user_shadow_readonly_v10(admin_subprocess_shadow_state)',
    template_content,
)

if "render_admin_user_shadow_readonly_v10(admin_subprocess_shadow_state)" not in template_content:
    raise RuntimeError("Render V10 não encontrado no new_user.html.")

write_text(template_path, template_content)


####################################################################################
# (4) LIMPAR JS DE INTERCEPTAÇÃO DE CLIQUE
####################################################################################

js_path = ROOT / "static" / "js" / "modules" / "admin_user_shadow_table_v1.js"
js_content = read_text(js_path)

js_content = re.sub(
    r'\n\s*function\s+handleNativeActionClick\(event\)\s*{.*?\n\s*}\n',
    "\n",
    js_content,
    flags=re.S,
)

js_content = re.sub(
    r'\n\s*function\s+handleShadowActionClick\(event\)\s*{.*?\n\s*}\n',
    "\n",
    js_content,
    flags=re.S,
)

js_content = re.sub(
    r'\n\s*document\.addEventListener\("click",\s*handleNativeActionClick,\s*true\);\n',
    "\n",
    js_content,
)

js_content = re.sub(
    r'\n\s*document\.addEventListener\("click",\s*handleShadowActionClick,\s*true\);\n',
    "\n",
    js_content,
)

if "handleNativeActionClick" in js_content or "handleShadowActionClick" in js_content:
    raise RuntimeError("Ainda existe interceptador de clique no JS.")

write_text(js_path, js_content)


####################################################################################
# (5) ATUALIZAR VALIDAÇÃO JINJA
####################################################################################

check_path = ROOT / "scripts" / "check_template_jinja_utilizador_shadow_v1.py"

check_content = '''\
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
    "href=\\"{{ view_url }}\\"",
    "href=\\"{{ edit_url }}\\"",
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
'''

write_text(check_path, check_content)


####################################################################################
# (6) RESULTADO
####################################################################################

print("OK: ações do Utilizador convertidas para links HTML reais.")
print("OK: interceptação JS dos botões olho/lápis removida.")
print("OK: new_user.html atualizado para render_admin_user_shadow_readonly_v10.")
