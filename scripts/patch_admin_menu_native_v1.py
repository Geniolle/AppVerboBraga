# -*- coding: utf-8 -*-
from __future__ import annotations

import re
import sys
from pathlib import Path


PAGE_HANDLER = Path("appverbo/routes/profile/page_handler.py")
TEMPLATE = Path("templates/new_user.html")
CSS = Path("static/css/new_user.css")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: Path, content: str) -> None:
    path.write_text(content.rstrip() + "\n", encoding="utf-8", newline="\n")


def patch_page_handler() -> None:
    text = read(PAGE_HANDLER)
    original = text

    # APPVERBO_ADMIN_MENU_NATIVE_BACKEND_V1: aceitar admin_tab=menu
    pattern = r'if resolved_admin_tab not in \{([^}]+)\}:'
    match = re.search(pattern, text, flags=re.DOTALL)

    if not match:
        raise RuntimeError("Nao foi possivel localizar a validacao de resolved_admin_tab.")

    allowed_body = match.group(1)

    if '"menu"' not in allowed_body and "'menu'" not in allowed_body:
        new_allowed_body = allowed_body.rstrip() + ', "menu"'
        text = text[:match.start(1)] + new_allowed_body + text[match.end(1):]

    # APPVERBO_ADMIN_MENU_NATIVE_TARGET_RESOLVE_V1
    if "APPVERBO_ADMIN_MENU_NATIVE_TARGET_RESOLVE_V1_START" not in text:
        anchor = '''        if resolved_admin_tab == "contas":
            return "#admin-account-status-card", ""'''

        insert = '''        # APPVERBO_ADMIN_MENU_NATIVE_TARGET_RESOLVE_V1_START
        if resolved_admin_tab == "menu":
            return "#settings-card", ""
        # APPVERBO_ADMIN_MENU_NATIVE_TARGET_RESOLVE_V1_END
'''

        if anchor not in text:
            raise RuntimeError("Nao foi possivel localizar o bloco de target do Administrativo.")

        text = text.replace(anchor, insert + anchor, 1)

    # APPVERBO_ADMIN_MENU_NATIVE_POST_CONTEXT_V1
    if "APPVERBO_ADMIN_MENU_NATIVE_POST_CONTEXT_V1_START" not in text:
        anchor = '''    if resolved_admin_tab == "sessoes":
        if str(sidebar_section_edit_key or "").strip():
            initial_menu_target = "#admin-sidebar-sections-form-card"
        else:
            initial_menu_target = "#admin-sidebar-sections-card"
        initial_dynamic_process_section = ""
        clean_dynamic_section_from_query = ""'''

        insert = '''    # APPVERBO_ADMIN_MENU_NATIVE_POST_CONTEXT_V1_START
    if resolved_admin_tab == "menu":
        initial_menu_target = "#settings-card"
        initial_dynamic_process_section = ""
        clean_dynamic_section_from_query = ""
    # APPVERBO_ADMIN_MENU_NATIVE_POST_CONTEXT_V1_END

'''

        if anchor not in text:
            raise RuntimeError("Nao foi possivel localizar o bloco de contexto de sessoes.")

        text = text.replace(anchor, insert + anchor, 1)

    if text != original:
        write(PAGE_HANDLER, text)


def patch_template() -> None:
    text = read(TEMPLATE)
    original = text

    # Remove guard visual antigo do Menu, porque agora o Menu passa a ter card nativo.
    text = re.sub(
        r'\s*<script src="/static/js/modules/appverbo_menu_render_guard_v1\.js[^"]*" defer></script>',
        "",
        text,
    )
    text = re.sub(
        r'\s*<script src="/static/js/modules/appverbo_menu_render_guard_v1\.js[^"]*"></script>',
        "",
        text,
    )

    card = r'''
        <!-- APPVERBO_ADMIN_MENU_NATIVE_CARD_V1_START -->
        {% if current_user_is_admin %}
        <section
          id="settings-card"
          class="card appverbo-admin-native-card appverbo-admin-menu-card-v1"
          data-menu-scope="administrativo"
          data-admin-subprocess="menu"
          style="{% if admin_tab == 'menu' %}display: block;{% else %}display: none;{% endif %}"
        >
          <div class="profile-card-header">
            <div>
              <h2>Menu</h2>
              <p class="appverbo-admin-menu-subtitle-v1">Configuração dos processos visíveis no menu lateral.</p>
            </div>
          </div>

          {% if admin_tab == "menu" and settings_success %}
            <div class="alert ok">{{ settings_success }}</div>
          {% endif %}
          {% if admin_tab == "menu" and settings_error %}
            <div class="alert error">{{ settings_error }}</div>
          {% endif %}

          {% set menu_rows = sidebar_menu_settings if sidebar_menu_settings is defined else [] %}

          {% if menu_rows %}
          <div class="admin-subsection appverbo-admin-menu-list-v1">
            <table class="admin-subprocess-table-v1 appverbo-admin-menu-table-v1">
              <thead>
                <tr>
                  <th>Processo</th>
                  <th>Chave</th>
                  <th>Visível</th>
                  <th>Campos</th>
                  <th>Ações</th>
                </tr>
              </thead>
              <tbody>
                {% for row in menu_rows %}
                  {% set row_key = row.get('key', '') %}
                  {% set row_label = row.get('label', row_key) %}
                  {% set row_visible = row.get('visible', row.get('is_visible', True)) %}
                  {% set field_rows = row.get('process_visible_field_rows', []) %}
                  <tr>
                    <td>
                      <strong>{{ row_label }}</strong>
                    </td>
                    <td>{{ row_key }}</td>
                    <td>
                      {% if row_visible %}
                        <span class="status-pill active">Ativo</span>
                      {% else %}
                        <span class="status-pill inactive">Inativo</span>
                      {% endif %}
                    </td>
                    <td>{{ field_rows|length }}</td>
                    <td>
                      <div class="admin-subprocess-row-actions-v1">
                        <a
                          class="admin-subprocess-action-link-v1"
                          href="/users/new?menu=administrativo&admin_tab=menu&settings_tab=menu&settings_action=edit&settings_edit_key={{ row_key }}&target=settings-menu-edit-card#settings-menu-edit-card"
                          title="Editar"
                        >✎</a>
                      </div>
                    </td>
                  </tr>
                {% endfor %}
              </tbody>
            </table>
          </div>
          {% else %}
            <p class="empty">Sem processos configurados no menu.</p>
          {% endif %}
        </section>
        {% endif %}
        <!-- APPVERBO_ADMIN_MENU_NATIVE_CARD_V1_END -->
'''

    text = re.sub(
        r"(?s)\s*<!-- APPVERBO_ADMIN_MENU_NATIVE_CARD_V1_START -->.*?<!-- APPVERBO_ADMIN_MENU_NATIVE_CARD_V1_END -->",
        "\n" + card,
        text,
    )

    if "APPVERBO_ADMIN_MENU_NATIVE_CARD_V1_START" not in text:
        anchor = "<!-- APPVERBO_SIDEBAR_SECTIONS_JSON_V2_START -->"
        if anchor not in text:
            anchor = '<section id="dynamic-process-card"'

        if anchor not in text:
            raise RuntimeError("Nao foi possivel encontrar ponto de insercao para settings-card.")

        text = text.replace(anchor, card + "\n\n" + anchor, 1)

    # Inserir script nativo depois dos outros scripts do head_extra.
    text = re.sub(
        r'\s*<script src="/static/js/modules/appverbo_admin_menu_native_v1\.js[^"]*" defer></script>',
        "",
        text,
    )

    head_match = re.search(r"(?s)\{% block head_extra %\}.*?\{% endblock %\}", text)
    if not head_match:
        raise RuntimeError("Bloco head_extra nao encontrado.")

    script_tag = '  <script src="/static/js/modules/appverbo_admin_menu_native_v1.js?v=20260510-menu-nativo-v1" defer></script>'
    head_block = head_match.group(0)
    head_block_new = head_block.replace("{% endblock %}", script_tag + "\n{% endblock %}")
    text = text[: head_match.start()] + head_block_new + text[head_match.end():]

    # Atualizar cache dos assets principais.
    text = re.sub(
        r'href="/static/css/new_user\.css\?v=[^"]+"',
        'href="/static/css/new_user.css?v=20260510-menu-nativo-v1"',
        text,
    )
    text = re.sub(
        r'src="/static/js/new_user\.js(\?v=[^"]*)?"',
        'src="/static/js/new_user.js?v=20260510-menu-nativo-v1"',
        text,
    )

    if text != original:
        write(TEMPLATE, text)


def patch_css() -> None:
    text = read(CSS)

    text = re.sub(
        r"(?s)\n?/\* APPVERBO_ADMIN_MENU_NATIVE_V1_START \*/.*?/\* APPVERBO_ADMIN_MENU_NATIVE_V1_END \*/\n?",
        "\n",
        text,
    )

    css = r'''

/* APPVERBO_ADMIN_MENU_NATIVE_V1_START */
/*
  Subprocesso Administrativo > Menu.
  O Menu agora possui card nativo (#settings-card), reconhecido pelo backend.
*/
body.appverbo-admin-tab-menu #settings-card,
body.appverbo-menu-native-ok #settings-card,
#settings-card[data-admin-subprocess="menu"] {
  visibility: visible;
}

body.appverbo-menu-native-ok #settings-card {
  display: block !important;
  visibility: visible !important;
  opacity: 1 !important;
}

body.appverbo-menu-native-ok #menu-tabs-card {
  display: block !important;
  visibility: visible !important;
  opacity: 1 !important;
}

body.appverbo-menu-native-ok #home-summary-card,
body.appverbo-menu-native-ok #create-entity-card,
body.appverbo-menu-native-ok #create-user-card,
body.appverbo-menu-native-ok #admin-sidebar-sections-card,
body.appverbo-menu-native-ok #admin-account-status-card,
body.appverbo-menu-native-ok .admin-subprocess-card-v1:not(#settings-card) {
  display: none !important;
}

.appverbo-admin-menu-card-v1 .profile-card-header {
  align-items: flex-start;
}

.appverbo-admin-menu-subtitle-v1 {
  margin: 4px 0 0;
  color: #667085;
  font-size: 13px;
}

.appverbo-admin-menu-list-v1 {
  margin-top: 14px;
}

.appverbo-admin-menu-table-v1 td,
.appverbo-admin-menu-table-v1 th {
  vertical-align: middle;
}

body.appverbo-menu-native-ok #submenu-items [data-appverbo-menu-active="true"] {
  background: #1557b7 !important;
  background-color: #1557b7 !important;
  border-color: #1557b7 !important;
  color: #ffffff !important;
}

body.appverbo-menu-native-ok #submenu-items [data-appverbo-menu-inactive="true"] {
  background: #f9fbff !important;
  background-color: #f9fbff !important;
  border-color: #dce3f2 !important;
  color: #2f3850 !important;
  box-shadow: none !important;
}
/* APPVERBO_ADMIN_MENU_NATIVE_V1_END */
'''

    text = text.rstrip() + css + "\n"
    write(CSS, text)


def main() -> int:
    patch_page_handler()
    patch_template()
    patch_css()
    print("OK: subprocesso Menu integrado no backend, template e CSS.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
