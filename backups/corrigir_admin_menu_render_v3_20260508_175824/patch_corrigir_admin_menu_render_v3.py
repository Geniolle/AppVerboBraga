from pathlib import Path
import re

####################################################################################
# (1) CAMINHOS
####################################################################################

page_handler_path = Path("appverbo/routes/profile/page_handler.py")
template_path = Path("templates/new_user.html")

####################################################################################
# (2) AJUSTAR page_handler.py
####################################################################################

page_text = page_handler_path.read_text(encoding="utf-8")

# Aceitar admin_tab=menu na whitelist.
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

# Corrigir target inicial do Administrativo -> Menu.
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

page_text, count_target = admin_target_pattern.subn(
    admin_target_replacement,
    page_text,
    count=1,
)

if count_target != 1:
    raise RuntimeError("Não foi possível localizar/substituir o bloco de target do menu Administrativo.")

# Reforço para garantir que admin_tab=menu aponta para settings-card.
reinforcement_marker = "APPVERBO_ADMIN_MENU_TARGET_RENDER_V3_START"

if reinforcement_marker not in page_text:
    insertion_points = [
        "    # APPVERBO_ADMIN_SUBPROCESS_STATE_SESSOES_V2_START",
        "    # APPVERBO_ADMIN_SUBPROCESS_STATE_SESSOES_V1_START",
        "    template_context =",
        "    context =",
    ]

    insertion_point = ""

    for candidate in insertion_points:
        if candidate in page_text:
            insertion_point = candidate
            break

    if not insertion_point:
        raise RuntimeError("Não foi possível localizar ponto de inserção para reforço do target Menu.")

    reinforcement_block = '''
    # APPVERBO_ADMIN_MENU_TARGET_RENDER_V3_START
    if resolved_menu == "administrativo" and resolved_admin_tab == "menu":
        if clean_settings_edit_key:
            initial_menu_target = "#settings-menu-edit-card"
        else:
            initial_menu_target = "#settings-card"

        initial_dynamic_process_section = ""
        clean_dynamic_section_from_query = ""
    # APPVERBO_ADMIN_MENU_TARGET_RENDER_V3_END

'''

    page_text = page_text.replace(insertion_point, reinforcement_block + insertion_point, 1)

required_page_markers = [
    'resolved_admin_tab == "menu"',
    'return "#settings-card", ""',
    'APPVERBO_ADMIN_MENU_TARGET_RENDER_V3_START',
    'initial_menu_target = "#settings-card"',
]

for marker in required_page_markers:
    if marker not in page_text:
        raise RuntimeError(f"Validação falhou em page_handler.py. Marcador ausente: {marker}")

page_handler_path.write_text(page_text, encoding="utf-8")

####################################################################################
# (3) AJUSTAR templates/new_user.html
####################################################################################

template_text = template_path.read_text(encoding="utf-8")

block_start = "<!-- APPVERBO_ADMIN_MENU_RENDER_V3_START -->"
block_end = "<!-- APPVERBO_ADMIN_MENU_RENDER_V3_END -->"

# Remover versões antigas/parciais do bloco novo, se existirem.
template_text = re.sub(
    re.escape(block_start) + r".*?" + re.escape(block_end) + r"\n*",
    "",
    template_text,
    flags=re.DOTALL,
)

template_text = re.sub(
    r"<!-- APPVERBO_ADMIN_MENU_RENDER_V2_START -->.*?<!-- APPVERBO_ADMIN_MENU_RENDER_V2_END -->\n*",
    "",
    template_text,
    flags=re.DOTALL,
)

menu_block = '''
        <!-- APPVERBO_ADMIN_MENU_RENDER_V3_START -->
        {% if admin_tab == "menu" %}
        <section id="settings-card" class="card admin-menu-render-card-v3" data-menu-scope="administrativo">
          <div class="entity-create-toolbar">
            <a
              class="action-btn"
              href="/users/new?menu=administrativo&amp;admin_tab=menu&amp;settings_action=create&amp;target=settings-menu-edit-card#settings-menu-edit-card"
            >Criar menu</a>
          </div>
        </section>

        <section id="settings-card-active" class="card admin-menu-render-card-v3" data-menu-scope="administrativo">
          <div class="admin-menu-render-head-v3">
            <div>
              <h2>Menus ativos</h2>
              {% set active_counter = namespace(value=0) %}
              {% for menu_row in sidebar_menu_settings %}
                {% set raw_status = (menu_row.get("status_label") or menu_row.get("status") or "")|string|lower %}
                {% set row_is_inactive = raw_status in ["inativo", "inactive", "0", "false", "no", "nao", "não", "off"] or menu_row.get("is_active") is sameas false or menu_row.get("is_visible") is sameas false %}
                {% if not row_is_inactive %}
                  {% set active_counter.value = active_counter.value + 1 %}
                {% endif %}
              {% endfor %}
              <p><strong>Total: {{ active_counter.value }}</strong></p>
            </div>
            <input class="admin-menu-render-search-v3" type="search" placeholder="Procurar" aria-label="Procurar menu ativo">
          </div>

          <div class="admin-menu-render-table-wrap-v3">
            <table class="admin-menu-render-table-v3">
              <thead>
                <tr>
                  <th>NOME</th>
                  <th>SISTEMA</th>
                  <th>ESTADO</th>
                  <th class="admin-menu-render-actions-col-v3">AÇÕES</th>
                </tr>
              </thead>
              <tbody>
                {% set active_rows = namespace(found=False) %}
                {% for menu_row in sidebar_menu_settings %}
                  {% set raw_status = (menu_row.get("status_label") or menu_row.get("status") or "")|string|lower %}
                  {% set row_is_inactive = raw_status in ["inativo", "inactive", "0", "false", "no", "nao", "não", "off"] or menu_row.get("is_active") is sameas false or menu_row.get("is_visible") is sameas false %}
                  {% if not row_is_inactive %}
                    {% set active_rows.found = True %}
                    {% set row_key = menu_row.get("key") or menu_row.get("menu_key") or "" %}
                    {% set row_label = menu_row.get("label") or menu_row.get("menu_label") or menu_row.get("name") or row_key %}
                    {% set row_scope = menu_row.get("visibility_scope_label") or menu_row.get("system_label") or menu_row.get("scope_label") or "Owner e Legado" %}
                    <tr>
                      <td>{{ row_label }}</td>
                      <td>{{ row_scope }}</td>
                      <td><span class="admin-menu-render-badge-active-v3">Ativo</span></td>
                      <td>
                        <div class="admin-menu-render-actions-v3">
                          <form method="post" action="/settings/menu/move" class="admin-menu-render-inline-form-v3">
                            <input type="hidden" name="menu_key" value="{{ row_key }}">
                            <input type="hidden" name="direction" value="up">
                            <input type="hidden" name="return_url" value="/users/new?menu=administrativo&amp;admin_tab=menu">
                            <button type="submit" class="admin-menu-render-action-btn-v3" title="Subir" aria-label="Subir">↑</button>
                          </form>
                          <form method="post" action="/settings/menu/move" class="admin-menu-render-inline-form-v3">
                            <input type="hidden" name="menu_key" value="{{ row_key }}">
                            <input type="hidden" name="direction" value="down">
                            <input type="hidden" name="return_url" value="/users/new?menu=administrativo&amp;admin_tab=menu">
                            <button type="submit" class="admin-menu-render-action-btn-v3" title="Descer" aria-label="Descer">↓</button>
                          </form>
                          <button
                            type="button"
                            class="admin-menu-render-action-btn-v3"
                            title="Visualizar"
                            aria-label="Visualizar"
                            data-menu-view-label="{{ row_label }}"
                            data-menu-view-scope="{{ row_scope }}"
                            data-menu-view-status="Ativo"
                          >Ver</button>
                          <a
                            class="admin-menu-render-action-btn-v3 admin-menu-render-action-link-v3"
                            title="Editar"
                            aria-label="Editar"
                            href="/users/new?menu=administrativo&amp;admin_tab=menu&amp;settings_edit_key={{ row_key }}&amp;settings_action=edit&amp;settings_tab=geral&amp;target=settings-menu-edit-card#settings-menu-edit-card"
                          >Editar</a>
                        </div>
                      </td>
                    </tr>
                  {% endif %}
                {% endfor %}
                {% if not active_rows.found %}
                  <tr>
                    <td colspan="4">Sem registos.</td>
                  </tr>
                {% endif %}
              </tbody>
            </table>
          </div>
        </section>

        <section id="settings-card-inactive" class="card admin-menu-render-card-v3" data-menu-scope="administrativo">
          <h2>Menus inativos</h2>

          <div class="admin-menu-render-table-wrap-v3">
            <table class="admin-menu-render-table-v3">
              <thead>
                <tr>
                  <th>NOME</th>
                  <th>SISTEMA</th>
                  <th>ESTADO</th>
                  <th class="admin-menu-render-actions-col-v3">AÇÕES</th>
                </tr>
              </thead>
              <tbody>
                {% set inactive_rows = namespace(found=False) %}
                {% for menu_row in sidebar_menu_settings %}
                  {% set raw_status = (menu_row.get("status_label") or menu_row.get("status") or "")|string|lower %}
                  {% set row_is_inactive = raw_status in ["inativo", "inactive", "0", "false", "no", "nao", "não", "off"] or menu_row.get("is_active") is sameas false or menu_row.get("is_visible") is sameas false %}
                  {% if row_is_inactive %}
                    {% set inactive_rows.found = True %}
                    {% set row_key = menu_row.get("key") or menu_row.get("menu_key") or "" %}
                    {% set row_label = menu_row.get("label") or menu_row.get("menu_label") or menu_row.get("name") or row_key %}
                    {% set row_scope = menu_row.get("visibility_scope_label") or menu_row.get("system_label") or menu_row.get("scope_label") or "Owner e Legado" %}
                    <tr>
                      <td>{{ row_label }}</td>
                      <td>{{ row_scope }}</td>
                      <td><span class="admin-menu-render-badge-inactive-v3">Inativo</span></td>
                      <td>
                        <div class="admin-menu-render-actions-v3">
                          <button
                            type="button"
                            class="admin-menu-render-action-btn-v3"
                            title="Visualizar"
                            aria-label="Visualizar"
                            data-menu-view-label="{{ row_label }}"
                            data-menu-view-scope="{{ row_scope }}"
                            data-menu-view-status="Inativo"
                          >Ver</button>
                          <a
                            class="admin-menu-render-action-btn-v3 admin-menu-render-action-link-v3"
                            title="Editar"
                            aria-label="Editar"
                            href="/users/new?menu=administrativo&amp;admin_tab=menu&amp;settings_edit_key={{ row_key }}&amp;settings_action=edit&amp;settings_tab=geral&amp;target=settings-menu-edit-card#settings-menu-edit-card"
                          >Editar</a>
                        </div>
                      </td>
                    </tr>
                  {% endif %}
                {% endfor %}
                {% if not inactive_rows.found %}
                  <tr>
                    <td colspan="4">Sem registos.</td>
                  </tr>
                {% endif %}
              </tbody>
            </table>
          </div>
        </section>
        {% endif %}
        <!-- APPVERBO_ADMIN_MENU_RENDER_V3_END -->
'''

####################################################################################
# (4) LOCALIZAR PONTO DE INSERÇÃO DO BLOCO NO TEMPLATE
####################################################################################

insert_markers = [
    "<!-- APPVERBO_CORRIGIR_ORDEM_ABAS_SESSOES_ADMIN_SUBPROCESS_V5_END -->",
    "<!-- APPVERBO_CORRIGIR_ORDEM_ABAS_SESSOES_ADMIN_SUBPROCESS_V4_END -->",
    "<!-- APPVERBO_CORRIGIR_ORDEM_ABAS_SESSOES_ADMIN_SUBPROCESS_V3_END -->",
    "<!-- APPVERBO_ADMIN_SUBPROCESS_SESSOES_RENDER_END -->",
]

inserted = False

for marker in insert_markers:
    if marker in template_text:
        template_text = template_text.replace(marker, marker + "\n" + menu_block, 1)
        inserted = True
        break

if not inserted:
    # Inserir antes do card do perfil, pois o Menu pertence à área administrativa antes do conteúdo de perfil.
    fallback_markers = [
        '<section id="perfil-pessoal-card"',
        '<div id="perfil-pessoal-card"',
        'id="perfil-pessoal-card"',
    ]

    for marker in fallback_markers:
        index = template_text.find(marker)

        if index >= 0:
            line_start = template_text.rfind("\n", 0, index)
            insert_at = line_start + 1 if line_start >= 0 else index
            template_text = template_text[:insert_at] + menu_block + "\n" + template_text[insert_at:]
            inserted = True
            break

if not inserted:
    # Último recurso: inserir antes do fim do bloco content.
    marker = "{% endblock %}"
    last_index = template_text.rfind(marker)

    if last_index < 0:
        raise RuntimeError("Não foi possível localizar ponto para inserir o bloco Administrativo -> Menu.")

    template_text = template_text[:last_index] + menu_block + "\n" + template_text[last_index:]

####################################################################################
# (5) INSERIR CSS E JS AUXILIAR NO head_extra
####################################################################################

style_marker = "APPVERBO_ADMIN_MENU_RENDER_STYLE_V3_START"

if style_marker not in template_text:
    style_block = '''
<style>
/* APPVERBO_ADMIN_MENU_RENDER_STYLE_V3_START */
.admin-menu-render-card-v3 { margin-top: 16px; }
.admin-menu-render-head-v3 { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; }
.admin-menu-render-search-v3 { min-width: 240px; max-width: 320px; padding: 8px 12px; border: 1px solid #bfcee6; border-radius: 999px; }
.admin-menu-render-table-wrap-v3 { overflow-x: auto; }
.admin-menu-render-table-v3 { width: 100%; border-collapse: collapse; }
.admin-menu-render-table-v3 th, .admin-menu-render-table-v3 td { padding: 12px 10px; border-bottom: 1px solid #d7e0ef; text-align: left; }
.admin-menu-render-table-v3 th { font-size: 12px; font-weight: 800; color: #0f172a; }
.admin-menu-render-actions-col-v3 { text-align: right !important; width: 240px; }
.admin-menu-render-actions-v3 { display: flex; justify-content: flex-end; align-items: center; gap: 6px; }
.admin-menu-render-inline-form-v3 { margin: 0; display: inline-flex; }
.admin-menu-render-action-btn-v3 { display: inline-flex; align-items: center; justify-content: center; min-width: 30px; height: 28px; padding: 0 8px; border: 1px solid #9fc1ff; border-radius: 6px; background: #eef5ff; color: #0f4fb8; font-weight: 700; font-size: 12px; text-decoration: none; cursor: pointer; }
.admin-menu-render-action-link-v3 { color: #0f4fb8; }
.admin-menu-render-badge-active-v3 { display: inline-flex; align-items: center; padding: 2px 9px; border-radius: 999px; border: 1px solid #9ad7b8; background: #e7f8ef; color: #08753f; font-weight: 800; font-size: 12px; }
.admin-menu-render-badge-inactive-v3 { display: inline-flex; align-items: center; padding: 2px 9px; border-radius: 999px; border: 1px solid #fecaca; background: #fef2f2; color: #b91c1c; font-weight: 800; font-size: 12px; }
/* APPVERBO_ADMIN_MENU_RENDER_STYLE_V3_END */
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

    head_start = template_text.find("{% block head_extra %}")

    if head_start >= 0:
        head_end = template_text.find("{% endblock %}", head_start)

        if head_end < 0:
            raise RuntimeError("Fim do bloco head_extra não encontrado.")

        template_text = template_text[:head_end] + style_block + "\n" + template_text[head_end:]
    elif "</head>" in template_text:
        template_text = template_text.replace("</head>", style_block + "\n</head>", 1)
    else:
        # Se o template não tiver head, deixa o CSS junto do bloco renderizado.
        template_text = template_text.replace(block_start, style_block + "\n" + block_start, 1)

####################################################################################
# (6) VALIDAR E GRAVAR TEMPLATE
####################################################################################

required_template_markers = [
    "APPVERBO_ADMIN_MENU_RENDER_V3_START",
    'id="settings-card"',
    "Criar menu",
    "Menus ativos",
    "Menus inativos",
    "sidebar_menu_settings",
    "APPVERBO_ADMIN_MENU_RENDER_STYLE_V3_START",
]

for marker in required_template_markers:
    if marker not in template_text:
        raise RuntimeError(f"Validação falhou em new_user.html. Marcador ausente: {marker}")

template_path.write_text(template_text, encoding="utf-8")

print("OK: patch V3 aplicado para Administrativo -> Menu.")
