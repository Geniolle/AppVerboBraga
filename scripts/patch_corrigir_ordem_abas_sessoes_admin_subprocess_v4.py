from pathlib import Path
import re
import sys

ROOT = Path.cwd()

AGENTS_UPPER_PATH = ROOT / "AGENTS.md"
AGENTS_TITLE_PATH = ROOT / "Agents.md"
TEMPLATE_PATH = ROOT / "templates" / "new_user.html"
MACRO_PATH = ROOT / "templates" / "macros" / "admin_subprocess.html"
ADMIN_CSS_PATH = ROOT / "static" / "css" / "modules" / "admin_subprocesses_v1.css"
ADMIN_JS_PATH = ROOT / "static" / "js" / "modules" / "admin_subprocesses_v1.js"

AGENTS_MARKER_START = "<!-- APPVERBO_CORRIGIR_ORDEM_ABAS_SESSOES_ADMIN_SUBPROCESS_V4_START -->"
AGENTS_MARKER_END = "<!-- APPVERBO_CORRIGIR_ORDEM_ABAS_SESSOES_ADMIN_SUBPROCESS_V4_END -->"

TEMPLATE_MARKER_START = "<!-- APPVERBO_CORRIGIR_ORDEM_ABAS_SESSOES_ADMIN_SUBPROCESS_V4_START -->"
TEMPLATE_MARKER_END = "<!-- APPVERBO_CORRIGIR_ORDEM_ABAS_SESSOES_ADMIN_SUBPROCESS_V4_END -->"

ADMIN_CSS_CACHE = "/static/css/modules/admin_subprocesses_v1.css?v=20260505-corrigir-ordem-abas-sessoes-v4"
ADMIN_JS_CACHE = "/static/js/modules/admin_subprocesses_v1.js?v=20260505-corrigir-ordem-abas-sessoes-v4"

OLD_TEMPLATE_MARKERS = [
    ("<!-- APPVERBO_MIGRAR_SESSOES_ADMIN_SUBPROCESS_V2_START -->", "<!-- APPVERBO_MIGRAR_SESSOES_ADMIN_SUBPROCESS_V2_END -->"),
    ("<!-- APPVERBO_CORRIGIR_ORDEM_ABAS_SESSOES_ADMIN_SUBPROCESS_V3_START -->", "<!-- APPVERBO_CORRIGIR_ORDEM_ABAS_SESSOES_ADMIN_SUBPROCESS_V3_END -->"),
    (TEMPLATE_MARKER_START, TEMPLATE_MARKER_END),
    ("<!-- APPVERBO_SESSOES_SERVER_RENDER_IGUAL_ENTIDADE_V25_START -->", "<!-- APPVERBO_SESSOES_SERVER_RENDER_IGUAL_ENTIDADE_V25_END -->"),
    ("<!-- APPVERBO_SESSOES_SERVER_RENDER_UNICO_V28_START -->", "<!-- APPVERBO_SESSOES_SERVER_RENDER_UNICO_V28_END -->"),
    ("<!-- APPVERBO_SESSOES_CORRIGIR_V28_REMOVER_DUPLICADOS_V29_START -->", "<!-- APPVERBO_SESSOES_CORRIGIR_V28_REMOVER_DUPLICADOS_V29_END -->"),
    ("<!-- APPVERBO_SESSOES_FLUXO_NATIVO_IGUAL_ENTIDADE_V30_START -->", "<!-- APPVERBO_SESSOES_FLUXO_NATIVO_IGUAL_ENTIDADE_V30_END -->"),
]


def fail_v4(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


def read_text_v4(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text_v4(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
    print(f"OK: escrito {path}")


def resolve_agents_path_v4() -> Path:
    if AGENTS_UPPER_PATH.exists():
        return AGENTS_UPPER_PATH

    if AGENTS_TITLE_PATH.exists():
        return AGENTS_TITLE_PATH

    AGENTS_UPPER_PATH.write_text("# AGENTS.md\n\n", encoding="utf-8")
    return AGENTS_UPPER_PATH


def strip_trailing_whitespace_v4(content: str) -> str:
    return "\n".join(line.rstrip() for line in content.splitlines()) + "\n"


def remove_marked_block_v4(content: str, start_marker: str, end_marker: str) -> str:
    while start_marker in content and end_marker in content:
        content = re.sub(
            re.escape(start_marker) + r"[\s\S]*?" + re.escape(end_marker),
            "",
            content,
            count=1,
        )

    return content


def find_section_bounds_by_id_v4(content: str, section_id: str) -> tuple[int, int]:
    pattern = re.compile(
        r"<section\b[^>]*\bid=[\"']" + re.escape(section_id) + r"[\"'][^>]*>",
        re.IGNORECASE,
    )

    match = pattern.search(content)

    if not match:
        fail_v4(f"section #{section_id} não encontrada.")

    start = match.start()
    cursor = match.end()
    depth = 1
    token_pattern = re.compile(r"</?section\b[^>]*>", re.IGNORECASE)

    for token in token_pattern.finditer(content, cursor):
        token_text = token.group(0).lower()

        if token_text.startswith("</section"):
            depth -= 1

            if depth == 0:
                return start, token.end()
        else:
            depth += 1

    fail_v4(f"não encontrei fechamento da section #{section_id}.")


def remove_section_by_id_v4(content: str, section_id: str) -> str:
    pattern = re.compile(
        r"<section\b[^>]*\bid=[\"']" + re.escape(section_id) + r"[\"'][^>]*>",
        re.IGNORECASE,
    )

    while pattern.search(content):
        start, end = find_section_bounds_by_id_v4(content, section_id)
        content = content[:start] + content[end:]

    return content


def remove_sections_containing_v4(content: str, patterns: list[str]) -> str:
    section_pattern = re.compile(r"<section\b[\s\S]*?</section>", re.IGNORECASE)

    changed = True

    while changed:
        changed = False

        for match in list(section_pattern.finditer(content)):
            block = match.group(0)

            if any(pattern in block for pattern in patterns):
                content = content[:match.start()] + content[match.end():]
                changed = True
                break

    return content


def ensure_macro_import_v4(content: str) -> str:
    macro_import = '{% from "macros/admin_subprocess.html" import render_admin_subprocess_state %}'

    if macro_import in content:
        return content

    extends_match = re.search(r"({%\s*extends[^\n]+%}\s*)", content)

    if extends_match:
        return content[:extends_match.end()] + "\n" + macro_import + "\n" + content[extends_match.end():]

    return macro_import + "\n" + content


def ensure_head_asset_v4(content: str, asset_html: str, asset_name: str) -> str:
    content = re.sub(
        r"\s*<link[^>]+href=[\"'][^\"']*" + re.escape(asset_name) + r"[^\"']*[\"'][^>]*>",
        "",
        content,
    )

    content = re.sub(
        r"\s*<script[^>]+src=[\"'][^\"']*" + re.escape(asset_name) + r"[^\"']*[\"'][^>]*>\s*</script>",
        "",
        content,
    )

    head_match = re.search(r"({%\s*block\s+head_extra\s*%})([\s\S]*?)({%\s*endblock\s*%})", content)

    if head_match:
        start = head_match.start(3)
        return content[:start] + "  " + asset_html + "\n" + content[start:]

    if "</head>" in content:
        return content.replace("</head>", "  " + asset_html + "\n</head>", 1)

    fail_v4(f"não encontrei local para inserir asset: {asset_name}")


####################################################################################
# (1) VALIDAR FICHEIROS
####################################################################################

for file_path in [TEMPLATE_PATH, MACRO_PATH, ADMIN_CSS_PATH, ADMIN_JS_PATH]:
    if not file_path.exists():
        fail_v4(f"ficheiro obrigatório não encontrado: {file_path}")


####################################################################################
# (2) CORRIGIR TEMPLATE: ABAS PRIMEIRO, SESSOES DEPOIS
####################################################################################

template_content = read_text_v4(TEMPLATE_PATH)
template_content = strip_trailing_whitespace_v4(template_content)

for start_marker, end_marker in OLD_TEMPLATE_MARKERS:
    template_content = remove_marked_block_v4(template_content, start_marker, end_marker)

for section_id in [
    "admin-sidebar-sections-form-card",
    "admin-sidebar-sections-create-card",
    "admin-sidebar-sections-card",
    "admin-sidebar-sections-inactive-card",
]:
    template_content = remove_section_by_id_v4(template_content, section_id)

template_content = remove_sections_containing_v4(
    template_content,
    [
        'data-admin-subprocess="sessoes"',
        "data-admin-subprocess='sessoes'",
        "appverbo-sessoes-card",
        "appverbo-sessoes-list-card",
        "appverbo-sessoes-inactive-card",
        "Sessões do sidebar",
        "Sessões ativas",
        "Sessões inativas",
    ],
)

template_content = ensure_macro_import_v4(template_content)

tabs_start, tabs_end = find_section_bounds_by_id_v4(template_content, "menu-tabs-card")

template_block = f'''
        {TEMPLATE_MARKER_START}
        {{% if admin_tab == "sessoes" and admin_subprocess_state %}}
          {{{{ render_admin_subprocess_state(admin_subprocess_state) }}}}
        {{% endif %}}
        {TEMPLATE_MARKER_END}
'''

template_content = template_content[:tabs_end] + template_block + template_content[tabs_end:]

template_content = ensure_head_asset_v4(
    template_content,
    f'<link rel="stylesheet" href="{ADMIN_CSS_CACHE}">',
    "admin_subprocesses_v1.css",
)

template_content = ensure_head_asset_v4(
    template_content,
    f'<script src="{ADMIN_JS_CACHE}" defer></script>',
    "admin_subprocesses_v1.js",
)

template_content = strip_trailing_whitespace_v4(template_content)
write_text_v4(TEMPLATE_PATH, template_content)


####################################################################################
# (3) ATUALIZAR AGENTS.md
####################################################################################

agents_path = resolve_agents_path_v4()
agents_content = read_text_v4(agents_path)

agents_rule = f"""{AGENTS_MARKER_START}
## Ordem definitiva da aba Sessões

Na aba **Sessões**, a ordem visual correta é:

1. Primeiro o card central de ABAS (`menu-tabs-card`);
2. Depois o bloco do subprocesso renderizado por `render_admin_subprocess_state(admin_subprocess_state)`;
3. Nenhum bloco de Sessões pode ficar antes do card de ABAS;
4. Não devem existir sections manuais antigas com:
   - `admin-sidebar-sections-form-card`;
   - `admin-sidebar-sections-card`;
   - `admin-sidebar-sections-inactive-card`;
   - classes `appverbo-sessoes-*`;
5. A renderização de Sessões deve depender de `admin_tab == "sessoes"` e `admin_subprocess_state`.
{AGENTS_MARKER_END}"""

agents_content = remove_marked_block_v4(agents_content, AGENTS_MARKER_START, AGENTS_MARKER_END)
agents_content = agents_content.rstrip() + "\n\n" + agents_rule + "\n"

write_text_v4(agents_path, agents_content)


####################################################################################
# (4) VALIDAR RESULTADO
####################################################################################

template_validado = read_text_v4(TEMPLATE_PATH)
agents_validado = read_text_v4(agents_path)

if TEMPLATE_MARKER_START not in template_validado:
    fail_v4("marcador V4 ausente no template.")

if "render_admin_subprocess_state(admin_subprocess_state)" not in template_validado:
    fail_v4("macro render_admin_subprocess_state ausente no template.")

if ADMIN_CSS_CACHE not in template_validado:
    fail_v4("CSS admin_subprocesses_v1.css V4 não foi incluído no template.")

if ADMIN_JS_CACHE not in template_validado:
    fail_v4("JS admin_subprocesses_v1.js V4 não foi incluído no template.")

tabs_start_validado, tabs_end_validado = find_section_bounds_by_id_v4(template_validado, "menu-tabs-card")
macro_index_validado = template_validado.find(TEMPLATE_MARKER_START)

if macro_index_validado < tabs_end_validado:
    fail_v4("o bloco de Sessões ainda está antes ou dentro do menu-tabs-card.")

for forbidden in [
    'id="admin-sidebar-sections-form-card"',
    "id='admin-sidebar-sections-form-card'",
    'id="admin-sidebar-sections-card"',
    "id='admin-sidebar-sections-card'",
    'id="admin-sidebar-sections-inactive-card"',
    "id='admin-sidebar-sections-inactive-card'",
    "appverbo-sessoes-card",
    "Sessões do sidebar",
]:
    if forbidden in template_validado:
        fail_v4(f"conteúdo antigo ainda existe no template: {forbidden}")

if AGENTS_MARKER_START not in agents_validado:
    fail_v4("AGENTS.md não recebeu regra V4.")

print("OK: patch_corrigir_ordem_abas_sessoes_admin_subprocess_v4 concluído.")
