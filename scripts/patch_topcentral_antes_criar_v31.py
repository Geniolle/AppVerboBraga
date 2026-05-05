from pathlib import Path
import re
import sys

ROOT = Path.cwd()

TEMPLATE_PATH = ROOT / "templates" / "new_user.html"
TOP_MENU_JS_PATH = ROOT / "static" / "js" / "modules" / "top_menu_active_v1.js"
SIDEBAR_JS_PATH = ROOT / "static" / "js" / "modules" / "sidebar_sections_layout_v1.js"

NEW_SESSOES_URL = "/users/new?menu=administrativo&admin_tab=sessoes&sidebar_sections_tab=sessoes&target=admin-sidebar-sections-card#admin-sidebar-sections-card"
OLD_SESSOES_URL = "/users/new?menu=administrativo&admin_tab=contas#admin-sidebar-sections-card"

TOP_CACHE = "/static/js/modules/top_menu_active_v1.js?v=20260505-topcentral-antes-criar-v31"
SIDEBAR_CACHE = "/static/js/modules/sidebar_sections_layout_v1.js?v=20260505-topcentral-antes-criar-v31"

TOP_MARKER_START = "// APPVERBO_TOPCENTRAL_ANTES_CRIAR_V31_START"
TOP_MARKER_END = "// APPVERBO_TOPCENTRAL_ANTES_CRIAR_V31_END"

SIDEBAR_MARKER_START = "// APPVERBO_TOPCENTRAL_ANTES_CRIAR_SIDEBAR_V31_START"
SIDEBAR_MARKER_END = "// APPVERBO_TOPCENTRAL_ANTES_CRIAR_SIDEBAR_V31_END"


####################################################################################
# (1) UTILITARIOS
####################################################################################

def fail_v31(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


def read_text_v31(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text_v31(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def remove_blocks_v31(content: str, marker_family: str) -> str:
    pattern = re.compile(
        r"\n?// " + re.escape(marker_family) + r"_V\d+_START[\s\S]*?// " + re.escape(marker_family) + r"_V\d+_END\n?",
        re.S,
    )
    return pattern.sub("\n", content)


def replace_marked_block_v31(content: str, start_marker: str, end_marker: str, block: str) -> str:
    pattern = re.compile(
        re.escape(start_marker) + r"[\s\S]*?" + re.escape(end_marker),
        re.S,
    )

    if pattern.search(content):
        return pattern.sub(block.strip(), content, count=1)

    return content.rstrip() + "\n\n" + block.strip() + "\n"


def find_menu_tabs_section_v31(content: str):
    pattern = re.compile(
        r'\n?[ \t]*<section\b(?=[^>]*\bid\s*=\s*["\']menu-tabs-card["\'])[\s\S]*?</section>[ \t]*\n?',
        re.I,
    )
    return pattern.search(content)


def find_container_open_end_v31(content: str) -> int:
    main_match = re.search(
        r'<main\b(?=[^>]*\bclass\s*=\s*["\'][^"\']*\bcontent\b[^"\']*["\'])[^>]*>',
        content,
        re.I,
    )

    if not main_match:
        fail_v31('não foi encontrado <main class="content"> em templates/new_user.html')

    container_match = re.search(
        r'<div\b(?=[^>]*\bclass\s*=\s*["\'][^"\']*\bcontainer\b[^"\']*["\'])[^>]*>',
        content[main_match.end():],
        re.I,
    )

    if not container_match:
        fail_v31('não foi encontrado <div class="container"> dentro de <main class="content">')

    return main_match.end() + container_match.end()


####################################################################################
# (2) VALIDAR FICHEIROS
####################################################################################

for file_path in [TEMPLATE_PATH, TOP_MENU_JS_PATH, SIDEBAR_JS_PATH]:
    if not file_path.exists():
        fail_v31(f"ficheiro não encontrado: {file_path}")


####################################################################################
# (3) CORRIGIR TEMPLATE: TOPCENTRAL PRIMEIRO NO CONTAINER
####################################################################################

template_html = read_text_v31(TEMPLATE_PATH)

tabs_match = find_menu_tabs_section_v31(template_html)

if tabs_match:
    tabs_block = tabs_match.group(0).strip()
    template_without_tabs = template_html[:tabs_match.start()] + "\n" + template_html[tabs_match.end():]
else:
    tabs_block = '''<section id="menu-tabs-card" class="card menu-tabs-card">
          <div id="submenu-items" class="menu-tabs" role="tablist" aria-label="Abas do menu"></div>
        </section>'''
    template_without_tabs = template_html

container_open_end = find_container_open_end_v31(template_without_tabs)

template_html = (
    template_without_tabs[:container_open_end].rstrip() +
    "\n        " +
    tabs_block +
    "\n\n" +
    template_without_tabs[container_open_end:].lstrip()
)

write_text_v31(TEMPLATE_PATH, template_html)

print("OK: templates/new_user.html corrigido para TopCentral ser o primeiro card do container.")


####################################################################################
# (4) CORRIGIR TOP MENU: OBSERVADOR PERMANENTE DE ORDEM
####################################################################################

top_js = read_text_v31(TOP_MENU_JS_PATH)

top_js = remove_blocks_v31(top_js, "APPVERBO_ABAS_SUPERIORES_CONTAINER")
top_js = remove_blocks_v31(top_js, "APPVERBO_TOPCENTRAL_ANTES_CRIAR")
top_js = top_js.replace(OLD_SESSOES_URL, NEW_SESSOES_URL)

top_js = re.sub(
    r'sessoes:\s*"[^"]*admin-sidebar-sections-card[^"]*"',
    f'sessoes: "{NEW_SESSOES_URL}"',
    top_js,
    count=1,
)

if 'adminTab === "sessoes"' not in top_js:
    alvo = '    if (adminTab === "contas" && hash === "#admin-sidebar-sections-card") {'
    insercao = '''    if (adminTab === "sessoes" ||
      String(parametros.get("sidebar_sections_tab") || "").trim().toLowerCase() === "sessoes" ||
      parametros.has("sidebar_section_edit_key")) {
      return "sessoes";
    }

'''
    if alvo in top_js:
        top_js = top_js.replace(alvo, insercao + alvo, 1)

top_block = r'''// APPVERBO_TOPCENTRAL_ANTES_CRIAR_V31_START
(function () {
  "use strict";

  //###################################################################################
  // (1) ESTADO
  //###################################################################################

  let aplicandoOrdemTopCentral_v31 = false;
  let observadorTopCentral_v31 = null;
  let timerTopCentral_v31 = null;

  //###################################################################################
  // (2) LOCALIZAR ESTRUTURA CENTRAL
  //###################################################################################

  function obterMainContentTopCentral_v31() {
    return document.querySelector("main.content");
  }

  function obterContainerCentralTopCentral_v31() {
    const main = obterMainContentTopCentral_v31();

    if (!main) {
      return null;
    }

    return main.querySelector(":scope > .container") ||
      main.querySelector(".container") ||
      null;
  }

  function obterCardTopCentral_v31() {
    return document.getElementById("menu-tabs-card");
  }

  function obterContainerAbasTopCentral_v31() {
    return document.getElementById("submenu-items");
  }

  //###################################################################################
  // (3) GARANTIR TOPCENTRAL ANTES DO BOTAO CRIAR
  //###################################################################################

  function garantirTopCentralPrimeiroCard_v31() {
    if (aplicandoOrdemTopCentral_v31) {
      return;
    }

    const container = obterContainerCentralTopCentral_v31();
    const cardTopCentral = obterCardTopCentral_v31();

    if (!container || !cardTopCentral) {
      return;
    }

    aplicandoOrdemTopCentral_v31 = true;

    try {
      if (cardTopCentral.parentElement !== container) {
        container.insertBefore(cardTopCentral, container.firstElementChild || null);
      }

      if (container.firstElementChild !== cardTopCentral) {
        container.insertBefore(cardTopCentral, container.firstElementChild || null);
      }
    } finally {
      window.setTimeout(function () {
        aplicandoOrdemTopCentral_v31 = false;
      }, 0);
    }
  }

  function reagendarGarantiaTopCentral_v31() {
    if (timerTopCentral_v31) {
      window.clearTimeout(timerTopCentral_v31);
    }

    timerTopCentral_v31 = window.setTimeout(function () {
      timerTopCentral_v31 = null;
      garantirTopCentralPrimeiroCard_v31();
    }, 20);
  }

  //###################################################################################
  // (4) GARANTIR URL CORRETA DA ABA SESSOES
  //###################################################################################

  function normalizarTextoTopCentral_v31(valor) {
    return String(valor || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase();
  }

  function obterAbasSuperioresTopCentral_v31() {
    const containerAbas = obterContainerAbasTopCentral_v31();

    if (!containerAbas) {
      return [];
    }

    return Array.from(containerAbas.querySelectorAll("a, button, .submenu-item, [role='tab']"));
  }

  function obterTextoAbaTopCentral_v31(aba) {
    return normalizarTextoTopCentral_v31(aba ? aba.textContent : "");
  }

  function obterUrlSessoesTopCentral_v31() {
    return "/users/new?menu=administrativo&admin_tab=sessoes&sidebar_sections_tab=sessoes&target=admin-sidebar-sections-card#admin-sidebar-sections-card";
  }

  function tratarCliqueTopCentral_v31(event) {
    const containerAbas = obterContainerAbasTopCentral_v31();

    if (!containerAbas) {
      return;
    }

    const aba = event.target.closest("a, button, .submenu-item, [role='tab']");

    if (!aba || !containerAbas.contains(aba)) {
      return;
    }

    garantirTopCentralPrimeiroCard_v31();

    if (obterTextoAbaTopCentral_v31(aba) !== "sessoes") {
      return;
    }

    const destino = obterUrlSessoesTopCentral_v31();
    const atual = String(window.location.pathname || "") +
      String(window.location.search || "") +
      String(window.location.hash || "");

    event.preventDefault();
    event.stopPropagation();

    if (typeof event.stopImmediatePropagation === "function") {
      event.stopImmediatePropagation();
    }

    if (atual !== destino) {
      window.location.assign(destino);
    }
  }

  //###################################################################################
  // (5) OBSERVAR ALTERACOES DINAMICAS
  //###################################################################################

  function observarContainerTopCentral_v31() {
    const container = obterContainerCentralTopCentral_v31();

    if (!container || observadorTopCentral_v31) {
      return;
    }

    observadorTopCentral_v31 = new MutationObserver(function () {
      reagendarGarantiaTopCentral_v31();
    });

    observadorTopCentral_v31.observe(container, {
      childList: true,
      subtree: false
    });
  }

  //###################################################################################
  // (6) INICIALIZACAO
  //###################################################################################

  function inicializarTopCentralAntesCriar_v31() {
    document.addEventListener("click", tratarCliqueTopCentral_v31, true);

    garantirTopCentralPrimeiroCard_v31();
    observarContainerTopCentral_v31();

    window.setTimeout(garantirTopCentralPrimeiroCard_v31, 50);
    window.setTimeout(garantirTopCentralPrimeiroCard_v31, 120);
    window.setTimeout(garantirTopCentralPrimeiroCard_v31, 250);
    window.setTimeout(garantirTopCentralPrimeiroCard_v31, 500);
    window.setTimeout(garantirTopCentralPrimeiroCard_v31, 900);
    window.setTimeout(garantirTopCentralPrimeiroCard_v31, 1500);
    window.setTimeout(observarContainerTopCentral_v31, 1600);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", inicializarTopCentralAntesCriar_v31);
  } else {
    inicializarTopCentralAntesCriar_v31();
  }

  window.addEventListener("popstate", garantirTopCentralPrimeiroCard_v31);
  window.addEventListener("hashchange", garantirTopCentralPrimeiroCard_v31);
  window.addEventListener("pageshow", garantirTopCentralPrimeiroCard_v31);
})();
// APPVERBO_TOPCENTRAL_ANTES_CRIAR_V31_END'''

top_js = replace_marked_block_v31(
    top_js,
    TOP_MARKER_START,
    TOP_MARKER_END,
    top_block,
)

write_text_v31(TOP_MENU_JS_PATH, top_js)

print("OK: top_menu_active_v1.js corrigido com observador permanente V31.")


####################################################################################
# (5) CORRIGIR SIDEBAR SCRIPT: PROTECAO EXTRA
####################################################################################

sidebar_js = read_text_v31(SIDEBAR_JS_PATH)

sidebar_js = remove_blocks_v31(sidebar_js, "APPVERBO_ABAS_SUPERIORES_CONTAINER_SIDEBAR")
sidebar_js = remove_blocks_v31(sidebar_js, "APPVERBO_TOPCENTRAL_ANTES_CRIAR_SIDEBAR")
sidebar_js = sidebar_js.replace(OLD_SESSOES_URL, NEW_SESSOES_URL)

sidebar_block = r'''// APPVERBO_TOPCENTRAL_ANTES_CRIAR_SIDEBAR_V31_START
(function () {
  "use strict";

  //###################################################################################
  // (1) LOCALIZAR ESTRUTURA CENTRAL
  //###################################################################################

  function obterContainerCentralTopCentralSidebar_v31() {
    const main = document.querySelector("main.content");

    if (!main) {
      return null;
    }

    return main.querySelector(":scope > .container") ||
      main.querySelector(".container") ||
      null;
  }

  function obterCardTopCentralSidebar_v31() {
    return document.getElementById("menu-tabs-card");
  }

  //###################################################################################
  // (2) PROTEGER ORDEM DO TOPCENTRAL
  //###################################################################################

  function garantirTopCentralPrimeiroCardSidebar_v31() {
    const container = obterContainerCentralTopCentralSidebar_v31();
    const cardTopCentral = obterCardTopCentralSidebar_v31();

    if (!container || !cardTopCentral) {
      return;
    }

    if (cardTopCentral.parentElement !== container || container.firstElementChild !== cardTopCentral) {
      container.insertBefore(cardTopCentral, container.firstElementChild || null);
    }
  }

  //###################################################################################
  // (3) INICIALIZACAO
  //###################################################################################

  function inicializarProtecaoTopCentralSidebar_v31() {
    garantirTopCentralPrimeiroCardSidebar_v31();

    window.setTimeout(garantirTopCentralPrimeiroCardSidebar_v31, 80);
    window.setTimeout(garantirTopCentralPrimeiroCardSidebar_v31, 240);
    window.setTimeout(garantirTopCentralPrimeiroCardSidebar_v31, 600);
    window.setTimeout(garantirTopCentralPrimeiroCardSidebar_v31, 1200);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", inicializarProtecaoTopCentralSidebar_v31);
  } else {
    inicializarProtecaoTopCentralSidebar_v31();
  }
})();
// APPVERBO_TOPCENTRAL_ANTES_CRIAR_SIDEBAR_V31_END'''

sidebar_js = replace_marked_block_v31(
    sidebar_js,
    SIDEBAR_MARKER_START,
    SIDEBAR_MARKER_END,
    sidebar_block,
)

write_text_v31(SIDEBAR_JS_PATH, sidebar_js)

print("OK: sidebar_sections_layout_v1.js corrigido com proteção extra V31.")


####################################################################################
# (6) ATUALIZAR CACHE BUSTER
####################################################################################

for template_file in (ROOT / "templates").rglob("*.html"):
    content = read_text_v31(template_file)
    original = content

    content = re.sub(
        r"/static/js/modules/top_menu_active_v1\.js(?:\?v=[^\"']*)?",
        TOP_CACHE,
        content,
    )

    content = re.sub(
        r"/static/js/modules/sidebar_sections_layout_v1\.js(?:\?v=[^\"']*)?",
        SIDEBAR_CACHE,
        content,
    )

    if content != original:
        write_text_v31(template_file, content)
        print(f"OK: cache buster atualizado em {template_file}")


####################################################################################
# (7) VALIDAR CONTEUDO FINAL
####################################################################################

template_validado = read_text_v31(TEMPLATE_PATH)
top_validado = read_text_v31(TOP_MENU_JS_PATH)
sidebar_validado = read_text_v31(SIDEBAR_JS_PATH)

tabs_match_validado = find_menu_tabs_section_v31(template_validado)

if not tabs_match_validado:
    fail_v31("menu-tabs-card não encontrado no template.")

container_open_end_validado = find_container_open_end_v31(template_validado)

if tabs_match_validado.start() < container_open_end_validado:
    fail_v31("menu-tabs-card não ficou dentro do container central.")

conteudo_depois_container = template_validado[container_open_end_validado:tabs_match_validado.start()].strip()

if conteudo_depois_container:
    fail_v31("menu-tabs-card não ficou como primeiro elemento do container central.")

if TOP_MARKER_START not in top_validado:
    fail_v31("bloco V31 ausente em top_menu_active_v1.js.")

if SIDEBAR_MARKER_START not in sidebar_validado:
    fail_v31("bloco V31 ausente em sidebar_sections_layout_v1.js.")

if NEW_SESSOES_URL not in top_validado:
    fail_v31("URL correta de Sessões ausente em top_menu_active_v1.js.")

print("OK: validações V31 concluídas.")
