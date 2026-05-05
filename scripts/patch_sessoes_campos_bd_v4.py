from pathlib import Path
import json
import os
import re
import sys
import time

ROOT = Path.cwd()

AGENTS_UPPER_PATH = ROOT / "AGENTS.md"
AGENTS_TITLE_PATH = ROOT / "Agents.md"
TEMPLATE_PATH = ROOT / "templates" / "new_user.html"
JS_PATH = ROOT / "static" / "js" / "modules" / "sidebar_sections_layout_v1.js"
CSS_PATH = ROOT / "static" / "css" / "modules" / "sidebar_sections_layout_v1.css"
NEW_USER_CSS_PATH = ROOT / "static" / "css" / "new_user.css"

BACKUP_NAME = os.environ.get("APPVERBO_SESSOES_BD_FIELDS_BACKUP_NAME", "sessoes_campos_bd_v4_manual")
BACKUP_ROOT = ROOT / "backups" / BACKUP_NAME
BACKUP_ROOT.mkdir(parents=True, exist_ok=True)

AGENTS_MARKER_START = "<!-- APPVERBO_SESSOES_DB_FIELDS_CREATE_RULE_V4_START -->"
AGENTS_MARKER_END = "<!-- APPVERBO_SESSOES_DB_FIELDS_CREATE_RULE_V4_END -->"

JS_MARKER_START = "// APPVERBO_SESSOES_CREATE_FIELDS_BD_V4_START"
JS_MARKER_END = "// APPVERBO_SESSOES_CREATE_FIELDS_BD_V4_END"

CSS_MARKER_START = "/* APPVERBO_SESSOES_CREATE_FIELDS_BD_V4_START */"
CSS_MARKER_END = "/* APPVERBO_SESSOES_CREATE_FIELDS_BD_V4_END */"

JS_CACHE = "/static/js/modules/sidebar_sections_layout_v1.js?v=20260505-sessoes-campos-bd-v4"
CSS_CACHE = "/static/css/modules/sidebar_sections_layout_v1.css?v=20260505-sessoes-campos-bd-v4"
NEW_USER_CSS_CACHE = "/static/css/new_user.css?v=20260505-sessoes-campos-bd-v4"


def fail_v4(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


####################################################################################
# (1) RESOLVER AGENTS.md
####################################################################################

def resolve_agents_path_v4() -> Path:
    if AGENTS_UPPER_PATH.exists():
        return AGENTS_UPPER_PATH

    if AGENTS_TITLE_PATH.exists():
        return AGENTS_TITLE_PATH

    AGENTS_UPPER_PATH.write_text("# AGENTS.md\n\n", encoding="utf-8")
    return AGENTS_UPPER_PATH


####################################################################################
# (2) DIAGNOSTICAR CAMPOS NO BD
####################################################################################

def parse_menu_config_v4(raw_config):
    if isinstance(raw_config, dict):
        return raw_config

    try:
        parsed = json.loads(raw_config or "{}")
    except Exception:
        parsed = {}

    return parsed if isinstance(parsed, dict) else {}


def diagnosticar_campos_bd_v4():
    report = {
        "timestamp": int(time.time()),
        "table": "sidebar_menu_settings",
        "menu_key": "administrativo",
        "db_available": False,
        "raw_sidebar_sections": [],
        "normalized_sidebar_sections": [],
        "detected_section_fields": [],
        "fields_used_in_create_form": [
            {
                "field": "label",
                "label": "Nome da sessão",
                "required": True,
                "input": "text",
            },
            {
                "field": "key",
                "label": "Chave da sessão",
                "required": True,
                "input": "text",
            },
            {
                "field": "visibility_scope_mode",
                "label": "Visibilidade",
                "required": True,
                "input": "select",
                "options": ["all", "owner", "legado"],
            },
        ],
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
                menu_config = parse_menu_config_v4(row.get("menu_config"))
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

                if detected_fields:
                    report["notes"].append(
                        "Os campos existentes no BD/config normalizada foram usados como referência para o formulário de criação."
                    )
                else:
                    report["notes"].append(
                        "Nenhum campo foi detectado no BD; foram usados os campos mínimos label, key e visibility_scope_mode."
                    )
            else:
                report["notes"].append("Menu administrativo não encontrado no BD.")

    except Exception as exc:
        report["notes"].append(f"Diagnóstico do BD não executado: {exc}")

    report_path = BACKUP_ROOT / "diagnostico_campos_sessoes_bd_v4.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )

    print("")
    print("===== DIAGNOSTICO CAMPOS SESSOES BD V4 =====")
    print(f"Relatório: {report_path}")
    print(f"BD disponível: {report['db_available']}")
    print("Campos detectados:")
    for field in report["detected_section_fields"]:
        print(f" - {field}")
    print("Campos usados no formulário Criar sessão:")
    for item in report["fields_used_in_create_form"]:
        print(f" - {item.get('field')} | {item.get('label')} | obrigatório={item.get('required')}")
    print("===== FIM DIAGNOSTICO CAMPOS SESSOES BD V4 =====")
    print("")

    return report


diagnosticar_campos_bd_v4()


####################################################################################
# (3) ATUALIZAR AGENTS.md
####################################################################################

agents_path = resolve_agents_path_v4()
agents_content = agents_path.read_text(encoding="utf-8")

agents_rule = f"""{AGENTS_MARKER_START}
## Regra para campos de criação baseados na edição/BD

Sempre que existir um botão **Criar + nome da aba/processo**:

1. Os botões **Guardar** e **Cancelar** devem existir apenas dentro do bloco/card de criação.
2. Não deve existir outro par **Guardar/Cancelar** no rodapé da tabela/lista para a mesma ação de criação.
3. Ao clicar em **Criar + nome**, devem aparecer todos os campos necessários que existem na edição ou na configuração persistida no BD.
4. Para sessões do sidebar, o formulário de criação deve permitir preencher:
   - Nome da sessão;
   - Chave da sessão;
   - Visibilidade/Sistema.
5. Campos derivados podem ser gravados como hidden, mas os campos editáveis principais devem estar visíveis no bloco de criação.
6. A tabela/lista inferior deve ficar apenas com a listagem e ações por linha.
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

print(f"OK: regra de campos de criação atualizada em {agents_path}")


####################################################################################
# (4) VALIDAR FICHEIROS
####################################################################################

if not TEMPLATE_PATH.exists():
    fail_v4(f"template não encontrado: {TEMPLATE_PATH}")

if not JS_PATH.exists():
    fail_v4(f"JS não encontrado: {JS_PATH}")

if not CSS_PATH.exists():
    fail_v4(f"CSS não encontrado: {CSS_PATH}")


####################################################################################
# (5) INSERIR JS V4: REMOVER RODAPE E CRIAR FORM COMPLETO
####################################################################################

js_content = JS_PATH.read_text(encoding="utf-8")

js_helper = f'''  {JS_MARKER_START}
  function obterLabelVisibilidadeSessoesCreate_v4(valor) {{
    const cleanValor = normalizarTextoSessoesLayout_v2(valor);

    if (cleanValor === "owner") {{
      return "Owner";
    }}

    if (cleanValor === "legado") {{
      return "Legado";
    }}

    return "Owner e Legado";
  }}

  function criarFieldCriacaoSessoes_v4(id, labelTexto, inputElement) {{
    const field = document.createElement("div");
    field.className = "field appverbo-create-entry-field-v4";

    const label = document.createElement("label");
    label.setAttribute("for", id);
    label.textContent = labelTexto;

    inputElement.id = id;

    field.appendChild(label);
    field.appendChild(inputElement);

    return field;
  }}

  function removerFooterListaSessoes_v4(wrapper) {{
    if (!wrapper) {{
      return;
    }}

    Array.from(wrapper.querySelectorAll(".appverbo-sidebar-sections-footer-v2")).forEach(function (footer) {{
      footer.remove();
    }});
  }}

  function criarChaveUnicaSessoesCreate_v4(tbody, nomeSessao, linhaAtual) {{
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
    if (!formulario || !wrapper || wrapper.dataset.createFieldsBdV4 === "1") {{
      removerFooterListaSessoes_v4(wrapper);
      return;
    }}

    const tbody = wrapper.querySelector(".appverbo-sidebar-sections-body-v2");
    const createBlock = document.querySelector("#admin-sidebar-sections-create-card .appverbo-create-entry-block-v1") ||
      wrapper.querySelector(".appverbo-create-entry-block-v1");

    if (!tbody || !createBlock) {{
      removerFooterListaSessoes_v4(wrapper);
      return;
    }}

    wrapper.dataset.createFieldsBdV4 = "1";
    removerFooterListaSessoes_v4(wrapper);

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
    grid.className = "appverbo-create-entry-grid-v4";

    const nomeInput = document.createElement("input");
    nomeInput.type = "text";
    nomeInput.maxLength = 80;
    nomeInput.placeholder = "Informe o nome da sessão";
    nomeInput.required = true;

    const chaveInput = document.createElement("input");
    chaveInput.type = "text";
    chaveInput.maxLength = 80;
    chaveInput.placeholder = "exemplo: nova_sessao";
    chaveInput.required = true;

    const visibilidadeSelect = document.createElement("select");
    visibilidadeSelect.required = true;

    [
      ["all", "Owner e Legado"],
      ["owner", "Owner"],
      ["legado", "Legado"]
    ].forEach(function (item) {{
      const option = document.createElement("option");
      option.value = item[0];
      option.textContent = item[1];
      visibilidadeSelect.appendChild(option);
    }});

    grid.appendChild(criarFieldCriacaoSessoes_v4(
      "appverbo-create-entry-session-name-v4",
      "Nome da sessão *",
      nomeInput
    ));

    grid.appendChild(criarFieldCriacaoSessoes_v4(
      "appverbo-create-entry-session-key-v4",
      "Chave da sessão *",
      chaveInput
    ));

    grid.appendChild(criarFieldCriacaoSessoes_v4(
      "appverbo-create-entry-session-visibility-v4",
      "Visibilidade *",
      visibilidadeSelect
    ));

    const error = document.createElement("p");
    error.className = "appverbo-create-entry-error-v4";
    error.hidden = true;

    const actions = document.createElement("div");
    actions.className = "appverbo-create-entry-actions-v4";

    const guardarBtn = document.createElement("button");
    guardarBtn.type = "button";
    guardarBtn.className = "action-btn appverbo-create-entry-save-btn-v4";
    guardarBtn.textContent = "Guardar";

    const cancelarBtn = document.createElement("button");
    cancelarBtn.type = "button";
    cancelarBtn.className = "action-btn-cancel appverbo-create-entry-cancel-btn-v4";
    cancelarBtn.textContent = "Cancelar";

    actions.appendChild(guardarBtn);
    actions.appendChild(cancelarBtn);

    formPanel.appendChild(grid);
    formPanel.appendChild(error);
    formPanel.appendChild(actions);

    function limparErros() {{
      error.hidden = true;
      error.textContent = "";
      nomeInput.classList.remove("appverbo-create-entry-input-error-v4");
      chaveInput.classList.remove("appverbo-create-entry-input-error-v4");
      visibilidadeSelect.classList.remove("appverbo-create-entry-input-error-v4");
    }}

    function abrirFormulario() {{
      limparErros();
      formPanel.hidden = false;
      abrirBtn.hidden = true;

      if (!chaveInput.value) {{
        chaveInput.value = criarChaveSessoesLayout_v2(nomeInput.value);
      }}

      nomeInput.focus();
    }}

    function fecharFormulario() {{
      nomeInput.value = "";
      chaveInput.value = "";
      visibilidadeSelect.value = "all";
      limparErros();
      formPanel.hidden = true;
      abrirBtn.hidden = false;
    }}

    function validarFormulario() {{
      limparErros();

      const nomeSessao = String(nomeInput.value || "").trim();
      const chaveSessao = criarChaveSessoesLayout_v2(chaveInput.value || nomeSessao);
      const visibilidade = String(visibilidadeSelect.value || "all").trim();

      if (!nomeSessao) {{
        error.textContent = "Informe o nome da sessão.";
        error.hidden = false;
        nomeInput.classList.add("appverbo-create-entry-input-error-v4");
        nomeInput.focus();
        return null;
      }}

      if (!chaveSessao) {{
        error.textContent = "Informe a chave da sessão.";
        error.hidden = false;
        chaveInput.classList.add("appverbo-create-entry-input-error-v4");
        chaveInput.focus();
        return null;
      }}

      if (!visibilidade) {{
        error.textContent = "Informe a visibilidade da sessão.";
        error.hidden = false;
        visibilidadeSelect.classList.add("appverbo-create-entry-input-error-v4");
        visibilidadeSelect.focus();
        return null;
      }}

      return {{
        label: nomeSessao,
        key: criarChaveUnicaSessoesCreate_v4(tbody, chaveSessao, null),
        visibility_scope_mode: visibilidade,
        visibility_scope_label: obterLabelVisibilidadeSessoesCreate_v4(visibilidade)
      }};
    }}

    nomeInput.addEventListener("input", function () {{
      if (!chaveInput.dataset.manualV4) {{
        chaveInput.value = criarChaveSessoesLayout_v2(nomeInput.value);
      }}
    }});

    chaveInput.addEventListener("input", function () {{
      chaveInput.dataset.manualV4 = "1";
      chaveInput.value = criarChaveSessoesLayout_v2(chaveInput.value);
    }});

    [nomeInput, chaveInput, visibilidadeSelect].forEach(function (campo) {{
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
        fail_v4("não encontrei âncora do bloco de instalação para inserir JS V4.")

    js_content = js_content.replace(install_anchor, js_helper + install_anchor, 1)

call_candidates = [
    '''    const cardListaSessoesV3 = formulario.closest(".card, section");
    moverBlocoCriacaoParaCardSeparadoSessoes_v3(cardListaSessoesV3, wrapper);

    return wrapper;
''',
    '''    aplicarBlocoCriacaoSessoes_v1(formulario, wrapper);

    return wrapper;
''',
]

call_replacement = '''    const cardListaSessoesV3 = formulario.closest(".card, section");
    moverBlocoCriacaoParaCardSeparadoSessoes_v3(cardListaSessoesV3, wrapper);
    aplicarFormularioCriacaoCompletoSessoes_v4(formulario, wrapper);
    removerFooterListaSessoes_v4(wrapper);

    return wrapper;
'''

replaced_call = False

for candidate in call_candidates:
    if candidate in js_content:
        js_content = js_content.replace(candidate, call_replacement, 1)
        replaced_call = True
        break

if not replaced_call and "aplicarFormularioCriacaoCompletoSessoes_v4(formulario, wrapper);" not in js_content:
    fail_v4("não encontrei local para chamar aplicarFormularioCriacaoCompletoSessoes_v4.")

JS_PATH.write_text(js_content, encoding="utf-8")

print("OK: JS atualizado para remover rodapé inferior e criar formulário completo.")


####################################################################################
# (6) CSS: OCULTAR RODAPE INFERIOR E PADRONIZAR CAMPOS
####################################################################################

css_content = CSS_PATH.read_text(encoding="utf-8")

css_block = f'''{CSS_MARKER_START}

.appverbo-sidebar-sections-card-v2 .appverbo-sidebar-sections-footer-v2 {{
  display: none !important;
}}

.appverbo-create-entry-grid-v4 {{
  display: grid;
  grid-template-columns: minmax(220px, 320px) minmax(220px, 320px) minmax(180px, 240px);
  gap: 12px;
  align-items: end;
  width: 100%;
}}

.appverbo-create-entry-field-v4 label {{
  display: block;
  margin-bottom: 6px;
  color: #243557;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
}}

.appverbo-create-entry-field-v4 input,
.appverbo-create-entry-field-v4 select {{
  width: 100%;
  border: 1px solid #c6d0e2;
  border-radius: 7px;
  background: #ffffff;
  color: #12213a;
  min-height: 38px;
  padding: 8px 10px;
  box-sizing: border-box;
}}

.appverbo-create-entry-field-v4 input:focus,
.appverbo-create-entry-field-v4 select:focus {{
  border-color: #2454b0;
  outline: none;
  box-shadow: 0 0 0 2px rgba(36, 84, 176, 0.12);
}}

.appverbo-create-entry-input-error-v4 {{
  border-color: #d93025 !important;
}}

.appverbo-create-entry-error-v4 {{
  margin: 10px 0 0;
  color: #b42318;
  font-size: 12px;
}}

.appverbo-create-entry-actions-v4 {{
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 8px;
  margin-top: 12px;
}}

.appverbo-create-entry-actions-v4 .action-btn,
.appverbo-create-entry-actions-v4 .action-btn-cancel {{
  min-width: 112px !important;
  width: 112px !important;
  height: 38px !important;
  min-height: 38px !important;
}}

@media (max-width: 1100px) {{
  .appverbo-create-entry-grid-v4 {{
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

print("OK: CSS atualizado para remover botões inferiores e exibir campos completos.")


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
    fail_v4("não encontrei JS sidebar_sections_layout_v1 no template.")

if "static/css/modules/sidebar_sections_layout_v1.css" in template_content:
    template_content = re.sub(
        r"/static/css/modules/sidebar_sections_layout_v1\.css\?v=[^\"]+",
        CSS_CACHE,
        template_content,
    )
else:
    fail_v4("não encontrei CSS sidebar_sections_layout_v1 no template.")

if "static/css/new_user.css" in template_content:
    template_content = re.sub(
        r"/static/css/new_user\.css\?v=[^\"]+",
        NEW_USER_CSS_CACHE,
        template_content,
    )

TEMPLATE_PATH.write_text(template_content, encoding="utf-8")

print("OK: cache buster atualizado.")


####################################################################################
# (8) VALIDAR CONTEUDO
####################################################################################

agents_validado = agents_path.read_text(encoding="utf-8")
js_validado = JS_PATH.read_text(encoding="utf-8")
css_validado = CSS_PATH.read_text(encoding="utf-8")
template_validado = TEMPLATE_PATH.read_text(encoding="utf-8")

validacoes = {
    "APPVERBO_SESSOES_DB_FIELDS_CREATE_RULE_V4_START": agents_validado,
    "Nome da sessão": agents_validado,
    "Chave da sessão": agents_validado,
    "Visibilidade/Sistema": agents_validado,
    "APPVERBO_SESSOES_CREATE_FIELDS_BD_V4_START": js_validado,
    "aplicarFormularioCriacaoCompletoSessoes_v4": js_validado,
    "Nome da sessão *": js_validado,
    "Chave da sessão *": js_validado,
    "Visibilidade *": js_validado,
    "removerFooterListaSessoes_v4": js_validado,
    "APPVERBO_SESSOES_CREATE_FIELDS_BD_V4_START": css_validado,
    ".appverbo-sidebar-sections-footer-v2": css_validado,
    "display: none !important": css_validado,
    "20260505-sessoes-campos-bd-v4": template_validado,
}

for termo, conteudo in validacoes.items():
    if termo not in conteudo:
        fail_v4(f"validação falhou, termo ausente: {termo}")

print("OK: patch_sessoes_campos_bd_v4 concluído.")
