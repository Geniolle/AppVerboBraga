from pathlib import Path
import re
import sys

ROOT = Path.cwd()

AGENTS_UPPER_PATH = ROOT / "AGENTS.md"
AGENTS_TITLE_PATH = ROOT / "Agents.md"
TEMPLATE_PATH = ROOT / "templates" / "new_user.html"
CSS_PATH = ROOT / "static" / "css" / "modules" / "sidebar_sections_layout_v1.css"
JS_PATH = ROOT / "static" / "js" / "modules" / "sidebar_sections_layout_v1.js"

AGENTS_MARKER_START = "<!-- APPVERBO_CREATE_CARD_NO_EMPTY_TOP_SPACE_V7_START -->"
AGENTS_MARKER_END = "<!-- APPVERBO_CREATE_CARD_NO_EMPTY_TOP_SPACE_V7_END -->"

CSS_MARKER_START = "/* APPVERBO_SESSOES_CREATE_CARD_NO_EMPTY_TOP_SPACE_V7_START */"
CSS_MARKER_END = "/* APPVERBO_SESSOES_CREATE_CARD_NO_EMPTY_TOP_SPACE_V7_END */"

JS_CACHE = "/static/js/modules/sidebar_sections_layout_v1.js?v=20260505-sessoes-no-empty-top-v7"
CSS_CACHE = "/static/css/modules/sidebar_sections_layout_v1.css?v=20260505-sessoes-no-empty-top-v7"


def fail_v7(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


####################################################################################
# (1) RESOLVER AGENTS.md
####################################################################################

def resolve_agents_path_v7() -> Path:
    if AGENTS_UPPER_PATH.exists():
        return AGENTS_UPPER_PATH

    if AGENTS_TITLE_PATH.exists():
        return AGENTS_TITLE_PATH

    AGENTS_UPPER_PATH.write_text("# AGENTS.md\n\n", encoding="utf-8")
    return AGENTS_UPPER_PATH


####################################################################################
# (2) ATUALIZAR REGRA GLOBAL NO AGENTS.md
####################################################################################

agents_path = resolve_agents_path_v7()
agents_content = agents_path.read_text(encoding="utf-8")

agents_rule = f"""{AGENTS_MARKER_START}
## Regra para evitar espaço vazio no bloco/card de criação

Quando o botão **Criar + nome** abre o formulário dentro do bloco/card de criação:

1. O espaço reservado ao botão oculto não deve continuar ocupando altura.
2. Os campos do formulário devem começar no topo útil do bloco/card.
3. Não deve existir faixa vazia acima dos campos.
4. Não deve existir borda/linha horizontal separando uma toolbar vazia dos campos.
5. Quando o formulário estiver fechado, o botão **Criar + nome** deve continuar alinhado à esquerda e centralizado verticalmente.
6. Quando o formulário estiver aberto, apenas os campos e os botões **Guardar** e **Cancelar** devem ocupar o bloco/card.
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

print(f"OK: regra de remoção de espaço vazio atualizada em {agents_path}")


####################################################################################
# (3) VALIDAR FICHEIROS
####################################################################################

for file_path in [TEMPLATE_PATH, CSS_PATH, JS_PATH]:
    if not file_path.exists():
        fail_v7(f"ficheiro não encontrado: {file_path}")


####################################################################################
# (4) ATUALIZAR CSS PARA REMOVER ESPACO ACIMA DOS CAMPOS
####################################################################################

css_content = CSS_PATH.read_text(encoding="utf-8")

css_block = f'''{CSS_MARKER_START}

#admin-sidebar-sections-create-card .appverbo-create-entry-open-btn-v1[hidden],
#admin-sidebar-sections-create-card .appverbo-create-entry-toolbar-v1:has(.appverbo-create-entry-open-btn-v1[hidden]) {{
  display: none !important;
  height: 0 !important;
  min-height: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
  overflow: hidden !important;
}}

#admin-sidebar-sections-create-card .appverbo-create-entry-panel-v1:not([hidden]),
#admin-sidebar-sections-create-card .appverbo-create-entry-panel-v6:not([hidden]) {{
  margin-top: 0 !important;
  padding-top: 0 !important;
  border-top: 0 !important;
}}

#admin-sidebar-sections-create-card .appverbo-create-entry-block-v1 {{
  padding-top: 0 !important;
}}

#admin-sidebar-sections-create-card .appverbo-create-entry-grid-v5,
#admin-sidebar-sections-create-card .appverbo-create-entry-grid-v6 {{
  margin-top: 0 !important;
}}

#admin-sidebar-sections-create-card.appverbo-sessoes-create-card-v3 {{
  align-items: flex-start !important;
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

print("OK: CSS atualizado para remover espaço vazio acima dos campos.")


####################################################################################
# (5) ATUALIZAR CACHE BUSTER
####################################################################################

template_content = TEMPLATE_PATH.read_text(encoding="utf-8")

if "static/js/modules/sidebar_sections_layout_v1.js" in template_content:
    template_content = re.sub(
        r"/static/js/modules/sidebar_sections_layout_v1\.js\?v=[^\"]+",
        JS_CACHE,
        template_content,
    )
else:
    fail_v7("não encontrei sidebar_sections_layout_v1.js no template.")

if "static/css/modules/sidebar_sections_layout_v1.css" in template_content:
    template_content = re.sub(
        r"/static/css/modules/sidebar_sections_layout_v1\.css\?v=[^\"]+",
        CSS_CACHE,
        template_content,
    )
else:
    fail_v7("não encontrei sidebar_sections_layout_v1.css no template.")

TEMPLATE_PATH.write_text(template_content, encoding="utf-8")

print("OK: cache buster atualizado.")


####################################################################################
# (6) VALIDAR CONTEUDO
####################################################################################

agents_validado = agents_path.read_text(encoding="utf-8")
css_validado = CSS_PATH.read_text(encoding="utf-8")
template_validado = TEMPLATE_PATH.read_text(encoding="utf-8")

validacoes = {
    "APPVERBO_CREATE_CARD_NO_EMPTY_TOP_SPACE_V7_START": agents_validado,
    "espaço reservado ao botão oculto": agents_validado,
    "APPVERBO_SESSOES_CREATE_CARD_NO_EMPTY_TOP_SPACE_V7_START": css_validado,
    ".appverbo-create-entry-toolbar-v1:has": css_validado,
    ".appverbo-create-entry-panel-v1:not([hidden])": css_validado,
    "border-top: 0 !important": css_validado,
    "20260505-sessoes-no-empty-top-v7": template_validado,
}

for termo, conteudo in validacoes.items():
    if termo not in conteudo:
        fail_v7(f"validação falhou, termo ausente: {termo}")

print("OK: patch_sessoes_remover_espaco_topo_criacao_v7 concluído.")
