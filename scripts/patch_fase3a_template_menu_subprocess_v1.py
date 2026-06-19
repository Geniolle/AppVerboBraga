from pathlib import Path

NEW_USER_TEMPLATE = Path("templates/new_user.html")
MENU_TEMPLATE_DIR = Path("templates/admin_subprocesses")
MENU_TEMPLATE = MENU_TEMPLATE_DIR / "menu.html"
PAGE_HANDLER = Path("appverbo/routes/profile/page_handler.py")
REGISTRY_FILE = Path("appverbo/admin_subprocesses/registry.py")
TOP_MENU_JS = Path("static/js/modules/top_menu_active_v1.js")


MENU_TEMPLATE_CONTENT = '''{# ################################################################################### #}
{# (1) TEMPLATE DO SUBPROCESSO ADMINISTRATIVO MENU - V1 #}
{# ################################################################################### #}

{% from "macros/admin_subprocess.html" import render_admin_subprocess_state %}

{# ################################################################################### #}
{# (2) CONTRATO DE ENTRADA #}
{# ################################################################################### #}
{#
  Este template recebe admin_menu_state montado no backend.

  Fase 3A:
  - Template profissional criado e validado.
  - Renderização nativa mantida desativada por segurança.
  - O HTML legado do Menu continua ativo no new_user.html.

  Fase 3B:
  - Ativar renderização visível.
  - Remover bloco legado do Menu após validação visual.
#}

{# ################################################################################### #}
{# (3) RENDERIZAÇÃO PREPARADA, SEM DUPLICAR UI LEGADA #}
{# ################################################################################### #}

{% if admin_menu_state %}
  <div
    id="admin-menu-template-v1"
    class="admin-menu-template-v1"
    data-admin-subprocess-template="menu"
    data-admin-subprocess-status="state-ready"
    hidden
  >
    {{ render_admin_subprocess_state(admin_menu_state) }}
  </div>
{% endif %}

{# ################################################################################### #}
{# FIM DO TEMPLATE DO SUBPROCESSO MENU #}
{# ################################################################################### #}
'''


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8", newline="\n")


def ensure_menu_template_v1() -> None:
    MENU_TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
    write_text(MENU_TEMPLATE, MENU_TEMPLATE_CONTENT)


def ensure_new_user_prepared_include_v1() -> None:
    text = read_text(NEW_USER_TEMPLATE)

    marker = "APPVERBO_ADMIN_MENU_TEMPLATE_INCLUDE_READY_V1"

    if marker in text:
        return

    include_block = '''
{# APPVERBO_ADMIN_MENU_TEMPLATE_INCLUDE_READY_V1_START #}
{#
  Fase 3A: include preparado, mas não ativado visualmente.
  Quando a Fase 3B for executada, este bloco poderá substituir o HTML legado do Menu.
#}
{% set admin_menu_template_include_ready_v1 = true %}
{# {% include "admin_subprocesses/menu.html" %} #}
{# APPVERBO_ADMIN_MENU_TEMPLATE_INCLUDE_READY_V1_END #}

'''

    anchors = [
        "{% block content %}",
        "<main",
        "<body",
    ]

    for anchor in anchors:
        index = text.find(anchor)

        if index >= 0:
            line_end = text.find("\n", index)

            if line_end >= 0:
                text = text[:line_end + 1] + include_block + text[line_end + 1:]
                write_text(NEW_USER_TEMPLATE, text)
                return

    text = include_block + text
    write_text(NEW_USER_TEMPLATE, text)


def ensure_page_handler_context_flag_v1() -> None:
    text = read_text(PAGE_HANDLER)

    if '"admin_menu_template_ready_v1": True,' in text:
        return

    anchor = '        "admin_menu_state": admin_menu_state,\n'

    if anchor not in text:
        raise RuntimeError("Anchor admin_menu_state não encontrado no context de page_handler.py")

    text = text.replace(
        anchor,
        anchor + '        "admin_menu_template_ready_v1": True,\n',
        1,
    )

    write_text(PAGE_HANDLER, text)


def validate_files_v1() -> None:
    menu_template_text = read_text(MENU_TEMPLATE)
    new_user_text = read_text(NEW_USER_TEMPLATE)
    page_text = read_text(PAGE_HANDLER)
    registry_text = read_text(REGISTRY_FILE)
    top_menu_text = read_text(TOP_MENU_JS)

    required_menu_template = [
        "TEMPLATE DO SUBPROCESSO ADMINISTRATIVO MENU - V1",
        'from "macros/admin_subprocess.html" import render_admin_subprocess_state',
        "{% if admin_menu_state %}",
        'data-admin-subprocess-template="menu"',
        "render_admin_subprocess_state(admin_menu_state)",
        "hidden",
    ]

    required_new_user = [
        "APPVERBO_ADMIN_MENU_TEMPLATE_INCLUDE_READY_V1_START",
        "admin_menu_template_include_ready_v1 = true",
        '{# {% include "admin_subprocesses/menu.html" %} #}',
    ]

    required_page = [
        '"admin_menu_state": admin_menu_state,',
        '"admin_menu_template_ready_v1": True,',
        "build_admin_menu_state",
        "admin_tab=menu&target=admin-menu-card",
    ]

    required_registry = [
        "MENU_CONFIG = AdminSubprocessConfig(",
        'key="menu"',
        'migration_status="state_ready"',
        "actions=MENU_ACTIONS,",
    ]

    required_top_menu = [
        "admin_tab=menu",
        'adminTab === "menu"',
        'adminTab === "contas"',
        'adminTab === "definicoes"',
    ]

    checks = [
        ("templates/admin_subprocesses/menu.html", menu_template_text, required_menu_template),
        ("templates/new_user.html", new_user_text, required_new_user),
        ("appverbo/routes/profile/page_handler.py", page_text, required_page),
        ("appverbo/admin_subprocesses/registry.py", registry_text, required_registry),
        ("static/js/modules/top_menu_active_v1.js", top_menu_text, required_top_menu),
    ]

    for name, content, required_items in checks:
        missing = [item for item in required_items if item not in content]

        if missing:
            raise RuntimeError(f"Validação falhou em {name}: " + " | ".join(missing))


def main() -> None:
    ensure_menu_template_v1()
    ensure_new_user_prepared_include_v1()
    ensure_page_handler_context_flag_v1()
    validate_files_v1()
    print("OK: Fase 3A aplicada. Template do subprocesso Menu criado e include preparado sem ativar UI duplicada.")


if __name__ == "__main__":
    main()
