from __future__ import annotations

import re
import shutil
from datetime import datetime
from pathlib import Path


####################################################################################
# (1) CONFIGURACAO
####################################################################################

PROJECT_ROOT = Path.cwd()

PAGE_HANDLER_PATH = PROJECT_ROOT / "appverbo" / "routes" / "profile" / "page_handler.py"
TEMPLATE_PATH = PROJECT_ROOT / "templates" / "new_user.html"
V2_REGISTRY_PATH = PROJECT_ROOT / "appverbo" / "admin_subprocesses" / "v2_registry.py"
V2_SERVICE_PATH = PROJECT_ROOT / "appverbo" / "admin_subprocesses" / "v2_service.py"
V2_HANDLERS_PATH = PROJECT_ROOT / "appverbo" / "routes" / "profile" / "admin_subprocess_handlers_v2.py"
V2_MACRO_PATH = PROJECT_ROOT / "templates" / "macros" / "admin_subprocess_v2.html"
V2_INTEGRATION_JS_PATH = PROJECT_ROOT / "static" / "js" / "modules" / "admin_subprocesses_v2_integration.js"

REQUIRED_V2_FILES = [
    PROJECT_ROOT / "appverbo" / "admin_subprocesses" / "v2_models.py",
    PROJECT_ROOT / "appverbo" / "admin_subprocesses" / "v2_repository.py",
    PROJECT_ROOT / "appverbo" / "admin_subprocesses" / "v2_entity_repository.py",
    V2_REGISTRY_PATH,
    V2_SERVICE_PATH,
    V2_HANDLERS_PATH,
    V2_MACRO_PATH,
    PROJECT_ROOT / "static" / "css" / "modules" / "admin_subprocesses_v2.css",
    PROJECT_ROOT / "static" / "js" / "modules" / "admin_subprocesses_v2.js",
]


####################################################################################
# (2) FUNCOES AUXILIARES
####################################################################################

def now_stamp_v1() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def read_text_v1(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text_v1(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def backup_file_v1(path: Path, suffix: str) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"Ficheiro nao encontrado para backup: {path}")

    backup_path = path.with_name(path.name + f".bak_{suffix}_{now_stamp_v1()}")
    shutil.copy2(path, backup_path)
    return backup_path


def require_file_v1(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Ficheiro obrigatorio nao encontrado: {path}")


def replace_marker_block_v1(content: str, start_marker: str, end_marker: str, new_block: str) -> str:
    pattern = re.compile(
        re.escape(start_marker) + r".*?" + re.escape(end_marker),
        flags=re.DOTALL,
    )

    if pattern.search(content):
        return pattern.sub(lambda _match: new_block.strip(), content)

    return content.rstrip() + "\n\n" + new_block.strip() + "\n"


####################################################################################
# (3) VALIDAR MOTOR V2 EXISTENTE
####################################################################################

def validate_v2_base_exists_v1() -> None:
    missing = [str(path) for path in REQUIRED_V2_FILES if not path.exists()]

    if missing:
        raise RuntimeError(
            "Motor Admin Subprocess V2 ainda nao existe. Execute primeiro o patch do motor V2. "
            "Ficheiros ausentes: " + ", ".join(missing)
        )


####################################################################################
# (4) AJUSTAR REGISTRY V2
####################################################################################

def patch_v2_registry_v1() -> None:
    content = read_text_v1(V2_REGISTRY_PATH)

    content = content.replace('edit_param="entity_id"', 'edit_param="entity_edit_id"')

    if 'edit_param="entity_edit_id"' not in content:
        raise RuntimeError("Nao foi possivel configurar edit_param='entity_edit_id' na Entidade V2.")

    write_text_v1(V2_REGISTRY_PATH, content)


####################################################################################
# (5) AJUSTAR SERVICE V2
####################################################################################

def patch_v2_service_v1() -> None:
    content = read_text_v1(V2_SERVICE_PATH)

    new_block = '''def default_admin_subprocess_return_url_v2(config: AdminSubprocessConfigV2) -> str:
    return (
        f"/users/new?menu=administrativo&admin_tab={config.key}"
        f"&target=%23{config.resolved_default_target}"
    )
'''

    if "def default_admin_subprocess_return_url_v2" not in content:
        raise RuntimeError("Nao encontrei default_admin_subprocess_return_url_v2 em v2_service.py.")

    content = re.sub(
        r"def default_admin_subprocess_return_url_v2\(config: AdminSubprocessConfigV2\) -> str:\n.*?(?=\n\n#|\n\n\ndef |\Z)",
        new_block.rstrip(),
        content,
        count=1,
        flags=re.DOTALL,
    )

    if "target=%23{config.resolved_default_target}" not in content:
        raise RuntimeError("Return URL V2 nao contem target do subprocesso.")

    write_text_v1(V2_SERVICE_PATH, content)


####################################################################################
# (6) AJUSTAR HANDLERS V2
####################################################################################

def patch_v2_handlers_v1() -> None:
    content = read_text_v1(V2_HANDLERS_PATH)

    old_signature = '''def admin_subprocess_standalone_page_v2(
    subprocess_key: str,
    request: Request,
    edit_key: str = "",
) -> HTMLResponse:'''

    new_signature = '''def admin_subprocess_standalone_page_v2(
    subprocess_key: str,
    request: Request,
    edit_key: str = "",
    entity_edit_id: str = "",
) -> HTMLResponse:'''

    if old_signature in content:
        content = content.replace(old_signature, new_signature, 1)

    if "entity_edit_id: str = \"\"," not in content:
        raise RuntimeError("Handler standalone V2 nao aceita entity_edit_id.")

    if "edit_key=edit_key," in content:
        content = content.replace("edit_key=edit_key,", "edit_key=edit_key or entity_edit_id,", 1)

    if "edit_key=edit_key or entity_edit_id," not in content:
        raise RuntimeError("Handler standalone V2 nao usa entity_edit_id no estado.")

    write_text_v1(V2_HANDLERS_PATH, content)


####################################################################################
# (7) AJUSTAR MACRO V2
####################################################################################

def patch_v2_macro_v1() -> None:
    content = read_text_v1(V2_MACRO_PATH)

    old_href = 'href="/admin/subprocess-v2/{{ state.config.key }}?edit_key={{ row_key }}"'
    new_href = 'href="{{ state.return_url }}{% if \'?\' in state.return_url %}&{% else %}?{% endif %}{{ state.config.edit_param }}={{ row_key }}&target=%23{{ state.config.resolved_edit_target }}#{{ state.config.resolved_edit_target }}"'

    if old_href in content:
        content = content.replace(old_href, new_href, 1)

    if "{{ state.config.edit_param }}={{ row_key }}" not in content:
        raise RuntimeError("Macro V2 nao usa edit_param configuravel para editar.")

    write_text_v1(V2_MACRO_PATH, content)


####################################################################################
# (8) AJUSTAR PAGE_HANDLER
####################################################################################

def patch_page_handler_imports_v1(content: str) -> str:
    if "build_admin_subprocess_state_v2" in content:
        return content

    anchor = "from appverbo.admin_subprocesses.service import build_admin_subprocess_state\n"

    if anchor not in content:
        raise RuntimeError("Nao encontrei import build_admin_subprocess_state em page_handler.py.")

    import_block = '''# APPVERBO_ADMIN_SUBPROCESS_V2_PAGE_IMPORTS_START
from appverbo.admin_subprocesses.v2_service import build_admin_subprocess_state_v2
# APPVERBO_ADMIN_SUBPROCESS_V2_PAGE_IMPORTS_END
'''

    return content.replace(anchor, anchor + import_block, 1)


def patch_page_handler_target_v1(content: str) -> str:
    if 'if resolved_admin_tab == "entidade":\n            return "#admin-subprocess-v2-entidade", ""' in content:
        return content

    old_return = '        return "#create-entity-card", ""'

    new_return = '''        if resolved_admin_tab == "entidade":
            return "#admin-subprocess-v2-entidade", ""
        return "#create-entity-card", ""'''

    if old_return not in content:
        raise RuntimeError("Nao encontrei return #create-entity-card para trocar pelo target Entidade V2.")

    return content.replace(old_return, new_return, 1)


def patch_page_handler_state_v1(content: str) -> str:
    start_marker = "# APPVERBO_ADMIN_SUBPROCESS_STATE_ENTIDADE_V2_START"
    end_marker = "# APPVERBO_ADMIN_SUBPROCESS_STATE_ENTIDADE_V2_END"

    state_block = '''    # APPVERBO_ADMIN_SUBPROCESS_STATE_ENTIDADE_V2_START
    if resolved_admin_tab == "entidade":
        admin_subprocess_state_v2 = build_admin_subprocess_state_v2(
            key="entidade",
            session=session,
            request=request,
            current_user=current_user,
            edit_key=clean_entity_edit_id,
            success=entity_success or "",
            error=entity_error or "",
            return_url="/users/new?menu=administrativo&admin_tab=entidade&target=%23admin-subprocess-v2-entidade",
        )
    # APPVERBO_ADMIN_SUBPROCESS_STATE_ENTIDADE_V2_END

'''

    if start_marker in content and end_marker in content:
        pattern = re.compile(
            re.escape(start_marker) + r".*?" + re.escape(end_marker) + r"\n\n",
            flags=re.DOTALL,
        )
        return pattern.sub(lambda _match: state_block, content)

    anchors = [
        '    # APPVERBO_ADMIN_SUBPROCESS_STATE_SESSOES_V2_START\n',
        '    context = {\n',
    ]

    for anchor in anchors:
        if anchor in content:
            return content.replace(anchor, state_block + anchor, 1)

    raise RuntimeError("Nao encontrei ponto para inserir estado Entidade V2 no page_handler.py.")


def patch_page_handler_v1() -> None:
    content = read_text_v1(PAGE_HANDLER_PATH)

    content = patch_page_handler_imports_v1(content)
    content = patch_page_handler_target_v1(content)
    content = patch_page_handler_state_v1(content)

    required = [
        "build_admin_subprocess_state_v2",
        "APPVERBO_ADMIN_SUBPROCESS_STATE_ENTIDADE_V2_START",
        "admin_tab=entidade",
        "#admin-subprocess-v2-entidade",
    ]

    missing = [marker for marker in required if marker not in content]

    if missing:
        raise RuntimeError("Marcadores ausentes em page_handler.py: " + ", ".join(missing))

    write_text_v1(PAGE_HANDLER_PATH, content)


####################################################################################
# (9) AJUSTAR TEMPLATE
####################################################################################

def patch_template_imports_v1(content: str) -> str:
    import_line = '{% from "macros/admin_subprocess_v2.html" import render_admin_subprocess_v2_state %}'

    if import_line in content:
        return content

    anchor = '{% from "macros/admin_subprocess.html" import render_admin_subprocess_state %}\n'

    if anchor not in content:
        raise RuntimeError("Nao encontrei import de macro admin_subprocess.html.")

    return content.replace(anchor, anchor + import_line + "\n", 1)


def patch_template_assets_v1(content: str) -> str:
    css_line = '<link rel="stylesheet" href="/static/css/modules/admin_subprocesses_v2.css?v=20260506-entidade-v2-users-new-v2">'
    js_line = '<script src="/static/js/modules/admin_subprocesses_v2.js?v=20260506-entidade-v2-users-new-v2" defer></script>'
    integration_line = '<script src="/static/js/modules/admin_subprocesses_v2_integration.js?v=20260506-entidade-v2-users-new-v2" defer></script>'

    if "admin_subprocesses_v2.css" not in content:
        head_anchor = "{% block head_extra %}\n"

        if head_anchor not in content:
            raise RuntimeError("Nao encontrei bloco head_extra no template.")

        content = content.replace(head_anchor, head_anchor + css_line + "\n", 1)
    else:
        content = re.sub(
            r'<link rel="stylesheet" href="/static/css/modules/admin_subprocesses_v2\.css\?v=[^"]+">',
            css_line,
            content,
            count=1,
        )

    if "admin_subprocesses_v2.js" not in content:
        content = content.replace("{% endblock %}", "  " + js_line + "\n{% endblock %}", 1)
    else:
        content = re.sub(
            r'<script src="/static/js/modules/admin_subprocesses_v2\.js\?v=[^"]+" defer></script>',
            js_line,
            content,
            count=1,
        )

    if "admin_subprocesses_v2_integration.js" not in content:
        content = content.replace(js_line, js_line + "\n  " + integration_line, 1)
    else:
        content = re.sub(
            r'<script src="/static/js/modules/admin_subprocesses_v2_integration\.js\?v=[^"]+" defer></script>',
            integration_line,
            content,
            count=1,
        )

    return content


def patch_template_render_block_v1(content: str) -> str:
    start_marker = "<!-- APPVERBO_ADMIN_ENTIDADE_V2_USERS_NEW_START -->"
    end_marker = "<!-- APPVERBO_ADMIN_ENTIDADE_V2_USERS_NEW_END -->"

    render_block = '''        <!-- APPVERBO_ADMIN_ENTIDADE_V2_USERS_NEW_START -->
        {% if admin_tab == "entidade" and admin_subprocess_state and admin_subprocess_state.config.key == "entidade" %}
          <div id="admin-entidade-v2-integrated-root" data-admin-entidade-v2-integrated="1">
            {{ render_admin_subprocess_v2_state(admin_subprocess_state) }}
          </div>
        {% endif %}
        <!-- APPVERBO_ADMIN_ENTIDADE_V2_USERS_NEW_END -->

'''

    if start_marker in content and end_marker in content:
        pattern = re.compile(
            re.escape(start_marker) + r".*?" + re.escape(end_marker) + r"\n\n",
            flags=re.DOTALL,
        )
        return pattern.sub(lambda _match: render_block, content)

    anchors = [
        "<!-- APPVERBO_CORRIGIR_ORDEM_ABAS_SESSOES_ADMIN_SUBPROCESS_V5_START -->",
        '<section id="dynamic-process-card"',
        '<section id="home-summary-card"',
        '<section id="perfil-pessoal-card"',
    ]

    for anchor in anchors:
        if anchor in content:
            return content.replace(anchor, render_block + anchor, 1)

    raise RuntimeError("Nao encontrei ponto seguro para inserir bloco Entidade V2 no template.")


def patch_template_v1() -> None:
    content = read_text_v1(TEMPLATE_PATH)

    content = patch_template_imports_v1(content)
    content = patch_template_assets_v1(content)
    content = patch_template_render_block_v1(content)

    required = [
        "render_admin_subprocess_v2_state",
        "admin-entidade-v2-integrated-root",
        "admin_subprocesses_v2.css?v=20260506-entidade-v2-users-new-v2",
        "admin_subprocesses_v2_integration.js?v=20260506-entidade-v2-users-new-v2",
    ]

    missing = [marker for marker in required if marker not in content]

    if missing:
        raise RuntimeError("Marcadores ausentes em new_user.html: " + ", ".join(missing))

    write_text_v1(TEMPLATE_PATH, content)


####################################################################################
# (10) CRIAR JS DE INTEGRACAO
####################################################################################

INTEGRATION_JS = r'''// APPVERBO_ADMIN_ENTIDADE_V2_USERS_NEW_START
(function setupAdminEntidadeV2UsersNewV2() {
  "use strict";

  //###################################################################################
  // (1) HELPERS
  //###################################################################################

  function hasEntidadeV2RootV2() {
    return Boolean(document.querySelector("[data-admin-entidade-v2-integrated='1']"));
  }

  function hideElementV2(element) {
    if (!element) {
      return;
    }

    element.dataset.adminEntidadeV2LegacyHidden = "1";
    element.hidden = true;
    element.style.display = "none";
  }

  //###################################################################################
  // (2) OCULTAR LEGADO DA ENTIDADE QUANDO V2 ESTIVER ATIVO
  //###################################################################################

  function hideLegacyEntidadeCardsV2() {
    if (!hasEntidadeV2RootV2()) {
      return;
    }

    const legacySelectors = [
      "#create-entity-card",
      "#edit-entity-card",
      "#entities-card",
      "#active-entities-card",
      "#inactive-entities-card",
      "#recent-entities-card",
      "#entity-list-card",
      "#entity-active-card",
      "#entity-inactive-card",
      "#entity-view-card"
    ];

    legacySelectors.forEach((selector) => {
      document.querySelectorAll(selector).forEach(hideElementV2);
    });

    document.querySelectorAll("section[id], .card[id]").forEach((element) => {
      const elementId = String(element.id || "").toLowerCase();

      if (!elementId) {
        return;
      }

      const isLegacyEntityCard = (
        elementId.includes("entity") ||
        elementId.includes("entities") ||
        elementId.includes("entidade")
      );

      if (!isLegacyEntityCard) {
        return;
      }

      if (element.closest("[data-admin-entidade-v2-integrated='1']")) {
        return;
      }

      hideElementV2(element);
    });
  }

  //###################################################################################
  // (3) GARANTIR TARGET V2 NA URL
  //###################################################################################

  function ensureEntidadeV2TargetV2() {
    if (!hasEntidadeV2RootV2()) {
      return;
    }

    try {
      const params = new URLSearchParams(window.location.search);

      if (params.get("menu") !== "administrativo" || params.get("admin_tab") !== "entidade") {
        return;
      }

      const currentTarget = params.get("target") || "";

      if (currentTarget && currentTarget.includes("admin-subprocess-v2-entidade")) {
        return;
      }

      params.set("target", "#admin-subprocess-v2-entidade");

      const cleanUrl = window.location.pathname + "?" + params.toString() + window.location.hash;

      if (window.history && typeof window.history.replaceState === "function") {
        window.history.replaceState(window.history.state, document.title, cleanUrl);
      }
    } catch (error) {
      // Ignora ambiente sem URLSearchParams.
    }
  }

  function runEntidadeV2IntegrationV2() {
    hideLegacyEntidadeCardsV2();
    ensureEntidadeV2TargetV2();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", runEntidadeV2IntegrationV2);
  } else {
    runEntidadeV2IntegrationV2();
  }

  window.setTimeout(runEntidadeV2IntegrationV2, 100);
  window.setTimeout(runEntidadeV2IntegrationV2, 400);
  window.setTimeout(runEntidadeV2IntegrationV2, 1200);
})();
// APPVERBO_ADMIN_ENTIDADE_V2_USERS_NEW_END
'''


def write_integration_js_v1() -> None:
    write_text_v1(V2_INTEGRATION_JS_PATH, INTEGRATION_JS)


####################################################################################
# (11) VALIDAR
####################################################################################

def validate_v1() -> None:
    page_content = read_text_v1(PAGE_HANDLER_PATH)
    template_content = read_text_v1(TEMPLATE_PATH)
    registry_content = read_text_v1(V2_REGISTRY_PATH)
    macro_content = read_text_v1(V2_MACRO_PATH)
    service_content = read_text_v1(V2_SERVICE_PATH)
    integration_js_content = read_text_v1(V2_INTEGRATION_JS_PATH)

    checks = [
        ("page_handler import V2", "build_admin_subprocess_state_v2" in page_content),
        ("page_handler state entidade", "APPVERBO_ADMIN_SUBPROCESS_STATE_ENTIDADE_V2_START" in page_content),
        ("page_handler target entidade", "#admin-subprocess-v2-entidade" in page_content),
        ("template macro V2", "render_admin_subprocess_v2_state" in template_content),
        ("template root V2", "admin-entidade-v2-integrated-root" in template_content),
        ("template css V2", "admin_subprocesses_v2.css?v=20260506-entidade-v2-users-new-v2" in template_content),
        ("template integration JS", "admin_subprocesses_v2_integration.js?v=20260506-entidade-v2-users-new-v2" in template_content),
        ("registry edit param", 'edit_param="entity_edit_id"' in registry_content),
        ("macro edit param", "{{ state.config.edit_param }}={{ row_key }}" in macro_content),
        ("service return url", "target=%23{config.resolved_default_target}" in service_content),
        ("integration hide legacy", "hideLegacyEntidadeCardsV2" in integration_js_content),
    ]

    failed = [label for label, ok in checks if not ok]

    if failed:
        raise RuntimeError("Validacoes falharam: " + ", ".join(failed))

    print("OK: Entidade V2 integrada no /users/new.")
    print("OK: template renderiza Admin Subprocess V2 para admin_tab=entidade.")
    print("OK: legado da Entidade e ocultado quando V2 estiver ativo.")
    print("OK: edicao usa entity_edit_id e permanece em /users/new.")


####################################################################################
# (12) EXECUCAO
####################################################################################

def main() -> None:
    validate_v2_base_exists_v1()

    files_to_backup = [
        PAGE_HANDLER_PATH,
        TEMPLATE_PATH,
        V2_REGISTRY_PATH,
        V2_SERVICE_PATH,
        V2_HANDLERS_PATH,
        V2_MACRO_PATH,
    ]

    if V2_INTEGRATION_JS_PATH.exists():
        files_to_backup.append(V2_INTEGRATION_JS_PATH)

    for path in files_to_backup:
        backup_path = backup_file_v1(path, "integrar_entidade_v2_users_new_fix_v2")
        print(f"OK: backup criado: {backup_path}")

    patch_v2_registry_v1()
    patch_v2_service_v1()
    patch_v2_handlers_v1()
    patch_v2_macro_v1()
    patch_page_handler_v1()
    patch_template_v1()
    write_integration_js_v1()
    validate_v1()

    print("OK: correcao integracao Entidade V2 concluida.")


if __name__ == "__main__":
    main()
