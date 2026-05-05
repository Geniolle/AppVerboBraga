from pathlib import Path
import re
import sys

ROOT = Path.cwd()

TEMPLATE_PATH = ROOT / "templates" / "new_user.html"
TOP_MENU_JS_PATH = ROOT / "static" / "js" / "modules" / "top_menu_active_v1.js"
SIDEBAR_JS_PATH = ROOT / "static" / "js" / "modules" / "sidebar_sections_layout_v1.js"

TOP_CACHE = "/static/js/modules/top_menu_active_v1.js?v=20260505-abas-container-v30"
SIDEBAR_CACHE = "/static/js/modules/sidebar_sections_layout_v1.js?v=20260505-abas-container-v30"

TOP_MARKER_START = "// APPVERBO_ABAS_SUPERIORES_CONTAINER_V30_START"
TOP_MARKER_END = "// APPVERBO_ABAS_SUPERIORES_CONTAINER_V30_END"

SIDEBAR_MARKER_START = "// APPVERBO_ABAS_SUPERIORES_CONTAINER_SIDEBAR_V30_START"
SIDEBAR_MARKER_END = "// APPVERBO_ABAS_SUPERIORES_CONTAINER_SIDEBAR_V30_END"


####################################################################################
# (1) UTILITARIOS
####################################################################################

def fail_v30(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


def read_text_v30(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text_v30(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def remove_marked_blocks_v30(content: str, start_prefix: str, end_prefix: str) -> str:
    pattern = re.compile(
        r"\n?" + re.escape(start_prefix) + r"(?:_V\d+)?_START[\s\S]*?" + re.escape(end_prefix) + r"(?:_V\d+)?_END\n?",
        re.S,
    )
    return pattern.sub("\n", content)


def replace_marked_block_v30(content: str, start_marker: str, end_marker: str, block: str) -> str:
    pattern = re.compile(
        re.escape(start_marker) + r"[\s\S]*?" + re.escape(end_marker),
        re.S,
    )

    if pattern.search(content):
        return pattern.sub(block.strip(), content, count=1)

    return content.rstrip() + "\n\n" + block.strip() + "\n"


def find_matching_close_v30(content: str, tag_name: str, start_pos: int) -> int:
    tag_pattern = re.compile(rf"</?{tag_name}\b[^>]*>", re.I)
    depth = 0

    for match in tag_pattern.finditer(content, start_pos):
        token = match.group(0)
        is_close = token.startswith("</")
        is_self_close = token.endswith("/>")

        if not is_close and not is_self_close:
            depth += 1

        if is_close:
            depth -= 1
            if depth == 0:
                return match.end()

    return -1


def find_container_open_end_v30(content: str) -> int:
    main_match = re.search(r'<main\b(?=[^>]*\bclass\s*=\s*["\'][^"\']*\bcontent\b[^"\']*["\'])[^>]*>', content, re.I)

    if not main_match:
        fail_v30('não foi encontrado <main class="content"> em templates/new_user.html')

    search_start = main_match.end()

    container_match = re.search(
        r'<div\b(?=[^>]*\bclass\s*=\s*["\'][^"\']*\bcontainer\b[^"\']*["\'])[^>]*>',
        content[search_start:],
        re.I,
    )

    if not container_match:
        fail_v30('não foi encontrado <div class="container"> dentro de <main class="content">')

    return search_start + container_match.end()


def find_menu_tabs_section_v30(content: str):
    pattern = re.compile(
        r'\n?[ \t]*<section\b(?=[^>]*\bid\s*=\s*["\']menu-tabs-card["\'])[\s\S]*?</section>[ \t]*\n?',
        re.I,
    )
    return pattern.search(content)


####################################################################################
# (2) VALIDAR FICHEIROS
####################################################################################

for file_path in [TEMPLATE_PATH, TOP_MENU_JS_PATH, SIDEBAR_JS_PATH]:
    if not file_path.exists():
        fail_v30(f"ficheiro não encontrado: {file_path}")


####################################################################################
# (3) CORRIGIR TEMPLATE: ABAS SEMPRE DENTRO DO CONTEUDO CENTRAL
####################################################################################

template_html = read_text_v30(TEMPLATE_PATH)

tabs_match = find_menu_tabs_section_v30(template_html)

if tabs_match:
    tabs_block = tabs_match.group(0).strip()
    template_without_tabs = template_html[:tabs_match.start()] + "\n" + template_html[tabs_match.end():]
else:
    tabs_block = '''<section id="menu-tabs-card" class="card menu-tabs-card">
          <div id="submenu-items" class="menu-tabs" role="tablist" aria-label="Abas do menu"></div>
        </section>'''
    template_without_tabs = template_html

container_open_end = find_container_open_end_v30(template_without_tabs)

template_html = (
    template_without_tabs[:container_open_end].rstrip() +
    "\n        " +
    tabs_block +
    "\n\n" +
    template_without_tabs[container_open_end:].lstrip()
)

write_text_v30(TEMPLATE_PATH, template_html)

print("OK: templates/new_user.html corrigido: menu-tabs-card dentro de main.content > .container.")


####################################################################################
# (4) CORRIGIR TOP MENU: REHOME SE O CARD SAIR DO CONTAINER
####################################################################################

top_js = read_text_v30(TOP_MENU_JS_PATH)

top_block = r'''// APPVERBO_ABAS_SUPERIORES_CONTAINER_V30_START
(function () {
  "use strict";

  //###################################################################################
  // (1) LOCALIZAR ESTRUTURA CORRETA
  //###################################################################################

  function obterContainerConteudoAbas_v30() {
    const main = document.querySelector("main.content");

    if (!main) {
      return null;
    }

    return main.querySelector(":scope > .container") ||
      main.querySelector(".container") ||
      null;
  }

  function obterCardAbasSuperiores_v30() {
    return document.getElementById("menu-tabs-card");
  }

  function obterPrimeiroCardConteudo_v30(container, cardAbas) {
    if (!container) {
      return null;
    }

    return Array.from(container.children).find(function (elemento) {
      return elemento !== cardAbas &&
        elemento.classList &&
        elemento.classList.contains("card");
    }) || null;
  }

  //###################################################################################
  // (2) GARANTIR POSICAO CORRETA
  //###################################################################################

  function garantirAbasNoContainerCentral_v30() {
    const container = obterContainerConteudoAbas_v30();
    const cardAbas = obterCardAbasSuperiores_v30();

    if (!container || !cardAbas) {
      return;
    }

    if (cardAbas.parentElement !== container) {
      container.insertBefore(cardAbas, container.firstElementChild || null);
      return;
    }

    const primeiroCard = obterPrimeiroCardConteudo_v30(container, cardAbas);

    if (primeiroCard && cardAbas.nextElementSibling !== primeiroCard) {
      container.insertBefore(cardAbas, primeiroCard);
      return;
    }

    if (!primeiroCard && container.firstElementChild !== cardAbas) {
      container.insertBefore(cardAbas, container.firstElementChild || null);
    }
  }

  //###################################################################################
  // (3) INICIALIZACAO
  //###################################################################################

  function inicializarAbasSuperioresContainer_v30() {
    garantirAbasNoContainerCentral_v30();

    window.setTimeout(garantirAbasNoContainerCentral_v30, 50);
    window.setTimeout(garantirAbasNoContainerCentral_v30, 150);
    window.setTimeout(garantirAbasNoContainerCentral_v30, 350);
    window.setTimeout(garantirAbasNoContainerCentral_v30, 800);
    window.setTimeout(garantirAbasNoContainerCentral_v30, 1400);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", inicializarAbasSuperioresContainer_v30);
  } else {
    inicializarAbasSuperioresContainer_v30();
  }

  window.addEventListener("popstate", garantirAbasNoContainerCentral_v30);
  window.addEventListener("hashchange", garantirAbasNoContainerCentral_v30);
})();
// APPVERBO_ABAS_SUPERIORES_CONTAINER_V30_END'''

top_js = replace_marked_block_v30(
    top_js,
    TOP_MARKER_START,
    TOP_MARKER_END,
    top_block,
)

write_text_v30(TOP_MENU_JS_PATH, top_js)

print("OK: top_menu_active_v1.js recebeu proteção para manter abas no container central.")


####################################################################################
# (5) CORRIGIR SIDEBAR SCRIPT: NAO REPOSICIONAR ABAS FORA DO CONTAINER
####################################################################################

sidebar_js = read_text_v30(SIDEBAR_JS_PATH)

sidebar_block = r'''// APPVERBO_ABAS_SUPERIORES_CONTAINER_SIDEBAR_V30_START
(function () {
  "use strict";

  //###################################################################################
  // (1) LOCALIZAR ESTRUTURA CORRETA
  //###################################################################################

  function obterContainerConteudoAbasSidebar_v30() {
    const main = document.querySelector("main.content");

    if (!main) {
      return null;
    }

    return main.querySelector(":scope > .container") ||
      main.querySelector(".container") ||
      null;
  }

  function obterCardAbasSuperioresSidebar_v30() {
    return document.getElementById("menu-tabs-card");
  }

  //###################################################################################
  // (2) PROTECAO FINAL
  //###################################################################################

  function garantirAbasNoContainerCentralSidebar_v30() {
    const container = obterContainerConteudoAbasSidebar_v30();
    const cardAbas = obterCardAbasSuperioresSidebar_v30();

    if (!container || !cardAbas) {
      return;
    }

    if (cardAbas.parentElement !== container) {
      container.insertBefore(cardAbas, container.firstElementChild || null);
    }
  }

  //###################################################################################
  // (3) INICIALIZACAO
  //###################################################################################

  function inicializarProtecaoAbasSidebar_v30() {
    garantirAbasNoContainerCentralSidebar_v30();

    window.setTimeout(garantirAbasNoContainerCentralSidebar_v30, 100);
    window.setTimeout(garantirAbasNoContainerCentralSidebar_v30, 400);
    window.setTimeout(garantirAbasNoContainerCentralSidebar_v30, 1000);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", inicializarProtecaoAbasSidebar_v30);
  } else {
    inicializarProtecaoAbasSidebar_v30();
  }
})();
// APPVERBO_ABAS_SUPERIORES_CONTAINER_SIDEBAR_V30_END'''

sidebar_js = replace_marked_block_v30(
    sidebar_js,
    SIDEBAR_MARKER_START,
    SIDEBAR_MARKER_END,
    sidebar_block,
)

write_text_v30(SIDEBAR_JS_PATH, sidebar_js)

print("OK: sidebar_sections_layout_v1.js recebeu proteção final do container central.")


####################################################################################
# (6) ATUALIZAR CACHE BUSTER
####################################################################################

for template_file in (ROOT / "templates").rglob("*.html"):
    content = read_text_v30(template_file)
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
        write_text_v30(template_file, content)
        print(f"OK: cache buster atualizado em {template_file}")


####################################################################################
# (7) VALIDAR ORDEM FINAL NO TEMPLATE
####################################################################################

template_validado = read_text_v30(TEMPLATE_PATH)

main_match = re.search(r'<main\b(?=[^>]*\bclass\s*=\s*["\'][^"\']*\bcontent\b[^"\']*["\'])[^>]*>', template_validado, re.I)

if not main_match:
    fail_v30('validação falhou: <main class="content"> ausente.')

container_open_end_validado = find_container_open_end_v30(template_validado)
tabs_match_validado = find_menu_tabs_section_v30(template_validado)

if not tabs_match_validado:
    fail_v30('validação falhou: menu-tabs-card ausente.')

if tabs_match_validado.start() < main_match.start():
    fail_v30('validação falhou: menu-tabs-card ficou antes da topbar/layout.')

if tabs_match_validado.start() < container_open_end_validado:
    fail_v30('validação falhou: menu-tabs-card não ficou dentro do container central.')

if "APPVERBO_ABAS_SUPERIORES_CONTAINER_V30_START" not in read_text_v30(TOP_MENU_JS_PATH):
    fail_v30("validação falhou: bloco V30 ausente em top_menu_active_v1.js.")

if "APPVERBO_ABAS_SUPERIORES_CONTAINER_SIDEBAR_V30_START" not in read_text_v30(SIDEBAR_JS_PATH):
    fail_v30("validação falhou: bloco V30 ausente em sidebar_sections_layout_v1.js.")

print("OK: validações V30 concluídas.")
