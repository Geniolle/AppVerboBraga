from pathlib import Path

NEW_USER_TEMPLATE = Path("templates/new_user.html")
MENU_TEMPLATE = Path("templates/admin_subprocesses/menu.html")
PAGE_HANDLER = Path("appverbo/routes/profile/page_handler.py")
REGISTRY_FILE = Path("appverbo/admin_subprocesses/registry.py")
TOP_MENU_JS = Path("static/js/modules/top_menu_active_v1.js")


MENU_TEMPLATE_CONTENT = '''{# ################################################################################### #}
{# (1) TEMPLATE DO SUBPROCESSO ADMINISTRATIVO MENU - V3 #}
{# ################################################################################### #}

{% from "macros/admin_subprocess.html" import render_admin_subprocess_state %}

{# ################################################################################### #}
{# (2) CONTRATO DE ENTRADA #}
{# ################################################################################### #}
{#
  Este template recebe:
  - admin_menu_state
  - admin_menu_template_mode

  Fase 3C:
  - Native passa a ser o modo padrão para admin_tab=menu.
  - admin_menu_template_mode=legacy mantém fallback temporário.
#}

{# ################################################################################### #}
{# (3) RENDERIZAÇÃO NATIVA PADRÃO #}
{# ################################################################################### #}

{% set is_admin_menu_legacy_v1 = admin_menu_template_mode|default("native", true) == "legacy" %}
{% set is_admin_menu_native_v1 = not is_admin_menu_legacy_v1 %}

{% if admin_menu_state %}
  <div
    id="admin-menu-template-v1"
    class="admin-menu-template-v1"
    data-admin-subprocess-template="menu"
    data-admin-subprocess-status="state-ready"
    data-admin-template-mode="{{ admin_menu_template_mode|default('native', true) }}"
    {% if not is_admin_menu_native_v1 %}hidden{% endif %}
  >
    {{ render_admin_subprocess_state(admin_menu_state) }}
  </div>

  {% if is_admin_menu_native_v1 %}
    <script>
      (function () {
        function hideLegacyMenuCardsV1() {
          var wrapper = document.getElementById("admin-menu-template-v1");

          if (!wrapper) {
            return;
          }

          var selectors = [
            "#admin-menu-card",
            "#settings-card",
            "#settings-menu-edit-card",
            "#admin-account-status-card"
          ];

          selectors.forEach(function (selector) {
            document.querySelectorAll(selector).forEach(function (card) {
              if (wrapper.contains(card)) {
                return;
              }

              card.setAttribute("hidden", "hidden");
              card.classList.add("appverbo-menu-legacy-hidden-v1");
              card.setAttribute("data-admin-menu-legacy-hidden", "true");
            });
          });

          document.documentElement.setAttribute("data-admin-menu-template-mode", "native");
        }

        if (document.readyState === "loading") {
          document.addEventListener("DOMContentLoaded", hideLegacyMenuCardsV1, { once: true });
        }
        else {
          hideLegacyMenuCardsV1();
        }
      })();
    </script>
  {% endif %}
{% endif %}

{# ################################################################################### #}
{# FIM DO TEMPLATE DO SUBPROCESSO MENU #}
{# ################################################################################### #}
'''


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8", newline="\n")


def replace_between_markers(text: str, start_marker: str, end_marker: str, replacement: str) -> tuple[str, bool]:
    start = text.find(start_marker)
    end = text.find(end_marker)

    if start < 0 or end < 0 or end < start:
        return text, False

    end = end + len(end_marker)
    return text[:start] + replacement + text[end:], True


def patch_menu_template_v3() -> None:
    write_text(MENU_TEMPLATE, MENU_TEMPLATE_CONTENT)


def patch_new_user_include_v1() -> None:
    text = read_text(NEW_USER_TEMPLATE)

    start_marker = "{# APPVERBO_ADMIN_MENU_TEMPLATE_INCLUDE_READY_V1_START #}"
    end_marker = "{# APPVERBO_ADMIN_MENU_TEMPLATE_INCLUDE_READY_V1_END #}"

    include_block = '''{# APPVERBO_ADMIN_MENU_TEMPLATE_INCLUDE_READY_V1_START #}
{# Fase 3C: include ativo por padrão para admin_tab=menu; legacy fica disponível por query param. #}
{% set appverbo_current_admin_tab_v1 = resolved_admin_tab|default(admin_tab|default("", true), true) %}
{% if admin_menu_template_ready_v1 and admin_menu_template_mode != "legacy" and appverbo_current_admin_tab_v1 == "menu" %}
  {% include "admin_subprocesses/menu.html" %}
{% endif %}
{# APPVERBO_ADMIN_MENU_TEMPLATE_INCLUDE_READY_V1_END #}'''

    text, replaced = replace_between_markers(
        text,
        start_marker,
        end_marker,
        include_block,
    )

    if not replaced:
        raise RuntimeError("Bloco APPVERBO_ADMIN_MENU_TEMPLATE_INCLUDE_READY_V1 não encontrado em new_user.html")

    write_text(NEW_USER_TEMPLATE, text)


def patch_page_handler_context_v1() -> None:
    text = read_text(PAGE_HANDLER)

    old_line = '        "admin_menu_template_mode": str(request.query_params.get("admin_menu_template_mode") or "").strip().lower(),\n'
    new_line = '        "admin_menu_template_mode": (str(request.query_params.get("admin_menu_template_mode") or "native").strip().lower() or "native"),\n'

    if old_line in text:
        text = text.replace(old_line, new_line, 1)
    elif new_line not in text:
        anchor = '        "admin_menu_template_ready_v1": True,\n'

        if anchor not in text:
            raise RuntimeError("Anchor admin_menu_template_ready_v1 não encontrado no context de page_handler.py")

        text = text.replace(anchor, anchor + new_line, 1)

    write_text(PAGE_HANDLER, text)


def validate_files_v1() -> None:
    menu_template_text = read_text(MENU_TEMPLATE)
    new_user_text = read_text(NEW_USER_TEMPLATE)
    page_text = read_text(PAGE_HANDLER)
    registry_text = read_text(REGISTRY_FILE)
    top_menu_text = read_text(TOP_MENU_JS)

    required_menu_template = [
        "TEMPLATE DO SUBPROCESSO ADMINISTRATIVO MENU - V3",
        "is_admin_menu_legacy_v1",
        'admin_menu_template_mode|default("native", true) == "legacy"',
        "is_admin_menu_native_v1 = not is_admin_menu_legacy_v1",
        'id="admin-menu-template-v1"',
        "render_admin_subprocess_state(admin_menu_state)",
        "hideLegacyMenuCardsV1",
        "appverbo-menu-legacy-hidden-v1",
    ]

    required_new_user = [
        "APPVERBO_ADMIN_MENU_TEMPLATE_INCLUDE_READY_V1_START",
        'admin_menu_template_mode != "legacy"',
        'appverbo_current_admin_tab_v1 == "menu"',
        '{% include "admin_subprocesses/menu.html" %}',
    ]

    required_page = [
        '"admin_menu_state": admin_menu_state,',
        '"admin_menu_template_ready_v1": True,',
        '"admin_menu_template_mode": (str(request.query_params.get("admin_menu_template_mode") or "native").strip().lower() or "native"),',
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
    patch_menu_template_v3()
    patch_new_user_include_v1()
    patch_page_handler_context_v1()
    validate_files_v1()
    print("OK: Fase 3C aplicada. Menu nativo agora é padrão com fallback legacy por query param.")


if __name__ == "__main__":
    main()
