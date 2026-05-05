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

AGENTS_MARKER_START = "<!-- APPVERBO_SESSOES_REIDRATAR_BD_V6_START -->"
AGENTS_MARKER_END = "<!-- APPVERBO_SESSOES_REIDRATAR_BD_V6_END -->"

ENDPOINT_MARKER_START = "# APPVERBO_SIDEBAR_SECTIONS_DATA_ENDPOINT_V6_START"
ENDPOINT_MARKER_END = "# APPVERBO_SIDEBAR_SECTIONS_DATA_ENDPOINT_V6_END"

JS_MARKER_START = "// APPVERBO_SESSOES_REIDRATAR_LISTA_BD_V6_START"
JS_MARKER_END = "// APPVERBO_SESSOES_REIDRATAR_LISTA_BD_V6_END"

CSS_MARKER_START = "/* APPVERBO_SESSOES_REIDRATAR_LISTA_BD_V6_START */"
CSS_MARKER_END = "/* APPVERBO_SESSOES_REIDRATAR_LISTA_BD_V6_END */"

JS_CACHE = "/static/js/modules/sidebar_sections_layout_v1.js?v=20260505-sessoes-reidratar-bd-v6"
CSS_CACHE = "/static/css/modules/sidebar_sections_layout_v1.css?v=20260505-sessoes-reidratar-bd-v6"


def fail_v6(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


####################################################################################
# (1) RESOLVER AGENTS.md
####################################################################################

def resolve_agents_path_v6() -> Path:
    if AGENTS_UPPER_PATH.exists():
        return AGENTS_UPPER_PATH

    if AGENTS_TITLE_PATH.exists():
        return AGENTS_TITLE_PATH

    AGENTS_UPPER_PATH.write_text("# AGENTS.md\n\n", encoding="utf-8")
    return AGENTS_UPPER_PATH


####################################################################################
# (2) ATUALIZAR REGRA NO AGENTS.md
####################################################################################

agents_path = resolve_agents_path_v6()
agents_content = agents_path.read_text(encoding="utf-8")

agents_rule = f"""{AGENTS_MARKER_START}
## Regra para reidratação das Sessões pelo BD

Na aba **Sessões**, a lista inferior deve sempre ser reidratada a partir do BD/configuração persistida.

1. O bloco **Criar sessão** é apenas o formulário de criação.
2. A listagem **Sessões do sidebar** deve mostrar todas as sessões existentes no BD.
3. Se o JavaScript principal falhar ou montar a tela sem linhas, deve existir recuperação consultando o endpoint de dados das sessões.
4. Os campos visíveis de criação devem permanecer:
   - Nome da sessão;
   - Sistema;
   - Estado.
5. A chave técnica continua oculta e gerada automaticamente.
6. Os botões Guardar/Cancelar devem ficar apenas no bloco de criação.
7. A hierarquia da tabela deve ser gravada conforme a ordem das linhas renderizadas.
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

print(f"OK: regra de reidratação BD atualizada em {agents_path}")


####################################################################################
# (3) VALIDAR FICHEIROS
####################################################################################

for file_path in [TEMPLATE_PATH, SETTINGS_HANDLERS_PATH, JS_PATH, CSS_PATH]:
    if not file_path.exists():
        fail_v6(f"ficheiro não encontrado: {file_path}")


####################################################################################
# (4) ADICIONAR ENDPOINT PARA LER SESSOES DIRETO DO BD
####################################################################################

settings_handlers = SETTINGS_HANDLERS_PATH.read_text(encoding="utf-8")

endpoint_code = f'''{ENDPOINT_MARKER_START}

# ###################################################################################
# (SIDEBAR_SECTIONS_DATA_ENDPOINT_V6) LER SESSOES DO SIDEBAR DIRETO DO BD
# ###################################################################################

@router.get("/settings/menu/sidebar-sections-data")
def get_sidebar_sections_data_v6(request: Request) -> JSONResponse:
    with SessionLocal() as session:
        current_user = get_current_user(request, session)

        if current_user is None:
            return JSONResponse(
                {{"ok": False, "sections": [], "error": "Efetue login para continuar."}},
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            from appverbo.menu_settings import (
                MENU_CONFIG_SIDEBAR_SECTIONS_KEY,
                normalize_sidebar_sections,
            )

            raw_menu_config = session.execute(
                text(
                    """
                    SELECT menu_config
                    FROM sidebar_menu_settings
                    WHERE lower(trim(menu_key)) = :menu_key
                    LIMIT 1
                    """
                ),
                {{"menu_key": "administrativo"}},
            ).scalar_one_or_none()

            try:
                menu_config = json.loads(raw_menu_config or "{{}}")
            except (TypeError, ValueError):
                menu_config = {{}}

            if not isinstance(menu_config, dict):
                menu_config = {{}}

            sections = normalize_sidebar_sections(
                menu_config.get(MENU_CONFIG_SIDEBAR_SECTIONS_KEY)
            )

            return JSONResponse(
                {{
                    "ok": True,
                    "sections": sections,
                }}
            )
        except Exception as exc:
            return JSONResponse(
                {{
                    "ok": False,
                    "sections": [],
                    "error": str(exc),
                }},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

{ENDPOINT_MARKER_END}
'''

if ENDPOINT_MARKER_START in settings_handlers and ENDPOINT_MARKER_END in settings_handlers:
    endpoint_pattern = re.compile(
        re.escape(ENDPOINT_MARKER_START) + r"[\s\S]*?" + re.escape(ENDPOINT_MARKER_END),
        re.S,
    )
    settings_handlers = endpoint_pattern.sub(endpoint_code.strip(), settings_handlers, count=1)
else:
    anchor = "# APPVERBO_SIDEBAR_SECTIONS_HANDLER_V2_START"

    if anchor not in settings_handlers:
        fail_v6("não encontrei âncora APPVERBO_SIDEBAR_SECTIONS_HANDLER_V2_START.")

    settings_handlers = settings_handlers.replace(anchor, endpoint_code + "\n\n" + anchor, 1)

try:
    ast.parse(settings_handlers)
except SyntaxError as exc:
    fail_v6(f"settings_handlers.py ficaria inválido: {exc}")

SETTINGS_HANDLERS_PATH.write_text(settings_handlers, encoding="utf-8")

print("OK: endpoint /settings/menu/sidebar-sections-data criado/atualizado.")


####################################################################################
# (5) ADICIONAR REIDRATACAO JS DA LISTAGEM PELO BD
####################################################################################

js_content = JS_PATH.read_text(encoding="utf-8")

repair_js = f'''{JS_MARKER_START}
(function () {{
  "use strict";

  //###################################################################################
  // (1) NORMALIZACAO
  //###################################################################################

  function normalizarTextoSessoesV6(valor) {{
    return String(valor || "")
      .normalize("NFD")
      .replace(/[\\u0300-\\u036f]/g, "")
      .trim()
      .toLowerCase();
  }}

  function criarChaveSessoesV6(valor) {{
    return normalizarTextoSessoesV6(valor)
      .replace(/[^a-z0-9]+/g, "_")
      .replace(/_+/g, "_")
      .replace(/^_+|_+$/g, "");
  }}

  function normalizarEstadoSessoesV6(valor) {{
    const cleanValor = normalizarTextoSessoesV6(valor);

    if (["inativo", "inactive", "0", "false", "nao", "não", "off"].includes(cleanValor)) {{
      return "inativo";
    }}

    return "ativo";
  }}

  function obterLabelEstadoSessoesV6(valor) {{
    return normalizarEstadoSessoesV6(valor) === "inativo" ? "Inativo" : "Ativo";
  }}

  function obterLabelSistemaSessoesV6(valor, fallback) {{
    const cleanValor = normalizarTextoSessoesV6(valor);

    if (cleanValor === "owner") {{
      return "Owner";
    }}

    if (cleanValor === "legado") {{
      return "Legado";
    }}

    return fallback || "Owner e Legado";
  }}

  function criarCampoOcultoSessoesV6(nome, valor) {{
    const input = document.createElement("input");
    input.type = "hidden";
    input.name = nome;
    input.value = valor || "";
    return input;
  }}

  //###################################################################################
  // (2) LER SESSOES DO TEMPLATE OU DO ENDPOINT
  //###################################################################################

  function lerSessoesDoTemplateSessoesV6() {{
    const script = document.getElementById("appverbo-sidebar-section-options-v2") ||
      document.getElementById("appverbo-sidebar-section-options-v1");

    if (!script) {{
      return [];
    }}

    try {{
      const parsed = JSON.parse(script.textContent || "[]");
      return Array.isArray(parsed) ? parsed : [];
    }} catch (error) {{
      console.warn("APPVERBO V6: não foi possível ler sessões do template.", error);
      return [];
    }}
  }}

  async function carregarSessoesBdSessoesV6() {{
    const sessoesTemplate = lerSessoesDoTemplateSessoesV6();

    if (sessoesTemplate.length) {{
      return sessoesTemplate;
    }}

    try {{
      const response = await fetch("/settings/menu/sidebar-sections-data", {{
        headers: {{
          Accept: "application/json"
        }},
        credentials: "same-origin"
      }});

      if (!response.ok) {{
        console.warn("APPVERBO V6: endpoint de sessões respondeu com erro.", response.status);
        return [];
      }}

      const payload = await response.json();

      if (payload && Array.isArray(payload.sections)) {{
        return payload.sections;
      }}
    }} catch (error) {{
      console.warn("APPVERBO V6: falha ao consultar sessões do BD.", error);
    }}

    return [];
  }}

  function normalizarSessaoSessoesV6(sessao) {{
    if (!sessao || typeof sessao !== "object") {{
      return null;
    }}

    const label = String(sessao.label || sessao.name || sessao.title || "").trim();
    const key = criarChaveSessoesV6(sessao.key || sessao.section_key || label);

    if (!label || !key) {{
      return null;
    }}

    const sistema = String(sessao.visibility_scope_mode || sessao.scope_mode || sessao.scope || "all").trim() || "all";
    const estado = normalizarEstadoSessoesV6(
      sessao.status || (sessao.is_active === false ? "inativo" : "ativo")
    );

    return {{
      key: key,
      label: label,
      visibility_scope_mode: sistema,
      visibility_scope_label: obterLabelSistemaSessoesV6(sistema, sessao.visibility_scope_label || ""),
      status: estado,
      is_active: estado === "ativo",
      status_label: obterLabelEstadoSessoesV6(estado)
    }};
  }}

  //###################################################################################
  // (3) CRIAR TABELA DA LISTAGEM
  //###################################################################################

  function criarBotaoAcaoSessoesV6(tipo, titulo, texto) {{
    const botao = document.createElement("button");
    botao.type = "button";
    botao.className = "appverbo-sidebar-section-action-btn-v2 appverbo-sidebar-section-action-btn-v6";
    botao.dataset.sidebarSectionActionV6 = tipo;
    botao.title = titulo;
    botao.setAttribute("aria-label", titulo);
    botao.textContent = texto;
    return botao;
  }}

  function criarLinhaSessoesV6(sessao) {{
    const tr = document.createElement("tr");
    tr.className = "appverbo-sidebar-section-row-v2 appverbo-sidebar-section-row-v6";

    const keyInput = criarCampoOcultoSessoesV6("section_key", sessao.key);
    const labelInput = document.createElement("input");
    labelInput.type = "hidden";
    labelInput.name = "section_label";
    labelInput.value = sessao.label;

    const scopeInput = criarCampoOcultoSessoesV6("section_visibility_scope_mode", sessao.visibility_scope_mode || "all");
    const statusInput = criarCampoOcultoSessoesV6("section_status", sessao.status || "ativo");

    const tdMenu = document.createElement("td");
    tdMenu.className = "appverbo-sidebar-section-menu-cell-v2";
    tdMenu.textContent = sessao.label;
    tdMenu.appendChild(keyInput);
    tdMenu.appendChild(labelInput);
    tdMenu.appendChild(scopeInput);
    tdMenu.appendChild(statusInput);

    const tdSistema = document.createElement("td");
    tdSistema.className = "appverbo-sidebar-section-system-cell-v2";
    tdSistema.textContent = obterLabelSistemaSessoesV6(
      sessao.visibility_scope_mode,
      sessao.visibility_scope_label || "Owner e Legado"
    );

    const tdEstado = document.createElement("td");
    tdEstado.className = "appverbo-sidebar-section-state-cell-v2";

    const estado = normalizarEstadoSessoesV6(sessao.status);
    const badge = document.createElement("span");
    badge.className = "appverbo-sidebar-section-state-badge-v2 appverbo-sidebar-section-state-badge-" + estado + "-v6";
    badge.textContent = obterLabelEstadoSessoesV6(estado);
    tdEstado.appendChild(badge);

    const tdAcoes = document.createElement("td");
    tdAcoes.className = "appverbo-sidebar-section-actions-cell-v2";

    const actions = document.createElement("div");
    actions.className = "appverbo-sidebar-section-actions-v2";
    actions.appendChild(criarBotaoAcaoSessoesV6("up", "Subir sessão", "↑"));
    actions.appendChild(criarBotaoAcaoSessoesV6("down", "Descer sessão", "↓"));
    actions.appendChild(criarBotaoAcaoSessoesV6("view", "Visualizar detalhes", "👁"));
    actions.appendChild(criarBotaoAcaoSessoesV6("edit", "Editar sessão", "✎"));

    tdAcoes.appendChild(actions);

    tr.appendChild(tdMenu);
    tr.appendChild(tdSistema);
    tr.appendChild(tdEstado);
    tr.appendChild(tdAcoes);

    return tr;
  }}

  function atualizarEstadoBotoesSessoesV6(tbody) {{
    const linhas = Array.from(tbody.querySelectorAll("tr.appverbo-sidebar-section-row-v6"));

    linhas.forEach(function (linha, indice) {{
      const subir = linha.querySelector('[data-sidebar-section-action-v6="up"]');
      const descer = linha.querySelector('[data-sidebar-section-action-v6="down"]');

      if (subir) {{
        subir.disabled = indice === 0;
      }}

      if (descer) {{
        descer.disabled = indice === linhas.length - 1;
      }}
    }});
  }}

  function submeterFormularioSessoesV6(formulario) {{
    if (!formulario) {{
      return;
    }}

    if (typeof formulario.requestSubmit === "function") {{
      formulario.requestSubmit();
    }} else {{
      formulario.submit();
    }}
  }}

  function moverLinhaSessoesV6(linha, direcao) {{
    const tbody = linha && linha.parentElement;

    if (!tbody) {{
      return;
    }}

    if (direcao === "up") {{
      const anterior = linha.previousElementSibling;

      if (anterior && anterior.classList.contains("appverbo-sidebar-section-row-v6")) {{
        tbody.insertBefore(linha, anterior);
      }}
    }}

    if (direcao === "down") {{
      const proxima = linha.nextElementSibling;

      if (proxima && proxima.classList.contains("appverbo-sidebar-section-row-v6")) {{
        tbody.insertBefore(proxima, linha);
      }}
    }}

    atualizarEstadoBotoesSessoesV6(tbody);
    submeterFormularioSessoesV6(linha.closest("form"));
  }}

  function criarTabelaSessoesV6(formulario, sessoes) {{
    formulario.innerHTML = "";
    formulario.method = "post";
    formulario.action = "/settings/menu/sidebar-sections";

    formulario.appendChild(criarCampoOcultoSessoesV6("redirect_menu", "administrativo"));
    formulario.appendChild(criarCampoOcultoSessoesV6("redirect_target", "#admin-sidebar-sections-card"));

    const descricao = document.createElement("p");
    descricao.className = "appverbo-sidebar-sections-list-description-v6";
    descricao.textContent = "Ative os processos do menu lateral. Um menu só aparece quando estiver ativo aqui.";

    const tableWrap = document.createElement("div");
    tableWrap.className = "appverbo-sidebar-sections-table-wrap-v2 appverbo-sidebar-sections-table-wrap-v6";

    const table = document.createElement("table");
    table.className = "appverbo-sidebar-sections-table-v2 appverbo-sidebar-sections-table-v6";

    const thead = document.createElement("thead");
    thead.innerHTML = "<tr><th>MENU LATERAL</th><th>SISTEMA</th><th>ESTADO</th><th>AÇÕES</th></tr>";

    const tbody = document.createElement("tbody");
    tbody.className = "appverbo-sidebar-sections-body-v2 appverbo-sidebar-sections-body-v6";

    sessoes.forEach(function (sessao) {{
      tbody.appendChild(criarLinhaSessoesV6(sessao));
    }});

    tbody.addEventListener("click", function (event) {{
      const botao = event.target.closest("[data-sidebar-section-action-v6]");

      if (!botao) {{
        return;
      }}

      const linha = botao.closest("tr.appverbo-sidebar-section-row-v6");
      const acao = botao.dataset.sidebarSectionActionV6;

      if (!linha) {{
        return;
      }}

      if (acao === "up" || acao === "down") {{
        moverLinhaSessoesV6(linha, acao);
      }}

      if (acao === "view") {{
        const label = linha.querySelector('[name="section_label"]');
        const key = linha.querySelector('[name="section_key"]');
        const sistema = linha.querySelector('[name="section_visibility_scope_mode"]');
        const estado = linha.querySelector('[name="section_status"]');

        alert(
          "Nome da sessão: " + ((label && label.value) || "") +
          "\\nChave: " + ((key && key.value) || "") +
          "\\nSistema: " + obterLabelSistemaSessoesV6(sistema && sistema.value, "") +
          "\\nEstado: " + obterLabelEstadoSessoesV6(estado && estado.value)
        );
      }}

      if (acao === "edit") {{
        alert("Edição inline será ajustada no próximo passo. Para já, use Criar sessão para novas entradas.");
      }}
    }});

    table.appendChild(thead);
    table.appendChild(tbody);
    tableWrap.appendChild(table);

    formulario.appendChild(descricao);
    formulario.appendChild(tableWrap);

    atualizarEstadoBotoesSessoesV6(tbody);

    return tbody;
  }}

  //###################################################################################
  // (4) CRIAR FORMULARIO DE CRIACAO GARANTINDO BD
  //###################################################################################

  function obterOuCriarCardCriacaoSessoesV6(cardLista) {{
    if (!cardLista || !cardLista.parentElement) {{
      return null;
    }}

    let createCard = document.getElementById("admin-sidebar-sections-create-card");

    if (!createCard) {{
      createCard = document.createElement("section");
      createCard.id = "admin-sidebar-sections-create-card";
      createCard.className = "card appverbo-standard-create-card-v4 appverbo-sessoes-create-card-v3";
      cardLista.parentElement.insertBefore(createCard, cardLista);
    }}

    return createCard;
  }}

  function criarOpcaoSelectSessoesV6(valor, texto) {{
    const option = document.createElement("option");
    option.value = valor;
    option.textContent = texto;
    return option;
  }}

  function instalarCriacaoSessoesV6(cardLista, formulario, tbody) {{
    const createCard = obterOuCriarCardCriacaoSessoesV6(cardLista);

    if (!createCard || !formulario || !tbody || createCard.dataset.createRepairV6 === "1") {{
      return;
    }}

    createCard.dataset.createRepairV6 = "1";
    createCard.innerHTML = "";

    const block = document.createElement("div");
    block.className = "appverbo-create-entry-block-v1 appverbo-create-entry-block-v6";

    const toolbar = document.createElement("div");
    toolbar.className = "appverbo-create-entry-toolbar-v1";

    const abrirBtn = document.createElement("button");
    abrirBtn.type = "button";
    abrirBtn.className = "action-btn appverbo-create-entry-open-btn-v1";
    abrirBtn.textContent = "Criar sessão";

    toolbar.appendChild(abrirBtn);

    const panel = document.createElement("div");
    panel.className = "appverbo-create-entry-panel-v1 appverbo-create-entry-panel-v6";
    panel.hidden = true;

    const grid = document.createElement("div");
    grid.className = "appverbo-create-entry-grid-v5 appverbo-create-entry-grid-v6";

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
    sistemaSelect.appendChild(criarOpcaoSelectSessoesV6("all", "Owner e Legado"));
    sistemaSelect.appendChild(criarOpcaoSelectSessoesV6("owner", "Owner"));
    sistemaSelect.appendChild(criarOpcaoSelectSessoesV6("legado", "Legado"));

    sistemaField.appendChild(sistemaLabel);
    sistemaField.appendChild(sistemaSelect);

    const estadoField = document.createElement("div");
    estadoField.className = "field appverbo-create-entry-field-v5";

    const estadoLabel = document.createElement("label");
    estadoLabel.textContent = "Estado *";

    const estadoSelect = document.createElement("select");
    estadoSelect.appendChild(criarOpcaoSelectSessoesV6("ativo", "Ativo"));
    estadoSelect.appendChild(criarOpcaoSelectSessoesV6("inativo", "Inativo"));

    estadoField.appendChild(estadoLabel);
    estadoField.appendChild(estadoSelect);

    grid.appendChild(nomeField);
    grid.appendChild(sistemaField);
    grid.appendChild(estadoField);

    const erro = document.createElement("p");
    erro.className = "appverbo-create-entry-error-v5";
    erro.hidden = true;

    const actions = document.createElement("div");
    actions.className = "appverbo-create-entry-actions-v5";

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

    function limparCriacao() {{
      nomeInput.value = "";
      sistemaSelect.value = "all";
      estadoSelect.value = "ativo";
      erro.hidden = true;
      erro.textContent = "";
      panel.hidden = true;
      abrirBtn.hidden = false;
    }}

    abrirBtn.addEventListener("click", function () {{
      erro.hidden = true;
      panel.hidden = false;
      abrirBtn.hidden = true;
      nomeInput.focus();
    }});

    cancelarBtn.addEventListener("click", limparCriacao);

    guardarBtn.addEventListener("click", function () {{
      const nomeSessao = String(nomeInput.value || "").trim();

      if (!nomeSessao) {{
        erro.textContent = "Informe o nome da sessão.";
        erro.hidden = false;
        nomeInput.focus();
        return;
      }}

      const novaSessao = {{
        label: nomeSessao,
        key: criarChaveSessoesV6(nomeSessao),
        visibility_scope_mode: sistemaSelect.value || "all",
        visibility_scope_label: obterLabelSistemaSessoesV6(sistemaSelect.value || "all", ""),
        status: normalizarEstadoSessoesV6(estadoSelect.value || "ativo"),
        is_active: normalizarEstadoSessoesV6(estadoSelect.value || "ativo") === "ativo"
      }};

      tbody.appendChild(criarLinhaSessoesV6(novaSessao));
      atualizarEstadoBotoesSessoesV6(tbody);
      limparCriacao();
      submeterFormularioSessoesV6(formulario);
    }});
  }}

  //###################################################################################
  // (5) INSTALAR REIDRATACAO
  //###################################################################################

  async function reidratarSessoesBdV6(force) {{
    const card = document.getElementById("admin-sidebar-sections-card");

    if (!card) {{
      return;
    }}

    const linhasAtuais = card.querySelectorAll("tr.appverbo-sidebar-section-row-v2, tr.appverbo-sidebar-section-row-v6");

    if (!force && linhasAtuais.length > 0 && card.dataset.rehydratedFromBdV6 === "1") {{
      return;
    }}

    const sessoesRaw = await carregarSessoesBdSessoesV6();
    const sessoes = sessoesRaw.map(normalizarSessaoSessoesV6).filter(Boolean);

    if (!sessoes.length) {{
      console.warn("APPVERBO V6: nenhuma sessão retornada do BD/template.");
      return;
    }}

    card.dataset.rehydratedFromBdV6 = "1";

    let formulario = card.querySelector('form[action*="/settings/menu/sidebar-sections"], form[action*="sidebar-sections"]');

    if (!formulario) {{
      formulario = document.createElement("form");
      card.appendChild(formulario);
    }}

    const tituloExistente = card.querySelector("h1, h2, h3");

    if (!tituloExistente) {{
      const titulo = document.createElement("h2");
      titulo.textContent = "Sessoes do sidebar";
      card.insertBefore(titulo, formulario);
    }}

    const tbody = criarTabelaSessoesV6(formulario, sessoes);
    instalarCriacaoSessoesV6(card, formulario, tbody);
  }}

  function iniciarReidratacaoSessoesV6() {{
    window.setTimeout(function () {{
      reidratarSessoesBdV6(false);
    }}, 300);

    window.setTimeout(function () {{
      const card = document.getElementById("admin-sidebar-sections-card");
      const linhas = card ? card.querySelectorAll("tr.appverbo-sidebar-section-row-v2, tr.appverbo-sidebar-section-row-v6") : [];

      if (!linhas || linhas.length === 0) {{
        reidratarSessoesBdV6(true);
      }}
    }}, 900);

    window.setTimeout(function () {{
      const card = document.getElementById("admin-sidebar-sections-card");
      const linhas = card ? card.querySelectorAll("tr.appverbo-sidebar-section-row-v2, tr.appverbo-sidebar-section-row-v6") : [];

      if (!linhas || linhas.length === 0) {{
        reidratarSessoesBdV6(true);
      }}
    }}, 1600);

    document.addEventListener("click", function () {{
      window.setTimeout(function () {{
        const card = document.getElementById("admin-sidebar-sections-card");
        const linhas = card ? card.querySelectorAll("tr.appverbo-sidebar-section-row-v2, tr.appverbo-sidebar-section-row-v6") : [];

        if (!linhas || linhas.length === 0) {{
          reidratarSessoesBdV6(true);
        }}
      }}, 120);
    }});
  }}

  if (document.readyState === "loading") {{
    document.addEventListener("DOMContentLoaded", iniciarReidratacaoSessoesV6);
  }} else {{
    iniciarReidratacaoSessoesV6();
  }}
}})();
{JS_MARKER_END}
'''

if JS_MARKER_START in js_content and JS_MARKER_END in js_content:
    js_pattern = re.compile(
        re.escape(JS_MARKER_START) + r"[\s\S]*?" + re.escape(JS_MARKER_END),
        re.S,
    )
    js_content = js_pattern.sub(repair_js, js_content, count=1)
else:
    js_content = js_content.rstrip() + "\n\n" + repair_js + "\n"

JS_PATH.write_text(js_content, encoding="utf-8")

print("OK: JS de reidratação da lista pelo BD criado/atualizado.")


####################################################################################
# (6) ADICIONAR CSS DE REIDRATACAO
####################################################################################

css_content = CSS_PATH.read_text(encoding="utf-8")

css_block = f'''{CSS_MARKER_START}

.appverbo-sidebar-sections-list-description-v6 {{
  margin: 0 0 12px;
  color: #52607a;
  font-size: 13px;
}}

.appverbo-sidebar-sections-table-v6 {{
  width: 100%;
}}

.appverbo-sidebar-section-row-v6 td {{
  height: 44px;
}}

.appverbo-sidebar-section-state-badge-inativo-v6 {{
  border-color: #f0c36d !important;
  background: #fff7e0 !important;
  color: #8a5a00 !important;
}}

.appverbo-create-entry-block-v6 {{
  width: 100%;
}}

.appverbo-create-entry-panel-v6[hidden] {{
  display: none !important;
}}

.appverbo-create-entry-grid-v6 {{
  display: grid;
  grid-template-columns: minmax(240px, 320px) minmax(220px, 260px) minmax(160px, 220px);
  gap: 12px;
  align-items: end;
  width: 100%;
}}

@media (max-width: 1100px) {{
  .appverbo-create-entry-grid-v6 {{
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

print("OK: CSS de reidratação V6 criado/atualizado.")


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
    fail_v6("não encontrei sidebar_sections_layout_v1.js no template.")

if "static/css/modules/sidebar_sections_layout_v1.css" in template_content:
    template_content = re.sub(
        r"/static/css/modules/sidebar_sections_layout_v1\.css\?v=[^\"]+",
        CSS_CACHE,
        template_content,
    )
else:
    fail_v6("não encontrei sidebar_sections_layout_v1.css no template.")

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
    "APPVERBO_SESSOES_REIDRATAR_BD_V6_START": agents_validado,
    "SIDEBAR_SECTIONS_DATA_ENDPOINT_V6": settings_validado,
    "/settings/menu/sidebar-sections-data": settings_validado,
    "get_sidebar_sections_data_v6": settings_validado,
    "APPVERBO_SESSOES_REIDRATAR_LISTA_BD_V6_START": js_validado,
    "reidratarSessoesBdV6": js_validado,
    "carregarSessoesBdSessoesV6": js_validado,
    "Criar sessão": js_validado,
    "Nome da sessão": js_validado,
    "Sistema": js_validado,
    "Estado": js_validado,
    "APPVERBO_SESSOES_REIDRATAR_LISTA_BD_V6_START": css_validado,
    "20260505-sessoes-reidratar-bd-v6": template_validado,
}

for termo, conteudo in validacoes.items():
    if termo not in conteudo:
        fail_v6(f"validação falhou, termo ausente: {termo}")

try:
    ast.parse(settings_validado)
except SyntaxError as exc:
    fail_v6(f"settings_handlers.py final inválido: {exc}")

print("OK: patch_sessoes_reidratar_lista_bd_v6 concluído.")
