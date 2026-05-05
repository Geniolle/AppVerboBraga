from pathlib import Path
import re
import sys

ROOT = Path.cwd()

AGENTS_UPPER_PATH = ROOT / "AGENTS.md"
AGENTS_TITLE_PATH = ROOT / "Agents.md"
TEMPLATE_PATH = ROOT / "templates" / "new_user.html"
JS_PATH = ROOT / "static" / "js" / "modules" / "sidebar_sections_layout_v1.js"
CSS_PATH = ROOT / "static" / "css" / "modules" / "sidebar_sections_layout_v1.css"

AGENTS_MARKER_START = "<!-- APPVERBO_SESSOES_RECREATE_CREATE_CARD_V14_START -->"
AGENTS_MARKER_END = "<!-- APPVERBO_SESSOES_RECREATE_CREATE_CARD_V14_END -->"

JS_MARKER_START = "// APPVERBO_SESSOES_RECREATE_CREATE_CARD_V14_START"
JS_MARKER_END = "// APPVERBO_SESSOES_RECREATE_CREATE_CARD_V14_END"

CSS_MARKER_START = "/* APPVERBO_SESSOES_RECREATE_CREATE_CARD_V14_START */"
CSS_MARKER_END = "/* APPVERBO_SESSOES_RECREATE_CREATE_CARD_V14_END */"

JS_CACHE = "/static/js/modules/sidebar_sections_layout_v1.js?v=20260505-sessoes-recreate-create-card-v14"
CSS_CACHE = "/static/css/modules/sidebar_sections_layout_v1.css?v=20260505-sessoes-recreate-create-card-v14"


def fail_v14(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


####################################################################################
# (1) RESOLVER AGENTS.md
####################################################################################

def resolve_agents_path_v14() -> Path:
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
        fail_v14(f"ficheiro não encontrado: {file_path}")


####################################################################################
# (3) ATUALIZAR AGENTS.md
####################################################################################

agents_path = resolve_agents_path_v14()
agents_content = agents_path.read_text(encoding="utf-8")

agents_rule = f"""{AGENTS_MARKER_START}
## Regra de recriação do card Criar sessão

Na aba **Sessões**, o card **Criar sessão** deve ser resiliente à navegação entre abas.

1. Ao entrar inicialmente em **Sessões**, o card **Criar sessão** deve aparecer acima da listagem.
2. Ao sair de **Sessões**, o card pode ser removido para não aparecer em outras abas.
3. Ao retornar para **Sessões**, o card **Criar sessão** deve ser recriado automaticamente.
4. Nenhum guard antigo pode remover o card **Criar sessão** quando a aba **Sessões** estiver ativa.
5. A detecção de aba ativa deve usar o botão/tab ativo pelo texto **Sessões** e a visibilidade real do card de sessões.
6. A URL/hash não deve ser usada como único critério, pois pode continuar apontando para outro card.
7. O card deve continuar permitindo criar com os campos: Nome da sessão, Sistema e Estado.
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

print(f"OK: regra de recriação do card Criar sessão atualizada em {agents_path}")


####################################################################################
# (4) ADICIONAR JS V14
####################################################################################

js_content = JS_PATH.read_text(encoding="utf-8")

js_block = r'''// APPVERBO_SESSOES_RECREATE_CREATE_CARD_V14_START
(function () {
  "use strict";

  //###################################################################################
  // (1) NORMALIZACAO E DETECCAO DA ABA ATIVA
  //###################################################################################

  function normalizarTextoSessoesV14(valor) {
    return String(valor || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase();
  }

  function elementoVisivelSessoesV14(elemento) {
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

  function elementoComEstadoAtivoSessoesV14(elemento) {
    const className = normalizarTextoSessoesV14(elemento.className || "");

    if (elemento.getAttribute("aria-selected") === "true") {
      return true;
    }

    if (
      className.includes("active") ||
      className.includes("ativo") ||
      className.includes("selected") ||
      className.includes("current") ||
      className.includes("is-active")
    ) {
      return true;
    }

    const parent = elemento.parentElement;
    const parentClass = parent ? normalizarTextoSessoesV14(parent.className || "") : "";

    if (
      parentClass.includes("active") ||
      parentClass.includes("ativo") ||
      parentClass.includes("selected") ||
      parentClass.includes("current") ||
      parentClass.includes("is-active")
    ) {
      return true;
    }

    const estilo = window.getComputedStyle(elemento);
    const corTexto = normalizarTextoSessoesV14(estilo.color);
    const corFundo = normalizarTextoSessoesV14(estilo.backgroundColor);

    if (
      corTexto.includes("255, 255, 255") &&
      !corFundo.includes("rgba(0, 0, 0, 0)") &&
      !corFundo.includes("transparent")
    ) {
      return true;
    }

    return false;
  }

  function tabAtivaPorTextoSessoesV14(textoEsperado) {
    const candidatos = Array.from(document.querySelectorAll("button, a, [role='tab'], [data-admin-tab], .tab-button, .admin-tab"));

    return candidatos.some(function (elemento) {
      const texto = normalizarTextoSessoesV14(elemento.textContent);

      if (texto !== textoEsperado) {
        return false;
      }

      if (!elementoVisivelSessoesV14(elemento)) {
        return false;
      }

      return elementoComEstadoAtivoSessoesV14(elemento);
    });
  }

  function outraAbaAdministrativaAtivaSessoesV14() {
    return ["entidade", "utilizador", "menu"].some(function (texto) {
      return tabAtivaPorTextoSessoesV14(texto);
    });
  }

  function cardListaSessoesVisivelV14() {
    const card = document.getElementById("admin-sidebar-sections-card");

    if (!card || !elementoVisivelSessoesV14(card)) {
      return false;
    }

    const textoCard = normalizarTextoSessoesV14(card.textContent);

    return textoCard.includes("sessoes do sidebar") ||
      textoCard.includes("menu lateral") ||
      Boolean(card.querySelector(".appverbo-sidebar-section-row-v10, .appverbo-sidebar-section-row-v9, .appverbo-sidebar-section-row-v6, .appverbo-sidebar-section-row-v2"));
  }

  function abaSessoesAtivaV14() {
    if (tabAtivaPorTextoSessoesV14("sessoes")) {
      return true;
    }

    if (outraAbaAdministrativaAtivaSessoesV14()) {
      return false;
    }

    return cardListaSessoesVisivelV14();
  }

  //###################################################################################
  // (2) PROTEGER CARD CONTRA REMOCAO INDEVIDA QUANDO SESSOES ESTA ATIVA
  //###################################################################################

  function instalarProtecaoRemoveSessoesV14() {
    if (window.__appverboSessoesRemoveProtectedV14 === true) {
      return;
    }

    window.__appverboSessoesRemoveProtectedV14 = true;

    const originalRemove = Element.prototype.remove;

    Element.prototype.remove = function () {
      const id = this && this.id ? this.id : "";

      if (
        (id === "admin-sidebar-sections-create-card" || id === "admin-sidebar-sections-inactive-card") &&
        abaSessoesAtivaV14()
      ) {
        return;
      }

      return originalRemove.call(this);
    };
  }

  //###################################################################################
  // (3) CAMPOS E PAYLOAD
  //###################################################################################

  function criarCampoOcultoSessoesV14(nome, valor) {
    const input = document.createElement("input");
    input.type = "hidden";
    input.name = nome;
    input.value = valor || "";
    return input;
  }

  function criarChaveSessoesV14(valor) {
    return normalizarTextoSessoesV14(valor)
      .replace(/[^a-z0-9]+/g, "_")
      .replace(/_+/g, "_")
      .replace(/^_+|_+$/g, "");
  }

  function normalizarEstadoSessoesCriacaoV14(valor) {
    const clean = normalizarTextoSessoesV14(valor);

    if (["inativo", "inactive", "0", "false", "nao", "não", "off"].includes(clean)) {
      return "inativo";
    }

    return "ativo";
  }

  function obterFormularioSessoesV14() {
    const cardLista = document.getElementById("admin-sidebar-sections-card");

    if (!cardLista) {
      return null;
    }

    let formulario = cardLista.querySelector('form[action*="/settings/menu/sidebar-sections"], form[action*="sidebar-sections"]');

    if (!formulario) {
      formulario = document.createElement("form");
      formulario.method = "post";
      formulario.action = "/settings/menu/sidebar-sections";
      cardLista.appendChild(formulario);
    }

    formulario.method = "post";
    formulario.action = "/settings/menu/sidebar-sections";

    return formulario;
  }

  function obterChavesExistentesSessoesV14() {
    const chaves = new Set();

    Array.from(document.querySelectorAll('[name="section_key"]')).forEach(function (input) {
      const chave = criarChaveSessoesV14(input.value);

      if (chave) {
        chaves.add(chave);
      }
    });

    Array.from(document.querySelectorAll("[data-section-key-v10], [data-section-key-v9], [data-section-key-v6]")).forEach(function (linha) {
      const chave = criarChaveSessoesV14(
        linha.dataset.sectionKeyV10 ||
        linha.dataset.sectionKeyV9 ||
        linha.dataset.sectionKeyV6 ||
        ""
      );

      if (chave) {
        chaves.add(chave);
      }
    });

    return chaves;
  }

  function criarChaveUnicaSessoesV14(nomeSessao) {
    const baseKey = criarChaveSessoesV14(nomeSessao) || "nova_sessao";
    const usadas = obterChavesExistentesSessoesV14();

    if (!usadas.has(baseKey)) {
      return baseKey;
    }

    let contador = 2;
    let chaveFinal = baseKey + "_" + contador;

    while (usadas.has(chaveFinal)) {
      contador += 1;
      chaveFinal = baseKey + "_" + contador;
    }

    return chaveFinal;
  }

  function submeterNovaSessaoV14(dados) {
    const formulario = obterFormularioSessoesV14();

    if (!formulario) {
      return;
    }

    if (!formulario.querySelector('[name="redirect_menu"]')) {
      formulario.appendChild(criarCampoOcultoSessoesV14("redirect_menu", "administrativo"));
    }

    if (!formulario.querySelector('[name="redirect_target"]')) {
      formulario.appendChild(criarCampoOcultoSessoesV14("redirect_target", "#admin-sidebar-sections-card"));
    }

    formulario.appendChild(criarCampoOcultoSessoesV14("section_key", dados.key));
    formulario.appendChild(criarCampoOcultoSessoesV14("section_label", dados.label));
    formulario.appendChild(criarCampoOcultoSessoesV14("section_visibility_scope_mode", dados.system));
    formulario.appendChild(criarCampoOcultoSessoesV14("section_status", dados.status));

    if (typeof formulario.requestSubmit === "function") {
      formulario.requestSubmit();
    }
    else {
      formulario.submit();
    }
  }

  //###################################################################################
  // (4) CRIAR OU RECRIAR CARD CRIAR SESSAO
  //###################################################################################

  function criarOpcaoSelectSessoesV14(valor, texto) {
    const option = document.createElement("option");
    option.value = valor;
    option.textContent = texto;
    return option;
  }

  function obterOuCriarCreateCardSessoesV14() {
    const cardLista = document.getElementById("admin-sidebar-sections-card");

    if (!cardLista || !cardLista.parentElement) {
      return null;
    }

    let createCard = document.getElementById("admin-sidebar-sections-create-card");

    if (!createCard) {
      createCard = document.createElement("section");
      createCard.id = "admin-sidebar-sections-create-card";
      cardLista.parentElement.insertBefore(createCard, cardLista);
    }

    createCard.className = "card appverbo-standard-create-card-v4 appverbo-sessoes-create-card-v3 appverbo-sessoes-create-card-v14";
    createCard.hidden = false;
    createCard.style.display = "";
    createCard.style.visibility = "";

    return createCard;
  }

  function montarConteudoCreateCardSessoesV14(createCard) {
    if (!createCard || createCard.dataset.appverboSessoesCreateV14 === "1") {
      return;
    }

    createCard.dataset.appverboSessoesCreateV14 = "1";
    createCard.innerHTML = "";

    const block = document.createElement("div");
    block.className = "appverbo-create-entry-block-v1 appverbo-create-entry-block-v14";

    const toolbar = document.createElement("div");
    toolbar.className = "appverbo-create-entry-toolbar-v1 appverbo-create-entry-toolbar-v14";

    const abrirBtn = document.createElement("button");
    abrirBtn.type = "button";
    abrirBtn.className = "action-btn appverbo-create-entry-open-btn-v1";
    abrirBtn.textContent = "Criar sessão";

    toolbar.appendChild(abrirBtn);

    const panel = document.createElement("div");
    panel.className = "appverbo-create-entry-panel-v1 appverbo-create-entry-panel-v14";
    panel.hidden = true;

    const grid = document.createElement("div");
    grid.className = "appverbo-create-entry-grid-v5 appverbo-create-entry-grid-v14";

    const nomeField = document.createElement("div");
    nomeField.className = "field appverbo-create-entry-field-v5";

    const nomeLabel = document.createElement("label");
    nomeLabel.textContent = "Nome da sessão *";

    const nomeInput = document.createElement("input");
    nomeInput.type = "text";
    nomeInput.maxLength = 80;
    nomeInput.placeholder = "Informe o nome da sessão";

    nomeField.appendChild(nomeLabel);
    nomeField.appendChild(nomeInput);

    const sistemaField = document.createElement("div");
    sistemaField.className = "field appverbo-create-entry-field-v5";

    const sistemaLabel = document.createElement("label");
    sistemaLabel.textContent = "Sistema *";

    const sistemaSelect = document.createElement("select");
    sistemaSelect.appendChild(criarOpcaoSelectSessoesV14("all", "Owner e Legado"));
    sistemaSelect.appendChild(criarOpcaoSelectSessoesV14("owner", "Owner"));
    sistemaSelect.appendChild(criarOpcaoSelectSessoesV14("legado", "Legado"));

    sistemaField.appendChild(sistemaLabel);
    sistemaField.appendChild(sistemaSelect);

    const estadoField = document.createElement("div");
    estadoField.className = "field appverbo-create-entry-field-v5";

    const estadoLabel = document.createElement("label");
    estadoLabel.textContent = "Estado *";

    const estadoSelect = document.createElement("select");
    estadoSelect.appendChild(criarOpcaoSelectSessoesV14("ativo", "Ativo"));
    estadoSelect.appendChild(criarOpcaoSelectSessoesV14("inativo", "Inativo"));

    estadoField.appendChild(estadoLabel);
    estadoField.appendChild(estadoSelect);

    grid.appendChild(nomeField);
    grid.appendChild(sistemaField);
    grid.appendChild(estadoField);

    const erro = document.createElement("p");
    erro.className = "appverbo-create-entry-error-v5 appverbo-create-entry-error-v14";
    erro.hidden = true;

    const actions = document.createElement("div");
    actions.className = "appverbo-create-entry-actions-v5 appverbo-create-entry-actions-v14";

    const guardarBtn = document.createElement("button");
    guardarBtn.type = "button";
    guardarBtn.className = "action-btn";
    guardarBtn.textContent = "Guardar";

    const cancelarBtn = document.createElement("button");
    cancelarBtn.type = "button";
    cancelarBtn.className = "action-btn-cancel";
    cancelarBtn.textContent = "Cancelar";

    actions.appendChild(guardarBtn);
    actions.appendChild(cancelarBtn);

    panel.appendChild(grid);
    panel.appendChild(erro);
    panel.appendChild(actions);

    block.appendChild(toolbar);
    block.appendChild(panel);
    createCard.appendChild(block);

    function limparFormulario() {
      nomeInput.value = "";
      sistemaSelect.value = "all";
      estadoSelect.value = "ativo";
      erro.hidden = true;
      erro.textContent = "";
      panel.hidden = true;
      abrirBtn.hidden = false;
    }

    abrirBtn.addEventListener("click", function () {
      erro.hidden = true;
      erro.textContent = "";
      panel.hidden = false;
      abrirBtn.hidden = true;
      nomeInput.focus();
    });

    cancelarBtn.addEventListener("click", limparFormulario);

    guardarBtn.addEventListener("click", function () {
      const nome = String(nomeInput.value || "").trim();

      if (!nome) {
        erro.textContent = "Informe o nome da sessão.";
        erro.hidden = false;
        nomeInput.focus();
        return;
      }

      const dados = {
        key: criarChaveUnicaSessoesV14(nome),
        label: nome,
        system: sistemaSelect.value || "all",
        status: normalizarEstadoSessoesCriacaoV14(estadoSelect.value || "ativo")
      };

      limparFormulario();
      submeterNovaSessaoV14(dados);
    });
  }

  function garantirCreateCardSessoesV14() {
    if (!abaSessoesAtivaV14()) {
      Array.from(document.querySelectorAll("#admin-sidebar-sections-create-card")).forEach(function (card) {
        card.remove();
      });

      document.body.classList.remove("appverbo-admin-sessoes-active-v14");
      document.body.classList.add("appverbo-admin-sessoes-inactive-v14");
      return;
    }

    document.body.classList.add("appverbo-admin-sessoes-active-v14");
    document.body.classList.remove("appverbo-admin-sessoes-inactive-v14");
    document.body.classList.add("appverbo-admin-sessoes-active-v12");
    document.body.classList.remove("appverbo-admin-sessoes-inactive-v12");
    document.body.classList.add("appverbo-admin-sessoes-active-v13");
    document.body.classList.remove("appverbo-admin-sessoes-inactive-v13");

    const createCard = obterOuCriarCreateCardSessoesV14();

    if (!createCard) {
      return;
    }

    montarConteudoCreateCardSessoesV14(createCard);
  }

  //###################################################################################
  // (5) OBSERVAR RETORNO A ABA SESSOES
  //###################################################################################

  function agendarGarantiaCreateCardSessoesV14() {
    window.setTimeout(garantirCreateCardSessoesV14, 50);
    window.setTimeout(garantirCreateCardSessoesV14, 160);
    window.setTimeout(garantirCreateCardSessoesV14, 360);
    window.setTimeout(garantirCreateCardSessoesV14, 750);
    window.setTimeout(garantirCreateCardSessoesV14, 1300);
  }

  function instalarObserverSessoesV14() {
    if (window.__appverboSessoesCreateCardObserverV14 === true) {
      return;
    }

    window.__appverboSessoesCreateCardObserverV14 = true;

    instalarProtecaoRemoveSessoesV14();

    document.addEventListener("click", function () {
      agendarGarantiaCreateCardSessoesV14();
    });

    window.addEventListener("hashchange", agendarGarantiaCreateCardSessoesV14);
    window.addEventListener("popstate", agendarGarantiaCreateCardSessoesV14);

    const observer = new MutationObserver(function () {
      window.clearTimeout(window.__appverboSessoesCreateCardObserverTimerV14);

      window.__appverboSessoesCreateCardObserverTimerV14 = window.setTimeout(function () {
        garantirCreateCardSessoesV14();
      }, 80);
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ["class", "hidden", "style", "aria-selected", "aria-hidden"]
    });

    agendarGarantiaCreateCardSessoesV14();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", instalarObserverSessoesV14);
  }
  else {
    instalarObserverSessoesV14();
  }
})();
// APPVERBO_SESSOES_RECREATE_CREATE_CARD_V14_END
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

print("OK: JS V14 aplicado para recriar Criar sessão ao retornar à aba.")


####################################################################################
# (5) ADICIONAR CSS V14
####################################################################################

css_content = CSS_PATH.read_text(encoding="utf-8")

css_block = f'''{CSS_MARKER_START}

body.appverbo-admin-sessoes-active-v14 #admin-sidebar-sections-create-card {{
  display: block !important;
  visibility: visible !important;
}}

body.appverbo-admin-sessoes-inactive-v14 #admin-sidebar-sections-create-card {{
  display: none !important;
}}

.appverbo-sessoes-create-card-v14 {{
  margin-bottom: 12px !important;
  min-height: 64px !important;
}}

.appverbo-create-entry-panel-v14[hidden] {{
  display: none !important;
}}

.appverbo-create-entry-block-v14 {{
  width: 100%;
}}

.appverbo-create-entry-toolbar-v14 {{
  display: flex;
  align-items: center;
  justify-content: flex-start;
}}

.appverbo-create-entry-grid-v14 {{
  display: grid;
  grid-template-columns: minmax(240px, 320px) minmax(220px, 260px) minmax(160px, 220px);
  gap: 12px;
  align-items: end;
  width: 100%;
}}

.appverbo-create-entry-actions-v14 {{
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 8px;
  margin-top: 12px;
}}

.appverbo-create-entry-actions-v14 .action-btn,
.appverbo-create-entry-actions-v14 .action-btn-cancel {{
  min-width: 112px !important;
  width: 112px !important;
  height: 38px !important;
  min-height: 38px !important;
}}

@media (max-width: 1100px) {{
  .appverbo-create-entry-grid-v14 {{
    grid-template-columns: 1fr;
  }}
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

print("OK: CSS V14 aplicado.")


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
    fail_v14("não encontrei sidebar_sections_layout_v1.js no template.")

if "static/css/modules/sidebar_sections_layout_v1.css" in template_content:
    template_content = re.sub(
        r"/static/css/modules/sidebar_sections_layout_v1\.css\?v=[^\"]+",
        CSS_CACHE,
        template_content,
    )
else:
    fail_v14("não encontrei sidebar_sections_layout_v1.css no template.")

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
    "APPVERBO_SESSOES_RECREATE_CREATE_CARD_V14_START": agents_validado,
    "APPVERBO_SESSOES_RECREATE_CREATE_CARD_V14_START": js_validado,
    "garantirCreateCardSessoesV14": js_validado,
    "instalarProtecaoRemoveSessoesV14": js_validado,
    "obterOuCriarCreateCardSessoesV14": js_validado,
    "Criar sessão": js_validado,
    "Nome da sessão": js_validado,
    "Sistema": js_validado,
    "Estado": js_validado,
    "APPVERBO_SESSOES_RECREATE_CREATE_CARD_V14_START": css_validado,
    "20260505-sessoes-recreate-create-card-v14": template_validado,
}

for termo, conteudo in validacoes.items():
    if termo not in conteudo:
        fail_v14(f"validação falhou, termo ausente: {termo}")

print("OK: patch_sessoes_recriar_bloco_criar_v14 concluído.")
