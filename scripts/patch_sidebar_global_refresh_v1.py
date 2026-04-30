from pathlib import Path
import ast
import re
import sys

ROOT = Path.cwd()

MENU_SETTINGS_PATH = ROOT / "appverbo" / "menu_settings.py"
SETTINGS_HANDLERS_PATH = ROOT / "appverbo" / "routes" / "profile" / "settings_handlers.py"
TEMPLATE_PATH = ROOT / "templates" / "new_user.html"
JS_PATH = ROOT / "static" / "js" / "modules" / "sidebar_global_refresh_v1.js"


def fail(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


####################################################################################
# (1) VALIDAR FICHEIROS
####################################################################################

for file_path in [MENU_SETTINGS_PATH, SETTINGS_HANDLERS_PATH, TEMPLATE_PATH]:
    if not file_path.exists():
        fail(f"ficheiro nao encontrado: {file_path}")


####################################################################################
# (2) LER FICHEIROS
####################################################################################

menu_settings = MENU_SETTINGS_PATH.read_text(encoding="utf-8")
settings_handlers = SETTINGS_HANDLERS_PATH.read_text(encoding="utf-8")
template = TEMPLATE_PATH.read_text(encoding="utf-8")


####################################################################################
# (3) ATUALIZAR menu_settings.py PARA GERAR VERSAO GLOBAL
####################################################################################

if 'MENU_CONFIG_SIDEBAR_GLOBAL_REFRESH_VERSION_KEY = "sidebar_global_refresh_version"' not in menu_settings:
    anchor = 'MENU_CONFIG_SIDEBAR_SECTIONS_KEY = "sidebar_sections"\n'
    if anchor not in menu_settings:
        fail("nao encontrei MENU_CONFIG_SIDEBAR_SECTIONS_KEY em menu_settings.py.")

    menu_settings = menu_settings.replace(
        anchor,
        anchor + 'MENU_CONFIG_SIDEBAR_GLOBAL_REFRESH_VERSION_KEY = "sidebar_global_refresh_version"\n',
        1,
    )
    print("OK: constante MENU_CONFIG_SIDEBAR_GLOBAL_REFRESH_VERSION_KEY adicionada.")
else:
    print("OK: constante global refresh ja existe.")


if 'def build_sidebar_global_refresh_version_v1(' not in menu_settings:
    helper_block = '''
# ###################################################################################
# (SIDEBAR_GLOBAL_REFRESH_V1) VERSAO GLOBAL PARA REFRESH DOS UTILIZADORES LOGADOS
# ###################################################################################

def build_sidebar_global_refresh_version_v1() -> str:
    from time import time as _appverbo_time

    return str(int(_appverbo_time() * 1000))


def get_sidebar_global_refresh_version_v1(session: Session) -> str:
    row = session.execute(
        text(
            """
            SELECT menu_config
            FROM sidebar_menu_settings
            WHERE lower(trim(menu_key)) = :menu_key
            LIMIT 1
            """
        ),
        {"menu_key": "administrativo"},
    ).mappings().one_or_none()

    if row is None:
        return ""

    try:
        menu_config = json.loads(row.get("menu_config") or "{}")
    except (TypeError, ValueError, json.JSONDecodeError):
        menu_config = {}

    if not isinstance(menu_config, dict):
        return ""

    return str(menu_config.get(MENU_CONFIG_SIDEBAR_GLOBAL_REFRESH_VERSION_KEY) or "")

'''
    insert_index = menu_settings.find("# APPVERBO_SIDEBAR_SECTIONS_UPDATE_V2_START")
    if insert_index == -1:
        menu_settings = menu_settings.rstrip() + "\n\n" + helper_block.strip() + "\n"
    else:
        menu_settings = menu_settings[:insert_index] + helper_block + menu_settings[insert_index:]

    print("OK: helpers de refresh global adicionados em menu_settings.py.")
else:
    print("OK: helpers de refresh global ja existem.")


admin_refresh_line = (
    'menu_config[MENU_CONFIG_SIDEBAR_GLOBAL_REFRESH_VERSION_KEY] = '
    'build_sidebar_global_refresh_version_v1()'
)

if admin_refresh_line not in menu_settings:
    target = '''        if clean_menu_key == "administrativo":
            menu_config[MENU_CONFIG_SIDEBAR_SECTIONS_KEY] = normalized_sections
'''
    replacement = '''        if clean_menu_key == "administrativo":
            menu_config[MENU_CONFIG_SIDEBAR_SECTIONS_KEY] = normalized_sections
            menu_config[MENU_CONFIG_SIDEBAR_GLOBAL_REFRESH_VERSION_KEY] = build_sidebar_global_refresh_version_v1()
'''

    if target not in menu_settings:
        fail("nao encontrei o bloco do menu administrativo dentro de update_sidebar_sections_v2.")

    menu_settings = menu_settings.replace(target, replacement, 1)
    print("OK: update_sidebar_sections_v2 passa a gerar nova versão global.")
else:
    print("OK: update_sidebar_sections_v2 ja gera versão global.")


####################################################################################
# (4) ATUALIZAR IMPORTS EM settings_handlers.py
####################################################################################

if "JSONResponse" not in settings_handlers:
    settings_handlers = settings_handlers.replace(
        "from fastapi.responses import HTMLResponse, RedirectResponse",
        "from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse",
        1,
    )
    print("OK: JSONResponse importado.")
else:
    print("OK: JSONResponse ja importado.")


if "get_sidebar_global_refresh_version_v1" not in settings_handlers:
    import_pattern = re.compile(
        r"from appverbo\.menu_settings import \(\n(?P<body>[\s\S]*?)\n\)",
        re.S,
    )

    match = import_pattern.search(settings_handlers)

    if not match:
        fail("nao encontrei o bloco de importacao de appverbo.menu_settings.")

    body = match.group("body").rstrip() + "\n    get_sidebar_global_refresh_version_v1,"
    settings_handlers = (
        settings_handlers[:match.start("body")]
        + body
        + settings_handlers[match.end("body"):]
    )

    print("OK: get_sidebar_global_refresh_version_v1 importado.")
else:
    print("OK: get_sidebar_global_refresh_version_v1 ja importado.")


####################################################################################
# (5) ADICIONAR ENDPOINT DE POLLING
####################################################################################

endpoint_marker_start = "# APPVERBO_SIDEBAR_GLOBAL_REFRESH_ENDPOINT_V1_START"
endpoint_marker_end = "# APPVERBO_SIDEBAR_GLOBAL_REFRESH_ENDPOINT_V1_END"

endpoint_block = f'''
{endpoint_marker_start}

# ###################################################################################
# (SIDEBAR_GLOBAL_REFRESH_ENDPOINT_V1) CONSULTAR VERSAO GLOBAL DO SIDEBAR
# ###################################################################################

@router.get("/settings/menu/sidebar-refresh-version")
def get_sidebar_refresh_version_v1(request: Request) -> JSONResponse:
    with SessionLocal() as session:
        current_user = get_current_user(request, session)

        if current_user is None:
            return JSONResponse(
                {{"authenticated": False, "version": ""}},
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        refresh_version = get_sidebar_global_refresh_version_v1(session)

        return JSONResponse(
            {{
                "authenticated": True,
                "version": refresh_version,
            }}
        )

{endpoint_marker_end}
'''

endpoint_pattern = re.compile(
    re.escape(endpoint_marker_start) + r"[\s\S]*?" + re.escape(endpoint_marker_end),
    re.S,
)

if endpoint_marker_start in settings_handlers:
    settings_handlers = endpoint_pattern.sub(endpoint_block.strip(), settings_handlers, count=1)
    print("OK: endpoint sidebar-refresh-version substituido.")
else:
    insert_before = "# APPVERBO_SIDEBAR_SECTIONS_HANDLER_V2_START"
    insert_index = settings_handlers.find(insert_before)

    if insert_index == -1:
        insert_before = '@router.post("/settings/menu/sidebar-sections"'
        insert_index = settings_handlers.find(insert_before)

    if insert_index == -1:
        settings_handlers = settings_handlers.rstrip() + "\n\n" + endpoint_block.strip() + "\n"
    else:
        settings_handlers = (
            settings_handlers[:insert_index]
            + endpoint_block.strip()
            + "\n\n"
            + settings_handlers[insert_index:]
        )

    print("OK: endpoint sidebar-refresh-version adicionado.")


####################################################################################
# (6) CRIAR JS DE REFRESH GLOBAL PARA TODOS OS LOGADOS
####################################################################################

js_content = r'''(function () {
  "use strict";

  //###################################################################################
  // (1) CONFIGURACAO
  //###################################################################################

  const POLL_INTERVAL_MS = 5000;
  const REFRESH_ENDPOINT = "/settings/menu/sidebar-refresh-version";

  let initialVersion = "";
  let initialized = false;
  let isChecking = false;
  let stopped = false;

  //###################################################################################
  // (2) VERIFICAR VERSAO GLOBAL
  //###################################################################################

  function shouldIgnoreCurrentPage() {
    const path = String(window.location.pathname || "");
    return !path.startsWith("/users/new");
  }

  function getCurrentVersion(payload) {
    if (!payload || typeof payload !== "object") {
      return "";
    }

    return String(payload.version || "").trim();
  }

  function checkRefreshVersion() {
    if (stopped || isChecking || shouldIgnoreCurrentPage()) {
      return;
    }

    isChecking = true;

    fetch(REFRESH_ENDPOINT, {
      method: "GET",
      credentials: "same-origin",
      cache: "no-store",
      headers: {
        "Accept": "application/json",
        "X-Requested-With": "fetch"
      }
    })
      .then((response) => {
        if (response.status === 401 || response.status === 403) {
          stopped = true;
          return null;
        }

        if (!response.ok) {
          return null;
        }

        return response.json();
      })
      .then((payload) => {
        if (!payload || stopped) {
          return;
        }

        const currentVersion = getCurrentVersion(payload);

        if (!currentVersion) {
          return;
        }

        if (!initialized) {
          initialized = true;
          initialVersion = currentVersion;
          return;
        }

        if (currentVersion !== initialVersion) {
          stopped = true;
          window.location.reload();
        }
      })
      .catch((error) => {
        console.warn("Falha ao verificar refresh global do sidebar:", error);
      })
      .finally(() => {
        isChecking = false;
      });
  }

  //###################################################################################
  // (3) INICIALIZAR POLLING
  //###################################################################################

  function initGlobalRefreshWatcher() {
    if (shouldIgnoreCurrentPage()) {
      return;
    }

    checkRefreshVersion();
    window.setInterval(checkRefreshVersion, POLL_INTERVAL_MS);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initGlobalRefreshWatcher);
  } else {
    initGlobalRefreshWatcher();
  }
})();
'''

JS_PATH.write_text(js_content, encoding="utf-8")
print("OK: sidebar_global_refresh_v1.js criado.")


####################################################################################
# (7) INCLUIR JS EM new_user.html
####################################################################################

script_tag = '<script src="/static/js/modules/sidebar_global_refresh_v1.js?v=20260430-sidebar-global-refresh-v1"></script>'

if "sidebar_global_refresh_v1.js" not in template:
    scripts_block_pattern = re.compile(
        r"(?P<start>\{% block scripts %\}[\s\S]*?)(?P<end>\n\{% endblock %\})",
        re.S,
    )

    match = scripts_block_pattern.search(template)

    if match:
        template = (
            template[:match.end("start")]
            + "\n  "
            + script_tag
            + template[match.end("start"):]
        )
    else:
        template = template.rstrip() + "\n\n{% block scripts %}\n  " + script_tag + "\n{% endblock %}\n"

    print("OK: sidebar_global_refresh_v1.js incluído em new_user.html.")
else:
    template = re.sub(
        r'/static/js/modules/sidebar_global_refresh_v1\.js\?v=[^"]+',
        '/static/js/modules/sidebar_global_refresh_v1.js?v=20260430-sidebar-global-refresh-v1',
        template,
    )
    print("OK: cache buster do sidebar_global_refresh_v1.js atualizado.")


####################################################################################
# (8) VALIDAR SINTAXE PYTHON
####################################################################################

try:
    ast.parse(menu_settings)
except SyntaxError as exc:
    fail(f"menu_settings.py ficaria com erro de sintaxe: {exc}")

try:
    ast.parse(settings_handlers)
except SyntaxError as exc:
    fail(f"settings_handlers.py ficaria com erro de sintaxe: {exc}")


####################################################################################
# (9) GRAVAR FICHEIROS
####################################################################################

MENU_SETTINGS_PATH.write_text(menu_settings, encoding="utf-8")
SETTINGS_HANDLERS_PATH.write_text(settings_handlers, encoding="utf-8")
TEMPLATE_PATH.write_text(template, encoding="utf-8")

print("OK: menu_settings.py atualizado.")
print("OK: settings_handlers.py atualizado.")
print("OK: new_user.html atualizado.")
print("OK: patch_sidebar_global_refresh_v1 concluido.")
