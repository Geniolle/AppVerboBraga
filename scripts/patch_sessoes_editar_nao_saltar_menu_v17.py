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

AGENTS_MARKER_START = "<!-- APPVERBO_SESSOES_EDITAR_NAO_SALTAR_MENU_V17_START -->"
AGENTS_MARKER_END = "<!-- APPVERBO_SESSOES_EDITAR_NAO_SALTAR_MENU_V17_END -->"

JS_MARKER_START = "// APPVERBO_SESSOES_EDITAR_NAO_SALTAR_MENU_V17_START"
JS_MARKER_END = "// APPVERBO_SESSOES_EDITAR_NAO_SALTAR_MENU_V17_END"

CSS_MARKER_START = "/* APPVERBO_SESSOES_EDITAR_NAO_SALTAR_MENU_V17_START */"
CSS_MARKER_END = "/* APPVERBO_SESSOES_EDITAR_NAO_SALTAR_MENU_V17_END */"

PY_MARKER_START = "# APPVERBO_SESSOES_RETURN_URL_V17_START"
PY_MARKER_END = "# APPVERBO_SESSOES_RETURN_URL_V17_END"

JS_CACHE = "/static/js/modules/sidebar_sections_layout_v1.js?v=20260505-sessoes-nao-saltar-menu-v17"
CSS_CACHE = "/static/css/modules/sidebar_sections_layout_v1.css?v=20260505-sessoes-nao-saltar-menu-v17"


def fail_v17(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


####################################################################################
# (1) RESOLVER AGENTS.md
####################################################################################

def resolve_agents_path_v17() -> Path:
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
        fail_v17(f"ficheiro não encontrado: {file_path}")


####################################################################################
# (3) ATUALIZAR AGENTS.md
####################################################################################

agents_path = resolve_agents_path_v17()
agents_content = agents_path.read_text(encoding="utf-8")

agents_rule = f"""{AGENTS_MARKER_START}
## Regra para editar Sessões sem saltar para Menu

Na aba **Sessões**, a ação **Editar** deve permanecer sempre no subprocesso **Sessões**.

Regras:

1. O clique em **Editar** deve usar a URL atual como base.
2. Deve adicionar apenas o parâmetro técnico `sidebar_section_edit_key`.
3. Não deve adicionar `settings_edit_key`, `settings_action` ou `settings_tab`, porque esses parâmetros pertencem ao fluxo de Menu e podem abrir o subprocesso errado.
4. O botão **Cancelar** deve remover apenas `sidebar_section_edit_key` e retornar para a própria aba Sessões.
5. Após **Guardar**, o backend deve redirecionar para a URL de retorno enviada pelo formulário, preservando a aba Sessões.
6. A edição deve abrir o bloco superior como **Editar sessão**, com Nome da sessão, Sistema e Estado preenchidos.
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

print(f"OK: regra V17 atualizada em {agents_path}")


####################################################################################
# (4) ATUALIZAR BACKEND PARA ACEITAR RETURN_URL SEGURO
####################################################################################

settings_content = SETTINGS_HANDLERS_PATH.read_text(encoding="utf-8")

py_block = r'''# APPVERBO_SESSOES_RETURN_URL_V17_START

# ###################################################################################
# (SIDEBAR_SECTION_RETURN_URL_V17) URL SEGURA DE RETORNO PARA A ABA SESSOES
# ###################################################################################

def _sanitize_sidebar_section_return_url_v17(return_url: object) -> str:
    raw_url = str(return_url or "").strip()

    if not raw_url:
        return "/users/new?menu=administrativo#admin-sidebar-sections-card"

    if raw_url.startswith("http://") or raw_url.startswith("https://") or raw_url.startswith("//"):
        return "/users/new?menu=administrativo#admin-sidebar-sections-card"

    if not raw_url.startswith("/users/new"):
        return "/users/new?menu=administrativo#admin-sidebar-sections-card"

    return raw_url

# APPVERBO_SESSOES_RETURN_URL_V17_END
'''

if PY_MARKER_START in settings_content and PY_MARKER_END in settings_content:
    py_pattern = re.compile(
        re.escape(PY_MARKER_START) + r"[\s\S]*?" + re.escape(PY_MARKER_END),
        re.S,
    )
    settings_content = py_pattern.sub(py_block, settings_content, count=1)
else:
    anchor = "# APPVERBO_SESSOES_SAVE_ONE_V16_START"

    if anchor not in settings_content:
        fail_v17("não encontrei APPVERBO_SESSOES_SAVE_ONE_V16_START. Execute primeiro o V16.")

    settings_content = settings_content.replace(anchor, py_block + "\n\n" + anchor, 1)

if 'sidebar_section_return_url: str = Form("")' not in settings_content:
    old_signature = '''    section_status: str = Form("ativo"),
    redirect_menu: str = Form("administrativo"),
'''
    new_signature = '''    section_status: str = Form("ativo"),
    sidebar_section_return_url: str = Form(""),
    redirect_menu: str = Form("administrativo"),
'''

    if old_signature not in settings_content:
        fail_v17("não encontrei assinatura do save_one_sidebar_section_v16 para incluir sidebar_section_return_url.")

    settings_content = settings_content.replace(old_signature, new_signature, 1)

if "safe_return_url_v17 = _sanitize_sidebar_section_return_url_v17(sidebar_section_return_url)" not in settings_content:
    old_with_session = '''    with SessionLocal() as session:
        current_user = get_current_user(request, session)
'''
    new_with_session = '''    safe_return_url_v17 = _sanitize_sidebar_section_return_url_v17(sidebar_section_return_url)

    with SessionLocal() as session:
        current_user = get_current_user(request, session)
'''

    first_save_pos = settings_content.find("def save_one_sidebar_section_v16(")
    if first_save_pos < 0:
        fail_v17("não encontrei save_one_sidebar_section_v16.")

    replace_pos = settings_content.find(old_with_session, first_save_pos)
    if replace_pos < 0:
        fail_v17("não encontrei início do with SessionLocal no save_one_sidebar_section_v16.")

    settings_content = (
        settings_content[:replace_pos]
        + new_with_session
        + settings_content[replace_pos + len(old_with_session):]
    )

success_pattern = re.compile(
    r'''        return RedirectResponse\(
            url=_build_settings_redirect_url\(
                success_message=\(
                    "Sessão atualizada com sucesso\."
                    if clean_mode == "edit"
                    else "Sessão criada com sucesso\."
                \),
                redirect_menu=redirect_menu,
                redirect_target=redirect_target,
                settings_edit_key="administrativo",
                settings_action="edit",
                settings_tab="sessoes",
            \),
            status_code=status\.HTTP_303_SEE_OTHER,
        \)''',
    re.S,
)

success_replacement = '''        success_separator = "&" if "?" in safe_return_url_v17 else "?"
        success_url = (
            f"{safe_return_url_v17}{success_separator}success="
            + (
                "Sessão atualizada com sucesso."
                if clean_mode == "edit"
                else "Sessão criada com sucesso."
            )
        )

        return RedirectResponse(
            url=success_url,
            status_code=status.HTTP_303_SEE_OTHER,
        )'''

if success_pattern.search(settings_content):
    settings_content = success_pattern.sub(success_replacement, settings_content, count=1)
elif "success_url = (" not in settings_content:
    fail_v17("não encontrei bloco de sucesso do save_one_sidebar_section_v16 para substituir.")

try:
    ast.parse(settings_content)
except SyntaxError as exc:
    fail_v17(f"settings_handlers.py ficaria inválido: {exc}")

SETTINGS_HANDLERS_PATH.write_text(settings_content, encoding="utf-8")

print("OK: backend V17 aceita sidebar_section_return_url e redireciona sem abrir Menu.")


####################################################################################
# (5) ADICIONAR JS V17 PARA MANTER EDITAR NA ABA SESSOES
####################################################################################

js_content = JS_PATH.read_text(encoding="utf-8")

js_block = r'''// APPVERBO_SESSOES_EDITAR_NAO_SALTAR_MENU_V17_START
(function () {
  "use strict";

  //###################################################################################
  // (1) NORMALIZACAO
  //###################################################################################

  function normalizarTextoSessoesV17(valor) {
    return String(valor || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase();
  }

  function criarChaveSessoesV17(valor) {
    return normalizarTextoSessoesV17(valor)
      .replace(/[^a-z0-9]+/g, "_")
      .replace(/_+/g, "_")
      .replace(/^_+|_+$/g, "");
  }

  //###################################################################################
  // (2) URL CORRETA DO SUBPROCESSO SESSOES
  //###################################################################################

  function limparParametrosMenuDaUrlV17(url) {
    url.searchParams.delete("settings_edit_key");
    url.searchParams.delete("settings_action");
    url.searchParams.delete("settings_tab");
    url.searchParams.delete("sidebar_section_return_url");
    url.searchParams.set("menu", "administrativo");
    return url;
  }

  function obterUrlSessaoAtualV17() {
    const url = new URL(window.location.href);
    limparParametrosMenuDaUrlV17(url);
    url.hash = "admin-sidebar-sections-card";
    return url;
  }

  function obterUrlRetornoSessaoV17() {
    const url = obterUrlSessaoAtualV17();
    url.searchParams.delete("sidebar_section_edit_key");
    return url.pathname + url.search + url.hash;
  }

  function navegarParaEditarSessaoV17(chave) {
    const cleanChave = criarChaveSessoesV17(chave);

    if (!cleanChave) {
      return;
    }

    const url = obterUrlSessaoAtualV17();
    url.searchParams.set("sidebar_section_edit_key", cleanChave);
    window.location.href = url.pathname + url.search + url.hash;
  }

  function cancelarEdicaoSessaoV17() {
    window.location.href = obterUrlRetornoSessaoV17();
  }

  //###################################################################################
  // (3) CORRIGIR FORMULARIO GERADO PELO V16
  //###################################################################################

  function garantirReturnUrlFormularioSessoesV17() {
    const cardSuperior = document.getElementById("admin-sidebar-sections-create-card");

    if (!cardSuperior) {
      return;
    }

    const form = cardSuperior.querySelector('form[action="/settings/menu/sidebar-section-save"], form[action*="/settings/menu/sidebar-section-save"]');

    if (!form) {
      return;
    }

    Array.from(form.querySelectorAll('[name="sidebar_section_return_url"]')).forEach(function (input) {
      input.remove();
    });

    const input = document.createElement("input");
    input.type = "hidden";
    input.name = "sidebar_section_return_url";
    input.value = obterUrlRetornoSessaoV17();
    form.appendChild(input);
  }

  function corrigirCancelarFormularioSessoesV17() {
    const cardSuperior = document.getElementById("admin-sidebar-sections-create-card");

    if (!cardSuperior) {
      return;
    }

    const cancelButtons = Array.from(cardSuperior.querySelectorAll(".action-btn-cancel"));

    cancelButtons.forEach(function (botao) {
      if (botao.dataset.appverboCancelV17 === "1") {
        return;
      }

      botao.dataset.appverboCancelV17 = "1";

      botao.addEventListener("click", function (event) {
        const url = new URL(window.location.href);

        if (!url.searchParams.get("sidebar_section_edit_key")) {
          return;
        }

        event.preventDefault();
        event.stopPropagation();
        event.stopImmediatePropagation();
        cancelarEdicaoSessaoV17();
      }, true);
    });
  }

  function corrigirFormularioSessoesV17() {
    garantirReturnUrlFormularioSessoesV17();
    corrigirCancelarFormularioSessoesV17();
  }

  //###################################################################################
  // (4) CAPTURAR EDITAR ANTES DOS HANDLERS ANTIGOS
  //###################################################################################

  function obterChaveLinhaSessoesV17(linha) {
    if (!linha) {
      return "";
    }

    const datasetKey = linha.dataset.sectionKeyV10 ||
      linha.dataset.sectionKeyV9 ||
      linha.dataset.sectionKeyV6 ||
      linha.dataset.sectionKeyV2 ||
      "";

    if (datasetKey) {
      return criarChaveSessoesV17(datasetKey);
    }

    const hiddenKey = linha.querySelector('[name="section_key"]');

    if (hiddenKey && hiddenKey.value) {
      return criarChaveSessoesV17(hiddenKey.value);
    }

    const primeiraCelula = linha.querySelector("td");

    return primeiraCelula ? criarChaveSessoesV17(primeiraCelula.textContent) : "";
  }

  function cliqueEhEditarSessaoV17(event) {
    const botaoEditar = event.target.closest(
      '[data-sidebar-section-action-v10="edit"], ' +
      '[data-sidebar-section-action-v9="edit"], ' +
      '[data-sidebar-section-action-v6="edit"], ' +
      '[data-sidebar-section-action="edit"]'
    );

    if (!botaoEditar) {
      return null;
    }

    const linha = botaoEditar.closest("tr");
    const chave = obterChaveLinhaSessoesV17(linha);

    if (!chave) {
      return null;
    }

    const card = botaoEditar.closest("#admin-sidebar-sections-card, #admin-sidebar-sections-inactive-card");

    if (!card) {
      return null;
    }

    return {
      chave: chave
    };
  }

  function instalarCapturaEditarSessoesV17() {
    if (window.__appverboSessoesEditNoMenuV17 === true) {
      return;
    }

    window.__appverboSessoesEditNoMenuV17 = true;

    document.addEventListener("click", function (event) {
      const resultado = cliqueEhEditarSessaoV17(event);

      if (!resultado) {
        return;
      }

      event.preventDefault();
      event.stopPropagation();
      event.stopImmediatePropagation();

      navegarParaEditarSessaoV17(resultado.chave);
    }, true);
  }

  //###################################################################################
  // (5) INSTALAR E OBSERVAR
  //###################################################################################

  function agendarCorrecoesSessoesV17() {
    window.setTimeout(corrigirFormularioSessoesV17, 80);
    window.setTimeout(corrigirFormularioSessoesV17, 250);
    window.setTimeout(corrigirFormularioSessoesV17, 600);
    window.setTimeout(corrigirFormularioSessoesV17, 1200);
  }

  function instalarSessoesV17() {
    instalarCapturaEditarSessoesV17();
    agendarCorrecoesSessoesV17();

    document.addEventListener("click", function () {
      agendarCorrecoesSessoesV17();
    });

    window.addEventListener("hashchange", agendarCorrecoesSessoesV17);
    window.addEventListener("popstate", agendarCorrecoesSessoesV17);

    const observer = new MutationObserver(function () {
      window.clearTimeout(window.__appverboSessoesNoMenuTimerV17);
      window.__appverboSessoesNoMenuTimerV17 = window.setTimeout(corrigirFormularioSessoesV17, 120);
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ["class", "hidden", "style", "aria-selected", "aria-hidden"]
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", instalarSessoesV17);
  }
  else {
    instalarSessoesV17();
  }
})();
// APPVERBO_SESSOES_EDITAR_NAO_SALTAR_MENU_V17_END
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

print("OK: JS V17 aplicado para editar Sessões sem saltar para Menu.")


####################################################################################
# (6) ADICIONAR CSS V17
####################################################################################

css_content = CSS_PATH.read_text(encoding="utf-8")

css_block = f'''{CSS_MARKER_START}

#admin-sidebar-sections-create-card.appverbo-sessoes-create-card-v16 {{
  display: block !important;
  visibility: visible !important;
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

print("OK: CSS V17 aplicado.")


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
    fail_v17("não encontrei sidebar_sections_layout_v1.js no template.")

if "static/css/modules/sidebar_sections_layout_v1.css" in template_content:
    template_content = re.sub(
        r"/static/css/modules/sidebar_sections_layout_v1\.css\?v=[^\"]+",
        CSS_CACHE,
        template_content,
    )
else:
    fail_v17("não encontrei sidebar_sections_layout_v1.css no template.")

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
    "APPVERBO_SESSOES_EDITAR_NAO_SALTAR_MENU_V17_START": agents_validado,
    "APPVERBO_SESSOES_RETURN_URL_V17_START": settings_validado,
    "_sanitize_sidebar_section_return_url_v17": settings_validado,
    "sidebar_section_return_url: str = Form(\"\")": settings_validado,
    "safe_return_url_v17": settings_validado,
    "APPVERBO_SESSOES_EDITAR_NAO_SALTAR_MENU_V17_START": js_validado,
    "navegarParaEditarSessaoV17": js_validado,
    "settings_edit_key": js_validado,
    "sidebar_section_return_url": js_validado,
    "APPVERBO_SESSOES_EDITAR_NAO_SALTAR_MENU_V17_START": css_validado,
    "20260505-sessoes-nao-saltar-menu-v17": template_validado,
}

for termo, conteudo in validacoes.items():
    if termo not in conteudo:
        fail_v17(f"validação falhou, termo ausente: {termo}")

try:
    ast.parse(settings_validado)
except SyntaxError as exc:
    fail_v17(f"Python final inválido: {exc}")

print("OK: patch_sessoes_editar_nao_saltar_menu_v17 concluído.")
