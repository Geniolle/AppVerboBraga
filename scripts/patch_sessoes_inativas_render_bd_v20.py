from pathlib import Path
import re
import sys

ROOT = Path.cwd()

AGENTS_UPPER_PATH = ROOT / "AGENTS.md"
AGENTS_TITLE_PATH = ROOT / "Agents.md"
TEMPLATE_PATH = ROOT / "templates" / "new_user.html"
JS_PATH = ROOT / "static" / "js" / "modules" / "sidebar_sections_layout_v1.js"
CSS_PATH = ROOT / "static" / "css" / "modules" / "sidebar_sections_layout_v1.css"

AGENTS_MARKER_START = "<!-- APPVERBO_SESSOES_INATIVAS_RENDER_BD_V20_START -->"
AGENTS_MARKER_END = "<!-- APPVERBO_SESSOES_INATIVAS_RENDER_BD_V20_END -->"

JS_MARKER_START = "// APPVERBO_SESSOES_INATIVAS_RENDER_BD_V20_START"
JS_MARKER_END = "// APPVERBO_SESSOES_INATIVAS_RENDER_BD_V20_END"

CSS_MARKER_START = "/* APPVERBO_SESSOES_INATIVAS_RENDER_BD_V20_START */"
CSS_MARKER_END = "/* APPVERBO_SESSOES_INATIVAS_RENDER_BD_V20_END */"

JS_CACHE = "/static/js/modules/sidebar_sections_layout_v1.js?v=20260505-sessoes-inativas-render-bd-v20"
CSS_CACHE = "/static/css/modules/sidebar_sections_layout_v1.css?v=20260505-sessoes-inativas-render-bd-v20"


def fail_v20(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


####################################################################################
# (1) RESOLVER AGENTS.md
####################################################################################

def resolve_agents_path_v20() -> Path:
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
        fail_v20(f"ficheiro não encontrado: {file_path}")


####################################################################################
# (3) ATUALIZAR AGENTS.md
####################################################################################

agents_path = resolve_agents_path_v20()
agents_content = agents_path.read_text(encoding="utf-8")

agents_rule = f"""{AGENTS_MARKER_START}
## Regra para renderização das Sessões inativas a partir do BD

Na aba **Sessões**:

1. O card **Sessões inativas** deve ser montado a partir dos dados reais retornados por `/settings/menu/sidebar-sections-data`.
2. Toda sessão com `status` diferente de **ativo** deve aparecer no card **Sessões inativas**.
3. Toda sessão com `is_active` igual a `false` deve aparecer no card **Sessões inativas**.
4. Após alterar uma sessão de **Ativo** para **Inativo** e gravar, ela deve aparecer no card inferior após o reload.
5. O card deve permanecer visível mesmo quando não houver inativas, mostrando **Sem sessões inativas.**
6. O botão **Editar** dentro do card de inativas deve continuar usando o fluxo padrão Entidade da aba Sessões.
7. O card **Sessões inativas** não pode aparecer fora da aba **Sessões**.
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

print(f"OK: regra V20 atualizada em {agents_path}")


####################################################################################
# (4) ADICIONAR JS V20 PARA RENDERIZAR INATIVAS PELO BD
####################################################################################

js_content = JS_PATH.read_text(encoding="utf-8")

js_block = r'''// APPVERBO_SESSOES_INATIVAS_RENDER_BD_V20_START
(function () {
  "use strict";

  //###################################################################################
  // (1) NORMALIZACAO
  //###################################################################################

  function normalizarTextoSessoesInativasV20(valor) {
    return String(valor || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase();
  }

  function criarChaveSessoesInativasV20(valor) {
    return normalizarTextoSessoesInativasV20(valor)
      .replace(/[^a-z0-9]+/g, "_")
      .replace(/_+/g, "_")
      .replace(/^_+|_+$/g, "");
  }

  function normalizarEstadoSessoesInativasV20(sessao) {
    if (sessao && sessao.is_active === false) {
      return "inativo";
    }

    const status = normalizarTextoSessoesInativasV20(
      sessao ? (sessao.status || sessao.status_label || "") : ""
    );

    if (["inativo", "inactive", "0", "false", "nao", "não", "off"].includes(status)) {
      return "inativo";
    }

    return "ativo";
  }

  function labelEstadoSessoesInativasV20(sessao) {
    return normalizarEstadoSessoesInativasV20(sessao) === "inativo" ? "Inativo" : "Ativo";
  }

  function normalizarSistemaSessoesInativasV20(valor) {
    const sistema = normalizarTextoSessoesInativasV20(valor);

    if (sistema === "owner") {
      return "Owner";
    }

    if (sistema === "legado") {
      return "Legado";
    }

    return "Owner e Legado";
  }

  //###################################################################################
  // (2) DETETAR ABA SESSOES
  //###################################################################################

  function elementoVisivelSessoesInativasV20(elemento) {
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

  function elementoAtivoSessoesInativasV20(elemento) {
    const className = normalizarTextoSessoesInativasV20(elemento.className || "");
    const parentClass = elemento.parentElement
      ? normalizarTextoSessoesInativasV20(elemento.parentElement.className || "")
      : "";

    return elemento.getAttribute("aria-selected") === "true" ||
      className.includes("active") ||
      className.includes("ativo") ||
      className.includes("selected") ||
      className.includes("current") ||
      className.includes("is-active") ||
      parentClass.includes("active") ||
      parentClass.includes("ativo") ||
      parentClass.includes("selected") ||
      parentClass.includes("current") ||
      parentClass.includes("is-active");
  }

  function tabAtivaSessoesInativasV20(textoEsperado) {
    const candidatos = Array.from(document.querySelectorAll("button, a, [role='tab'], [data-admin-tab], .tab-button, .admin-tab"));

    return candidatos.some(function (elemento) {
      return normalizarTextoSessoesInativasV20(elemento.textContent) === textoEsperado &&
        elementoVisivelSessoesInativasV20(elemento) &&
        elementoAtivoSessoesInativasV20(elemento);
    });
  }

  function abaSessoesAtivaInativasV20() {
    if (tabAtivaSessoesInativasV20("sessoes")) {
      return true;
    }

    if (
      tabAtivaSessoesInativasV20("entidade") ||
      tabAtivaSessoesInativasV20("utilizador") ||
      tabAtivaSessoesInativasV20("menu")
    ) {
      return false;
    }

    const url = new URL(window.location.href);

    if (
      url.searchParams.get("admin_tab") === "sessoes" ||
      url.searchParams.get("sidebar_sections_tab") === "sessoes" ||
      url.searchParams.get("target") === "admin-sidebar-sections-card"
    ) {
      return true;
    }

    const card = document.getElementById("admin-sidebar-sections-card");

    if (!card || !elementoVisivelSessoesInativasV20(card)) {
      return false;
    }

    const textoCard = normalizarTextoSessoesInativasV20(card.textContent);

    return textoCard.includes("sessoes do sidebar") ||
      textoCard.includes("menu lateral") ||
      Boolean(card.querySelector(".appverbo-sidebar-section-row-v10, .appverbo-sidebar-section-row-v9, .appverbo-sidebar-section-row-v6, .appverbo-sidebar-section-row-v2"));
  }

  //###################################################################################
  // (3) CARREGAR SESSOES DO BD/TEMPLATE
  //###################################################################################

  function lerSessoesTemplateInativasV20() {
    const script = document.getElementById("appverbo-sidebar-section-options-v2") ||
      document.getElementById("appverbo-sidebar-section-options-v1");

    if (!script) {
      return [];
    }

    try {
      const parsed = JSON.parse(script.textContent || "[]");
      return Array.isArray(parsed) ? parsed : [];
    }
    catch (error) {
      return [];
    }
  }

  async function carregarSessoesInativasV20() {
    try {
      const response = await fetch("/settings/menu/sidebar-sections-data", {
        headers: {
          Accept: "application/json"
        },
        credentials: "same-origin"
      });

      if (response.ok) {
        const payload = await response.json();

        if (payload && Array.isArray(payload.sections)) {
          return payload.sections;
        }
      }
    }
    catch (error) {
      console.warn("APPVERBO V20: falha ao carregar sessões para card de inativas.", error);
    }

    return lerSessoesTemplateInativasV20();
  }

  function normalizarSessaoInativasV20(sessao) {
    if (!sessao || typeof sessao !== "object") {
      return null;
    }

    const label = String(sessao.label || sessao.name || sessao.title || "").trim();
    const key = criarChaveSessoesInativasV20(sessao.key || sessao.section_key || label);

    if (!label || !key) {
      return null;
    }

    const sistema = String(sessao.visibility_scope_mode || sessao.scope_mode || "all").trim() || "all";
    const estado = normalizarEstadoSessoesInativasV20(sessao);

    return {
      key: key,
      label: label,
      visibility_scope_mode: sistema,
      visibility_scope_label: sessao.visibility_scope_label || normalizarSistemaSessoesInativasV20(sistema),
      status: estado,
      is_active: estado === "ativo",
      status_label: labelEstadoSessoesInativasV20(sessao)
    };
  }

  //###################################################################################
  // (4) CRIAR COMPONENTES DO CARD DE INATIVAS
  //###################################################################################

  function criarBotaoAcaoInativasV20(tipo, titulo, texto) {
    const botao = document.createElement("button");
    botao.type = "button";
    botao.className = "appverbo-sidebar-section-action-btn-v2 appverbo-sidebar-section-action-btn-v20";
    botao.dataset.sidebarSectionActionV10 = tipo;
    botao.dataset.sidebarSectionActionV20 = tipo;
    botao.title = titulo;
    botao.setAttribute("aria-label", titulo);
    botao.textContent = texto;
    return botao;
  }

  function criarBadgeEstadoInativasV20(sessao) {
    const badge = document.createElement("span");
    badge.className = "appverbo-sidebar-section-state-badge-v2 appverbo-sidebar-section-state-badge-inativo-v20";
    badge.textContent = labelEstadoSessoesInativasV20(sessao);
    return badge;
  }

  function criarLinhaInativaV20(sessao) {
    const tr = document.createElement("tr");
    tr.className = "appverbo-sidebar-section-row-v2 appverbo-sidebar-section-row-v10 appverbo-sidebar-section-row-v20";
    tr.dataset.sectionKeyV10 = sessao.key;
    tr.dataset.sectionKeyV20 = sessao.key;
    tr.dataset.sectionStatusV20 = sessao.status;

    const tdMenu = document.createElement("td");
    tdMenu.className = "appverbo-sidebar-section-menu-cell-v2";
    tdMenu.textContent = sessao.label;

    const tdSistema = document.createElement("td");
    tdSistema.className = "appverbo-sidebar-section-system-cell-v2";
    tdSistema.textContent = sessao.visibility_scope_label || normalizarSistemaSessoesInativasV20(sessao.visibility_scope_mode);

    const tdEstado = document.createElement("td");
    tdEstado.className = "appverbo-sidebar-section-state-cell-v2";
    tdEstado.appendChild(criarBadgeEstadoInativasV20(sessao));

    const tdAcoes = document.createElement("td");
    tdAcoes.className = "appverbo-sidebar-section-actions-cell-v2";

    const actions = document.createElement("div");
    actions.className = "appverbo-sidebar-section-actions-v2";
    actions.appendChild(criarBotaoAcaoInativasV20("view", "Visualizar detalhes", "👁"));
    actions.appendChild(criarBotaoAcaoInativasV20("edit", "Editar sessão", "✎"));

    tdAcoes.appendChild(actions);

    tr.appendChild(tdMenu);
    tr.appendChild(tdSistema);
    tr.appendChild(tdEstado);
    tr.appendChild(tdAcoes);

    return tr;
  }

  function criarTabelaInativasV20(sessoesInativas) {
    const tableWrap = document.createElement("div");
    tableWrap.className = "appverbo-sidebar-sections-table-wrap-v2 appverbo-sidebar-sections-table-wrap-v20";

    const table = document.createElement("table");
    table.className = "appverbo-sidebar-sections-table-v2 appverbo-sidebar-sections-table-v20";

    const thead = document.createElement("thead");
    thead.innerHTML = "<tr><th>MENU LATERAL</th><th>SISTEMA</th><th>ESTADO</th><th>AÇÕES</th></tr>";

    const tbody = document.createElement("tbody");
    tbody.className = "appverbo-sidebar-sections-body-v2 appverbo-sidebar-sections-body-v20";
    tbody.dataset.statusGroupV20 = "inativo";

    sessoesInativas.forEach(function (sessao) {
      tbody.appendChild(criarLinhaInativaV20(sessao));
    });

    table.appendChild(thead);
    table.appendChild(tbody);
    tableWrap.appendChild(table);

    return tableWrap;
  }

  function obterOuCriarCardInativasV20(cardAtivas) {
    let cardInativas = document.getElementById("admin-sidebar-sections-inactive-card");

    if (!cardInativas) {
      cardInativas = document.createElement("section");
      cardInativas.id = "admin-sidebar-sections-inactive-card";
    }

    cardInativas.className = "card appverbo-sidebar-sections-inactive-card-v20";
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

  function removerInativasDoCardPrincipalV20(sessoesInativas) {
    const cardAtivas = document.getElementById("admin-sidebar-sections-card");

    if (!cardAtivas) {
      return;
    }

    const chavesInativas = new Set(
      sessoesInativas.map(function (sessao) {
        return criarChaveSessoesInativasV20(sessao.key);
      })
    );

    Array.from(cardAtivas.querySelectorAll("tr")).forEach(function (linha) {
      const datasetKey = linha.dataset.sectionKeyV10 ||
        linha.dataset.sectionKeyV9 ||
        linha.dataset.sectionKeyV6 ||
        linha.dataset.sectionKeyV2 ||
        linha.dataset.sectionKeyV20 ||
        "";

      const hiddenKey = linha.querySelector('[name="section_key"]');
      const key = criarChaveSessoesInativasV20(datasetKey || (hiddenKey ? hiddenKey.value : ""));

      if (key && chavesInativas.has(key)) {
        linha.remove();
      }
    });

    Array.from(cardAtivas.querySelectorAll(".appverbo-sidebar-section-list-block-inativo-v9, .appverbo-sidebar-section-list-block-inativo-v10")).forEach(function (bloco) {
      bloco.remove();
    });

    Array.from(cardAtivas.querySelectorAll("h1, h2, h3, h4, strong")).forEach(function (titulo) {
      if (normalizarTextoSessoesInativasV20(titulo.textContent) === "sessoes inativas") {
        titulo.remove();
      }
    });
  }

  //###################################################################################
  // (5) RENDERIZAR CARD DE INATIVAS
  //###################################################################################

  async function renderizarCardInativasDoBdV20() {
    if (!abaSessoesAtivaInativasV20()) {
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

    const sessoesRaw = await carregarSessoesInativasV20();
    const sessoes = sessoesRaw.map(normalizarSessaoInativasV20).filter(Boolean);

    const sessoesInativas = sessoes.filter(function (sessao) {
      return normalizarEstadoSessoesInativasV20(sessao) !== "ativo";
    });

    removerInativasDoCardPrincipalV20(sessoesInativas);

    const cardInativas = obterOuCriarCardInativasV20(cardAtivas);
    cardInativas.innerHTML = "";

    const titulo = document.createElement("h2");
    titulo.className = "appverbo-sidebar-section-list-main-title-v20";
    titulo.textContent = "Sessões inativas";
    cardInativas.appendChild(titulo);

    if (sessoesInativas.length) {
      cardInativas.appendChild(criarTabelaInativasV20(sessoesInativas));
    }
    else {
      const vazio = document.createElement("p");
      vazio.className = "appverbo-sidebar-section-empty-text-v20";
      vazio.textContent = "Sem sessões inativas.";
      cardInativas.appendChild(vazio);
    }
  }

  //###################################################################################
  // (6) EVENTOS DO CARD DE INATIVAS
  //###################################################################################

  function instalarEventosInativasV20() {
    if (window.__appverboSessoesInativasEventosV20 === true) {
      return;
    }

    window.__appverboSessoesInativasEventosV20 = true;

    document.addEventListener("click", function (event) {
      const botao = event.target.closest("[data-sidebar-section-action-v20]");

      if (!botao) {
        return;
      }

      const linha = botao.closest("tr.appverbo-sidebar-section-row-v20");

      if (!linha) {
        return;
      }

      const acao = botao.dataset.sidebarSectionActionV20;
      const chave = linha.dataset.sectionKeyV20 || linha.dataset.sectionKeyV10 || "";
      const nome = linha.querySelector(".appverbo-sidebar-section-menu-cell-v2");
      const sistema = linha.querySelector(".appverbo-sidebar-section-system-cell-v2");
      const estado = linha.querySelector(".appverbo-sidebar-section-state-cell-v2");

      if (acao === "view") {
        event.preventDefault();
        event.stopPropagation();
        event.stopImmediatePropagation();

        alert(
          "Nome da sessão: " + (nome ? nome.textContent.trim() : "") +
          "\nSistema: " + (sistema ? sistema.textContent.trim() : "") +
          "\nEstado: " + (estado ? estado.textContent.trim() : "")
        );
      }

      if (acao === "edit") {
        event.preventDefault();
        event.stopPropagation();
        event.stopImmediatePropagation();

        const url = new URL(window.location.href);
        url.searchParams.delete("settings_edit_key");
        url.searchParams.delete("settings_action");
        url.searchParams.delete("settings_tab");
        url.searchParams.delete("success");
        url.searchParams.delete("error");
        url.searchParams.set("menu", "administrativo");
        url.searchParams.set("admin_tab", "sessoes");
        url.searchParams.set("sidebar_sections_tab", "sessoes");
        url.searchParams.set("target", "admin-sidebar-sections-card");
        url.searchParams.set("sidebar_section_edit_key", criarChaveSessoesInativasV20(chave));
        url.hash = "admin-sidebar-sections-card";

        window.location.href = url.pathname + url.search + url.hash;
      }
    }, true);
  }

  //###################################################################################
  // (7) INSTALAR OBSERVADORES
  //###################################################################################

  function agendarRenderInativasV20() {
    window.setTimeout(renderizarCardInativasDoBdV20, 100);
    window.setTimeout(renderizarCardInativasDoBdV20, 350);
    window.setTimeout(renderizarCardInativasDoBdV20, 800);
    window.setTimeout(renderizarCardInativasDoBdV20, 1600);
    window.setTimeout(renderizarCardInativasDoBdV20, 2600);
  }

  function instalarRenderInativasV20() {
    instalarEventosInativasV20();
    agendarRenderInativasV20();

    document.addEventListener("click", function () {
      agendarRenderInativasV20();
    });

    window.addEventListener("hashchange", agendarRenderInativasV20);
    window.addEventListener("popstate", agendarRenderInativasV20);

    const observer = new MutationObserver(function () {
      window.clearTimeout(window.__appverboSessoesInativasTimerV20);

      window.__appverboSessoesInativasTimerV20 = window.setTimeout(function () {
        renderizarCardInativasDoBdV20();
      }, 180);
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ["class", "hidden", "style", "aria-selected", "aria-hidden"]
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", instalarRenderInativasV20);
  }
  else {
    instalarRenderInativasV20();
  }
})();
// APPVERBO_SESSOES_INATIVAS_RENDER_BD_V20_END
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

print("OK: JS V20 aplicado para renderizar Sessões inativas a partir do BD.")


####################################################################################
# (5) ADICIONAR CSS V20
####################################################################################

css_content = CSS_PATH.read_text(encoding="utf-8")

css_block = f'''{CSS_MARKER_START}

#admin-sidebar-sections-inactive-card.appverbo-sidebar-sections-inactive-card-v20 {{
  display: block !important;
  visibility: visible !important;
  margin-top: 12px !important;
  padding: 16px !important;
  border: 1px solid #d5dceb !important;
  border-radius: 12px !important;
  background: #ffffff !important;
  box-sizing: border-box !important;
}}

#admin-sidebar-sections-inactive-card .appverbo-sidebar-section-list-main-title-v20 {{
  margin: 0 0 12px !important;
  color: #12213a !important;
  font-size: 22px !important;
  font-weight: 800 !important;
}}

#admin-sidebar-sections-inactive-card .appverbo-sidebar-section-empty-text-v20 {{
  margin: 0 !important;
  color: #52607a !important;
  font-size: 14px !important;
}}

#admin-sidebar-sections-inactive-card .appverbo-sidebar-sections-table-wrap-v20 {{
  width: 100% !important;
}}

#admin-sidebar-sections-inactive-card .appverbo-sidebar-sections-table-v20 {{
  width: 100% !important;
}}

#admin-sidebar-sections-inactive-card .appverbo-sidebar-section-row-v20 td {{
  height: 44px !important;
}}

#admin-sidebar-sections-inactive-card .appverbo-sidebar-section-state-badge-inativo-v20 {{
  border-color: #f0c36d !important;
  background: #fff7e0 !important;
  color: #8a5a00 !important;
}}

#admin-sidebar-sections-card .appverbo-sidebar-section-list-block-inativo-v9,
#admin-sidebar-sections-card .appverbo-sidebar-section-list-block-inativo-v10 {{
  display: none !important;
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

print("OK: CSS V20 aplicado.")


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
    fail_v20("não encontrei sidebar_sections_layout_v1.js no template.")

if "static/css/modules/sidebar_sections_layout_v1.css" in template_content:
    template_content = re.sub(
        r"/static/css/modules/sidebar_sections_layout_v1\.css\?v=[^\"]+",
        CSS_CACHE,
        template_content,
    )
else:
    fail_v20("não encontrei sidebar_sections_layout_v1.css no template.")

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
    "APPVERBO_SESSOES_INATIVAS_RENDER_BD_V20_START": agents_validado,
    "APPVERBO_SESSOES_INATIVAS_RENDER_BD_V20_START": js_validado,
    "renderizarCardInativasDoBdV20": js_validado,
    "/settings/menu/sidebar-sections-data": js_validado,
    "Sessões inativas": js_validado,
    "Sem sessões inativas.": js_validado,
    "APPVERBO_SESSOES_INATIVAS_RENDER_BD_V20_START": css_validado,
    "appverbo-sidebar-sections-inactive-card-v20": css_validado,
    "20260505-sessoes-inativas-render-bd-v20": template_validado,
}

for termo, conteudo in validacoes.items():
    if termo not in conteudo:
        fail_v20(f"validação falhou, termo ausente: {termo}")

print("OK: patch_sessoes_inativas_render_bd_v20 concluído.")
