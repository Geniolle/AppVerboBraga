from pathlib import Path
import re
import sys

ROOT = Path.cwd()

AGENTS_UPPER_PATH = ROOT / "AGENTS.md"
AGENTS_TITLE_PATH = ROOT / "Agents.md"
TEMPLATE_PATH = ROOT / "templates" / "new_user.html"
JS_PATH = ROOT / "static" / "js" / "modules" / "sidebar_sections_layout_v1.js"
CSS_PATH = ROOT / "static" / "css" / "modules" / "sidebar_sections_layout_v1.css"

AGENTS_MARKER_START = "<!-- APPVERBO_SESSOES_INATIVAS_ACOES_VISIVEIS_V24_START -->"
AGENTS_MARKER_END = "<!-- APPVERBO_SESSOES_INATIVAS_ACOES_VISIVEIS_V24_END -->"

JS_MARKER_START = "// APPVERBO_SESSOES_INATIVAS_ACOES_VISIVEIS_V24_START"
JS_MARKER_END = "// APPVERBO_SESSOES_INATIVAS_ACOES_VISIVEIS_V24_END"

CSS_MARKER_START = "/* APPVERBO_SESSOES_INATIVAS_ACOES_VISIVEIS_V24_START */"
CSS_MARKER_END = "/* APPVERBO_SESSOES_INATIVAS_ACOES_VISIVEIS_V24_END */"

JS_CACHE = "/static/js/modules/sidebar_sections_layout_v1.js?v=20260505-sessoes-inativas-acoes-visiveis-v24"
CSS_CACHE = "/static/css/modules/sidebar_sections_layout_v1.css?v=20260505-sessoes-inativas-acoes-visiveis-v24"


def fail_v24(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


####################################################################################
# (1) RESOLVER AGENTS.md
####################################################################################

def resolve_agents_path_v24() -> Path:
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
        fail_v24(f"ficheiro não encontrado: {file_path}")


####################################################################################
# (3) ATUALIZAR AGENTS.md
####################################################################################

agents_path = resolve_agents_path_v24()
agents_content = agents_path.read_text(encoding="utf-8")

agents_rule = f"""{AGENTS_MARKER_START}
## Regra para ações visíveis nas Sessões inativas

Na aba **Sessões**:

1. O bloco **Sessões inativas** deve mostrar ações visíveis.
2. Cada linha inativa deve apresentar, no mínimo:
   - ação **Visualizar**;
   - ação **Editar**.
3. Os botões não podem aparecer vazios.
4. As ações de inativas devem usar o mesmo padrão visual das ações de ativas.
5. O botão **Editar** de uma sessão inativa deve continuar usando `sidebar_section_edit_key`.
6. Não usar `dynamic_process_section` nas ações da aba Sessões.
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
# (4) ADICIONAR JS V24 PARA HIDRATAR ACOES VAZIAS
####################################################################################

js_content = JS_PATH.read_text(encoding="utf-8")

js_block = r'''// APPVERBO_SESSOES_INATIVAS_ACOES_VISIVEIS_V24_START
(function () {
  "use strict";

  //###################################################################################
  // (1) MAPA DE ICONES
  //###################################################################################

  const MAPA_ACOES_SESSOES_V24 = {
    up: {
      texto: "↑",
      titulo: "Subir sessão"
    },
    down: {
      texto: "↓",
      titulo: "Descer sessão"
    },
    view: {
      texto: "👁",
      titulo: "Visualizar detalhes"
    },
    edit: {
      texto: "✎",
      titulo: "Editar sessão"
    }
  };

  //###################################################################################
  // (2) NORMALIZAR BOTOES DE ACAO
  //###################################################################################

  function obterAcaoBotaoSessoesV24(botao) {
    if (!botao || !botao.dataset) {
      return "";
    }

    return botao.dataset.sidebarSectionActionV23 ||
      botao.dataset.sidebarSectionActionV22 ||
      botao.dataset.sidebarSectionActionV21 ||
      botao.dataset.sidebarSectionActionV20 ||
      botao.dataset.sidebarSectionActionV10 ||
      botao.dataset.sidebarSectionActionV9 ||
      botao.dataset.sidebarSectionActionV6 ||
      botao.dataset.sidebarSectionActionV2 ||
      "";
  }

  function hidratarBotaoAcaoSessoesV24(botao) {
    const acao = obterAcaoBotaoSessoesV24(botao);
    const config = MAPA_ACOES_SESSOES_V24[acao];

    if (!config) {
      return;
    }

    botao.dataset.sidebarSectionActionV23 = acao;
    botao.dataset.sidebarSectionActionV24 = acao;
    botao.classList.add("appverbo-sidebar-section-action-btn-v24");

    if (!botao.getAttribute("title")) {
      botao.title = config.titulo;
    }

    if (!botao.getAttribute("aria-label")) {
      botao.setAttribute("aria-label", config.titulo);
    }

    const textoAtual = String(botao.textContent || "").trim();

    if (!textoAtual) {
      botao.textContent = config.texto;
    }

    if (!botao.querySelector(".appverbo-sidebar-section-action-icon-v24")) {
      const textoFinal = String(botao.textContent || config.texto).trim() || config.texto;
      botao.textContent = "";

      const span = document.createElement("span");
      span.className = "appverbo-sidebar-section-action-icon-v24";
      span.setAttribute("aria-hidden", "true");
      span.textContent = textoFinal;

      botao.appendChild(span);
    }
  }

  function hidratarAcoesSessoesInativasV24() {
    const cardInativas = document.getElementById("admin-sidebar-sections-inactive-card");

    if (!cardInativas) {
      return;
    }

    const botoes = Array.from(
      cardInativas.querySelectorAll(
        "button[data-sidebar-section-action-v23], " +
        "button[data-sidebar-section-action-v22], " +
        "button[data-sidebar-section-action-v21], " +
        "button[data-sidebar-section-action-v20], " +
        "button[data-sidebar-section-action-v10], " +
        "button[data-sidebar-section-action-v9], " +
        "button[data-sidebar-section-action-v6], " +
        "button[data-sidebar-section-action-v2]"
      )
    );

    botoes.forEach(hidratarBotaoAcaoSessoesV24);
  }

  //###################################################################################
  // (3) INSTALAR SEM MUTATIONOBSERVER CONTINUO
  //###################################################################################

  function agendarHidratacaoSessoesV24() {
    window.setTimeout(hidratarAcoesSessoesInativasV24, 80);
    window.setTimeout(hidratarAcoesSessoesInativasV24, 250);
    window.setTimeout(hidratarAcoesSessoesInativasV24, 700);
  }

  function instalarAcoesSessoesV24() {
    if (window.__appverboSessoesAcoesVisiveisV24 === true) {
      return;
    }

    window.__appverboSessoesAcoesVisiveisV24 = true;

    agendarHidratacaoSessoesV24();

    document.addEventListener("click", function () {
      agendarHidratacaoSessoesV24();
    }, true);

    window.addEventListener("hashchange", agendarHidratacaoSessoesV24);
    window.addEventListener("popstate", agendarHidratacaoSessoesV24);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", instalarAcoesSessoesV24);
  }
  else {
    instalarAcoesSessoesV24();
  }
})();
// APPVERBO_SESSOES_INATIVAS_ACOES_VISIVEIS_V24_END
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

print("OK: JS V24 aplicado.")


####################################################################################
# (5) ADICIONAR CSS V24 PARA BOTOES VISIVEIS
####################################################################################

css_content = CSS_PATH.read_text(encoding="utf-8")

css_block = f'''{CSS_MARKER_START}

#admin-sidebar-sections-inactive-card .appverbo-sidebar-section-actions-v23,
#admin-sidebar-sections-inactive-card .appverbo-sidebar-section-actions-v24 {{
  display: flex !important;
  align-items: center !important;
  justify-content: flex-end !important;
  gap: 6px !important;
}}

#admin-sidebar-sections-inactive-card button[data-sidebar-section-action-v23],
#admin-sidebar-sections-inactive-card button[data-sidebar-section-action-v24],
#admin-sidebar-sections-inactive-card .appverbo-sidebar-section-action-btn-v23,
#admin-sidebar-sections-inactive-card .appverbo-sidebar-section-action-btn-v24 {{
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  width: 30px !important;
  min-width: 30px !important;
  height: 30px !important;
  min-height: 30px !important;
  padding: 0 !important;
  border: 1px solid #b9cdf5 !important;
  border-radius: 7px !important;
  background: #eef5ff !important;
  color: #174ea6 !important;
  font-size: 15px !important;
  font-weight: 800 !important;
  line-height: 1 !important;
  text-align: center !important;
  cursor: pointer !important;
  opacity: 1 !important;
  overflow: visible !important;
}}

#admin-sidebar-sections-inactive-card button[data-sidebar-section-action-v23]:hover,
#admin-sidebar-sections-inactive-card button[data-sidebar-section-action-v24]:hover,
#admin-sidebar-sections-inactive-card .appverbo-sidebar-section-action-btn-v23:hover,
#admin-sidebar-sections-inactive-card .appverbo-sidebar-section-action-btn-v24:hover {{
  background: #dfeaff !important;
  border-color: #7fa8f2 !important;
}}

#admin-sidebar-sections-inactive-card .appverbo-sidebar-section-action-icon-v24 {{
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  width: 100% !important;
  height: 100% !important;
  color: #174ea6 !important;
  font-size: 15px !important;
  font-weight: 800 !important;
  line-height: 1 !important;
  text-indent: 0 !important;
  opacity: 1 !important;
  visibility: visible !important;
}}

#admin-sidebar-sections-inactive-card button[data-sidebar-section-action-v23="view"]:empty::before,
#admin-sidebar-sections-inactive-card button[data-sidebar-section-action-v24="view"]:empty::before {{
  content: "👁" !important;
}}

#admin-sidebar-sections-inactive-card button[data-sidebar-section-action-v23="edit"]:empty::before,
#admin-sidebar-sections-inactive-card button[data-sidebar-section-action-v24="edit"]:empty::before {{
  content: "✎" !important;
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

print("OK: CSS V24 aplicado.")


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
    fail_v24("não encontrei sidebar_sections_layout_v1.js no template.")

if "static/css/modules/sidebar_sections_layout_v1.css" in template_content:
    template_content = re.sub(
        r"/static/css/modules/sidebar_sections_layout_v1\.css\?v=[^\"]+",
        CSS_CACHE,
        template_content,
    )
else:
    fail_v24("não encontrei sidebar_sections_layout_v1.css no template.")

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
    "APPVERBO_SESSOES_INATIVAS_ACOES_VISIVEIS_V24_START": agents_validado,
    "APPVERBO_SESSOES_INATIVAS_ACOES_VISIVEIS_V24_START": js_validado,
    "hidratarAcoesSessoesInativasV24": js_validado,
    "appverbo-sidebar-section-action-icon-v24": js_validado,
    "APPVERBO_SESSOES_INATIVAS_ACOES_VISIVEIS_V24_START": css_validado,
    "appverbo-sidebar-section-action-btn-v24": css_validado,
    "20260505-sessoes-inativas-acoes-visiveis-v24": template_validado,
}

for termo, conteudo in validacoes.items():
    if termo not in conteudo:
        fail_v24(f"validação falhou, termo ausente: {termo}")

print("OK: patch_sessoes_inativas_acoes_visiveis_v24 concluído.")
