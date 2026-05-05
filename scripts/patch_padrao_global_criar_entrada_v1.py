from pathlib import Path
import re
import sys

ROOT = Path.cwd()

AGENTS_UPPER_PATH = ROOT / "AGENTS.md"
AGENTS_TITLE_PATH = ROOT / "Agents.md"
TEMPLATE_PATH = ROOT / "templates" / "new_user.html"
JS_PATH = ROOT / "static" / "js" / "modules" / "sidebar_sections_layout_v1.js"
CSS_PATH = ROOT / "static" / "css" / "modules" / "sidebar_sections_layout_v1.css"
NEW_USER_CSS_PATH = ROOT / "static" / "css" / "new_user.css"

AGENTS_MARKER_START = "<!-- APPVERBO_CREATE_ENTRY_BLOCK_RULE_V1_START -->"
AGENTS_MARKER_END = "<!-- APPVERBO_CREATE_ENTRY_BLOCK_RULE_V1_END -->"

JS_MARKER_START = "// APPVERBO_CREATE_ENTRY_BLOCK_SESSOES_V1_START"
JS_MARKER_END = "// APPVERBO_CREATE_ENTRY_BLOCK_SESSOES_V1_END"

CSS_MARKER_START = "/* APPVERBO_CREATE_ENTRY_BLOCK_STANDARD_V1_START */"
CSS_MARKER_END = "/* APPVERBO_CREATE_ENTRY_BLOCK_STANDARD_V1_END */"

JS_CACHE = "/static/js/modules/sidebar_sections_layout_v1.js?v=20260505-create-entry-block-v1"
CSS_CACHE = "/static/css/modules/sidebar_sections_layout_v1.css?v=20260505-create-entry-block-v1"
NEW_USER_CSS_CACHE = "/static/css/new_user.css?v=20260505-create-entry-block-v1"


def fail_v1(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


####################################################################################
# (1) RESOLVER AGENTS.md
####################################################################################

def resolve_agents_path_v1() -> Path:
    if AGENTS_UPPER_PATH.exists():
        return AGENTS_UPPER_PATH

    if AGENTS_TITLE_PATH.exists():
        return AGENTS_TITLE_PATH

    AGENTS_UPPER_PATH.write_text("# AGENTS.md\n\n", encoding="utf-8")
    return AGENTS_UPPER_PATH


####################################################################################
# (2) ATUALIZAR AGENTS.md COM REGRA GLOBAL
####################################################################################

agents_path = resolve_agents_path_v1()
agents_content = agents_path.read_text(encoding="utf-8")

agents_rule = f"""{AGENTS_MARKER_START}
## Regra global para criação de entradas em abas/subprocessos

Sempre que uma aba, subprocesso ou lista administrativa tiver a opção de criar uma nova entrada relacionada ao processo atual:

1. Deve existir um bloco separado acima da tabela/lista principal.
2. Dentro desse bloco, o botão inicial deve ficar no lado esquerdo e seguir o padrão: **Criar + nome da aba/processo**.
   - Exemplos: **Criar entidade**, **Criar utilizador**, **Criar sessão**, **Criar menu**.
3. O botão de criação não deve ficar no lado direito do cabeçalho da tabela/lista.
4. Ao clicar em **Criar + nome**, o bloco deve expandir/apresentar os campos necessários para preencher a nova entrada.
5. Os botões **Guardar** e **Cancelar** devem ficar dentro desse mesmo bloco de criação.
6. Os botões **Guardar** e **Cancelar** devem ficar sempre alinhados à esquerda, com o mesmo tamanho e dimensão em todo o projeto.
7. A ordem visual deve ser sempre: **Guardar** primeiro e **Cancelar** depois.
8. A tabela/lista inferior deve permanecer separada, exibindo apenas os registos já criados e as ações de cada registo.
9. Quando a entrada for cancelada, limpar os campos do bloco e fechar/ocultar a área de preenchimento.
10. Quando a entrada for guardada, validar os campos obrigatórios antes de inserir/gravar.
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

print(f"OK: regra global de criação atualizada em {agents_path}")


####################################################################################
# (3) VALIDAR FICHEIROS DA TELA SESSÕES
####################################################################################

if not TEMPLATE_PATH.exists():
    fail_v1(f"ficheiro não encontrado: {TEMPLATE_PATH}")

if not JS_PATH.exists():
    fail_v1(f"ficheiro não encontrado: {JS_PATH}")

if not CSS_PATH.exists():
    fail_v1(f"ficheiro não encontrado: {CSS_PATH}")


####################################################################################
# (4) APLICAR BLOCO CRIAR SESSÃO NO JS
####################################################################################

js_content = JS_PATH.read_text(encoding="utf-8")

js_content = js_content.replace(
    'criarBtn.textContent = "Criar pasta";',
    'criarBtn.textContent = "Criar sessão";',
)

create_entry_helper = f'''  {JS_MARKER_START}
  function criarChaveUnicaSessoesCreateBlock_v1(tbody, nomeSessao, linhaAtual) {{
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

  function aplicarBlocoCriacaoSessoes_v1(formulario, wrapper) {{
    if (!formulario || !wrapper || wrapper.dataset.createEntryBlockV1 === "1") {{
      return;
    }}

    const originalCreateBtn = wrapper.querySelector(".appverbo-sidebar-section-create-btn-v2");
    const tableWrap = wrapper.querySelector(".appverbo-sidebar-sections-table-wrap-v2");
    const tbody = wrapper.querySelector(".appverbo-sidebar-sections-body-v2");

    if (!originalCreateBtn || !tableWrap || !tbody) {{
      return;
    }}

    wrapper.dataset.createEntryBlockV1 = "1";

    originalCreateBtn.hidden = true;
    originalCreateBtn.setAttribute("aria-hidden", "true");
    originalCreateBtn.classList.add("appverbo-create-entry-original-hidden-v1");

    const createBlock = document.createElement("div");
    createBlock.className = "appverbo-create-entry-block-v1";
    createBlock.dataset.createEntryBlock = "sessoes";

    const createToolbar = document.createElement("div");
    createToolbar.className = "appverbo-create-entry-toolbar-v1";

    const abrirBtn = document.createElement("button");
    abrirBtn.type = "button";
    abrirBtn.className = "action-btn appverbo-create-entry-open-btn-v1";
    abrirBtn.textContent = "Criar sessão";

    createToolbar.appendChild(abrirBtn);

    const formPanel = document.createElement("div");
    formPanel.className = "appverbo-create-entry-panel-v1";
    formPanel.hidden = true;

    const grid = document.createElement("div");
    grid.className = "appverbo-create-entry-grid-v1";

    const field = document.createElement("div");
    field.className = "field appverbo-create-entry-field-v1";

    const label = document.createElement("label");
    label.setAttribute("for", "appverbo-create-entry-session-name-v1");
    label.textContent = "Nome da sessão *";

    const input = document.createElement("input");
    input.id = "appverbo-create-entry-session-name-v1";
    input.type = "text";
    input.maxLength = 80;
    input.placeholder = "Informe o nome da sessão";

    const error = document.createElement("p");
    error.className = "appverbo-create-entry-error-v1";
    error.hidden = true;
    error.textContent = "Informe o nome da sessão.";

    field.appendChild(label);
    field.appendChild(input);
    field.appendChild(error);
    grid.appendChild(field);

    const actions = document.createElement("div");
    actions.className = "appverbo-create-entry-actions-v1";

    const guardarBtn = document.createElement("button");
    guardarBtn.type = "button";
    guardarBtn.className = "action-btn appverbo-create-entry-save-btn-v1";
    guardarBtn.textContent = "Guardar";

    const cancelarBtn = document.createElement("button");
    cancelarBtn.type = "button";
    cancelarBtn.className = "action-btn-cancel appverbo-create-entry-cancel-btn-v1";
    cancelarBtn.textContent = "Cancelar";

    actions.appendChild(guardarBtn);
    actions.appendChild(cancelarBtn);

    formPanel.appendChild(grid);
    formPanel.appendChild(actions);

    createBlock.appendChild(createToolbar);
    createBlock.appendChild(formPanel);

    wrapper.insertBefore(createBlock, tableWrap);

    function abrirFormularioCriacao() {{
      formPanel.hidden = false;
      abrirBtn.hidden = true;
      error.hidden = true;
      input.classList.remove("appverbo-create-entry-input-error-v1");
      input.focus();
    }}

    function fecharFormularioCriacao() {{
      input.value = "";
      error.hidden = true;
      input.classList.remove("appverbo-create-entry-input-error-v1");
      formPanel.hidden = true;
      abrirBtn.hidden = false;
    }}

    abrirBtn.addEventListener("click", abrirFormularioCriacao);

    cancelarBtn.addEventListener("click", function () {{
      fecharFormularioCriacao();
    }});

    input.addEventListener("keydown", function (event) {{
      if (event.key === "Enter") {{
        event.preventDefault();
        guardarBtn.click();
      }}

      if (event.key === "Escape") {{
        event.preventDefault();
        cancelarBtn.click();
      }}
    }});

    guardarBtn.addEventListener("click", function () {{
      const nomeSessao = String(input.value || "").trim();

      if (!nomeSessao) {{
        error.hidden = false;
        input.classList.add("appverbo-create-entry-input-error-v1");
        input.focus();
        return;
      }}

      originalCreateBtn.click();

      const linhas = Array.from(tbody.querySelectorAll("tr.appverbo-sidebar-section-row-v2"));
      const novaLinha = linhas[linhas.length - 1];

      if (!novaLinha) {{
        return;
      }}

      const labelInput = novaLinha.querySelector('[name="section_label"]');
      const keyInput = novaLinha.querySelector('[name="section_key"]');
      const novaChave = criarChaveUnicaSessoesCreateBlock_v1(tbody, nomeSessao, novaLinha);

      if (labelInput) {{
        labelInput.value = nomeSessao;
        labelInput.readOnly = true;
        labelInput.classList.remove("appverbo-sidebar-section-label-input-editing-v2");
        labelInput.dispatchEvent(new Event("input", {{
          bubbles: true,
          cancelable: true
        }}));
        labelInput.dispatchEvent(new Event("blur", {{
          bubbles: true,
          cancelable: true
        }}));
      }}

      if (keyInput) {{
        keyInput.value = novaChave;
        keyInput.dataset.generatedV2 = "1";
      }}

      sincronizarLinhaSessoesLayout_v2(novaLinha);
      atualizarDetalheSessoesLayout_v2(novaLinha);
      atualizarEstadoBotoesSessoesLayout_v2(tbody);
      marcarAlteradoSessoesLayout_v2(formulario);

      fecharFormularioCriacao();

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
    js_content = js_pattern.sub(create_entry_helper.strip(), js_content, count=1)
else:
    install_anchor = "  //###################################################################################\n  // (6) INSTALAR LAYOUT\n  //###################################################################################\n\n"

    if install_anchor not in js_content:
        fail_v1("não encontrei âncora do bloco de instalação para inserir o bloco Criar sessão.")

    js_content = js_content.replace(install_anchor, create_entry_helper + install_anchor, 1)

call_old = '''    atualizarEstadoBotoesSessoesLayout_v2(tbody);

    return wrapper;
'''

call_new = '''    atualizarEstadoBotoesSessoesLayout_v2(tbody);
    aplicarBlocoCriacaoSessoes_v1(formulario, wrapper);

    return wrapper;
'''

if call_old in js_content:
    js_content = js_content.replace(call_old, call_new, 1)
elif "aplicarBlocoCriacaoSessoes_v1(formulario, wrapper);" not in js_content:
    fail_v1("não encontrei local para chamar aplicarBlocoCriacaoSessoes_v1.")

JS_PATH.write_text(js_content, encoding="utf-8")

print("OK: bloco Criar sessão aplicado no JS.")


####################################################################################
# (5) APLICAR CSS DO BLOCO DE CRIAÇÃO
####################################################################################

css_content = CSS_PATH.read_text(encoding="utf-8")

css_block = f'''{CSS_MARKER_START}

.appverbo-create-entry-block-v1 {{
  border: 1px solid #d5dceb;
  background: #f7faff;
  border-radius: 12px;
  padding: 14px;
  margin: 0 0 16px;
}}

.appverbo-create-entry-toolbar-v1 {{
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 8px;
}}

.appverbo-create-entry-panel-v1 {{
  margin-top: 14px;
}}

.appverbo-create-entry-panel-v1[hidden],
.appverbo-create-entry-open-btn-v1[hidden] {{
  display: none !important;
}}

.appverbo-create-entry-grid-v1 {{
  display: grid;
  grid-template-columns: minmax(260px, 420px);
  gap: 12px;
  align-items: end;
}}

.appverbo-create-entry-field-v1 label {{
  display: block;
  margin-bottom: 6px;
  color: #243557;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
}}

.appverbo-create-entry-field-v1 input {{
  width: 100%;
  border: 1px solid #c6d0e2;
  border-radius: 7px;
  background: #ffffff;
  color: #12213a;
  min-height: 38px;
  padding: 8px 10px;
  box-sizing: border-box;
}}

.appverbo-create-entry-field-v1 input:focus {{
  border-color: #2454b0;
  outline: none;
  box-shadow: 0 0 0 2px rgba(36, 84, 176, 0.12);
}}

.appverbo-create-entry-input-error-v1 {{
  border-color: #d93025 !important;
}}

.appverbo-create-entry-error-v1 {{
  margin: 6px 0 0;
  color: #b42318;
  font-size: 12px;
}}

.appverbo-create-entry-actions-v1 {{
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 8px;
  margin-top: 12px;
}}

.appverbo-create-entry-actions-v1 .action-btn,
.appverbo-create-entry-actions-v1 .action-btn-cancel,
.appverbo-create-entry-toolbar-v1 .action-btn {{
  min-width: 112px;
  width: 112px;
  height: 38px;
  min-height: 38px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
}}

.appverbo-create-entry-original-hidden-v1 {{
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

print("OK: CSS do bloco Criar sessão aplicado.")


####################################################################################
# (6) ATUALIZAR CACHE BUSTER NO TEMPLATE
####################################################################################

template_content = TEMPLATE_PATH.read_text(encoding="utf-8")

if "static/js/modules/sidebar_sections_layout_v1.js" in template_content:
    template_content = re.sub(
        r"/static/js/modules/sidebar_sections_layout_v1\.js\?v=[^\"]+",
        JS_CACHE,
        template_content,
    )
else:
    fail_v1("não encontrei sidebar_sections_layout_v1.js no template.")

if "static/css/modules/sidebar_sections_layout_v1.css" in template_content:
    template_content = re.sub(
        r"/static/css/modules/sidebar_sections_layout_v1\.css\?v=[^\"]+",
        CSS_CACHE,
        template_content,
    )
else:
    fail_v1("não encontrei sidebar_sections_layout_v1.css no template.")

if "static/css/new_user.css" in template_content:
    template_content = re.sub(
        r"/static/css/new_user\.css\?v=[^\"]+",
        NEW_USER_CSS_CACHE,
        template_content,
    )

TEMPLATE_PATH.write_text(template_content, encoding="utf-8")

print("OK: cache buster atualizado.")


####################################################################################
# (7) VALIDAR CONTEUDO FINAL
####################################################################################

agents_validado = agents_path.read_text(encoding="utf-8")
js_validado = JS_PATH.read_text(encoding="utf-8")
css_validado = CSS_PATH.read_text(encoding="utf-8")
template_validado = TEMPLATE_PATH.read_text(encoding="utf-8")

validacoes = {
    "APPVERBO_CREATE_ENTRY_BLOCK_RULE_V1_START": agents_validado,
    "Criar + nome da aba/processo": agents_validado,
    "APPVERBO_CREATE_ENTRY_BLOCK_SESSOES_V1_START": js_validado,
    "function aplicarBlocoCriacaoSessoes_v1": js_validado,
    'abrirBtn.textContent = "Criar sessão";': js_validado,
    'guardarBtn.textContent = "Guardar";': js_validado,
    'cancelarBtn.textContent = "Cancelar";': js_validado,
    "appverbo-create-entry-block-v1": css_validado,
    "APPVERBO_CREATE_ENTRY_BLOCK_STANDARD_V1_START": css_validado,
    "20260505-create-entry-block-v1": template_validado,
}

for termo, conteudo in validacoes.items():
    if termo not in conteudo:
        fail_v1(f"validação falhou, termo ausente: {termo}")

print("OK: regra global e aplicação na aba Sessões concluídas.")
