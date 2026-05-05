from pathlib import Path
import ast
import re
import sys

ROOT = Path.cwd()

AGENTS_UPPER_PATH = ROOT / "AGENTS.md"
AGENTS_TITLE_PATH = ROOT / "Agents.md"
TEMPLATE_PATH = ROOT / "templates" / "new_user.html"
PAGE_HANDLER_PATH = ROOT / "appverbo" / "routes" / "profile" / "page_handler.py"
SETTINGS_HANDLERS_PATH = ROOT / "appverbo" / "routes" / "profile" / "settings_handlers.py"
JS_PATH = ROOT / "static" / "js" / "modules" / "sidebar_sections_layout_v1.js"
CSS_PATH = ROOT / "static" / "css" / "modules" / "sidebar_sections_layout_v1.css"

AGENTS_MARKER_START = "<!-- APPVERBO_SESSOES_BACKEND_SPLIT_ENTIDADE_V22_START -->"
AGENTS_MARKER_END = "<!-- APPVERBO_SESSOES_BACKEND_SPLIT_ENTIDADE_V22_END -->"

PAGE_MARKER_START = "# APPVERBO_SESSOES_BACKEND_SPLIT_ENTIDADE_V22_START"
PAGE_MARKER_END = "# APPVERBO_SESSOES_BACKEND_SPLIT_ENTIDADE_V22_END"

TEMPLATE_MARKER_START = "<!-- APPVERBO_SESSOES_BACKEND_SPLIT_JSON_V22_START -->"
TEMPLATE_MARKER_END = "<!-- APPVERBO_SESSOES_BACKEND_SPLIT_JSON_V22_END -->"

JS_MARKER_START = "// APPVERBO_SESSOES_BACKEND_SPLIT_ENTIDADE_V22_START"
JS_MARKER_END = "// APPVERBO_SESSOES_BACKEND_SPLIT_ENTIDADE_V22_END"

CSS_MARKER_START = "/* APPVERBO_SESSOES_BACKEND_SPLIT_ENTIDADE_V22_START */"
CSS_MARKER_END = "/* APPVERBO_SESSOES_BACKEND_SPLIT_ENTIDADE_V22_END */"

JS_CACHE = "/static/js/modules/sidebar_sections_layout_v1.js?v=20260505-sessoes-backend-split-entidade-v22"
CSS_CACHE = "/static/css/modules/sidebar_sections_layout_v1.css?v=20260505-sessoes-backend-split-entidade-v22"


def fail_v22(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


####################################################################################
# (1) RESOLVER AGENTS.md
####################################################################################

def resolve_agents_path_v22() -> Path:
    if AGENTS_UPPER_PATH.exists():
        return AGENTS_UPPER_PATH

    if AGENTS_TITLE_PATH.exists():
        return AGENTS_TITLE_PATH

    AGENTS_UPPER_PATH.write_text("# AGENTS.md\n\n", encoding="utf-8")
    return AGENTS_UPPER_PATH


####################################################################################
# (2) VALIDAR FICHEIROS
####################################################################################

for file_path in [TEMPLATE_PATH, PAGE_HANDLER_PATH, SETTINGS_HANDLERS_PATH, JS_PATH, CSS_PATH]:
    if not file_path.exists():
        fail_v22(f"ficheiro não encontrado: {file_path}")


####################################################################################
# (3) ATUALIZAR AGENTS.md
####################################################################################

agents_path = resolve_agents_path_v22()
agents_content = agents_path.read_text(encoding="utf-8")

agents_rule = f"""{AGENTS_MARKER_START}
## Regra definitiva para Sessões no padrão Entidade

A aba **Sessões** deve tratar itens **Ativos** e **Inativos** no mesmo padrão do subprocesso **Entidade**.

Regras:

1. A separação entre ativos e inativos deve acontecer no backend/contexto da página.
2. A página deve receber:
   - `active_sidebar_sections`;
   - `inactive_sidebar_sections`;
   - `sidebar_section_edit_key`;
   - `sidebar_section_edit_data`.
3. O `admin_tab=sessoes` deve ser aceito no page handler, sem cair para `entidade`.
4. Quando `admin_tab=sessoes`, o target inicial deve ser `#admin-sidebar-sections-card`.
5. Quando `admin_tab=sessoes`, limpar qualquer `dynamic_process_section`, especialmente `field:entidade`.
6. A sessão com `status=inativo` ou `is_active=false` deve aparecer em **Sessões inativas**.
7. A sessão inativa não pode aparecer na lista principal **Sessões do sidebar**.
8. O card **Sessões inativas** deve existir mesmo vazio, mostrando **Sem sessões inativas.**
9. A ação **Editar** deve permanecer no fluxo dedicado de Sessões, com `sidebar_section_edit_key`, sem usar parâmetros do subprocesso Menu.
10. O backend de gravação não deve preservar `dynamic_process_section`, `settings_edit_key`, `settings_action` ou `settings_tab`.
{AGENTS_MARKER_END}"""

if AGENTS_MARKER_START in agents_content and AGENTS_MARKER_END in agents_content:
    agents_content = re.sub(
        re.escape(AGENTS_MARKER_START) + r"[\s\S]*?" + re.escape(AGENTS_MARKER_END),
        agents_rule,
        agents_content,
        count=1,
    )
else:
    agents_content = agents_content.rstrip() + "\n\n" + agents_rule + "\n"

agents_path.write_text(agents_content, encoding="utf-8")

print(f"OK: AGENTS.md atualizado em {agents_path}")


####################################################################################
# (4) REFATORAR PAGE_HANDLER PARA SEPARAR SESSOES NO BACKEND
####################################################################################

page_content = PAGE_HANDLER_PATH.read_text(encoding="utf-8-sig")

if "MENU_CONFIG_SIDEBAR_SECTIONS_KEY" not in page_content:
    old_import = """from appverbo.menu_settings import (
    MENU_MEU_PERFIL_KEY,
"""
    new_import = """from appverbo.menu_settings import (
    MENU_CONFIG_SIDEBAR_SECTIONS_KEY,
    MENU_MEU_PERFIL_KEY,
    normalize_sidebar_sections,
"""

    if old_import not in page_content:
        fail_v22("não encontrei bloco de import appverbo.menu_settings no page_handler.py.")

    page_content = page_content.replace(old_import, new_import, 1)
elif "normalize_sidebar_sections" not in page_content:
    page_content = page_content.replace(
        "MENU_CONFIG_SIDEBAR_SECTIONS_KEY,",
        "MENU_CONFIG_SIDEBAR_SECTIONS_KEY,\n    normalize_sidebar_sections,",
        1,
    )

if 'sidebar_section_edit_key: str = "",' not in page_content:
    old_param = '''    section_key: str = "",
    appverbo_after_save: str = "",
'''
    new_param = '''    section_key: str = "",
    sidebar_section_edit_key: str = "",
    appverbo_after_save: str = "",
'''

    if old_param not in page_content:
        fail_v22("não encontrei local para inserir sidebar_section_edit_key na assinatura.")

    page_content = page_content.replace(old_param, new_param, 1)

old_admin_allowed = '''    if resolved_admin_tab not in {"utilizador", "entidade", "contas", "definicoes"}:
        resolved_admin_tab = "entidade"
'''
new_admin_allowed = '''    if resolved_admin_tab not in {"utilizador", "entidade", "contas", "definicoes", "sessoes"}:
        resolved_admin_tab = "entidade"
'''

if old_admin_allowed in page_content:
    page_content = page_content.replace(old_admin_allowed, new_admin_allowed, 1)
elif '"sessoes"' not in page_content[page_content.find("resolved_admin_tab"):page_content.find("parsed_entity_edit_id")]:
    fail_v22("não consegui incluir admin_tab=sessoes.")

helper_block = f'''{PAGE_MARKER_START}

def _normalize_sidebar_section_status_for_page_v22(raw_status: object, raw_is_active: object = None) -> str:
    if raw_is_active is False:
        return "inativo"

    clean_status = str(raw_status or "").strip().lower()

    if clean_status in {{"inativo", "inactive", "0", "false", "no", "nao", "não", "off"}}:
        return "inativo"

    return "ativo"


def _sidebar_section_is_active_for_page_v22(section: dict[str, Any]) -> bool:
    if not isinstance(section, dict):
        return True

    return _normalize_sidebar_section_status_for_page_v22(
        section.get("status"),
        section.get("is_active"),
    ) == "ativo"


def _resolve_sidebar_sections_from_page_data_v22(page_data: dict[str, Any]) -> list[dict[str, Any]]:
    raw_sections = page_data.get("sidebar_section_options")

    if isinstance(raw_sections, list):
        return normalize_sidebar_sections(raw_sections)

    for menu_row in page_data.get("sidebar_menu_settings", []):
        if not isinstance(menu_row, dict):
            continue

        row_key = str(menu_row.get("key") or menu_row.get("menu_key") or "").strip().lower()

        if row_key != "administrativo":
            continue

        for possible_key in (
            MENU_CONFIG_SIDEBAR_SECTIONS_KEY,
            "sidebar_sections",
            "sections",
            "admin_sidebar_sections",
        ):
            possible_sections = menu_row.get(possible_key)

            if isinstance(possible_sections, list):
                return normalize_sidebar_sections(possible_sections)

        menu_config = menu_row.get("menu_config")

        if isinstance(menu_config, dict):
            possible_sections = menu_config.get(MENU_CONFIG_SIDEBAR_SECTIONS_KEY)

            if isinstance(possible_sections, list):
                return normalize_sidebar_sections(possible_sections)

    return []


def _split_sidebar_sections_for_page_v22(
    page_data: dict[str, Any],
    sidebar_section_edit_key: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any] | None]:
    all_sections = _resolve_sidebar_sections_from_page_data_v22(page_data)

    active_sections = [
        section
        for section in all_sections
        if _sidebar_section_is_active_for_page_v22(section)
    ]

    inactive_sections = [
        section
        for section in all_sections
        if not _sidebar_section_is_active_for_page_v22(section)
    ]

    clean_edit_key = str(sidebar_section_edit_key or "").strip().lower()
    edit_data = None

    if clean_edit_key:
        for section in all_sections:
            section_key = str(section.get("key") or "").strip().lower()

            if section_key == clean_edit_key:
                edit_data = dict(section)
                break

    return active_sections, inactive_sections, edit_data

{PAGE_MARKER_END}

'''

if PAGE_MARKER_START in page_content and PAGE_MARKER_END in page_content:
    page_content = re.sub(
        re.escape(PAGE_MARKER_START) + r"[\s\S]*?" + re.escape(PAGE_MARKER_END) + r"\n*",
        helper_block + "\n",
        page_content,
        count=1,
    )
else:
    anchor = "\n\n@router.get(\"/users/new\", response_class=HTMLResponse)\n"

    if anchor not in page_content:
        fail_v22("não encontrei âncora do @router.get('/users/new').")

    page_content = page_content.replace(anchor, "\n\n" + helper_block + anchor, 1)

if "active_sidebar_sections_v22, inactive_sidebar_sections_v22, sidebar_section_edit_data_v22" not in page_content:
    anchor = '''        user_edit_data = get_user_edit_data(
            session,
            parsed_user_edit_id,
            allowed_entity_ids=entity_permissions["allowed_entity_ids"],
        )
'''

    insert = '''        active_sidebar_sections_v22, inactive_sidebar_sections_v22, sidebar_section_edit_data_v22 = _split_sidebar_sections_for_page_v22(
            page_data,
            sidebar_section_edit_key,
        )
'''

    if anchor not in page_content:
        fail_v22("não encontrei local para calcular active/inactive sidebar sections.")

    page_content = page_content.replace(anchor, anchor + "\n" + insert, 1)

if "resolved_admin_tab == \"sessoes\"" not in page_content:
    old_context_logic = '''    if clean_dynamic_section_from_query:
        initial_dynamic_process_section = clean_dynamic_section_from_query

    is_post_save_return = str(appverbo_after_save or "").strip() == "1"
'''
    new_context_logic = '''    if clean_dynamic_section_from_query:
        initial_dynamic_process_section = clean_dynamic_section_from_query

    if resolved_admin_tab == "sessoes":
        initial_menu_target = "#admin-sidebar-sections-card"
        initial_dynamic_process_section = ""
        clean_dynamic_section_from_query = ""

    is_post_save_return = str(appverbo_after_save or "").strip() == "1"
'''

    if old_context_logic not in page_content:
        fail_v22("não encontrei bloco POST_SAVE_CONTEXT para limpar dynamic_process_section.")

    page_content = page_content.replace(old_context_logic, new_context_logic, 1)

context_anchor = '''        "admin_tab": resolved_admin_tab,
'''
context_insert = '''        "sidebar_section_edit_key": str(sidebar_section_edit_key or "").strip().lower(),
        "sidebar_section_edit_data": sidebar_section_edit_data_v22,
        "active_sidebar_sections": active_sidebar_sections_v22,
        "inactive_sidebar_sections": inactive_sidebar_sections_v22,
'''

if context_insert.strip() not in page_content:
    if context_anchor not in page_content:
        fail_v22("não encontrei local para inserir variáveis de contexto.")

    page_content = page_content.replace(context_anchor, context_insert + context_anchor, 1)

try:
    ast.parse(page_content)
except SyntaxError as exc:
    fail_v22(f"page_handler.py ficaria inválido: {exc}")

PAGE_HANDLER_PATH.write_text(page_content, encoding="utf-8")

print("OK: page_handler.py atualizado com split backend de Sessões.")


####################################################################################
# (5) CORRIGIR BACKEND DE GRAVACAO PARA NAO PRESERVAR dynamic_process_section
####################################################################################

settings_content = SETTINGS_HANDLERS_PATH.read_text(encoding="utf-8")

if '"dynamic_process_section",' not in settings_content:
    blocked_candidates = [
        '''        "settings_edit_key",
        "settings_action",
        "settings_tab",
        "sidebar_section_edit_key",
        "sidebar_section_return_url",
        "success",
        "error",
''',
        '''        "settings_edit_key",
        "settings_action",
        "settings_tab",
        "sidebar_section_edit_key",
        "sidebar_section_return_url",
        "appverbo_after_save",
        "success",
        "error",
''',
    ]

    replaced = False

    for old_block in blocked_candidates:
        if old_block in settings_content:
            new_block = old_block.replace(
                '"sidebar_section_return_url",',
                '"sidebar_section_return_url",\n        "dynamic_process_section",',
            )

            if '"appverbo_after_save",' not in new_block:
                new_block = new_block.replace(
                    '"dynamic_process_section",',
                    '"dynamic_process_section",\n        "appverbo_after_save",',
                )

            settings_content = settings_content.replace(old_block, new_block, 1)
            replaced = True
            break

    if not replaced:
        print("AVISO: não encontrei blocked_params para inserir dynamic_process_section. Pode já estar noutro formato.")

try:
    ast.parse(settings_content)
except SyntaxError as exc:
    fail_v22(f"settings_handlers.py ficaria inválido: {exc}")

SETTINGS_HANDLERS_PATH.write_text(settings_content, encoding="utf-8")

print("OK: settings_handlers.py validado.")


####################################################################################
# (6) ADICIONAR JSON BACKEND NO TEMPLATE
####################################################################################

template_content = TEMPLATE_PATH.read_text(encoding="utf-8")

template_block = f'''{TEMPLATE_MARKER_START}
        <script id="appverbo-sidebar-section-split-v22" type="application/json">{{{{
          {{
            "active": active_sidebar_sections|default([]),
            "inactive": inactive_sidebar_sections|default([]),
            "edit_key": sidebar_section_edit_key|default(""),
            "edit_data": sidebar_section_edit_data|default(none)
          }}|tojson
        }}}}</script>
        {TEMPLATE_MARKER_END}'''

if TEMPLATE_MARKER_START in template_content and TEMPLATE_MARKER_END in template_content:
    template_content = re.sub(
        re.escape(TEMPLATE_MARKER_START) + r"[\s\S]*?" + re.escape(TEMPLATE_MARKER_END),
        template_block,
        template_content,
        count=1,
    )
else:
    anchor = '<!-- APPVERBO_SIDEBAR_SECTIONS_JSON_V2_END -->'

    if anchor not in template_content:
        fail_v22("não encontrei APPVERBO_SIDEBAR_SECTIONS_JSON_V2_END no template.")

    template_content = template_content.replace(anchor, anchor + "\n" + template_block, 1)

if "static/js/modules/sidebar_sections_layout_v1.js" in template_content:
    template_content = re.sub(
        r"/static/js/modules/sidebar_sections_layout_v1\.js\?v=[^\"]+",
        JS_CACHE,
        template_content,
    )
else:
    fail_v22("não encontrei sidebar_sections_layout_v1.js no template.")

if "static/css/modules/sidebar_sections_layout_v1.css" in template_content:
    template_content = re.sub(
        r"/static/css/modules/sidebar_sections_layout_v1\.css\?v=[^\"]+",
        CSS_CACHE,
        template_content,
    )
else:
    fail_v22("não encontrei sidebar_sections_layout_v1.css no template.")

TEMPLATE_PATH.write_text(template_content, encoding="utf-8")

print("OK: template atualizado com JSON backend split V22.")


####################################################################################
# (7) ADICIONAR JS V22 PARA CONSUMIR SPLIT BACKEND
####################################################################################

js_content = JS_PATH.read_text(encoding="utf-8")

js_block = r'''// APPVERBO_SESSOES_BACKEND_SPLIT_ENTIDADE_V22_START
(function () {
  "use strict";

  //###################################################################################
  // (1) NORMALIZACAO
  //###################################################################################

  function normalizarTextoSessoesV22(valor) {
    return String(valor || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase();
  }

  function criarChaveSessoesV22(valor) {
    return normalizarTextoSessoesV22(valor)
      .replace(/[^a-z0-9]+/g, "_")
      .replace(/_+/g, "_")
      .replace(/^_+|_+$/g, "");
  }

  function estadoSessaoV22(sessao) {
    if (sessao && sessao.is_active === false) {
      return "inativo";
    }

    const status = normalizarTextoSessoesV22(
      sessao ? (sessao.status || sessao.status_label || "") : ""
    );

    if (["inativo", "inactive", "0", "false", "nao", "não", "off"].includes(status)) {
      return "inativo";
    }

    return "ativo";
  }

  function labelSistemaSessoesV22(valor, fallback) {
    const sistema = normalizarTextoSessoesV22(valor);

    if (sistema === "owner") {
      return "Owner";
    }

    if (sistema === "legado") {
      return "Legado";
    }

    return fallback || "Owner e Legado";
  }

  //###################################################################################
  // (2) LER DADOS BACKEND
  //###################################################################################

  function lerSplitBackendSessoesV22() {
    const script = document.getElementById("appverbo-sidebar-section-split-v22");

    if (!script) {
      return {
        active: [],
        inactive: [],
        edit_key: "",
        edit_data: null
      };
    }

    try {
      const parsed = JSON.parse(script.textContent || "{}");

      return {
        active: Array.isArray(parsed.active) ? parsed.active : [],
        inactive: Array.isArray(parsed.inactive) ? parsed.inactive : [],
        edit_key: parsed.edit_key || "",
        edit_data: parsed.edit_data || null
      };
    }
    catch (error) {
      console.warn("APPVERBO V22: não foi possível ler split backend de Sessões.", error);

      return {
        active: [],
        inactive: [],
        edit_key: "",
        edit_data: null
      };
    }
  }

  function normalizarSessaoV22(sessao) {
    if (!sessao || typeof sessao !== "object") {
      return null;
    }

    const label = String(sessao.label || sessao.name || sessao.title || "").trim();
    const key = criarChaveSessoesV22(sessao.key || sessao.section_key || label);

    if (!label || !key) {
      return null;
    }

    const status = estadoSessaoV22(sessao);
    const sistema = String(sessao.visibility_scope_mode || sessao.scope_mode || "all").trim() || "all";

    return {
      key: key,
      label: label,
      visibility_scope_mode: sistema,
      visibility_scope_label: sessao.visibility_scope_label || labelSistemaSessoesV22(sistema, ""),
      status: status,
      is_active: status === "ativo",
      status_label: status === "inativo" ? "Inativo" : "Ativo"
    };
  }

  //###################################################################################
  // (3) URL SEM CONTEXTO DE ENTIDADE
  //###################################################################################

  function limparUrlSessoesV22() {
    const url = new URL(window.location.href);

    const contextoSessoes = url.searchParams.get("admin_tab") === "sessoes" ||
      url.searchParams.get("sidebar_sections_tab") === "sessoes" ||
      url.searchParams.get("target") === "admin-sidebar-sections-card" ||
      url.searchParams.has("sidebar_section_edit_key") ||
      window.location.hash === "#admin-sidebar-sections-card";

    if (!contextoSessoes) {
      return;
    }

    let mudou = false;

    [
      "dynamic_process_section",
      "settings_edit_key",
      "settings_action",
      "settings_tab",
      "sidebar_section_return_url",
      "appverbo_after_save"
    ].forEach(function (parametro) {
      if (url.searchParams.has(parametro)) {
        url.searchParams.delete(parametro);
        mudou = true;
      }
    });

    if (url.searchParams.get("menu") !== "administrativo") {
      url.searchParams.set("menu", "administrativo");
      mudou = true;
    }

    if (url.searchParams.get("admin_tab") !== "sessoes") {
      url.searchParams.set("admin_tab", "sessoes");
      mudou = true;
    }

    if (url.searchParams.get("sidebar_sections_tab") !== "sessoes") {
      url.searchParams.set("sidebar_sections_tab", "sessoes");
      mudou = true;
    }

    if (url.searchParams.get("target") !== "admin-sidebar-sections-card") {
      url.searchParams.set("target", "admin-sidebar-sections-card");
      mudou = true;
    }

    if (url.hash !== "#admin-sidebar-sections-card") {
      url.hash = "admin-sidebar-sections-card";
      mudou = true;
    }

    if (mudou) {
      window.history.replaceState({}, document.title, url.pathname + url.search + url.hash);
    }
  }

  function urlEditarSessaoV22(chave) {
    const url = new URL(window.location.href);

    [
      "dynamic_process_section",
      "settings_edit_key",
      "settings_action",
      "settings_tab",
      "sidebar_section_return_url",
      "appverbo_after_save",
      "success",
      "error"
    ].forEach(function (parametro) {
      url.searchParams.delete(parametro);
    });

    url.searchParams.set("menu", "administrativo");
    url.searchParams.set("admin_tab", "sessoes");
    url.searchParams.set("sidebar_sections_tab", "sessoes");
    url.searchParams.set("target", "admin-sidebar-sections-card");
    url.searchParams.set("sidebar_section_edit_key", criarChaveSessoesV22(chave));
    url.hash = "admin-sidebar-sections-card";

    return url.pathname + url.search + url.hash;
  }

  function urlRetornoSessoesV22() {
    const url = new URL(window.location.href);

    [
      "dynamic_process_section",
      "settings_edit_key",
      "settings_action",
      "settings_tab",
      "sidebar_section_return_url",
      "sidebar_section_edit_key",
      "appverbo_after_save",
      "success",
      "error"
    ].forEach(function (parametro) {
      url.searchParams.delete(parametro);
    });

    url.searchParams.set("menu", "administrativo");
    url.searchParams.set("admin_tab", "sessoes");
    url.searchParams.set("sidebar_sections_tab", "sessoes");
    url.searchParams.set("target", "admin-sidebar-sections-card");
    url.hash = "admin-sidebar-sections-card";

    return url.pathname + url.search + url.hash;
  }

  //###################################################################################
  // (4) COMPONENTES
  //###################################################################################

  function criarBotaoAcaoSessoesV22(tipo, titulo, texto) {
    const botao = document.createElement("button");
    botao.type = "button";
    botao.className = "appverbo-sidebar-section-action-btn-v2 appverbo-sidebar-section-action-btn-v22";
    botao.dataset.sidebarSectionActionV22 = tipo;
    botao.title = titulo;
    botao.setAttribute("aria-label", titulo);
    botao.textContent = texto;
    return botao;
  }

  function criarBadgeEstadoSessoesV22(status) {
    const badge = document.createElement("span");
    badge.className = "appverbo-sidebar-section-state-badge-v2";

    if (status === "inativo") {
      badge.classList.add("appverbo-sidebar-section-state-badge-inativo-v22");
      badge.textContent = "Inativo";
    }
    else {
      badge.classList.add("appverbo-sidebar-section-state-badge-ativo-v22");
      badge.textContent = "Ativo";
    }

    return badge;
  }

  function criarLinhaSessoesV22(sessao, grupo) {
    const tr = document.createElement("tr");
    tr.className = "appverbo-sidebar-section-row-v2 appverbo-sidebar-section-row-v22";
    tr.dataset.sectionKeyV22 = sessao.key;
    tr.dataset.sectionKeyV10 = sessao.key;
    tr.dataset.sectionStatusV22 = grupo;

    const tdMenu = document.createElement("td");
    tdMenu.className = "appverbo-sidebar-section-menu-cell-v2";
    tdMenu.textContent = sessao.label;

    const tdSistema = document.createElement("td");
    tdSistema.className = "appverbo-sidebar-section-system-cell-v2";
    tdSistema.textContent = sessao.visibility_scope_label || labelSistemaSessoesV22(sessao.visibility_scope_mode, "");

    const tdEstado = document.createElement("td");
    tdEstado.className = "appverbo-sidebar-section-state-cell-v2";
    tdEstado.appendChild(criarBadgeEstadoSessoesV22(grupo));

    const tdAcoes = document.createElement("td");
    tdAcoes.className = "appverbo-sidebar-section-actions-cell-v2";

    const actions = document.createElement("div");
    actions.className = "appverbo-sidebar-section-actions-v2";

    if (grupo === "ativo") {
      actions.appendChild(criarBotaoAcaoSessoesV22("up", "Subir sessão", "↑"));
      actions.appendChild(criarBotaoAcaoSessoesV22("down", "Descer sessão", "↓"));
    }

    actions.appendChild(criarBotaoAcaoSessoesV22("view", "Visualizar detalhes", "👁"));
    actions.appendChild(criarBotaoAcaoSessoesV22("edit", "Editar sessão", "✎"));

    tdAcoes.appendChild(actions);

    tr.appendChild(tdMenu);
    tr.appendChild(tdSistema);
    tr.appendChild(tdEstado);
    tr.appendChild(tdAcoes);

    return tr;
  }

  function criarTabelaSessoesV22(sessoes, grupo) {
    const wrap = document.createElement("div");
    wrap.className = "appverbo-sidebar-sections-table-wrap-v2 appverbo-sidebar-sections-table-wrap-v22";

    const table = document.createElement("table");
    table.className = "appverbo-sidebar-sections-table-v2 appverbo-sidebar-sections-table-v22";

    const thead = document.createElement("thead");
    thead.innerHTML = "<tr><th>MENU LATERAL</th><th>SISTEMA</th><th>ESTADO</th><th>AÇÕES</th></tr>";

    const tbody = document.createElement("tbody");
    tbody.className = "appverbo-sidebar-sections-body-v2 appverbo-sidebar-sections-body-v22";
    tbody.dataset.statusGroupV22 = grupo;

    sessoes.forEach(function (sessao) {
      tbody.appendChild(criarLinhaSessoesV22(sessao, grupo));
    });

    table.appendChild(thead);
    table.appendChild(tbody);
    wrap.appendChild(table);

    return wrap;
  }

  //###################################################################################
  // (5) RENDERIZAR LISTAS A PARTIR DO BACKEND
  //###################################################################################

  function obterCardAtivasV22() {
    return document.getElementById("admin-sidebar-sections-card");
  }

  function obterOuCriarCardInativasV22(cardAtivas) {
    let cardInativas = document.getElementById("admin-sidebar-sections-inactive-card");

    if (!cardInativas) {
      cardInativas = document.createElement("section");
      cardInativas.id = "admin-sidebar-sections-inactive-card";
    }

    cardInativas.className = "card appverbo-sidebar-sections-inactive-card-v22";
    cardInativas.hidden = false;
    cardInativas.style.display = "";
    cardInativas.style.visibility = "";

    if (cardInativas.parentElement !== cardAtivas.parentElement) {
      cardAtivas.parentElement.insertBefore(cardInativas, cardAtivas.nextSibling);
    }
    else if (cardInativas.previousElementSibling !== cardAtivas) {
      cardAtivas.parentElement.insertBefore(cardInativas, cardAtivas.nextSibling);
    }

    return cardInativas;
  }

  function renderizarCardsBackendV22() {
    limparUrlSessoesV22();

    const split = lerSplitBackendSessoesV22();
    const ativas = split.active.map(normalizarSessaoV22).filter(Boolean).filter(function (sessao) {
      return sessao.status === "ativo";
    });
    const inativas = split.inactive.map(normalizarSessaoV22).filter(Boolean).filter(function (sessao) {
      return sessao.status !== "ativo" || sessao.is_active === false;
    });

    const cardAtivas = obterCardAtivasV22();

    if (!cardAtivas || !cardAtivas.parentElement) {
      return;
    }

    const cardInativas = obterOuCriarCardInativasV22(cardAtivas);

    cardAtivas.classList.add("appverbo-sidebar-sections-active-card-v22");

    const tituloAtivas = document.createElement("h2");
    tituloAtivas.className = "appverbo-sidebar-section-list-main-title-v22";
    tituloAtivas.textContent = "Sessões do sidebar";

    const descricaoAtivas = document.createElement("p");
    descricaoAtivas.className = "appverbo-sidebar-section-list-description-v22";
    descricaoAtivas.textContent = "Defina e organize apenas as sessões do menu lateral.";

    const preserveForms = Array.from(cardAtivas.querySelectorAll("form")).filter(function (form) {
      return String(form.getAttribute("action") || "").includes("/settings/menu/sidebar-sections");
    });

    cardAtivas.innerHTML = "";
    cardAtivas.appendChild(tituloAtivas);
    cardAtivas.appendChild(descricaoAtivas);

    if (ativas.length) {
      cardAtivas.appendChild(criarTabelaSessoesV22(ativas, "ativo"));
    }
    else {
      const vazioAtivas = document.createElement("p");
      vazioAtivas.className = "appverbo-sidebar-section-empty-text-v22";
      vazioAtivas.textContent = "Sem sessões ativas.";
      cardAtivas.appendChild(vazioAtivas);
    }

    preserveForms.forEach(function (form) {
      form.hidden = true;
      cardAtivas.appendChild(form);
    });

    cardInativas.innerHTML = "";

    const tituloInativas = document.createElement("h2");
    tituloInativas.className = "appverbo-sidebar-section-list-main-title-v22";
    tituloInativas.textContent = "Sessões inativas";
    cardInativas.appendChild(tituloInativas);

    if (inativas.length) {
      cardInativas.appendChild(criarTabelaSessoesV22(inativas, "inativo"));
    }
    else {
      const vazioInativas = document.createElement("p");
      vazioInativas.className = "appverbo-sidebar-section-empty-text-v22";
      vazioInativas.textContent = "Sem sessões inativas.";
      cardInativas.appendChild(vazioInativas);
    }
  }

  //###################################################################################
  // (6) EVENTOS
  //###################################################################################

  function instalarEventosSessoesV22() {
    if (window.__appverboSessoesBackendSplitEventosV22 === true) {
      return;
    }

    window.__appverboSessoesBackendSplitEventosV22 = true;

    document.addEventListener("click", function (event) {
      const botao = event.target.closest("[data-sidebar-section-action-v22]");

      if (!botao) {
        return;
      }

      const linha = botao.closest("tr.appverbo-sidebar-section-row-v22");

      if (!linha) {
        return;
      }

      const acao = botao.dataset.sidebarSectionActionV22;
      const chave = linha.dataset.sectionKeyV22 || "";
      const nome = linha.querySelector(".appverbo-sidebar-section-menu-cell-v2");
      const sistema = linha.querySelector(".appverbo-sidebar-section-system-cell-v2");
      const estado = linha.querySelector(".appverbo-sidebar-section-state-cell-v2");

      event.preventDefault();
      event.stopPropagation();
      event.stopImmediatePropagation();

      if (acao === "view") {
        alert(
          "Nome da sessão: " + (nome ? nome.textContent.trim() : "") +
          "\nSistema: " + (sistema ? sistema.textContent.trim() : "") +
          "\nEstado: " + (estado ? estado.textContent.trim() : "")
        );
        return;
      }

      if (acao === "edit") {
        window.location.href = urlEditarSessaoV22(chave);
      }
    }, true);

    document.addEventListener("submit", function (event) {
      const form = event.target;

      if (!form || !String(form.getAttribute("action") || "").includes("/settings/menu/sidebar-section-save")) {
        return;
      }

      let returnInput = form.querySelector('input[name="sidebar_section_return_url"]');

      if (!returnInput) {
        returnInput = document.createElement("input");
        returnInput.type = "hidden";
        returnInput.name = "sidebar_section_return_url";
        form.appendChild(returnInput);
      }

      returnInput.value = urlRetornoSessoesV22();
    }, true);
  }

  //###################################################################################
  // (7) INSTALAR
  //###################################################################################

  function agendarRenderSessoesV22() {
    window.setTimeout(renderizarCardsBackendV22, 80);
    window.setTimeout(renderizarCardsBackendV22, 250);
    window.setTimeout(renderizarCardsBackendV22, 700);
    window.setTimeout(renderizarCardsBackendV22, 1400);
  }

  function instalarSessoesBackendSplitV22() {
    instalarEventosSessoesV22();
    agendarRenderSessoesV22();

    document.addEventListener("click", function () {
      agendarRenderSessoesV22();
    });

    window.addEventListener("hashchange", agendarRenderSessoesV22);
    window.addEventListener("popstate", agendarRenderSessoesV22);

    const observer = new MutationObserver(function () {
      window.clearTimeout(window.__appverboSessoesBackendSplitTimerV22);
      window.__appverboSessoesBackendSplitTimerV22 = window.setTimeout(renderizarCardsBackendV22, 180);
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ["class", "hidden", "style", "aria-selected", "aria-hidden"]
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", instalarSessoesBackendSplitV22);
  }
  else {
    instalarSessoesBackendSplitV22();
  }
})();
// APPVERBO_SESSOES_BACKEND_SPLIT_ENTIDADE_V22_END
'''

if JS_MARKER_START in js_content and JS_MARKER_END in js_content:
    js_content = re.sub(
        re.escape(JS_MARKER_START) + r"[\s\S]*?" + re.escape(JS_MARKER_END),
        js_block,
        js_content,
        count=1,
    )
else:
    js_content = js_content.rstrip() + "\n\n" + js_block + "\n"

JS_PATH.write_text(js_content, encoding="utf-8")

print("OK: JS V22 aplicado.")


####################################################################################
# (8) CSS V22
####################################################################################

css_content = CSS_PATH.read_text(encoding="utf-8")

css_block = f'''{CSS_MARKER_START}

#admin-sidebar-sections-card.appverbo-sidebar-sections-active-card-v22,
#admin-sidebar-sections-inactive-card.appverbo-sidebar-sections-inactive-card-v22 {{
  display: block !important;
  visibility: visible !important;
  padding: 16px !important;
  border: 1px solid #d5dceb !important;
  border-radius: 12px !important;
  background: #ffffff !important;
  box-sizing: border-box !important;
}}

#admin-sidebar-sections-inactive-card.appverbo-sidebar-sections-inactive-card-v22 {{
  margin-top: 12px !important;
}}

.appverbo-sidebar-section-list-main-title-v22 {{
  margin: 0 0 12px !important;
  color: #12213a !important;
  font-size: 22px !important;
  font-weight: 800 !important;
}}

.appverbo-sidebar-section-list-description-v22 {{
  margin: 0 0 12px !important;
  color: #52607a !important;
  font-size: 13px !important;
}}

.appverbo-sidebar-section-empty-text-v22 {{
  margin: 0 !important;
  color: #52607a !important;
  font-size: 14px !important;
}}

.appverbo-sidebar-sections-table-wrap-v22,
.appverbo-sidebar-sections-table-v22 {{
  width: 100% !important;
}}

.appverbo-sidebar-section-row-v22 td {{
  height: 44px !important;
}}

.appverbo-sidebar-section-state-badge-inativo-v22 {{
  border-color: #f0c36d !important;
  background: #fff7e0 !important;
  color: #8a5a00 !important;
}}

.appverbo-sidebar-section-state-badge-ativo-v22 {{
  border-color: #badbcc !important;
  background: #e9f7ef !important;
  color: #0f5132 !important;
}}

{CSS_MARKER_END}'''

if CSS_MARKER_START in css_content and CSS_MARKER_END in css_content:
    css_content = re.sub(
        re.escape(CSS_MARKER_START) + r"[\s\S]*?" + re.escape(CSS_MARKER_END),
        css_block,
        css_content,
        count=1,
    )
else:
    css_content = css_content.rstrip() + "\n\n" + css_block + "\n"

CSS_PATH.write_text(css_content, encoding="utf-8")

print("OK: CSS V22 aplicado.")


####################################################################################
# (9) VALIDAR CONTEUDO
####################################################################################

agents_validado = agents_path.read_text(encoding="utf-8")
page_validado = PAGE_HANDLER_PATH.read_text(encoding="utf-8")
settings_validado = SETTINGS_HANDLERS_PATH.read_text(encoding="utf-8")
template_validado = TEMPLATE_PATH.read_text(encoding="utf-8")
js_validado = JS_PATH.read_text(encoding="utf-8")
css_validado = CSS_PATH.read_text(encoding="utf-8")

validacoes = {
    "APPVERBO_SESSOES_BACKEND_SPLIT_ENTIDADE_V22_START": agents_validado,
    "APPVERBO_SESSOES_BACKEND_SPLIT_ENTIDADE_V22_START": page_validado,
    "active_sidebar_sections_v22": page_validado,
    "inactive_sidebar_sections_v22": page_validado,
    '"sessoes"': page_validado,
    '"dynamic_process_section",': settings_validado,
    "APPVERBO_SESSOES_BACKEND_SPLIT_JSON_V22_START": template_validado,
    "appverbo-sidebar-section-split-v22": template_validado,
    "APPVERBO_SESSOES_BACKEND_SPLIT_ENTIDADE_V22_START": js_validado,
    "renderizarCardsBackendV22": js_validado,
    "Sessões inativas": js_validado,
    "APPVERBO_SESSOES_BACKEND_SPLIT_ENTIDADE_V22_START": css_validado,
    "appverbo-sidebar-sections-inactive-card-v22": css_validado,
    "20260505-sessoes-backend-split-entidade-v22": template_validado,
}

for termo, conteudo in validacoes.items():
    if termo not in conteudo:
        fail_v22(f"validação falhou, termo ausente: {termo}")

try:
    ast.parse(page_validado)
    ast.parse(settings_validado)
except SyntaxError as exc:
    fail_v22(f"Python final inválido: {exc}")

print("OK: patch_sessoes_backend_split_padrao_entidade_v22 concluído.")
