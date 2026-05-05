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

AGENTS_MARKER_START = "<!-- APPVERBO_SESSOES_INATIVAS_CARD_SEPARADO_V10_START -->"
AGENTS_MARKER_END = "<!-- APPVERBO_SESSOES_INATIVAS_CARD_SEPARADO_V10_END -->"

JS_MARKER_START = "// APPVERBO_SESSOES_INATIVAS_CARD_SEPARADO_V10_START"
JS_MARKER_END = "// APPVERBO_SESSOES_INATIVAS_CARD_SEPARADO_V10_END"

CSS_MARKER_START = "/* APPVERBO_SESSOES_INATIVAS_CARD_SEPARADO_V10_START */"
CSS_MARKER_END = "/* APPVERBO_SESSOES_INATIVAS_CARD_SEPARADO_V10_END */"

JS_CACHE = "/static/js/modules/sidebar_sections_layout_v1.js?v=20260505-sessoes-inativas-card-v10"
CSS_CACHE = "/static/css/modules/sidebar_sections_layout_v1.css?v=20260505-sessoes-inativas-card-v10"


def fail_v10(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


####################################################################################
# (1) RESOLVER AGENTS.md
####################################################################################

def resolve_agents_path_v10() -> Path:
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
        fail_v10(f"ficheiro não encontrado: {file_path}")


####################################################################################
# (3) ATUALIZAR REGRA NO AGENTS.md
####################################################################################

agents_path = resolve_agents_path_v10()
agents_content = agents_path.read_text(encoding="utf-8")

agents_rule = f"""{AGENTS_MARKER_START}
## Regra para bloco separado de sessões inativas

Na aba **Sessões**:

1. A lista principal **Sessões do sidebar** deve apresentar somente sessões com Estado **Ativo**.
2. Sessões com Estado diferente de **Ativo** devem aparecer em um card/bloco separado abaixo, chamado **Sessões inativas**.
3. O card **Sessões inativas** deve seguir o mesmo padrão visual de blocos separados usado em **Entidades inativas**.
4. Quando não houver sessões inativas, o card deve permanecer visível com a mensagem **Sem sessões inativas.**
5. Ao alterar o Estado na edição, a sessão deve mudar automaticamente para o card correto.
6. Ao gravar, todos os registros, ativos e inativos, devem ser enviados ao backend através dos campos ocultos do formulário.
7. O campo técnico `section_status` deve persistir o Estado no BD/configuração.
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

print(f"OK: regra de card separado de sessões inativas atualizada em {agents_path}")


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
        fail_v10("não encontrei local para adicionar section_status no endpoint.")

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
        fail_v10("não encontrei rows_count para incluir section_status.")

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
        fail_v10("não encontrei payload para incluir status.")

    settings_handlers = settings_handlers.replace(old_payload, new_payload, 1)

try:
    ast.parse(settings_handlers)
except SyntaxError as exc:
    fail_v10(f"settings_handlers.py ficaria inválido: {exc}")

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
        fail_v10("não encontrei _build_sidebar_section_payload em menu_settings.py.")

    menu_settings = menu_settings.replace(anchor, helper + anchor, 1)

if "status: Any = \"ativo\"" not in menu_settings:
    menu_settings = menu_settings.replace(
        '''    visibility_scopes: Any,
) -> dict[str, Any]:''',
        '''    visibility_scopes: Any,
    status: Any = "ativo",
) -> dict[str, Any]:''',
        1,
    )

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

if '"status": normalized_status' not in menu_settings:
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
    fail_v10(f"menu_settings.py ficaria inválido: {exc}")

MENU_SETTINGS_PATH.write_text(menu_settings, encoding="utf-8")

print("OK: menu_settings.py validado para normalizar e persistir Estado.")


####################################################################################
# (6) ADICIONAR JS V10 PARA CARD SEPARADO DE INATIVOS
####################################################################################

js_content = JS_PATH.read_text(encoding="utf-8")

js_block = r'''// APPVERBO_SESSOES_INATIVAS_CARD_SEPARADO_V10_START
(function () {
  "use strict";

  //###################################################################################
  // (1) NORMALIZACAO
  //###################################################################################

  function normalizarTextoSessoesV10(valor) {
    return String(valor || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase();
  }

  function criarChaveSessoesV10(valor) {
    return normalizarTextoSessoesV10(valor)
      .replace(/[^a-z0-9]+/g, "_")
      .replace(/_+/g, "_")
      .replace(/^_+|_+$/g, "");
  }

  function normalizarEstadoSessoesV10(valor) {
    const cleanValor = normalizarTextoSessoesV10(valor);

    if (["inativo", "inactive", "0", "false", "nao", "não", "off"].includes(cleanValor)) {
      return "inativo";
    }

    return "ativo";
  }

  function obterLabelEstadoSessoesV10(valor) {
    return normalizarEstadoSessoesV10(valor) === "inativo" ? "Inativo" : "Ativo";
  }

  function obterLabelSistemaSessoesV10(valor, fallback) {
    const cleanValor = normalizarTextoSessoesV10(valor);

    if (cleanValor === "owner") {
      return "Owner";
    }

    if (cleanValor === "legado") {
      return "Legado";
    }

    return fallback || "Owner e Legado";
  }

  function criarCampoOcultoSessoesV10(nome, valor) {
    const input = document.createElement("input");
    input.type = "hidden";
    input.name = nome;
    input.value = valor || "";
    return input;
  }

  //###################################################################################
  // (2) ESTADO LOCAL E LEITURA
  //###################################################################################

  let sessoesV10 = [];
  let instaladoV10 = false;

  function lerSessoesTemplateV10() {
    const script = document.getElementById("appverbo-sidebar-section-options-v2") ||
      document.getElementById("appverbo-sidebar-section-options-v1");

    if (!script) {
      return [];
    }

    try {
      const parsed = JSON.parse(script.textContent || "[]");
      return Array.isArray(parsed) ? parsed : [];
    } catch (error) {
      console.warn("APPVERBO V10: não foi possível ler sessões do template.", error);
      return [];
    }
  }

  async function carregarSessoesV10() {
    try {
      const response = await fetch("/settings/menu/sidebar-sections-data", {
        headers: {
          Accept: "application/json"
        },
        credentials: "same-origin"
      });

      if (response.ok) {
        const payload = await response.json();

        if (payload && Array.isArray(payload.sections) && payload.sections.length) {
          return payload.sections;
        }
      }
    } catch (error) {
      console.warn("APPVERBO V10: falha ao carregar sessões do BD.", error);
    }

    return lerSessoesTemplateV10();
  }

  function normalizarSessaoV10(sessao) {
    if (!sessao || typeof sessao !== "object") {
      return null;
    }

    const label = String(sessao.label || sessao.name || sessao.title || "").trim();
    const key = criarChaveSessoesV10(sessao.key || sessao.section_key || label);

    if (!label || !key) {
      return null;
    }

    const sistema = String(sessao.visibility_scope_mode || sessao.scope_mode || "all").trim() || "all";
    const estado = normalizarEstadoSessoesV10(
      sessao.status || (sessao.is_active === false ? "inativo" : "ativo")
    );

    return {
      key: key,
      label: label,
      visibility_scope_mode: sistema,
      visibility_scope_label: obterLabelSistemaSessoesV10(sistema, sessao.visibility_scope_label || ""),
      status: estado,
      is_active: estado === "ativo",
      status_label: obterLabelEstadoSessoesV10(estado)
    };
  }

  function encontrarIndiceSessaoV10(chave) {
    const cleanChave = criarChaveSessoesV10(chave);

    return sessoesV10.findIndex(function (sessao) {
      return criarChaveSessoesV10(sessao.key) === cleanChave;
    });
  }

  function gerarChaveUnicaV10(nomeSessao) {
    const baseKey = criarChaveSessoesV10(nomeSessao) || "nova_sessao";
    const usadas = new Set(
      sessoesV10.map(function (sessao) {
        return criarChaveSessoesV10(sessao.key);
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
  // (3) CARDS BASE
  //###################################################################################

  function obterCardAtivasV10() {
    return document.getElementById("admin-sidebar-sections-card");
  }

  function obterOuCriarCardCriacaoV10(cardAtivas) {
    let cardCriacao = document.getElementById("admin-sidebar-sections-create-card");

    if (!cardCriacao) {
      cardCriacao = document.createElement("section");
      cardCriacao.id = "admin-sidebar-sections-create-card";
      cardCriacao.className = "card appverbo-standard-create-card-v4 appverbo-sessoes-create-card-v3 appverbo-sessoes-create-card-v10";
      cardAtivas.parentElement.insertBefore(cardCriacao, cardAtivas);
    }

    return cardCriacao;
  }

  function obterOuCriarCardInativasV10(cardAtivas) {
    let cardInativas = document.getElementById("admin-sidebar-sections-inactive-card");

    if (!cardInativas) {
      cardInativas = document.createElement("section");
      cardInativas.id = "admin-sidebar-sections-inactive-card";
      cardInativas.className = "card appverbo-sidebar-sections-inactive-card-v10";
      cardAtivas.parentElement.insertBefore(cardInativas, cardAtivas.nextSibling);
    }

    return cardInativas;
  }

  function obterOuCriarFormularioV10(cardAtivas) {
    let formulario = cardAtivas.querySelector('form[action*="/settings/menu/sidebar-sections"], form[action*="sidebar-sections"]');

    if (!formulario) {
      formulario = document.createElement("form");
      cardAtivas.appendChild(formulario);
    }

    formulario.method = "post";
    formulario.action = "/settings/menu/sidebar-sections";

    return formulario;
  }

  //###################################################################################
  // (4) PAYLOAD OCULTO
  //###################################################################################

  function adicionarPayloadOcultoV10(formulario) {
    const payload = document.createElement("div");
    payload.className = "appverbo-sidebar-sections-hidden-payload-v10";
    payload.hidden = true;

    payload.appendChild(criarCampoOcultoSessoesV10("redirect_menu", "administrativo"));
    payload.appendChild(criarCampoOcultoSessoesV10("redirect_target", "#admin-sidebar-sections-card"));

    sessoesV10.forEach(function (sessao) {
      payload.appendChild(criarCampoOcultoSessoesV10("section_key", sessao.key));
      payload.appendChild(criarCampoOcultoSessoesV10("section_label", sessao.label));
      payload.appendChild(criarCampoOcultoSessoesV10("section_visibility_scope_mode", sessao.visibility_scope_mode || "all"));
      payload.appendChild(criarCampoOcultoSessoesV10("section_status", normalizarEstadoSessoesV10(sessao.status)));
    });

    formulario.appendChild(payload);
  }

  function submeterFormularioV10() {
    const cardAtivas = obterCardAtivasV10();

    if (!cardAtivas) {
      return;
    }

    const formulario = obterOuCriarFormularioV10(cardAtivas);

    formulario.querySelectorAll(".appverbo-sidebar-sections-hidden-payload-v10").forEach(function (item) {
      item.remove();
    });

    adicionarPayloadOcultoV10(formulario);

    if (typeof formulario.requestSubmit === "function") {
      formulario.requestSubmit();
    } else {
      formulario.submit();
    }
  }

  //###################################################################################
  // (5) COMPONENTES
  //###################################################################################

  function criarBotaoAcaoV10(tipo, titulo, texto) {
    const botao = document.createElement("button");
    botao.type = "button";
    botao.className = "appverbo-sidebar-section-action-btn-v2 appverbo-sidebar-section-action-btn-v10";
    botao.dataset.sidebarSectionActionV10 = tipo;
    botao.title = titulo;
    botao.setAttribute("aria-label", titulo);
    botao.textContent = texto;
    return botao;
  }

  function criarBadgeEstadoV10(estado) {
    const estadoNormalizado = normalizarEstadoSessoesV10(estado);
    const badge = document.createElement("span");
    badge.className = "appverbo-sidebar-section-state-badge-v2 appverbo-sidebar-section-state-badge-" + estadoNormalizado + "-v10";
    badge.textContent = obterLabelEstadoSessoesV10(estadoNormalizado);
    return badge;
  }

  function criarSelectSistemaV10(valorAtual) {
    const select = document.createElement("select");
    select.className = "appverbo-sidebar-section-edit-select-v10";

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

  function criarSelectEstadoV10(valorAtual) {
    const select = document.createElement("select");
    select.className = "appverbo-sidebar-section-edit-select-v10";
    const estadoAtual = normalizarEstadoSessoesV10(valorAtual);

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

  function criarLinhaV10(sessao) {
    const tr = document.createElement("tr");
    tr.className = "appverbo-sidebar-section-row-v2 appverbo-sidebar-section-row-v10";
    tr.dataset.sectionKeyV10 = sessao.key;
    tr.dataset.sectionStatusV10 = normalizarEstadoSessoesV10(sessao.status);

    const tdMenu = document.createElement("td");
    tdMenu.className = "appverbo-sidebar-section-menu-cell-v2";
    tdMenu.textContent = sessao.label;

    const tdSistema = document.createElement("td");
    tdSistema.className = "appverbo-sidebar-section-system-cell-v2";
    tdSistema.textContent = obterLabelSistemaSessoesV10(sessao.visibility_scope_mode, sessao.visibility_scope_label || "");

    const tdEstado = document.createElement("td");
    tdEstado.className = "appverbo-sidebar-section-state-cell-v2";
    tdEstado.appendChild(criarBadgeEstadoV10(sessao.status));

    const tdAcoes = document.createElement("td");
    tdAcoes.className = "appverbo-sidebar-section-actions-cell-v2";

    const actions = document.createElement("div");
    actions.className = "appverbo-sidebar-section-actions-v2";
    actions.appendChild(criarBotaoAcaoV10("up", "Subir sessão", "↑"));
    actions.appendChild(criarBotaoAcaoV10("down", "Descer sessão", "↓"));
    actions.appendChild(criarBotaoAcaoV10("view", "Visualizar detalhes", "👁"));
    actions.appendChild(criarBotaoAcaoV10("edit", "Editar sessão", "✎"));

    tdAcoes.appendChild(actions);

    tr.appendChild(tdMenu);
    tr.appendChild(tdSistema);
    tr.appendChild(tdEstado);
    tr.appendChild(tdAcoes);

    return tr;
  }

  function criarTabelaV10(sessoes, tipo) {
    const tableWrap = document.createElement("div");
    tableWrap.className = "appverbo-sidebar-sections-table-wrap-v2 appverbo-sidebar-sections-table-wrap-v10";

    const table = document.createElement("table");
    table.className = "appverbo-sidebar-sections-table-v2 appverbo-sidebar-sections-table-v10";

    const thead = document.createElement("thead");
    thead.innerHTML = "<tr><th>MENU LATERAL</th><th>SISTEMA</th><th>ESTADO</th><th>AÇÕES</th></tr>";

    const tbody = document.createElement("tbody");
    tbody.className = "appverbo-sidebar-sections-body-v2 appverbo-sidebar-sections-body-v10";
    tbody.dataset.statusGroupV10 = tipo;

    sessoes.forEach(function (sessao) {
      tbody.appendChild(criarLinhaV10(sessao));
    });

    table.appendChild(thead);
    table.appendChild(tbody);
    tableWrap.appendChild(table);

    return tableWrap;
  }

  function atualizarEstadoBotoesV10() {
    document.querySelectorAll("tbody.appverbo-sidebar-sections-body-v10").forEach(function (tbody) {
      const linhas = Array.from(tbody.querySelectorAll("tr.appverbo-sidebar-section-row-v10"));

      linhas.forEach(function (linha, indice) {
        const subir = linha.querySelector('[data-sidebar-section-action-v10="up"]');
        const descer = linha.querySelector('[data-sidebar-section-action-v10="down"]');

        if (subir) {
          subir.disabled = indice === 0;
        }

        if (descer) {
          descer.disabled = indice === linhas.length - 1;
        }
      });
    });
  }

  //###################################################################################
  // (6) RENDERIZAR CARDS SEPARADOS
  //###################################################################################

  function renderizarCardsV10() {
    const cardAtivas = obterCardAtivasV10();

    if (!cardAtivas) {
      return;
    }

    const cardInativas = obterOuCriarCardInativasV10(cardAtivas);
    const formulario = obterOuCriarFormularioV10(cardAtivas);

    const ativas = sessoesV10.filter(function (sessao) {
      return normalizarEstadoSessoesV10(sessao.status) === "ativo";
    });

    const inativas = sessoesV10.filter(function (sessao) {
      return normalizarEstadoSessoesV10(sessao.status) !== "ativo";
    });

    cardAtivas.innerHTML = "";
    cardInativas.innerHTML = "";

    const tituloAtivas = document.createElement("h2");
    tituloAtivas.className = "appverbo-sidebar-section-list-main-title-v10";
    tituloAtivas.textContent = "Sessoes do sidebar";

    const descricao = document.createElement("p");
    descricao.className = "appverbo-sidebar-sections-list-description-v10";
    descricao.textContent = "Ative os processos do menu lateral. Um menu só aparece quando estiver ativo aqui.";

    formulario.innerHTML = "";
    adicionarPayloadOcultoV10(formulario);

    if (ativas.length) {
      formulario.appendChild(criarTabelaV10(ativas, "ativo"));
    }
    else {
      const emptyAtivas = document.createElement("p");
      emptyAtivas.className = "appverbo-sidebar-section-empty-text-v10";
      emptyAtivas.textContent = "Sem sessões ativas.";
      formulario.appendChild(emptyAtivas);
    }

    cardAtivas.appendChild(tituloAtivas);
    cardAtivas.appendChild(descricao);
    cardAtivas.appendChild(formulario);

    const tituloInativas = document.createElement("h2");
    tituloInativas.className = "appverbo-sidebar-section-list-main-title-v10";
    tituloInativas.textContent = "Sessões inativas";

    cardInativas.appendChild(tituloInativas);

    if (inativas.length) {
      cardInativas.appendChild(criarTabelaV10(inativas, "inativo"));
    }
    else {
      const emptyInativas = document.createElement("p");
      emptyInativas.className = "appverbo-sidebar-section-empty-text-v10";
      emptyInativas.textContent = "Sem sessões inativas.";
      cardInativas.appendChild(emptyInativas);
    }

    atualizarEstadoBotoesV10();
  }

  //###################################################################################
  // (7) CRIAR SESSAO
  //###################################################################################

  function instalarCriacaoV10() {
    const cardAtivas = obterCardAtivasV10();

    if (!cardAtivas || !cardAtivas.parentElement) {
      return;
    }

    const cardCriacao = obterOuCriarCardCriacaoV10(cardAtivas);
    cardCriacao.innerHTML = "";

    const block = document.createElement("div");
    block.className = "appverbo-create-entry-block-v1 appverbo-create-entry-block-v10";

    const toolbar = document.createElement("div");
    toolbar.className = "appverbo-create-entry-toolbar-v1 appverbo-create-entry-toolbar-v10";

    const abrirBtn = document.createElement("button");
    abrirBtn.type = "button";
    abrirBtn.className = "action-btn appverbo-create-entry-open-btn-v1";
    abrirBtn.textContent = "Criar sessão";

    toolbar.appendChild(abrirBtn);

    const panel = document.createElement("div");
    panel.className = "appverbo-create-entry-panel-v1 appverbo-create-entry-panel-v10";
    panel.hidden = true;

    const grid = document.createElement("div");
    grid.className = "appverbo-create-entry-grid-v5 appverbo-create-entry-grid-v10";

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

    const sistemaSelect = criarSelectSistemaV10("all");

    sistemaField.appendChild(sistemaLabel);
    sistemaField.appendChild(sistemaSelect);

    const estadoField = document.createElement("div");
    estadoField.className = "field appverbo-create-entry-field-v5";

    const estadoLabel = document.createElement("label");
    estadoLabel.textContent = "Estado *";

    const estadoSelect = criarSelectEstadoV10("ativo");

    estadoField.appendChild(estadoLabel);
    estadoField.appendChild(estadoSelect);

    grid.appendChild(nomeField);
    grid.appendChild(sistemaField);
    grid.appendChild(estadoField);

    const erro = document.createElement("p");
    erro.className = "appverbo-create-entry-error-v5 appverbo-create-entry-error-v10";
    erro.hidden = true;

    const actions = document.createElement("div");
    actions.className = "appverbo-create-entry-actions-v5 appverbo-create-entry-actions-v10";

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
    cardCriacao.appendChild(block);

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

      const estado = normalizarEstadoSessoesV10(estadoSelect.value);

      sessoesV10.push({
        key: gerarChaveUnicaV10(nome),
        label: nome,
        visibility_scope_mode: sistemaSelect.value || "all",
        visibility_scope_label: obterLabelSistemaSessoesV10(sistemaSelect.value || "all", ""),
        status: estado,
        is_active: estado === "ativo",
        status_label: obterLabelEstadoSessoesV10(estado)
      });

      fechar();
      renderizarCardsV10();
      submeterFormularioV10();
    });
  }

  //###################################################################################
  // (8) EDITAR, VISUALIZAR E ORDENAR
  //###################################################################################

  function moverSessaoV10(chave, direcao) {
    const indice = encontrarIndiceSessaoV10(chave);

    if (indice < 0) {
      return;
    }

    const sessao = sessoesV10[indice];
    const statusAtual = normalizarEstadoSessoesV10(sessao.status);

    const indicesMesmoGrupo = sessoesV10
      .map(function (item, index) {
        return {
          item: item,
          index: index
        };
      })
      .filter(function (entry) {
        return normalizarEstadoSessoesV10(entry.item.status) === statusAtual;
      })
      .map(function (entry) {
        return entry.index;
      });

    const posicaoGrupo = indicesMesmoGrupo.indexOf(indice);

    if (direcao === "up" && posicaoGrupo > 0) {
      const indiceAnterior = indicesMesmoGrupo[posicaoGrupo - 1];
      const temp = sessoesV10[indiceAnterior];
      sessoesV10[indiceAnterior] = sessoesV10[indice];
      sessoesV10[indice] = temp;
    }

    if (direcao === "down" && posicaoGrupo < indicesMesmoGrupo.length - 1) {
      const indiceProximo = indicesMesmoGrupo[posicaoGrupo + 1];
      const temp = sessoesV10[indiceProximo];
      sessoesV10[indiceProximo] = sessoesV10[indice];
      sessoesV10[indice] = temp;
    }

    renderizarCardsV10();
    submeterFormularioV10();
  }

  function abrirEdicaoV10(linha) {
    const chave = linha.dataset.sectionKeyV10;
    const indice = encontrarIndiceSessaoV10(chave);

    if (indice < 0) {
      return;
    }

    const sessao = Object.assign({}, sessoesV10[indice]);

    const tdMenu = linha.querySelector(".appverbo-sidebar-section-menu-cell-v2");
    const tdSistema = linha.querySelector(".appverbo-sidebar-section-system-cell-v2");
    const tdEstado = linha.querySelector(".appverbo-sidebar-section-state-cell-v2");
    const tdAcoes = linha.querySelector(".appverbo-sidebar-section-actions-cell-v2");

    if (!tdMenu || !tdSistema || !tdEstado || !tdAcoes) {
      return;
    }

    const nomeInput = document.createElement("input");
    nomeInput.type = "text";
    nomeInput.className = "appverbo-sidebar-section-edit-input-v10";
    nomeInput.value = sessao.label;
    nomeInput.maxLength = 80;

    const sistemaSelect = criarSelectSistemaV10(sessao.visibility_scope_mode);
    const estadoSelect = criarSelectEstadoV10(sessao.status);

    tdMenu.innerHTML = "";
    tdMenu.appendChild(nomeInput);

    tdSistema.innerHTML = "";
    tdSistema.appendChild(sistemaSelect);

    tdEstado.innerHTML = "";
    tdEstado.appendChild(estadoSelect);

    tdAcoes.innerHTML = "";

    const actions = document.createElement("div");
    actions.className = "appverbo-sidebar-section-edit-actions-v10";

    const guardarBtn = document.createElement("button");
    guardarBtn.type = "button";
    guardarBtn.className = "action-btn appverbo-sidebar-section-edit-save-v10";
    guardarBtn.textContent = "Guardar";

    const cancelarBtn = document.createElement("button");
    cancelarBtn.type = "button";
    cancelarBtn.className = "action-btn-cancel appverbo-sidebar-section-edit-cancel-v10";
    cancelarBtn.textContent = "Cancelar";

    actions.appendChild(guardarBtn);
    actions.appendChild(cancelarBtn);
    tdAcoes.appendChild(actions);

    guardarBtn.addEventListener("click", function () {
      const nome = String(nomeInput.value || "").trim();

      if (!nome) {
        nomeInput.classList.add("appverbo-sidebar-section-edit-input-error-v10");
        nomeInput.focus();
        return;
      }

      const estado = normalizarEstadoSessoesV10(estadoSelect.value);

      sessoesV10[indice] = {
        key: sessao.key,
        label: nome,
        visibility_scope_mode: sistemaSelect.value || "all",
        visibility_scope_label: obterLabelSistemaSessoesV10(sistemaSelect.value || "all", ""),
        status: estado,
        is_active: estado === "ativo",
        status_label: obterLabelEstadoSessoesV10(estado)
      };

      renderizarCardsV10();
      submeterFormularioV10();
    });

    cancelarBtn.addEventListener("click", function () {
      renderizarCardsV10();
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

  function instalarEventosV10() {
    if (document.body.dataset.appverboSessoesEventosV10 === "1") {
      return;
    }

    document.body.dataset.appverboSessoesEventosV10 = "1";

    document.addEventListener("click", function (event) {
      const botao = event.target.closest("[data-sidebar-section-action-v10]");

      if (!botao) {
        return;
      }

      const linha = botao.closest("tr.appverbo-sidebar-section-row-v10");

      if (!linha) {
        return;
      }

      const acao = botao.dataset.sidebarSectionActionV10;
      const chave = linha.dataset.sectionKeyV10;
      const indice = encontrarIndiceSessaoV10(chave);
      const sessao = indice >= 0 ? sessoesV10[indice] : null;

      if (acao === "up" || acao === "down") {
        moverSessaoV10(chave, acao);
      }

      if (acao === "view" && sessao) {
        alert(
          "Nome da sessão: " + sessao.label +
          "\nSistema: " + obterLabelSistemaSessoesV10(sessao.visibility_scope_mode, sessao.visibility_scope_label || "") +
          "\nEstado: " + obterLabelEstadoSessoesV10(sessao.status)
        );
      }

      if (acao === "edit") {
        abrirEdicaoV10(linha);
      }
    });
  }

  //###################################################################################
  // (9) INSTALAR
  //###################################################################################

  async function instalarSessoesV10(force) {
    const cardAtivas = obterCardAtivasV10();

    if (!cardAtivas) {
      return;
    }

    if (instaladoV10 && !force) {
      return;
    }

    const raw = await carregarSessoesV10();
    const normalizadas = raw.map(normalizarSessaoV10).filter(Boolean);

    if (!normalizadas.length) {
      return;
    }

    sessoesV10 = normalizadas;
    instaladoV10 = true;

    instalarCriacaoV10();
    renderizarCardsV10();
    instalarEventosV10();
  }

  function iniciarSessoesV10() {
    window.setTimeout(function () {
      instalarSessoesV10(true);
    }, 700);

    window.setTimeout(function () {
      instalarSessoesV10(true);
    }, 1500);

    window.setTimeout(function () {
      instalarSessoesV10(true);
    }, 2600);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", iniciarSessoesV10);
  } else {
    iniciarSessoesV10();
  }
})();
// APPVERBO_SESSOES_INATIVAS_CARD_SEPARADO_V10_END
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

print("OK: JS V10 aplicado para separar Sessões inativas em card próprio.")


####################################################################################
# (7) ADICIONAR CSS V10
####################################################################################

css_content = CSS_PATH.read_text(encoding="utf-8")

css_block = f'''{CSS_MARKER_START}

#admin-sidebar-sections-inactive-card {{
  margin-top: 12px;
}}

.appverbo-sidebar-sections-inactive-card-v10 {{
  padding: 16px;
  border: 1px solid #d5dceb;
  border-radius: 8px;
  background: #ffffff;
}}

.appverbo-sidebar-section-list-main-title-v10 {{
  margin: 0 0 12px;
  color: #12213a;
  font-size: 22px;
  font-weight: 800;
}}

.appverbo-sidebar-sections-list-description-v10 {{
  margin: 0 0 12px;
  color: #52607a;
  font-size: 13px;
}}

.appverbo-sidebar-section-empty-text-v10 {{
  margin: 0;
  color: #52607a;
  font-size: 14px;
}

.appverbo-sidebar-sections-table-wrap-v10 {{
  width: 100%;
}}

.appverbo-sidebar-sections-table-v10 {{
  width: 100%;
}}

.appverbo-sidebar-section-row-v10 td {{
  height: 44px;
}}

.appverbo-sidebar-section-state-badge-inativo-v10 {{
  border-color: #f0c36d !important;
  background: #fff7e0 !important;
  color: #8a5a00 !important;
}}

.appverbo-sidebar-section-edit-input-v10,
.appverbo-sidebar-section-edit-select-v10 {{
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

.appverbo-sidebar-section-edit-input-v10:focus,
.appverbo-sidebar-section-edit-select-v10:focus {{
  border-color: #2454b0;
  outline: none;
  box-shadow: 0 0 0 2px rgba(36, 84, 176, 0.12);
}}

.appverbo-sidebar-section-edit-input-error-v10 {{
  border-color: #d93025 !important;
}}

.appverbo-sidebar-section-edit-actions-v10 {{
  display: inline-flex;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
  white-space: nowrap;
}}

.appverbo-sidebar-section-edit-actions-v10 .action-btn,
.appverbo-sidebar-section-edit-actions-v10 .action-btn-cancel {{
  min-width: 78px !important;
  width: 78px !important;
  height: 30px !important;
  min-height: 30px !important;
  padding: 0 8px !important;
  font-size: 11px !important;
}}

.appverbo-create-entry-panel-v10[hidden] {{
  display: none !important;
}}

.appverbo-sidebar-sections-hidden-payload-v10 {{
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

print("OK: CSS V10 aplicado para card separado de Sessões inativas.")


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
    fail_v10("não encontrei sidebar_sections_layout_v1.js no template.")

if "static/css/modules/sidebar_sections_layout_v1.css" in template_content:
    template_content = re.sub(
        r"/static/css/modules/sidebar_sections_layout_v1\.css\?v=[^\"]+",
        CSS_CACHE,
        template_content,
    )
else:
    fail_v10("não encontrei sidebar_sections_layout_v1.css no template.")

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
    "APPVERBO_SESSOES_INATIVAS_CARD_SEPARADO_V10_START": agents_validado,
    "Sessões inativas": agents_validado,
    "section_status: list[str] = Form(default=[])": settings_validado,
    '"status": (': settings_validado,
    "_normalize_sidebar_section_status_v5": menu_settings_validado,
    '"status": normalized_status': menu_settings_validado,
    "APPVERBO_SESSOES_INATIVAS_CARD_SEPARADO_V10_START": js_validado,
    "admin-sidebar-sections-inactive-card": js_validado,
    "Sessões inativas": js_validado,
    "Sem sessões inativas.": js_validado,
    "section_status": js_validado,
    "APPVERBO_SESSOES_INATIVAS_CARD_SEPARADO_V10_START": css_validado,
    "appverbo-sidebar-sections-inactive-card-v10": css_validado,
    "20260505-sessoes-inativas-card-v10": template_validado,
}

for termo, conteudo in validacoes.items():
    if termo not in conteudo:
        fail_v10(f"validação falhou, termo ausente: {termo}")

try:
    ast.parse(menu_settings_validado)
    ast.parse(settings_validado)
except SyntaxError as exc:
    fail_v10(f"Python final inválido: {exc}")

print("OK: patch_sessoes_inativas_card_separado_v10 concluído.")
