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

AGENTS_MARKER_START = "<!-- APPVERBO_CORRIGIR_ORDEM_ABAS_SESSOES_ADMIN_SUBPROCESS_V3_START -->"
AGENTS_MARKER_END = "<!-- APPVERBO_CORRIGIR_ORDEM_ABAS_SESSOES_ADMIN_SUBPROCESS_V3_END -->"

TEMPLATE_MARKER_START = "<!-- APPVERBO_CORRIGIR_ORDEM_ABAS_SESSOES_ADMIN_SUBPROCESS_V3_START -->"
TEMPLATE_MARKER_END = "<!-- APPVERBO_CORRIGIR_ORDEM_ABAS_SESSOES_ADMIN_SUBPROCESS_V3_END -->"

OLD_TEMPLATE_MARKERS = [
    ("<!-- APPVERBO_MIGRAR_SESSOES_ADMIN_SUBPROCESS_V2_START -->", "<!-- APPVERBO_MIGRAR_SESSOES_ADMIN_SUBPROCESS_V2_END -->"),
    ("<!-- APPVERBO_MIGRAR_SESSOES_ADMIN_SUBPROCESS_V3_START -->", "<!-- APPVERBO_MIGRAR_SESSOES_ADMIN_SUBPROCESS_V3_END -->"),
    (TEMPLATE_MARKER_START, TEMPLATE_MARKER_END),
]

ADMIN_CSS_CACHE = "/static/css/modules/admin_subprocesses_v1.css?v=20260505-corrigir-ordem-abas-sessoes-v3"
ADMIN_JS_CACHE = "/static/js/modules/admin_subprocesses_v1.js?v=20260505-corrigir-ordem-abas-sessoes-v3"


def fail_v3(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


def read_text_v3(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text_v3(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
    print(f"OK: escrito {path}")


def resolve_agents_path_v3() -> Path:
    if AGENTS_UPPER_PATH.exists():
        return AGENTS_UPPER_PATH

    if AGENTS_TITLE_PATH.exists():
        return AGENTS_TITLE_PATH

    AGENTS_UPPER_PATH.write_text("# AGENTS.md\n\n", encoding="utf-8")
    return AGENTS_UPPER_PATH


def strip_trailing_whitespace_v3(content: str) -> str:
    lines = content.splitlines()
    return "\n".join(line.rstrip() for line in lines) + "\n"


def remove_marked_block_v3(content: str, start_marker: str, end_marker: str) -> str:
    while start_marker in content and end_marker in content:
        content = re.sub(
            re.escape(start_marker) + r"[\s\S]*?" + re.escape(end_marker),
            "",
            content,
            count=1,
        )

    return content


def find_section_bounds_by_start_v3(content: str, start_index: int) -> tuple[int, int]:
    section_start_match = re.search(r"<section\b[^>]*>", content[start_index:], re.IGNORECASE)

    if not section_start_match:
        fail_v3("não encontrei início de section no índice informado.")

    start = start_index + section_start_match.start()
    cursor = start_index + section_start_match.end()
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

    fail_v3("não encontrei fechamento da section.")


def find_all_section_blocks_v3(content: str) -> list[tuple[int, int, str]]:
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


def remove_section_by_id_v3(content: str, section_id: str) -> str:
    pattern = re.compile(
        r"<section\b[^>]*\bid=[\"']" + re.escape(section_id) + r"[\"'][^>]*>",
        re.IGNORECASE,
    )

    while True:
        match = pattern.search(content)

        if not match:
            return content

        start, end = find_section_bounds_by_start_v3(content, match.start())
        content = content[:start] + content[end:]


def remove_orphan_sessoes_sections_v3(content: str) -> str:
    orphan_terms = [
        "Sessões ativas",
        "Sessões inativas",
        "Sessões do sidebar",
        "Criar sessão",
    ]

    changed = True

    while changed:
        changed = False

        for start, end, block in find_all_section_blocks_v3(content):
            if TEMPLATE_MARKER_START in block:
                continue

            if any(term in block for term in orphan_terms):
                content = content[:start] + content[end:]
                changed = True
                break

    return content


def find_admin_tabs_section_end_v3(content: str) -> int:
    candidates: list[tuple[int, int, int]] = []

    for start, end, block in find_all_section_blocks_v3(content):
        has_entidade = "Entidade" in block
        has_utilizador = "Utilizador" in block
        has_menu = "Menu" in block
        has_sessoes = "Sessões" in block or "Sessoes" in block
        has_admin_tab = "admin_tab" in block or "data-admin-tab" in block or "admin-tab" in block

        if has_entidade and has_utilizador and has_menu and has_sessoes and has_admin_tab:
            candidates.append((start, end, len(block)))

    if candidates:
        candidates.sort(key=lambda item: item[2])
        return candidates[0][1]

    fallback_match = re.search(
        r"(Entidade[\s\S]{0,2500}Utilizador[\s\S]{0,2500}Menu[\s\S]{0,2500}Sess(?:õ|o)es)",
        content,
        re.IGNORECASE,
    )

    if not fallback_match:
        fail_v3("não encontrei o bloco das ABAS Entidade/Utilizador/Menu/Sessões no template.")

    section_blocks = find_all_section_blocks_v3(content)

    for start, end, block in section_blocks:
        if start <= fallback_match.start() <= end:
            return end

    fail_v3("encontrei textos das ABAS, mas não consegui identificar a section externa.")


####################################################################################
# (1) VALIDAR FICHEIROS
####################################################################################

for file_path in [TEMPLATE_PATH, MACRO_PATH, ADMIN_CSS_PATH, ADMIN_JS_PATH]:
    if not file_path.exists():
        fail_v3(f"ficheiro obrigatório não encontrado: {file_path}")


####################################################################################
# (2) LIMPAR E REPOSICIONAR BLOCO DE SESSOES NO TEMPLATE
####################################################################################

template_content = read_text_v3(TEMPLATE_PATH)
template_content = strip_trailing_whitespace_v3(template_content)

for start_marker, end_marker in OLD_TEMPLATE_MARKERS:
    template_content = remove_marked_block_v3(template_content, start_marker, end_marker)

for section_id in [
    "admin-sidebar-sections-form-card",
    "admin-sidebar-sections-create-card",
    "admin-sidebar-sections-card",
    "admin-sidebar-sections-inactive-card",
]:
    template_content = remove_section_by_id_v3(template_content, section_id)

template_content = remove_orphan_sessoes_sections_v3(template_content)

macro_import = '{% from "macros/admin_subprocess.html" import render_admin_subprocess_state %}'

if macro_import not in template_content:
    extends_match = re.search(r"({%\s*extends[^\n]+%}\s*)", template_content)

    if extends_match:
        template_content = template_content[:extends_match.end()] + "\n" + macro_import + "\n" + template_content[extends_match.end():]
    else:
        template_content = macro_import + "\n" + template_content

template_block = f'''{TEMPLATE_MARKER_START}
        {{% if admin_tab == "sessoes" and admin_subprocess_state %}}
          {{{{ render_admin_subprocess_state(admin_subprocess_state) }}}}
        {{% endif %}}
        {TEMPLATE_MARKER_END}
'''

tabs_end_index = find_admin_tabs_section_end_v3(template_content)
template_content = template_content[:tabs_end_index] + "\n" + template_block + template_content[tabs_end_index:]

template_content = re.sub(
    r"/static/css/modules/admin_subprocesses_v1\.css(?:\?v=[^\"']+)?",
    ADMIN_CSS_CACHE,
    template_content,
)

template_content = re.sub(
    r"/static/js/modules/admin_subprocesses_v1\.js(?:\?v=[^\"']+)?",
    ADMIN_JS_CACHE,
    template_content,
)

if ADMIN_CSS_CACHE not in template_content:
    if "</head>" not in template_content:
        fail_v3("não encontrei </head> para incluir CSS admin_subprocesses_v1.css.")

    template_content = template_content.replace(
        "</head>",
        f'  <link rel="stylesheet" href="{ADMIN_CSS_CACHE}">\n</head>',
        1,
    )

if ADMIN_JS_CACHE not in template_content:
    if "</body>" not in template_content:
        fail_v3("não encontrei </body> para incluir JS admin_subprocesses_v1.js.")

    template_content = template_content.replace(
        "</body>",
        f'  <script src="{ADMIN_JS_CACHE}"></script>\n</body>',
        1,
    )

template_content = strip_trailing_whitespace_v3(template_content)
write_text_v3(TEMPLATE_PATH, template_content)


####################################################################################
# (3) ATUALIZAR AGENTS.md
####################################################################################

agents_path = resolve_agents_path_v3()
agents_content = read_text_v3(agents_path)

agents_rule = f"""{AGENTS_MARKER_START}
## Ordem visual do subprocesso Sessões

Na aba **Sessões**, a ordem correta é obrigatória:

1. Primeiro aparece o card central das ABAS:
   - Entidade;
   - Utilizador;
   - Menu;
   - Sessões.
2. Depois das ABAS aparece o subprocesso Sessões renderizado por:
   - `render_admin_subprocess_state(admin_subprocess_state)`.
3. Nenhum card antigo/orfão de Sessões pode aparecer antes das ABAS.
4. O template não pode manter sections manuais antigas com:
   - `Sessões ativas`;
   - `Sessões inativas`;
   - `Sessões do sidebar`;
   - `Criar sessão`.
5. A renderização de Sessões deve ficar imediatamente após o bloco das ABAS, seguindo o mesmo posicionamento visual da Entidade.
{AGENTS_MARKER_END}"""

agents_content = remove_marked_block_v3(agents_content, AGENTS_MARKER_START, AGENTS_MARKER_END)
agents_content = agents_content.rstrip() + "\n\n" + agents_rule + "\n"
write_text_v3(agents_path, agents_content)


####################################################################################
# (4) VALIDAR RESULTADO
####################################################################################

template_validado = read_text_v3(TEMPLATE_PATH)
agents_validado = read_text_v3(agents_path)

if TEMPLATE_MARKER_START not in template_validado:
    fail_v3("marcador V3 não foi inserido no template.")

if "render_admin_subprocess_state(admin_subprocess_state)" not in template_validado:
    fail_v3("macro render_admin_subprocess_state não foi inserida no template.")

tabs_end_index_validado = find_admin_tabs_section_end_v3(template_validado)
macro_index_validado = template_validado.find(TEMPLATE_MARKER_START)

if macro_index_validado < tabs_end_index_validado:
    fail_v3("bloco de Sessões ainda está antes das ABAS.")

for section_id in [
    "admin-sidebar-sections-form-card",
    "admin-sidebar-sections-card",
    "admin-sidebar-sections-inactive-card",
]:
    count = len(re.findall(r'id=[\"\']' + re.escape(section_id) + r'[\"\']', template_validado))

    if count != 0:
        fail_v3(f"section manual antiga ainda existe no template: {section_id} ({count})")

for term in [
    "Sessões ativas",
    "Sessões inativas",
    "Sessões do sidebar",
]:
    if term in template_validado:
        fail_v3(f"texto antigo/orfão ainda existe no template: {term}")

if AGENTS_MARKER_START not in agents_validado:
    fail_v3("AGENTS.md não recebeu regra V3.")

print("OK: patch_corrigir_ordem_abas_sessoes_admin_subprocess_v3 concluído.")
