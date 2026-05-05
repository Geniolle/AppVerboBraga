from pathlib import Path
import re
import sys

ROOT = Path.cwd()

AGENTS_UPPER_PATH = ROOT / "AGENTS.md"
AGENTS_TITLE_PATH = ROOT / "Agents.md"
TEMPLATE_PATH = ROOT / "templates" / "new_user.html"
JS_PATH = ROOT / "static" / "js" / "modules" / "sidebar_sections_layout_v1.js"
CSS_PATH = ROOT / "static" / "css" / "modules" / "sidebar_sections_layout_v1.css"

AGENTS_MARKER_START = "<!-- APPVERBO_SESSOES_SCOPE_GUARD_V11_START -->"
AGENTS_MARKER_END = "<!-- APPVERBO_SESSOES_SCOPE_GUARD_V11_END -->"

JS_MARKER_START = "// APPVERBO_SESSOES_SCOPE_GUARD_V11_START"
JS_MARKER_END = "// APPVERBO_SESSOES_SCOPE_GUARD_V11_END"

CSS_MARKER_START = "/* APPVERBO_SESSOES_SCOPE_GUARD_V11_START */"
CSS_MARKER_END = "/* APPVERBO_SESSOES_SCOPE_GUARD_V11_END */"

JS_CACHE = "/static/js/modules/sidebar_sections_layout_v1.js?v=20260505-sessoes-scope-guard-v11"
CSS_CACHE = "/static/css/modules/sidebar_sections_layout_v1.css?v=20260505-sessoes-scope-guard-v11"


def fail_v11(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


####################################################################################
# (1) RESOLVER AGENTS.md
####################################################################################

def resolve_agents_path_v11() -> Path:
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
        fail_v11(f"ficheiro não encontrado: {file_path}")


####################################################################################
# (3) ATUALIZAR AGENTS.md
####################################################################################

agents_path = resolve_agents_path_v11()
agents_content = agents_path.read_text(encoding="utf-8")

agents_rule = f"""{AGENTS_MARKER_START}
## Regra de escopo para subprocessos dinâmicos

Scripts de um subprocesso/aba não podem criar, mover ou exibir blocos fora da própria aba ativa.

Para a aba **Sessões**:

1. O bloco **Criar sessão** só pode aparecer quando a aba **Sessões** estiver ativa.
2. O card **Sessões inativas** só pode aparecer quando a aba **Sessões** estiver ativa.
3. Se a aba ativa for **Entidade**, **Utilizador**, **Menu** ou qualquer outra, o JavaScript de Sessões deve remover qualquer bloco órfão de Sessões.
4. A validação de escopo deve verificar aba ativa, visibilidade do card e contexto da URL/hash.
5. Nenhum bloco de Sessões pode aparecer no fim da aba Entidade ou fora do card correto do subprocesso.
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

print(f"OK: regra de escopo de Sessões atualizada em {agents_path}")


####################################################################################
# (4) ADICIONAR GUARDA DE ESCOPO NO JS
####################################################################################

js_content = JS_PATH.read_text(encoding="utf-8")

js_block = r'''// APPVERBO_SESSOES_SCOPE_GUARD_V11_START
(function () {
  "use strict";

  //###################################################################################
  // (1) NORMALIZAR TEXTO
  //###################################################################################

  function normalizarTextoScopeSessoesV11(valor) {
    return String(valor || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase();
  }

  //###################################################################################
  // (2) VALIDAR SE A ABA SESSOES ESTA ATIVA
  //###################################################################################

  function elementoVisivelScopeSessoesV11(elemento) {
    if (!elemento) {
      return false;
    }

    const estilo = window.getComputedStyle(elemento);

    if (
      estilo.display === "none" ||
      estilo.visibility === "hidden" ||
      elemento.hidden ||
      elemento.getAttribute("aria-hidden") === "true"
    ) {
      return false;
    }

    return Boolean(elemento.offsetWidth || elemento.offsetHeight || elemento.getClientRects().length);
  }

  function existeTabSessoesAtivoScopeSessoesV11() {
    const candidatos = Array.from(document.querySelectorAll("button, a, [role='tab'], .admin-tab, .tab-button"));

    return candidatos.some(function (elemento) {
      const texto = normalizarTextoScopeSessoesV11(elemento.textContent);

      if (texto !== "sessoes" && texto !== "sessões") {
        return false;
      }

      const ariaSelected = elemento.getAttribute("aria-selected") === "true";
      const className = String(elemento.className || "").toLowerCase();
      const isActive = className.includes("active") ||
        className.includes("ativo") ||
        className.includes("selected") ||
        className.includes("current");

      return ariaSelected || isActive;
    });
  }

  function cardSessoesVisivelScopeSessoesV11() {
    const card = document.getElementById("admin-sidebar-sections-card");

    if (!card) {
      return false;
    }

    if (!elementoVisivelScopeSessoesV11(card)) {
      return false;
    }

    const textoCard = normalizarTextoScopeSessoesV11(card.textContent);

    return textoCard.includes("sessoes do sidebar") ||
      textoCard.includes("sessões do sidebar") ||
      textoCard.includes("menu lateral") ||
      textoCard.includes("criar sessao") ||
      textoCard.includes("criar sessão");
  }

  function urlApontaParaSessoesScopeSessoesV11() {
    const hash = normalizarTextoScopeSessoesV11(window.location.hash);
    const search = normalizarTextoScopeSessoesV11(window.location.search);
    const href = normalizarTextoScopeSessoesV11(window.location.href);

    return hash.includes("admin-sidebar-sections-card") ||
      search.includes("admin_tab=sessoes") ||
      search.includes("admin_tab=sessões") ||
      href.includes("dynamic_process_section=sidebar") ||
      href.includes("dynamic_process_section=sessoes") ||
      href.includes("dynamic_process_section=sessões");
  }

  function abaSessoesAtivaScopeSessoesV11() {
    return existeTabSessoesAtivoScopeSessoesV11() ||
      cardSessoesVisivelScopeSessoesV11() ||
      urlApontaParaSessoesScopeSessoesV11();
  }

  //###################################################################################
  // (3) REMOVER BLOCOS ORFAOS DE SESSOES
  //###################################################################################

  function removerBlocosOrfaosSessoesV11() {
    if (abaSessoesAtivaScopeSessoesV11()) {
      return;
    }

    const seletores = [
      "#admin-sidebar-sections-create-card",
      "#admin-sidebar-sections-inactive-card",
      ".appverbo-sessoes-create-card-v3",
      ".appverbo-sessoes-create-card-v10",
      ".appverbo-sidebar-sections-inactive-card-v10"
    ];

    seletores.forEach(function (seletor) {
      Array.from(document.querySelectorAll(seletor)).forEach(function (elemento) {
        elemento.remove();
      });
    });
  }

  function ocultarBlocosSessoesQuandoForaDaAbaV11() {
    const ativo = abaSessoesAtivaScopeSessoesV11();

    Array.from(document.querySelectorAll("#admin-sidebar-sections-create-card, #admin-sidebar-sections-inactive-card")).forEach(function (elemento) {
      if (!ativo) {
        elemento.remove();
      }
    });
  }

  //###################################################################################
  // (4) INSTALAR GUARDA DE ESCOPO
  //###################################################################################

  function instalarScopeGuardSessoesV11() {
    removerBlocosOrfaosSessoesV11();
    ocultarBlocosSessoesQuandoForaDaAbaV11();

    window.setTimeout(removerBlocosOrfaosSessoesV11, 100);
    window.setTimeout(removerBlocosOrfaosSessoesV11, 400);
    window.setTimeout(removerBlocosOrfaosSessoesV11, 900);
    window.setTimeout(removerBlocosOrfaosSessoesV11, 1600);
    window.setTimeout(removerBlocosOrfaosSessoesV11, 2600);
  }

  document.addEventListener("click", function () {
    window.setTimeout(instalarScopeGuardSessoesV11, 80);
    window.setTimeout(instalarScopeGuardSessoesV11, 350);
  });

  window.addEventListener("hashchange", instalarScopeGuardSessoesV11);
  window.addEventListener("popstate", instalarScopeGuardSessoesV11);

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", instalarScopeGuardSessoesV11);
  }
  else {
    instalarScopeGuardSessoesV11();
  }
})();
// APPVERBO_SESSOES_SCOPE_GUARD_V11_END
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

print("OK: guarda de escopo V11 adicionada ao JS.")


####################################################################################
# (5) ADICIONAR CSS DEFENSIVO
####################################################################################

css_content = CSS_PATH.read_text(encoding="utf-8")

css_block = f'''{CSS_MARKER_START}

body:not(.appverbo-admin-sessoes-active-v11) .appverbo-sessoes-create-card-v10.appverbo-force-hide-v11,
body:not(.appverbo-admin-sessoes-active-v11) .appverbo-sidebar-sections-inactive-card-v10.appverbo-force-hide-v11 {{
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

print("OK: CSS defensivo V11 adicionado.")


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
    fail_v11("não encontrei sidebar_sections_layout_v1.js no template.")

if "static/css/modules/sidebar_sections_layout_v1.css" in template_content:
    template_content = re.sub(
        r"/static/css/modules/sidebar_sections_layout_v1\.css\?v=[^\"]+",
        CSS_CACHE,
        template_content,
    )
else:
    fail_v11("não encontrei sidebar_sections_layout_v1.css no template.")

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
    "APPVERBO_SESSOES_SCOPE_GUARD_V11_START": agents_validado,
    "O bloco **Criar sessão** só pode aparecer quando a aba **Sessões** estiver ativa.": agents_validado,
    "APPVERBO_SESSOES_SCOPE_GUARD_V11_START": js_validado,
    "removerBlocosOrfaosSessoesV11": js_validado,
    "abaSessoesAtivaScopeSessoesV11": js_validado,
    "#admin-sidebar-sections-create-card": js_validado,
    "#admin-sidebar-sections-inactive-card": js_validado,
    "APPVERBO_SESSOES_SCOPE_GUARD_V11_START": css_validado,
    "20260505-sessoes-scope-guard-v11": template_validado,
}

for termo, conteudo in validacoes.items():
    if termo not in conteudo:
        fail_v11(f"validação falhou, termo ausente: {termo}")

print("OK: patch_sessoes_remover_bloco_orfao_v11 concluído.")
