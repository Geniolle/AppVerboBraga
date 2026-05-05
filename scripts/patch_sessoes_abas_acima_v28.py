from pathlib import Path
import re
import sys

ROOT = Path.cwd()

TOP_MENU_JS_PATH = ROOT / "static" / "js" / "modules" / "top_menu_active_v1.js"
SIDEBAR_JS_PATH = ROOT / "static" / "js" / "modules" / "sidebar_sections_layout_v1.js"
TEMPLATE_PATH = ROOT / "templates" / "new_user.html"

NEW_SESSOES_URL = "/users/new?menu=administrativo&admin_tab=sessoes&sidebar_sections_tab=sessoes&target=admin-sidebar-sections-card#admin-sidebar-sections-card"
OLD_SESSOES_URL = "/users/new?menu=administrativo&admin_tab=contas#admin-sidebar-sections-card"

TOP_MARKER_START = "// APPVERBO_SESSOES_ABAS_ACIMA_V28_START"
TOP_MARKER_END = "// APPVERBO_SESSOES_ABAS_ACIMA_V28_END"

SIDEBAR_MARKER_START = "// APPVERBO_SESSOES_LEGADO_NAO_REPOSICIONAR_V28_START"
SIDEBAR_MARKER_END = "// APPVERBO_SESSOES_LEGADO_NAO_REPOSICIONAR_V28_END"

TOP_CACHE = "/static/js/modules/top_menu_active_v1.js?v=20260505-sessoes-abas-acima-v28"
SIDEBAR_CACHE = "/static/js/modules/sidebar_sections_layout_v1.js?v=20260505-sessoes-abas-acima-v28"


####################################################################################
# (1) VALIDAR FICHEIROS
####################################################################################

def fail_v28(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


for file_path in [TOP_MENU_JS_PATH, SIDEBAR_JS_PATH, TEMPLATE_PATH]:
    if not file_path.exists():
        fail_v28(f"ficheiro não encontrado: {file_path}")


####################################################################################
# (2) UTILITARIOS
####################################################################################

def read_text_v28(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text_v28(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def replace_marked_block_v28(content: str, start_marker: str, end_marker: str, block: str) -> str:
    pattern = re.compile(
        re.escape(start_marker) + r"[\s\S]*?" + re.escape(end_marker),
        re.S,
    )

    if pattern.search(content):
        return pattern.sub(block, content, count=1)

    return content.rstrip() + "\n\n" + block + "\n"


def first_existing_position_v28(content: str, terms: list[str]) -> int:
    positions = [content.find(term) for term in terms if content.find(term) >= 0]
    return min(positions) if positions else -1


####################################################################################
# (3) CORRIGIR TOP MENU
####################################################################################

top_menu_js = read_text_v28(TOP_MENU_JS_PATH)

top_menu_js = top_menu_js.replace(OLD_SESSOES_URL, NEW_SESSOES_URL)

top_menu_js = re.sub(
    r'sessoes:\s*"[^"]*admin-sidebar-sections-card[^"]*"',
    f'sessoes: "{NEW_SESSOES_URL}"',
    top_menu_js,
    count=1,
)

if 'adminTab === "sessoes"' not in top_menu_js:
    alvo = '    if (adminTab === "contas" && hash === "#admin-sidebar-sections-card") {'
    insercao = '''    if (adminTab === "sessoes" ||
      String(parametros.get("sidebar_sections_tab") || "").trim().toLowerCase() === "sessoes" ||
      parametros.has("sidebar_section_edit_key")) {
      return "sessoes";
    }

'''
    if alvo in top_menu_js:
        top_menu_js = top_menu_js.replace(alvo, insercao + alvo, 1)

top_block = r'''// APPVERBO_SESSOES_ABAS_ACIMA_V28_START
(function () {
  "use strict";

  //###################################################################################
  // (1) NORMALIZACAO
  //###################################################################################

  function normalizarTextoAbasSessoes_v6(valor) {
    return String(valor || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase();
  }

  function obterUrlAtualAbasSessoes_v6() {
    try {
      return new URL(window.location.href);
    } catch (erro) {
      return null;
    }
  }

  function estaNoAdministrativoAbasSessoes_v6() {
    const url = obterUrlAtualAbasSessoes_v6();

    if (!url) {
      return false;
    }

    return normalizarTextoAbasSessoes_v6(url.searchParams.get("menu")) === "administrativo";
  }

  function contextoSessoesNaUrlAbasSessoes_v6() {
    const url = obterUrlAtualAbasSessoes_v6();

    if (!url) {
      return false;
    }

    const adminTab = normalizarTextoAbasSessoes_v6(url.searchParams.get("admin_tab"));
    const sidebarTab = normalizarTextoAbasSessoes_v6(url.searchParams.get("sidebar_sections_tab"));
    const hash = normalizarTextoAbasSessoes_v6(window.location.hash);

    return adminTab === "sessoes" ||
      sidebarTab === "sessoes" ||
      url.searchParams.has("sidebar_section_edit_key") ||
      hash === "#admin-sidebar-sections-card" ||
      hash === "#admin-sidebar-sections-form-card";
  }

  function obterUrlSessoesCorreta_v6() {
    return "/users/new?menu=administrativo&admin_tab=sessoes&sidebar_sections_tab=sessoes&target=admin-sidebar-sections-card#admin-sidebar-sections-card";
  }

  //###################################################################################
  // (2) LOCALIZAR ABAS
  //###################################################################################

  function obterContainerAbasSessoes_v6() {
    return document.getElementById("submenu-items");
  }

  function obterCardAbasSessoes_v6() {
    return document.getElementById("menu-tabs-card");
  }

  function obterAbasSuperioresSessoes_v6() {
    const container = obterContainerAbasSessoes_v6();

    if (!container) {
      return [];
    }

    return Array.from(container.querySelectorAll("a, button, .submenu-item, [role='tab']"));
  }

  function obterTextoAbaSessoes_v6(aba) {
    return normalizarTextoAbasSessoes_v6(aba ? aba.textContent : "");
  }

  function localizarAbaSessoes_v6() {
    return obterAbasSuperioresSessoes_v6().find(function (aba) {
      return obterTextoAbaSessoes_v6(aba) === "sessoes";
    }) || null;
  }

  //###################################################################################
  // (3) GARANTIR ABAS ACIMA DO BLOCO SESSOES
  //###################################################################################

  function obterPrimeiroCardSessoes_v6() {
    return document.querySelector('[data-admin-tab-pane="sessoes"]') ||
      document.getElementById("admin-sidebar-sections-form-card") ||
      document.getElementById("admin-sidebar-sections-card") ||
      document.getElementById("admin-sidebar-sections-inactive-card");
  }

  function garantirAbasAcimaDoBlocoSessoes_v6() {
    if (!estaNoAdministrativoAbasSessoes_v6()) {
      return;
    }

    const cardAbas = obterCardAbasSessoes_v6();
    const primeiroCardSessoes = obterPrimeiroCardSessoes_v6();

    if (!cardAbas || !primeiroCardSessoes || !primeiroCardSessoes.parentElement) {
      return;
    }

    if (cardAbas.nextElementSibling !== primeiroCardSessoes) {
      primeiroCardSessoes.parentElement.insertBefore(cardAbas, primeiroCardSessoes);
    }
  }

  //###################################################################################
  // (4) ACTIVE DA ABA SESSOES
  //###################################################################################

  function aplicarActiveSessoes_v6() {
    if (!estaNoAdministrativoAbasSessoes_v6() || !contextoSessoesNaUrlAbasSessoes_v6()) {
      return;
    }

    const abaSessoes = localizarAbaSessoes_v6();

    if (!abaSessoes) {
      return;
    }

    obterAbasSuperioresSessoes_v6().forEach(function (aba) {
      aba.classList.remove("active");
      aba.classList.remove("is-active");
      aba.classList.remove("selected");
      aba.setAttribute("aria-selected", "false");
    });

    abaSessoes.classList.add("active");
    abaSessoes.setAttribute("aria-selected", "true");
  }

  //###################################################################################
  // (5) CLIQUE NA ABA SESSOES
  //###################################################################################

  function tratarCliqueAbaSessoes_v6(event) {
    if (!estaNoAdministrativoAbasSessoes_v6()) {
      return;
    }

    const container = obterContainerAbasSessoes_v6();

    if (!container) {
      return;
    }

    const aba = event.target.closest("a, button, .submenu-item, [role='tab']");

    if (!aba || !container.contains(aba)) {
      return;
    }

    if (obterTextoAbaSessoes_v6(aba) !== "sessoes") {
      return;
    }

    const destino = obterUrlSessoesCorreta_v6();
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
      return;
    }

    aplicarCorrecaoSessoesAbas_v6();
  }

  //###################################################################################
  // (6) INICIALIZACAO
  //###################################################################################

  function aplicarCorrecaoSessoesAbas_v6() {
    garantirAbasAcimaDoBlocoSessoes_v6();
    aplicarActiveSessoes_v6();
  }

  function inicializarSessoesAbasAcima_v6() {
    if (window.__appverboSessoesAbasAcimaV28 === "1") {
      aplicarCorrecaoSessoesAbas_v6();
      return;
    }

    window.__appverboSessoesAbasAcimaV28 = "1";

    document.addEventListener("click", tratarCliqueAbaSessoes_v6, true);

    aplicarCorrecaoSessoesAbas_v6();

    window.setTimeout(aplicarCorrecaoSessoesAbas_v6, 80);
    window.setTimeout(aplicarCorrecaoSessoesAbas_v6, 180);
    window.setTimeout(aplicarCorrecaoSessoesAbas_v6, 420);
    window.setTimeout(aplicarCorrecaoSessoesAbas_v6, 820);
    window.setTimeout(aplicarCorrecaoSessoesAbas_v6, 1320);
    window.setTimeout(aplicarCorrecaoSessoesAbas_v6, 1820);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", inicializarSessoesAbasAcima_v6);
  } else {
    inicializarSessoesAbasAcima_v6();
  }

  window.addEventListener("popstate", aplicarCorrecaoSessoesAbas_v6);
  window.addEventListener("hashchange", aplicarCorrecaoSessoesAbas_v6);
})();
// APPVERBO_SESSOES_ABAS_ACIMA_V28_END'''

top_menu_js = replace_marked_block_v28(
    top_menu_js,
    TOP_MARKER_START,
    TOP_MARKER_END,
    top_block,
)

write_text_v28(TOP_MENU_JS_PATH, top_menu_js)

print("OK: top_menu_active_v1.js corrigido.")


####################################################################################
# (4) CORRIGIR SIDEBAR LEGADO
####################################################################################

sidebar_js = read_text_v28(SIDEBAR_JS_PATH)

sidebar_js = sidebar_js.replace(OLD_SESSOES_URL, NEW_SESSOES_URL)

guard_obter = '''function obterOuCriarCardCriacaoSessoes_v3(cardLista) {
    if (document.getElementById("admin-sidebar-sections-form-card") ||
      document.querySelector('[data-admin-tab-pane="sessoes"]')) {
      return null;
    }

'''

if "function obterOuCriarCardCriacaoSessoes_v3(cardLista) {" in sidebar_js and "APPVERBO_GUARD_OBTER_CARD_CRIACAO_SESSOES_V28" not in sidebar_js:
    sidebar_js = sidebar_js.replace(
        "function obterOuCriarCardCriacaoSessoes_v3(cardLista) {\n",
        '''function obterOuCriarCardCriacaoSessoes_v3(cardLista) {
    // APPVERBO_GUARD_OBTER_CARD_CRIACAO_SESSOES_V28
    if (document.getElementById("admin-sidebar-sections-form-card") ||
      document.querySelector('[data-admin-tab-pane="sessoes"]')) {
      return null;
    }

''',
        1,
    )

if "function moverBlocoCriacaoParaCardSeparadoSessoes_v3(cardLista, wrapper) {" in sidebar_js and "APPVERBO_GUARD_MOVER_CARD_CRIACAO_SESSOES_V28" not in sidebar_js:
    sidebar_js = sidebar_js.replace(
        "function moverBlocoCriacaoParaCardSeparadoSessoes_v3(cardLista, wrapper) {\n",
        '''function moverBlocoCriacaoParaCardSeparadoSessoes_v3(cardLista, wrapper) {
    // APPVERBO_GUARD_MOVER_CARD_CRIACAO_SESSOES_V28
    if (document.getElementById("admin-sidebar-sections-form-card") ||
      document.querySelector('[data-admin-tab-pane="sessoes"]')) {
      return;
    }

''',
        1,
    )

sidebar_block = r'''// APPVERBO_SESSOES_LEGADO_NAO_REPOSICIONAR_V28_START
(function () {
  "use strict";

  //###################################################################################
  // (1) LOCALIZAR ELEMENTOS
  //###################################################################################

  function existeServerRenderSessoes_v28() {
    return Boolean(
      document.getElementById("admin-sidebar-sections-form-card") ||
      document.getElementById("admin-sidebar-sections-card") ||
      document.getElementById("admin-sidebar-sections-inactive-card") ||
      document.querySelector('[data-admin-tab-pane="sessoes"]')
    );
  }

  function obterCardAbasSessoes_v28() {
    return document.getElementById("menu-tabs-card");
  }

  function obterPrimeiroCardSessoes_v28() {
    return document.querySelector('[data-admin-tab-pane="sessoes"]') ||
      document.getElementById("admin-sidebar-sections-form-card") ||
      document.getElementById("admin-sidebar-sections-card") ||
      document.getElementById("admin-sidebar-sections-inactive-card");
  }

  //###################################################################################
  // (2) REMOVER CARD LEGADO
  //###################################################################################

  function removerCardCriacaoLegadoSessoes_v28() {
    if (!existeServerRenderSessoes_v28()) {
      return;
    }

    const cardLegado = document.getElementById("admin-sidebar-sections-create-card");

    if (cardLegado) {
      cardLegado.remove();
    }
  }

  //###################################################################################
  // (3) GARANTIR ORDEM VISUAL
  //###################################################################################

  function garantirOrdemVisualSessoes_v28() {
    const cardAbas = obterCardAbasSessoes_v28();
    const primeiroCardSessoes = obterPrimeiroCardSessoes_v28();

    if (!cardAbas || !primeiroCardSessoes || !primeiroCardSessoes.parentElement) {
      return;
    }

    if (cardAbas.nextElementSibling !== primeiroCardSessoes) {
      primeiroCardSessoes.parentElement.insertBefore(cardAbas, primeiroCardSessoes);
    }
  }

  //###################################################################################
  // (4) INICIALIZACAO
  //###################################################################################

  function inicializarSessoesLegadoNaoReposicionar_v28() {
    removerCardCriacaoLegadoSessoes_v28();
    garantirOrdemVisualSessoes_v28();

    window.setTimeout(removerCardCriacaoLegadoSessoes_v28, 120);
    window.setTimeout(garantirOrdemVisualSessoes_v28, 140);
    window.setTimeout(removerCardCriacaoLegadoSessoes_v28, 520);
    window.setTimeout(garantirOrdemVisualSessoes_v28, 540);
    window.setTimeout(removerCardCriacaoLegadoSessoes_v28, 1220);
    window.setTimeout(garantirOrdemVisualSessoes_v28, 1240);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", inicializarSessoesLegadoNaoReposicionar_v28);
  } else {
    inicializarSessoesLegadoNaoReposicionar_v28();
  }
})();
// APPVERBO_SESSOES_LEGADO_NAO_REPOSICIONAR_V28_END'''

sidebar_js = replace_marked_block_v28(
    sidebar_js,
    SIDEBAR_MARKER_START,
    SIDEBAR_MARKER_END,
    sidebar_block,
)

write_text_v28(SIDEBAR_JS_PATH, sidebar_js)

print("OK: sidebar_sections_layout_v1.js corrigido.")


####################################################################################
# (5) REPOSICIONAR MENU-TABS-CARD NO TEMPLATE
####################################################################################

template_html = read_text_v28(TEMPLATE_PATH)

tabs_pattern = re.compile(
    r'\n?[ \t]*<section\b(?=[^>]*\bid=["\']menu-tabs-card["\'])[\s\S]*?</section>[ \t]*\n?',
    re.I,
)

tabs_match = tabs_pattern.search(template_html)

if not tabs_match:
    fail_v28('não foi encontrado <section id="menu-tabs-card"> em templates/new_user.html')

tabs_block = tabs_match.group(0).strip()
template_sem_tabs = tabs_pattern.sub("\n", template_html, count=1)

session_patterns = [
    re.compile(r'\n?[ \t]*<section\b(?=[^>]*\bdata-admin-tab-pane=["\']sessoes["\'])', re.I),
    re.compile(r'\n?[ \t]*<section\b(?=[^>]*\bid=["\']admin-sidebar-sections-form-card["\'])', re.I),
    re.compile(r'\n?[ \t]*<section\b(?=[^>]*\bid=["\']admin-sidebar-sections-card["\'])', re.I),
    re.compile(r'\n?[ \t]*<section\b(?=[^>]*\bid=["\']admin-sidebar-sections-inactive-card["\'])', re.I),
    re.compile(r'\n?[ \t]*<!--\s*APPVERBO_SESSOES_[\s\S]*?_START\s*-->', re.I),
]

session_matches = []

for pattern in session_patterns:
    match = pattern.search(template_sem_tabs)
    if match:
        session_matches.append(match)

if not session_matches:
    fail_v28("não foi encontrado nenhum anchor real do bloco de Sessões no template.")

first_session_match = min(session_matches, key=lambda item: item.start())
insert_at = first_session_match.start()

template_html = (
    template_sem_tabs[:insert_at].rstrip() +
    "\n\n        " +
    tabs_block +
    "\n\n" +
    template_sem_tabs[insert_at:].lstrip()
)

write_text_v28(TEMPLATE_PATH, template_html)

print("OK: menu-tabs-card reposicionado antes do primeiro card de Sessões.")


####################################################################################
# (6) ATUALIZAR CACHE BUSTER DOS SCRIPTS
####################################################################################

for template_file in (ROOT / "templates").rglob("*.html"):
    content = read_text_v28(template_file)
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
        write_text_v28(template_file, content)
        print(f"OK: cache buster atualizado em {template_file}")


####################################################################################
# (7) VALIDAR CONTEUDO FINAL
####################################################################################

top_validado = read_text_v28(TOP_MENU_JS_PATH)
sidebar_validado = read_text_v28(SIDEBAR_JS_PATH)
template_validado = read_text_v28(TEMPLATE_PATH)

checks = {
    "APPVERBO_SESSOES_ABAS_ACIMA_V28_START": top_validado,
    "function inicializarSessoesAbasAcima_v6": top_validado,
    NEW_SESSOES_URL: top_validado,
    "APPVERBO_SESSOES_LEGADO_NAO_REPOSICIONAR_V28_START": sidebar_validado,
    "function inicializarSessoesLegadoNaoReposicionar_v28": sidebar_validado,
    'id="menu-tabs-card"': template_validado,
}

for term, content in checks.items():
    if term not in content:
        fail_v28(f"validação falhou, termo ausente: {term}")

pos_abas = template_validado.find('id="menu-tabs-card"')
pos_sessoes = first_existing_position_v28(
    template_validado,
    [
        'data-admin-tab-pane="sessoes"',
        'id="admin-sidebar-sections-form-card"',
        'id="admin-sidebar-sections-card"',
        'id="admin-sidebar-sections-inactive-card"',
    ],
)

if pos_abas < 0:
    fail_v28("menu-tabs-card não encontrado no template após correção.")

if pos_sessoes < 0:
    fail_v28("card de Sessões não encontrado no template após correção.")

if pos_abas > pos_sessoes:
    fail_v28("menu-tabs-card continua abaixo do bloco de Sessões.")

print("OK: validações V28 concluídas.")
