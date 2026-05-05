from pathlib import Path
import ast
import json
import os
import re
import sys
import time

ROOT = Path.cwd()

AGENTS_UPPER_PATH = ROOT / "AGENTS.md"
AGENTS_TITLE_PATH = ROOT / "Agents.md"
TEMPLATE_PATH = ROOT / "templates" / "new_user.html"
MENU_SETTINGS_PATH = ROOT / "appverbo" / "menu_settings.py"
SETTINGS_HANDLERS_PATH = ROOT / "appverbo" / "routes" / "profile" / "settings_handlers.py"
JS_PATH = ROOT / "static" / "js" / "modules" / "sidebar_sections_layout_v1.js"
CSS_PATH = ROOT / "static" / "css" / "modules" / "sidebar_sections_layout_v1.css"

BACKUP_NAME = os.environ.get("APPVERBO_SESSOES_FIELDS_V5_BACKUP_NAME", "sessoes_campos_nome_sistema_estado_v5_manual")
BACKUP_ROOT = ROOT / "backups" / BACKUP_NAME
BACKUP_ROOT.mkdir(parents=True, exist_ok=True)

AGENTS_MARKER_START = "<!-- APPVERBO_SESSOES_CREATE_FIELDS_NOME_SISTEMA_ESTADO_V5_START -->"
AGENTS_MARKER_END = "<!-- APPVERBO_SESSOES_CREATE_FIELDS_NOME_SISTEMA_ESTADO_V5_END -->"

JS_MARKER_START = "// APPVERBO_SESSOES_CREATE_FIELDS_BD_V4_START"
JS_MARKER_END = "// APPVERBO_SESSOES_CREATE_FIELDS_BD_V4_END"

CSS_MARKER_START = "/* APPVERBO_SESSOES_CREATE_FIELDS_NOME_SISTEMA_ESTADO_V5_START */"
CSS_MARKER_END = "/* APPVERBO_SESSOES_CREATE_FIELDS_NOME_SISTEMA_ESTADO_V5_END */"

JS_CACHE = "/static/js/modules/sidebar_sections_layout_v1.js?v=20260505-sessoes-nome-sistema-estado-v5"
CSS_CACHE = "/static/css/modules/sidebar_sections_layout_v1.css?v=20260505-sessoes-nome-sistema-estado-v5"


def fail_v5(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


####################################################################################
# (1) RESOLVER AGENTS.md
####################################################################################

def resolve_agents_path_v5() -> Path:
    if AGENTS_UPPER_PATH.exists():
        return AGENTS_UPPER_PATH

    if AGENTS_TITLE_PATH.exists():
        return AGENTS_TITLE_PATH

    AGENTS_UPPER_PATH.write_text("# AGENTS.md\n\n", encoding="utf-8")
    return AGENTS_UPPER_PATH


####################################################################################
# (2) DIAGNOSTICAR CAMPOS EXISTENTES NO BD
####################################################################################

def parse_menu_config_v5(raw_config):
    if isinstance(raw_config, dict):
        return raw_config

    try:
        parsed = json.loads(raw_config or "{}")
    except Exception:
        parsed = {}

    return parsed if isinstance(parsed, dict) else {}


def diagnosticar_campos_bd_v5():
    report = {
        "timestamp": int(time.time()),
        "table": "sidebar_menu_settings",
        "menu_key": "administrativo",
        "db_available": False,
        "raw_sidebar_sections": [],
        "normalized_sidebar_sections": [],
        "detected_section_fields": [],
        "requested_create_fields": ["label", "visibility_scope_mode", "status"],
        "requested_create_labels": ["Nome da sessão", "Sistema", "Estado"],
        "notes": [],
    }

    try:
        sys.path.insert(0, str(ROOT))

        from sqlalchemy import text
        from appverbo.core import SessionLocal
        from appverbo.menu_settings import (
            MENU_CONFIG_SIDEBAR_SECTIONS_KEY,
            normalize_sidebar_sections,
        )

        with SessionLocal() as session:
            row = session.execute(
                text(
                    """
                    SELECT menu_key, menu_config
                    FROM sidebar_menu_settings
                    WHERE lower(trim(menu_key)) = :menu_key
                    LIMIT 1
                    """
                ),
                {"menu_key": "administrativo"},
            ).mappings().first()

            if row:
                menu_config = parse_menu_config_v5(row.get("menu_config"))
                raw_sections = menu_config.get(MENU_CONFIG_SIDEBAR_SECTIONS_KEY) or []
                normalized_sections = normalize_sidebar_sections(raw_sections)

                detected_fields = []
                detected_set = set()

                for section in normalized_sections:
                    if not isinstance(section, dict):
                        continue

                    for key in section.keys():
                        clean_key = str(key or "").strip()

                        if clean_key and clean_key not in detected_set:
                            detected_set.add(clean_key)
                            detected_fields.append(clean_key)

                report["db_available"] = True
                report["raw_sidebar_sections"] = raw_sections if isinstance(raw_sections, list) else []
                report["normalized_sidebar_sections"] = normalized_sections
                report["detected_section_fields"] = detected_fields
                report["notes"].append(
                    "O campo chave continua a existir no BD, mas passa a ser gerado automaticamente a partir do Nome da sessão."
                )
                report["notes"].append(
                    "O campo Sistema usa visibility_scope_mode/visibility_scope_label."
                )
                report["notes"].append(
                    "O campo Estado será persistido como status, is_active e status_label."
                )
            else:
                report["notes"].append("Menu administrativo não encontrado no BD.")

    except Exception as exc:
        report["notes"].append(f"Diagnóstico do BD não executado: {exc}")

    report_path = BACKUP_ROOT / "diagnostico_campos_sessoes_bd_v5.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )

    print("")
    print("===== DIAGNOSTICO CAMPOS SESSOES BD V5 =====")
    print(f"Relatório: {report_path}")
    print(f"BD disponível: {report['db_available']}")
    print("Campos detectados no BD/config:")
    for field in report["detected_section_fields"]:
        print(f" - {field}")
    print("Campos solicitados para Criar sessão:")
    for label in report["requested_create_labels"]:
        print(f" - {label}")
    print("===== FIM DIAGNOSTICO CAMPOS SESSOES BD V5 =====")
    print("")


diagnosticar_campos_bd_v5()


####################################################################################
# (3) ATUALIZAR AGENTS.md
####################################################################################

agents_path = resolve_agents_path_v5()
agents_content = agents_path.read_text(encoding="utf-8")

agents_rule = f"""{AGENTS_MARKER_START}
## Regra para criação de sessões do sidebar

Na aba **Sessões**, ao clicar em **Criar sessão**, os campos visíveis disponíveis para preenchimento devem ser exatamente:

1. **Nome da sessão**;
2. **Sistema**;
3. **Estado**.

A chave técnica da sessão deve continuar a existir para gravação no BD, mas deve ser gerada automaticamente a partir do Nome da sessão e não deve aparecer como campo visível no bloco de criação.

O campo **Sistema** deve gravar a visibilidade/sistema da sessão.

O campo **Estado** deve gravar se a sessão está ativa ou inativa.

Os botões **Guardar** e **Cancelar** devem existir apenas no bloco de criação, nunca no rodapé da listagem.
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

print(f"OK: regra de campos Nome/Sistema/Estado atualizada em {agents_path}")


####################################################################################
# (4) VALIDAR FICHEIROS
####################################################################################

for path in [TEMPLATE_PATH, MENU_SETTINGS_PATH, SETTINGS_HANDLERS_PATH, JS_PATH, CSS_PATH]:
    if not path.exists():
        fail_v5(f"ficheiro não encontrado: {path}")


####################################################################################
# (5) ATUALIZAR BACKEND: NORMALIZAR E PERSISTIR ESTADO DA SESSAO
####################################################################################

menu_settings = MENU_SETTINGS_PATH.read_text(encoding="utf-8")

status_helper = '''def _normalize_sidebar_section_status_v5(raw_status: Any) -> str:
    if isinstance(raw_status, bool):
        return "ativo" if raw_status else "inativo"

    clean_status = str(raw_status or "").strip().lower()

    if clean_status in {"inativo", "inactive", "0", "false", "no", "nao", "não", "off"}:
        return "inativo"

    return "ativo"


def _sidebar_section_status_label_v5(raw_status: Any) -> str:
    return "Inativo" if _normalize_sidebar_section_status_v5(raw_status) == "inativo" else "Ativo"


'''

if "_normalize_sidebar_section_status_v5" not in menu_settings:
    anchor = "def _build_sidebar_section_payload(\n"

    if anchor not in menu_settings:
        fail_v5("não encontrei _build_sidebar_section_payload em menu_settings.py.")

    menu_settings = menu_settings.replace(anchor, status_helper + anchor, 1)

old_signature = '''def _build_sidebar_section_payload(
    section_key: str,
    section_label: str,
    visibility_scopes: Any,
) -> dict[str, Any]:
    normalized_scopes = _normalize_sidebar_section_visibility_scopes(visibility_scopes)
    visibility_scope_mode = _resolve_visibility_scope_mode_from_scopes(normalized_scopes)
    return {
        "key": section_key,
        "label": section_label,
        "visibility_scopes": normalized_scopes,
        "visibility_scope_mode": visibility_scope_mode,
        "visibility_scope_label": _resolve_visibility_scope_label_from_mode(visibility_scope_mode),
    }
'''

new_signature = '''def _build_sidebar_section_payload(
    section_key: str,
    section_label: str,
    visibility_scopes: Any,
    status: Any = "ativo",
) -> dict[str, Any]:
    normalized_scopes = _normalize_sidebar_section_visibility_scopes(visibility_scopes)
    visibility_scope_mode = _resolve_visibility_scope_mode_from_scopes(normalized_scopes)
    normalized_status = _normalize_sidebar_section_status_v5(status)

    return {
        "key": section_key,
        "label": section_label,
        "visibility_scopes": normalized_scopes,
        "visibility_scope_mode": visibility_scope_mode,
        "visibility_scope_label": _resolve_visibility_scope_label_from_mode(visibility_scope_mode),
        "status": normalized_status,
        "is_active": normalized_status == "ativo",
        "status_label": _sidebar_section_status_label_v5(normalized_status),
    }
'''

if old_signature in menu_settings:
    menu_settings = menu_settings.replace(old_signature, new_signature, 1)
elif "status: Any = \"ativo\"" not in menu_settings:
    fail_v5("não consegui atualizar assinatura de _build_sidebar_section_payload.")

old_raw_dict_block = '''        if isinstance(raw_item, dict):
            clean_label = _normalize_sidebar_section_label(raw_item.get("label"))
            clean_key = _normalize_sidebar_section_key(raw_item.get("key"))
            clean_visibility_scopes = get_sidebar_section_visibility_scopes(raw_item)
        else:
            clean_label = _normalize_sidebar_section_label(raw_item)
            clean_key = ""
            clean_visibility_scopes = list(MENU_VISIBILITY_SCOPES)
'''

new_raw_dict_block = '''        if isinstance(raw_item, dict):
            clean_label = _normalize_sidebar_section_label(raw_item.get("label"))
            clean_key = _normalize_sidebar_section_key(raw_item.get("key"))
            clean_visibility_scopes = get_sidebar_section_visibility_scopes(raw_item)
            clean_status = raw_item.get("status", raw_item.get("is_active", "ativo"))
        else:
            clean_label = _normalize_sidebar_section_label(raw_item)
            clean_key = ""
            clean_visibility_scopes = list(MENU_VISIBILITY_SCOPES)
            clean_status = "ativo"
'''

if old_raw_dict_block in menu_settings:
    menu_settings = menu_settings.replace(old_raw_dict_block, new_raw_dict_block, 1)
elif "clean_status = raw_item.get(\"status\", raw_item.get(\"is_active\", \"ativo\"))" not in menu_settings:
    fail_v5("não consegui inserir clean_status na normalização de sessões.")

old_payload_call = '''        normalized_sections.append(
            _build_sidebar_section_payload(clean_key, clean_label, clean_visibility_scopes)
        )
'''

new_payload_call = '''        normalized_sections.append(
            _build_sidebar_section_payload(clean_key, clean_label, clean_visibility_scopes, clean_status)
        )
'''

if old_payload_call in menu_settings:
    menu_settings = menu_settings.replace(old_payload_call, new_payload_call, 1)
elif "_build_sidebar_section_payload(clean_key, clean_label, clean_visibility_scopes, clean_status)" not in menu_settings:
    fail_v5("não consegui atualizar chamada de _build_sidebar_section_payload com status.")

try:
    ast.parse(menu_settings)
except SyntaxError as exc:
    fail_v5(f"menu_settings.py ficaria inválido: {exc}")

MENU_SETTINGS_PATH.write_text(menu_settings, encoding="utf-8")

print("OK: menu_settings.py atualizado para persistir Estado da sessão.")


####################################################################################
# (6) ATUALIZAR ENDPOINT: RECEBER section_status
####################################################################################

settings_handlers = SETTINGS_HANDLERS_PATH.read_text(encoding="utf-8")

old_signature_line = '''    section_visibility_scope_mode: list[str] = Form(default=[]),
    redirect_menu: str = Form("administrativo"),
'''

new_signature_line = '''    section_visibility_scope_mode: list[str] = Form(default=[]),
    section_status: list[str] = Form(default=[]),
    redirect_menu: str = Form("administrativo"),
'''

if old_signature_line in settings_handlers:
    settings_handlers = settings_handlers.replace(old_signature_line, new_signature_line, 1)
elif "section_status: list[str] = Form(default=[])" not in settings_handlers:
    fail_v5("não consegui adicionar section_status ao endpoint.")

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

if old_rows_count in settings_handlers:
    settings_handlers = settings_handlers.replace(old_rows_count, new_rows_count, 1)
elif "len(section_status)" not in settings_handlers:
    fail_v5("não consegui adicionar section_status ao rows_count.")

old_payload_item = '''                    "visibility_scope_mode": (
                        section_visibility_scope_mode[row_index]
                        if row_index < len(section_visibility_scope_mode)
                        else ""
                    ),
'''

new_payload_item = '''                    "visibility_scope_mode": (
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

if old_payload_item in settings_handlers:
    settings_handlers = settings_handlers.replace(old_payload_item, new_payload_item, 1)
elif '"status": (' not in settings_handlers:
    fail_v5("não consegui adicionar status ao payload do endpoint.")

try:
    ast.parse(settings_handlers)
except SyntaxError as exc:
    fail_v5(f"settings_handlers.py ficaria inválido: {exc}")

SETTINGS_HANDLERS_PATH.write_text(settings_handlers, encoding="utf-8")

print("OK: settings_handlers.py atualizado para receber Estado da sessão.")


####################################################################################
# (7) ATUALIZAR JS: FORM COM NOME, SISTEMA E ESTADO
####################################################################################

js_content = JS_PATH.read_text(encoding="utf-8")

js_helper = f'''  {JS_MARKER_START}
  function obterLabelVisibilidadeSessoesCreate_v5(valor) {{
    const cleanValor = normalizarTextoSessoesLayout_v2(valor);

    if (cleanValor === "owner") {{
      return "Owner";
    }}

    if (cleanValor === "legado") {{
      return "Legado";
    }}

    return "Owner e Legado";
  }}

  function normalizarEstadoSessoesCreate_v5(valor) {{
    const cleanValor = normalizarTextoSessoesLayout_v2(valor);

    if (["inativo", "inactive", "0", "false", "nao", "não", "off"].includes(cleanValor)) {{
      return "inativo";
    }}

    return "ativo";
  }}

  function obterLabelEstadoSessoesCreate_v5(valor) {{
    return normalizarEstadoSessoesCreate_v5(valor) === "inativo" ? "Inativo" : "Ativo";
  }}

  function criarFieldCriacaoSessoes_v5(id, labelTexto, inputElement) {{
    const field = document.createElement("div");
    field.className = "field appverbo-create-entry-field-v5";

    const label = document.createElement("label");
    label.setAttribute("for", id);
    label.textContent = labelTexto;

    inputElement.id = id;

    field.appendChild(label);
    field.appendChild(inputElement);

    return field;
  }}

  function removerFooterListaSessoes_v5(wrapper) {{
    if (!wrapper) {{
      return;
    }}

    Array.from(wrapper.querySelectorAll(".appverbo-sidebar-sections-footer-v2")).forEach(function (footer) {{
      footer.remove();
    }});
  }}

  function criarChaveUnicaSessoesCreate_v5(tbody, nomeSessao, linhaAtual) {{
    const baseKey = criarChaveSessoesLayout_v2(nomeSessao) || "nova_sessao";
    const keysExistentes = new Set();

    Array.from(tbody.querySelectorAll("tr.appverbo-sidebar-section-row-v2")).forEach(function (linha) {{
      if (linha === linhaAtual) {{
        return;
      }}

      const keyInput = linha.querySelector('[name="section_key"]');
      const chave = String((keyInput && keyInput.value) || "").trim().toLowerCase();

      if (chave) {{
        keysExistentes.add(chave);
      }}
    }});

    if (!keysExistentes.has(baseKey)) {{
      return baseKey;
    }}

    let contador = 2;
    let chaveFinal = baseKey + "_" + contador;

    while (keysExistentes.has(chaveFinal)) {{
      contador += 1;
      chaveFinal = baseKey + "_" + contador;
    }}

    return chaveFinal;
  }}

  function aplicarFormularioCriacaoCompletoSessoes_v4(formulario, wrapper) {{
    if (!formulario || !wrapper || wrapper.dataset.createFieldsNomeSistemaEstadoV5 === "1") {{
      removerFooterListaSessoes_v5(wrapper);
      return;
    }}

    const tbody = wrapper.querySelector(".appverbo-sidebar-sections-body-v2");
    const createBlock = document.querySelector("#admin-sidebar-sections-create-card .appverbo-create-entry-block-v1") ||
      wrapper.querySelector(".appverbo-create-entry-block-v1");

    if (!tbody || !createBlock) {{
      removerFooterListaSessoes_v5(wrapper);
      return;
    }}

    wrapper.dataset.createFieldsNomeSistemaEstadoV5 = "1";
    removerFooterListaSessoes_v5(wrapper);

    const toolbar = createBlock.querySelector(".appverbo-create-entry-toolbar-v1") || document.createElement("div");
    toolbar.className = "appverbo-create-entry-toolbar-v1";

    let abrirBtnAtual = toolbar.querySelector(".appverbo-create-entry-open-btn-v1, .action-btn");

    if (!abrirBtnAtual) {{
      abrirBtnAtual = document.createElement("button");
      abrirBtnAtual.type = "button";
      toolbar.appendChild(abrirBtnAtual);
    }}

    const abrirBtn = abrirBtnAtual.cloneNode(true);
    abrirBtn.type = "button";
    abrirBtn.className = "action-btn appverbo-create-entry-open-btn-v1";
    abrirBtn.textContent = "Criar sessão";
    abrirBtnAtual.replaceWith(abrirBtn);

    let formPanel = createBlock.querySelector(".appverbo-create-entry-panel-v1");

    if (!formPanel) {{
      formPanel = document.createElement("div");
      formPanel.className = "appverbo-create-entry-panel-v1";
      createBlock.appendChild(formPanel);
    }}

    formPanel.innerHTML = "";
    formPanel.hidden = true;

    if (!toolbar.parentElement) {{
      createBlock.insertBefore(toolbar, createBlock.firstChild);
    }}

    const grid = document.createElement("div");
    grid.className = "appverbo-create-entry-grid-v5";

    const nomeInput = document.createElement("input");
    nomeInput.type = "text";
    nomeInput.maxLength = 80;
    nomeInput.placeholder = "Informe o nome da sessão";
    nomeInput.required = true;

    const sistemaSelect = document.createElement("select");
    sistemaSelect.required = true;

    [
      ["all", "Owner e Legado"],
      ["owner", "Owner"],
      ["legado", "Legado"]
    ].forEach(function (item) {{
      const option = document.createElement("option");
      option.value = item[0];
      option.textContent = item[1];
      sistemaSelect.appendChild(option);
    }});

    const estadoSelect = document.createElement("select");
    estadoSelect.required = true;

    [
      ["ativo", "Ativo"],
      ["inativo", "Inativo"]
    ].forEach(function (item) {{
      const option = document.createElement("option");
      option.value = item[0];
      option.textContent = item[1];
      estadoSelect.appendChild(option);
    }});

    grid.appendChild(criarFieldCriacaoSessoes_v5(
      "appverbo-create-entry-session-name-v5",
      "Nome da sessão *",
      nomeInput
    ));

    grid.appendChild(criarFieldCriacaoSessoes_v5(
      "appverbo-create-entry-session-system-v5",
      "Sistema *",
      sistemaSelect
    ));

    grid.appendChild(criarFieldCriacaoSessoes_v5(
      "appverbo-create-entry-session-status-v5",
      "Estado *",
      estadoSelect
    ));

    const error = document.createElement("p");
    error.className = "appverbo-create-entry-error-v5";
    error.hidden = true;

    const actions = document.createElement("div");
    actions.className = "appverbo-create-entry-actions-v5";

    const guardarBtn = document.createElement("button");
    guardarBtn.type = "button";
    guardarBtn.className = "action-btn appverbo-create-entry-save-btn-v5";
    guardarBtn.textContent = "Guardar";

    const cancelarBtn = document.createElement("button");
    cancelarBtn.type = "button";
    cancelarBtn.className = "action-btn-cancel appverbo-create-entry-cancel-btn-v5";
    cancelarBtn.textContent = "Cancelar";

    actions.appendChild(guardarBtn);
    actions.appendChild(cancelarBtn);

    formPanel.appendChild(grid);
    formPanel.appendChild(error);
    formPanel.appendChild(actions);

    function limparErros() {{
      error.hidden = true;
      error.textContent = "";
      nomeInput.classList.remove("appverbo-create-entry-input-error-v5");
      sistemaSelect.classList.remove("appverbo-create-entry-input-error-v5");
      estadoSelect.classList.remove("appverbo-create-entry-input-error-v5");
    }}

    function abrirFormulario() {{
      limparErros();
      formPanel.hidden = false;
      abrirBtn.hidden = true;
      nomeInput.focus();
    }}

    function fecharFormulario() {{
      nomeInput.value = "";
      sistemaSelect.value = "all";
      estadoSelect.value = "ativo";
      limparErros();
      formPanel.hidden = true;
      abrirBtn.hidden = false;
    }}

    function validarFormulario() {{
      limparErros();

      const nomeSessao = String(nomeInput.value || "").trim();
      const sistema = String(sistemaSelect.value || "all").trim();
      const estado = normalizarEstadoSessoesCreate_v5(estadoSelect.value);

      if (!nomeSessao) {{
        error.textContent = "Informe o nome da sessão.";
        error.hidden = false;
        nomeInput.classList.add("appverbo-create-entry-input-error-v5");
        nomeInput.focus();
        return null;
      }}

      if (!sistema) {{
        error.textContent = "Informe o sistema da sessão.";
        error.hidden = false;
        sistemaSelect.classList.add("appverbo-create-entry-input-error-v5");
        sistemaSelect.focus();
        return null;
      }}

      if (!estado) {{
        error.textContent = "Informe o estado da sessão.";
        error.hidden = false;
        estadoSelect.classList.add("appverbo-create-entry-input-error-v5");
        estadoSelect.focus();
        return null;
      }}

      return {{
        label: nomeSessao,
        key: criarChaveUnicaSessoesCreate_v5(tbody, nomeSessao, null),
        visibility_scope_mode: sistema,
        visibility_scope_label: obterLabelVisibilidadeSessoesCreate_v5(sistema),
        status: estado,
        is_active: estado === "ativo",
        status_label: obterLabelEstadoSessoesCreate_v5(estado)
      }};
    }}

    [nomeInput, sistemaSelect, estadoSelect].forEach(function (campo) {{
      campo.addEventListener("keydown", function (event) {{
        if (event.key === "Enter") {{
          event.preventDefault();
          guardarBtn.click();
        }}

        if (event.key === "Escape") {{
          event.preventDefault();
          cancelarBtn.click();
        }}
      }});
    }});

    abrirBtn.addEventListener("click", abrirFormulario);
    cancelarBtn.addEventListener("click", fecharFormulario);

    guardarBtn.addEventListener("click", function () {{
      const dados = validarFormulario();

      if (!dados) {{
        return;
      }}

      const novaLinha = criarLinhaTabelaSessoesLayout_v2(dados);
      tbody.appendChild(novaLinha.row);
      tbody.appendChild(novaLinha.detailRow);

      atualizarDetalheSessoesLayout_v2(novaLinha.row);
      atualizarEstadoBotoesSessoesLayout_v2(tbody);
      marcarAlteradoSessoesLayout_v2(formulario);

      fecharFormulario();

      if (typeof formulario.requestSubmit === "function") {{
        formulario.requestSubmit();
      }} else {{
        formulario.submit();
      }}
    }});
  }}
  {JS_MARKER_END}

'''

if JS_MARKER_START in js_content and JS_MARKER_END in js_content:
    js_pattern = re.compile(
        re.escape(JS_MARKER_START) + r"[\s\S]*?" + re.escape(JS_MARKER_END),
        re.S,
    )
    js_content = js_pattern.sub(js_helper.strip(), js_content, count=1)
else:
    install_anchor = "  //###################################################################################\n  // (6) INSTALAR LAYOUT\n  //###################################################################################\n\n"

    if install_anchor not in js_content:
        fail_v5("não encontrei âncora do bloco de instalação para inserir JS V5.")

    js_content = js_content.replace(install_anchor, js_helper + install_anchor, 1)

if "const statusInput = criarCampoOcultoSessoesLayout_v2(\"section_status\"" not in js_content:
    needle = '''    const keyInput = criarCampoOcultoSessoesLayout_v2("section_key", sessao.key);
    const scopeInput = criarCampoOcultoSessoesLayout_v2("section_visibility_scope_mode", sessao.visibility_scope_mode || "all");
'''

    replacement = '''    const keyInput = criarCampoOcultoSessoesLayout_v2("section_key", sessao.key);
    const scopeInput = criarCampoOcultoSessoesLayout_v2("section_visibility_scope_mode", sessao.visibility_scope_mode || "all");
    const statusInput = criarCampoOcultoSessoesLayout_v2("section_status", sessao.status || (sessao.is_active === false ? "inativo" : "ativo"));
'''

    if needle not in js_content:
        fail_v5("não encontrei local para criar statusInput.")

    js_content = js_content.replace(needle, replacement, 1)

if "tdMenu.appendChild(statusInput);" not in js_content:
    needle = '''    tdMenu.appendChild(labelInput);
    tdMenu.appendChild(keyInput);
    tdMenu.appendChild(scopeInput);
'''

    replacement = '''    tdMenu.appendChild(labelInput);
    tdMenu.appendChild(keyInput);
    tdMenu.appendChild(scopeInput);
    tdMenu.appendChild(statusInput);
'''

    if needle not in js_content:
        fail_v5("não encontrei local para anexar statusInput.")

    js_content = js_content.replace(needle, replacement, 1)

old_badge = '''    const badge = document.createElement("span");
    badge.className = "appverbo-sidebar-section-state-badge-v2";
    badge.textContent = "Ativo";
    tdEstado.appendChild(badge);
'''

new_badge = '''    const badge = document.createElement("span");
    const estadoSessao = normalizarEstadoSessoesCreate_v5(statusInput.value);
    badge.className = "appverbo-sidebar-section-state-badge-v2 appverbo-sidebar-section-state-badge-" + estadoSessao + "-v5";
    badge.textContent = obterLabelEstadoSessoesCreate_v5(estadoSessao);
    tdEstado.appendChild(badge);
'''

if old_badge in js_content:
    js_content = js_content.replace(old_badge, new_badge, 1)
elif "appverbo-sidebar-section-state-badge-inativo-v5" not in js_content:
    print("AVISO: bloco badge antigo não encontrado; pode já estar atualizado.")

if "removerFooterListaSessoes_v5(wrapper);" not in js_content:
    call_candidates = [
        '''    moverBlocoCriacaoParaCardSeparadoSessoes_v3(cardListaSessoesV3, wrapper);
    aplicarFormularioCriacaoCompletoSessoes_v4(formulario, wrapper);
    removerFooterListaSessoes_v4(wrapper);

    return wrapper;
''',
        '''    moverBlocoCriacaoParaCardSeparadoSessoes_v3(cardListaSessoesV3, wrapper);
    aplicarFormularioCriacaoCompletoSessoes_v4(formulario, wrapper);

    return wrapper;
''',
    ]

    replacement_call = '''    moverBlocoCriacaoParaCardSeparadoSessoes_v3(cardListaSessoesV3, wrapper);
    aplicarFormularioCriacaoCompletoSessoes_v4(formulario, wrapper);
    removerFooterListaSessoes_v5(wrapper);

    return wrapper;
'''

    replaced_call = False

    for candidate in call_candidates:
        if candidate in js_content:
            js_content = js_content.replace(candidate, replacement_call, 1)
            replaced_call = True
            break

    if not replaced_call:
        print("AVISO: chamada removerFooterListaSessoes_v5 não inserida; validando se já existe equivalente.")

JS_PATH.write_text(js_content, encoding="utf-8")

print("OK: JS atualizado para campos Nome da sessão, Sistema e Estado.")


####################################################################################
# (8) ATUALIZAR CSS
####################################################################################

css_content = CSS_PATH.read_text(encoding="utf-8")

css_block = f'''{CSS_MARKER_START}

.appverbo-sidebar-sections-card-v2 .appverbo-sidebar-sections-footer-v2 {{
  display: none !important;
}}

.appverbo-create-entry-grid-v5 {{
  display: grid;
  grid-template-columns: minmax(240px, 320px) minmax(220px, 260px) minmax(160px, 220px);
  gap: 12px;
  align-items: end;
  width: 100%;
}}

.appverbo-create-entry-field-v5 label {{
  display: block;
  margin-bottom: 6px;
  color: #243557;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
}}

.appverbo-create-entry-field-v5 input,
.appverbo-create-entry-field-v5 select {{
  width: 100%;
  border: 1px solid #c6d0e2;
  border-radius: 7px;
  background: #ffffff;
  color: #12213a;
  min-height: 38px;
  padding: 8px 10px;
  box-sizing: border-box;
}}

.appverbo-create-entry-field-v5 input:focus,
.appverbo-create-entry-field-v5 select:focus {{
  border-color: #2454b0;
  outline: none;
  box-shadow: 0 0 0 2px rgba(36, 84, 176, 0.12);
}}

.appverbo-create-entry-input-error-v5 {{
  border-color: #d93025 !important;
}}

.appverbo-create-entry-error-v5 {{
  margin: 10px 0 0;
  color: #b42318;
  font-size: 12px;
}}

.appverbo-create-entry-actions-v5 {{
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 8px;
  margin-top: 12px;
}}

.appverbo-create-entry-actions-v5 .action-btn,
.appverbo-create-entry-actions-v5 .action-btn-cancel {{
  min-width: 112px !important;
  width: 112px !important;
  height: 38px !important;
  min-height: 38px !important;
}}

.appverbo-sidebar-section-state-badge-inativo-v5 {{
  border-color: #f0c36d !important;
  background: #fff7e0 !important;
  color: #8a5a00 !important;
}}

@media (max-width: 1100px) {{
  .appverbo-create-entry-grid-v5 {{
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

print("OK: CSS atualizado para Nome/Sistema/Estado e remoção do rodapé inferior.")


####################################################################################
# (9) ATUALIZAR CACHE BUSTER
####################################################################################

template_content = TEMPLATE_PATH.read_text(encoding="utf-8")

if "static/js/modules/sidebar_sections_layout_v1.js" in template_content:
    template_content = re.sub(
        r"/static/js/modules/sidebar_sections_layout_v1\.js\?v=[^\"]+",
        JS_CACHE,
        template_content,
    )
else:
    fail_v5("não encontrei JS sidebar_sections_layout_v1 no template.")

if "static/css/modules/sidebar_sections_layout_v1.css" in template_content:
    template_content = re.sub(
        r"/static/css/modules/sidebar_sections_layout_v1\.css\?v=[^\"]+",
        CSS_CACHE,
        template_content,
    )
else:
    fail_v5("não encontrei CSS sidebar_sections_layout_v1 no template.")

TEMPLATE_PATH.write_text(template_content, encoding="utf-8")

print("OK: cache buster atualizado.")


####################################################################################
# (10) VALIDAR CONTEUDO
####################################################################################

agents_validado = agents_path.read_text(encoding="utf-8")
menu_settings_validado = MENU_SETTINGS_PATH.read_text(encoding="utf-8")
settings_handlers_validado = SETTINGS_HANDLERS_PATH.read_text(encoding="utf-8")
js_validado = JS_PATH.read_text(encoding="utf-8")
css_validado = CSS_PATH.read_text(encoding="utf-8")
template_validado = TEMPLATE_PATH.read_text(encoding="utf-8")

validacoes = {
    "APPVERBO_SESSOES_CREATE_FIELDS_NOME_SISTEMA_ESTADO_V5_START": agents_validado,
    "Nome da sessão": agents_validado,
    "Sistema": agents_validado,
    "Estado": agents_validado,
    "_normalize_sidebar_section_status_v5": menu_settings_validado,
    '"status": normalized_status': menu_settings_validado,
    '"is_active": normalized_status == "ativo"': menu_settings_validado,
    "section_status: list[str] = Form(default=[])": settings_handlers_validado,
    '"status": (': settings_handlers_validado,
    "normalizarEstadoSessoesCreate_v5": js_validado,
    "Nome da sessão *": js_validado,
    "Sistema *": js_validado,
    "Estado *": js_validado,
    "section_status": js_validado,
    "APPVERBO_SESSOES_CREATE_FIELDS_NOME_SISTEMA_ESTADO_V5_START": css_validado,
    ".appverbo-sidebar-sections-footer-v2": css_validado,
    "20260505-sessoes-nome-sistema-estado-v5": template_validado,
}

for termo, conteudo in validacoes.items():
    if termo not in conteudo:
        fail_v5(f"validação falhou, termo ausente: {termo}")

try:
    ast.parse(menu_settings_validado)
    ast.parse(settings_handlers_validado)
except SyntaxError as exc:
    fail_v5(f"Python final inválido: {exc}")

print("OK: patch_sessoes_nome_sistema_estado_v5 concluído.")
