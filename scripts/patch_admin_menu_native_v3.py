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


def ensure_value_in_set_after_phrase(text: str, phrase: str, value: str) -> str:
    index = text.find(phrase)

    if index < 0:
        raise RuntimeError(f"Nao foi possivel localizar frase: {phrase}")

    open_index = text.find("{", index)

    if open_index < 0:
        raise RuntimeError(f"Nao foi possivel localizar abertura do set apos: {phrase}")

    close_index = text.find("}", open_index)

    if close_index < 0:
        raise RuntimeError(f"Nao foi possivel localizar fecho do set apos: {phrase}")

    body = text[open_index + 1:close_index]

    if f'"{value}"' in body or f"'{value}'" in body:
        return text

    new_body = body.rstrip() + f',\n        "{value}",\n    '

    return text[:open_index + 1] + new_body + text[close_index:]


def remove_marker_block(text: str, marker: str) -> str:
    return re.sub(
        rf"(?s)\n?\s*# {marker}_START.*?# {marker}_END\n?",
        "\n",
        text,
    )


def patch_page_handler() -> None:
    text = read(PAGE_HANDLER)
    original = text

    text = remove_marker_block(text, "APPVERBO_ADMIN_MENU_NATIVE_TARGET_RESOLVE_V1")
    text = remove_marker_block(text, "APPVERBO_ADMIN_MENU_NATIVE_TARGET_RESOLVE_V2")
    text = remove_marker_block(text, "APPVERBO_ADMIN_MENU_NATIVE_TARGET_RESOLVE_V3")
    text = remove_marker_block(text, "APPVERBO_ADMIN_MENU_NATIVE_POST_CONTEXT_V1")
    text = remove_marker_block(text, "APPVERBO_ADMIN_MENU_NATIVE_POST_CONTEXT_V2")
    text = remove_marker_block(text, "APPVERBO_ADMIN_MENU_NATIVE_POST_CONTEXT_V3")

    text = ensure_value_in_set_after_phrase(
        text,
        "if resolved_admin_tab not in",
        "menu",
    )

    text = ensure_value_in_set_after_phrase(
        text,
        "if clean_settings_tab not in",
        "menu",
    )

    admin_block_match = re.search(
        r'(?s)(    if clean_menu_key == "administrativo":\n)(.*?)(    if clean_menu_key == "configuracao":)',
        text,
    )

    if not admin_block_match:
        raise RuntimeError("Nao foi possivel localizar bloco administrativo em _resolve_initial_menu_target.")

    admin_header = admin_block_match.group(1)
    admin_body = admin_block_match.group(2)
    next_block = admin_block_match.group(3)

    if 'resolved_admin_tab == "menu"' not in admin_body:
        menu_target_block = (
            '        # APPVERBO_ADMIN_MENU_NATIVE_TARGET_RESOLVE_V3_START\n'
            '        if resolved_admin_tab == "menu":\n'
            '            return "#settings-card", ""\n'
            '        # APPVERBO_ADMIN_MENU_NATIVE_TARGET_RESOLVE_V3_END\n'
        )

        if 'if settings_edit_key:' in admin_body:
            admin_body = admin_body.replace(
                '        if settings_edit_key:\n            return "#settings-menu-edit-card", ""\n',
                '        if settings_edit_key:\n            return "#settings-menu-edit-card", ""\n'
                + menu_target_block,
                1,
            )
        else:
            admin_body = menu_target_block + admin_body

    text = (
        text[:admin_block_match.start()]
        + admin_header
        + admin_body
        + next_block
        + text[admin_block_match.end():]
    )

    post_context_block = (
        '\n    # APPVERBO_ADMIN_MENU_NATIVE_POST_CONTEXT_V3_START\n'
        '    if resolved_admin_tab == "menu":\n'
        '        initial_menu_target = "#settings-card"\n'
        '        initial_dynamic_process_section = ""\n'
        '        clean_dynamic_section_from_query = ""\n'
        '    # APPVERBO_ADMIN_MENU_NATIVE_POST_CONTEXT_V3_END\n\n'
    )

    insertion_markers = [
        "    # APPVERBO_ADMIN_SUBPROCESS_STATE_SESSOES_V2_START",
        "    context = {",
        "    is_post_save_return = str(appverbo_after_save or \"\").strip() == \"1\"",
    ]

    inserted = False

    for marker in insertion_markers:
        position = text.find(marker)

        if position >= 0:
            if marker.startswith("    is_post_save_return"):
                line_end = text.find("\n", position)
                if line_end < 0:
                    line_end = position + len(marker)
                text = text[:line_end + 1] + post_context_block + text[line_end + 1:]
            else:
                text = text[:position] + post_context_block + text[position:]
            inserted = True
            break

    if not inserted:
        raise RuntimeError("Nao foi possivel encontrar ponto seguro para contexto do Menu.")

    if text != original:
        write(PAGE_HANDLER, text)


def build_menu_card() -> str:
    return r'''
        <!-- APPVERBO_ADMIN_MENU_NATIVE_CARD_V3_START -->
        {% if current_user_is_admin %}
        <section
          id="settings-card"
          class="card appverbo-admin-native-card appverbo-admin-menu-card-v3"
          data-menu-scope="administrativo"
          data-admin-subprocess="menu"
          style="{% if admin_tab == 'menu' %}display: block;{% else %}display: none;{% endif %}"
        >
          <div class="profile-card-header">
            <div>
              <h2>Menu</h2>
              <p class="appverbo-admin-menu-subtitle-v3">
                Configuração dos processos visíveis no menu lateral.
              </p>
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
          <div class="admin-subsection appverbo-admin-menu-list-v3">
            <table class="admin-subprocess-table-v1 appverbo-admin-menu-table-v3">
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
                    <td><strong>{{ row_label }}</strong></td>
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
        <!-- APPVERBO_ADMIN_MENU_NATIVE_CARD_V3_END -->
'''


def patch_template() -> None:
    text = read(TEMPLATE)
    original = text

    for script_name in (
        "appverbo_menu_render_guard_v1.js",
        "appverbo_admin_menu_native_v1.js",
        "appverbo_admin_menu_native_v2.js",
        "appverbo_admin_menu_native_v3.js",
    ):
        text = re.sub(
            rf'\s*<script src="/static/js/modules/{re.escape(script_name)}[^"]*" defer></script>',
            "",
            text,
        )
        text = re.sub(
            rf'\s*<script src="/static/js/modules/{re.escape(script_name)}[^"]*"></script>',
            "",
            text,
        )

    for version in ("V1", "V2", "V3"):
        text = re.sub(
            rf"(?s)\s*<!-- APPVERBO_ADMIN_MENU_NATIVE_CARD_{version}_START -->.*?<!-- APPVERBO_ADMIN_MENU_NATIVE_CARD_{version}_END -->",
            "\n",
            text,
        )

    card = build_menu_card()

    anchors = [
        "<!-- APPVERBO_SIDEBAR_SECTIONS_JSON_V2_START -->",
        '<section id="dynamic-process-card"',
        '<div id="dynamic-process-card"',
        "{% block scripts %}",
        "</main>",
    ]

    inserted = False

    for anchor in anchors:
        if anchor in text:
            text = text.replace(anchor, card + "\n\n" + anchor, 1)
            inserted = True
            break

    if not inserted:
        last_container = text.rfind("</div>")

        if last_container < 0:
            raise RuntimeError("Nao foi possivel encontrar ponto de insercao para settings-card.")

        text = text[:last_container] + card + "\n" + text[last_container:]

    head_match = re.search(r"(?s)\{% block head_extra %\}.*?\{% endblock %\}", text)

    if not head_match:
        raise RuntimeError("Bloco head_extra nao encontrado.")

    script_tag = '  <script src="/static/js/modules/appverbo_admin_menu_native_v3.js?v=20260510-menu-nativo-v3" defer></script>'
    head_block = head_match.group(0)
    head_block_new = head_block.replace("{% endblock %}", script_tag + "\n{% endblock %}")

    text = text[:head_match.start()] + head_block_new + text[head_match.end():]

    text = re.sub(
        r'href="/static/css/new_user\.css\?v=[^"]+"',
        'href="/static/css/new_user.css?v=20260510-menu-nativo-v3"',
        text,
    )
    text = re.sub(
        r'src="/static/js/new_user\.js(\?v=[^"]*)?"',
        'src="/static/js/new_user.js?v=20260510-menu-nativo-v3"',
        text,
    )

    if text != original:
        write(TEMPLATE, text)


def patch_css() -> None:
    text = read(CSS)

    for marker in (
        "APPVERBO_MENU_RENDER_GUARD_V1",
        "APPVERBO_ADMIN_MENU_NATIVE_V1",
        "APPVERBO_ADMIN_MENU_NATIVE_V2",
        "APPVERBO_ADMIN_MENU_NATIVE_V3",
    ):
        text = re.sub(
            rf"(?s)\n?/\* {marker}_START \*/.*?/\* {marker}_END \*/\n?",
            "\n",
            text,
        )

    css = r'''

/* APPVERBO_ADMIN_MENU_NATIVE_V3_START */
/*
  Administrativo > Menu.
  O Menu agora possui card nativo (#settings-card), reconhecido pelo backend.
*/
body.appverbo-menu-native-ok #settings-card,
body.appverbo-admin-tab-menu #settings-card,
#settings-card[data-admin-subprocess="menu"] {
  display: block;
  visibility: visible;
  opacity: 1;
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

.appverbo-admin-menu-card-v3 .profile-card-header {
  align-items: flex-start;
}

.appverbo-admin-menu-subtitle-v3 {
  margin: 4px 0 0;
  color: #667085;
  font-size: 13px;
}

.appverbo-admin-menu-list-v3 {
  margin-top: 14px;
}

.appverbo-admin-menu-table-v3 td,
.appverbo-admin-menu-table-v3 th {
  vertical-align: middle;
}

body.appverbo-menu-native-ok #submenu-items [data-appverbo-menu-active="true"] {
  background: #1557b7 !important;
  background-color: #1557b7 !important;
  border-color: #1557b7 !important;
  color: #ffffff !important;
}

body.appverbo-menu-native-ok #submenu-items [data-appverbo-menu-active="true"] * {
  color: #ffffff !important;
}

body.appverbo-menu-native-ok #submenu-items [data-appverbo-menu-inactive="true"] {
  background: #f9fbff !important;
  background-color: #f9fbff !important;
  border-color: #dce3f2 !important;
  color: #2f3850 !important;
  box-shadow: none !important;
}
/* APPVERBO_ADMIN_MENU_NATIVE_V3_END */
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
