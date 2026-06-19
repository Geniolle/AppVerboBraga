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
# (2) CRIAR PARTIAL READONLY DO SUBPROCESSO UTILIZADOR
####################################################################################

partial_path = ROOT / "templates" / "partials" / "admin_user_shadow_readonly_v1.html"

partial_content = '''\
{% macro render_admin_user_shadow_readonly_v1(state) %}
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
        Validação do novo processo único. Este bloco é apenas leitura e não altera a criação, edição ou envio de convites.
      </p>
    </div>
  </div>

  <div class="admin-subsection">
    <h3>{{ state.config.active_title }}</h3>

    {% if state.active_rows %}
    <div class="admin-table-wrap">
      <table class="admin-subprocess-table-v1 admin-user-shadow-table-v1">
        <thead>
          <tr>
            {% for column in state.config.columns %}
            <th>{{ column.label }}</th>
            {% endfor %}
          </tr>
        </thead>
        <tbody>
          {% for row in state.active_rows %}
          <tr data-admin-user-shadow-row="{{ row.get('id', '') }}">
            {% for column in state.config.columns %}
            <td>{{ row.get(column.source, "-") }}</td>
            {% endfor %}
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
    {% else %}
    <p class="empty">Sem utilizadores ativos no processo nativo.</p>
    {% endif %}
  </div>

  <div class="admin-subsection">
    <h3>{{ state.config.inactive_title }}</h3>

    {% if state.inactive_rows %}
    <div class="admin-table-wrap">
      <table class="admin-subprocess-table-v1 admin-user-shadow-table-v1">
        <thead>
          <tr>
            {% for column in state.config.columns %}
            <th>{{ column.label }}</th>
            {% endfor %}
          </tr>
        </thead>
        <tbody>
          {% for row in state.inactive_rows %}
          <tr data-admin-user-shadow-row="{{ row.get('id', '') }}">
            {% for column in state.config.columns %}
            <td>{{ row.get(column.source, "-") }}</td>
            {% endfor %}
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
    {% else %}
    <p class="empty">Sem utilizadores inativos, pendentes ou bloqueados no processo nativo.</p>
    {% endif %}
  </div>
</section>
{% endmacro %}
'''

write_text(partial_path, partial_content)


####################################################################################
# (3) ATUALIZAR IMPORT NO NEW_USER.HTML
####################################################################################

template_path = ROOT / "templates" / "new_user.html"
template_content = read_text(template_path)

import_line = '{% from "partials/admin_user_shadow_readonly_v1.html" import render_admin_user_shadow_readonly_v1 %}\n'

if import_line not in template_content:
    if '{% from "partials/admin_user_table_v1.html" import render_admin_user_table_v1 %}\n' in template_content:
        template_content = template_content.replace(
            '{% from "partials/admin_user_table_v1.html" import render_admin_user_table_v1 %}\n',
            '{% from "partials/admin_user_table_v1.html" import render_admin_user_table_v1 %}\n' + import_line,
            1,
        )
    elif '{% from "macros/admin_subprocess.html" import render_admin_subprocess_state %}\n' in template_content:
        template_content = template_content.replace(
            '{% from "macros/admin_subprocess.html" import render_admin_subprocess_state %}\n',
            '{% from "macros/admin_subprocess.html" import render_admin_subprocess_state %}\n' + import_line,
            1,
        )
    elif '{% extends "base.html" %}' in template_content:
        template_content = template_content.replace(
            '{% extends "base.html" %}',
            '{% extends "base.html" %}\n\n' + import_line,
            1,
        )
    else:
        raise RuntimeError("Não foi possível encontrar ponto de import no new_user.html")


####################################################################################
# (4) INSERIR BLOCO READONLY ANTES DO CARD LEGADO DO UTILIZADOR
####################################################################################

shadow_block = '''\
<!-- APPVERBO_UTILIZADOR_SHADOW_READONLY_V1_START -->
        {% if current_user_is_admin and admin_tab == "utilizador" and admin_subprocess_shadow_state %}
          {{ render_admin_user_shadow_readonly_v1(admin_subprocess_shadow_state) }}
        {% endif %}
        <!-- APPVERBO_UTILIZADOR_SHADOW_READONLY_V1_END -->

'''

start_marker = "<!-- APPVERBO_UTILIZADOR_SHADOW_READONLY_V1_START -->"
end_marker = "<!-- APPVERBO_UTILIZADOR_SHADOW_READONLY_V1_END -->"

start_index = template_content.find(start_marker)

if start_index >= 0:
    end_index = template_content.find(end_marker, start_index)

    if end_index < 0:
        raise RuntimeError("Marcador final do bloco readonly não encontrado.")

    end_index = template_content.find("\n", end_index)

    if end_index < 0:
        end_index = len(template_content)
    else:
        end_index += 1

    template_content = (
        template_content[:start_index]
        + shadow_block
        + template_content[end_index:]
    )
else:
    create_user_index = template_content.find('id="create-user-card"')

    if create_user_index < 0:
        raise RuntimeError("Não foi possível localizar id=\"create-user-card\" no new_user.html")

    section_start_index = template_content.rfind("<section", 0, create_user_index)

    if section_start_index < 0:
        raise RuntimeError("Não foi possível localizar início da section create-user-card.")

    admin_if_index = template_content.rfind("{% if current_user_is_admin %}", 0, section_start_index)

    if admin_if_index >= 0:
        insert_index = admin_if_index
    else:
        insert_index = section_start_index

    template_content = (
        template_content[:insert_index]
        + shadow_block
        + template_content[insert_index:]
    )

write_text(template_path, template_content)


####################################################################################
# (5) RESULTADO
####################################################################################

print("OK: partial readonly do Utilizador criado/atualizado.")
print("OK: bloco readonly inserido antes da área legada de Utilizador.")
