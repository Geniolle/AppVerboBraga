from pathlib import Path
import re
import sys

ROOT = Path.cwd()

AGENTS_UPPER_PATH = ROOT / "AGENTS.md"
AGENTS_TITLE_PATH = ROOT / "Agents.md"
TEMPLATE_PATH = ROOT / "templates" / "new_user.html"
JS_PATH = ROOT / "static" / "js" / "modules" / "sidebar_sections_layout_v1.js"
CSS_PATH = ROOT / "static" / "css" / "modules" / "sidebar_sections_layout_v1.css"

AGENTS_MARKER_START = "<!-- APPVERBO_SESSOES_REEXIBIR_CRIAR_AO_RETORNAR_V27_START -->"
AGENTS_MARKER_END = "<!-- APPVERBO_SESSOES_REEXIBIR_CRIAR_AO_RETORNAR_V27_END -->"

JS_MARKER_START = "// APPVERBO_SESSOES_REEXIBIR_CRIAR_AO_RETORNAR_V27_START"
JS_MARKER_END = "// APPVERBO_SESSOES_REEXIBIR_CRIAR_AO_RETORNAR_V27_END"

CSS_MARKER_START = "/* APPVERBO_SESSOES_REEXIBIR_CRIAR_AO_RETORNAR_V27_START */"
CSS_MARKER_END = "/* APPVERBO_SESSOES_REEXIBIR_CRIAR_AO_RETORNAR_V27_END */"

JS_CACHE = "/static/js/modules/sidebar_sections_layout_v1.js?v=20260505-sessoes-reexibir-criar-ao-retornar-v27"
CSS_CACHE = "/static/css/modules/sidebar_sections_layout_v1.css?v=20260505-sessoes-reexibir-criar-ao-retornar-v27"


def fail_v27(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


####################################################################################
# (1) RESOLVER AGENTS.md
####################################################################################

def resolve_agents_path_v27() -> Path:
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
        fail_v27(f"ficheiro não encontrado: {file_path}")


####################################################################################
# (3) ATUALIZAR AGENTS.md
####################################################################################

agents_path = resolve_agents_path_v27()
agents_content = agents_path.read_text(encoding="utf-8")

agents_rule = f"""{AGENTS_MARKER_START}
## Regra de persistência visual do card Criar sessão

Na aba **Sessões**:

1. O card de criação/edição `admin-sidebar-sections-form-card` deve permanecer visível sempre que a aba **Sessões** estiver ativa.
2. Ao alternar para Entidade, Utilizador ou Menu, os cards de Sessões podem ser ocultados.
3. Ao retornar para Sessões, devem reaparecer juntos:
   - `admin-sidebar-sections-form-card`;
   - `admin-sidebar-sections-card`;
   - `admin-sidebar-sections-inactive-card`.
4. O card de criação não deve depender de reconstrução por JavaScript.
5. O JavaScript só pode controlar visibilidade, sem recriar listas, formulários ou linhas.
6. Não usar `MutationObserver` para este comportamento.
{AGENTS_MARKER_END}"""

if AGENTS_MARKER_START in agents_content and AGENTS_MARKER_END in agents_content:
    agents_content = re.sub(
        re.escape(AGENTS_MARKER_START) + r"[\s\S]*?" + re.escape(AGENTS_MARKER_END),
        agents_rule,
        agents_content,
        count=1,
    )
else:
    agents_content = agents_content.rstrip() + "\n\n" + agents_rule + "\n"

agents_path.write_text(agents_content, encoding="utf-8")

print(f"OK: AGENTS.md atualizado em {agents_path}")


####################################################################################
# (4) GARANTIR CACHE BUSTER NO TEMPLATE
####################################################################################

template_content = TEMPLATE_PATH.read_text(encoding="utf-8")

if "admin-sidebar-sections-form-card" not in template_content:
    fail_v27("não encontrei admin-sidebar-sections-form-card no template. O server-render V25 precisa existir.")

if "data-admin-tab-pane=\"sessoes\"" not in template_content:
    fail_v27("não encontrei data-admin-tab-pane=\"sessoes\" no template.")

if "static/js/modules/sidebar_sections_layout_v1.js" in template_content:
    template_content = re.sub(
        r"/static/js/modules/sidebar_sections_layout_v1\.js\?v=[^\"]+",
        JS_CACHE,
        template_content,
    )
else:
    fail_v27("não encontrei sidebar_sections_layout_v1.js no template.")

if "static/css/modules/sidebar_sections_layout_v1.css" in template_content:
    template_content = re.sub(
        r"/static/css/modules/sidebar_sections_layout_v1\.css\?v=[^\"]+",
        CSS_CACHE,
        template_content,
    )
else:
    fail_v27("não encontrei sidebar_sections_layout_v1.css no template.")

TEMPLATE_PATH.write_text(template_content, encoding="utf-8")

print("OK: cache buster atualizado no template.")


####################################################################################
# (5) ADICIONAR JS V27 PARA REEXIBIR CARDS AO RETORNAR PARA SESSOES
####################################################################################

js_content = JS_PATH.read_text(encoding="utf-8")

js_block = r'''// APPVERBO_SESSOES_REEXIBIR_CRIAR_AO_RETORNAR_V27_START
(function () {
  "use strict";

  //###################################################################################
  // (1) NORMALIZACAO
  //###################################################################################

  function normalizarTextoSessoesV27(valor) {
    return String(valor || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase();
  }

  function elementoVisivelSessoesV27(elemento) {
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

  function elementoAtivoSessoesV27(elemento) {
    if (!elemento) {
      return false;
    }

    const classe = normalizarTextoSessoesV27(elemento.className || "");
    const parentClasse = elemento.parentElement
      ? normalizarTextoSessoesV27(elemento.parentElement.className || "")
      : "";

    return elemento.getAttribute("aria-selected") === "true" ||
      elemento.getAttribute("data-active") === "true" ||
      classe.includes("active") ||
      classe.includes("ativo") ||
      classe.includes("selected") ||
      classe.includes("current") ||
      classe.includes("is-active") ||
      parentClasse.includes("active") ||
      parentClasse.includes("ativo") ||
      parentClasse.includes("selected") ||
      parentClasse.includes("current") ||
      parentClasse.includes("is-active");
  }

  //###################################################################################
  // (2) DETETAR ABA ATIVA
  //###################################################################################

  function encontrarTabsSessoesV27() {
    return Array.from(
      document.querySelectorAll("button, a, [role='tab'], [data-admin-tab], .tab-button, .admin-tab")
    );
  }

  function tabAtivaPorTextoSessoesV27(textoEsperado) {
    const textoNormalizado = normalizarTextoSessoesV27(textoEsperado);

    return encontrarTabsSessoesV27().some(function (elemento) {
      const texto = normalizarTextoSessoesV27(elemento.textContent);
      const dataAdminTab = normalizarTextoSessoesV27(elemento.getAttribute("data-admin-tab"));
      const href = normalizarTextoSessoesV27(elemento.getAttribute("href"));

      const corresponde = texto === textoNormalizado ||
        dataAdminTab === textoNormalizado ||
        href.includes("admin_tab=" + textoNormalizado);

      return corresponde && elementoVisivelSessoesV27(elemento) && elementoAtivoSessoesV27(elemento);
    });
  }

  function cliqueFoiNaAbaSessoesV27(target) {
    const elemento = target && target.closest
      ? target.closest("button, a, [role='tab'], [data-admin-tab], .tab-button, .admin-tab")
      : null;

    if (!elemento) {
      return false;
    }

    const texto = normalizarTextoSessoesV27(elemento.textContent);
    const dataAdminTab = normalizarTextoSessoesV27(elemento.getAttribute("data-admin-tab"));
    const href = normalizarTextoSessoesV27(elemento.getAttribute("href"));

    return texto === "sessoes" ||
      dataAdminTab === "sessoes" ||
      href.includes("admin_tab=sessoes") ||
      href.includes("sidebar_sections_tab=sessoes");
  }

  function cliqueFoiNoutraAbaAdminV27(target) {
    const elemento = target && target.closest
      ? target.closest("button, a, [role='tab'], [data-admin-tab], .tab-button, .admin-tab")
      : null;

    if (!elemento) {
      return false;
    }

    const texto = normalizarTextoSessoesV27(elemento.textContent);
    const dataAdminTab = normalizarTextoSessoesV27(elemento.getAttribute("data-admin-tab"));
    const href = normalizarTextoSessoesV27(elemento.getAttribute("href"));

    return ["entidade", "utilizador", "menu", "contas"].some(function (aba) {
      return texto === aba || dataAdminTab === aba || href.includes("admin_tab=" + aba);
    });
  }

  function abaSessoesAtivaV27() {
    if (
      tabAtivaPorTextoSessoesV27("entidade") ||
      tabAtivaPorTextoSessoesV27("utilizador") ||
      tabAtivaPorTextoSessoesV27("menu") ||
      tabAtivaPorTextoSessoesV27("contas")
    ) {
      return false;
    }

    if (tabAtivaPorTextoSessoesV27("sessoes")) {
      return true;
    }

    const url = new URL(window.location.href);

    return url.searchParams.get("admin_tab") === "sessoes" ||
      url.searchParams.get("sidebar_sections_tab") === "sessoes" ||
      url.searchParams.has("sidebar_section_edit_key") ||
      window.location.hash === "#admin-sidebar-sections-card" ||
      window.location.hash === "#admin-sidebar-sections-form-card";
  }

  //###################################################################################
  // (3) MOSTRAR/OCULTAR CARDS DE SESSOES
  //###################################################################################

  function obterCardsSessoesV27() {
    return [
      document.getElementById("admin-sidebar-sections-form-card"),
      document.getElementById("admin-sidebar-sections-card"),
      document.getElementById("admin-sidebar-sections-inactive-card")
    ].filter(Boolean);
  }

  function mostrarCardsSessoesV27() {
    document.body.classList.add("appverbo-sessoes-tab-active-v27");

    obterCardsSessoesV27().forEach(function (card) {
      card.hidden = false;
      card.removeAttribute("hidden");
      card.setAttribute("aria-hidden", "false");
      card.style.display = "";
      card.style.visibility = "";
      card.style.opacity = "";
      card.classList.add("appverbo-sessoes-card-visible-v27");
    });
  }

  function ocultarCardsSessoesV27() {
    document.body.classList.remove("appverbo-sessoes-tab-active-v27");

    obterCardsSessoesV27().forEach(function (card) {
      card.hidden = true;
      card.setAttribute("aria-hidden", "true");
      card.style.display = "none";
      card.classList.remove("appverbo-sessoes-card-visible-v27");
    });
  }

  function aplicarVisibilidadeSessoesV27() {
    if (abaSessoesAtivaV27()) {
      mostrarCardsSessoesV27();
      return;
    }

    ocultarCardsSessoesV27();
  }

  function agendarAplicacaoSessoesV27() {
    window.setTimeout(aplicarVisibilidadeSessoesV27, 20);
    window.setTimeout(aplicarVisibilidadeSessoesV27, 90);
    window.setTimeout(aplicarVisibilidadeSessoesV27, 180);
    window.setTimeout(aplicarVisibilidadeSessoesV27, 360);
    window.setTimeout(aplicarVisibilidadeSessoesV27, 720);
  }

  //###################################################################################
  // (4) EVENTOS SEM MUTATIONOBSERVER
  //###################################################################################

  function instalarReexibicaoSessoesV27() {
    if (window.__appverboSessoesReexibirCriarV27 === true) {
      return;
    }

    window.__appverboSessoesReexibirCriarV27 = true;

    document.addEventListener("click", function (event) {
      if (cliqueFoiNaAbaSessoesV27(event.target)) {
        document.body.classList.add("appverbo-sessoes-click-pendente-v27");
        agendarAplicacaoSessoesV27();
        return;
      }

      if (cliqueFoiNoutraAbaAdminV27(event.target)) {
        window.setTimeout(function () {
          document.body.classList.remove("appverbo-sessoes-click-pendente-v27");
          aplicarVisibilidadeSessoesV27();
        }, 120);
        window.setTimeout(aplicarVisibilidadeSessoesV27, 320);
        return;
      }

      window.setTimeout(aplicarVisibilidadeSessoesV27, 200);
    }, true);

    window.addEventListener("hashchange", agendarAplicacaoSessoesV27);
    window.addEventListener("popstate", agendarAplicacaoSessoesV27);
    window.addEventListener("pageshow", agendarAplicacaoSessoesV27);

    agendarAplicacaoSessoesV27();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", instalarReexibicaoSessoesV27);
  }
  else {
    instalarReexibicaoSessoesV27();
  }
})();
// APPVERBO_SESSOES_REEXIBIR_CRIAR_AO_RETORNAR_V27_END
'''

if JS_MARKER_START in js_content and JS_MARKER_END in js_content:
    js_content = re.sub(
        re.escape(JS_MARKER_START) + r"[\s\S]*?" + re.escape(JS_MARKER_END),
        js_block,
        js_content,
        count=1,
    )
else:
    js_content = js_content.rstrip() + "\n\n" + js_block + "\n"

JS_PATH.write_text(js_content, encoding="utf-8")

print("OK: JS V27 aplicado.")


####################################################################################
# (6) ADICIONAR CSS V27
####################################################################################

css_content = CSS_PATH.read_text(encoding="utf-8")

css_block = f'''{CSS_MARKER_START}

body.appverbo-sessoes-tab-active-v27 #admin-sidebar-sections-form-card.appverbo-sessoes-form-card-v25,
body.appverbo-sessoes-tab-active-v27 #admin-sidebar-sections-card.appverbo-sessoes-list-card-v25,
body.appverbo-sessoes-tab-active-v27 #admin-sidebar-sections-inactive-card.appverbo-sessoes-inactive-card-v25,
#admin-sidebar-sections-form-card.appverbo-sessoes-card-visible-v27,
#admin-sidebar-sections-card.appverbo-sessoes-card-visible-v27,
#admin-sidebar-sections-inactive-card.appverbo-sessoes-card-visible-v27 {{
  display: block !important;
  visibility: visible !important;
  opacity: 1 !important;
}}

body.appverbo-sessoes-tab-active-v27 #admin-sidebar-sections-form-card[hidden],
body.appverbo-sessoes-tab-active-v27 #admin-sidebar-sections-card[hidden],
body.appverbo-sessoes-tab-active-v27 #admin-sidebar-sections-inactive-card[hidden] {{
  display: block !important;
}}

#admin-sidebar-sections-form-card.appverbo-sessoes-form-card-v25 {{
  min-height: 58px !important;
}}

#admin-sidebar-sections-form-card.appverbo-sessoes-form-card-v25 .entity-create-collapse {{
  display: block !important;
}}

{CSS_MARKER_END}'''

if CSS_MARKER_START in css_content and CSS_MARKER_END in css_content:
    css_content = re.sub(
        re.escape(CSS_MARKER_START) + r"[\s\S]*?" + re.escape(CSS_MARKER_END),
        css_block,
        css_content,
        count=1,
    )
else:
    css_content = css_content.rstrip() + "\n\n" + css_block + "\n"

CSS_PATH.write_text(css_content, encoding="utf-8")

print("OK: CSS V27 aplicado.")


####################################################################################
# (7) VALIDAR CONTEUDO
####################################################################################

agents_validado = agents_path.read_text(encoding="utf-8")
template_validado = TEMPLATE_PATH.read_text(encoding="utf-8")
js_validado = JS_PATH.read_text(encoding="utf-8")
css_validado = CSS_PATH.read_text(encoding="utf-8")

validacoes = {
    "APPVERBO_SESSOES_REEXIBIR_CRIAR_AO_RETORNAR_V27_START": agents_validado,
    "admin-sidebar-sections-form-card": template_validado,
    "20260505-sessoes-reexibir-criar-ao-retornar-v27": template_validado,
    "APPVERBO_SESSOES_REEXIBIR_CRIAR_AO_RETORNAR_V27_START": js_validado,
    "mostrarCardsSessoesV27": js_validado,
    "ocultarCardsSessoesV27": js_validado,
    "appverbo-sessoes-tab-active-v27": js_validado,
    "APPVERBO_SESSOES_REEXIBIR_CRIAR_AO_RETORNAR_V27_START": css_validado,
    "appverbo-sessoes-card-visible-v27": css_validado,
}

for termo, conteudo in validacoes.items():
    if termo not in conteudo:
        fail_v27(f"validação falhou, termo ausente: {termo}")

if "MutationObserver" in js_block:
    fail_v27("V27 não pode usar MutationObserver.")

print("OK: patch_sessoes_reexibir_criar_ao_retornar_v27 concluído.")
