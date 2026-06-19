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
# (2) ATUALIZAR PARTIAL COM MACROS V2 E COLUNA AÇÕES
####################################################################################

partial_path = ROOT / "templates" / "partials" / "admin_user_shadow_readonly_v1.html"

partial_content = '''\
{% macro render_admin_user_shadow_cell_v2(row, column) %}
  {% set value = row.get(column.source, "-") %}
  {% if column.source == "status_label" %}
    <span class="status-pill status-pill-{{ row.get('status', '') }}">{{ value }}</span>
  {% else %}
    {{ value }}
  {% endif %}
{% endmacro %}

{% macro render_admin_user_shadow_actions_v1(row) %}
  {% set user_id = row.get('id', '') %}
  {% set view_url = "/users/new?menu=administrativo&admin_tab=utilizador&user_edit_id=" ~ user_id ~ "&user_readonly=1&readonly=1&mode=view&target=edit-user-card#edit-user-card" %}
  {% set edit_url = "/users/new?menu=administrativo&admin_tab=utilizador&user_edit_id=" ~ user_id ~ "&target=edit-user-card#edit-user-card" %}

  <div class="admin-user-shadow-actions-v1" role="group" aria-label="Ações do utilizador">
    <a
      class="action-icon-btn action-icon-btn-view"
      href="{{ view_url }}"
      title="Visualizar utilizador"
      aria-label="Visualizar utilizador"
    >Ver</a>
    <a
      class="action-icon-btn action-icon-btn-edit"
      href="{{ edit_url }}"
      title="Editar utilizador"
      aria-label="Editar utilizador"
    >Editar</a>
  </div>
{% endmacro %}

{% macro render_admin_user_shadow_table_v2(rows, columns) %}
<div class="admin-table-wrap">
  <table class="admin-subprocess-table-v1 admin-user-shadow-table-v1">
    <thead>
      <tr>
        {% for column in columns %}
        <th>{{ column.label }}</th>
        {% endfor %}
        <th>AÇÕES</th>
      </tr>
    </thead>
    <tbody>
      {% for row in rows %}
      <tr data-admin-user-shadow-row="{{ row.get('id', '') }}">
        {% for column in columns %}
        <td>{{ render_admin_user_shadow_cell_v2(row, column) }}</td>
        {% endfor %}
        <td>{{ render_admin_user_shadow_actions_v1(row) }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</div>
{% endmacro %}

{% macro render_admin_user_shadow_readonly_v2(state) %}
<section
  id="admin-user-shadow-readonly-card"
  class="card admin-user-shadow-readonly-card-v1"
  data-menu-scope="administrativo"
  data-admin-subprocess-shadow="utilizador"
>
  <div class="profile-card-header">
    <div>
      <h2>Utilizadores - leitura nativa</h2>
      <p class="muted">
        Validação do novo processo único. Este bloco é apenas leitura e usa as ações legadas para visualizar e editar.
      </p>
    </div>
  </div>

  <div class="admin-subsection">
    <h3>{{ state.config.active_title }}</h3>
    <p class="muted">Total: {{ state.active_rows|length }}</p>

    {% if state.active_rows %}
      {{ render_admin_user_shadow_table_v2(state.active_rows, state.config.columns) }}
    {% else %}
      <p class="empty">Sem utilizadores ativos no processo nativo.</p>
    {% endif %}
  </div>

  <div class="admin-subsection">
    <h3>{{ state.config.inactive_title }}</h3>

    {% if state.inactive_rows %}
      {{ render_admin_user_shadow_table_v2(state.inactive_rows, state.config.columns) }}
    {% else %}
      <p class="empty">Sem utilizadores inativos, pendentes ou bloqueados no processo nativo.</p>
    {% endif %}
  </div>
</section>
{% endmacro %}

{% macro render_admin_user_shadow_readonly_v1(state) %}
  {{ render_admin_user_shadow_readonly_v2(state) }}
{% endmacro %}
'''

write_text(partial_path, partial_content)


####################################################################################
# (3) ATUALIZAR NEW_USER.HTML PARA USAR MACRO V2
####################################################################################

template_path = ROOT / "templates" / "new_user.html"
template_content = read_text(template_path)

old_import = '{% from "partials/admin_user_shadow_readonly_v1.html" import render_admin_user_shadow_readonly_v1 %}'
new_import = '{% from "partials/admin_user_shadow_readonly_v1.html" import render_admin_user_shadow_readonly_v2 %}'

if old_import in template_content:
    template_content = template_content.replace(old_import, new_import, 1)
elif new_import not in template_content:
    extends_anchor = '{% extends "base.html" %}'

    if extends_anchor not in template_content:
        raise RuntimeError("Não foi possível localizar ponto de import no new_user.html")

    template_content = template_content.replace(
        extends_anchor,
        extends_anchor + "\\n\\n" + new_import,
        1,
    )

template_content = template_content.replace(
    "render_admin_user_shadow_readonly_v1(admin_subprocess_shadow_state)",
    "render_admin_user_shadow_readonly_v2(admin_subprocess_shadow_state)",
)

if "render_admin_user_shadow_readonly_v2(admin_subprocess_shadow_state)" not in template_content:
    raise RuntimeError("Render do Utilizador shadow V2 não encontrado no new_user.html")

write_text(template_path, template_content)


####################################################################################
# (4) ATUALIZAR SCRIPT DE VALIDAÇÃO JINJA
####################################################################################

jinja_check_path = ROOT / "scripts" / "check_template_jinja_utilizador_shadow_v1.py"

jinja_check_content = '''\
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
'''

write_text(jinja_check_path, jinja_check_content)


####################################################################################
# (5) RESULTADO
####################################################################################

print("OK: ações adicionadas ao bloco nativo do Utilizador.")
print("OK: new_user.html atualizado para macro render_admin_user_shadow_readonly_v2.")
print("OK: validação Jinja atualizada.")
