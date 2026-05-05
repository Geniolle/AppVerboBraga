from pathlib import Path
import re
import sys

ROOT = Path.cwd()

TOP_MENU_JS_PATH = ROOT / "static" / "js" / "modules" / "top_menu_active_v1.js"
SIDEBAR_JS_PATH = ROOT / "static" / "js" / "modules" / "sidebar_sections_layout_v1.js"
TEMPLATE_PATH = ROOT / "templates" / "new_user.html"

TOP_MARKER_START = "// APPVERBO_SESSOES_ABAS_ACIMA_V27_START"
TOP_MARKER_END = "// APPVERBO_SESSOES_ABAS_ACIMA_V27_END"

SIDEBAR_MARKER_START = "// APPVERBO_SESSOES_LEGADO_NAO_REPOSICIONAR_V27_START"
SIDEBAR_MARKER_END = "// APPVERBO_SESSOES_LEGADO_NAO_REPOSICIONAR_V27_END"

NEW_SESSOES_URL = "/users/new?menu=administrativo&admin_tab=sessoes&sidebar_sections_tab=sessoes&target=admin-sidebar-sections-card#admin-sidebar-sections-card"
OLD_SESSOES_URL = "/users/new?menu=administrativo&admin_tab=contas#admin-sidebar-sections-card"

TOP_CACHE = "/static/js/modules/top_menu_active_v1.js?v=20260505-sessoes-abas-acima-v27"
SIDEBAR_CACHE = "/static/js/modules/sidebar_sections_layout_v1.js?v=20260505-sessoes-abas-acima-v27"


####################################################################################
# (1) VALIDAR FICHEIROS
####################################################################################

def fail_v27(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


for file_path in [TOP_MENU_JS_PATH, SIDEBAR_JS_PATH, TEMPLATE_PATH]:
    if not file_path.exists():
        fail_v27(f"ficheiro não encontrado: {file_path}")


####################################################################################
# (2) UTILITARIOS
####################################################################################

def replace_marked_block_v27(content: str, start_marker: str, end_marker: str, block: str) -> str:
    pattern = re.compile(
        re.escape(start_marker) + r"[\s\S]*?" + re.escape(end_marker),
        re.S,
    )

    if pattern.search(content):
        return pattern.sub(block, content, count=1)

    return content.rstrip() + "\n\n" + block + "\n"


####################################################################################
# (3) CORRIGIR NAVEGACAO DA ABA SESSOES NO TOP MENU
####################################################################################

top_menu_js = TOP_MENU_JS_PATH.read_text(encoding="utf-8-sig")

top_menu_js = top_menu_js.replace(
    'sessoes: "/users/new?menu=administrativo&admin_tab=contas#admin-sidebar-sections-card"',
    'sessoes: "/users/new?menu=administrativo&admin_tab=sessoes&sidebar_sections_tab=sessoes&target=admin-sidebar-sections-card#admin-sidebar-sections-card"',
)

top_menu_js = top_menu_js.replace(OLD_SESSOES_URL, NEW_SESSOES_URL)

top_block = r'''// APPVERBO_SESSOES_ABAS_ACIMA_V27_START
(function () {
  "use strict";

  //###################################################################################
  // (1) NORMALIZACAO
  //###################################################################################

  function normalizarTextoAbasSessoes_v5(valor) {
    return String(valor || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase();
  }

  function obterUrlAtualAbasSessoes_v5() {
    try {
      return new URL(window.location.href);
    } catch (erro) {
      return null;
    }
  }

  function estaNoAdministrativoAbasSessoes_v5() {
    const url = obterUrlAtualAbasSessoes_v5();

    if (!url) {
      return false;
    }

    return normalizarTextoAbasSessoes_v5(url.searchParams.get("menu")) === "administrativo";
  }

  function urlSessaoCorretaAbasSessoes_v5() {
    return "/users/new?menu=administrativo&admin_tab=sessoes&sidebar_sections_tab=sessoes&target=admin-sidebar-sections-card#admin-sidebar-sections-card";
  }

  function contextoSessoesNaUrlAbasSessoes_v5() {
    const url = obterUrlAtualAbasSessoes_v5();

    if (!url) {
      return false;
    }

    return normalizarTextoAbasSessoes_v5(url.searchParams.get("admin_tab")) === "sessoes" ||
      normalizarTextoAbasSessoes_v5(url.searchParams.get("sidebar_sections_tab")) === "sessoes" ||
      url.searchParams.has("sidebar_section_edit_key") ||
      normalizarTextoAbasSessoes_v5(window.location.hash) === "#admin-sidebar-sections-card" ||
      normalizarTextoAbasSessoes_v5(window.location.hash) === "#admin-sidebar-sections-form-card";
  }

  //###################################################################################
  // (2) LOCALIZAR ABAS
  //###################################################################################

  function obterContainerAbasSessoes_v5() {
    return document.getElementById("submenu-items");
  }

  function obterCardAbasSessoes_v5() {
    return document.getElementById("menu-tabs-card");
  }

  function obterAbasSessoes_v5() {
    const container = obterContainerAbasSessoes_v5();

    if (!container) {
      return [];
    }

    return Array.from(container.querySelectorAll("a, button, .submenu-item, [role='tab']"));
  }

  function obterTextoAbaSessoes_v5(aba) {
    return normalizarTextoAbasSessoes_v5(aba ? aba.textContent : "");
  }

  function localizarAbaSessoes_v5() {
    return obterAbasSessoes_v5().find(function (aba) {
      return obterTextoAbaSessoes_v5(aba) === "sessoes";
    }) || null;
  }

  //###################################################################################
  // (3) ACTIVE CORRETO PARA SESSOES
  //###################################################################################

  function aplicarActiveSessoes_v5() {
    if (!estaNoAdministrativoAbasSessoes_v5() || !contextoSessoesNaUrlAbasSessoes_v5()) {
      return;
    }

    const abaSessoes = localizarAbaSessoes_v5();

    if (!abaSessoes) {
      return;
    }

    obterAbasSessoes_v5().forEach(function (aba) {
      aba.classList.remove("active");
      aba.classList.remove("is-active");
      aba.classList.remove("selected");
      aba.setAttribute("aria-selected", "false");
    });

    abaSessoes.classList.add("active");
    abaSessoes.setAttribute("aria-selected", "true");
  }

  //###################################################################################
  // (4) GARANTIR ABAS ACIMA DO BLOCO SESSOES
  //###################################################################################

  function obterPrimeiroCardSessoes_v5() {
    return document.querySelector('[data-admin-tab-pane="sessoes"]') ||
      document.getElementById("admin-sidebar-sections-form-card") ||
      document.getElementById("admin-sidebar-sections-card") ||
      document.getElementById("admin-sidebar-sections-inactive-card");
  }

  function garantirAbasAcimaDoBlocoSessoes_v5() {
    if (!estaNoAdministrativoAbasSessoes_v5()) {
      return;
    }

    const cardAbas = obterCardAbasSessoes_v5();
    const primeiroCardSessoes = obterPrimeiroCardSessoes_v5();

    if (!cardAbas || !primeiroCardSessoes || !primeiroCardSessoes.parentElement) {
      return;
    }

    if (cardAbas.compareDocumentPosition(primeiroCardSessoes) & Node.DOCUMENT_POSITION_PRECEDING) {
      primeiroCardSessoes.parentElement.insertBefore(cardAbas, primeiroCardSessoes);
    }

    if (cardAbas.nextElementSibling !== primeiroCardSessoes) {
      primeiroCardSessoes.parentElement.insertBefore(cardAbas, primeiroCardSessoes);
    }
  }

  //###################################################################################
  // (5) INTERCETAR CLIQUE EM SESSOES ANTES DO CONTROLADOR ANTIGO
  //###################################################################################

  function tratarCliqueSessoes_v5(event) {
    if (!estaNoAdministrativoAbasSessoes_v5()) {
      return;
    }

    const container = obterContainerAbasSessoes_v5();

    if (!container) {
      return;
    }

    const aba = event.target.closest("a, button, .submenu-item, [role='tab']");

    if (!aba || !container.contains(aba)) {
      return;
    }

    if (obterTextoAbaSessoes_v5(aba) !== "sessoes") {
      return;
    }

    const destino = urlSessaoCorretaAbasSessoes_v5();
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

    aplicarActiveSessoes_v5();
    garantirAbasAcimaDoBlocoSessoes_v5();
  }

  //###################################################################################
  // (6) INICIALIZACAO
  //###################################################################################

  function aplicarCorrecaoSessoes_v5() {
    garantirAbasAcimaDoBlocoSessoes_v5();
    aplicarActiveSessoes_v5();
  }

  function inicializarSessoesAbasAcima_v5() {
    if (window.__appverboSessoesAbasAcimaV27 === "1") {
      aplicarCorrecaoSessoes_v5();
      return;
    }

    window.__appverboSessoesAbasAcimaV27 = "1";

    document.addEventListener("click", tratarCliqueSessoes_v5, true);

    aplicarCorrecaoSessoes_v5();

    window.setTimeout(aplicarCorrecaoSessoes_v5, 80);
    window.setTimeout(aplicarCorrecaoSessoes_v5, 180);
    window.setTimeout(aplicarCorrecaoSessoes_v5, 420);
    window.setTimeout(aplicarCorrecaoSessoes_v5, 820);
    window.setTimeout(aplicarCorrecaoSessoes_v5, 1320);
    window.setTimeout(aplicarCorrecaoSessoes_v5, 1820);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", inicializarSessoesAbasAcima_v5);
  } else {
    inicializarSessoesAbasAcima_v5();
  }

  window.addEventListener("popstate", aplicarCorrecaoSessoes_v5);
  window.addEventListener("hashchange", aplicarCorrecaoSessoes_v5);
})();
// APPVERBO_SESSOES_ABAS_ACIMA_V27_END'''

top_menu_js = replace_marked_block_v27(
    top_menu_js,
    TOP_MARKER_START,
    TOP_MARKER_END,
    top_block,
)

TOP_MENU_JS_PATH.write_text(top_menu_js, encoding="utf-8")

print("OK: top_menu_active_v1.js corrigido para admin_tab=sessoes e abas acima.")


####################################################################################
# (4) NEUTRALIZAR URL ANTIGA E BLOCO LEGADO QUE REPOSICIONA SESSOES
####################################################################################

sidebar_js = SIDEBAR_JS_PATH.read_text(encoding="utf-8-sig")

sidebar_js = sidebar_js.replace(OLD_SESSOES_URL, NEW_SESSOES_URL)

sidebar_block = r'''// APPVERBO_SESSOES_LEGADO_NAO_REPOSICIONAR_V27_START
(function () {
  "use strict";

  //###################################################################################
  // (1) NORMALIZACAO
  //###################################################################################

  function existeServerRenderSessoes_v27() {
    return Boolean(
      document.getElementById("admin-sidebar-sections-form-card") ||
      document.getElementById("admin-sidebar-sections-card") ||
      document.querySelector('[data-admin-tab-pane="sessoes"]')
    );
  }

  function obterCardAbasSessoes_v27() {
    return document.getElementById("menu-tabs-card");
  }

  function obterPrimeiroCardSessoes_v27() {
    return document.querySelector('[data-admin-tab-pane="sessoes"]') ||
      document.getElementById("admin-sidebar-sections-form-card") ||
      document.getElementById("admin-sidebar-sections-card") ||
      document.getElementById("admin-sidebar-sections-inactive-card");
  }

  //###################################################################################
  // (2) REMOVER BLOCO ORFAO LEGADO
  //###################################################################################

  function removerCardCriacaoLegadoSessoes_v27() {
    if (!existeServerRenderSessoes_v27()) {
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

  function garantirOrdemVisualSessoes_v27() {
    const cardAbas = obterCardAbasSessoes_v27();
    const primeiroCardSessoes = obterPrimeiroCardSessoes_v27();

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

  function inicializarSessoesLegadoNaoReposicionar_v27() {
    removerCardCriacaoLegadoSessoes_v27();
    garantirOrdemVisualSessoes_v27();

    window.setTimeout(removerCardCriacaoLegadoSessoes_v27, 120);
    window.setTimeout(garantirOrdemVisualSessoes_v27, 140);
    window.setTimeout(removerCardCriacaoLegadoSessoes_v27, 520);
    window.setTimeout(garantirOrdemVisualSessoes_v27, 540);
    window.setTimeout(removerCardCriacaoLegadoSessoes_v27, 1220);
    window.setTimeout(garantirOrdemVisualSessoes_v27, 1240);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", inicializarSessoesLegadoNaoReposicionar_v27);
  } else {
    inicializarSessoesLegadoNaoReposicionar_v27();
  }
})();
// APPVERBO_SESSOES_LEGADO_NAO_REPOSICIONAR_V27_END'''

sidebar_js = replace_marked_block_v27(
    sidebar_js,
    SIDEBAR_MARKER_START,
    SIDEBAR_MARKER_END,
    sidebar_block,
)

SIDEBAR_JS_PATH.write_text(sidebar_js, encoding="utf-8")

print("OK: sidebar_sections_layout_v1.js recebeu guarda V27 contra reposicionamento legado.")


####################################################################################
# (5) ATUALIZAR CACHE BUSTER NOS TEMPLATES
####################################################################################

template_files = list((ROOT / "templates").rglob("*.html"))

for template_file in template_files:
    content = template_file.read_text(encoding="utf-8")
    original = content

    content = re.sub(
        r"/static/js/modules/top_menu_active_v1\.js\?v=[^\"]+",
        TOP_CACHE,
        content,
    )

    content = re.sub(
        r"/static/js/modules/sidebar_sections_layout_v1\.js\?v=[^\"]+",
        SIDEBAR_CACHE,
        content,
    )

    if content != original:
        template_file.write_text(content, encoding="utf-8")
        print(f"OK: cache buster atualizado em {template_file}")


####################################################################################
# (6) VALIDAR CONTEUDO
####################################################################################

top_validado = TOP_MENU_JS_PATH.read_text(encoding="utf-8")
sidebar_validado = SIDEBAR_JS_PATH.read_text(encoding="utf-8")
template_validado = TEMPLATE_PATH.read_text(encoding="utf-8")

validacoes = {
    "APPVERBO_SESSOES_ABAS_ACIMA_V27_START": top_validado,
    "function inicializarSessoesAbasAcima_v5": top_validado,
    NEW_SESSOES_URL: top_validado,
    "APPVERBO_SESSOES_LEGADO_NAO_REPOSICIONAR_V27_START": sidebar_validado,
    "function inicializarSessoesLegadoNaoReposicionar_v27": sidebar_validado,
    "menu-tabs-card": template_validado,
    "APPVERBO_SESSOES_SERVER_RENDER_IGUAL_ENTIDADE_V25_START": template_validado,
}

for termo, conteudo in validacoes.items():
    if termo not in conteudo:
        fail_v27(f"validação falhou, termo ausente: {termo}")

pos_abas = template_validado.find('id="menu-tabs-card"')
pos_sessoes = template_validado.find("APPVERBO_SESSOES_SERVER_RENDER_IGUAL_ENTIDADE_V25_START")

if pos_abas < 0 or pos_sessoes < 0 or pos_abas > pos_sessoes:
    fail_v27("a ordem do template continua incorreta: menu-tabs-card deve ficar antes do bloco de Sessões.")

if OLD_SESSOES_URL in top_validado:
    fail_v27("URL antiga de Sessões ainda existe em top_menu_active_v1.js.")

print("OK: validações V27 concluídas.")
