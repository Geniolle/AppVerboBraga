from pathlib import Path
import re
import sys

ROOT = Path.cwd()

AGENTS_UPPER_PATH = ROOT / "AGENTS.md"
AGENTS_TITLE_PATH = ROOT / "Agents.md"
TEMPLATE_PATH = ROOT / "templates" / "new_user.html"
JS_PATH = ROOT / "static" / "js" / "modules" / "sidebar_sections_layout_v1.js"
CSS_PATH = ROOT / "static" / "css" / "modules" / "sidebar_sections_layout_v1.css"

AGENTS_MARKER_START = "<!-- APPVERBO_SESSOES_EDIT_INLINE_V8_START -->"
AGENTS_MARKER_END = "<!-- APPVERBO_SESSOES_EDIT_INLINE_V8_END -->"

JS_MARKER_START = "// APPVERBO_SESSOES_EDIT_INLINE_V8_START"
JS_MARKER_END = "// APPVERBO_SESSOES_EDIT_INLINE_V8_END"

CSS_MARKER_START = "/* APPVERBO_SESSOES_EDIT_INLINE_V8_START */"
CSS_MARKER_END = "/* APPVERBO_SESSOES_EDIT_INLINE_V8_END */"

JS_CACHE = "/static/js/modules/sidebar_sections_layout_v1.js?v=20260505-sessoes-edit-inline-v8"
CSS_CACHE = "/static/css/modules/sidebar_sections_layout_v1.css?v=20260505-sessoes-edit-inline-v8"


def fail_v8(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


####################################################################################
# (1) RESOLVER AGENTS.md
####################################################################################

def resolve_agents_path_v8() -> Path:
    if AGENTS_UPPER_PATH.exists():
        return AGENTS_UPPER_PATH

    if AGENTS_TITLE_PATH.exists():
        return AGENTS_TITLE_PATH

    AGENTS_UPPER_PATH.write_text("# AGENTS.md\n\n", encoding="utf-8")
    return AGENTS_UPPER_PATH


####################################################################################
# (2) ATUALIZAR REGRA NO AGENTS.md
####################################################################################

agents_path = resolve_agents_path_v8()
agents_content = agents_path.read_text(encoding="utf-8")

agents_rule = f"""{AGENTS_MARKER_START}
## Regra para edição de Sessões

Na aba **Sessões**, o botão de editar da coluna **Ações** deve abrir edição diretamente na linha, sem usar `alert`.

Campos editáveis da linha:

1. **Nome da sessão**;
2. **Sistema**;
3. **Estado**.

A chave técnica da sessão deve continuar oculta e preservada, para não quebrar vínculos existentes dos menus/processos.

Durante a edição da linha:

1. Substituir os ícones de ação por **Guardar** e **Cancelar**.
2. **Guardar** atualiza os campos ocultos, grava a ordem atual e submete o formulário.
3. **Cancelar** restaura os valores anteriores sem gravar.
4. Não mostrar mensagens temporárias do tipo "edição será ajustada no próximo passo".
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

print(f"OK: regra de edição inline atualizada em {agents_path}")


####################################################################################
# (3) VALIDAR FICHEIROS
####################################################################################

for file_path in [TEMPLATE_PATH, JS_PATH, CSS_PATH]:
    if not file_path.exists():
        fail_v8(f"ficheiro não encontrado: {file_path}")


####################################################################################
# (4) INSERIR FUNCOES DE EDICAO INLINE NO JS
####################################################################################

js_content = JS_PATH.read_text(encoding="utf-8")

js_helper = "  " + JS_MARKER_START + r'''
  function criarSelectSistemaSessoesV8(valorAtual) {
    const select = document.createElement("select");
    select.className = "appverbo-sidebar-section-edit-select-v8";

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

  function criarSelectEstadoSessoesV8(valorAtual) {
    const estadoAtual = normalizarEstadoSessoesV6(valorAtual);
    const select = document.createElement("select");
    select.className = "appverbo-sidebar-section-edit-select-v8";

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

  function obterCamposLinhaSessoesV8(linha) {
    return {
      keyInput: linha.querySelector('[name="section_key"]'),
      labelInput: linha.querySelector('[name="section_label"]'),
      scopeInput: linha.querySelector('[name="section_visibility_scope_mode"]'),
      statusInput: linha.querySelector('[name="section_status"]')
    };
  }

  function criarBadgeEstadoSessoesV8(estado) {
    const estadoNormalizado = normalizarEstadoSessoesV6(estado);
    const badge = document.createElement("span");
    badge.className = "appverbo-sidebar-section-state-badge-v2 appverbo-sidebar-section-state-badge-" + estadoNormalizado + "-v6";
    badge.textContent = obterLabelEstadoSessoesV6(estadoNormalizado);
    return badge;
  }

  function restaurarAcoesLinhaSessoesV8(linha, tbody) {
    const tdAcoes = linha.querySelector(".appverbo-sidebar-section-actions-cell-v2");

    if (!tdAcoes) {
      return;
    }

    tdAcoes.innerHTML = "";

    const actions = document.createElement("div");
    actions.className = "appverbo-sidebar-section-actions-v2";
    actions.appendChild(criarBotaoAcaoSessoesV6("up", "Subir sessão", "↑"));
    actions.appendChild(criarBotaoAcaoSessoesV6("down", "Descer sessão", "↓"));
    actions.appendChild(criarBotaoAcaoSessoesV6("view", "Visualizar detalhes", "👁"));
    actions.appendChild(criarBotaoAcaoSessoesV6("edit", "Editar sessão", "✎"));

    tdAcoes.appendChild(actions);
    atualizarEstadoBotoesSessoesV6(tbody);
  }

  function restaurarLinhaSessoesV8(linha, valores, tbody) {
    const campos = obterCamposLinhaSessoesV8(linha);
    const tdMenu = linha.querySelector(".appverbo-sidebar-section-menu-cell-v2");
    const tdSistema = linha.querySelector(".appverbo-sidebar-section-system-cell-v2");
    const tdEstado = linha.querySelector(".appverbo-sidebar-section-state-cell-v2");

    if (!campos.keyInput || !campos.labelInput || !campos.scopeInput || !campos.statusInput || !tdMenu || !tdSistema || !tdEstado) {
      return;
    }

    campos.keyInput.value = valores.key;
    campos.labelInput.value = valores.label;
    campos.scopeInput.value = valores.scope;
    campos.statusInput.value = valores.status;

    tdMenu.innerHTML = "";
    tdMenu.textContent = valores.label;
    tdMenu.appendChild(campos.keyInput);
    tdMenu.appendChild(campos.labelInput);
    tdMenu.appendChild(campos.scopeInput);
    tdMenu.appendChild(campos.statusInput);

    tdSistema.innerHTML = "";
    tdSistema.textContent = obterLabelSistemaSessoesV6(valores.scope, valores.scopeLabel || "");

    tdEstado.innerHTML = "";
    tdEstado.appendChild(criarBadgeEstadoSessoesV8(valores.status));

    linha.dataset.editingV8 = "0";
    restaurarAcoesLinhaSessoesV8(linha, tbody);
  }

  function abrirEdicaoLinhaSessoesV8(linha, formulario, tbody) {
    if (!linha || linha.dataset.editingV8 === "1") {
      return;
    }

    const campos = obterCamposLinhaSessoesV8(linha);
    const tdMenu = linha.querySelector(".appverbo-sidebar-section-menu-cell-v2");
    const tdSistema = linha.querySelector(".appverbo-sidebar-section-system-cell-v2");
    const tdEstado = linha.querySelector(".appverbo-sidebar-section-state-cell-v2");
    const tdAcoes = linha.querySelector(".appverbo-sidebar-section-actions-cell-v2");

    if (!campos.keyInput || !campos.labelInput || !campos.scopeInput || !campos.statusInput || !tdMenu || !tdSistema || !tdEstado || !tdAcoes) {
      return;
    }

    linha.dataset.editingV8 = "1";

    const valoresOriginais = {
      key: String(campos.keyInput.value || "").trim(),
      label: String(campos.labelInput.value || "").trim(),
      scope: String(campos.scopeInput.value || "all").trim(),
      scopeLabel: obterLabelSistemaSessoesV6(campos.scopeInput.value || "all", ""),
      status: normalizarEstadoSessoesV6(campos.statusInput.value || "ativo")
    };

    const nomeInput = document.createElement("input");
    nomeInput.type = "text";
    nomeInput.className = "appverbo-sidebar-section-edit-input-v8";
    nomeInput.value = valoresOriginais.label;
    nomeInput.maxLength = 80;

    const sistemaSelect = criarSelectSistemaSessoesV8(valoresOriginais.scope);
    const estadoSelect = criarSelectEstadoSessoesV8(valoresOriginais.status);

    tdMenu.innerHTML = "";
    tdMenu.appendChild(nomeInput);
    tdMenu.appendChild(campos.keyInput);
    tdMenu.appendChild(campos.labelInput);
    tdMenu.appendChild(campos.scopeInput);
    tdMenu.appendChild(campos.statusInput);

    tdSistema.innerHTML = "";
    tdSistema.appendChild(sistemaSelect);

    tdEstado.innerHTML = "";
    tdEstado.appendChild(estadoSelect);

    tdAcoes.innerHTML = "";

    const actions = document.createElement("div");
    actions.className = "appverbo-sidebar-section-edit-actions-v8";

    const guardarBtn = document.createElement("button");
    guardarBtn.type = "button";
    guardarBtn.className = "action-btn appverbo-sidebar-section-edit-save-v8";
    guardarBtn.textContent = "Guardar";

    const cancelarBtn = document.createElement("button");
    cancelarBtn.type = "button";
    cancelarBtn.className = "action-btn-cancel appverbo-sidebar-section-edit-cancel-v8";
    cancelarBtn.textContent = "Cancelar";

    actions.appendChild(guardarBtn);
    actions.appendChild(cancelarBtn);
    tdAcoes.appendChild(actions);

    function validarNome() {
      const nome = String(nomeInput.value || "").trim();

      if (!nome) {
        nomeInput.classList.add("appverbo-sidebar-section-edit-input-error-v8");
        nomeInput.focus();
        return "";
      }

      nomeInput.classList.remove("appverbo-sidebar-section-edit-input-error-v8");
      return nome;
    }

    guardarBtn.addEventListener("click", function () {
      const nome = validarNome();

      if (!nome) {
        return;
      }

      const valoresAtualizados = {
        key: valoresOriginais.key || criarChaveSessoesV6(nome),
        label: nome,
        scope: String(sistemaSelect.value || "all").trim(),
        scopeLabel: obterLabelSistemaSessoesV6(sistemaSelect.value || "all", ""),
        status: normalizarEstadoSessoesV6(estadoSelect.value || "ativo")
      };

      restaurarLinhaSessoesV8(linha, valoresAtualizados, tbody);
      submeterFormularioSessoesV6(formulario);
    });

    cancelarBtn.addEventListener("click", function () {
      restaurarLinhaSessoesV8(linha, valoresOriginais, tbody);
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

    sistemaSelect.addEventListener("keydown", function (event) {
      if (event.key === "Escape") {
        event.preventDefault();
        cancelarBtn.click();
      }
    });

    estadoSelect.addEventListener("keydown", function (event) {
      if (event.key === "Escape") {
        event.preventDefault();
        cancelarBtn.click();
      }
    });

    nomeInput.focus();
    nomeInput.select();
  }

''' + "  " + JS_MARKER_END + "\n\n"

if JS_MARKER_START in js_content and JS_MARKER_END in js_content:
    js_pattern = re.compile(
        re.escape(JS_MARKER_START) + r"[\s\S]*?" + re.escape(JS_MARKER_END),
        re.S,
    )
    js_content = js_pattern.sub(js_helper.strip(), js_content, count=1)
else:
    anchor = "  function criarLinhaSessoesV6(sessao) {"

    if anchor not in js_content:
        fail_v8("não encontrei function criarLinhaSessoesV6 para inserir helpers de edição.")

    js_content = js_content.replace(anchor, js_helper + anchor, 1)

edit_alert_pattern = re.compile(
    r'''      if \(acao === "edit"\) \{\s*
        alert\("Edição inline será ajustada no próximo passo\. Para já, use Criar sessão para novas entradas\."\);\s*
      \}''',
    re.S,
)

edit_replacement = '''      if (acao === "edit") {
        abrirEdicaoLinhaSessoesV8(linha, formulario, tbody);
      }'''

if edit_alert_pattern.search(js_content):
    js_content = edit_alert_pattern.sub(edit_replacement, js_content, count=1)
elif "abrirEdicaoLinhaSessoesV8(linha, formulario, tbody);" not in js_content:
    generic_alert_pattern = re.compile(
        r'''      if \(acao === "edit"\) \{\s*
        alert\([\s\S]*?\);\s*
      \}''',
        re.S,
    )

    if generic_alert_pattern.search(js_content):
        js_content = generic_alert_pattern.sub(edit_replacement, js_content, count=1)
    else:
        fail_v8("não encontrei o bloco do botão editar com alert para substituir.")

if "Edição inline será ajustada no próximo passo" in js_content:
    fail_v8("a mensagem antiga de edição ainda existe no JS.")

JS_PATH.write_text(js_content, encoding="utf-8")

print("OK: botão Editar agora abre edição inline da linha.")


####################################################################################
# (5) ATUALIZAR CSS DA EDICAO INLINE
####################################################################################

css_content = CSS_PATH.read_text(encoding="utf-8")

css_block = f'''{CSS_MARKER_START}

.appverbo-sidebar-section-edit-input-v8,
.appverbo-sidebar-section-edit-select-v8 {{
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

.appverbo-sidebar-section-edit-input-v8:focus,
.appverbo-sidebar-section-edit-select-v8:focus {{
  border-color: #2454b0;
  outline: none;
  box-shadow: 0 0 0 2px rgba(36, 84, 176, 0.12);
}}

.appverbo-sidebar-section-edit-input-error-v8 {{
  border-color: #d93025 !important;
}}

.appverbo-sidebar-section-edit-actions-v8 {{
  display: inline-flex;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
  white-space: nowrap;
}}

.appverbo-sidebar-section-edit-actions-v8 .action-btn,
.appverbo-sidebar-section-edit-actions-v8 .action-btn-cancel {{
  min-width: 78px !important;
  width: 78px !important;
  height: 30px !important;
  min-height: 30px !important;
  padding: 0 8px !important;
  font-size: 11px !important;
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

print("OK: CSS da edição inline atualizado.")


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
    fail_v8("não encontrei sidebar_sections_layout_v1.js no template.")

if "static/css/modules/sidebar_sections_layout_v1.css" in template_content:
    template_content = re.sub(
        r"/static/css/modules/sidebar_sections_layout_v1\.css\?v=[^\"]+",
        CSS_CACHE,
        template_content,
    )
else:
    fail_v8("não encontrei sidebar_sections_layout_v1.css no template.")

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
    "APPVERBO_SESSOES_EDIT_INLINE_V8_START": agents_validado,
    "abrirEdicaoLinhaSessoesV8": js_validado,
    "criarSelectSistemaSessoesV8": js_validado,
    "criarSelectEstadoSessoesV8": js_validado,
    "restaurarLinhaSessoesV8": js_validado,
    "abrirEdicaoLinhaSessoesV8(linha, formulario, tbody);": js_validado,
    "APPVERBO_SESSOES_EDIT_INLINE_V8_START": css_validado,
    "appverbo-sidebar-section-edit-input-v8": css_validado,
    "20260505-sessoes-edit-inline-v8": template_validado,
}

for termo, conteudo in validacoes.items():
    if termo not in conteudo:
        fail_v8(f"validação falhou, termo ausente: {termo}")

if "Edição inline será ajustada no próximo passo" in js_validado:
    fail_v8("mensagem antiga ainda encontrada no JS.")

print("OK: patch_sessoes_edicao_inline_v8 concluído.")
