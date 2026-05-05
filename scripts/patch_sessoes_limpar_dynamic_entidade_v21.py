from pathlib import Path
import ast
import re
import sys

ROOT = Path.cwd()

AGENTS_UPPER_PATH = ROOT / "AGENTS.md"
AGENTS_TITLE_PATH = ROOT / "Agents.md"
TEMPLATE_PATH = ROOT / "templates" / "new_user.html"
SETTINGS_HANDLERS_PATH = ROOT / "appverbo" / "routes" / "profile" / "settings_handlers.py"
JS_PATH = ROOT / "static" / "js" / "modules" / "sidebar_sections_layout_v1.js"
CSS_PATH = ROOT / "static" / "css" / "modules" / "sidebar_sections_layout_v1.css"

AGENTS_MARKER_START = "<!-- APPVERBO_SESSOES_LIMPAR_DYNAMIC_ENTIDADE_V21_START -->"
AGENTS_MARKER_END = "<!-- APPVERBO_SESSOES_LIMPAR_DYNAMIC_ENTIDADE_V21_END -->"

JS_MARKER_START = "// APPVERBO_SESSOES_LIMPAR_DYNAMIC_ENTIDADE_V21_START"
JS_MARKER_END = "// APPVERBO_SESSOES_LIMPAR_DYNAMIC_ENTIDADE_V21_END"

CSS_MARKER_START = "/* APPVERBO_SESSOES_LIMPAR_DYNAMIC_ENTIDADE_V21_START */"
CSS_MARKER_END = "/* APPVERBO_SESSOES_LIMPAR_DYNAMIC_ENTIDADE_V21_END */"

JS_CACHE = "/static/js/modules/sidebar_sections_layout_v1.js?v=20260505-sessoes-limpar-dynamic-entidade-v21"
CSS_CACHE = "/static/css/modules/sidebar_sections_layout_v1.css?v=20260505-sessoes-limpar-dynamic-entidade-v21"


def fail_v21(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


####################################################################################
# (1) RESOLVER AGENTS.md
####################################################################################

def resolve_agents_path_v21() -> Path:
    if AGENTS_UPPER_PATH.exists():
        return AGENTS_UPPER_PATH

    if AGENTS_TITLE_PATH.exists():
        return AGENTS_TITLE_PATH

    AGENTS_UPPER_PATH.write_text("# AGENTS.md\n\n", encoding="utf-8")
    return AGENTS_UPPER_PATH


####################################################################################
# (2) VALIDAR FICHEIROS
####################################################################################

for file_path in [TEMPLATE_PATH, SETTINGS_HANDLERS_PATH, JS_PATH, CSS_PATH]:
    if not file_path.exists():
        fail_v21(f"ficheiro não encontrado: {file_path}")


####################################################################################
# (3) ATUALIZAR AGENTS.md
####################################################################################

agents_path = resolve_agents_path_v21()
agents_content = agents_path.read_text(encoding="utf-8")

agents_rule = f"""{AGENTS_MARKER_START}
## Regra para não contaminar Sessões com contexto da Entidade

Na aba **Sessões**:

1. A URL não pode manter `dynamic_process_section=field:entidade`.
2. Ao editar, guardar, cancelar ou retornar para **Sessões**, remover sempre:
   - `dynamic_process_section`;
   - `settings_edit_key`;
   - `settings_action`;
   - `settings_tab`;
   - `sidebar_section_return_url`;
   - `appverbo_after_save`.
3. O backend de `/settings/menu/sidebar-section-save` também não pode preservar `dynamic_process_section` no redirect.
4. O card **Sessões inativas** deve ser renderizado pelo BD sempre que `admin_tab=sessoes` ou `sidebar_sections_tab=sessoes`.
5. Uma sessão com `status=inativo` ou `is_active=false` deve aparecer no card **Sessões inativas**.
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

print(f"OK: regra V21 atualizada em {agents_path}")


####################################################################################
# (4) CORRIGIR BACKEND PARA NAO PRESERVAR dynamic_process_section
####################################################################################

settings_content = SETTINGS_HANDLERS_PATH.read_text(encoding="utf-8")

blocked_params_old = '''        "settings_edit_key",
        "settings_action",
        "settings_tab",
        "sidebar_section_edit_key",
        "sidebar_section_return_url",
        "success",
        "error",
'''

blocked_params_new = '''        "settings_edit_key",
        "settings_action",
        "settings_tab",
        "sidebar_section_edit_key",
        "sidebar_section_return_url",
        "dynamic_process_section",
        "appverbo_after_save",
        "success",
        "error",
'''

if blocked_params_old in settings_content:
    settings_content = settings_content.replace(blocked_params_old, blocked_params_new, 1)
elif '"dynamic_process_section",' not in settings_content:
    fail_v21("não encontrei blocked_params do endpoint de Sessões para adicionar dynamic_process_section.")

try:
    ast.parse(settings_content)
except SyntaxError as exc:
    fail_v21(f"settings_handlers.py ficaria inválido: {exc}")

SETTINGS_HANDLERS_PATH.write_text(settings_content, encoding="utf-8")

print("OK: backend atualizado para remover dynamic_process_section do redirect.")


####################################################################################
# (5) ADICIONAR JS V21 PARA LIMPAR URL E RENDERIZAR INATIVAS PELO BD
####################################################################################

js_content = JS_PATH.read_text(encoding="utf-8")

js_block = r'''// APPVERBO_SESSOES_LIMPAR_DYNAMIC_ENTIDADE_V21_START
(function () {
  "use strict";

  //###################################################################################
  // (1) NORMALIZACAO
  //###################################################################################

  function normalizarTextoSessoesV21(valor) {
    return String(valor || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase();
  }

  function criarChaveSessoesV21(valor) {
    return normalizarTextoSessoesV21(valor)
      .replace(/[^a-z0-9]+/g, "_")
      .replace(/_+/g, "_")
      .replace(/^_+|_+$/g, "");
  }

  function normalizarEstadoSessoesV21(sessao) {
    if (sessao && sessao.is_active === false) {
      return "inativo";
    }

    const status = normalizarTextoSessoesV21(
      sessao ? (sessao.status || sessao.status_label || "") : ""
    );

    if (["inativo", "inactive", "0", "false", "nao", "não", "off"].includes(status)) {
      return "inativo";
    }

    return "ativo";
  }

  function labelSistemaSessoesV21(valor, fallback) {
    const sistema = normalizarTextoSessoesV21(valor);

    if (sistema === "owner") {
      return "Owner";
    }

    if (sistema === "legado") {
      return "Legado";
    }

    return fallback || "Owner e Legado";
  }

  //###################################################################################
  // (2) LIMPAR URL DE SESSOES
  //###################################################################################

  function urlEhContextoSessoesV21(url) {
    return url.searchParams.get("admin_tab") === "sessoes" ||
      url.searchParams.get("sidebar_sections_tab") === "sessoes" ||
      url.searchParams.get("target") === "admin-sidebar-sections-card" ||
      url.searchParams.has("sidebar_section_edit_key") ||
      window.location.hash === "#admin-sidebar-sections-card";
  }

  function limparUrlSessoesV21() {
    const url = new URL(window.location.href);

    if (!urlEhContextoSessoesV21(url)) {
      return;
    }

    let alterou = false;

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
        alterou = true;
      }
    });

    url.searchParams.set("menu", "administrativo");
    url.searchParams.set("admin_tab", "sessoes");
    url.searchParams.set("sidebar_sections_tab", "sessoes");
    url.searchParams.set("target", "admin-sidebar-sections-card");

    if (url.hash !== "#admin-sidebar-sections-card") {
      url.hash = "admin-sidebar-sections-card";
      alterou = true;
    }

    if (alterou) {
      window.history.replaceState({}, document.title, url.pathname + url.search + url.hash);
    }
  }

  function obterUrlEditarSessaoV21(chave) {
    const url = new URL(window.location.href);

    url.searchParams.delete("dynamic_process_section");
    url.searchParams.delete("settings_edit_key");
    url.searchParams.delete("settings_action");
    url.searchParams.delete("settings_tab");
    url.searchParams.delete("sidebar_section_return_url");
    url.searchParams.delete("appverbo_after_save");
    url.searchParams.delete("success");
    url.searchParams.delete("error");

    url.searchParams.set("menu", "administrativo");
    url.searchParams.set("admin_tab", "sessoes");
    url.searchParams.set("sidebar_sections_tab", "sessoes");
    url.searchParams.set("target", "admin-sidebar-sections-card");
    url.searchParams.set("sidebar_section_edit_key", criarChaveSessoesV21(chave));
    url.hash = "admin-sidebar-sections-card";

    return url.pathname + url.search + url.hash;
  }

  function obterUrlRetornoSessaoV21() {
    const url = new URL(window.location.href);

    url.searchParams.delete("dynamic_process_section");
    url.searchParams.delete("settings_edit_key");
    url.searchParams.delete("settings_action");
    url.searchParams.delete("settings_tab");
    url.searchParams.delete("sidebar_section_return_url");
    url.searchParams.delete("sidebar_section_edit_key");
    url.searchParams.delete("appverbo_after_save");
    url.searchParams.delete("success");
    url.searchParams.delete("error");

    url.searchParams.set("menu", "administrativo");
    url.searchParams.set("admin_tab", "sessoes");
    url.searchParams.set("sidebar_sections_tab", "sessoes");
    url.searchParams.set("target", "admin-sidebar-sections-card");
    url.hash = "admin-sidebar-sections-card";

    return url.pathname + url.search + url.hash;
  }

  //###################################################################################
  // (3) CARREGAR SESSOES DO BD
  //###################################################################################

  async function carregarSessoesDoBdV21() {
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
      console.warn("APPVERBO V21: falha ao carregar sessões do BD.", error);
    }

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

  function normalizarSessaoV21(sessao) {
    if (!sessao || typeof sessao !== "object") {
      return null;
    }

    const label = String(sessao.label || sessao.name || sessao.title || "").trim();
    const key = criarChaveSessoesV21(sessao.key || sessao.section_key || label);

    if (!label || !key) {
      return null;
    }

    const status = normalizarEstadoSessoesV21(sessao);
    const sistema = String(sessao.visibility_scope_mode || sessao.scope_mode || "all").trim() || "all";

    return {
      key: key,
      label: label,
      visibility_scope_mode: sistema,
      visibility_scope_label: sessao.visibility_scope_label || labelSistemaSessoesV21(sistema, ""),
      status: status,
      is_active: status === "ativo",
      status_label: status === "inativo" ? "Inativo" : "Ativo"
    };
  }

  //###################################################################################
  // (4) RENDERIZAR CARD DE INATIVAS
  //###################################################################################

  function criarBotaoAcaoV21(tipo, titulo, texto) {
    const botao = document.createElement("button");
    botao.type = "button";
    botao.className = "appverbo-sidebar-section-action-btn-v2 appverbo-sidebar-section-action-btn-v21";
    botao.dataset.sidebarSectionActionV21 = tipo;
    botao.title = titulo;
    botao.setAttribute("aria-label", titulo);
    botao.textContent = texto;
    return botao;
  }

  function criarLinhaInativaV21(sessao) {
    const tr = document.createElement("tr");
    tr.className = "appverbo-sidebar-section-row-v2 appverbo-sidebar-section-row-v10 appverbo-sidebar-section-row-v21";
    tr.dataset.sectionKeyV21 = sessao.key;
    tr.dataset.sectionKeyV10 = sessao.key;

    const tdMenu = document.createElement("td");
    tdMenu.className = "appverbo-sidebar-section-menu-cell-v2";
    tdMenu.textContent = sessao.label;

    const tdSistema = document.createElement("td");
    tdSistema.className = "appverbo-sidebar-section-system-cell-v2";
    tdSistema.textContent = sessao.visibility_scope_label || labelSistemaSessoesV21(sessao.visibility_scope_mode, "");

    const tdEstado = document.createElement("td");
    tdEstado.className = "appverbo-sidebar-section-state-cell-v2";

    const badge = document.createElement("span");
    badge.className = "appverbo-sidebar-section-state-badge-v2 appverbo-sidebar-section-state-badge-inativo-v21";
    badge.textContent = "Inativo";

    tdEstado.appendChild(badge);

    const tdAcoes = document.createElement("td");
    tdAcoes.className = "appverbo-sidebar-section-actions-cell-v2";

    const actions = document.createElement("div");
    actions.className = "appverbo-sidebar-section-actions-v2";
    actions.appendChild(criarBotaoAcaoV21("view", "Visualizar detalhes", "👁"));
    actions.appendChild(criarBotaoAcaoV21("edit", "Editar sessão", "✎"));

    tdAcoes.appendChild(actions);

    tr.appendChild(tdMenu);
    tr.appendChild(tdSistema);
    tr.appendChild(tdEstado);
    tr.appendChild(tdAcoes);

    return tr;
  }

  function criarTabelaInativasV21(sessoesInativas) {
    const wrap = document.createElement("div");
    wrap.className = "appverbo-sidebar-sections-table-wrap-v2 appverbo-sidebar-sections-table-wrap-v21";

    const table = document.createElement("table");
    table.className = "appverbo-sidebar-sections-table-v2 appverbo-sidebar-sections-table-v21";

    const thead = document.createElement("thead");
    thead.innerHTML = "<tr><th>MENU LATERAL</th><th>SISTEMA</th><th>ESTADO</th><th>AÇÕES</th></tr>";

    const tbody = document.createElement("tbody");
    tbody.className = "appverbo-sidebar-sections-body-v2 appverbo-sidebar-sections-body-v21";

    sessoesInativas.forEach(function (sessao) {
      tbody.appendChild(criarLinhaInativaV21(sessao));
    });

    table.appendChild(thead);
    table.appendChild(tbody);
    wrap.appendChild(table);

    return wrap;
  }

  function removerInativasDoCardPrincipalV21(sessoesInativas) {
    const cardAtivas = document.getElementById("admin-sidebar-sections-card");

    if (!cardAtivas) {
      return;
    }

    const chavesInativas = new Set(
      sessoesInativas.map(function (sessao) {
        return criarChaveSessoesV21(sessao.key);
      })
    );

    Array.from(cardAtivas.querySelectorAll("tr")).forEach(function (linha) {
      const datasetKey = linha.dataset.sectionKeyV21 ||
        linha.dataset.sectionKeyV20 ||
        linha.dataset.sectionKeyV10 ||
        linha.dataset.sectionKeyV9 ||
        linha.dataset.sectionKeyV6 ||
        linha.dataset.sectionKeyV2 ||
        "";

      const hiddenKey = linha.querySelector('[name="section_key"]');
      const key = criarChaveSessoesV21(datasetKey || (hiddenKey ? hiddenKey.value : ""));

      if (key && chavesInativas.has(key)) {
        linha.remove();
      }
    });
  }

  async function renderizarInativasV21() {
    limparUrlSessoesV21();

    const url = new URL(window.location.href);
    const contextoSessoes = url.searchParams.get("admin_tab") === "sessoes" ||
      url.searchParams.get("sidebar_sections_tab") === "sessoes" ||
      url.searchParams.get("target") === "admin-sidebar-sections-card" ||
      document.getElementById("admin-sidebar-sections-card");

    if (!contextoSessoes) {
      return;
    }

    const cardAtivas = document.getElementById("admin-sidebar-sections-card");

    if (!cardAtivas || !cardAtivas.parentElement) {
      return;
    }

    const sessoesRaw = await carregarSessoesDoBdV21();
    const sessoes = sessoesRaw.map(normalizarSessaoV21).filter(Boolean);
    const sessoesInativas = sessoes.filter(function (sessao) {
      return sessao.status !== "ativo" || sessao.is_active === false;
    });

    removerInativasDoCardPrincipalV21(sessoesInativas);

    let cardInativas = document.getElementById("admin-sidebar-sections-inactive-card");

    if (!cardInativas) {
      cardInativas = document.createElement("section");
      cardInativas.id = "admin-sidebar-sections-inactive-card";
    }

    cardInativas.className = "card appverbo-sidebar-sections-inactive-card-v21";
    cardInativas.hidden = false;
    cardInativas.style.display = "";
    cardInativas.style.visibility = "";

    if (cardInativas.parentElement !== cardAtivas.parentElement) {
      cardAtivas.parentElement.insertBefore(cardInativas, cardAtivas.nextSibling);
    }
    else if (cardInativas.previousElementSibling !== cardAtivas) {
      cardAtivas.parentElement.insertBefore(cardInativas, cardAtivas.nextSibling);
    }

    cardInativas.innerHTML = "";

    const titulo = document.createElement("h2");
    titulo.className = "appverbo-sidebar-section-list-main-title-v21";
    titulo.textContent = "Sessões inativas";
    cardInativas.appendChild(titulo);

    if (sessoesInativas.length) {
      cardInativas.appendChild(criarTabelaInativasV21(sessoesInativas));
    }
    else {
      const vazio = document.createElement("p");
      vazio.className = "appverbo-sidebar-section-empty-text-v21";
      vazio.textContent = "Sem sessões inativas.";
      cardInativas.appendChild(vazio);
    }
  }

  //###################################################################################
  // (5) EVENTOS DO CARD
  //###################################################################################

  function instalarEventosSessoesV21() {
    if (window.__appverboSessoesEventosV21 === true) {
      return;
    }

    window.__appverboSessoesEventosV21 = true;

    document.addEventListener("click", function (event) {
      const botao = event.target.closest("[data-sidebar-section-action-v21]");

      if (!botao) {
        return;
      }

      const linha = botao.closest("tr.appverbo-sidebar-section-row-v21");

      if (!linha) {
        return;
      }

      const acao = botao.dataset.sidebarSectionActionV21;
      const chave = linha.dataset.sectionKeyV21 || "";
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
        window.location.href = obterUrlEditarSessaoV21(chave);
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

      returnInput.value = obterUrlRetornoSessaoV21();
    }, true);
  }

  //###################################################################################
  // (6) INSTALAR
  //###################################################################################

  function agendarRenderV21() {
    window.setTimeout(renderizarInativasV21, 80);
    window.setTimeout(renderizarInativasV21, 250);
    window.setTimeout(renderizarInativasV21, 650);
    window.setTimeout(renderizarInativasV21, 1300);
    window.setTimeout(renderizarInativasV21, 2400);
  }

  function instalarV21() {
    limparUrlSessoesV21();
    instalarEventosSessoesV21();
    agendarRenderV21();

    document.addEventListener("click", function () {
      agendarRenderV21();
    });

    window.addEventListener("hashchange", agendarRenderV21);
    window.addEventListener("popstate", agendarRenderV21);

    const observer = new MutationObserver(function () {
      window.clearTimeout(window.__appverboSessoesRenderV21Timer);
      window.__appverboSessoesRenderV21Timer = window.setTimeout(renderizarInativasV21, 160);
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ["class", "hidden", "style", "aria-selected", "aria-hidden"]
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", instalarV21);
  }
  else {
    instalarV21();
  }
})();
// APPVERBO_SESSOES_LIMPAR_DYNAMIC_ENTIDADE_V21_END
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

print("OK: JS V21 aplicado para limpar dynamic_process_section e renderizar inativas.")


####################################################################################
# (6) CSS V21
####################################################################################

css_content = CSS_PATH.read_text(encoding="utf-8")

css_block = f'''{CSS_MARKER_START}

#admin-sidebar-sections-inactive-card.appverbo-sidebar-sections-inactive-card-v21 {{
  display: block !important;
  visibility: visible !important;
  margin-top: 12px !important;
  padding: 16px !important;
  border: 1px solid #d5dceb !important;
  border-radius: 12px !important;
  background: #ffffff !important;
  box-sizing: border-box !important;
}}

#admin-sidebar-sections-inactive-card .appverbo-sidebar-section-list-main-title-v21 {{
  margin: 0 0 12px !important;
  color: #12213a !important;
  font-size: 22px !important;
  font-weight: 800 !important;
}}

#admin-sidebar-sections-inactive-card .appverbo-sidebar-section-empty-text-v21 {{
  margin: 0 !important;
  color: #52607a !important;
  font-size: 14px !important;
}}

#admin-sidebar-sections-inactive-card .appverbo-sidebar-sections-table-wrap-v21,
#admin-sidebar-sections-inactive-card .appverbo-sidebar-sections-table-v21 {{
  width: 100% !important;
}}

#admin-sidebar-sections-inactive-card .appverbo-sidebar-section-row-v21 td {{
  height: 44px !important;
}}

#admin-sidebar-sections-inactive-card .appverbo-sidebar-section-state-badge-inativo-v21 {{
  border-color: #f0c36d !important;
  background: #fff7e0 !important;
  color: #8a5a00 !important;
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

print("OK: CSS V21 aplicado.")


####################################################################################
# (7) ATUALIZAR CACHE BUSTER
####################################################################################

template_content = TEMPLATE_PATH.read_text(encoding="utf-8")

if "static/js/modules/sidebar_sections_layout_v1.js" in template_content:
    template_content = re.sub(
        r"/static/js/modules/sidebar_sections_layout_v1\.js\?v=[^\"]+",
        JS_CACHE,
        template_content,
    )
else:
    fail_v21("não encontrei sidebar_sections_layout_v1.js no template.")

if "static/css/modules/sidebar_sections_layout_v1.css" in template_content:
    template_content = re.sub(
        r"/static/css/modules/sidebar_sections_layout_v1\.css\?v=[^\"]+",
        CSS_CACHE,
        template_content,
    )
else:
    fail_v21("não encontrei sidebar_sections_layout_v1.css no template.")

TEMPLATE_PATH.write_text(template_content, encoding="utf-8")

print("OK: cache buster atualizado.")


####################################################################################
# (8) VALIDAR CONTEUDO
####################################################################################

agents_validado = agents_path.read_text(encoding="utf-8")
settings_validado = SETTINGS_HANDLERS_PATH.read_text(encoding="utf-8")
js_validado = JS_PATH.read_text(encoding="utf-8")
css_validado = CSS_PATH.read_text(encoding="utf-8")
template_validado = TEMPLATE_PATH.read_text(encoding="utf-8")

validacoes = {
    "APPVERBO_SESSOES_LIMPAR_DYNAMIC_ENTIDADE_V21_START": agents_validado,
    '"dynamic_process_section",': settings_validado,
    "APPVERBO_SESSOES_LIMPAR_DYNAMIC_ENTIDADE_V21_START": js_validado,
    "limparUrlSessoesV21": js_validado,
    "renderizarInativasV21": js_validado,
    "dynamic_process_section": js_validado,
    "Sessões inativas": js_validado,
    "APPVERBO_SESSOES_LIMPAR_DYNAMIC_ENTIDADE_V21_START": css_validado,
    "appverbo-sidebar-sections-inactive-card-v21": css_validado,
    "20260505-sessoes-limpar-dynamic-entidade-v21": template_validado,
}

for termo, conteudo in validacoes.items():
    if termo not in conteudo:
        fail_v21(f"validação falhou, termo ausente: {termo}")

try:
    ast.parse(settings_validado)
except SyntaxError as exc:
    fail_v21(f"Python final inválido: {exc}")

print("OK: patch_sessoes_limpar_dynamic_entidade_v21 concluído.")
