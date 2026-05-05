from pathlib import Path
import re
import sys

ROOT = Path.cwd()

AGENTS_UPPER_PATH = ROOT / "AGENTS.md"
AGENTS_TITLE_PATH = ROOT / "Agents.md"
TEMPLATE_PATH = ROOT / "templates" / "new_user.html"
JS_PATH = ROOT / "static" / "js" / "modules" / "sidebar_sections_layout_v1.js"
CSS_PATH = ROOT / "static" / "css" / "modules" / "sidebar_sections_layout_v1.css"

AGENTS_MARKER_START = "<!-- APPVERBO_SESSOES_INATIVAS_CARD_FORA_V15_START -->"
AGENTS_MARKER_END = "<!-- APPVERBO_SESSOES_INATIVAS_CARD_FORA_V15_END -->"

JS_MARKER_START = "// APPVERBO_SESSOES_INATIVAS_CARD_FORA_V15_START"
JS_MARKER_END = "// APPVERBO_SESSOES_INATIVAS_CARD_FORA_V15_END"

CSS_MARKER_START = "/* APPVERBO_SESSOES_INATIVAS_CARD_FORA_V15_START */"
CSS_MARKER_END = "/* APPVERBO_SESSOES_INATIVAS_CARD_FORA_V15_END */"

JS_CACHE = "/static/js/modules/sidebar_sections_layout_v1.js?v=20260505-sessoes-inativas-fora-v15"
CSS_CACHE = "/static/css/modules/sidebar_sections_layout_v1.css?v=20260505-sessoes-inativas-fora-v15"


def fail_v15(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


####################################################################################
# (1) RESOLVER AGENTS.md
####################################################################################

def resolve_agents_path_v15() -> Path:
    if AGENTS_UPPER_PATH.exists():
        return AGENTS_UPPER_PATH

    if AGENTS_TITLE_PATH.exists():
        return AGENTS_TITLE_PATH

    AGENTS_UPPER_PATH.write_text("# AGENTS.md\n\n", encoding="utf-8")
    return AGENTS_UPPER_PATH


####################################################################################
# (2) VALIDAR FICHEIROS
####################################################################################

for file_path in [TEMPLATE_PATH, JS_PATH, CSS_PATH]:
    if not file_path.exists():
        fail_v15(f"ficheiro não encontrado: {file_path}")


####################################################################################
# (3) ATUALIZAR AGENTS.md
####################################################################################

agents_path = resolve_agents_path_v15()
agents_content = agents_path.read_text(encoding="utf-8")

agents_rule = f"""{AGENTS_MARKER_START}
## Regra visual para Sessões inativas

Na aba **Sessões**, a área **Sessões inativas** deve ficar sempre em card/bloco próprio, separado abaixo do card **Sessões do sidebar**.

Regras:

1. **Sessões do sidebar** deve conter somente a listagem das sessões ativas.
2. **Sessões inativas** deve ficar em outro card abaixo, com borda, fundo e espaçamento iguais ao padrão de **Entidades inativas**.
3. Quando não houver sessões inativas, o card deve permanecer visível com a mensagem **Sem sessões inativas.**
4. O bloco de inativas não pode ficar dentro do mesmo card visual das sessões ativas.
5. Ao retornar para a aba **Sessões**, a separação em cards deve ser reaplicada automaticamente.
{AGENTS_MARKER_END}"""

if AGENTS_MARKER_START in agents_content and AGENTS_MARKER_END in agents_content:
    agents_pattern = re.compile(
        re.escape(AGENTS_MARKER_START) + r"[\s\S]*?" + re.escape(AGENTS_MARKER_END),
        re.S,
    )
    agents_content = agents_pattern.sub(agents_rule, agents_content, count=1)
else:
    agents_content = agents_content.rstrip() + "\n\n" + agents_rule + "\n"

agents_path.write_text(agents_content, encoding="utf-8")

print(f"OK: regra visual de Sessões inativas atualizada em {agents_path}")


####################################################################################
# (4) ADICIONAR JS PARA EXTRAIR SESSÕES INATIVAS PARA CARD SEPARADO
####################################################################################

js_content = JS_PATH.read_text(encoding="utf-8")

js_block = r'''// APPVERBO_SESSOES_INATIVAS_CARD_FORA_V15_START
(function () {
  "use strict";

  //###################################################################################
  // (1) NORMALIZAR E VALIDAR ESCOPO
  //###################################################################################

  function normalizarTextoSessoesInativasV15(valor) {
    return String(valor || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase();
  }

  function elementoVisivelSessoesInativasV15(elemento) {
    if (!elemento) {
      return false;
    }

    if (elemento.hidden || elemento.getAttribute("aria-hidden") === "true") {
      return false;
    }

    const estilo = window.getComputedStyle(elemento);

    if (estilo.display === "none" || estilo.visibility === "hidden") {
      return false;
    }

    return Boolean(elemento.offsetWidth || elemento.offsetHeight || elemento.getClientRects().length);
  }

  function tabSessoesAtivaInativasV15() {
    const candidatos = Array.from(document.querySelectorAll("button, a, [role='tab'], [data-admin-tab], .tab-button, .admin-tab"));

    return candidatos.some(function (elemento) {
      const texto = normalizarTextoSessoesInativasV15(elemento.textContent);

      if (texto !== "sessoes") {
        return false;
      }

      if (!elementoVisivelSessoesInativasV15(elemento)) {
        return false;
      }

      const className = normalizarTextoSessoesInativasV15(elemento.className || "");
      const parentClass = elemento.parentElement
        ? normalizarTextoSessoesInativasV15(elemento.parentElement.className || "")
        : "";

      return elemento.getAttribute("aria-selected") === "true" ||
        className.includes("active") ||
        className.includes("ativo") ||
        className.includes("selected") ||
        parentClass.includes("active") ||
        parentClass.includes("ativo") ||
        parentClass.includes("selected");
    });
  }

  function outraAbaAtivaInativasV15() {
    const candidatos = Array.from(document.querySelectorAll("button, a, [role='tab'], [data-admin-tab], .tab-button, .admin-tab"));

    return candidatos.some(function (elemento) {
      const texto = normalizarTextoSessoesInativasV15(elemento.textContent);

      if (!["entidade", "utilizador", "menu"].includes(texto)) {
        return false;
      }

      if (!elementoVisivelSessoesInativasV15(elemento)) {
        return false;
      }

      const className = normalizarTextoSessoesInativasV15(elemento.className || "");
      const parentClass = elemento.parentElement
        ? normalizarTextoSessoesInativasV15(elemento.parentElement.className || "")
        : "";

      return elemento.getAttribute("aria-selected") === "true" ||
        className.includes("active") ||
        className.includes("ativo") ||
        className.includes("selected") ||
        parentClass.includes("active") ||
        parentClass.includes("ativo") ||
        parentClass.includes("selected");
    });
  }

  function abaSessoesAtivaInativasV15() {
    if (tabSessoesAtivaInativasV15()) {
      return true;
    }

    if (outraAbaAtivaInativasV15()) {
      return false;
    }

    const cardAtivas = document.getElementById("admin-sidebar-sections-card");

    if (!cardAtivas || !elementoVisivelSessoesInativasV15(cardAtivas)) {
      return false;
    }

    const textoCard = normalizarTextoSessoesInativasV15(cardAtivas.textContent);

    return textoCard.includes("sessoes do sidebar") ||
      textoCard.includes("sessoes inativas") ||
      textoCard.includes("menu lateral");
  }

  //###################################################################################
  // (2) LOCALIZAR BLOCO/TABELA DE SESSÕES INATIVAS DENTRO DO CARD PRINCIPAL
  //###################################################################################

  function encontrarTituloInativasDentroDoCardV15(cardAtivas) {
    const titulos = Array.from(cardAtivas.querySelectorAll("h1, h2, h3, h4, strong, .appverbo-sidebar-section-list-title-v9"));

    return titulos.find(function (titulo) {
      return normalizarTextoSessoesInativasV15(titulo.textContent) === "sessoes inativas";
    }) || null;
  }

  function encontrarTabelaInativasAposTituloV15(titulo) {
    let atual = titulo ? titulo.nextElementSibling : null;

    while (atual) {
      if (
        atual.matches &&
        (
          atual.matches(".appverbo-sidebar-section-list-block-inativo-v9") ||
          atual.matches(".appverbo-sidebar-sections-table-wrap-v10") ||
          atual.matches(".appverbo-sidebar-sections-table-wrap-v9") ||
          atual.matches(".appverbo-sidebar-sections-table-wrap-v2") ||
          atual.querySelector("table")
        )
      ) {
        return atual;
      }

      atual = atual.nextElementSibling;
    }

    return null;
  }

  function encontrarBlocoInativasLegadoV15(cardAtivas) {
    return cardAtivas.querySelector(".appverbo-sidebar-section-list-block-inativo-v9") ||
      cardAtivas.querySelector(".appverbo-sidebar-section-list-block-inativo-v10") ||
      null;
  }

  //###################################################################################
  // (3) CRIAR CARD SEPARADO
  //###################################################################################

  function obterOuCriarCardInativasSeparadoV15(cardAtivas) {
    let cardInativas = document.getElementById("admin-sidebar-sections-inactive-card");

    if (!cardInativas) {
      cardInativas = document.createElement("section");
      cardInativas.id = "admin-sidebar-sections-inactive-card";
    }

    cardInativas.className = "card appverbo-sidebar-sections-inactive-card-v10 appverbo-sidebar-sections-inactive-card-v15";
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

  function criarTituloInativasV15() {
    const titulo = document.createElement("h2");
    titulo.className = "appverbo-sidebar-section-list-main-title-v10 appverbo-sidebar-section-list-main-title-v15";
    titulo.textContent = "Sessões inativas";
    return titulo;
  }

  function criarMensagemSemInativasV15() {
    const mensagem = document.createElement("p");
    mensagem.className = "appverbo-sidebar-section-empty-text-v10 appverbo-sidebar-section-empty-text-v15";
    mensagem.textContent = "Sem sessões inativas.";
    return mensagem;
  }

  function tabelaEstaVaziaInativasV15(elemento) {
    if (!elemento) {
      return true;
    }

    const linhas = Array.from(elemento.querySelectorAll("tbody tr"));

    if (!linhas.length) {
      return true;
    }

    const linhasComDados = linhas.filter(function (linha) {
      const texto = normalizarTextoSessoesInativasV15(linha.textContent);

      return texto &&
        !texto.includes("sem sessoes inativas") &&
        !texto.includes("sem sessões inativas");
    });

    return linhasComDados.length === 0;
  }

  //###################################################################################
  // (4) SEPARAR INATIVAS DO CARD PRINCIPAL
  //###################################################################################

  function limparRestosInativasNoCardPrincipalV15(cardAtivas) {
    const titulos = Array.from(cardAtivas.querySelectorAll("h1, h2, h3, h4, strong, .appverbo-sidebar-section-list-title-v9"));

    titulos.forEach(function (titulo) {
      if (normalizarTextoSessoesInativasV15(titulo.textContent) === "sessoes inativas") {
        titulo.remove();
      }
    });

    Array.from(cardAtivas.querySelectorAll(".appverbo-sidebar-section-list-block-inativo-v9, .appverbo-sidebar-section-list-block-inativo-v10")).forEach(function (bloco) {
      bloco.remove();
    });
  }

  function separarSessaoInativasParaCardV15() {
    if (!abaSessoesAtivaInativasV15()) {
      const cardInativasFora = document.getElementById("admin-sidebar-sections-inactive-card");

      if (cardInativasFora) {
        cardInativasFora.remove();
      }

      return;
    }

    const cardAtivas = document.getElementById("admin-sidebar-sections-card");

    if (!cardAtivas || !cardAtivas.parentElement) {
      return;
    }

    const cardInativas = obterOuCriarCardInativasSeparadoV15(cardAtivas);
    const blocoLegado = encontrarBlocoInativasLegadoV15(cardAtivas);
    const tituloDentro = encontrarTituloInativasDentroDoCardV15(cardAtivas);
    const tabelaDentro = blocoLegado || encontrarTabelaInativasAposTituloV15(tituloDentro);

    cardInativas.innerHTML = "";
    cardInativas.appendChild(criarTituloInativasV15());

    if (tabelaDentro) {
      if (blocoLegado) {
        const tabela = blocoLegado.querySelector(".appverbo-sidebar-sections-table-wrap-v2, .appverbo-sidebar-sections-table-wrap-v9, .appverbo-sidebar-sections-table-wrap-v10, table");

        if (tabela) {
          cardInativas.appendChild(tabela);
        }
        else if (!tabelaEstaVaziaInativasV15(blocoLegado)) {
          cardInativas.appendChild(blocoLegado);
        }
        else {
          cardInativas.appendChild(criarMensagemSemInativasV15());
        }
      }
      else if (!tabelaEstaVaziaInativasV15(tabelaDentro)) {
        cardInativas.appendChild(tabelaDentro);
      }
      else {
        cardInativas.appendChild(criarMensagemSemInativasV15());
      }
    }
    else {
      cardInativas.appendChild(criarMensagemSemInativasV15());
    }

    limparRestosInativasNoCardPrincipalV15(cardAtivas);

    cardAtivas.classList.add("appverbo-sidebar-sections-active-card-v15");
    cardInativas.classList.add("appverbo-sidebar-sections-inactive-card-separated-v15");
  }

  //###################################################################################
  // (5) OBSERVAR RENDERIZAÇÕES E RETORNO À ABA
  //###################################################################################

  function agendarSepararInativasV15() {
    window.setTimeout(separarSessaoInativasParaCardV15, 60);
    window.setTimeout(separarSessaoInativasParaCardV15, 180);
    window.setTimeout(separarSessaoInativasParaCardV15, 420);
    window.setTimeout(separarSessaoInativasParaCardV15, 900);
    window.setTimeout(separarSessaoInativasParaCardV15, 1600);
  }

  function instalarSeparadorInativasV15() {
    if (window.__appverboSessoesInactiveCardV15Installed === true) {
      return;
    }

    window.__appverboSessoesInactiveCardV15Installed = true;

    document.addEventListener("click", function () {
      agendarSepararInativasV15();
    });

    window.addEventListener("hashchange", agendarSepararInativasV15);
    window.addEventListener("popstate", agendarSepararInativasV15);

    const observer = new MutationObserver(function () {
      window.clearTimeout(window.__appverboSessoesInactiveCardV15Timer);

      window.__appverboSessoesInactiveCardV15Timer = window.setTimeout(function () {
        separarSessaoInativasParaCardV15();
      }, 120);
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });

    agendarSepararInativasV15();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", instalarSeparadorInativasV15);
  }
  else {
    instalarSeparadorInativasV15();
  }
})();
// APPVERBO_SESSOES_INATIVAS_CARD_FORA_V15_END
'''

if JS_MARKER_START in js_content and JS_MARKER_END in js_content:
    js_pattern = re.compile(
        re.escape(JS_MARKER_START) + r"[\s\S]*?" + re.escape(JS_MARKER_END),
        re.S,
    )
    js_content = js_pattern.sub(js_block, js_content, count=1)
else:
    js_content = js_content.rstrip() + "\n\n" + js_block + "\n"

JS_PATH.write_text(js_content, encoding="utf-8")

print("OK: JS V15 aplicado para separar Sessões inativas em card fora do principal.")


####################################################################################
# (5) ADICIONAR CSS V15
####################################################################################

css_content = CSS_PATH.read_text(encoding="utf-8")

css_block = f'''{CSS_MARKER_START}

#admin-sidebar-sections-inactive-card.appverbo-sidebar-sections-inactive-card-v15 {{
  display: block !important;
  visibility: visible !important;
  margin-top: 12px !important;
  padding: 16px !important;
  border: 1px solid #d5dceb !important;
  border-radius: 8px !important;
  background: #ffffff !important;
  box-sizing: border-box !important;
}}

#admin-sidebar-sections-inactive-card .appverbo-sidebar-section-list-main-title-v15 {{
  margin: 0 0 12px !important;
  color: #12213a !important;
  font-size: 22px !important;
  font-weight: 800 !important;
}}

#admin-sidebar-sections-inactive-card .appverbo-sidebar-section-empty-text-v15 {{
  margin: 0 !important;
  color: #52607a !important;
  font-size: 14px !important;
}}

#admin-sidebar-sections-card .appverbo-sidebar-section-list-block-inativo-v9,
#admin-sidebar-sections-card .appverbo-sidebar-section-list-block-inativo-v10 {{
  display: none !important;
}}

#admin-sidebar-sections-inactive-card .appverbo-sidebar-sections-table-wrap-v2,
#admin-sidebar-sections-inactive-card .appverbo-sidebar-sections-table-wrap-v9,
#admin-sidebar-sections-inactive-card .appverbo-sidebar-sections-table-wrap-v10 {{
  width: 100% !important;
}}

#admin-sidebar-sections-inactive-card table {{
  width: 100% !important;
}}

{CSS_MARKER_END}'''

if CSS_MARKER_START in css_content and CSS_MARKER_END in css_content:
    css_pattern = re.compile(
        re.escape(CSS_MARKER_START) + r"[\s\S]*?" + re.escape(CSS_MARKER_END),
        re.S,
    )
    css_content = css_pattern.sub(css_block, css_content, count=1)
else:
    css_content = css_content.rstrip() + "\n\n" + css_block + "\n"

CSS_PATH.write_text(css_content, encoding="utf-8")

print("OK: CSS V15 aplicado para card separado de Sessões inativas.")


####################################################################################
# (6) ATUALIZAR CACHE BUSTER
####################################################################################

template_content = TEMPLATE_PATH.read_text(encoding="utf-8")

if "static/js/modules/sidebar_sections_layout_v1.js" in template_content:
    template_content = re.sub(
        r"/static/js/modules/sidebar_sections_layout_v1\.js\?v=[^\"]+",
        JS_CACHE,
        template_content,
    )
else:
    fail_v15("não encontrei sidebar_sections_layout_v1.js no template.")

if "static/css/modules/sidebar_sections_layout_v1.css" in template_content:
    template_content = re.sub(
        r"/static/css/modules/sidebar_sections_layout_v1\.css\?v=[^\"]+",
        CSS_CACHE,
        template_content,
    )
else:
    fail_v15("não encontrei sidebar_sections_layout_v1.css no template.")

TEMPLATE_PATH.write_text(template_content, encoding="utf-8")

print("OK: cache buster atualizado.")


####################################################################################
# (7) VALIDAR CONTEUDO
####################################################################################

agents_validado = agents_path.read_text(encoding="utf-8")
js_validado = JS_PATH.read_text(encoding="utf-8")
css_validado = CSS_PATH.read_text(encoding="utf-8")
template_validado = TEMPLATE_PATH.read_text(encoding="utf-8")

validacoes = {
    "APPVERBO_SESSOES_INATIVAS_CARD_FORA_V15_START": agents_validado,
    "APPVERBO_SESSOES_INATIVAS_CARD_FORA_V15_START": js_validado,
    "separarSessaoInativasParaCardV15": js_validado,
    "admin-sidebar-sections-inactive-card": js_validado,
    "Sem sessões inativas.": js_validado,
    "APPVERBO_SESSOES_INATIVAS_CARD_FORA_V15_START": css_validado,
    "appverbo-sidebar-sections-inactive-card-v15": css_validado,
    "20260505-sessoes-inativas-fora-v15": template_validado,
}

for termo, conteudo in validacoes.items():
    if termo not in conteudo:
        fail_v15(f"validação falhou, termo ausente: {termo}")

print("OK: patch_sessoes_inativas_separar_card_v15 concluído.")
