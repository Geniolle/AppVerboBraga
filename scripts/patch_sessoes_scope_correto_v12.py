from pathlib import Path
import re
import sys

ROOT = Path.cwd()

AGENTS_UPPER_PATH = ROOT / "AGENTS.md"
AGENTS_TITLE_PATH = ROOT / "Agents.md"
TEMPLATE_PATH = ROOT / "templates" / "new_user.html"
JS_PATH = ROOT / "static" / "js" / "modules" / "sidebar_sections_layout_v1.js"
CSS_PATH = ROOT / "static" / "css" / "modules" / "sidebar_sections_layout_v1.css"

AGENTS_MARKER_START = "<!-- APPVERBO_SESSOES_SCOPE_CORRETO_V12_START -->"
AGENTS_MARKER_END = "<!-- APPVERBO_SESSOES_SCOPE_CORRETO_V12_END -->"

JS_MARKER_START = "// APPVERBO_SESSOES_SCOPE_CORRETO_V12_START"
JS_MARKER_END = "// APPVERBO_SESSOES_SCOPE_CORRETO_V12_END"

CSS_MARKER_START = "/* APPVERBO_SESSOES_SCOPE_CORRETO_V12_START */"
CSS_MARKER_END = "/* APPVERBO_SESSOES_SCOPE_CORRETO_V12_END */"

JS_CACHE = "/static/js/modules/sidebar_sections_layout_v1.js?v=20260505-sessoes-scope-correto-v12"
CSS_CACHE = "/static/css/modules/sidebar_sections_layout_v1.css?v=20260505-sessoes-scope-correto-v12"


def fail_v12(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


####################################################################################
# (1) RESOLVER AGENTS.md
####################################################################################

def resolve_agents_path_v12() -> Path:
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
        fail_v12(f"ficheiro não encontrado: {file_path}")


####################################################################################
# (3) ATUALIZAR AGENTS.md
####################################################################################

agents_path = resolve_agents_path_v12()
agents_content = agents_path.read_text(encoding="utf-8")

agents_rule = f"""{AGENTS_MARKER_START}
## Regra correta de escopo da aba Sessões

O botão **Criar sessão** pertence ao subprocesso/aba **Sessões** e deve aparecer sempre dentro dessa aba.

Regras:

1. Quando a aba ativa for **Sessões**, o card **Criar sessão** deve estar visível acima da lista de sessões.
2. Quando a aba ativa não for **Sessões**, qualquer card órfão de Sessões deve ser removido.
3. O card **Criar sessão** não pode aparecer no final da aba **Entidade** ou fora do subprocesso **Sessões**.
4. O card **Sessões inativas** também pertence somente ao subprocesso **Sessões**.
5. A validação deve considerar o botão/tab ativo pelo texto **Sessões**, classes de estado ativo e visibilidade real do card de sessões.
6. Não usar apenas URL/hash como critério, porque a URL pode manter hash de outro card mesmo com a aba Sessões ativa.
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

print(f"OK: regra correta de escopo da aba Sessões atualizada em {agents_path}")


####################################################################################
# (4) ADICIONAR GUARDA V12 NO JS
####################################################################################

js_content = JS_PATH.read_text(encoding="utf-8")

js_block = r'''// APPVERBO_SESSOES_SCOPE_CORRETO_V12_START
(function () {
  "use strict";

  //###################################################################################
  // (1) NORMALIZACAO
  //###################################################################################

  function normalizarTextoSessoesScopeV12(valor) {
    return String(valor || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase();
  }

  //###################################################################################
  // (2) UTILITARIOS DE VISIBILIDADE
  //###################################################################################

  function elementoVisivelSessoesScopeV12(elemento) {
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

  function estaAtivoPorClasseSessoesScopeV12(elemento) {
    const className = normalizarTextoSessoesScopeV12(elemento.className || "");

    return className.includes("active") ||
      className.includes("ativo") ||
      className.includes("selected") ||
      className.includes("current") ||
      className.includes("is-active");
  }

  function tabSessoesEstaAtivoV12() {
    const candidatos = Array.from(document.querySelectorAll("button, a, [role='tab'], [data-admin-tab], .tab-button, .admin-tab"));

    return candidatos.some(function (elemento) {
      const texto = normalizarTextoSessoesScopeV12(elemento.textContent);

      if (texto !== "sessoes") {
        return false;
      }

      if (!elementoVisivelSessoesScopeV12(elemento)) {
        return false;
      }

      if (elemento.getAttribute("aria-selected") === "true") {
        return true;
      }

      if (estaAtivoPorClasseSessoesScopeV12(elemento)) {
        return true;
      }

      const parent = elemento.parentElement;

      if (parent && estaAtivoPorClasseSessoesScopeV12(parent)) {
        return true;
      }

      return false;
    });
  }

  function tabEntidadeOuOutraEstaAtivaV12() {
    const candidatos = Array.from(document.querySelectorAll("button, a, [role='tab'], [data-admin-tab], .tab-button, .admin-tab"));

    return candidatos.some(function (elemento) {
      const texto = normalizarTextoSessoesScopeV12(elemento.textContent);

      if (!["entidade", "utilizador", "menu"].includes(texto)) {
        return false;
      }

      if (!elementoVisivelSessoesScopeV12(elemento)) {
        return false;
      }

      if (elemento.getAttribute("aria-selected") === "true") {
        return true;
      }

      if (estaAtivoPorClasseSessoesScopeV12(elemento)) {
        return true;
      }

      const parent = elemento.parentElement;

      if (parent && estaAtivoPorClasseSessoesScopeV12(parent)) {
        return true;
      }

      return false;
    });
  }

  function cardListaSessoesExisteEVisivelV12() {
    const card = document.getElementById("admin-sidebar-sections-card");

    if (!card || !elementoVisivelSessoesScopeV12(card)) {
      return false;
    }

    const texto = normalizarTextoSessoesScopeV12(card.textContent);

    return texto.includes("sessoes do sidebar") ||
      texto.includes("criar sessao") ||
      texto.includes("menu lateral") ||
      Boolean(card.querySelector(".appverbo-sidebar-section-row-v10, .appverbo-sidebar-section-row-v9, .appverbo-sidebar-section-row-v6, .appverbo-sidebar-section-row-v2"));
  }

  function abaSessoesEstaAtivaV12() {
    if (tabSessoesEstaAtivoV12()) {
      return true;
    }

    if (tabEntidadeOuOutraEstaAtivaV12()) {
      return false;
    }

    return cardListaSessoesExisteEVisivelV12();
  }

  //###################################################################################
  // (3) REMOVER SOMENTE ORFAOS
  //###################################################################################

  function cardEstaDentroAreaSessoesV12(card) {
    if (!card) {
      return false;
    }

    const cardLista = document.getElementById("admin-sidebar-sections-card");

    if (!cardLista || !cardLista.parentElement) {
      return false;
    }

    if (card.id === "admin-sidebar-sections-create-card") {
      return card.parentElement === cardLista.parentElement;
    }

    if (card.id === "admin-sidebar-sections-inactive-card") {
      return card.parentElement === cardLista.parentElement;
    }

    return false;
  }

  function removerCardsOrfaosSessoesV12() {
    const sessoesAtiva = abaSessoesEstaAtivaV12();

    Array.from(document.querySelectorAll("#admin-sidebar-sections-create-card, #admin-sidebar-sections-inactive-card")).forEach(function (card) {
      if (!sessoesAtiva) {
        card.remove();
        return;
      }

      if (!cardEstaDentroAreaSessoesV12(card)) {
        card.remove();
      }
    });
  }

  function marcarEstadoBodySessoesV12() {
    if (abaSessoesEstaAtivaV12()) {
      document.body.classList.add("appverbo-admin-sessoes-active-v12");
      document.body.classList.remove("appverbo-admin-sessoes-inactive-v12");
    }
    else {
      document.body.classList.remove("appverbo-admin-sessoes-active-v12");
      document.body.classList.add("appverbo-admin-sessoes-inactive-v12");
    }
  }

  //###################################################################################
  // (4) INSTALAR
  //###################################################################################

  function executarScopeCorretoSessoesV12() {
    marcarEstadoBodySessoesV12();
    removerCardsOrfaosSessoesV12();
  }

  function instalarScopeCorretoSessoesV12() {
    executarScopeCorretoSessoesV12();

    window.setTimeout(executarScopeCorretoSessoesV12, 80);
    window.setTimeout(executarScopeCorretoSessoesV12, 250);
    window.setTimeout(executarScopeCorretoSessoesV12, 700);
    window.setTimeout(executarScopeCorretoSessoesV12, 1300);
  }

  document.addEventListener("click", function () {
    window.setTimeout(instalarScopeCorretoSessoesV12, 80);
    window.setTimeout(instalarScopeCorretoSessoesV12, 300);
  });

  window.addEventListener("hashchange", instalarScopeCorretoSessoesV12);
  window.addEventListener("popstate", instalarScopeCorretoSessoesV12);

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", instalarScopeCorretoSessoesV12);
  }
  else {
    instalarScopeCorretoSessoesV12();
  }
})();
// APPVERBO_SESSOES_SCOPE_CORRETO_V12_END
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

print("OK: guarda de escopo correta V12 adicionada ao JS.")


####################################################################################
# (5) ADICIONAR CSS DEFENSIVO V12
####################################################################################

css_content = CSS_PATH.read_text(encoding="utf-8")

css_block = f'''{CSS_MARKER_START}

body.appverbo-admin-sessoes-inactive-v12 #admin-sidebar-sections-create-card,
body.appverbo-admin-sessoes-inactive-v12 #admin-sidebar-sections-inactive-card {{
  display: none !important;
}}

body.appverbo-admin-sessoes-active-v12 #admin-sidebar-sections-create-card,
body.appverbo-admin-sessoes-active-v12 #admin-sidebar-sections-inactive-card {{
  display: block;
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

print("OK: CSS defensivo V12 adicionado.")


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
    fail_v12("não encontrei sidebar_sections_layout_v1.js no template.")

if "static/css/modules/sidebar_sections_layout_v1.css" in template_content:
    template_content = re.sub(
        r"/static/css/modules/sidebar_sections_layout_v1\.css\?v=[^\"]+",
        CSS_CACHE,
        template_content,
    )
else:
    fail_v12("não encontrei sidebar_sections_layout_v1.css no template.")

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
    "APPVERBO_SESSOES_SCOPE_CORRETO_V12_START": agents_validado,
    "O botão **Criar sessão** pertence ao subprocesso/aba **Sessões**": agents_validado,
    "APPVERBO_SESSOES_SCOPE_CORRETO_V12_START": js_validado,
    "abaSessoesEstaAtivaV12": js_validado,
    "tabSessoesEstaAtivoV12": js_validado,
    "removerCardsOrfaosSessoesV12": js_validado,
    "APPVERBO_SESSOES_SCOPE_CORRETO_V12_START": css_validado,
    "appverbo-admin-sessoes-active-v12": css_validado,
    "20260505-sessoes-scope-correto-v12": template_validado,
}

for termo, conteudo in validacoes.items():
    if termo not in conteudo:
        fail_v12(f"validação falhou, termo ausente: {termo}")

print("OK: patch_sessoes_scope_correto_v12 concluído.")
