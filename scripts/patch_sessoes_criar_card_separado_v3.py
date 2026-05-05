from pathlib import Path
import re
import sys

ROOT = Path.cwd()

AGENTS_UPPER_PATH = ROOT / "AGENTS.md"
AGENTS_TITLE_PATH = ROOT / "Agents.md"
TEMPLATE_PATH = ROOT / "templates" / "new_user.html"
JS_PATH = ROOT / "static" / "js" / "modules" / "sidebar_sections_layout_v1.js"
CSS_PATH = ROOT / "static" / "css" / "modules" / "sidebar_sections_layout_v1.css"

AGENTS_MARKER_START = "<!-- APPVERBO_CREATE_ENTRY_SEPARATE_CARD_RULE_V3_START -->"
AGENTS_MARKER_END = "<!-- APPVERBO_CREATE_ENTRY_SEPARATE_CARD_RULE_V3_END -->"

JS_MARKER_START = "// APPVERBO_SESSOES_CREATE_CARD_SEPARADO_V3_START"
JS_MARKER_END = "// APPVERBO_SESSOES_CREATE_CARD_SEPARADO_V3_END"

CSS_MARKER_START = "/* APPVERBO_SESSOES_CREATE_CARD_SEPARADO_V3_START */"
CSS_MARKER_END = "/* APPVERBO_SESSOES_CREATE_CARD_SEPARADO_V3_END */"

JS_CACHE = "/static/js/modules/sidebar_sections_layout_v1.js?v=20260505-sessoes-create-card-v3"
CSS_CACHE = "/static/css/modules/sidebar_sections_layout_v1.css?v=20260505-sessoes-create-card-v3"


def fail_v3(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


####################################################################################
# (1) RESOLVER AGENTS.md
####################################################################################

def resolve_agents_path_v3() -> Path:
    if AGENTS_UPPER_PATH.exists():
        return AGENTS_UPPER_PATH

    if AGENTS_TITLE_PATH.exists():
        return AGENTS_TITLE_PATH

    AGENTS_UPPER_PATH.write_text("# AGENTS.md\n\n", encoding="utf-8")
    return AGENTS_UPPER_PATH


####################################################################################
# (2) ATUALIZAR REGRA NO AGENTS.md
####################################################################################

agents_path = resolve_agents_path_v3()
agents_content = agents_path.read_text(encoding="utf-8")

agents_rule = f"""{AGENTS_MARKER_START}
## Regra global para card separado de criação

Sempre que uma aba/subprocesso tiver uma opção de criar nova entrada:

1. O botão **Criar + nome da aba/processo** deve ficar em um **card/bloco próprio**, separado visualmente do card da tabela/lista.
2. O card de criação deve ficar acima do card da tabela/lista, no mesmo padrão visual usado na aba **Entidade**.
3. O botão de criação deve ficar no lado esquerdo do card de criação.
4. Ao clicar no botão de criação, os campos devem abrir dentro desse mesmo card de criação.
5. Os botões **Guardar** e **Cancelar** do formulário de criação devem ficar dentro do card de criação, sempre à esquerda e com o mesmo tamanho.
6. A tabela/lista deve ficar em outro card separado, exibindo apenas os registos já criados e as ações da listagem.
7. Não colocar o bloco de criação dentro do mesmo card da lista quando o layout de referência separar criação e listagem.
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

print(f"OK: regra de card separado atualizada em {agents_path}")


####################################################################################
# (3) VALIDAR FICHEIROS
####################################################################################

if not TEMPLATE_PATH.exists():
    fail_v3(f"template não encontrado: {TEMPLATE_PATH}")

if not JS_PATH.exists():
    fail_v3(f"JS não encontrado: {JS_PATH}")

if not CSS_PATH.exists():
    fail_v3(f"CSS não encontrado: {CSS_PATH}")


####################################################################################
# (4) INSERIR FUNCAO PARA MOVER CRIACAO PARA CARD PROPRIO
####################################################################################

js_content = JS_PATH.read_text(encoding="utf-8")

create_card_helper = f'''  {JS_MARKER_START}
  function obterOuCriarCardCriacaoSessoes_v3(cardLista) {{
    if (!cardLista || !cardLista.parentElement) {{
      return null;
    }}

    let createCard = document.getElementById("admin-sidebar-sections-create-card");

    if (!createCard) {{
      createCard = document.createElement("section");
      createCard.id = "admin-sidebar-sections-create-card";
      createCard.className = "card appverbo-sessoes-create-card-v3";
      createCard.dataset.menuScope = "administrativo";
      cardLista.parentElement.insertBefore(createCard, cardLista);
    }}

    return createCard;
  }}

  function moverBlocoCriacaoParaCardSeparadoSessoes_v3(cardLista, wrapper) {{
    const createBlock = wrapper && wrapper.querySelector(".appverbo-create-entry-block-v1");

    if (!cardLista || !wrapper || !createBlock) {{
      return;
    }}

    const createCard = obterOuCriarCardCriacaoSessoes_v3(cardLista);

    if (!createCard) {{
      return;
    }}

    if (createBlock.parentElement !== createCard) {{
      createCard.appendChild(createBlock);
    }}

    createCard.hidden = false;
    createCard.style.display = "";

    const slotsVazios = Array.from(wrapper.querySelectorAll(".appverbo-create-entry-slot-v2"));

    slotsVazios.forEach(function (slot) {{
      if (!slot.children.length) {{
        slot.remove();
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
    js_content = js_pattern.sub(create_card_helper.strip(), js_content, count=1)
else:
    install_anchor = "  //###################################################################################\n  // (6) INSTALAR LAYOUT\n  //###################################################################################\n\n"

    if install_anchor not in js_content:
        fail_v3("não encontrei âncora do bloco de instalação para inserir helper V3.")

    js_content = js_content.replace(install_anchor, create_card_helper + install_anchor, 1)


####################################################################################
# (5) CHAMAR A FUNCAO APOS CRIAR O LAYOUT
####################################################################################

target_call = '''    atualizarEstadoBotoesSessoesLayout_v2(tbody);
    aplicarBlocoCriacaoSessoes_v1(formulario, wrapper);

    return wrapper;
'''

replacement_call = '''    atualizarEstadoBotoesSessoesLayout_v2(tbody);
    aplicarBlocoCriacaoSessoes_v1(formulario, wrapper);

    const cardListaSessoesV3 = formulario.closest(".card, section");
    moverBlocoCriacaoParaCardSeparadoSessoes_v3(cardListaSessoesV3, wrapper);

    return wrapper;
'''

if target_call in js_content:
    js_content = js_content.replace(target_call, replacement_call, 1)
elif "moverBlocoCriacaoParaCardSeparadoSessoes_v3(cardListaSessoesV3, wrapper);" not in js_content:
    fail_v3("não encontrei local para chamar moverBlocoCriacaoParaCardSeparadoSessoes_v3.")

JS_PATH.write_text(js_content, encoding="utf-8")

print("OK: JS atualizado para mover Criar sessão para card separado.")


####################################################################################
# (6) ATUALIZAR CSS
####################################################################################

css_content = CSS_PATH.read_text(encoding="utf-8")

css_block = f"""{CSS_MARKER_START}

.appverbo-sessoes-create-card-v3 {{
  margin-bottom: 12px;
  padding: 16px;
  min-height: 66px;
  display: flex;
  align-items: center;
  justify-content: flex-start;
}}

.appverbo-sessoes-create-card-v3 .appverbo-create-entry-block-v1 {{
  width: 100%;
  margin: 0 !important;
  border: 0 !important;
  background: transparent !important;
  border-radius: 0 !important;
  padding: 0 !important;
}}

.appverbo-sessoes-create-card-v3 .appverbo-create-entry-toolbar-v1 {{
  display: flex !important;
  justify-content: flex-start !important;
  align-items: center !important;
}}

.appverbo-sessoes-create-card-v3 .appverbo-create-entry-panel-v1 {{
  margin-top: 14px !important;
  padding-top: 14px !important;
  border-top: 1px solid #d5dceb !important;
}}

.appverbo-sessoes-create-card-v3 .appverbo-create-entry-actions-v1 {{
  display: flex !important;
  justify-content: flex-start !important;
  align-items: center !important;
  gap: 8px !important;
}}

.appverbo-sidebar-sections-card-v2 .appverbo-create-entry-slot-v2,
.appverbo-sidebar-sections-card-v2 .appverbo-create-entry-slot-v2:empty {{
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

CSS_PATH.write_text(css_content, encoding="utf-8")

print("OK: CSS atualizado para card separado de Criar sessão.")


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
    fail_v3("não encontrei JS sidebar_sections_layout_v1 no template.")

if "static/css/modules/sidebar_sections_layout_v1.css" in template_content:
    template_content = re.sub(
        r"/static/css/modules/sidebar_sections_layout_v1\.css\?v=[^\"]+",
        CSS_CACHE,
        template_content,
    )
else:
    fail_v3("não encontrei CSS sidebar_sections_layout_v1 no template.")

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
    "APPVERBO_CREATE_ENTRY_SEPARATE_CARD_RULE_V3_START": agents_validado,
    "card/bloco próprio": agents_validado,
    "APPVERBO_SESSOES_CREATE_CARD_SEPARADO_V3_START": js_validado,
    "admin-sidebar-sections-create-card": js_validado,
    "moverBlocoCriacaoParaCardSeparadoSessoes_v3": js_validado,
    "APPVERBO_SESSOES_CREATE_CARD_SEPARADO_V3_START": css_validado,
    "appverbo-sessoes-create-card-v3": css_validado,
    "20260505-sessoes-create-card-v3": template_validado,
}

for termo, conteudo in validacoes.items():
    if termo not in conteudo:
        fail_v3(f"validação falhou, termo ausente: {termo}")

print("OK: card separado de criação aplicado e validado.")
