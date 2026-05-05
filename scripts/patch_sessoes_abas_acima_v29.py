from pathlib import Path
import re
import sys
import unicodedata

ROOT = Path.cwd()

TOP_MENU_JS_PATH = ROOT / "static" / "js" / "modules" / "top_menu_active_v1.js"
SIDEBAR_JS_PATH = ROOT / "static" / "js" / "modules" / "sidebar_sections_layout_v1.js"
TEMPLATE_PATH = ROOT / "templates" / "new_user.html"

NEW_SESSOES_URL = "/users/new?menu=administrativo&admin_tab=sessoes&sidebar_sections_tab=sessoes&target=admin-sidebar-sections-card#admin-sidebar-sections-card"
OLD_SESSOES_URL = "/users/new?menu=administrativo&admin_tab=contas#admin-sidebar-sections-card"

TOP_MARKER_START = "// APPVERBO_SESSOES_ABAS_ACIMA_V29_START"
TOP_MARKER_END = "// APPVERBO_SESSOES_ABAS_ACIMA_V29_END"

SIDEBAR_MARKER_START = "// APPVERBO_SESSOES_LEGADO_NAO_REPOSICIONAR_V29_START"
SIDEBAR_MARKER_END = "// APPVERBO_SESSOES_LEGADO_NAO_REPOSICIONAR_V29_END"

TOP_CACHE = "/static/js/modules/top_menu_active_v1.js?v=20260505-sessoes-abas-acima-v29"
SIDEBAR_CACHE = "/static/js/modules/sidebar_sections_layout_v1.js?v=20260505-sessoes-abas-acima-v29"


####################################################################################
# (1) VALIDAR FICHEIROS
####################################################################################

def fail_v29(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


for file_path in [TOP_MENU_JS_PATH, SIDEBAR_JS_PATH, TEMPLATE_PATH]:
    if not file_path.exists():
        fail_v29(f"ficheiro não encontrado: {file_path}")


####################################################################################
# (2) UTILITARIOS
####################################################################################

def read_text_v29(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text_v29(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def normalize_v29(value: str) -> str:
    text = str(value or "")
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return text.strip().lower()


def remove_marked_blocks_by_prefix_v29(content: str, prefix: str) -> str:
    pattern = re.compile(
        r"\n?" + re.escape(prefix) + r"_V(?:27|28|29)_START[\s\S]*?" + re.escape(prefix) + r"_V(?:27|28|29)_END\n?",
        re.S,
    )
    return pattern.sub("\n", content)


def append_marked_block_v29(content: str, block: str) -> str:
    return content.rstrip() + "\n\n" + block.strip() + "\n"


def find_menu_tabs_section_v29(content: str):
    pattern = re.compile(
        r'\n?[ \t]*<section\b(?=[^>]*\bid\s*=\s*["\']menu-tabs-card["\'])[\s\S]*?</section>[ \t]*\n?',
        re.I,
    )
    return pattern.search(content)


def iter_section_blocks_v29(content: str):
    pattern = re.compile(r'<section\b[\s\S]*?</section>', re.I)
    return list(pattern.finditer(content))


def is_sessoes_section_v29(section_html: str) -> bool:
    clean = normalize_v29(re.sub(r"<[^>]+>", " ", section_html))
    raw = section_html.lower()

    return (
        'data-admin-tab-pane="sessoes"' in raw or
        "data-admin-tab-pane='sessoes'" in raw or
        'id="admin-sidebar-sections-form-card"' in raw or
        "id='admin-sidebar-sections-form-card'" in raw or
        'id="admin-sidebar-sections-card"' in raw or
        "id='admin-sidebar-sections-card'" in raw or
        'id="admin-sidebar-sections-inactive-card"' in raw or
        "id='admin-sidebar-sections-inactive-card'" in raw or
        "sessoes ativas" in clean or
        "sessoes do sidebar" in clean or
        "sessoes inativas" in clean or
        "criar sessao" in clean or
        "editar sessao" in clean
    )


def find_first_sessoes_anchor_v29(content: str) -> int:
    positions = []

    attr_patterns = [
        r'<section\b(?=[^>]*\bdata-admin-tab-pane\s*=\s*["\']sessoes["\'])',
        r'<section\b(?=[^>]*\bid\s*=\s*["\']admin-sidebar-sections-form-card["\'])',
        r'<section\b(?=[^>]*\bid\s*=\s*["\']admin-sidebar-sections-card["\'])',
        r'<section\b(?=[^>]*\bid\s*=\s*["\']admin-sidebar-sections-inactive-card["\'])',
        r'<!--\s*APPVERBO_SESSOES_[\s\S]*?_START\s*-->',
    ]

    for pattern in attr_patterns:
        match = re.search(pattern, content, re.I)
        if match:
            positions.append(match.start())

    for section_match in iter_section_blocks_v29(content):
        if is_sessoes_section_v29(section_match.group(0)):
            positions.append(section_match.start())

    return min(positions) if positions else -1


def validate_template_order_v29(content: str) -> None:
    tabs_match = find_menu_tabs_section_v29(content)

    if not tabs_match:
        fail_v29("menu-tabs-card não encontrado no template.")

    sessoes_pos = find_first_sessoes_anchor_v29(content)

    if sessoes_pos < 0:
        diagnostics = []
        for line_no, line in enumerate(content.splitlines(), start=1):
            if "sesso" in normalize_v29(line) or "sidebar-section" in normalize_v29(line):
                diagnostics.append(f"L{line_no}: {line.strip()}")
            if len(diagnostics) >= 20:
                break

        print("DIAGNOSTICO: primeiras linhas relacionadas com Sessões/sidebar-section:")
        for item in diagnostics:
            print(item)

        fail_v29("card/bloco de Sessões não encontrado no template.")

    if tabs_match.start() > sessoes_pos:
        fail_v29("menu-tabs-card continua abaixo do bloco de Sessões.")


####################################################################################
# (3) CORRIGIR TOP MENU
####################################################################################

top_menu_js = read_text_v29(TOP_MENU_JS_PATH)

top_menu_js = remove_marked_blocks_by_prefix_v29(
    top_menu_js,
    "// APPVERBO_SESSOES_ABAS_ACIMA",
)

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

top_block = r'''// APPVERBO_SESSOES_ABAS_ACIMA_V29_START
(function () {
  "use strict";

  //###################################################################################
  // (1) NORMALIZACAO
  //###################################################################################

  function normalizarTextoAbasSessoes_v7(valor) {
    return String(valor || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase();
  }

  function obterUrlAtualAbasSessoes_v7() {
    try {
      return new URL(window.location.href);
    } catch (erro) {
      return null;
    }
  }

  function estaNoAdministrativoAbasSessoes_v7() {
    const url = obterUrlAtualAbasSessoes_v7();

    if (!url) {
      return false;
    }

    return normalizarTextoAbasSessoes_v7(url.searchParams.get("menu")) === "administrativo";
  }

  function contextoSessoesNaUrlAbasSessoes_v7() {
    const url = obterUrlAtualAbasSessoes_v7();

    if (!url) {
      return false;
    }

    const adminTab = normalizarTextoAbasSessoes_v7(url.searchParams.get("admin_tab"));
    const sidebarTab = normalizarTextoAbasSessoes_v7(url.searchParams.get("sidebar_sections_tab"));
    const hash = normalizarTextoAbasSessoes_v7(window.location.hash);

    return adminTab === "sessoes" ||
      sidebarTab === "sessoes" ||
      url.searchParams.has("sidebar_section_edit_key") ||
      hash === "#admin-sidebar-sections-card" ||
      hash === "#admin-sidebar-sections-form-card";
  }

  function obterUrlSessoesCorreta_v7() {
    return "/users/new?menu=administrativo&admin_tab=sessoes&sidebar_sections_tab=sessoes&target=admin-sidebar-sections-card#admin-sidebar-sections-card";
  }

  //###################################################################################
  // (2) LOCALIZAR ABAS
  //###################################################################################

  function obterContainerAbasSessoes_v7() {
    return document.getElementById("submenu-items");
  }

  function obterCardAbasSessoes_v7() {
    return document.getElementById("menu-tabs-card");
  }

  function obterAbasSuperioresSessoes_v7() {
    const container = obterContainerAbasSessoes_v7();

    if (!container) {
      return [];
    }

    return Array.from(container.querySelectorAll("a, button, .submenu-item, [role='tab']"));
  }

  function obterTextoAbaSessoes_v7(aba) {
    return normalizarTextoAbasSessoes_v7(aba ? aba.textContent : "");
  }

  function localizarAbaSessoes_v7() {
    return obterAbasSuperioresSessoes_v7().find(function (aba) {
      return obterTextoAbaSessoes_v7(aba) === "sessoes";
    }) || null;
  }

  //###################################################################################
  // (3) LOCALIZAR PRIMEIRO BLOCO DE SESSOES
  //###################################################################################

  function contemTextoSessoes_v7(elemento) {
    const texto = normalizarTextoAbasSessoes_v7(elemento ? elemento.textContent : "");

    return texto.indexOf("sessoes ativas") >= 0 ||
      texto.indexOf("sessoes do sidebar") >= 0 ||
      texto.indexOf("sessoes inativas") >= 0 ||
      texto.indexOf("criar sessao") >= 0 ||
      texto.indexOf("editar sessao") >= 0;
  }

  function obterPrimeiroCardSessoes_v7() {
    const porIdOuAtributo = document.querySelector('[data-admin-tab-pane="sessoes"]') ||
      document.getElementById("admin-sidebar-sections-form-card") ||
      document.getElementById("admin-sidebar-sections-card") ||
      document.getElementById("admin-sidebar-sections-inactive-card");

    if (porIdOuAtributo) {
      return porIdOuAtributo;
    }

    return Array.from(document.querySelectorAll("section.card, section, .card")).find(function (elemento) {
      return contemTextoSessoes_v7(elemento);
    }) || null;
  }

  //###################################################################################
  // (4) GARANTIR ABAS ACIMA DO BLOCO SESSOES
  //###################################################################################

  function garantirAbasAcimaDoBlocoSessoes_v7() {
    if (!estaNoAdministrativoAbasSessoes_v7()) {
      return;
    }

    const cardAbas = obterCardAbasSessoes_v7();
    const primeiroCardSessoes = obterPrimeiroCardSessoes_v7();

    if (!cardAbas || !primeiroCardSessoes || !primeiroCardSessoes.parentElement) {
      return;
    }

    if (cardAbas.nextElementSibling !== primeiroCardSessoes) {
      primeiroCardSessoes.parentElement.insertBefore(cardAbas, primeiroCardSessoes);
    }
  }

  //###################################################################################
  // (5) ACTIVE DA ABA SESSOES
  //###################################################################################

  function aplicarActiveSessoes_v7() {
    if (!estaNoAdministrativoAbasSessoes_v7() || !contextoSessoesNaUrlAbasSessoes_v7()) {
      return;
    }

    const abaSessoes = localizarAbaSessoes_v7();

    if (!abaSessoes) {
      return;
    }

    obterAbasSuperioresSessoes_v7().forEach(function (aba) {
      aba.classList.remove("active");
      aba.classList.remove("is-active");
      aba.classList.remove("selected");
      aba.setAttribute("aria-selected", "false");
    });

    abaSessoes.classList.add("active");
    abaSessoes.setAttribute("aria-selected", "true");
  }

  //###################################################################################
  // (6) CLIQUE NA ABA SESSOES
  //###################################################################################

  function tratarCliqueAbaSessoes_v7(event) {
    if (!estaNoAdministrativoAbasSessoes_v7()) {
      return;
    }

    const container = obterContainerAbasSessoes_v7();

    if (!container) {
      return;
    }

    const aba = event.target.closest("a, button, .submenu-item, [role='tab']");

    if (!aba || !container.contains(aba)) {
      return;
    }

    if (obterTextoAbaSessoes_v7(aba) !== "sessoes") {
      return;
    }

    const destino = obterUrlSessoesCorreta_v7();
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

    aplicarCorrecaoSessoesAbas_v7();
  }

  //###################################################################################
  // (7) INICIALIZACAO
  //###################################################################################

  function aplicarCorrecaoSessoesAbas_v7() {
    garantirAbasAcimaDoBlocoSessoes_v7();
    aplicarActiveSessoes_v7();
  }

  function inicializarSessoesAbasAcima_v7() {
    if (window.__appverboSessoesAbasAcimaV29 === "1") {
      aplicarCorrecaoSessoesAbas_v7();
      return;
    }

    window.__appverboSessoesAbasAcimaV29 = "1";

    document.addEventListener("click", tratarCliqueAbaSessoes_v7, true);

    aplicarCorrecaoSessoesAbas_v7();

    window.setTimeout(aplicarCorrecaoSessoesAbas_v7, 80);
    window.setTimeout(aplicarCorrecaoSessoesAbas_v7, 180);
    window.setTimeout(aplicarCorrecaoSessoesAbas_v7, 420);
    window.setTimeout(aplicarCorrecaoSessoesAbas_v7, 820);
    window.setTimeout(aplicarCorrecaoSessoesAbas_v7, 1320);
    window.setTimeout(aplicarCorrecaoSessoesAbas_v7, 1820);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", inicializarSessoesAbasAcima_v7);
  } else {
    inicializarSessoesAbasAcima_v7();
  }

  window.addEventListener("popstate", aplicarCorrecaoSessoesAbas_v7);
  window.addEventListener("hashchange", aplicarCorrecaoSessoesAbas_v7);
})();
// APPVERBO_SESSOES_ABAS_ACIMA_V29_END'''

top_menu_js = append_marked_block_v29(top_menu_js, top_block)

write_text_v29(TOP_MENU_JS_PATH, top_menu_js)

print("OK: top_menu_active_v1.js corrigido com V29.")


####################################################################################
# (4) CORRIGIR SIDEBAR LEGADO
####################################################################################

sidebar_js = read_text_v29(SIDEBAR_JS_PATH)

sidebar_js = remove_marked_blocks_by_prefix_v29(
    sidebar_js,
    "// APPVERBO_SESSOES_LEGADO_NAO_REPOSICIONAR",
)

sidebar_js = sidebar_js.replace(OLD_SESSOES_URL, NEW_SESSOES_URL)

if "function obterOuCriarCardCriacaoSessoes_v3(cardLista) {" in sidebar_js and "APPVERBO_GUARD_OBTER_CARD_CRIACAO_SESSOES_V29" not in sidebar_js:
    sidebar_js = sidebar_js.replace(
        "function obterOuCriarCardCriacaoSessoes_v3(cardLista) {\n",
        '''function obterOuCriarCardCriacaoSessoes_v3(cardLista) {
    // APPVERBO_GUARD_OBTER_CARD_CRIACAO_SESSOES_V29
    if (document.getElementById("admin-sidebar-sections-form-card") ||
      document.querySelector('[data-admin-tab-pane="sessoes"]')) {
      return null;
    }

''',
        1,
    )

if "function moverBlocoCriacaoParaCardSeparadoSessoes_v3(cardLista, wrapper) {" in sidebar_js and "APPVERBO_GUARD_MOVER_CARD_CRIACAO_SESSOES_V29" not in sidebar_js:
    sidebar_js = sidebar_js.replace(
        "function moverBlocoCriacaoParaCardSeparadoSessoes_v3(cardLista, wrapper) {\n",
        '''function moverBlocoCriacaoParaCardSeparadoSessoes_v3(cardLista, wrapper) {
    // APPVERBO_GUARD_MOVER_CARD_CRIACAO_SESSOES_V29
    if (document.getElementById("admin-sidebar-sections-form-card") ||
      document.querySelector('[data-admin-tab-pane="sessoes"]')) {
      return;
    }

''',
        1,
    )

sidebar_block = r'''// APPVERBO_SESSOES_LEGADO_NAO_REPOSICIONAR_V29_START
(function () {
  "use strict";

  //###################################################################################
  // (1) NORMALIZACAO
  //###################################################################################

  function normalizarTextoSessoesLegado_v29(valor) {
    return String(valor || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase();
  }

  //###################################################################################
  // (2) LOCALIZAR ELEMENTOS
  //###################################################################################

  function obterCardAbasSessoesLegado_v29() {
    return document.getElementById("menu-tabs-card");
  }

  function contemTextoSessoesLegado_v29(elemento) {
    const texto = normalizarTextoSessoesLegado_v29(elemento ? elemento.textContent : "");

    return texto.indexOf("sessoes ativas") >= 0 ||
      texto.indexOf("sessoes do sidebar") >= 0 ||
      texto.indexOf("sessoes inativas") >= 0 ||
      texto.indexOf("criar sessao") >= 0 ||
      texto.indexOf("editar sessao") >= 0;
  }

  function obterPrimeiroCardSessoesLegado_v29() {
    const porIdOuAtributo = document.querySelector('[data-admin-tab-pane="sessoes"]') ||
      document.getElementById("admin-sidebar-sections-form-card") ||
      document.getElementById("admin-sidebar-sections-card") ||
      document.getElementById("admin-sidebar-sections-inactive-card");

    if (porIdOuAtributo) {
      return porIdOuAtributo;
    }

    return Array.from(document.querySelectorAll("section.card, section, .card")).find(function (elemento) {
      return contemTextoSessoesLegado_v29(elemento);
    }) || null;
  }

  //###################################################################################
  // (3) REMOVER CARD LEGADO
  //###################################################################################

  function removerCardCriacaoLegadoSessoes_v29() {
    const cardLegado = document.getElementById("admin-sidebar-sections-create-card");

    if (cardLegado) {
      cardLegado.remove();
    }
  }

  //###################################################################################
  // (4) GARANTIR ORDEM VISUAL
  //###################################################################################

  function garantirOrdemVisualSessoes_v29() {
    const cardAbas = obterCardAbasSessoesLegado_v29();
    const primeiroCardSessoes = obterPrimeiroCardSessoesLegado_v29();

    if (!cardAbas || !primeiroCardSessoes || !primeiroCardSessoes.parentElement) {
      return;
    }

    if (cardAbas.nextElementSibling !== primeiroCardSessoes) {
      primeiroCardSessoes.parentElement.insertBefore(cardAbas, primeiroCardSessoes);
    }
  }

  //###################################################################################
  // (5) INICIALIZACAO
  //###################################################################################

  function inicializarSessoesLegadoNaoReposicionar_v29() {
    removerCardCriacaoLegadoSessoes_v29();
    garantirOrdemVisualSessoes_v29();

    window.setTimeout(removerCardCriacaoLegadoSessoes_v29, 120);
    window.setTimeout(garantirOrdemVisualSessoes_v29, 140);
    window.setTimeout(removerCardCriacaoLegadoSessoes_v29, 520);
    window.setTimeout(garantirOrdemVisualSessoes_v29, 540);
    window.setTimeout(removerCardCriacaoLegadoSessoes_v29, 1220);
    window.setTimeout(garantirOrdemVisualSessoes_v29, 1240);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", inicializarSessoesLegadoNaoReposicionar_v29);
  } else {
    inicializarSessoesLegadoNaoReposicionar_v29();
  }
})();
// APPVERBO_SESSOES_LEGADO_NAO_REPOSICIONAR_V29_END'''

sidebar_js = append_marked_block_v29(sidebar_js, sidebar_block)

write_text_v29(SIDEBAR_JS_PATH, sidebar_js)

print("OK: sidebar_sections_layout_v1.js corrigido com V29.")


####################################################################################
# (5) REPOSICIONAR MENU-TABS-CARD NO TEMPLATE
####################################################################################

template_html = read_text_v29(TEMPLATE_PATH)

tabs_match = find_menu_tabs_section_v29(template_html)

if not tabs_match:
    fail_v29('não foi encontrado <section id="menu-tabs-card"> em templates/new_user.html')

tabs_block = tabs_match.group(0).strip()
template_without_tabs = template_html[:tabs_match.start()] + "\n" + template_html[tabs_match.end():]

session_pos = find_first_sessoes_anchor_v29(template_without_tabs)

if session_pos < 0:
    diagnostics = []
    for line_no, line in enumerate(template_without_tabs.splitlines(), start=1):
        if "sesso" in normalize_v29(line) or "sidebar-section" in normalize_v29(line):
            diagnostics.append(f"L{line_no}: {line.strip()}")
        if len(diagnostics) >= 20:
            break

    print("DIAGNOSTICO: primeiras linhas relacionadas com Sessões/sidebar-section:")
    for item in diagnostics:
        print(item)

    fail_v29("não foi encontrado anchor real do bloco de Sessões no template.")

template_html = (
    template_without_tabs[:session_pos].rstrip() +
    "\n\n        " +
    tabs_block +
    "\n\n" +
    template_without_tabs[session_pos:].lstrip()
)

write_text_v29(TEMPLATE_PATH, template_html)

print("OK: menu-tabs-card reposicionado acima do primeiro bloco de Sessões.")


####################################################################################
# (6) ATUALIZAR CACHE BUSTER DOS SCRIPTS
####################################################################################

for template_file in (ROOT / "templates").rglob("*.html"):
    content = read_text_v29(template_file)
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
        write_text_v29(template_file, content)
        print(f"OK: cache buster atualizado em {template_file}")


####################################################################################
# (7) VALIDAR CONTEUDO FINAL
####################################################################################

top_validado = read_text_v29(TOP_MENU_JS_PATH)
sidebar_validado = read_text_v29(SIDEBAR_JS_PATH)
template_validado = read_text_v29(TEMPLATE_PATH)

checks = {
    "APPVERBO_SESSOES_ABAS_ACIMA_V29_START": top_validado,
    "function inicializarSessoesAbasAcima_v7": top_validado,
    NEW_SESSOES_URL: top_validado,
    "APPVERBO_SESSOES_LEGADO_NAO_REPOSICIONAR_V29_START": sidebar_validado,
    "function inicializarSessoesLegadoNaoReposicionar_v29": sidebar_validado,
}

for term, content in checks.items():
    if term not in content:
        fail_v29(f"validação falhou, termo ausente: {term}")

validate_template_order_v29(template_validado)

print("OK: validações V29 concluídas.")
