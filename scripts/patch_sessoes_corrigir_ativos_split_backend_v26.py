from pathlib import Path
import ast
import re
import sys

ROOT = Path.cwd()

AGENTS_UPPER_PATH = ROOT / "AGENTS.md"
AGENTS_TITLE_PATH = ROOT / "Agents.md"
PAGE_HANDLER_PATH = ROOT / "appverbo" / "routes" / "profile" / "page_handler.py"
TEMPLATE_PATH = ROOT / "templates" / "new_user.html"
CSS_PATH = ROOT / "static" / "css" / "modules" / "sidebar_sections_layout_v1.css"
JS_PATH = ROOT / "static" / "js" / "modules" / "sidebar_sections_layout_v1.js"

AGENTS_MARKER_START = "<!-- APPVERBO_SESSOES_CORRIGIR_ATIVOS_SPLIT_BACKEND_V26_START -->"
AGENTS_MARKER_END = "<!-- APPVERBO_SESSOES_CORRIGIR_ATIVOS_SPLIT_BACKEND_V26_END -->"

PAGE_MARKER_START = "# APPVERBO_SESSOES_CORRIGIR_ATIVOS_SPLIT_BACKEND_V26_START"
PAGE_MARKER_END = "# APPVERBO_SESSOES_CORRIGIR_ATIVOS_SPLIT_BACKEND_V26_END"

CSS_MARKER_START = "/* APPVERBO_SESSOES_CORRIGIR_ATIVOS_SPLIT_BACKEND_V26_START */"
CSS_MARKER_END = "/* APPVERBO_SESSOES_CORRIGIR_ATIVOS_SPLIT_BACKEND_V26_END */"

JS_CACHE = "/static/js/modules/sidebar_sections_layout_v1.js?v=20260505-sessoes-corrigir-ativos-split-backend-v26"
CSS_CACHE = "/static/css/modules/sidebar_sections_layout_v1.css?v=20260505-sessoes-corrigir-ativos-split-backend-v26"


def fail_v26(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


####################################################################################
# (1) RESOLVER AGENTS.md
####################################################################################

def resolve_agents_path_v26() -> Path:
    if AGENTS_UPPER_PATH.exists():
        return AGENTS_UPPER_PATH

    if AGENTS_TITLE_PATH.exists():
        return AGENTS_TITLE_PATH

    AGENTS_UPPER_PATH.write_text("# AGENTS.md\n\n", encoding="utf-8")
    return AGENTS_UPPER_PATH


####################################################################################
# (2) VALIDAR FICHEIROS
####################################################################################

for file_path in [PAGE_HANDLER_PATH, TEMPLATE_PATH, CSS_PATH, JS_PATH]:
    if not file_path.exists():
        fail_v26(f"ficheiro não encontrado: {file_path}")


####################################################################################
# (3) ATUALIZAR AGENTS.md
####################################################################################

agents_path = resolve_agents_path_v26()
agents_content = agents_path.read_text(encoding="utf-8")

agents_rule = f"""{AGENTS_MARKER_START}
## Correção do split backend das Sessões

Na aba **Sessões**, as listas devem ser separadas no backend antes do template.

Regras:

1. Recalcular sempre `active_sidebar_sections` e `inactive_sidebar_sections` a partir da configuração normalizada.
2. Uma sessão deve ser considerada inativa quando:
   - `is_active` for `false`; ou
   - `status` for `inativo`.
3. Uma sessão deve ser considerada ativa quando:
   - `is_active` for `true`; ou
   - `status` for `ativo`; ou
   - não existir estado explícito de inativo.
4. O template não deve depender de JavaScript para reconstruir as linhas.
5. O card **Sessões do sidebar** deve mostrar todas as sessões ativas.
6. O card **Sessões inativas** deve mostrar apenas as sessões inativas.
{AGENTS_MARKER_END}"""

if AGENTS_MARKER_START in agents_content and AGENTS_MARKER_END in agents_content:
    agents_content = re.sub(
        re.escape(AGENTS_MARKER_START) + r"[\s\S]*?" + re.escape(AGENTS_MARKER_END),
        agents_rule,
        agents_content,
        count=1,
    )
else:
    agents_content = agents_content.rstrip() + "\n\n" + agents_rule + "\n"

agents_path.write_text(agents_content, encoding="utf-8")

print(f"OK: AGENTS.md atualizado em {agents_path}")


####################################################################################
# (4) CORRIGIR SPLIT NO PAGE_HANDLER
####################################################################################

page_content = PAGE_HANDLER_PATH.read_text(encoding="utf-8-sig")

required_terms = [
    "_split_sidebar_sections_for_page_v22",
    "_resolve_sidebar_sections_from_page_data_v22",
    "_sidebar_section_is_active_for_page_v22",
    "active_sidebar_sections_v22",
    "inactive_sidebar_sections_v22",
]

for term in required_terms:
    if term not in page_content:
        fail_v26(f"termo esperado não encontrado no page_handler.py: {term}")

page_content = re.sub(
    re.escape(PAGE_MARKER_START) + r"[\s\S]*?" + re.escape(PAGE_MARKER_END) + r"\n*",
    "",
    page_content,
)

split_pattern = re.compile(
    r"(?P<full>"
    r"(?P<indent>[ \t]*)active_sidebar_sections_v22,\s*inactive_sidebar_sections_v22,\s*sidebar_section_edit_data_v22\s*=\s*_split_sidebar_sections_for_page_v22\(\s*\n"
    r"(?P=indent)[ \t]*page_data,\s*\n"
    r"(?P=indent)[ \t]*sidebar_section_edit_key,\s*\n"
    r"(?P=indent)[ \t]*\)\s*\n"
    r")",
    re.MULTILINE,
)

match = split_pattern.search(page_content)

if not match:
    fail_v26("não encontrei o bloco de split active/inactive para inserir a correção V26.")

indent = match.group("indent")

fix_block = f'''{indent}{PAGE_MARKER_START}
{indent}# Recalcula a separação diretamente da configuração normalizada.
{indent}# Isto evita que o template receba a lista de ativos vazia quando houver fallback antigo.
{indent}all_sidebar_sections_v26 = _resolve_sidebar_sections_from_page_data_v22(page_data)
{indent}
{indent}if all_sidebar_sections_v26:
{indent}    active_sidebar_sections_v22 = [
{indent}        section
{indent}        for section in all_sidebar_sections_v26
{indent}        if _sidebar_section_is_active_for_page_v22(section)
{indent}    ]
{indent}    inactive_sidebar_sections_v22 = [
{indent}        section
{indent}        for section in all_sidebar_sections_v26
{indent}        if not _sidebar_section_is_active_for_page_v22(section)
{indent}    ]
{indent}
{indent}    clean_sidebar_section_edit_key_v26 = str(sidebar_section_edit_key or "").strip().lower()
{indent}
{indent}    if clean_sidebar_section_edit_key_v26:
{indent}        sidebar_section_edit_data_v22 = next(
{indent}            (
{indent}                dict(section)
{indent}                for section in all_sidebar_sections_v26
{indent}                if str(section.get("key") or "").strip().lower() == clean_sidebar_section_edit_key_v26
{indent}            ),
{indent}            sidebar_section_edit_data_v22,
{indent}        )
{indent}{PAGE_MARKER_END}
'''

page_content = page_content[:match.end()] + fix_block + page_content[match.end():]

context_anchor = '''        "admin_tab": resolved_admin_tab,
'''

context_insert = '''        "sidebar_section_edit_key": str(sidebar_section_edit_key or "").strip().lower(),
        "sidebar_section_edit_data": sidebar_section_edit_data_v22,
        "active_sidebar_sections": active_sidebar_sections_v22,
        "inactive_sidebar_sections": inactive_sidebar_sections_v22,
'''

if '"active_sidebar_sections": active_sidebar_sections_v22,' not in page_content:
    if context_anchor not in page_content:
        fail_v26("não encontrei local para inserir active_sidebar_sections no contexto.")

    page_content = page_content.replace(context_anchor, context_insert + context_anchor, 1)

try:
    ast.parse(page_content)
except SyntaxError as exc:
    fail_v26(f"page_handler.py ficaria inválido: {exc}")

PAGE_HANDLER_PATH.write_text(page_content, encoding="utf-8")

print("OK: page_handler.py corrigido para recalcular ativos/inativos no backend.")


####################################################################################
# (5) GARANTIR CACHE BUSTER NO TEMPLATE
####################################################################################

template_content = TEMPLATE_PATH.read_text(encoding="utf-8")

if "static/js/modules/sidebar_sections_layout_v1.js" in template_content:
    template_content = re.sub(
        r"/static/js/modules/sidebar_sections_layout_v1\.js\?v=[^\"]+",
        JS_CACHE,
        template_content,
    )
else:
    fail_v26("não encontrei sidebar_sections_layout_v1.js no template.")

if "static/css/modules/sidebar_sections_layout_v1.css" in template_content:
    template_content = re.sub(
        r"/static/css/modules/sidebar_sections_layout_v1\.css\?v=[^\"]+",
        CSS_CACHE,
        template_content,
    )
else:
    fail_v26("não encontrei sidebar_sections_layout_v1.css no template.")

TEMPLATE_PATH.write_text(template_content, encoding="utf-8")

print("OK: cache buster atualizado no template.")


####################################################################################
# (6) REFORCAR CSS PARA MOSTRAR CARD ATIVO E INATIVO
####################################################################################

css_content = CSS_PATH.read_text(encoding="utf-8")

css_block = f'''{CSS_MARKER_START}

body:has(a[href*="admin_tab=sessoes"]) #admin-sidebar-sections-card.appverbo-sessoes-list-card-v25,
body:has(a[href*="admin_tab=sessoes"]) #admin-sidebar-sections-inactive-card.appverbo-sessoes-inactive-card-v25,
body:has(a[href*="admin_tab=sessoes"]) #admin-sidebar-sections-form-card.appverbo-sessoes-form-card-v25 {{
  visibility: visible;
}}

#admin-sidebar-sections-card.appverbo-sessoes-list-card-v25 {{
  min-height: 1px !important;
}}

#admin-sidebar-sections-card.appverbo-sessoes-list-card-v25 .appverbo-sessoes-table-v25 tbody tr {{
  display: table-row !important;
}}

#admin-sidebar-sections-card.appverbo-sessoes-list-card-v25 .empty {{
  color: #52607a !important;
}}

{CSS_MARKER_END}'''

if CSS_MARKER_START in css_content and CSS_MARKER_END in css_content:
    css_content = re.sub(
        re.escape(CSS_MARKER_START) + r"[\s\S]*?" + re.escape(CSS_MARKER_END),
        css_block,
        css_content,
        count=1,
    )
else:
    css_content = css_content.rstrip() + "\n\n" + css_block + "\n"

CSS_PATH.write_text(css_content, encoding="utf-8")

print("OK: CSS V26 aplicado.")


####################################################################################
# (7) VALIDAR CONTEUDO
####################################################################################

agents_validado = agents_path.read_text(encoding="utf-8")
page_validado = PAGE_HANDLER_PATH.read_text(encoding="utf-8")
template_validado = TEMPLATE_PATH.read_text(encoding="utf-8")
css_validado = CSS_PATH.read_text(encoding="utf-8")

validacoes = {
    "APPVERBO_SESSOES_CORRIGIR_ATIVOS_SPLIT_BACKEND_V26_START": agents_validado,
    "APPVERBO_SESSOES_CORRIGIR_ATIVOS_SPLIT_BACKEND_V26_START": page_validado,
    "all_sidebar_sections_v26": page_validado,
    "active_sidebar_sections_v22 = [": page_validado,
    "inactive_sidebar_sections_v22 = [": page_validado,
    '"active_sidebar_sections": active_sidebar_sections_v22': page_validado,
    '"inactive_sidebar_sections": inactive_sidebar_sections_v22': page_validado,
    "20260505-sessoes-corrigir-ativos-split-backend-v26": template_validado,
    "APPVERBO_SESSOES_CORRIGIR_ATIVOS_SPLIT_BACKEND_V26_START": css_validado,
}

for termo, conteudo in validacoes.items():
    if termo not in conteudo:
        fail_v26(f"validação falhou, termo ausente: {termo}")

try:
    ast.parse(page_validado)
except SyntaxError as exc:
    fail_v26(f"Python final inválido: {exc}")

print("OK: patch_sessoes_corrigir_ativos_split_backend_v26 concluído.")
