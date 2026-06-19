from pathlib import Path
import ast
import re
import sys

ROOT = Path.cwd()

AGENTS_UPPER_PATH = ROOT / "AGENTS.md"
AGENTS_TITLE_PATH = ROOT / "Agents.md"

MODELS_PATH = ROOT / "appverbo" / "admin_subprocesses" / "models.py"
REGISTRY_PATH = ROOT / "appverbo" / "admin_subprocesses" / "registry.py"
SERVICE_PATH = ROOT / "appverbo" / "admin_subprocesses" / "service.py"
PAGE_HANDLER_PATH = ROOT / "appverbo" / "routes" / "profile" / "page_handler.py"
TEMPLATE_PATH = ROOT / "templates" / "new_user.html"
MACRO_PATH = ROOT / "templates" / "macros" / "admin_subprocess.html"
ADMIN_CSS_PATH = ROOT / "static" / "css" / "modules" / "admin_subprocesses_v1.css"
ADMIN_JS_PATH = ROOT / "static" / "js" / "modules" / "admin_subprocesses_v1.js"
SESSOES_JS_PATH = ROOT / "static" / "js" / "modules" / "sidebar_sections_layout_v1.js"
SESSOES_CSS_PATH = ROOT / "static" / "css" / "modules" / "sidebar_sections_layout_v1.css"

AGENTS_MARKER_START = "<!-- APPVERBO_MIGRAR_SESSOES_ADMIN_SUBPROCESS_V2_START -->"
AGENTS_MARKER_END = "<!-- APPVERBO_MIGRAR_SESSOES_ADMIN_SUBPROCESS_V2_END -->"

PAGE_IMPORT_MARKER_START = "# APPVERBO_ADMIN_SUBPROCESS_PAGE_IMPORTS_V2_START"
PAGE_IMPORT_MARKER_END = "# APPVERBO_ADMIN_SUBPROCESS_PAGE_IMPORTS_V2_END"

PAGE_STATE_MARKER_START = "# APPVERBO_ADMIN_SUBPROCESS_STATE_SESSOES_V2_START"
PAGE_STATE_MARKER_END = "# APPVERBO_ADMIN_SUBPROCESS_STATE_SESSOES_V2_END"

TEMPLATE_MARKER_START = "<!-- APPVERBO_MIGRAR_SESSOES_ADMIN_SUBPROCESS_V2_START -->"
TEMPLATE_MARKER_END = "<!-- APPVERBO_MIGRAR_SESSOES_ADMIN_SUBPROCESS_V2_END -->"

JS_DISABLE_REASON = "Sessões migrado para AdminSubprocessState + macro Jinja V2."

ADMIN_CSS_CACHE = "/static/css/modules/admin_subprocesses_v1.css?v=20260505-migrar-sessoes-admin-subprocess-v2"
ADMIN_JS_CACHE = "/static/js/modules/admin_subprocesses_v1.js?v=20260505-migrar-sessoes-admin-subprocess-v2"


def fail_v2(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


def read_text_v2(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text_v2(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
    print(f"OK: escrito {path}")


def resolve_agents_path_v2() -> Path:
    if AGENTS_UPPER_PATH.exists():
        return AGENTS_UPPER_PATH

    if AGENTS_TITLE_PATH.exists():
        return AGENTS_TITLE_PATH

    AGENTS_UPPER_PATH.write_text("# AGENTS.md\n\n", encoding="utf-8")
    return AGENTS_UPPER_PATH


def strip_trailing_whitespace_v2(content: str) -> str:
    lines = content.splitlines()
    return "\n".join(line.rstrip() for line in lines) + ("\n" if content.endswith("\n") else "")


def remove_marked_block_v2(content: str, start_marker: str, end_marker: str) -> str:
    while start_marker in content and end_marker in content:
        content = re.sub(
            re.escape(start_marker) + r"[\s\S]*?" + re.escape(end_marker),
            "",
            content,
            count=1,
        )

    return content


def disable_js_block_v2(content: str, start_marker: str, end_marker: str, reason: str) -> str:
    if start_marker not in content or end_marker not in content:
        return content

    replacement = f"""{start_marker}
// Desativado pelo AdminSubprocess V2.
// Motivo: {reason}
{end_marker}"""

    return re.sub(
        re.escape(start_marker) + r"[\s\S]*?" + re.escape(end_marker),
        replacement,
        content,
        count=1,
    )


def remove_section_by_id_v2(content: str, section_id: str) -> str:
    pattern = re.compile(
        r"<section\b[^>]*\bid=[\"']" + re.escape(section_id) + r"[\"'][^>]*>",
        re.IGNORECASE,
    )

    while True:
        match = pattern.search(content)

        if not match:
            return content

        start = match.start()
        cursor = match.end()
        depth = 1
        token_pattern = re.compile(r"</?section\b[^>]*>", re.IGNORECASE)

        for token in token_pattern.finditer(content, cursor):
            token_text = token.group(0).lower()

            if token_text.startswith("</section"):
                depth -= 1

                if depth == 0:
                    end = token.end()
                    content = content[:start] + content[end:]
                    break
            else:
                depth += 1
        else:
            fail_v2(f"não consegui encontrar fechamento da section #{section_id}")


####################################################################################
# (1) VALIDAR FICHEIROS
####################################################################################

required_paths = [
    MODELS_PATH,
    REGISTRY_PATH,
    SERVICE_PATH,
    PAGE_HANDLER_PATH,
    TEMPLATE_PATH,
    MACRO_PATH,
    ADMIN_CSS_PATH,
    ADMIN_JS_PATH,
    SESSOES_JS_PATH,
    SESSOES_CSS_PATH,
]

for required_path in required_paths:
    if not required_path.exists():
        fail_v2(f"ficheiro obrigatório não encontrado: {required_path}")


####################################################################################
# (2) ATUALIZAR MODELS COM CAMPOS GENERICOS DE FORMULARIO
####################################################################################

models_content = read_text_v2(MODELS_PATH)

if "mode_field:" not in models_content:
    old = '''    label_field: str = "label"
    enabled: bool = True
'''
    new = '''    label_field: str = "label"
    mode_field: str = "subprocess_mode"
    edit_key_field: str = "subprocess_edit_key"
    return_url_field: str = "subprocess_return_url"
    create_mode_value: str = "create"
    edit_mode_value: str = "edit"
    enabled: bool = True
'''

    if old not in models_content:
        fail_v2("não encontrei ponto para inserir campos genericos no AdminSubprocessConfig.")

    models_content = models_content.replace(old, new, 1)

try:
    ast.parse(models_content)
except SyntaxError as exc:
    fail_v2(f"models.py ficaria inválido: {exc}")

write_text_v2(MODELS_PATH, models_content)


####################################################################################
# (3) ATUALIZAR REGISTRY PARA SESSOES USAR CAMPOS LEGADOS DO ENDPOINT ATUAL
####################################################################################

registry_content = read_text_v2(REGISTRY_PATH)

if 'mode_field="section_mode"' not in registry_content:
    old = '''    identity_field="key",
    label_field="label",
    enabled=True,
'''
    new = '''    identity_field="key",
    label_field="label",
    mode_field="section_mode",
    edit_key_field="original_section_key",
    return_url_field="sidebar_section_return_url",
    create_mode_value="create",
    edit_mode_value="edit",
    enabled=True,
'''

    occurrence_index = registry_content.find("SESSOES_CONFIG = AdminSubprocessConfig(")

    if occurrence_index < 0:
        fail_v2("SESSOES_CONFIG não encontrado no registry.py.")

    before = registry_content[:occurrence_index]
    after = registry_content[occurrence_index:]

    if old not in after:
        fail_v2("não encontrei ponto para configurar campos legados em SESSOES_CONFIG.")

    after = after.replace(old, new, 1)
    registry_content = before + after

try:
    ast.parse(registry_content)
except SyntaxError as exc:
    fail_v2(f"registry.py ficaria inválido: {exc}")

write_text_v2(REGISTRY_PATH, registry_content)


####################################################################################
# (4) ATUALIZAR MACRO GENERICA PARA FORMULARIO + ATIVOS + INATIVOS + ACOES
####################################################################################

macro_content = r'''
{% macro admin_subprocess_get_value(row, key, default="") %}
  {{ row.get(key, default) if row else default }}
{% endmacro %}


{% macro render_admin_subprocess_field(field, value="") %}
  <div class="field admin-subprocess-field-v1 {{ field.css_class }}">
    <label for="admin_subprocess_{{ field.key }}">{{ field.label }}{% if field.required %} *{% endif %}</label>

    {% if field.field_type == "select" %}
      <select
        id="admin_subprocess_{{ field.key }}"
        name="{{ field.input_name }}"
        {% if field.required %}required{% endif %}
      >
        {% for option_value, option_label in field.options %}
          <option value="{{ option_value }}" {% if value == option_value %}selected{% endif %}>{{ option_label }}</option>
        {% endfor %}
      </select>
    {% else %}
      <input
        id="admin_subprocess_{{ field.key }}"
        name="{{ field.input_name }}"
        type="{{ field.field_type }}"
        value="{{ value }}"
        {% if field.required %}required{% endif %}
        {% if field.max_length %}maxlength="{{ field.max_length }}"{% endif %}
        {% if field.placeholder %}placeholder="{{ field.placeholder }}"{% endif %}
      >
    {% endif %}
  </div>
{% endmacro %}


{% macro render_admin_subprocess_form(state) %}
  <section
    id="{{ state.config.edit_target if state.is_editing else state.config.default_target }}"
    class="card admin-subprocess-card-v1 admin-subprocess-form-card-v1"
    data-admin-subprocess="{{ state.config.key }}"
  >
    {% if state.success %}
      <div class="alert ok">{{ state.success }}</div>
    {% endif %}

    {% if state.error %}
      <div class="alert error">{{ state.error }}</div>
    {% endif %}

    {% if state.is_editing %}
      <h2>{{ state.config.edit_title }}</h2>

      <form method="post" action="{{ state.config.save_endpoint }}" class="admin-subprocess-form-v1">
        <input type="hidden" name="{{ state.config.mode_field }}" value="{{ state.config.edit_mode_value }}">
        <input type="hidden" name="{{ state.config.edit_key_field }}" value="{{ state.edit_key }}">
        <input type="hidden" name="{{ state.config.return_url_field }}" value="{{ state.return_url }}">

        <div class="admin-subprocess-grid-v1">
          {% for field in state.config.fields %}
            {% set field_value = state.edit_data.get(field.key, "") if state.edit_data else "" %}
            {{ render_admin_subprocess_field(field, field_value) }}
          {% endfor %}
        </div>

        <div class="form-action-row admin-subprocess-actions-v1">
          <button type="submit" class="action-btn">Guardar</button>
          <a class="action-btn-cancel" href="{{ state.return_url }}">Cancelar</a>
        </div>
      </form>
    {% else %}
      <details class="entity-create-collapse admin-subprocess-create-collapse-v1">
        <summary>
          <span>{{ state.config.create_title }}</span>
        </summary>

        <div class="entity-create-body">
          <form method="post" action="{{ state.config.save_endpoint }}" class="admin-subprocess-form-v1">
            <input type="hidden" name="{{ state.config.mode_field }}" value="{{ state.config.create_mode_value }}">
            <input type="hidden" name="{{ state.config.edit_key_field }}" value="">
            <input type="hidden" name="{{ state.config.return_url_field }}" value="{{ state.return_url }}">

            <div class="admin-subprocess-grid-v1">
              {% for field in state.config.fields %}
                {{ render_admin_subprocess_field(field, "") }}
              {% endfor %}
            </div>

            <div class="form-action-row admin-subprocess-actions-v1">
              <button type="submit" class="action-btn">Guardar</button>
              <button
                type="button"
                class="action-btn-cancel"
                onclick="const form=this.closest('form'); const details=this.closest('details'); if(form){form.reset();} if(details){details.open=false;}"
              >Cancelar</button>
            </div>
          </form>
        </div>
      </details>
    {% endif %}
  </section>
{% endmacro %}


{% macro render_admin_subprocess_row_actions(state, row, status_value) %}
  {% set row_key = row.get(state.config.identity_field, row.get("key", row.get("id", ""))) %}
  {% set row_label = row.get(state.config.label_field, row.get("label", row.get("name", ""))) %}
  {% set row_status_label = row.get("status_label", "Ativo" if status_value == state.config.active_value else "Inativo") %}
  {% set row_system_label = row.get("visibility_scope_label", "") %}

  <div class="admin-subprocess-row-actions-v1">
    {% if status_value == state.config.active_value and state.config.move_endpoint %}
      <form method="post" action="{{ state.config.move_endpoint }}" class="admin-subprocess-inline-form-v1">
        <input type="hidden" name="section_key" value="{{ row_key }}">
        <input type="hidden" name="direction" value="up">
        <input type="hidden" name="{{ state.config.return_url_field }}" value="{{ state.return_url }}">
        <button type="submit" class="admin-subprocess-action-btn-v1" title="Subir" aria-label="Subir">↑</button>
      </form>

      <form method="post" action="{{ state.config.move_endpoint }}" class="admin-subprocess-inline-form-v1">
        <input type="hidden" name="section_key" value="{{ row_key }}">
        <input type="hidden" name="direction" value="down">
        <input type="hidden" name="{{ state.config.return_url_field }}" value="{{ state.return_url }}">
        <button type="submit" class="admin-subprocess-action-btn-v1" title="Descer" aria-label="Descer">↓</button>
      </form>
    {% endif %}

    <button
      type="button"
      class="admin-subprocess-action-btn-v1"
      title="Visualizar detalhes"
      aria-label="Visualizar detalhes"
      data-admin-subprocess-view
      data-view-title="{{ state.config.singular_label }}"
      data-view-details="Nome: {{ row_label }}&#10;Sistema: {{ row_system_label or '-' }}&#10;Estado: {{ row_status_label }}"
    >👁</button>

    <a
      class="admin-subprocess-action-btn-v1 admin-subprocess-action-link-v1"
      title="Editar"
      aria-label="Editar"
      href="/users/new?menu=administrativo&amp;admin_tab={{ state.config.key }}{% if state.config.key == 'sessoes' %}&amp;sidebar_sections_tab=sessoes{% endif %}&amp;target={{ state.config.edit_target }}&amp;{{ state.config.edit_param }}={{ row_key }}#{{ state.config.edit_target }}"
    >✎</a>
  </div>
{% endmacro %}


{% macro render_admin_subprocess_table(state, rows, title, status_value) %}
  <section
    id="{{ state.config.default_target if status_value == state.config.active_value else state.config.default_target ~ '-inactive' }}"
    class="card admin-subprocess-card-v1 admin-subprocess-table-card-v1"
    data-admin-subprocess="{{ state.config.key }}"
    data-admin-subprocess-status="{{ status_value }}"
  >
    <h2>{{ title }}</h2>

    {% if rows %}
      <div class="admin-subprocess-table-wrap-v1">
        <table class="admin-subprocess-table-v1">
          <thead>
            <tr>
              {% for column in state.config.columns %}
                <th class="{{ column.css_class }}">{{ column.label }}</th>
              {% endfor %}
              <th>AÇÕES</th>
            </tr>
          </thead>
          <tbody>
            {% for row in rows %}
              <tr>
                {% for column in state.config.columns %}
                  {% set cell_value = row.get(column.source, "") %}
                  <td class="{{ column.css_class }}">
                    {% if column.key == "status" %}
                      <span class="admin-subprocess-badge-v1 {% if status_value == state.config.active_value %}admin-subprocess-badge-active-v1{% else %}admin-subprocess-badge-inactive-v1{% endif %}">
                        {{ cell_value or ("Ativo" if status_value == state.config.active_value else "Inativo") }}
                      </span>
                    {% else %}
                      {{ cell_value }}
                    {% endif %}
                  </td>
                {% endfor %}
                <td>
                  {{ render_admin_subprocess_row_actions(state, row, status_value) }}
                </td>
              </tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
    {% else %}
      <p class="empty">Sem registos.</p>
    {% endif %}
  </section>
{% endmacro %}


{% macro render_admin_subprocess_state(state) %}
  {{ render_admin_subprocess_form(state) }}
  {{ render_admin_subprocess_table(state, state.active_rows, state.config.active_title, state.config.active_value) }}
  {{ render_admin_subprocess_table(state, state.inactive_rows, state.config.inactive_title, state.config.inactive_value) }}
{% endmacro %}
'''

write_text_v2(MACRO_PATH, macro_content)


####################################################################################
# (5) ATUALIZAR CSS GENERICO
####################################################################################

admin_css_content = r'''
/* APPVERBO_ADMIN_SUBPROCESSES_V1_START */

.admin-subprocess-card-v1 {
  display: block;
  visibility: visible;
  width: 100%;
  box-sizing: border-box;
}

.admin-subprocess-form-card-v1 {
  background: #f3f6fb;
  border: 1px solid #d5dceb;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
}

.admin-subprocess-table-card-v1 {
  background: #ffffff;
  border: 1px solid #d5dceb;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
}

.admin-subprocess-card-v1 h2 {
  margin: 0 0 12px;
  color: #12213a;
  font-size: 22px;
  font-weight: 800;
}

.admin-subprocess-form-v1 {
  width: 100%;
}

.admin-subprocess-create-collapse-v1 > summary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 112px;
  min-height: 38px;
  padding: 0 16px;
  border-radius: 7px;
  background: #0f56c5;
  color: #ffffff;
  font-weight: 800;
  cursor: pointer;
  list-style: none;
}

.admin-subprocess-create-collapse-v1 > summary::-webkit-details-marker {
  display: none;
}

.admin-subprocess-create-collapse-v1[open] > summary {
  margin-bottom: 14px;
}

.admin-subprocess-grid-v1 {
  display: grid;
  grid-template-columns: minmax(240px, 320px) minmax(220px, 260px) minmax(160px, 220px);
  gap: 12px;
  align-items: end;
  width: 100%;
}

.admin-subprocess-field-v1 label {
  display: block;
  margin-bottom: 6px;
  color: #12213a;
  font-size: 11px;
  font-weight: 800;
  text-transform: uppercase;
}

.admin-subprocess-field-v1 input,
.admin-subprocess-field-v1 select {
  width: 100%;
  min-height: 38px;
  border: 1px solid #c6d0e2;
  border-radius: 7px;
  background: #ffffff;
  color: #12213a;
  padding: 8px 10px;
  box-sizing: border-box;
  font-size: 13px;
}

.admin-subprocess-actions-v1 {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 8px;
  margin-top: 12px;
}

.admin-subprocess-actions-v1 .action-btn,
.admin-subprocess-actions-v1 .action-btn-cancel {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 112px;
  width: 112px;
  height: 38px;
  min-height: 38px;
  box-sizing: border-box;
  text-decoration: none;
}

.admin-subprocess-table-wrap-v1,
.admin-subprocess-table-v1 {
  width: 100%;
}

.admin-subprocess-table-v1 {
  border-collapse: collapse;
}

.admin-subprocess-table-v1 th,
.admin-subprocess-table-v1 td {
  padding: 10px 12px;
  border-bottom: 1px solid #e3e8f2;
  text-align: left;
  vertical-align: middle;
}

.admin-subprocess-table-v1 th {
  color: #12213a;
  font-size: 11px;
  font-weight: 800;
  text-transform: uppercase;
}

.admin-subprocess-table-v1 th:last-child,
.admin-subprocess-table-v1 td:last-child {
  text-align: right;
}

.admin-subprocess-row-actions-v1 {
  display: inline-flex;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
}

.admin-subprocess-inline-form-v1 {
  display: inline-flex;
  margin: 0;
  padding: 0;
}

.admin-subprocess-action-btn-v1 {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  min-width: 30px;
  height: 30px;
  min-height: 30px;
  padding: 0;
  border: 1px solid #b9cdf5;
  border-radius: 7px;
  background: #eef5ff;
  color: #174ea6;
  font-size: 15px;
  font-weight: 800;
  line-height: 1;
  text-align: center;
  text-decoration: none;
  cursor: pointer;
}

.admin-subprocess-action-btn-v1:hover {
  background: #dfeaff;
  border-color: #7fa8f2;
}

.admin-subprocess-badge-v1 {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 3px 9px;
  border: 1px solid transparent;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}

.admin-subprocess-badge-active-v1 {
  border-color: #badbcc;
  background: #e9f7ef;
  color: #0f5132;
}

.admin-subprocess-badge-inactive-v1 {
  border-color: #f0c36d;
  background: #fff7e0;
  color: #8a5a00;
}

@media (max-width: 1100px) {
  .admin-subprocess-grid-v1 {
    grid-template-columns: 1fr;
  }
}

/* APPVERBO_ADMIN_SUBPROCESSES_V1_END */
'''

write_text_v2(ADMIN_CSS_PATH, admin_css_content)


####################################################################################
# (6) ATUALIZAR JS GENERICO
####################################################################################

admin_js_content = r'''
// APPVERBO_ADMIN_SUBPROCESSES_V1_START
(function () {
  "use strict";

  //###################################################################################
  // (1) VISUALIZAR DETALHES GENERICO
  //###################################################################################

  function instalarVisualizarAdminSubprocessV1() {
    if (window.__appverboAdminSubprocessV1 === true) {
      return;
    }

    window.__appverboAdminSubprocessV1 = true;

    document.addEventListener("click", function (event) {
      const button = event.target.closest("[data-admin-subprocess-view]");

      if (!button) {
        return;
      }

      event.preventDefault();

      const title = button.getAttribute("data-view-title") || "Detalhes";
      const details = button.getAttribute("data-view-details") || "";

      alert(title + (details ? "\n" + details : ""));
    });
  }

  //###################################################################################
  // (2) INICIAR
  //###################################################################################

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", instalarVisualizarAdminSubprocessV1);
  }
  else {
    instalarVisualizarAdminSubprocessV1();
  }
})();
// APPVERBO_ADMIN_SUBPROCESSES_V1_END
'''

write_text_v2(ADMIN_JS_PATH, admin_js_content)


####################################################################################
# (7) ATUALIZAR PAGE_HANDLER PARA GERAR admin_subprocess_state EM SESSOES
####################################################################################

page_content = read_text_v2(PAGE_HANDLER_PATH)

import_block = f'''{PAGE_IMPORT_MARKER_START}
from appverbo.admin_subprocesses.registry import get_admin_subprocess_config
from appverbo.admin_subprocesses.service import build_admin_subprocess_state
{PAGE_IMPORT_MARKER_END}
'''

page_content = remove_marked_block_v2(page_content, PAGE_IMPORT_MARKER_START, PAGE_IMPORT_MARKER_END)

if "from appverbo.admin_subprocesses.registry import get_admin_subprocess_config" not in page_content:
    import_anchor = "from appverbo"
    match = re.search(r"^(from appverbo[^\n]+\n)", page_content, re.MULTILINE)

    if match:
        page_content = page_content[:match.start()] + import_block + page_content[match.start():]
    else:
        page_content = import_block + "\n" + page_content

if "admin_subprocess_state_v2" not in page_content:
    state_block = f'''    {PAGE_STATE_MARKER_START}
    admin_subprocess_state_v2 = None

    if resolved_admin_tab == "sessoes":
        sessoes_subprocess_config_v2 = get_admin_subprocess_config("sessoes")

        if sessoes_subprocess_config_v2 is not None:
            all_sidebar_sections_for_subprocess_v2 = list(active_sidebar_sections_v22 or []) + list(inactive_sidebar_sections_v22 or [])
            clean_sidebar_section_edit_key_v2 = str(sidebar_section_edit_key or "").strip()

            admin_subprocess_state_v2 = build_admin_subprocess_state(
                config=sessoes_subprocess_config_v2,
                rows=all_sidebar_sections_for_subprocess_v2,
                edit_key=clean_sidebar_section_edit_key_v2,
                success=settings_success if resolved_admin_tab == "sessoes" else "",
                error=settings_error if resolved_admin_tab == "sessoes" else "",
                return_url="/users/new?menu=administrativo&admin_tab=sessoes&sidebar_sections_tab=sessoes&target=admin-sidebar-sections-card#admin-sidebar-sections-card",
            )
    {PAGE_STATE_MARKER_END}
'''

    anchor = "    context = {\n"

    if anchor not in page_content:
        fail_v2("não encontrei 'context = {' no page_handler.py para inserir admin_subprocess_state_v2.")

    page_content = page_content.replace(anchor, state_block + "\n" + anchor, 1)

if '"admin_subprocess_state": admin_subprocess_state_v2,' not in page_content:
    context_anchor = '''        "admin_tab": resolved_admin_tab,
'''

    if context_anchor not in page_content:
        fail_v2("não encontrei admin_tab no contexto para inserir admin_subprocess_state.")

    page_content = page_content.replace(
        context_anchor,
        context_anchor + '''        "admin_subprocess_state": admin_subprocess_state_v2,
''',
        1,
    )

try:
    ast.parse(page_content)
except SyntaxError as exc:
    fail_v2(f"page_handler.py ficaria inválido: {exc}")

write_text_v2(PAGE_HANDLER_PATH, page_content)


####################################################################################
# (8) ATUALIZAR TEMPLATE PARA USAR MACRO EM SESSOES E REMOVER BLOCOS ANTIGOS
####################################################################################

template_content = read_text_v2(TEMPLATE_PATH)

template_content = strip_trailing_whitespace_v2(template_content)

for start_marker, end_marker in [
    ("<!-- APPVERBO_SESSOES_SERVER_RENDER_IGUAL_ENTIDADE_V25_START -->", "<!-- APPVERBO_SESSOES_SERVER_RENDER_IGUAL_ENTIDADE_V25_END -->"),
    ("<!-- APPVERBO_SESSOES_SERVER_RENDER_UNICO_V28_START -->", "<!-- APPVERBO_SESSOES_SERVER_RENDER_UNICO_V28_END -->"),
    ("<!-- APPVERBO_SESSOES_SERVER_RENDER_UNICO_V29_START -->", "<!-- APPVERBO_SESSOES_SERVER_RENDER_UNICO_V29_END -->"),
    ("<!-- APPVERBO_SESSOES_FLUXO_NATIVO_IGUAL_ENTIDADE_V30_START -->", "<!-- APPVERBO_SESSOES_FLUXO_NATIVO_IGUAL_ENTIDADE_V30_END -->"),
    (TEMPLATE_MARKER_START, TEMPLATE_MARKER_END),
]:
    template_content = remove_marked_block_v2(template_content, start_marker, end_marker)

for section_id in [
    "admin-sidebar-sections-form-card",
    "admin-sidebar-sections-create-card",
    "admin-sidebar-sections-card",
    "admin-sidebar-sections-inactive-card",
]:
    template_content = remove_section_by_id_v2(template_content, section_id)

macro_import = '{% from "macros/admin_subprocess.html" import render_admin_subprocess_state %}'

if macro_import not in template_content:
    if "{% extends" in template_content:
        extend_match = re.search(r"({%\s*extends[^\n]+%}\s*)", template_content)

        if extend_match:
            template_content = template_content[:extend_match.end()] + "\n" + macro_import + "\n" + template_content[extend_match.end():]
        else:
            template_content = macro_import + "\n" + template_content
    else:
        template_content = macro_import + "\n" + template_content

macro_block = f'''{TEMPLATE_MARKER_START}
        {{% if admin_tab == "sessoes" and admin_subprocess_state %}}
          {{{{ render_admin_subprocess_state(admin_subprocess_state) }}}}
        {{% endif %}}
        {TEMPLATE_MARKER_END}
'''

anchor = '<section id="dynamic-process-card"'

if anchor not in template_content:
    fail_v2("não encontrei âncora dynamic-process-card no template.")

template_content = template_content.replace(anchor, macro_block + "\n" + anchor, 1)

if ADMIN_CSS_CACHE not in template_content:
    if "</head>" in template_content:
        template_content = template_content.replace(
            "</head>",
            f'  <link rel="stylesheet" href="{ADMIN_CSS_CACHE}">\n</head>',
            1,
        )
    else:
        fail_v2("não encontrei </head> para incluir CSS admin_subprocesses_v1.css.")

if ADMIN_JS_CACHE not in template_content:
    if "<!-- APPVERBO_UTILIZADOR_VIEW_TOGGLE_V3_START -->
<script defer src="/static/appverbo/js/utilizador_view_toggle.js"></script>
<script defer src="/static/js/utilizador_view_toggle.js"></script>
<!-- APPVERBO_UTILIZADOR_VIEW_TOGGLE_V3_END -->
</body>" in template_content:
        template_content = template_content.replace(
            "<!-- APPVERBO_UTILIZADOR_VIEW_TOGGLE_V3_START -->
<script defer src="/static/appverbo/js/utilizador_view_toggle.js"></script>
<script defer src="/static/js/utilizador_view_toggle.js"></script>
<!-- APPVERBO_UTILIZADOR_VIEW_TOGGLE_V3_END -->
</body>",
            f'  <script src="{ADMIN_JS_CACHE}"></script>\n<!-- APPVERBO_UTILIZADOR_VIEW_TOGGLE_V3_START -->
<script defer src="/static/appverbo/js/utilizador_view_toggle.js"></script>
<script defer src="/static/js/utilizador_view_toggle.js"></script>
<!-- APPVERBO_UTILIZADOR_VIEW_TOGGLE_V3_END -->
</body>',
            1,
        )
    else:
        fail_v2("não encontrei <!-- APPVERBO_UTILIZADOR_VIEW_TOGGLE_V3_START -->
<script defer src="/static/appverbo/js/utilizador_view_toggle.js"></script>
<script defer src="/static/js/utilizador_view_toggle.js"></script>
<!-- APPVERBO_UTILIZADOR_VIEW_TOGGLE_V3_END -->
</body> para incluir JS admin_subprocesses_v1.js.")

template_content = strip_trailing_whitespace_v2(template_content)
write_text_v2(TEMPLATE_PATH, template_content)


####################################################################################
# (9) DESATIVAR CONTROLADORES ANTIGOS DE SESSOES
####################################################################################

sessoes_js_content = read_text_v2(SESSOES_JS_PATH)

for start_marker, end_marker in [
    ("// APPVERBO_SESSOES_INATIVAS_CARD_FORA_V15_START", "// APPVERBO_SESSOES_INATIVAS_CARD_FORA_V15_END"),
    ("// APPVERBO_SESSOES_PADRAO_ENTIDADE_V18_START", "// APPVERBO_SESSOES_PADRAO_ENTIDADE_V18_END"),
    ("// APPVERBO_SESSOES_INATIVAS_RENDER_BD_V20_START", "// APPVERBO_SESSOES_INATIVAS_RENDER_BD_V20_END"),
    ("// APPVERBO_SESSOES_LIMPAR_DYNAMIC_ENTIDADE_V21_START", "// APPVERBO_SESSOES_LIMPAR_DYNAMIC_ENTIDADE_V21_END"),
    ("// APPVERBO_SESSOES_BACKEND_SPLIT_ENTIDADE_V22_START", "// APPVERBO_SESSOES_BACKEND_SPLIT_ENTIDADE_V22_END"),
    ("// APPVERBO_SESSOES_CONTROLADOR_UNICO_V23_START", "// APPVERBO_SESSOES_CONTROLADOR_UNICO_V23_END"),
    ("// APPVERBO_SESSOES_INATIVAS_ACOES_VISIVEIS_V24_START", "// APPVERBO_SESSOES_INATIVAS_ACOES_VISIVEIS_V24_END"),
    ("// APPVERBO_SESSOES_SERVER_RENDER_IGUAL_ENTIDADE_V25_START", "// APPVERBO_SESSOES_SERVER_RENDER_IGUAL_ENTIDADE_V25_END"),
    ("// APPVERBO_SESSOES_REEXIBIR_CRIAR_AO_RETORNAR_V27_START", "// APPVERBO_SESSOES_REEXIBIR_CRIAR_AO_RETORNAR_V27_END"),
    ("// APPVERBO_SESSOES_REMOVER_DUPLICADOS_SERVER_RENDER_V28_START", "// APPVERBO_SESSOES_REMOVER_DUPLICADOS_SERVER_RENDER_V28_END"),
    ("// APPVERBO_SESSOES_CORRIGIR_V28_REMOVER_DUPLICADOS_V29_START", "// APPVERBO_SESSOES_CORRIGIR_V28_REMOVER_DUPLICADOS_V29_END"),
    ("// APPVERBO_SESSOES_FLUXO_NATIVO_IGUAL_ENTIDADE_V30_START", "// APPVERBO_SESSOES_FLUXO_NATIVO_IGUAL_ENTIDADE_V30_END"),
]:
    sessoes_js_content = disable_js_block_v2(sessoes_js_content, start_marker, end_marker, JS_DISABLE_REASON)

write_text_v2(SESSOES_JS_PATH, sessoes_js_content)


####################################################################################
# (10) LIMPAR CSS ANTIGO DE SESSOES
####################################################################################

sessoes_css_content = read_text_v2(SESSOES_CSS_PATH)

for start_marker, end_marker in [
    ("/* APPVERBO_SESSOES_SERVER_RENDER_IGUAL_ENTIDADE_V25_START */", "/* APPVERBO_SESSOES_SERVER_RENDER_IGUAL_ENTIDADE_V25_END */"),
    ("/* APPVERBO_SESSOES_CORRIGIR_ATIVOS_SPLIT_BACKEND_V26_START */", "/* APPVERBO_SESSOES_CORRIGIR_ATIVOS_SPLIT_BACKEND_V26_END */"),
    ("/* APPVERBO_SESSOES_REEXIBIR_CRIAR_AO_RETORNAR_V27_START */", "/* APPVERBO_SESSOES_REEXIBIR_CRIAR_AO_RETORNAR_V27_END */"),
    ("/* APPVERBO_SESSOES_REMOVER_DUPLICADOS_SERVER_RENDER_V28_START */", "/* APPVERBO_SESSOES_REMOVER_DUPLICADOS_SERVER_RENDER_V28_END */"),
    ("/* APPVERBO_SESSOES_CORRIGIR_V28_REMOVER_DUPLICADOS_V29_START */", "/* APPVERBO_SESSOES_CORRIGIR_V28_REMOVER_DUPLICADOS_V29_END */"),
    ("/* APPVERBO_SESSOES_FLUXO_NATIVO_IGUAL_ENTIDADE_V30_START */", "/* APPVERBO_SESSOES_FLUXO_NATIVO_IGUAL_ENTIDADE_V30_END */"),
]:
    sessoes_css_content = remove_marked_block_v2(sessoes_css_content, start_marker, end_marker)

write_text_v2(SESSOES_CSS_PATH, sessoes_css_content)


####################################################################################
# (11) ATUALIZAR AGENTS.md
####################################################################################

agents_path = resolve_agents_path_v2()
agents_content = read_text_v2(agents_path)

agents_rule = f"""{AGENTS_MARKER_START}
## Migração de Sessões para AdminSubprocessState

O subprocesso **Sessões** passa a usar o motor reutilizável `AdminSubprocess`.

Fluxo obrigatório:

1. `page_handler.py` monta `admin_subprocess_state` quando `admin_tab == "sessoes"`.
2. O estado usa:
   - `SESSOES_CONFIG`;
   - `build_admin_subprocess_state`;
   - linhas normalizadas de sessões ativas e inativas.
3. `templates/new_user.html` não deve manter blocos manuais de Sessões.
4. `templates/new_user.html` deve chamar apenas:
   - `render_admin_subprocess_state(admin_subprocess_state)`.
5. O macro `templates/macros/admin_subprocess.html` renderiza:
   - card Criar/Editar;
   - tabela de ativos;
   - tabela de inativos;
   - ações Visualizar/Editar/Subir/Descer.
6. JavaScript não pode recriar cards, tabelas ou formulários.
7. O JS genérico só pode tratar ação auxiliar de visualizar detalhes.
8. Os endpoints atuais de Sessões continuam válidos:
   - `/settings/menu/sidebar-section-save`;
   - `/settings/menu/sidebar-section-move-one`.
{AGENTS_MARKER_END}"""

agents_content = remove_marked_block_v2(agents_content, AGENTS_MARKER_START, AGENTS_MARKER_END)
agents_content = agents_content.rstrip() + "\n\n" + agents_rule + "\n"
write_text_v2(agents_path, agents_content)


####################################################################################
# (12) VALIDAR CONTEUDO
####################################################################################

models_validado = read_text_v2(MODELS_PATH)
registry_validado = read_text_v2(REGISTRY_PATH)
page_validado = read_text_v2(PAGE_HANDLER_PATH)
template_validado = read_text_v2(TEMPLATE_PATH)
macro_validado = read_text_v2(MACRO_PATH)
admin_css_validado = read_text_v2(ADMIN_CSS_PATH)
admin_js_validado = read_text_v2(ADMIN_JS_PATH)
sessoes_js_validado = read_text_v2(SESSOES_JS_PATH)
agents_validado = read_text_v2(agents_path)

validacoes = {
    "mode_field": models_validado,
    'mode_field="section_mode"': registry_validado,
    "admin_subprocess_state_v2": page_validado,
    '"admin_subprocess_state": admin_subprocess_state_v2': page_validado,
    "render_admin_subprocess_state(admin_subprocess_state)": template_validado,
    ADMIN_CSS_CACHE: template_validado,
    ADMIN_JS_CACHE: template_validado,
    "render_admin_subprocess_table": macro_validado,
    "render_admin_subprocess_row_actions": macro_validado,
    "admin-subprocess-table-v1": admin_css_validado,
    "APPVERBO_ADMIN_SUBPROCESSES_V1_START": admin_js_validado,
    "Desativado pelo AdminSubprocess V2": sessoes_js_validado,
    "APPVERBO_MIGRAR_SESSOES_ADMIN_SUBPROCESS_V2_START": agents_validado,
}

for termo, conteudo in validacoes.items():
    if termo not in conteudo:
        fail_v2(f"validação falhou, termo ausente: {termo}")

for section_id in [
    "admin-sidebar-sections-form-card",
    "admin-sidebar-sections-card",
    "admin-sidebar-sections-inactive-card",
]:
    count = len(re.findall(r'id=[\"\']' + re.escape(section_id) + r'[\"\']', template_validado))

    if count != 0:
        fail_v2(f"template ainda contém section manual #{section_id}: {count}")

for path, content in [
    (MODELS_PATH, models_validado),
    (REGISTRY_PATH, registry_validado),
    (SERVICE_PATH, read_text_v2(SERVICE_PATH)),
    (PAGE_HANDLER_PATH, page_validado),
]:
    try:
        ast.parse(content)
    except SyntaxError as exc:
        fail_v2(f"Python inválido em {path}: {exc}")

print("OK: patch_migrar_sessoes_admin_subprocess_v2 concluído.")

