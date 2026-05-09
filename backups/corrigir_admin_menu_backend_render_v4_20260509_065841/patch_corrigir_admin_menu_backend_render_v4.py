from pathlib import Path
import re

####################################################################################
# (1) CAMINHOS
####################################################################################

page_handler_path = Path("appverbo/routes/profile/page_handler.py")
template_path = Path("templates/new_user.html")
legacy_js_path = Path("static/js/modules/admin_menu_tab_renderer_v1.js")

####################################################################################
# (2) CORRIGIR page_handler.py PARA ACEITAR admin_tab=menu
####################################################################################

page_text = page_handler_path.read_text(encoding="utf-8")

page_text = re.sub(
    r'if resolved_admin_tab not in \{([^}]*)\}:',
    lambda match: (
        match.group(0)
        if '"menu"' in match.group(1) or "'menu'" in match.group(1)
        else f'if resolved_admin_tab not in {{{match.group(1).rstrip()}, "menu"}}:'
    ),
    page_text,
    count=1,
)

admin_target_pattern = re.compile(
    r'    if clean_menu_key == "administrativo":\n'
    r'.*?'
    r'    if clean_menu_key == "configuracao":',
    flags=re.DOTALL,
)

admin_target_replacement = '''    if clean_menu_key == "administrativo":
        if settings_edit_key:
            return "#settings-menu-edit-card", ""
        if resolved_admin_tab == "menu":
            return "#settings-card", ""
        if resolved_admin_tab == "sessoes":
            return "#admin-sidebar-sections-card", ""
        if resolved_admin_tab == "contas":
            return "#admin-account-status-card", ""
        if resolved_admin_tab == "utilizador":
            return "#create-user-card", ""
        return "#create-entity-card", ""
    if clean_menu_key == "configuracao":'''

page_text, target_count = admin_target_pattern.subn(
    admin_target_replacement,
    page_text,
    count=1,
)

if target_count != 1:
    raise RuntimeError("Não foi possível localizar/substituir o bloco de target do menu Administrativo.")

reinforcement_marker = "APPVERBO_ADMIN_MENU_BACKEND_RENDER_V4_START"

if reinforcement_marker not in page_text:
    insertion_candidates = [
        "    # APPVERBO_ADMIN_SUBPROCESS_STATE_SESSOES_V2_START",
        "    # APPVERBO_ADMIN_SUBPROCESS_STATE_SESSOES_V1_START",
        "    template_context =",
        "    context =",
    ]

    insertion_point = ""

    for candidate in insertion_candidates:
        if candidate in page_text:
            insertion_point = candidate
            break

    if not insertion_point:
        raise RuntimeError("Ponto de inserção do reforço Administrativo -> Menu não encontrado.")

    reinforcement_block = '''
    # APPVERBO_ADMIN_MENU_BACKEND_RENDER_V4_START
    if resolved_menu == "administrativo" and resolved_admin_tab == "menu":
        if clean_settings_edit_key:
            initial_menu_target = "#settings-menu-edit-card"
        else:
            initial_menu_target = "#settings-card"

        initial_dynamic_process_section = ""
        clean_dynamic_section_from_query = ""
    # APPVERBO_ADMIN_MENU_BACKEND_RENDER_V4_END

'''

    page_text = page_text.replace(insertion_point, reinforcement_block + insertion_point, 1)

required_page_markers = [
    'resolved_admin_tab == "menu"',
    'return "#settings-card", ""',
    "APPVERBO_ADMIN_MENU_BACKEND_RENDER_V4_START",
    'initial_menu_target = "#settings-card"',
]

for marker in required_page_markers:
    if marker not in page_text:
        raise RuntimeError(f"Validação falhou em page_handler.py. Marcador ausente: {marker}")

page_handler_path.write_text(page_text, encoding="utf-8")

####################################################################################
# (3) CORRIGIR templates/new_user.html
####################################################################################

template_text = template_path.read_text(encoding="utf-8")

####################################################################################
# (3.1) REMOVER JS AGRESSIVO E BLOCOS ANTIGOS
####################################################################################

script_patterns = [
    r'\s*<script\s+src="/static/js/modules/admin_menu_tab_renderer_v1\.js\?v=[^"]*"\s+defer></script>\s*',
]

for pattern in script_patterns:
    template_text = re.sub(pattern, "\n", template_text)

old_block_patterns = [
    r"<!-- APPVERBO_ADMIN_MENU_RENDER_V2_START -->.*?<!-- APPVERBO_ADMIN_MENU_RENDER_V2_END -->\n*",
    r"<!-- APPVERBO_ADMIN_MENU_RENDER_V3_START -->.*?<!-- APPVERBO_ADMIN_MENU_RENDER_V3_END -->\n*",
    r"<!-- APPVERBO_ADMIN_MENU_RENDER_V4_START -->.*?<!-- APPVERBO_ADMIN_MENU_RENDER_V4_END -->\n*",
]

for pattern in old_block_patterns:
    template_text = re.sub(pattern, "", template_text, flags=re.DOTALL)

old_style_patterns = [
    r"<style>\s*/\* APPVERBO_ADMIN_MENU_RENDER_STYLE_V2_START \*/.*?APPVERBO_ADMIN_MENU_RENDER_STYLE_V2_END \*/\s*</style>\n*",
    r"<style>\s*/\* APPVERBO_ADMIN_MENU_RENDER_STYLE_V3_START \*/.*?APPVERBO_ADMIN_MENU_RENDER_STYLE_V3_END \*/\s*</style>\n*",
    r"<style>\s*/\* APPVERBO_ADMIN_MENU_BACKEND_RENDER_STYLE_V4_START \*/.*?APPVERBO_ADMIN_MENU_BACKEND_RENDER_STYLE_V4_END \*/\s*</style>\n*",
]

for pattern in old_style_patterns:
    template_text = re.sub(pattern, "", template_text, flags=re.DOTALL)

####################################################################################
# (3.2) CRIAR BLOCO SERVER-SIDE DO ADMINISTRATIVO -> MENU
####################################################################################

menu_block = '''
        <!-- APPVERBO_ADMIN_MENU_RENDER_V4_START -->
        {% if admin_tab == "menu" %}
        <section id="settings-card" class="card admin-menu-backend-card-v4" data-admin-tab-content="menu">
          <div class="entity-create-toolbar">
            <a
              class="action-btn"
              href="/users/new?menu=administrativo&amp;admin_tab=menu&amp;settings_action=create&amp;target=settings-menu-edit-card#settings-menu-edit-card"
            >Criar menu</a>
          </div>
        </section>

        <section id="settings-card-active" class="card admin-menu-backend-card-v4" data-admin-tab-content="menu">
          <div class="admin-menu-backend-head-v4">
            <div>
              <h2>Menus ativos</h2>
              {% set menu_rows_v4 = sidebar_menu_settings if sidebar_menu_settings is defined else [] %}
              {% set active_counter_v4 = namespace(value=0) %}
              {% for menu_row in menu_rows_v4 %}
                {% set raw_status_v4 = (menu_row.get("status_label") or menu_row.get("status") or "")|string|lower %}
                {% set row_is_inactive_v4 = raw_status_v4 in ["inativo", "inactive", "0", "false", "no", "nao", "não", "off"] or menu_row.get("is_active") is sameas false or menu_row.get("is_visible") is sameas false %}
                {% if not row_is_inactive_v4 %}
                  {% set active_counter_v4.value = active_counter_v4.value + 1 %}
                {% endif %}
              {% endfor %}
              <p><strong>Total: {{ active_counter_v4.value }}</strong></p>
            </div>
            <input class="admin-menu-backend-search-v4" type="search" placeholder="Procurar" aria-label="Procurar menu ativo">
          </div>

          <div class="admin-menu-backend-table-wrap-v4">
            <table class="admin-menu-backend-table-v4">
              <thead>
                <tr>
                  <th>NOME</th>
                  <th>SISTEMA</th>
                  <th>ESTADO</th>
                  <th class="admin-menu-backend-actions-col-v4">AÇÕES</th>
                </tr>
              </thead>
              <tbody>
                {% set active_rows_v4 = namespace(found=False) %}
                {% for menu_row in menu_rows_v4 %}
                  {% set raw_status_v4 = (menu_row.get("status_label") or menu_row.get("status") or "")|string|lower %}
                  {% set row_is_inactive_v4 = raw_status_v4 in ["inativo", "inactive", "0", "false", "no", "nao", "não", "off"] or menu_row.get("is_active") is sameas false or menu_row.get("is_visible") is sameas false %}
                  {% if not row_is_inactive_v4 %}
                    {% set active_rows_v4.found = True %}
                    {% set row_key_v4 = menu_row.get("key") or menu_row.get("menu_key") or "" %}
                    {% set row_label_v4 = menu_row.get("label") or menu_row.get("menu_label") or menu_row.get("name") or row_key_v4 %}
                    {% set row_scope_v4 = menu_row.get("visibility_scope_label") or menu_row.get("system_label") or menu_row.get("scope_label") or menu_row.get("visibility_scope") or "Owner e Legado" %}
                    <tr>
                      <td>{{ row_label_v4 }}</td>
                      <td>{{ row_scope_v4 }}</td>
                      <td><span class="admin-menu-backend-badge-active-v4">Ativo</span></td>
                      <td>
                        <div class="admin-menu-backend-actions-v4">
                          <button type="button" class="admin-menu-backend-action-btn-v4" title="Subir" aria-label="Subir">↑</button>
                          <button type="button" class="admin-menu-backend-action-btn-v4" title="Descer" aria-label="Descer">↓</button>
                          <button
                            type="button"
                            class="admin-menu-backend-action-btn-v4"
                            title="Visualizar"
                            aria-label="Visualizar"
                            data-menu-view-label="{{ row_label_v4 }}"
                            data-menu-view-scope="{{ row_scope_v4 }}"
                            data-menu-view-status="Ativo"
                          >Ver</button>
                          <a
                            class="admin-menu-backend-action-btn-v4 admin-menu-backend-action-link-v4"
                            title="Editar"
                            aria-label="Editar"
                            href="/users/new?menu=administrativo&amp;admin_tab=menu&amp;settings_edit_key={{ row_key_v4 }}&amp;settings_action=edit&amp;settings_tab=geral&amp;target=settings-menu-edit-card#settings-menu-edit-card"
                          >Editar</a>
                        </div>
                      </td>
                    </tr>
                  {% endif %}
                {% endfor %}
                {% if not active_rows_v4.found %}
                  <tr>
                    <td colspan="4">Sem registos.</td>
                  </tr>
                {% endif %}
              </tbody>
            </table>
          </div>
        </section>

        <section id="settings-card-inactive" class="card admin-menu-backend-card-v4" data-admin-tab-content="menu">
          <h2>Menus inativos</h2>

          <div class="admin-menu-backend-table-wrap-v4">
            <table class="admin-menu-backend-table-v4">
              <thead>
                <tr>
                  <th>NOME</th>
                  <th>SISTEMA</th>
                  <th>ESTADO</th>
                  <th class="admin-menu-backend-actions-col-v4">AÇÕES</th>
                </tr>
              </thead>
              <tbody>
                {% set inactive_rows_v4 = namespace(found=False) %}
                {% for menu_row in menu_rows_v4 %}
                  {% set raw_status_v4 = (menu_row.get("status_label") or menu_row.get("status") or "")|string|lower %}
                  {% set row_is_inactive_v4 = raw_status_v4 in ["inativo", "inactive", "0", "false", "no", "nao", "não", "off"] or menu_row.get("is_active") is sameas false or menu_row.get("is_visible") is sameas false %}
                  {% if row_is_inactive_v4 %}
                    {% set inactive_rows_v4.found = True %}
                    {% set row_key_v4 = menu_row.get("key") or menu_row.get("menu_key") or "" %}
                    {% set row_label_v4 = menu_row.get("label") or menu_row.get("menu_label") or menu_row.get("name") or row_key_v4 %}
                    {% set row_scope_v4 = menu_row.get("visibility_scope_label") or menu_row.get("system_label") or menu_row.get("scope_label") or menu_row.get("visibility_scope") or "Owner e Legado" %}
                    <tr>
                      <td>{{ row_label_v4 }}</td>
                      <td>{{ row_scope_v4 }}</td>
                      <td><span class="admin-menu-backend-badge-inactive-v4">Inativo</span></td>
                      <td>
                        <div class="admin-menu-backend-actions-v4">
                          <button
                            type="button"
                            class="admin-menu-backend-action-btn-v4"
                            title="Visualizar"
                            aria-label="Visualizar"
                            data-menu-view-label="{{ row_label_v4 }}"
                            data-menu-view-scope="{{ row_scope_v4 }}"
                            data-menu-view-status="Inativo"
                          >Ver</button>
                          <a
                            class="admin-menu-backend-action-btn-v4 admin-menu-backend-action-link-v4"
                            title="Editar"
                            aria-label="Editar"
                            href="/users/new?menu=administrativo&amp;admin_tab=menu&amp;settings_edit_key={{ row_key_v4 }}&amp;settings_action=edit&amp;settings_tab=geral&amp;target=settings-menu-edit-card#settings-menu-edit-card"
                          >Editar</a>
                        </div>
                      </td>
                    </tr>
                  {% endif %}
                {% endfor %}
                {% if not inactive_rows_v4.found %}
                  <tr>
                    <td colspan="4">Sem registos.</td>
                  </tr>
                {% endif %}
              </tbody>
            </table>
          </div>
        </section>
        {% endif %}
        <!-- APPVERBO_ADMIN_MENU_RENDER_V4_END -->
'''

####################################################################################
# (3.3) INSERIR BLOCO ANTES DOS CARDS DE ENTIDADE/PERFIL
####################################################################################

inserted = False

insert_markers = [
    "<!-- APPVERBO_CORRIGIR_ORDEM_ABAS_SESSOES_ADMIN_SUBPROCESS_V5_END -->",
    "<!-- APPVERBO_CORRIGIR_ORDEM_ABAS_SESSOES_ADMIN_SUBPROCESS_V4_END -->",
    "<!-- APPVERBO_CORRIGIR_ORDEM_ABAS_SESSOES_ADMIN_SUBPROCESS_V3_END -->",
    '<section id="create-entity-card"',
    '<section id="perfil-pessoal-card"',
    '<div id="perfil-pessoal-card"',
    'id="perfil-pessoal-card"',
]

for marker in insert_markers:
    index = template_text.find(marker)

    if index < 0:
        continue

    if marker.startswith("<!--"):
        template_text = template_text.replace(marker, marker + "\n" + menu_block, 1)
    else:
        line_start = template_text.rfind("\n", 0, index)
        insert_at = line_start + 1 if line_start >= 0 else index
        template_text = template_text[:insert_at] + menu_block + "\n" + template_text[insert_at:]

    inserted = True
    break

if not inserted:
    last_endblock = template_text.rfind("{% endblock %}")

    if last_endblock < 0:
        raise RuntimeError("Não foi possível localizar ponto de inserção no template.")

    template_text = template_text[:last_endblock] + menu_block + "\n" + template_text[last_endblock:]

####################################################################################
# (3.4) INSERIR CSS/JS AUXILIAR NÃO AGRESSIVO
####################################################################################

style_block = '''
<style>
/* APPVERBO_ADMIN_MENU_BACKEND_RENDER_STYLE_V4_START */
{% if admin_tab == "menu" %}
#create-entity-card,
#entities-card,
#inactive-entities-card,
#create-user-card,
#users-card,
#inactive-users-card,
#admin-sidebar-sections-card,
#admin-account-status-card {
  display: none !important;
}
{% endif %}

.admin-menu-backend-card-v4 { margin-top: 16px; }
.admin-menu-backend-head-v4 { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; }
.admin-menu-backend-search-v4 { min-width: 240px; max-width: 320px; padding: 8px 12px; border: 1px solid #bfcee6; border-radius: 999px; }
.admin-menu-backend-table-wrap-v4 { overflow-x: auto; }
.admin-menu-backend-table-v4 { width: 100%; border-collapse: collapse; }
.admin-menu-backend-table-v4 th, .admin-menu-backend-table-v4 td { padding: 12px 10px; border-bottom: 1px solid #d7e0ef; text-align: left; }
.admin-menu-backend-table-v4 th { font-size: 12px; font-weight: 800; color: #0f172a; }
.admin-menu-backend-actions-col-v4 { text-align: right !important; width: 240px; }
.admin-menu-backend-actions-v4 { display: flex; justify-content: flex-end; align-items: center; gap: 6px; }
.admin-menu-backend-action-btn-v4 { display: inline-flex; align-items: center; justify-content: center; min-width: 30px; height: 28px; padding: 0 8px; border: 1px solid #9fc1ff; border-radius: 6px; background: #eef5ff; color: #0f4fb8; font-weight: 700; font-size: 12px; text-decoration: none; cursor: pointer; }
.admin-menu-backend-action-link-v4 { color: #0f4fb8; }
.admin-menu-backend-badge-active-v4 { display: inline-flex; align-items: center; padding: 2px 9px; border-radius: 999px; border: 1px solid #9ad7b8; background: #e7f8ef; color: #08753f; font-weight: 800; font-size: 12px; }
.admin-menu-backend-badge-inactive-v4 { display: inline-flex; align-items: center; padding: 2px 9px; border-radius: 999px; border: 1px solid #fecaca; background: #fef2f2; color: #b91c1c; font-weight: 800; font-size: 12px; }
/* APPVERBO_ADMIN_MENU_BACKEND_RENDER_STYLE_V4_END */
</style>
<script>
(function () {
  "use strict";

  document.addEventListener("click", function (event) {
    var button = event.target && event.target.closest
      ? event.target.closest("[data-menu-view-label]")
      : null;

    if (!button) {
      return;
    }

    alert(
      "Menu: " + (button.getAttribute("data-menu-view-label") || "") + "\\n" +
      "Sistema: " + (button.getAttribute("data-menu-view-scope") || "") + "\\n" +
      "Estado: " + (button.getAttribute("data-menu-view-status") || "")
    );
  }, true);
})();
</script>
'''

if "APPVERBO_ADMIN_MENU_BACKEND_RENDER_STYLE_V4_START" not in template_text:
    head_start = template_text.find("{% block head_extra %}")

    if head_start >= 0:
        head_end = template_text.find("{% endblock %}", head_start)

        if head_end < 0:
            raise RuntimeError("Fim do bloco head_extra não encontrado.")

        template_text = template_text[:head_end] + style_block + "\n" + template_text[head_end:]
    elif "</head>" in template_text:
        template_text = template_text.replace("</head>", style_block + "\n</head>", 1)
    else:
        template_text = template_text.replace(
            "<!-- APPVERBO_ADMIN_MENU_RENDER_V4_START -->",
            style_block + "\n<!-- APPVERBO_ADMIN_MENU_RENDER_V4_START -->",
            1,
        )

####################################################################################
# (3.5) VALIDAR E GRAVAR TEMPLATE
####################################################################################

required_template_markers = [
    "APPVERBO_ADMIN_MENU_RENDER_V4_START",
    "APPVERBO_ADMIN_MENU_RENDER_V4_END",
    "APPVERBO_ADMIN_MENU_BACKEND_RENDER_STYLE_V4_START",
    'id="settings-card"',
    "Criar menu",
    "Menus ativos",
    "Menus inativos",
    "sidebar_menu_settings",
]

for marker in required_template_markers:
    if marker not in template_text:
        raise RuntimeError(f"Validação falhou em new_user.html. Marcador ausente: {marker}")

template_path.write_text(template_text, encoding="utf-8")

####################################################################################
# (4) NEUTRALIZAR JS AGRESSIVO ANTIGO
####################################################################################

legacy_js_path.parent.mkdir(parents=True, exist_ok=True)
legacy_js_path.write_text(
    """// APPVERBO_ADMIN_MENU_TAB_RENDERER_V1_DISABLED_BY_BACKEND_RENDER_V4
(function () {
  "use strict";
  // Desativado: a renderização do Administrativo -> Menu agora é server-side.
})();
""",
    encoding="utf-8",
)

print("OK: Administrativo -> Menu corrigido por backend/template.")
