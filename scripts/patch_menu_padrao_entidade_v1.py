from pathlib import Path
import re
import sys

ROOT = Path.cwd()

AGENTS_UPPER_PATH = ROOT / "AGENTS.md"
AGENTS_TITLE_PATH = ROOT / "Agents.md"
UI_STANDARDS_CSS_PATH = ROOT / "static" / "css" / "ui-standards.css"

AGENTS_MARKER_START = "<!-- APPVERBO_MENU_STANDARD_RULE_V1_START -->"
AGENTS_MARKER_END = "<!-- APPVERBO_MENU_STANDARD_RULE_V1_END -->"

CSS_MARKER_START = "/* APPVERBO_MENU_CREATE_CARD_STANDARD_V1_START */"
CSS_MARKER_END = "/* APPVERBO_MENU_CREATE_CARD_STANDARD_V1_END */"

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
# (2) ATUALIZAR AGENTS.md COM A REGRA DO MENU
####################################################################################
agents_path = resolve_agents_path_v1()
agents_content = agents_path.read_text(encoding="utf-8")

agents_rule = f"""{AGENTS_MARKER_START}
## Regra de Escopo e UI do subprocesso Menu

O botão **Criar menu** (ou item de menu) pertence exclusivamente ao subprocesso **Menu**.

1. O card de criação do Menu deve usar a classe global `appverbo-standard-create-card-v4` combinada com `appverbo-menu-create-card-v1`.
2. O ID do card deve ser `admin-menu-create-card`.
3. Quando a aba ativa for **Menu**, o card deve estar visível acima da tabela de menus.
4. O card deve possuir os botões **Guardar** e **Cancelar** (à esquerda, mesma largura).
5. Qualquer script de gestão do Menu deve escutar a aba ativa para montar ou esconder os seus orfãos.
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
print(f"OK: Regra do subprocesso Menu atualizada em {agents_path.name}")

####################################################################################
# (3) DEFINIR CSS DO MENU HERDANDO O PADRÃO V4
####################################################################################
menu_css = f"""{CSS_MARKER_START}
/* Estende o padrao V4 para o Menu */
.appverbo-menu-create-card-v1,
#admin-menu-create-card {{
  width: 100% !important;
  min-height: var(--appverbo-create-card-min-height-v4, 64px) !important;
  padding: var(--appverbo-create-card-padding-v4, 16px) !important;
  margin: 0 0 var(--appverbo-create-card-margin-bottom-v4, 12px) !important;
  border: 1px solid var(--appverbo-create-card-border-v4, #d5dceb) !important;
  border-radius: var(--appverbo-create-card-radius-v4, 12px) !important;
  background: var(--appverbo-create-card-background-v4, #f3f6fb) !important;
  box-sizing: border-box !important;
  display: flex !important;
  align-items: center !important;
  justify-content: flex-start !important;
}}

.appverbo-menu-create-card-v1 > *,
#admin-menu-create-card > * {{
  flex: 0 0 auto;
}}

body.appverbo-admin-menu-inactive-v1 #admin-menu-create-card {{
  display: none !important;
}}

body.appverbo-admin-menu-active-v1 #admin-menu-create-card {{
  display: flex !important;
}}
{CSS_MARKER_END}"""

def upsert_css_block(css_path: Path) -> None:
    if not css_path.exists():
        print(f"AVISO: CSS não encontrado, ignorado: {css_path}")
        return

    css_content = css_path.read_text(encoding="utf-8")
    if CSS_MARKER_START in css_content and CSS_MARKER_END in css_content:
        css_pattern = re.compile(re.escape(CSS_MARKER_START) + r"[\s\S]*?" + re.escape(CSS_MARKER_END), re.S)
        css_content = css_pattern.sub(menu_css, css_content, count=1)
    else:
        css_content = css_content.rstrip() + "\n\n" + menu_css + "\n"

    css_path.write_text(css_content, encoding="utf-8")
    print(f"OK: Padrão visual do Menu aplicado em {css_path.name}")

upsert_css_block(UI_STANDARDS_CSS_PATH)

print("OK: patch_menu_padrao_entidade_v1 concluído com sucesso!")