from pathlib import Path
import re
import sys

ROOT = Path.cwd()

AGENTS_UPPER_PATH = ROOT / "AGENTS.md"
AGENTS_TITLE_PATH = ROOT / "Agents.md"
TEMPLATE_PATH = ROOT / "templates" / "new_user.html"
SESSOES_JS_PATH = ROOT / "static" / "js" / "modules" / "sidebar_sections_layout_v1.js"
SESSOES_CSS_PATH = ROOT / "static" / "css" / "modules" / "sidebar_sections_layout_v1.css"
NEW_USER_CSS_PATH = ROOT / "static" / "css" / "new_user.css"

AGENTS_MARKER_START = "<!-- APPVERBO_CREATE_ENTRY_SEPARATE_BLOCK_RULE_V2_START -->"
AGENTS_MARKER_END = "<!-- APPVERBO_CREATE_ENTRY_SEPARATE_BLOCK_RULE_V2_END -->"

CSS_MARKER_START = "/* APPVERBO_CREATE_ENTRY_SEPARATE_BLOCK_V2_START */"
CSS_MARKER_END = "/* APPVERBO_CREATE_ENTRY_SEPARATE_BLOCK_V2_END */"

JS_CACHE = "/static/js/modules/sidebar_sections_layout_v1.js?v=20260505-create-entry-separated-block-v2"
CSS_CACHE = "/static/css/modules/sidebar_sections_layout_v1.css?v=20260505-create-entry-separated-block-v2"
NEW_USER_CSS_CACHE = "/static/css/new_user.css?v=20260505-create-entry-separated-block-v2"


def fail_v2(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


####################################################################################
# (1) RESOLVER AGENTS.md
####################################################################################

def resolve_agents_path_v2() -> Path:
    if AGENTS_UPPER_PATH.exists():
        return AGENTS_UPPER_PATH

    if AGENTS_TITLE_PATH.exists():
        return AGENTS_TITLE_PATH

    AGENTS_UPPER_PATH.write_text("# AGENTS.md\n\n", encoding="utf-8")
    return AGENTS_UPPER_PATH


####################################################################################
# (2) ATUALIZAR REGRA GLOBAL NO AGENTS.md
####################################################################################

agents_path = resolve_agents_path_v2()
agents_content = agents_path.read_text(encoding="utf-8")

agents_rule = f"""{AGENTS_MARKER_START}
## Regra global para bloco separado de criação

Sempre que uma aba, subprocesso ou lista administrativa tiver ação para criar uma nova entrada do processo atual:

1. A opção **Criar + nome da aba/processo** deve ficar em um bloco/card separado acima da tabela/lista.
2. Esse bloco deve ficar visualmente separado da tabela/lista principal, com margem inferior e borda própria.
3. O botão **Criar + nome** deve ficar sempre à esquerda dentro desse bloco.
4. Ao clicar no botão **Criar + nome**, os campos de preenchimento devem aparecer dentro do mesmo bloco separado.
5. Os botões **Guardar** e **Cancelar** devem ficar dentro desse mesmo bloco separado, sempre à esquerda, com o mesmo tamanho e dimensão.
6. A tabela/lista inferior deve exibir somente os registos já criados e as ações da listagem.
7. Não colocar botão de criação no lado direito do cabeçalho da tabela/lista.
8. Não misturar o formulário de criação dentro da área visual da tabela/lista, exceto quando tecnicamente necessário, mantendo sempre separação visual clara.
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

print(f"OK: regra global de bloco separado atualizada em {agents_path}")


####################################################################################
# (3) VALIDAR FICHEIROS
####################################################################################

if not TEMPLATE_PATH.exists():
    fail_v2(f"template não encontrado: {TEMPLATE_PATH}")

if not SESSOES_JS_PATH.exists():
    fail_v2(f"JS de Sessões não encontrado: {SESSOES_JS_PATH}")

if not SESSOES_CSS_PATH.exists():
    fail_v2(f"CSS de Sessões não encontrado: {SESSOES_CSS_PATH}")


####################################################################################
# (4) AJUSTAR JS DE SESSÕES PARA BLOCO SEPARADO
####################################################################################

js_content = SESSOES_JS_PATH.read_text(encoding="utf-8")

js_content = js_content.replace(
    'criarBtn.textContent = "Criar pasta";',
    'criarBtn.textContent = "Criar sessão";',
)

js_content = js_content.replace(
    'abrirBtn.textContent = "Criar sessão";',
    'abrirBtn.textContent = "Criar sessão";',
)

insert_after = '''    wrapper.appendChild(criarCampoOcultoSessoesLayout_v2("redirect_menu", "administrativo"));
    wrapper.appendChild(criarCampoOcultoSessoesLayout_v2("redirect_target", "#admin-sidebar-sections-card"));
    wrapper.appendChild(cabecalho);
    wrapper.appendChild(tableWrap);
    wrapper.appendChild(footer);
'''

replace_after = '''    wrapper.appendChild(criarCampoOcultoSessoesLayout_v2("redirect_menu", "administrativo"));
    wrapper.appendChild(criarCampoOcultoSessoesLayout_v2("redirect_target", "#admin-sidebar-sections-card"));
    wrapper.appendChild(cabecalho);

    const createEntrySlot = document.createElement("div");
    createEntrySlot.className = "appverbo-create-entry-slot-v2";
    wrapper.appendChild(createEntrySlot);

    const listBlock = document.createElement("div");
    listBlock.className = "appverbo-list-block-v2";
    listBlock.appendChild(tableWrap);
    listBlock.appendChild(footer);
    wrapper.appendChild(listBlock);
'''

if insert_after in js_content:
    js_content = js_content.replace(insert_after, replace_after, 1)
elif "appverbo-create-entry-slot-v2" not in js_content:
    fail_v2("não encontrei o bloco wrapper da tela Sessões para criar slot separado.")

old_insert = '''    wrapper.insertBefore(createBlock, tableWrap);
'''

new_insert = '''    const createEntrySlot = wrapper.querySelector(".appverbo-create-entry-slot-v2");

    if (createEntrySlot) {
      createEntrySlot.appendChild(createBlock);
    } else {
      wrapper.insertBefore(createBlock, tableWrap);
    }
'''

if old_insert in js_content:
    js_content = js_content.replace(old_insert, new_insert, 1)
elif "createEntrySlot.appendChild(createBlock);" not in js_content:
    fail_v2("não encontrei local para mover bloco Criar sessão para slot separado.")

js_content = js_content.replace(
    'criarBtn.hidden = true;',
    'criarBtn.hidden = true;',
)

if "appverbo-create-entry-block-v1" not in js_content:
    fail_v2("bloco Criar sessão V1 não existe no JS. Execute primeiro o patch do padrão Criar/Guardar/Cancelar.")

SESSOES_JS_PATH.write_text(js_content, encoding="utf-8")

print("OK: JS de Sessões ajustado para usar bloco separado de criação.")


####################################################################################
# (5) APLICAR CSS DO BLOCO SEPARADO EM SESSÕES
####################################################################################

css_content = SESSOES_CSS_PATH.read_text(encoding="utf-8")

css_block = f"""{CSS_MARKER_START}

.appverbo-create-entry-slot-v2 {{
  margin: 16px 0;
}}

.appverbo-create-entry-slot-v2:empty {{
  display: none;
}}

.appverbo-create-entry-block-v1 {{
  border: 1px solid #d5dceb !important;
  background: #f7faff !important;
  border-radius: 12px !important;
  padding: 16px !important;
  margin: 0 !important;
  width: 100% !important;
  box-sizing: border-box !important;
}}

.appverbo-create-entry-toolbar-v1 {{
  display: flex !important;
  align-items: center !important;
  justify-content: flex-start !important;
  gap: 8px !important;
}}

.appverbo-create-entry-panel-v1 {{
  margin-top: 14px !important;
  padding-top: 14px !important;
  border-top: 1px solid #d5dceb !important;
}}

.appverbo-create-entry-actions-v1 {{
  display: flex !important;
  justify-content: flex-start !important;
  align-items: center !important;
  gap: 8px !important;
  margin-top: 12px !important;
}}

.appverbo-list-block-v2 {{
  border-top: 0 !important;
  padding-top: 0 !important;
}}

.appverbo-sidebar-sections-header-v2 {{
  margin-bottom: 0 !important;
}}

.appverbo-sidebar-sections-header-v2 .appverbo-sidebar-section-create-btn-v2,
.appverbo-create-entry-original-hidden-v1 {{
  display: none !important;
}}

{CSS_MARKER_END}"""

if CSS_MARKER_START in css_content and CSS_MARKER_END in css_content:
    css_pattern = re.compile(
        re.escape(CSS_MARKER_START) + r"[\s\S]*?" + re.escape(CSS_MARKER_END),
        re.S,
    )
    css_content = css_pattern.sub(css_block, css_content, count=1)
else:
    css_content = css_content.rstrip() + "\n\n" + css_block + "\n"

SESSOES_CSS_PATH.write_text(css_content, encoding="utf-8")

print("OK: CSS de Sessões atualizado para bloco separado.")


####################################################################################
# (6) APLICAR CSS GLOBAL PARA BLOCOS DE CRIAÇÃO EXISTENTES
####################################################################################

if NEW_USER_CSS_PATH.exists():
    new_user_css = NEW_USER_CSS_PATH.read_text(encoding="utf-8")

    global_block = f"""{CSS_MARKER_START}

.entity-create-toolbar,
.appverbo-create-entry-block-v1 {{
  border: 1px solid #d5dceb;
  background: #f7faff;
  border-radius: 12px;
  padding: 16px;
  margin: 0 0 16px;
  box-sizing: border-box;
}}

.entity-create-toolbar {{
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 8px;
}}

.entity-create-toolbar .action-btn,
.entity-create-toolbar .action-btn-secondary,
.appverbo-create-entry-toolbar-v1 .action-btn {{
  align-self: flex-start;
}}

{CSS_MARKER_END}"""

    if CSS_MARKER_START in new_user_css and CSS_MARKER_END in new_user_css:
        global_pattern = re.compile(
            re.escape(CSS_MARKER_START) + r"[\s\S]*?" + re.escape(CSS_MARKER_END),
            re.S,
        )
        new_user_css = global_pattern.sub(global_block, new_user_css, count=1)
    else:
        new_user_css = new_user_css.rstrip() + "\n\n" + global_block + "\n"

    NEW_USER_CSS_PATH.write_text(new_user_css, encoding="utf-8")
    print("OK: CSS global new_user.css atualizado para blocos de criação.")
else:
    print("AVISO: static/css/new_user.css não encontrado.")


####################################################################################
# (7) ATUALIZAR CACHE BUSTER NO TEMPLATE
####################################################################################

template_content = TEMPLATE_PATH.read_text(encoding="utf-8")

if "static/js/modules/sidebar_sections_layout_v1.js" in template_content:
    template_content = re.sub(
        r"/static/js/modules/sidebar_sections_layout_v1\.js\?v=[^\"]+",
        JS_CACHE,
        template_content,
    )
else:
    fail_v2("não encontrei JS sidebar_sections_layout_v1 no template.")

if "static/css/modules/sidebar_sections_layout_v1.css" in template_content:
    template_content = re.sub(
        r"/static/css/modules/sidebar_sections_layout_v1\.css\?v=[^\"]+",
        CSS_CACHE,
        template_content,
    )
else:
    fail_v2("não encontrei CSS sidebar_sections_layout_v1 no template.")

if "static/css/new_user.css" in template_content:
    template_content = re.sub(
        r"/static/css/new_user\.css\?v=[^\"]+",
        NEW_USER_CSS_CACHE,
        template_content,
    )

TEMPLATE_PATH.write_text(template_content, encoding="utf-8")

print("OK: cache buster atualizado no template.")


####################################################################################
# (8) VALIDAR CONTEUDO
####################################################################################

agents_validado = agents_path.read_text(encoding="utf-8")
js_validado = SESSOES_JS_PATH.read_text(encoding="utf-8")
css_validado = SESSOES_CSS_PATH.read_text(encoding="utf-8")
template_validado = TEMPLATE_PATH.read_text(encoding="utf-8")

validacoes = {
    "APPVERBO_CREATE_ENTRY_SEPARATE_BLOCK_RULE_V2_START": agents_validado,
    "bloco/card separado acima da tabela/lista": agents_validado,
    "appverbo-create-entry-slot-v2": js_validado,
    "appverbo-list-block-v2": js_validado,
    "createEntrySlot.appendChild(createBlock);": js_validado,
    "APPVERBO_CREATE_ENTRY_SEPARATE_BLOCK_V2_START": css_validado,
    "appverbo-create-entry-slot-v2": css_validado,
    "20260505-create-entry-separated-block-v2": template_validado,
}

for termo, conteudo in validacoes.items():
    if termo not in conteudo:
        fail_v2(f"validação falhou, termo ausente: {termo}")

print("OK: criação de entradas em bloco separado aplicada e validada.")
