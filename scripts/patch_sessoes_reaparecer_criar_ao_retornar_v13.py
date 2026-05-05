from pathlib import Path
import re
import sys

ROOT = Path.cwd()

AGENTS_UPPER_PATH = ROOT / "AGENTS.md"
AGENTS_TITLE_PATH = ROOT / "Agents.md"
TEMPLATE_PATH = ROOT / "templates" / "new_user.html"
JS_PATH = ROOT / "static" / "js" / "modules" / "sidebar_sections_layout_v1.js"
CSS_PATH = ROOT / "static" / "css" / "modules" / "sidebar_sections_layout_v1.css"

AGENTS_MARKER_START = "<!-- APPVERBO_SESSOES_RELOAD_ON_RETURN_V13_START -->"
AGENTS_MARKER_END = "<!-- APPVERBO_SESSOES_RELOAD_ON_RETURN_V13_END -->"

JS_MARKER_START = "// APPVERBO_SESSOES_RELOAD_ON_TAB_RETURN_V13_START"
JS_MARKER_END = "// APPVERBO_SESSOES_RELOAD_ON_TAB_RETURN_V13_END"

CSS_MARKER_START = "/* APPVERBO_SESSOES_RELOAD_ON_TAB_RETURN_V13_START */"
CSS_MARKER_END = "/* APPVERBO_SESSOES_RELOAD_ON_TAB_RETURN_V13_END */"

JS_CACHE = "/static/js/modules/sidebar_sections_layout_v1.js?v=20260505-sessoes-return-tab-v13"
CSS_CACHE = "/static/css/modules/sidebar_sections_layout_v1.css?v=20260505-sessoes-return-tab-v13"


def fail_v13(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


####################################################################################
# (1) RESOLVER AGENTS.md
####################################################################################

def resolve_agents_path_v13() -> Path:
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
        fail_v13(f"ficheiro não encontrado: {file_path}")


####################################################################################
# (3) ATUALIZAR AGENTS.md
####################################################################################

agents_path = resolve_agents_path_v13()
agents_content = agents_path.read_text(encoding="utf-8")

agents_rule = f"""{AGENTS_MARKER_START}
## Regra para retorno à aba Sessões

Na área administrativa, ao navegar entre as abas do subprocesso e voltar para **Sessões**:

1. O card **Criar sessão** deve reaparecer automaticamente dentro da aba **Sessões**.
2. O card **Sessões inativas** deve reaparecer automaticamente dentro da aba **Sessões**.
3. A lista de sessões deve ser reidratada novamente a partir do BD/configuração.
4. Blocos de Sessões continuam proibidos fora da aba **Sessões**.
5. Ao sair para **Entidade**, **Utilizador** ou **Menu**, qualquer bloco órfão de Sessões deve ser removido.
6. Ao retornar para **Sessões**, a montagem da aba deve ser executada novamente mesmo sem reload da página.
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

print(f"OK: regra de retorno à aba Sessões atualizada em {agents_path}")


####################################################################################
# (4) ATUALIZAR JS PARA REIDRATAR AO RETORNAR PARA SESSÕES
####################################################################################

js_content = JS_PATH.read_text(encoding="utf-8")

if "function instalarSessoesV10(force)" not in js_content:
    fail_v13("não encontrei function instalarSessoesV10(force). Execute primeiro o patch V10 das Sessões.")

helper_block = r'''  // APPVERBO_SESSOES_RELOAD_ON_TAB_RETURN_V13_START
  function normalizarTextoRetornoSessoesV13(valor) {
    return String(valor || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase();
  }

  function elementoVisivelRetornoSessoesV13(elemento) {
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

  function elementoAtivoRetornoSessoesV13(elemento) {
    const className = normalizarTextoRetornoSessoesV13(elemento.className || "");

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
    const parentClass = parent ? normalizarTextoRetornoSessoesV13(parent.className || "") : "";

    return parentClass.includes("active") ||
      parentClass.includes("ativo") ||
      parentClass.includes("selected") ||
      parentClass.includes("current") ||
      parentClass.includes("is-active");
  }

  function alvoEhTabSessoesRetornoV13(alvo) {
    const tab = alvo && alvo.closest
      ? alvo.closest("button, a, [role='tab'], [data-admin-tab], .tab-button, .admin-tab")
      : null;

    if (!tab) {
      return false;
    }

    const texto = normalizarTextoRetornoSessoesV13(tab.textContent);

    return texto === "sessoes";
  }

  function abaSessoesAtivaRetornoV13() {
    const candidatos = Array.from(document.querySelectorAll("button, a, [role='tab'], [data-admin-tab], .tab-button, .admin-tab"));

    const tabSessoesAtiva = candidatos.some(function (elemento) {
      const texto = normalizarTextoRetornoSessoesV13(elemento.textContent);

      return texto === "sessoes" &&
        elementoVisivelRetornoSessoesV13(elemento) &&
        elementoAtivoRetornoSessoesV13(elemento);
    });

    if (tabSessoesAtiva) {
      return true;
    }

    const outraTabAtiva = candidatos.some(function (elemento) {
      const texto = normalizarTextoRetornoSessoesV13(elemento.textContent);

      return ["entidade", "utilizador", "menu"].includes(texto) &&
        elementoVisivelRetornoSessoesV13(elemento) &&
        elementoAtivoRetornoSessoesV13(elemento);
    });

    if (outraTabAtiva) {
      return false;
    }

    const card = document.getElementById("admin-sidebar-sections-card");

    if (!card || !elementoVisivelRetornoSessoesV13(card)) {
      return false;
    }

    const textoCard = normalizarTextoRetornoSessoesV13(card.textContent);

    return textoCard.includes("sessoes do sidebar") ||
      textoCard.includes("criar sessao") ||
      textoCard.includes("menu lateral");
  }

  function marcarBodySessoesAtivaRetornoV13() {
    document.body.classList.add("appverbo-admin-sessoes-active-v12");
    document.body.classList.add("appverbo-admin-sessoes-active-v13");
    document.body.classList.remove("appverbo-admin-sessoes-inactive-v12");
    document.body.classList.remove("appverbo-admin-sessoes-inactive-v13");
  }

  function marcarBodySessoesInativaRetornoV13() {
    document.body.classList.remove("appverbo-admin-sessoes-active-v12");
    document.body.classList.remove("appverbo-admin-sessoes-active-v13");
    document.body.classList.add("appverbo-admin-sessoes-inactive-v13");
  }

  function removerBlocosOrfaosRetornoSessoesV13() {
    if (abaSessoesAtivaRetornoV13()) {
      return;
    }

    marcarBodySessoesInativaRetornoV13();

    Array.from(document.querySelectorAll("#admin-sidebar-sections-create-card, #admin-sidebar-sections-inactive-card")).forEach(function (card) {
      card.remove();
    });
  }

  function reidratarSessoesAoRetornarV13() {
    if (!abaSessoesAtivaRetornoV13()) {
      removerBlocosOrfaosRetornoSessoesV13();
      return;
    }

    marcarBodySessoesAtivaRetornoV13();

    try {
      instaladoV10 = false;
      instalarSessoesV10(true);
    }
    catch (error) {
      console.warn("APPVERBO V13: falha ao reidratar aba Sessões no retorno.", error);
    }
  }

  function agendarReidratarSessoesAoRetornarV13() {
    marcarBodySessoesAtivaRetornoV13();

    window.setTimeout(reidratarSessoesAoRetornarV13, 80);
    window.setTimeout(reidratarSessoesAoRetornarV13, 250);
    window.setTimeout(reidratarSessoesAoRetornarV13, 600);
    window.setTimeout(reidratarSessoesAoRetornarV13, 1100);
  }

  function instalarEventosRetornoSessoesV13() {
    if (window.__appverboSessoesReturnV13Installed === true) {
      return;
    }

    window.__appverboSessoesReturnV13Installed = true;

    document.addEventListener("click", function (event) {
      if (alvoEhTabSessoesRetornoV13(event.target)) {
        agendarReidratarSessoesAoRetornarV13();
        return;
      }

      window.setTimeout(removerBlocosOrfaosRetornoSessoesV13, 120);
      window.setTimeout(removerBlocosOrfaosRetornoSessoesV13, 450);
    });

    window.addEventListener("hashchange", function () {
      window.setTimeout(reidratarSessoesAoRetornarV13, 120);
    });

    window.addEventListener("popstate", function () {
      window.setTimeout(reidratarSessoesAoRetornarV13, 120);
    });
  }
  // APPVERBO_SESSOES_RELOAD_ON_TAB_RETURN_V13_END

'''

if JS_MARKER_START in js_content and JS_MARKER_END in js_content:
    helper_pattern = re.compile(
        re.escape(JS_MARKER_START) + r"[\s\S]*?" + re.escape(JS_MARKER_END) + r"\n?",
        re.S,
    )
    js_content = helper_pattern.sub(helper_block, js_content, count=1)
else:
    anchor = "  async function instalarSessoesV10(force) {"

    if anchor not in js_content:
        fail_v13("não encontrei âncora async function instalarSessoesV10(force).")

    js_content = js_content.replace(anchor, helper_block + anchor, 1)

if "instalarEventosRetornoSessoesV13();" not in js_content:
    iniciar_anchor = '''  function iniciarSessoesV10() {
'''

    if iniciar_anchor not in js_content:
        fail_v13("não encontrei function iniciarSessoesV10().")

    js_content = js_content.replace(
        iniciar_anchor,
        '''  function iniciarSessoesV10() {
    instalarEventosRetornoSessoesV13();

''',
        1,
    )

if "document.body.classList.add(\"appverbo-admin-sessoes-active-v13\")" not in js_content:
    fail_v13("marcação de body active V13 não foi adicionada.")

JS_PATH.write_text(js_content, encoding="utf-8")

print("OK: JS atualizado para reidratar Criar sessão ao retornar para a aba Sessões.")


####################################################################################
# (5) ATUALIZAR CSS DEFENSIVO V13
####################################################################################

css_content = CSS_PATH.read_text(encoding="utf-8")

css_block = f'''{CSS_MARKER_START}

body.appverbo-admin-sessoes-active-v13 #admin-sidebar-sections-create-card,
body.appverbo-admin-sessoes-active-v13 #admin-sidebar-sections-inactive-card {{
  display: block !important;
}}

body.appverbo-admin-sessoes-inactive-v13 #admin-sidebar-sections-create-card,
body.appverbo-admin-sessoes-inactive-v13 #admin-sidebar-sections-inactive-card {{
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

print("OK: CSS V13 atualizado.")


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
    fail_v13("não encontrei sidebar_sections_layout_v1.js no template.")

if "static/css/modules/sidebar_sections_layout_v1.css" in template_content:
    template_content = re.sub(
        r"/static/css/modules/sidebar_sections_layout_v1\.css\?v=[^\"]+",
        CSS_CACHE,
        template_content,
    )
else:
    fail_v13("não encontrei sidebar_sections_layout_v1.css no template.")

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
    "APPVERBO_SESSOES_RELOAD_ON_RETURN_V13_START": agents_validado,
    "APPVERBO_SESSOES_RELOAD_ON_TAB_RETURN_V13_START": js_validado,
    "instalarEventosRetornoSessoesV13": js_validado,
    "reidratarSessoesAoRetornarV13": js_validado,
    "instaladoV10 = false": js_validado,
    "instalarSessoesV10(true)": js_validado,
    "appverbo-admin-sessoes-active-v13": css_validado,
    "20260505-sessoes-return-tab-v13": template_validado,
}

for termo, conteudo in validacoes.items():
    if termo not in conteudo:
        fail_v13(f"validação falhou, termo ausente: {termo}")

print("OK: patch_sessoes_reaparecer_criar_ao_retornar_v13 concluído.")
