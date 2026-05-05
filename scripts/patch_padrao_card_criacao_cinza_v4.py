from pathlib import Path
import re
import sys

ROOT = Path.cwd()

AGENTS_UPPER_PATH = ROOT / "AGENTS.md"
AGENTS_TITLE_PATH = ROOT / "Agents.md"
TEMPLATE_PATH = ROOT / "templates" / "new_user.html"
NEW_USER_CSS_PATH = ROOT / "static" / "css" / "new_user.css"
UI_STANDARDS_CSS_PATH = ROOT / "static" / "css" / "ui-standards.css"
SESSOES_CSS_PATH = ROOT / "static" / "css" / "modules" / "sidebar_sections_layout_v1.css"
SESSOES_JS_PATH = ROOT / "static" / "js" / "modules" / "sidebar_sections_layout_v1.js"

AGENTS_MARKER_START = "<!-- APPVERBO_CREATE_CARD_STANDARD_RULE_V4_START -->"
AGENTS_MARKER_END = "<!-- APPVERBO_CREATE_CARD_STANDARD_RULE_V4_END -->"

CSS_MARKER_START = "/* APPVERBO_CREATE_CARD_STANDARD_V4_START */"
CSS_MARKER_END = "/* APPVERBO_CREATE_CARD_STANDARD_V4_END */"

JS_CACHE = "/static/js/modules/sidebar_sections_layout_v1.js?v=20260505-create-card-standard-v4"
SESSOES_CSS_CACHE = "/static/css/modules/sidebar_sections_layout_v1.css?v=20260505-create-card-standard-v4"
NEW_USER_CSS_CACHE = "/static/css/new_user.css?v=20260505-create-card-standard-v4"


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
# (2) ATUALIZAR AGENTS.md COM REGRA GERAL DO CARD DE CRIACAO
####################################################################################

agents_path = resolve_agents_path_v4()
agents_content = agents_path.read_text(encoding="utf-8")

agents_rule = f"""{AGENTS_MARKER_START}
## Regra global para card/bloco de criação

Sempre que uma aba, subprocesso ou lista administrativa tiver a opção de criar uma nova entrada:

1. O botão **Criar + nome da aba/processo** deve ficar em um card/bloco separado acima da tabela/lista.
2. Esse card/bloco deve seguir o padrão visual da aba **Entidade**:
   - fundo cinza claro;
   - borda suave;
   - cantos arredondados;
   - altura mínima padronizada;
   - botão alinhado à esquerda e centralizado verticalmente.
3. O tamanho padrão do card/bloco de criação deve ser:
   - largura: 100% do container;
   - altura mínima: 64px;
   - padding horizontal e vertical: 16px;
   - margem inferior: 12px.
4. O botão **Criar + nome** deve ficar sempre à esquerda.
5. Ao clicar no botão, os campos de criação devem abrir dentro do mesmo card/bloco.
6. Os botões **Guardar** e **Cancelar** devem ficar dentro do mesmo card/bloco, sempre à esquerda e com o mesmo tamanho.
7. A tabela/lista inferior deve ficar em outro card separado, exibindo apenas os registos já criados.
8. Este padrão é global e deve ser reaproveitado em todas as abas que tenham ação de criação.
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

print(f"OK: regra global do card de criação atualizada em {agents_path}")


####################################################################################
# (3) DEFINIR CSS GLOBAL DO CARD DE CRIACAO
####################################################################################

standard_css = f"""{CSS_MARKER_START}

:root {{
  --appverbo-create-card-background-v4: #f3f6fb;
  --appverbo-create-card-border-v4: #d5dceb;
  --appverbo-create-card-radius-v4: 12px;
  --appverbo-create-card-min-height-v4: 64px;
  --appverbo-create-card-padding-v4: 16px;
  --appverbo-create-card-margin-bottom-v4: 12px;
}}

.appverbo-standard-create-card-v4,
.entity-create-toolbar,
.appverbo-sessoes-create-card-v3,
#admin-sidebar-sections-create-card {{
  width: 100% !important;
  min-height: var(--appverbo-create-card-min-height-v4) !important;
  padding: var(--appverbo-create-card-padding-v4) !important;
  margin: 0 0 var(--appverbo-create-card-margin-bottom-v4) !important;
  border: 1px solid var(--appverbo-create-card-border-v4) !important;
  border-radius: var(--appverbo-create-card-radius-v4) !important;
  background: var(--appverbo-create-card-background-v4) !important;
  box-sizing: border-box !important;
  display: flex !important;
  align-items: center !important;
  justify-content: flex-start !important;
}}

.appverbo-standard-create-card-v4 > *,
.entity-create-toolbar > *,
.appverbo-sessoes-create-card-v3 > *,
#admin-sidebar-sections-create-card > * {{
  flex: 0 0 auto;
}}

.appverbo-standard-create-card-v4 .action-btn,
.entity-create-toolbar .action-btn,
.appverbo-sessoes-create-card-v3 .action-btn,
#admin-sidebar-sections-create-card .action-btn {{
  align-self: center !important;
}}

.appverbo-sessoes-create-card-v3 .appverbo-create-entry-block-v1,
#admin-sidebar-sections-create-card .appverbo-create-entry-block-v1 {{
  width: 100% !important;
  margin: 0 !important;
  padding: 0 !important;
  border: 0 !important;
  background: transparent !important;
  border-radius: 0 !important;
  box-sizing: border-box !important;
}}

.appverbo-sessoes-create-card-v3 .appverbo-create-entry-toolbar-v1,
#admin-sidebar-sections-create-card .appverbo-create-entry-toolbar-v1 {{
  min-height: 32px !important;
  display: flex !important;
  align-items: center !important;
  justify-content: flex-start !important;
  gap: 8px !important;
}}

.appverbo-sessoes-create-card-v3 .appverbo-create-entry-panel-v1,
#admin-sidebar-sections-create-card .appverbo-create-entry-panel-v1 {{
  width: 100% !important;
  margin-top: 14px !important;
  padding-top: 14px !important;
  border-top: 1px solid var(--appverbo-create-card-border-v4) !important;
}}

{CSS_MARKER_END}"""


def upsert_css_block_v4(css_path: Path) -> None:
    if not css_path.exists():
        print(f"AVISO: CSS não encontrado, ignorado: {css_path}")
        return

    css_content = css_path.read_text(encoding="utf-8")

    if CSS_MARKER_START in css_content and CSS_MARKER_END in css_content:
        css_pattern = re.compile(
            re.escape(CSS_MARKER_START) + r"[\s\S]*?" + re.escape(CSS_MARKER_END),
            re.S,
        )
        css_content = css_pattern.sub(standard_css, css_content, count=1)
    else:
        css_content = css_content.rstrip() + "\n\n" + standard_css + "\n"

    css_path.write_text(css_content, encoding="utf-8")
    print(f"OK: padrão visual do card de criação aplicado em {css_path}")


upsert_css_block_v4(NEW_USER_CSS_PATH)
upsert_css_block_v4(UI_STANDARDS_CSS_PATH)
upsert_css_block_v4(SESSOES_CSS_PATH)


####################################################################################
# (4) GARANTIR CLASSE PADRAO NO CARD CRIADO PELA ABA SESSOES
####################################################################################

if not SESSOES_JS_PATH.exists():
    fail_v4(f"JS de Sessões não encontrado: {SESSOES_JS_PATH}")

sessoes_js = SESSOES_JS_PATH.read_text(encoding="utf-8")

old_class = 'createCard.className = "card appverbo-sessoes-create-card-v3";'
new_class = 'createCard.className = "card appverbo-standard-create-card-v4 appverbo-sessoes-create-card-v3";'

if old_class in sessoes_js:
    sessoes_js = sessoes_js.replace(old_class, new_class, 1)
elif new_class not in sessoes_js:
    fail_v4("não encontrei a criação do card de Sessões para aplicar a classe padrão.")

SESSOES_JS_PATH.write_text(sessoes_js, encoding="utf-8")

print("OK: JS de Sessões atualizado com classe global do card de criação.")


####################################################################################
# (5) ATUALIZAR CACHE BUSTER NO TEMPLATE
####################################################################################

if not TEMPLATE_PATH.exists():
    fail_v4(f"template não encontrado: {TEMPLATE_PATH}")

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
        SESSOES_CSS_CACHE,
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
else:
    print("AVISO: static/css/new_user.css não encontrado no template para cache buster.")

TEMPLATE_PATH.write_text(template_content, encoding="utf-8")

print("OK: cache buster atualizado no template.")


####################################################################################
# (6) VALIDAR CONTEUDO
####################################################################################

agents_validado = agents_path.read_text(encoding="utf-8")
sessoes_css_validado = SESSOES_CSS_PATH.read_text(encoding="utf-8")
sessoes_js_validado = SESSOES_JS_PATH.read_text(encoding="utf-8")
template_validado = TEMPLATE_PATH.read_text(encoding="utf-8")

validacoes = {
    "APPVERBO_CREATE_CARD_STANDARD_RULE_V4_START": agents_validado,
    "fundo cinza claro": agents_validado,
    "altura mínima: 64px": agents_validado,
    "APPVERBO_CREATE_CARD_STANDARD_V4_START": sessoes_css_validado,
    "--appverbo-create-card-background-v4: #f3f6fb;": sessoes_css_validado,
    "--appverbo-create-card-min-height-v4: 64px;": sessoes_css_validado,
    "appverbo-standard-create-card-v4": sessoes_js_validado,
    "20260505-create-card-standard-v4": template_validado,
}

for termo, conteudo in validacoes.items():
    if termo not in conteudo:
        fail_v4(f"validação falhou, termo ausente: {termo}")

if NEW_USER_CSS_PATH.exists():
    new_user_css_validado = NEW_USER_CSS_PATH.read_text(encoding="utf-8")
    if "APPVERBO_CREATE_CARD_STANDARD_V4_START" not in new_user_css_validado:
        fail_v4("padrão global não foi aplicado em static/css/new_user.css.")

print("OK: padrão cinza e tamanho global do card de criação aplicado.")
