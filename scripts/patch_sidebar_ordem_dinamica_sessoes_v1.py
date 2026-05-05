from pathlib import Path
import re
import sys

ROOT = Path.cwd()
SIDEBAR_PATH = ROOT / "templates" / "partials" / "new_user_sidebar.html"

MARKER_START = "{# APPVERBO_SIDEBAR_DYNAMIC_SECTIONS_ORDER_V1_START #}"
MARKER_END = "{# APPVERBO_SIDEBAR_DYNAMIC_SECTIONS_ORDER_V1_END #}"


def fail_v1(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


####################################################################################
# (1) VALIDAR FICHEIRO
####################################################################################

if not SIDEBAR_PATH.exists():
    fail_v1(f"ficheiro não encontrado: {SIDEBAR_PATH}")


####################################################################################
# (2) DEFINIR BLOCO DINAMICO DE SESSOES
####################################################################################

dynamic_sidebar_sections_block = f'''    {MARKER_START}
    {{% set fallback_sidebar_sections = [
      ("sistema", "Sistema"),
      ("geral", "Geral"),
      ("dados_gerais", "Dados gerais"),
      ("igreja", "Igreja"),
      ("tesouraria", "Tesouraria")
    ] %}}

    {{% set dynamic_sidebar_sections = namespace(items=[]) %}}

    {{% if sidebar_section_options is defined and sidebar_section_options %}}
      {{% for section in sidebar_section_options %}}
        {{% set section_key = section.key|default("", true)|lower %}}
        {{% set section_label = section.label|default(section_key, true) %}}

        {{% if section_key %}}
          {{% set dynamic_sidebar_sections.items = dynamic_sidebar_sections.items + [(section_key, section_label)] %}}
        {{% endif %}}
      {{% endfor %}}
    {{% endif %}}

    {{% set sidebar_sections = dynamic_sidebar_sections.items if dynamic_sidebar_sections.items else fallback_sidebar_sections %}}
    {MARKER_END}
'''


####################################################################################
# (3) APLICAR ALTERACAO
####################################################################################

sidebar_content = SIDEBAR_PATH.read_text(encoding="utf-8")

if MARKER_START in sidebar_content and MARKER_END in sidebar_content:
    marker_pattern = re.compile(
        re.escape(MARKER_START) + r"[\s\S]*?" + re.escape(MARKER_END),
        re.S,
    )

    sidebar_content = marker_pattern.sub(
        dynamic_sidebar_sections_block.strip(),
        sidebar_content,
        count=1,
    )

    print("OK: bloco dinamico existente atualizado.")
else:
    fixed_block_pattern = re.compile(
        r'''    \{% set sidebar_sections = \[
      \("sistema", "Sistema"\),
      \("geral", "Geral"\),
      \("dados_gerais", "Dados gerais"\),
      \("igreja", "Igreja"\),
      \("tesouraria", "Tesouraria"\)
    \] %\}
''',
        re.S,
    )

    if not fixed_block_pattern.search(sidebar_content):
        fail_v1("não encontrei o bloco fixo sidebar_sections para substituir.")

    sidebar_content = fixed_block_pattern.sub(
        dynamic_sidebar_sections_block,
        sidebar_content,
        count=1,
    )

    print("OK: bloco fixo sidebar_sections substituído por ordem dinâmica.")


####################################################################################
# (4) VALIDAR CONTEUDO
####################################################################################

required_terms = [
    MARKER_START,
    MARKER_END,
    "sidebar_section_options",
    "fallback_sidebar_sections",
    "dynamic_sidebar_sections",
    "section_state.has_items",
]

for required_term in required_terms:
    if required_term not in sidebar_content:
        fail_v1(f"conteúdo obrigatório ausente no sidebar: {required_term}")

if sidebar_content.count("APPVERBO_SIDEBAR_DYNAMIC_SECTIONS_ORDER_V1_START") != 1:
    fail_v1("marcador START duplicado.")

if sidebar_content.count("APPVERBO_SIDEBAR_DYNAMIC_SECTIONS_ORDER_V1_END") != 1:
    fail_v1("marcador END duplicado.")

SIDEBAR_PATH.write_text(sidebar_content, encoding="utf-8")

print("OK: templates/partials/new_user_sidebar.html atualizado.")
print("OK: sidebar lateral agora usa a ordem de sidebar_section_options.")
