# -*- coding: utf-8 -*-
from __future__ import annotations

import re
import sys
from pathlib import Path


TEMPLATE = Path("templates/new_user.html")
CSS = Path("static/css/new_user.css")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig").lstrip("\ufeff")


def write(path: Path, content: str) -> None:
    path.write_text(content.rstrip() + "\n", encoding="utf-8", newline="\n")


def patch_template() -> None:
    text = read(TEMPLATE)

    for script_name in (
        "appverbo_menu_render_guard_v1.js",
        "appverbo_admin_menu_native_v1.js",
        "appverbo_admin_menu_native_v2.js",
        "appverbo_admin_menu_native_v3.js",
        "appverbo_admin_menu_native_v4.js",
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

    head_match = re.search(r"(?s)\{% block head_extra %\}.*?\{% endblock %\}", text)

    if not head_match:
        raise RuntimeError("Bloco head_extra nao encontrado.")

    script_tag = '  <script src="/static/js/modules/appverbo_admin_menu_native_v4.js?v=20260510-menu-isolado-v4" defer></script>'
    head_block = head_match.group(0)
    head_block_new = head_block.replace("{% endblock %}", script_tag + "\n{% endblock %}")
    text = text[:head_match.start()] + head_block_new + text[head_match.end():]

    text = re.sub(
        r'href="/static/css/new_user\.css\?v=[^"]+"',
        'href="/static/css/new_user.css?v=20260510-menu-isolado-v4"',
        text,
    )
    text = re.sub(
        r'src="/static/js/new_user\.js(\?v=[^"]*)?"',
        'src="/static/js/new_user.js?v=20260510-menu-isolado-v4"',
        text,
    )

    write(TEMPLATE, text)


def patch_css() -> None:
    text = read(CSS)

    for marker in (
        "APPVERBO_MENU_RENDER_GUARD_V1",
        "APPVERBO_ADMIN_MENU_NATIVE_V1",
        "APPVERBO_ADMIN_MENU_NATIVE_V2",
        "APPVERBO_ADMIN_MENU_NATIVE_V3",
        "APPVERBO_ADMIN_MENU_NATIVE_V4",
    ):
        text = re.sub(
            rf"(?s)\n?/\* {marker}_START \*/.*?/\* {marker}_END \*/\n?",
            "\n",
            text,
        )

    css = r'''

/* APPVERBO_ADMIN_MENU_NATIVE_V4_START */
/*
  Isolamento definitivo do subprocesso Administrativo > Menu.
  Quando Menu estiver ativo, somente #menu-tabs-card e #settings-card ficam visiveis.
*/
body.appverbo-menu-native-ok #menu-tabs-card,
body.appverbo-menu-native-ok #settings-card {
  display: block !important;
  visibility: visible !important;
  opacity: 1 !important;
}

body.appverbo-menu-native-ok .content .card:not(#menu-tabs-card):not(#settings-card),
body.appverbo-menu-native-ok .content .admin-subprocess-card-v1:not(#menu-tabs-card):not(#settings-card),
body.appverbo-menu-native-ok main .card:not(#menu-tabs-card):not(#settings-card),
body.appverbo-menu-native-ok main .admin-subprocess-card-v1:not(#menu-tabs-card):not(#settings-card) {
  display: none !important;
  visibility: hidden !important;
  opacity: 0 !important;
}

body.appverbo-menu-native-ok #home-summary-card,
body.appverbo-menu-native-ok #create-entity-card,
body.appverbo-menu-native-ok #create-user-card,
body.appverbo-menu-native-ok #admin-sidebar-sections-card,
body.appverbo-menu-native-ok #admin-account-status-card,
body.appverbo-menu-native-ok #settings-menu-edit-card,
body.appverbo-menu-native-ok [data-admin-subprocess="entidade"],
body.appverbo-menu-native-ok [data-admin-subprocess="utilizador"],
body.appverbo-menu-native-ok [data-admin-subprocess="sessoes"],
body.appverbo-menu-native-ok [data-admin-subprocess="contas"] {
  display: none !important;
  visibility: hidden !important;
  opacity: 0 !important;
}

body.appverbo-menu-native-ok #settings-card[data-admin-subprocess="menu"] {
  display: block !important;
  visibility: visible !important;
  opacity: 1 !important;
}

.appverbo-admin-menu-card-v3 .profile-card-header,
.appverbo-admin-menu-card-v4 .profile-card-header {
  align-items: flex-start;
}

.appverbo-admin-menu-subtitle-v3,
.appverbo-admin-menu-subtitle-v4 {
  margin: 4px 0 0;
  color: #667085;
  font-size: 13px;
}

.appverbo-admin-menu-list-v3,
.appverbo-admin-menu-list-v4 {
  margin-top: 14px;
}

.appverbo-admin-menu-table-v3 td,
.appverbo-admin-menu-table-v3 th,
.appverbo-admin-menu-table-v4 td,
.appverbo-admin-menu-table-v4 th {
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
/* APPVERBO_ADMIN_MENU_NATIVE_V4_END */
'''

    text = text.rstrip() + css + "\n"
    write(CSS, text)


def main() -> int:
    patch_template()
    patch_css()
    print("OK: template e CSS atualizados para isolamento do Menu.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
