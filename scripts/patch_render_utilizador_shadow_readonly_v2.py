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
# (3) ATUALIZAR NEW_USER.HTML COM IMPORT DO PARTIAL
####################################################################################

template_path = ROOT / "templates" / "new_user.html"
template_content = read_text(template_path)

import_line = '{% from "partials/admin_user_shadow_readonly_v1.html" import render_admin_user_shadow_readonly_v1 %}\n'

if import_line not in template_content:
    anchor_options = [
        '{% from "partials/admin_user_table_v1.html" import render_admin_user_table_v1 %}\n',
        '{% from "macros/admin_subprocess.html" import render_admin_subprocess_state %}\n',
    ]

    inserted = False

    for anchor in anchor_options:
        if anchor in template_content:
            template_content = template_content.replace(anchor, anchor + import_line, 1)
            inserted = True
            break

    if not inserted:
        extends_anchor = '{% extends "base.html" %}\n'

        if extends_anchor not in template_content:
            raise RuntimeError("Não foi possível encontrar ponto de import no new_user.html")

        template_content = template_content.replace(
            extends_anchor,
            extends_anchor + "\n" + import_line,
            1,
        )


####################################################################################
# (4) INSERIR BLOCO READONLY DO UTILIZADOR NATIVO
####################################################################################

shadow_block = '''\
<!-- APPVERBO_UTILIZADOR_SHADOW_READONLY_V1_START -->
        {% if admin_tab == "utilizador" and admin_subprocess_shadow_state %}
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
        raise RuntimeError("Marcador final do bloco shadow readonly não encontrado.")

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
    sessao_anchor = "<!-- APPVERBO_CORRIGIR_ORDEM_ABAS_SESSOES_ADMIN_SUBPROCESS_V5_END -->"

    if sessao_anchor in template_content:
        insert_index = template_content.find(sessao_anchor) + len(sessao_anchor)
        next_line_index = template_content.find("\n", insert_index)

        if next_line_index >= 0:
            insert_index = next_line_index + 1

        template_content = (
            template_content[:insert_index]
            + "\n"
            + shadow_block
            + template_content[insert_index:]
        )
    else:
        menu_tabs_anchor = '</section>\n\n<!-- APPVERBO_SIDEBAR_SECTIONS_JSON_V2_START -->'

        if menu_tabs_anchor not in template_content:
            raise RuntimeError("Não foi possível localizar ponto seguro para inserir o bloco readonly do Utilizador.")

        template_content = template_content.replace(
            menu_tabs_anchor,
            '</section>\n\n'
            + shadow_block
            + '<!-- APPVERBO_SIDEBAR_SECTIONS_JSON_V2_START -->',
            1,
        )

write_text(template_path, template_content)


####################################################################################
# (5) RESULTADO
####################################################################################

print("OK: partial readonly do Utilizador criado.")
print("OK: new_user.html atualizado para renderizar admin_subprocess_shadow_state em modo leitura.")
