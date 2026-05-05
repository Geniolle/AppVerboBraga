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
SIDEBAR_CSS_PATH = ROOT / "static" / "css" / "modules" / "sidebar_sections_layout_v1.css"
SIDEBAR_JS_PATH = ROOT / "static" / "js" / "modules" / "sidebar_sections_layout_v1.js"

AGENTS_MARKER_START = "<!-- APPVERBO_CORRIGIR_ORDEM_ABAS_SESSOES_ADMIN_SUBPROCESS_V5_START -->"
AGENTS_MARKER_END = "<!-- APPVERBO_CORRIGIR_ORDEM_ABAS_SESSOES_ADMIN_SUBPROCESS_V5_END -->"

TEMPLATE_MARKER_START = "<!-- APPVERBO_CORRIGIR_ORDEM_ABAS_SESSOES_ADMIN_SUBPROCESS_V5_START -->"
TEMPLATE_MARKER_END = "<!-- APPVERBO_CORRIGIR_ORDEM_ABAS_SESSOES_ADMIN_SUBPROCESS_V5_END -->"

ADMIN_CSS_CACHE = "/static/css/modules/admin_subprocesses_v1.css?v=20260505-corrigir-ordem-abas-sessoes-v5"
ADMIN_JS_CACHE = "/static/js/modules/admin_subprocesses_v1.js?v=20260505-corrigir-ordem-abas-sessoes-v5"

OLD_TEMPLATE_MARKERS = [
    ("<!-- APPVERBO_MIGRAR_SESSOES_ADMIN_SUBPROCESS_V2_START -->", "<!-- APPVERBO_MIGRAR_SESSOES_ADMIN_SUBPROCESS_V2_END -->"),
    ("<!-- APPVERBO_CORRIGIR_ORDEM_ABAS_SESSOES_ADMIN_SUBPROCESS_V3_START -->", "<!-- APPVERBO_CORRIGIR_ORDEM_ABAS_SESSOES_ADMIN_SUBPROCESS_V3_END -->"),
    ("<!-- APPVERBO_CORRIGIR_ORDEM_ABAS_SESSOES_ADMIN_SUBPROCESS_V4_START -->", "<!-- APPVERBO_CORRIGIR_ORDEM_ABAS_SESSOES_ADMIN_SUBPROCESS_V4_END -->"),
    (TEMPLATE_MARKER_START, TEMPLATE_MARKER_END),
    ("<!-- APPVERBO_SESSOES_SERVER_RENDER_IGUAL_ENTIDADE_V25_START -->", "<!-- APPVERBO_SESSOES_SERVER_RENDER_IGUAL_ENTIDADE_V25_END -->"),
    ("<!-- APPVERBO_SESSOES_SERVER_RENDER_UNICO_V28_START -->", "<!-- APPVERBO_SESSOES_SERVER_RENDER_UNICO_V28_END -->"),
    ("<!-- APPVERBO_SESSOES_CORRIGIR_V28_REMOVER_DUPLICADOS_V29_START -->", "<!-- APPVERBO_SESSOES_CORRIGIR_V28_REMOVER_DUPLICADOS_V29_END -->"),
    ("<!-- APPVERBO_SESSOES_FLUXO_NATIVO_IGUAL_ENTIDADE_V30_START -->", "<!-- APPVERBO_SESSOES_FLUXO_NATIVO_IGUAL_ENTIDADE_V30_END -->"),
]


def fail_v5(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


def read_text_v5(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text_v5(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
    print(f"OK: escrito {path}")


def strip_trailing_whitespace_v5(content: str) -> str:
    return "\n".join(line.rstrip() for line in content.splitlines()) + "\n"


def resolve_agents_path_v5() -> Path:
    if AGENTS_UPPER_PATH.exists():
        return AGENTS_UPPER_PATH

    if AGENTS_TITLE_PATH.exists():
        return AGENTS_TITLE_PATH

    AGENTS_UPPER_PATH.write_text("# AGENTS.md\n\n", encoding="utf-8")
    return AGENTS_UPPER_PATH


def remove_marked_block_v5(content: str, start_marker: str, end_marker: str) -> str:
    while start_marker in content and end_marker in content:
        content = re.sub(
            re.escape(start_marker) + r"[\s\S]*?" + re.escape(end_marker),
            "",
            content,
            count=1,
        )

    return content


def find_section_bounds_by_id_v5(content: str, section_id: str) -> tuple[int, int]:
    pattern = re.compile(
        r"<section\b[^>]*\bid=[\"']" + re.escape(section_id) + r"[\"'][^>]*>",
        re.IGNORECASE,
    )

    match = pattern.search(content)

    if not match:
        fail_v5(f"section #{section_id} não encontrada.")

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

    fail_v5(f"não encontrei fechamento da section #{section_id}.")


def remove_section_by_id_v5(content: str, section_id: str) -> str:
    pattern = re.compile(
        r"<section\b[^>]*\bid=[\"']" + re.escape(section_id) + r"[\"'][^>]*>",
        re.IGNORECASE,
    )

    while pattern.search(content):
        start, end = find_section_bounds_by_id_v5(content, section_id)
        content = content[:start] + content[end:]

    return content


def find_all_section_blocks_v5(content: str) -> list[tuple[int, int, str]]:
    result: list[tuple[int, int, str]] = []
    token_pattern = re.compile(r"</?section\b[^>]*>", re.IGNORECASE)
    stack: list[re.Match[str]] = []

    for token in token_pattern.finditer(content):
        token_text = token.group(0).lower()

        if not token_text.startswith("</section"):
            stack.append(token)
            continue

        if not stack:
            continue

        start_token = stack.pop()

        if not stack:
            result.append((start_token.start(), token.end(), content[start_token.start():token.end()]))

    return result


def remove_sections_containing_v5(content: str, patterns: list[str]) -> str:
    changed = True

    while changed:
        changed = False

        for start, end, block in find_all_section_blocks_v5(content):
            if any(pattern in block for pattern in patterns):
                content = content[:start] + content[end:]
                changed = True
                break

    return content


def remove_script_by_id_v5(content: str, script_id: str) -> str:
    pattern = re.compile(
        r"\s*<script\b[^>]*\bid=[\"']" + re.escape(script_id) + r"[\"'][^>]*>[\s\S]*?</script>",
        re.IGNORECASE,
    )

    return pattern.sub("", content)


def remove_empty_old_sessoes_comments_v5(content: str) -> str:
    content = re.sub(
        r"\n\s*<!-- APPVERBO_[A-Z0-9_]*SESSOES[A-Z0-9_]*_START -->\s*<!-- APPVERBO_[A-Z0-9_]*SESSOES[A-Z0-9_]*_END -->",
        "",
        content,
    )

    return content


def ensure_macro_import_v5(content: str) -> str:
    macro_import = '{% from "macros/admin_subprocess.html" import render_admin_subprocess_state %}'

    if macro_import in content:
        return content

    extends_match = re.search(r"({%\s*extends[^\n]+%}\s*)", content)

    if extends_match:
        return content[:extends_match.end()] + "\n" + macro_import + "\n" + content[extends_match.end():]

    return macro_import + "\n" + content


def ensure_head_asset_v5(content: str, asset_html: str, asset_name: str) -> str:
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

    fail_v5(f"não encontrei local para inserir asset: {asset_name}")


def print_contexts_v5(content: str, term: str) -> None:
    for match in re.finditer(re.escape(term), content):
        start = max(0, match.start() - 160)
        end = min(len(content), match.end() + 160)
        print("----- contexto -----")
        print(content[start:end])


####################################################################################
# (1) VALIDAR FICHEIROS
####################################################################################

for file_path in [TEMPLATE_PATH, MACRO_PATH, ADMIN_CSS_PATH, ADMIN_JS_PATH]:
    if not file_path.exists():
        fail_v5(f"ficheiro obrigatório não encontrado: {file_path}")


####################################################################################
# (2) CORRIGIR TEMPLATE
####################################################################################

template_content = read_text_v5(TEMPLATE_PATH)
template_content = strip_trailing_whitespace_v5(template_content)

for start_marker, end_marker in OLD_TEMPLATE_MARKERS:
    template_content = remove_marked_block_v5(template_content, start_marker, end_marker)

for section_id in [
    "admin-sidebar-sections-form-card",
    "admin-sidebar-sections-create-card",
    "admin-sidebar-sections-card",
    "admin-sidebar-sections-inactive-card",
]:
    template_content = remove_section_by_id_v5(template_content, section_id)

template_content = remove_script_by_id_v5(template_content, "appverbo-sidebar-section-split-v22")
template_content = remove_script_by_id_v5(template_content, "appverbo-sidebar-section-options-v2")

template_content = remove_sections_containing_v5(
    template_content,
    [
        'data-admin-subprocess="sessoes"',
        "data-admin-subprocess='sessoes'",
        "appverbo-sessoes-card",
        "appverbo-sessoes-list-card",
        "appverbo-sessoes-inactive-card",
        "appverbo-sessoes-form-card",
        "Sessões do sidebar",
        "Sessões ativas",
        "Sessões inativas",
    ],
)

template_content = remove_empty_old_sessoes_comments_v5(template_content)
template_content = ensure_macro_import_v5(template_content)

tabs_start, tabs_end = find_section_bounds_by_id_v5(template_content, "menu-tabs-card")

template_block = f'''
        {TEMPLATE_MARKER_START}
        {{% if admin_tab == "sessoes" and admin_subprocess_state %}}
          {{{{ render_admin_subprocess_state(admin_subprocess_state) }}}}
        {{% endif %}}
        {TEMPLATE_MARKER_END}
'''

template_content = template_content[:tabs_end] + template_block + template_content[tabs_end:]

template_content = ensure_head_asset_v5(
    template_content,
    f'<link rel="stylesheet" href="{ADMIN_CSS_CACHE}">',
    "admin_subprocesses_v1.css",
)

template_content = ensure_head_asset_v5(
    template_content,
    f'<script src="{ADMIN_JS_CACHE}" defer></script>',
    "admin_subprocesses_v1.js",
)

template_content = strip_trailing_whitespace_v5(template_content)
write_text_v5(TEMPLATE_PATH, template_content)


####################################################################################
# (3) LIMPAR ESPACOS DOS FICHEIROS ALTERADOS
####################################################################################

for path in [
    TEMPLATE_PATH,
    ADMIN_CSS_PATH,
    ADMIN_JS_PATH,
    SIDEBAR_CSS_PATH,
    SIDEBAR_JS_PATH,
]:
    if path.exists():
        write_text_v5(path, strip_trailing_whitespace_v5(read_text_v5(path)))


####################################################################################
# (4) ATUALIZAR AGENTS.md
####################################################################################

agents_path = resolve_agents_path_v5()
agents_content = read_text_v5(agents_path)

agents_rule = f"""{AGENTS_MARKER_START}
## Ordem definitiva da aba Sessões

Na aba **Sessões**, a ordem visual correta é:

1. Primeiro o card central de ABAS (`menu-tabs-card`);
2. Depois o bloco do subprocesso renderizado por `render_admin_subprocess_state(admin_subprocess_state)`;
3. Nenhum bloco manual antigo de Sessões pode ficar antes do card de ABAS;
4. Não devem existir sections manuais antigas com:
   - `admin-sidebar-sections-form-card`;
   - `admin-sidebar-sections-card`;
   - `admin-sidebar-sections-inactive-card`;
   - classes `appverbo-sessoes-*`;
5. A renderização de Sessões deve depender de `admin_tab == "sessoes"` e `admin_subprocess_state`.
{AGENTS_MARKER_END}"""

agents_content = remove_marked_block_v5(agents_content, AGENTS_MARKER_START, AGENTS_MARKER_END)
agents_content = agents_content.rstrip() + "\n\n" + agents_rule + "\n"

write_text_v5(agents_path, agents_content)


####################################################################################
# (5) VALIDAR RESULTADO
####################################################################################

template_validado = read_text_v5(TEMPLATE_PATH)
agents_validado = read_text_v5(agents_path)

if TEMPLATE_MARKER_START not in template_validado:
    fail_v5("marcador V5 ausente no template.")

if "render_admin_subprocess_state(admin_subprocess_state)" not in template_validado:
    fail_v5("macro render_admin_subprocess_state ausente no template.")

if ADMIN_CSS_CACHE not in template_validado:
    fail_v5("CSS admin_subprocesses_v1.css V5 não foi incluído no template.")

if ADMIN_JS_CACHE not in template_validado:
    fail_v5("JS admin_subprocesses_v1.js V5 não foi incluído no template.")

tabs_start_validado, tabs_end_validado = find_section_bounds_by_id_v5(template_validado, "menu-tabs-card")
macro_index_validado = template_validado.find(TEMPLATE_MARKER_START)

if macro_index_validado < tabs_end_validado:
    fail_v5("o bloco de Sessões ainda está antes ou dentro do menu-tabs-card.")

for forbidden in [
    'id="admin-sidebar-sections-form-card"',
    "id='admin-sidebar-sections-form-card'",
    'id="admin-sidebar-sections-card"',
    "id='admin-sidebar-sections-card'",
    'id="admin-sidebar-sections-inactive-card"',
    "id='admin-sidebar-sections-inactive-card'",
    "Sessões do sidebar",
]:
    if forbidden in template_validado:
        print_contexts_v5(template_validado, forbidden)
        fail_v5(f"conteúdo antigo ainda existe no template: {forbidden}")

old_class_count = template_validado.count("appverbo-sessoes-card")

if old_class_count:
    print("AVISO: ainda existem referências textuais a appverbo-sessoes-card no template.")
    print("AVISO: mostrando contexto para validação manual, mas não bloqueando se não houver section antiga.")
    print_contexts_v5(template_validado, "appverbo-sessoes-card")

if AGENTS_MARKER_START not in agents_validado:
    fail_v5("AGENTS.md não recebeu regra V5.")

print("OK: patch_corrigir_ordem_abas_sessoes_admin_subprocess_v5 concluído.")
