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


def add_to_set_literal(text: str, set_start_pattern: str, value: str, marker_name: str) -> str:
    match = re.search(set_start_pattern, text, flags=re.DOTALL)

    if not match:
        raise RuntimeError(f"Nao foi possivel localizar set para {marker_name}.")

    set_body = match.group(1)

    if f'"{value}"' in set_body or f"'{value}'" in set_body:
        return text

    new_set_body = set_body.rstrip() + f',\n        "{value}",\n    '
    return text[:match.start(1)] + new_set_body + text[match.end(1):]


def patch_page_handler() -> None:
    text = read(PAGE_HANDLER)
    original = text

    # Aceitar admin_tab=menu.
    resolved_set_pattern = r"if resolved_admin_tab not in \{(.*?)\}:"
    text = add_to_set_literal(
        text,
        resolved_set_pattern,
        "menu",
        "resolved_admin_tab",
    )

    # Aceitar settings_tab=menu.
    settings_set_pattern = r"if clean_settings_tab not in \{(.*?)\}:"
    text = add_to_set_literal(
        text,
        settings_set_pattern,
        "menu",
        "clean_settings_tab",
    )

    # Normalizar definicoes apenas para contas, sem afetar menu.
    text = re.sub(
        r'if resolved_admin_tab == "definicoes":\s*\n\s*resolved_admin_tab = "contas"',
        'if resolved_admin_tab == "definicoes":\n        resolved_admin_tab = "contas"',
        text,
        count=1,
    )

    # Resolver target nativo do Menu dentro de _resolve_initial_menu_target.
    if "APPVERBO_ADMIN_MENU_NATIVE_TARGET_RESOLVE_V2_START" not in text:
        settings_anchor = '        if settings_edit_key:\n            return "#settings-menu-edit-card", ""\n'

        if settings_anchor in text:
            insert = (
                settings_anchor
                + '        # APPVERBO_ADMIN_MENU_NATIVE_TARGET_RESOLVE_V2_START\n'
                + '        if resolved_admin_tab == "menu":\n'
                + '            return "#settings-card", ""\n'
                + '        # APPVERBO_ADMIN_MENU_NATIVE_TARGET_RESOLVE_V2_END\n'
            )
            text = text.replace(settings_anchor, insert, 1)
        else:
            admin_anchor = '    if clean_menu_key == "administrativo":\n'
            if admin_anchor not in text:
                raise RuntimeError("Nao foi possivel localizar bloco clean_menu_key == administrativo.")

            insert = (
                admin_anchor
                + '        # APPVERBO_ADMIN_MENU_NATIVE_TARGET_RESOLVE_V2_START\n'
                + '        if resolved_admin_tab == "menu":\n'
                + '            return "#settings-card", ""\n'
                + '        # APPVERBO_ADMIN_MENU_NATIVE_TARGET_RESOLVE_V2_END\n'
            )
            text = text.replace(admin_anchor, insert, 1)

    # Forcar contexto do Menu depois dos parametros target/dynamic serem tratados.
    if "APPVERBO_ADMIN_MENU_NATIVE_POST_CONTEXT_V2_START" not in text:
        sessoes_anchor = re.search(
            r'\n    if resolved_admin_tab == "sessoes":\n',
            text,
        )

        if not sessoes_anchor:
            raise RuntimeError("Nao foi possivel localizar if resolved_admin_tab == sessoes.")

        insert = (
            '\n    # APPVERBO_ADMIN_MENU_NATIVE_POST_CONTEXT_V2_START\n'
            '    if resolved_admin_tab == "menu":\n'
            '        initial_menu_target = "#settings-card"\n'
            '        initial_dynamic_process_section = ""\n'
            '        clean_dynamic_section_from_query = ""\n'
            '    # APPVERBO_ADMIN_MENU_NATIVE_POST_CONTEXT_V2_END\n'
        )

        text = text[:sessoes_anchor.start()] + insert + text[sessoes_anchor.start():]

    if text != original:
        write(PAGE_HANDLER, text)


def build_menu_card() -> str:
    return r'''
        <!-- APPVERBO_ADMIN_MENU_NATIVE_CARD_V2_START -->
        {% if current_user_is_admin %}
        <section
          id="settings-card"
          class="card appverbo-admin-native-card appverbo-admin-menu-card-v2"
          data-menu-scope="administrativo"
          data-admin-subprocess="menu"
          style="{% if admin_tab == 'menu' %}display: block;{% else %}display: none;{% endif %}"
        >
          <div class="profile-card-header">
            <div>
              <h2>Menu</h2>
              <p class="appverbo-admin-menu-subtitle-v2">
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
          <div class="admin-subsection appverbo-admin-menu-list-v2">
            <table class="admin-subprocess-table-v1 appverbo-admin-menu-table-v2">
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
        <!-- APPVERBO_ADMIN_MENU_NATIVE_CARD_V2_END -->
'''


def patch_template() -> None:
    text = read(TEMPLATE)
    original = text

    # Remover scripts antigos/duplicados do Menu.
    for script_name in (
        "appverbo_menu_render_guard_v1.js",
        "appverbo_admin_menu_native_v1.js",
        "appverbo_admin_menu_native_v2.js",
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

    # Remover bloco nativo antigo se existir.
    text = re.sub(
        r"(?s)\s*<!-- APPVERBO_ADMIN_MENU_NATIVE_CARD_V1_START -->.*?<!-- APPVERBO_ADMIN_MENU_NATIVE_CARD_V1_END -->",
        "\n",
        text,
    )
    text = re.sub(
        r"(?s)\s*<!-- APPVERBO_ADMIN_MENU_NATIVE_CARD_V2_START -->.*?<!-- APPVERBO_ADMIN_MENU_NATIVE_CARD_V2_END -->",
        "\n",
        text,
    )

    card = build_menu_card()

    # Inserir antes do bloco de processo dinâmico/JSON, ou antes do fim do conteúdo.
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
        last_div = text.rfind("</div>")
        if last_div < 0:
            raise RuntimeError("Nao foi possivel encontrar ponto de insercao para settings-card.")
        text = text[:last_div] + card + "\n" + text[last_div:]

    # Inserir script nativo no head_extra.
    head_match = re.search(r"(?s)\{% block head_extra %\}.*?\{% endblock %\}", text)

    if not head_match:
        raise RuntimeError("Bloco head_extra nao encontrado.")

    script_tag = '  <script src="/static/js/modules/appverbo_admin_menu_native_v2.js?v=20260510-menu-nativo-v2" defer></script>'
    head_block = head_match.group(0)

    if "appverbo_admin_menu_native_v2.js" not in head_block:
        head_block_new = head_block.replace("{% endblock %}", script_tag + "\n{% endblock %}")
        text = text[:head_match.start()] + head_block_new + text[head_match.end():]

    # Atualizar cache.
    text = re.sub(
        r'href="/static/css/new_user\.css\?v=[^"]+"',
        'href="/static/css/new_user.css?v=20260510-menu-nativo-v2"',
        text,
    )
    text = re.sub(
        r'src="/static/js/new_user\.js(\?v=[^"]*)?"',
        'src="/static/js/new_user.js?v=20260510-menu-nativo-v2"',
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
    ):
        text = re.sub(
            rf"(?s)\n?/\* {marker}_START \*/.*?/\* {marker}_END \*/\n?",
            "\n",
            text,
        )

    css = r'''

/* APPVERBO_ADMIN_MENU_NATIVE_V2_START */
/*
  Administrativo > Menu.
  Agora o Menu possui card nativo (#settings-card), reconhecido pelo backend.
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

.appverbo-admin-menu-card-v2 .profile-card-header {
  align-items: flex-start;
}

.appverbo-admin-menu-subtitle-v2 {
  margin: 4px 0 0;
  color: #667085;
  font-size: 13px;
}

.appverbo-admin-menu-list-v2 {
  margin-top: 14px;
}

.appverbo-admin-menu-table-v2 td,
.appverbo-admin-menu-table-v2 th {
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
/* APPVERBO_ADMIN_MENU_NATIVE_V2_END */
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
