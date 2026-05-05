from pathlib import Path
import ast
import re
import sys

ROOT = Path.cwd()

AGENTS_UPPER_PATH = ROOT / "AGENTS.md"
AGENTS_TITLE_PATH = ROOT / "Agents.md"
TEMPLATE_PATH = ROOT / "templates" / "new_user.html"
MENU_SETTINGS_PATH = ROOT / "appverbo" / "menu_settings.py"
SETTINGS_HANDLERS_PATH = ROOT / "appverbo" / "routes" / "profile" / "settings_handlers.py"
JS_PATH = ROOT / "static" / "js" / "modules" / "sidebar_sections_layout_v1.js"
CSS_PATH = ROOT / "static" / "css" / "modules" / "sidebar_sections_layout_v1.css"

AGENTS_MARKER_START = "<!-- APPVERBO_SESSOES_ESTADO_BLOCOS_V9_START -->"
AGENTS_MARKER_END = "<!-- APPVERBO_SESSOES_ESTADO_BLOCOS_V9_END -->"

JS_MARKER_START = "// APPVERBO_SESSOES_ESTADO_BLOCOS_V9_START"
JS_MARKER_END = "// APPVERBO_SESSOES_ESTADO_BLOCOS_V9_END"

CSS_MARKER_START = "/* APPVERBO_SESSOES_ESTADO_BLOCOS_V9_START */"
CSS_MARKER_END = "/* APPVERBO_SESSOES_ESTADO_BLOCOS_V9_END */"

JS_CACHE = "/static/js/modules/sidebar_sections_layout_v1.js?v=20260505-sessoes-estado-blocos-v9"
CSS_CACHE = "/static/css/modules/sidebar_sections_layout_v1.css?v=20260505-sessoes-estado-blocos-v9"


def fail_v9(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


####################################################################################
# (1) RESOLVER AGENTS.md
####################################################################################

def resolve_agents_path_v9() -> Path:
    if AGENTS_UPPER_PATH.exists():
        return AGENTS_UPPER_PATH

    if AGENTS_TITLE_PATH.exists():
        return AGENTS_TITLE_PATH

    AGENTS_UPPER_PATH.write_text("# AGENTS.md\n\n", encoding="utf-8")
    return AGENTS_UPPER_PATH


####################################################################################
# (2) VALIDAR FICHEIROS
####################################################################################

for file_path in [TEMPLATE_PATH, MENU_SETTINGS_PATH, SETTINGS_HANDLERS_PATH, JS_PATH, CSS_PATH]:
    if not file_path.exists():
        fail_v9(f"ficheiro não encontrado: {file_path}")


####################################################################################
# (3) ATUALIZAR REGRA NO AGENTS.md
####################################################################################

agents_path = resolve_agents_path_v9()
agents_content = agents_path.read_text(encoding="utf-8")

agents_rule = f"""{AGENTS_MARKER_START}
## Regra para Estado das Sessões e blocos Ativo/Inativo

Na aba **Sessões**:

1. O campo **Estado** deve ser assumido corretamente ao criar ou editar uma sessão.
2. Quando o estado for **Ativo**, a sessão deve aparecer no bloco principal da lista.
3. Quando o estado for diferente de **Ativo**, a sessão deve aparecer em um bloco separado abaixo, chamado **Sessões inativas**.
4. A alteração do estado deve persistir no BD através do campo `section_status`.
5. A alteração de estado durante a edição deve mover automaticamente a linha para o bloco correto.
6. O botão de edição não deve usar `alert`; deve editar Nome da sessão, Sistema e Estado diretamente na linha.
7. A chave técnica da sessão deve continuar oculta e preservada.
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

print(f"OK: regra de estado Ativo/Inativo atualizada em {agents_path}")


####################################################################################
# (4) GARANTIR BACKEND COM section_status
####################################################################################

settings_handlers = SETTINGS_HANDLERS_PATH.read_text(encoding="utf-8")

if "section_status: list[str] = Form(default=[])" not in settings_handlers:
    old_signature = '''    section_visibility_scope_mode: list[str] = Form(default=[]),
    redirect_menu: str = Form("administrativo"),
'''
    new_signature = '''    section_visibility_scope_mode: list[str] = Form(default=[]),
    section_status: list[str] = Form(default=[]),
    redirect_menu: str = Form("administrativo"),
'''
    if old_signature not in settings_handlers:
        fail_v9("não encontrei local para adicionar section_status no endpoint.")

    settings_handlers = settings_handlers.replace(old_signature, new_signature, 1)

if "len(section_status)" not in settings_handlers:
    old_rows_count = '''        rows_count = max(
            len(section_key),
            len(section_label),
            len(section_visibility_scope_mode),
        )
'''
    new_rows_count = '''        rows_count = max(
            len(section_key),
            len(section_label),
            len(section_visibility_scope_mode),
            len(section_status),
        )
'''
    if old_rows_count not in settings_handlers:
        fail_v9("não encontrei rows_count para incluir section_status.")

    settings_handlers = settings_handlers.replace(old_rows_count, new_rows_count, 1)

if '"status": (' not in settings_handlers:
    old_payload = '''                    "visibility_scope_mode": (
                        section_visibility_scope_mode[row_index]
                        if row_index < len(section_visibility_scope_mode)
                        else ""
                    ),
'''
    new_payload = '''                    "visibility_scope_mode": (
                        section_visibility_scope_mode[row_index]
                        if row_index < len(section_visibility_scope_mode)
                        else ""
                    ),
                    "status": (
                        section_status[row_index]
                        if row_index < len(section_status)
                        else "ativo"
                    ),
'''
    if old_payload not in settings_handlers:
        fail_v9("não encontrei payload para incluir status.")

    settings_handlers = settings_handlers.replace(old_payload, new_payload, 1)

try:
    ast.parse(settings_handlers)
except SyntaxError as exc:
    fail_v9(f"settings_handlers.py ficaria inválido: {exc}")

SETTINGS_HANDLERS_PATH.write_text(settings_handlers, encoding="utf-8")

print("OK: backend validado para receber section_status.")


####################################################################################
# (5) GARANTIR NORMALIZACAO DO ESTADO EM menu_settings.py
####################################################################################

menu_settings = MENU_SETTINGS_PATH.read_text(encoding="utf-8")

if "_normalize_sidebar_section_status_v5" not in menu_settings:
    helper = '''def _normalize_sidebar_section_status_v5(raw_status: Any) -> str:
    if isinstance(raw_status, bool):
        return "ativo" if raw_status else "inativo"

    clean_status = str(raw_status or "").strip().lower()

    if clean_status in {"inativo", "inactive", "0", "false", "no", "nao", "não", "off"}:
        return "inativo"

    return "ativo"


def _sidebar_section_status_label_v5(raw_status: Any) -> str:
    return "Inativo" if _normalize_sidebar_section_status_v5(raw_status) == "inativo" else "Ativo"


'''
    anchor = "def _build_sidebar_section_payload("
    if anchor not in menu_settings:
        fail_v9("não encontrei _build_sidebar_section_payload em menu_settings.py.")

    menu_settings = menu_settings.replace(anchor, helper + anchor, 1)

if '"status": normalized_status' not in menu_settings:
    if "normalized_status = _normalize_sidebar_section_status_v5(status)" not in menu_settings:
        old_visibility = '''    visibility_scope_mode = _resolve_visibility_scope_mode_from_scopes(normalized_scopes)
    return {
'''
        new_visibility = '''    visibility_scope_mode = _resolve_visibility_scope_mode_from_scopes(normalized_scopes)
    normalized_status = _normalize_sidebar_section_status_v5(status)
    return {
'''
        if old_visibility in menu_settings:
            menu_settings = menu_settings.replace(old_visibility, new_visibility, 1)

    old_payload_line = '''        "visibility_scope_label": _resolve_visibility_scope_label_from_mode(visibility_scope_mode),
    }
'''
    new_payload_line = '''        "visibility_scope_label": _resolve_visibility_scope_label_from_mode(visibility_scope_mode),
        "status": normalized_status,
        "is_active": normalized_status == "ativo",
        "status_label": _sidebar_section_status_label_v5(normalized_status),
    }
'''
    if old_payload_line in menu_settings:
        menu_settings = menu_settings.replace(old_payload_line, new_payload_line, 1)

if "status: Any = \"ativo\"" not in menu_settings:
    menu_settings = menu_settings.replace(
        '''    visibility_scopes: Any,
) -> dict[str, Any]:''',
        '''    visibility_scopes: Any,
    status: Any = "ativo",
) -> dict[str, Any]:''',
        1,
    )

if "clean_status = raw_item.get(\"status\", raw_item.get(\"is_active\", \"ativo\"))" not in menu_settings:
    old_raw = '''            clean_visibility_scopes = get_sidebar_section_visibility_scopes(raw_item)
        else:
            clean_label = _normalize_sidebar_section_label(raw_item)
            clean_key = ""
            clean_visibility_scopes = list(MENU_VISIBILITY_SCOPES)
'''
    new_raw = '''            clean_visibility_scopes = get_sidebar_section_visibility_scopes(raw_item)
            clean_status = raw_item.get("status", raw_item.get("is_active", "ativo"))
        else:
            clean_label = _normalize_sidebar_section_label(raw_item)
            clean_key = ""
            clean_visibility_scopes = list(MENU_VISIBILITY_SCOPES)
            clean_status = "ativo"
'''
    if old_raw in menu_settings:
        menu_settings = menu_settings.replace(old_raw, new_raw, 1)

if "_build_sidebar_section_payload(clean_key, clean_label, clean_visibility_scopes, clean_status)" not in menu_settings:
    menu_settings = menu_settings.replace(
        "_build_sidebar_section_payload(clean_key, clean_label, clean_visibility_scopes)",
        "_build_sidebar_section_payload(clean_key, clean_label, clean_visibility_scopes, clean_status)",
        1,
    )

try:
    ast.parse(menu_settings)
except SyntaxError as exc:
    fail_v9(f"menu_settings.py ficaria inválido: {exc}")

MENU_SETTINGS_PATH.write_text(menu_settings, encoding="utf-8")

print("OK: menu_settings.py validado para normalizar e persistir Estado.")


####################################################################################
# (6) ADICIONAR JS V9 PARA ASSUMIR ESTADO E SEPARAR BLOCOS
####################################################################################

js_content = JS_PATH.read_text(encoding="utf-8")

js_block = r'''// APPVERBO_SESSOES_ESTADO_BLOCOS_V9_START
(function () {
  "use strict";

  //###################################################################################
  // (1) NORMALIZACAO
  //###################################################################################

  function normalizarTextoSessoesEstadoV9(valor) {
    return String(valor || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase();
  }

  function criarChaveSessoesEstadoV9(valor) {
    return normalizarTextoSessoesEstadoV9(valor)
      .replace(/[^a-z0-9]+/g, "_")
      .replace(/_+/g, "_")
      .replace(/^_+|_+$/g, "");
  }

  function normalizarEstadoSessoesEstadoV9(valor) {
    const cleanValor = normalizarTextoSessoesEstadoV9(valor);

    if (["inativo", "inactive", "0", "false", "nao", "não", "off"].includes(cleanValor)) {
      return "inativo";
    }

    return "ativo";
  }

  function obterLabelEstadoSessoesEstadoV9(valor) {
    return normalizarEstadoSessoesEstadoV9(valor) === "inativo" ? "Inativo" : "Ativo";
  }

  function obterLabelSistemaSessoesEstadoV9(valor, fallback) {
    const cleanValor = normalizarTextoSessoesEstadoV9(valor);

    if (cleanValor === "owner") {
      return "Owner";
    }

    if (cleanValor === "legado") {
      return "Legado";
    }

    return fallback || "Owner e Legado";
  }

  function criarCampoOcultoSessoesEstadoV9(nome, valor) {
    const input = document.createElement("input");
    input.type = "hidden";
    input.name = nome;
    input.value = valor || "";
    return input;
  }

  //###################################################################################
  // (2) ESTADO LOCAL E LEITURA DO BD/TEMPLATE
  //###################################################################################

  let sessoesEstadoV9 = [];
  let instaladoEstadoV9 = false;

  function lerSessoesTemplateEstadoV9() {
    const script = document.getElementById("appverbo-sidebar-section-options-v2") ||
      document.getElementById("appverbo-sidebar-section-options-v1");

    if (!script) {
      return [];
    }

    try {
      const parsed = JSON.parse(script.textContent || "[]");
      return Array.isArray(parsed) ? parsed : [];
    } catch (error) {
      console.warn("APPVERBO V9: não foi possível ler sessões do template.", error);
      return [];
    }
  }

  async function carregarSessoesEstadoV9() {
    const sessoesTemplate = lerSessoesTemplateEstadoV9();

    if (sessoesTemplate.length) {
      return sessoesTemplate;
    }

    try {
      const response = await fetch("/settings/menu/sidebar-sections-data", {
        headers: {
          Accept: "application/json"
        },
        credentials: "same-origin"
      });

      if (!response.ok) {
        return [];
      }

      const payload = await response.json();

      if (payload && Array.isArray(payload.sections)) {
        return payload.sections;
      }
    } catch (error) {
      console.warn("APPVERBO V9: falha ao carregar sessões do BD.", error);
    }

    return [];
  }

  function normalizarSessaoEstadoV9(sessao) {
    if (!sessao || typeof sessao !== "object") {
      return null;
    }

    const label = String(sessao.label || sessao.name || sessao.title || "").trim();
    const key = criarChaveSessoesEstadoV9(sessao.key || sessao.section_key || label);

    if (!label || !key) {
      return null;
    }

    const sistema = String(sessao.visibility_scope_mode || sessao.scope_mode || "all").trim() || "all";
    const estado = normalizarEstadoSessoesEstadoV9(
      sessao.status || (sessao.is_active === false ? "inativo" : "ativo")
    );

    return {
      key: key,
      label: label,
      visibility_scope_mode: sistema,
      visibility_scope_label: obterLabelSistemaSessoesEstadoV9(sistema, sessao.visibility_scope_label || ""),
      status: estado,
      is_active: estado === "ativo",
      status_label: obterLabelEstadoSessoesEstadoV9(estado)
    };
  }

  function encontrarIndiceSessaoEstadoV9(chave) {
    const cleanChave = criarChaveSessoesEstadoV9(chave);

    return sessoesEstadoV9.findIndex(function (sessao) {
      return criarChaveSessoesEstadoV9(sessao.key) === cleanChave;
    });
  }

  function gerarChaveUnicaEstadoV9(nomeSessao) {
    const baseKey = criarChaveSessoesEstadoV9(nomeSessao) || "nova_sessao";
    const usadas = new Set(
      sessoesEstadoV9.map(function (sessao) {
        return criarChaveSessoesEstadoV9(sessao.key);
      })
    );

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

  //###################################################################################
  // (3) ELEMENTOS BASE
  //###################################################################################

  function obterCardListaEstadoV9() {
    return document.getElementById("admin-sidebar-sections-card");
  }

  function obterOuCriarFormularioEstadoV9(cardLista) {
    let formulario = cardLista.querySelector('form[action*="/settings/menu/sidebar-sections"], form[action*="sidebar-sections"]');

    if (!formulario) {
      formulario = document.createElement("form");
      cardLista.appendChild(formulario);
    }

    formulario.method = "post";
    formulario.action = "/settings/menu/sidebar-sections";

    return formulario;
  }

  function obterOuCriarCardCriacaoEstadoV9(cardLista) {
    let createCard = document.getElementById("admin-sidebar-sections-create-card");

    if (!createCard) {
      createCard = document.createElement("section");
      createCard.id = "admin-sidebar-sections-create-card";
      createCard.className = "card appverbo-standard-create-card-v4 appverbo-sessoes-create-card-v3 appverbo-sessoes-create-card-v9";
      cardLista.parentElement.insertBefore(createCard, cardLista);
    }

    return createCard;
  }

  function submeterFormularioEstadoV9() {
    const cardLista = obterCardListaEstadoV9();

    if (!cardLista) {
      return;
    }

    const formulario = obterOuCriarFormularioEstadoV9(cardLista);

    if (typeof formulario.requestSubmit === "function") {
      formulario.requestSubmit();
    } else {
      formulario.submit();
    }
  }

  //###################################################################################
  // (4) CONTROLES
  //###################################################################################

  function criarBotaoAcaoEstadoV9(tipo, titulo, texto) {
    const botao = document.createElement("button");
    botao.type = "button";
    botao.className = "appverbo-sidebar-section-action-btn-v2 appverbo-sidebar-section-action-btn-v9";
    botao.dataset.sidebarSectionActionV9 = tipo;
    botao.title = titulo;
    botao.setAttribute("aria-label", titulo);
    botao.textContent = texto;
    return botao;
  }

  function criarSelectSistemaEstadoV9(valorAtual) {
    const select = document.createElement("select");
    select.className = "appverbo-sidebar-section-edit-select-v9";

    [
      ["all", "Owner e Legado"],
      ["owner", "Owner"],
      ["legado", "Legado"]
    ].forEach(function (item) {
      const option = document.createElement("option");
      option.value = item[0];
      option.textContent = item[1];

      if (String(valorAtual || "all") === item[0]) {
        option.selected = true;
      }

      select.appendChild(option);
    });

    return select;
  }

  function criarSelectEstadoEstadoV9(valorAtual) {
    const select = document.createElement("select");
    select.className = "appverbo-sidebar-section-edit-select-v9";
    const estadoAtual = normalizarEstadoSessoesEstadoV9(valorAtual);

    [
      ["ativo", "Ativo"],
      ["inativo", "Inativo"]
    ].forEach(function (item) {
      const option = document.createElement("option");
      option.value = item[0];
      option.textContent = item[1];

      if (estadoAtual === item[0]) {
        option.selected = true;
      }

      select.appendChild(option);
    });

    return select;
  }

  function criarBadgeEstadoV9(estado) {
    const estadoNormalizado = normalizarEstadoSessoesEstadoV9(estado);
    const badge = document.createElement("span");
    badge.className = "appverbo-sidebar-section-state-badge-v2 appverbo-sidebar-section-state-badge-" + estadoNormalizado + "-v9";
    badge.textContent = obterLabelEstadoSessoesEstadoV9(estadoNormalizado);
    return badge;
  }

  //###################################################################################
  // (5) LINHAS E TABELAS
  //###################################################################################

  function criarLinhaEstadoV9(sessao) {
    const tr = document.createElement("tr");
    tr.className = "appverbo-sidebar-section-row-v2 appverbo-sidebar-section-row-v9";
    tr.dataset.sectionKeyV9 = sessao.key;
    tr.dataset.sectionStatusV9 = normalizarEstadoSessoesEstadoV9(sessao.status);

    const keyInput = criarCampoOcultoSessoesEstadoV9("section_key", sessao.key);
    const labelInput = criarCampoOcultoSessoesEstadoV9("section_label", sessao.label);
    const scopeInput = criarCampoOcultoSessoesEstadoV9("section_visibility_scope_mode", sessao.visibility_scope_mode || "all");
    const statusInput = criarCampoOcultoSessoesEstadoV9("section_status", normalizarEstadoSessoesEstadoV9(sessao.status));

    const tdMenu = document.createElement("td");
    tdMenu.className = "appverbo-sidebar-section-menu-cell-v2";
    tdMenu.textContent = sessao.label;
    tdMenu.appendChild(keyInput);
    tdMenu.appendChild(labelInput);
    tdMenu.appendChild(scopeInput);
    tdMenu.appendChild(statusInput);

    const tdSistema = document.createElement("td");
    tdSistema.className = "appverbo-sidebar-section-system-cell-v2";
    tdSistema.textContent = obterLabelSistemaSessoesEstadoV9(sessao.visibility_scope_mode, sessao.visibility_scope_label || "");

    const tdEstado = document.createElement("td");
    tdEstado.className = "appverbo-sidebar-section-state-cell-v2";
    tdEstado.appendChild(criarBadgeEstadoV9(sessao.status));

    const tdAcoes = document.createElement("td");
    tdAcoes.className = "appverbo-sidebar-section-actions-cell-v2";

    const actions = document.createElement("div");
    actions.className = "appverbo-sidebar-section-actions-v2";
    actions.appendChild(criarBotaoAcaoEstadoV9("up", "Subir sessão", "↑"));
    actions.appendChild(criarBotaoAcaoEstadoV9("down", "Descer sessão", "↓"));
    actions.appendChild(criarBotaoAcaoEstadoV9("view", "Visualizar detalhes", "👁"));
    actions.appendChild(criarBotaoAcaoEstadoV9("edit", "Editar sessão", "✎"));

    tdAcoes.appendChild(actions);

    tr.appendChild(tdMenu);
    tr.appendChild(tdSistema);
    tr.appendChild(tdEstado);
    tr.appendChild(tdAcoes);

    return tr;
  }

  function criarTabelaEstadoV9(titulo, sessoes, tipo) {
    const bloco = document.createElement("div");
    bloco.className = "appverbo-sidebar-section-list-block-v9 appverbo-sidebar-section-list-block-" + tipo + "-v9";

    if (titulo) {
      const h3 = document.createElement("h3");
      h3.className = "appverbo-sidebar-section-list-title-v9";
      h3.textContent = titulo;
      bloco.appendChild(h3);
    }

    const tableWrap = document.createElement("div");
    tableWrap.className = "appverbo-sidebar-sections-table-wrap-v2 appverbo-sidebar-sections-table-wrap-v9";

    const table = document.createElement("table");
    table.className = "appverbo-sidebar-sections-table-v2 appverbo-sidebar-sections-table-v9";

    const thead = document.createElement("thead");
    thead.innerHTML = "<tr><th>MENU LATERAL</th><th>SISTEMA</th><th>ESTADO</th><th>AÇÕES</th></tr>";

    const tbody = document.createElement("tbody");
    tbody.className = "appverbo-sidebar-sections-body-v2 appverbo-sidebar-sections-body-v9";
    tbody.dataset.statusGroupV9 = tipo;

    sessoes.forEach(function (sessao) {
      tbody.appendChild(criarLinhaEstadoV9(sessao));
    });

    if (!sessoes.length) {
      const emptyRow = document.createElement("tr");
      emptyRow.className = "appverbo-sidebar-section-empty-row-v9";

      const emptyCell = document.createElement("td");
      emptyCell.colSpan = 4;
      emptyCell.textContent = tipo === "inativo" ? "Sem sessões inativas." : "Sem sessões ativas.";

      emptyRow.appendChild(emptyCell);
      tbody.appendChild(emptyRow);
    }

    table.appendChild(thead);
    table.appendChild(tbody);
    tableWrap.appendChild(table);
    bloco.appendChild(tableWrap);

    return bloco;
  }

  function atualizarEstadoBotoesEstadoV9(container) {
    const grupos = Array.from(container.querySelectorAll("tbody.appverbo-sidebar-sections-body-v9"));

    grupos.forEach(function (tbody) {
      const linhas = Array.from(tbody.querySelectorAll("tr.appverbo-sidebar-section-row-v9"));

      linhas.forEach(function (linha, indice) {
        const subir = linha.querySelector('[data-sidebar-section-action-v9="up"]');
        const descer = linha.querySelector('[data-sidebar-section-action-v9="down"]');

        if (subir) {
          subir.disabled = indice === 0;
        }

        if (descer) {
          descer.disabled = indice === linhas.length - 1;
        }
      });
    });
  }

  function renderizarListaEstadoV9() {
    const cardLista = obterCardListaEstadoV9();

    if (!cardLista) {
      return;
    }

    const formulario = obterOuCriarFormularioEstadoV9(cardLista);

    formulario.innerHTML = "";
    formulario.appendChild(criarCampoOcultoSessoesEstadoV9("redirect_menu", "administrativo"));
    formulario.appendChild(criarCampoOcultoSessoesEstadoV9("redirect_target", "#admin-sidebar-sections-card"));

    let titulo = cardLista.querySelector(".appverbo-sidebar-section-list-main-title-v9");

    cardLista.innerHTML = "";

    titulo = document.createElement("h2");
    titulo.className = "appverbo-sidebar-section-list-main-title-v9";
    titulo.textContent = "Sessoes do sidebar";

    const descricao = document.createElement("p");
    descricao.className = "appverbo-sidebar-sections-list-description-v9";
    descricao.textContent = "Ative os processos do menu lateral. Um menu só aparece quando estiver ativo aqui.";

    const ativas = sessoesEstadoV9.filter(function (sessao) {
      return normalizarEstadoSessoesEstadoV9(sessao.status) === "ativo";
    });

    const inativas = sessoesEstadoV9.filter(function (sessao) {
      return normalizarEstadoSessoesEstadoV9(sessao.status) !== "ativo";
    });

    formulario.appendChild(descricao);
    formulario.appendChild(criarTabelaEstadoV9("", ativas, "ativo"));
    formulario.appendChild(criarTabelaEstadoV9("Sessões inativas", inativas, "inativo"));

    cardLista.appendChild(titulo);
    cardLista.appendChild(formulario);

    atualizarEstadoBotoesEstadoV9(cardLista);
  }

  //###################################################################################
  // (6) CRIACAO
  //###################################################################################

  function instalarCriacaoEstadoV9() {
    const cardLista = obterCardListaEstadoV9();

    if (!cardLista || !cardLista.parentElement) {
      return;
    }

    const createCard = obterOuCriarCardCriacaoEstadoV9(cardLista);
    createCard.innerHTML = "";

    const block = document.createElement("div");
    block.className = "appverbo-create-entry-block-v1 appverbo-create-entry-block-v9";

    const toolbar = document.createElement("div");
    toolbar.className = "appverbo-create-entry-toolbar-v1 appverbo-create-entry-toolbar-v9";

    const abrirBtn = document.createElement("button");
    abrirBtn.type = "button";
    abrirBtn.className = "action-btn appverbo-create-entry-open-btn-v1";
    abrirBtn.textContent = "Criar sessão";

    toolbar.appendChild(abrirBtn);

    const panel = document.createElement("div");
    panel.className = "appverbo-create-entry-panel-v1 appverbo-create-entry-panel-v9";
    panel.hidden = true;

    const grid = document.createElement("div");
    grid.className = "appverbo-create-entry-grid-v5 appverbo-create-entry-grid-v9";

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

    const sistemaSelect = criarSelectSistemaEstadoV9("all");

    sistemaField.appendChild(sistemaLabel);
    sistemaField.appendChild(sistemaSelect);

    const estadoField = document.createElement("div");
    estadoField.className = "field appverbo-create-entry-field-v5";

    const estadoLabel = document.createElement("label");
    estadoLabel.textContent = "Estado *";

    const estadoSelect = criarSelectEstadoEstadoV9("ativo");

    estadoField.appendChild(estadoLabel);
    estadoField.appendChild(estadoSelect);

    grid.appendChild(nomeField);
    grid.appendChild(sistemaField);
    grid.appendChild(estadoField);

    const erro = document.createElement("p");
    erro.className = "appverbo-create-entry-error-v5 appverbo-create-entry-error-v9";
    erro.hidden = true;

    const actions = document.createElement("div");
    actions.className = "appverbo-create-entry-actions-v5 appverbo-create-entry-actions-v9";

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

    function fechar() {
      nomeInput.value = "";
      sistemaSelect.value = "all";
      estadoSelect.value = "ativo";
      erro.hidden = true;
      erro.textContent = "";
      panel.hidden = true;
      abrirBtn.hidden = false;
    }

    abrirBtn.addEventListener("click", function () {
      panel.hidden = false;
      abrirBtn.hidden = true;
      erro.hidden = true;
      nomeInput.focus();
    });

    cancelarBtn.addEventListener("click", fechar);

    guardarBtn.addEventListener("click", function () {
      const nome = String(nomeInput.value || "").trim();

      if (!nome) {
        erro.textContent = "Informe o nome da sessão.";
        erro.hidden = false;
        nomeInput.focus();
        return;
      }

      const estado = normalizarEstadoSessoesEstadoV9(estadoSelect.value);

      sessoesEstadoV9.push({
        key: gerarChaveUnicaEstadoV9(nome),
        label: nome,
        visibility_scope_mode: sistemaSelect.value || "all",
        visibility_scope_label: obterLabelSistemaSessoesEstadoV9(sistemaSelect.value || "all", ""),
        status: estado,
        is_active: estado === "ativo",
        status_label: obterLabelEstadoSessoesEstadoV9(estado)
      });

      fechar();
      renderizarListaEstadoV9();
      submeterFormularioEstadoV9();
    });
  }

  //###################################################################################
  // (7) EDICAO E ACOES
  //###################################################################################

  function moverSessaoEstadoV9(chave, direcao) {
    const indice = encontrarIndiceSessaoEstadoV9(chave);

    if (indice < 0) {
      return;
    }

    const sessao = sessoesEstadoV9[indice];
    const statusAtual = normalizarEstadoSessoesEstadoV9(sessao.status);

    const indicesMesmoGrupo = sessoesEstadoV9
      .map(function (item, index) {
        return {
          item: item,
          index: index
        };
      })
      .filter(function (entry) {
        return normalizarEstadoSessoesEstadoV9(entry.item.status) === statusAtual;
      })
      .map(function (entry) {
        return entry.index;
      });

    const posicaoGrupo = indicesMesmoGrupo.indexOf(indice);

    if (direcao === "up" && posicaoGrupo > 0) {
      const indiceAnterior = indicesMesmoGrupo[posicaoGrupo - 1];
      const temp = sessoesEstadoV9[indiceAnterior];
      sessoesEstadoV9[indiceAnterior] = sessoesEstadoV9[indice];
      sessoesEstadoV9[indice] = temp;
    }

    if (direcao === "down" && posicaoGrupo < indicesMesmoGrupo.length - 1) {
      const indiceProximo = indicesMesmoGrupo[posicaoGrupo + 1];
      const temp = sessoesEstadoV9[indiceProximo];
      sessoesEstadoV9[indiceProximo] = sessoesEstadoV9[indice];
      sessoesEstadoV9[indice] = temp;
    }

    renderizarListaEstadoV9();
    submeterFormularioEstadoV9();
  }

  function abrirEdicaoEstadoV9(linha) {
    const chave = linha.dataset.sectionKeyV9;
    const indice = encontrarIndiceSessaoEstadoV9(chave);

    if (indice < 0) {
      return;
    }

    const sessao = Object.assign({}, sessoesEstadoV9[indice]);

    const tdMenu = linha.querySelector(".appverbo-sidebar-section-menu-cell-v2");
    const tdSistema = linha.querySelector(".appverbo-sidebar-section-system-cell-v2");
    const tdEstado = linha.querySelector(".appverbo-sidebar-section-state-cell-v2");
    const tdAcoes = linha.querySelector(".appverbo-sidebar-section-actions-cell-v2");

    if (!tdMenu || !tdSistema || !tdEstado || !tdAcoes) {
      return;
    }

    const nomeInput = document.createElement("input");
    nomeInput.type = "text";
    nomeInput.className = "appverbo-sidebar-section-edit-input-v9";
    nomeInput.value = sessao.label;
    nomeInput.maxLength = 80;

    const sistemaSelect = criarSelectSistemaEstadoV9(sessao.visibility_scope_mode);
    const estadoSelect = criarSelectEstadoEstadoV9(sessao.status);

    tdMenu.innerHTML = "";
    tdMenu.appendChild(nomeInput);

    tdSistema.innerHTML = "";
    tdSistema.appendChild(sistemaSelect);

    tdEstado.innerHTML = "";
    tdEstado.appendChild(estadoSelect);

    tdAcoes.innerHTML = "";

    const actions = document.createElement("div");
    actions.className = "appverbo-sidebar-section-edit-actions-v9";

    const guardarBtn = document.createElement("button");
    guardarBtn.type = "button";
    guardarBtn.className = "action-btn appverbo-sidebar-section-edit-save-v9";
    guardarBtn.textContent = "Guardar";

    const cancelarBtn = document.createElement("button");
    cancelarBtn.type = "button";
    cancelarBtn.className = "action-btn-cancel appverbo-sidebar-section-edit-cancel-v9";
    cancelarBtn.textContent = "Cancelar";

    actions.appendChild(guardarBtn);
    actions.appendChild(cancelarBtn);
    tdAcoes.appendChild(actions);

    guardarBtn.addEventListener("click", function () {
      const nome = String(nomeInput.value || "").trim();

      if (!nome) {
        nomeInput.classList.add("appverbo-sidebar-section-edit-input-error-v9");
        nomeInput.focus();
        return;
      }

      const estado = normalizarEstadoSessoesEstadoV9(estadoSelect.value);

      sessoesEstadoV9[indice] = {
        key: sessao.key,
        label: nome,
        visibility_scope_mode: sistemaSelect.value || "all",
        visibility_scope_label: obterLabelSistemaSessoesEstadoV9(sistemaSelect.value || "all", ""),
        status: estado,
        is_active: estado === "ativo",
        status_label: obterLabelEstadoSessoesEstadoV9(estado)
      };

      renderizarListaEstadoV9();
      submeterFormularioEstadoV9();
    });

    cancelarBtn.addEventListener("click", function () {
      renderizarListaEstadoV9();
    });

    nomeInput.addEventListener("keydown", function (event) {
      if (event.key === "Enter") {
        event.preventDefault();
        guardarBtn.click();
      }

      if (event.key === "Escape") {
        event.preventDefault();
        cancelarBtn.click();
      }
    });

    nomeInput.focus();
    nomeInput.select();
  }

  function instalarEventosListaEstadoV9() {
    const cardLista = obterCardListaEstadoV9();

    if (!cardLista || cardLista.dataset.eventsEstadoV9 === "1") {
      return;
    }

    cardLista.dataset.eventsEstadoV9 = "1";

    cardLista.addEventListener("click", function (event) {
      const botao = event.target.closest("[data-sidebar-section-action-v9]");

      if (!botao) {
        return;
      }

      const linha = botao.closest("tr.appverbo-sidebar-section-row-v9");

      if (!linha) {
        return;
      }

      const acao = botao.dataset.sidebarSectionActionV9;
      const chave = linha.dataset.sectionKeyV9;
      const indice = encontrarIndiceSessaoEstadoV9(chave);
      const sessao = indice >= 0 ? sessoesEstadoV9[indice] : null;

      if (acao === "up" || acao === "down") {
        moverSessaoEstadoV9(chave, acao);
      }

      if (acao === "view" && sessao) {
        alert(
          "Nome da sessão: " + sessao.label +
          "\nSistema: " + obterLabelSistemaSessoesEstadoV9(sessao.visibility_scope_mode, sessao.visibility_scope_label || "") +
          "\nEstado: " + obterLabelEstadoSessoesEstadoV9(sessao.status)
        );
      }

      if (acao === "edit") {
        abrirEdicaoEstadoV9(linha);
      }
    });
  }

  //###################################################################################
  // (8) INSTALAR
  //###################################################################################

  async function instalarSessoesEstadoV9(force) {
    const cardLista = obterCardListaEstadoV9();

    if (!cardLista) {
      return;
    }

    if (instaladoEstadoV9 && !force) {
      return;
    }

    const raw = await carregarSessoesEstadoV9();
    const normalizadas = raw.map(normalizarSessaoEstadoV9).filter(Boolean);

    if (!normalizadas.length) {
      return;
    }

    sessoesEstadoV9 = normalizadas;
    instaladoEstadoV9 = true;

    instalarCriacaoEstadoV9();
    renderizarListaEstadoV9();
    instalarEventosListaEstadoV9();
  }

  function iniciarSessoesEstadoV9() {
    window.setTimeout(function () {
      instalarSessoesEstadoV9(true);
    }, 500);

    window.setTimeout(function () {
      instalarSessoesEstadoV9(true);
    }, 1200);

    window.setTimeout(function () {
      instalarSessoesEstadoV9(true);
    }, 2000);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", iniciarSessoesEstadoV9);
  } else {
    iniciarSessoesEstadoV9();
  }
})();
// APPVERBO_SESSOES_ESTADO_BLOCOS_V9_END
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

print("OK: JS V9 aplicado para Estado e blocos Ativo/Inativo.")


####################################################################################
# (7) ADICIONAR CSS V9
####################################################################################

css_content = CSS_PATH.read_text(encoding="utf-8")

css_block = f'''{CSS_MARKER_START}

.appverbo-sidebar-section-list-block-v9 {{
  margin-top: 10px;
}}

.appverbo-sidebar-section-list-block-inativo-v9 {{
  margin-top: 22px;
  padding-top: 14px;
  border-top: 1px solid #d5dceb;
}}

.appverbo-sidebar-section-list-title-v9 {{
  margin: 0 0 10px;
  color: #12213a;
  font-size: 18px;
  font-weight: 800;
}}

.appverbo-sidebar-sections-list-description-v9 {{
  margin: 0 0 12px;
  color: #52607a;
  font-size: 13px;
}}

.appverbo-sidebar-section-empty-row-v9 td {{
  color: #52607a;
  padding: 14px 6px;
}}

.appverbo-sidebar-section-state-badge-inativo-v9 {{
  border-color: #f0c36d !important;
  background: #fff7e0 !important;
  color: #8a5a00 !important;
}}

.appverbo-sidebar-section-edit-input-v9,
.appverbo-sidebar-section-edit-select-v9 {{
  width: 100%;
  max-width: 320px;
  border: 1px solid #c6d0e2;
  border-radius: 7px;
  background: #ffffff;
  color: #12213a;
  min-height: 34px;
  padding: 7px 9px;
  box-sizing: border-box;
  font-size: 12px;
}}

.appverbo-sidebar-section-edit-input-v9:focus,
.appverbo-sidebar-section-edit-select-v9:focus {{
  border-color: #2454b0;
  outline: none;
  box-shadow: 0 0 0 2px rgba(36, 84, 176, 0.12);
}}

.appverbo-sidebar-section-edit-input-error-v9 {{
  border-color: #d93025 !important;
}}

.appverbo-sidebar-section-edit-actions-v9 {{
  display: inline-flex;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
  white-space: nowrap;
}}

.appverbo-sidebar-section-edit-actions-v9 .action-btn,
.appverbo-sidebar-section-edit-actions-v9 .action-btn-cancel {{
  min-width: 78px !important;
  width: 78px !important;
  height: 30px !important;
  min-height: 30px !important;
  padding: 0 8px !important;
  font-size: 11px !important;
}}

.appverbo-create-entry-panel-v9[hidden] {{
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

print("OK: CSS V9 aplicado.")


####################################################################################
# (8) ATUALIZAR CACHE BUSTER
####################################################################################

template_content = TEMPLATE_PATH.read_text(encoding="utf-8")

if "static/js/modules/sidebar_sections_layout_v1.js" in template_content:
    template_content = re.sub(
        r"/static/js/modules/sidebar_sections_layout_v1\.js\?v=[^\"]+",
        JS_CACHE,
        template_content,
    )
else:
    fail_v9("não encontrei sidebar_sections_layout_v1.js no template.")

if "static/css/modules/sidebar_sections_layout_v1.css" in template_content:
    template_content = re.sub(
        r"/static/css/modules/sidebar_sections_layout_v1\.css\?v=[^\"]+",
        CSS_CACHE,
        template_content,
    )
else:
    fail_v9("não encontrei sidebar_sections_layout_v1.css no template.")

TEMPLATE_PATH.write_text(template_content, encoding="utf-8")

print("OK: cache buster atualizado.")


####################################################################################
# (9) VALIDAR CONTEUDO
####################################################################################

agents_validado = agents_path.read_text(encoding="utf-8")
menu_settings_validado = MENU_SETTINGS_PATH.read_text(encoding="utf-8")
settings_validado = SETTINGS_HANDLERS_PATH.read_text(encoding="utf-8")
js_validado = JS_PATH.read_text(encoding="utf-8")
css_validado = CSS_PATH.read_text(encoding="utf-8")
template_validado = TEMPLATE_PATH.read_text(encoding="utf-8")

validacoes = {
    "APPVERBO_SESSOES_ESTADO_BLOCOS_V9_START": agents_validado,
    "section_status: list[str] = Form(default=[])": settings_validado,
    '"status": (': settings_validado,
    "_normalize_sidebar_section_status_v5": menu_settings_validado,
    '"status": normalized_status': menu_settings_validado,
    "APPVERBO_SESSOES_ESTADO_BLOCOS_V9_START": js_validado,
    "Sessões inativas": js_validado,
    "normalizarEstadoSessoesEstadoV9": js_validado,
    "abrirEdicaoEstadoV9": js_validado,
    "data-sidebar-section-action-v9": js_validado,
    "APPVERBO_SESSOES_ESTADO_BLOCOS_V9_START": css_validado,
    "appverbo-sidebar-section-list-block-inativo-v9": css_validado,
    "20260505-sessoes-estado-blocos-v9": template_validado,
}

for termo, conteudo in validacoes.items():
    if termo not in conteudo:
        fail_v9(f"validação falhou, termo ausente: {termo}")

try:
    ast.parse(menu_settings_validado)
    ast.parse(settings_validado)
except SyntaxError as exc:
    fail_v9(f"Python final inválido: {exc}")

print("OK: patch_sessoes_estado_blocos_v9 concluído.")
