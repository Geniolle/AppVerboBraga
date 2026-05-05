from pathlib import Path
import re
import sys

ROOT = Path.cwd()

TEMPLATE_PATH = ROOT / "templates" / "new_user.html"
TOP_MENU_JS_PATH = ROOT / "static" / "js" / "modules" / "top_menu_active_v1.js"
SIDEBAR_JS_PATH = ROOT / "static" / "js" / "modules" / "sidebar_sections_layout_v1.js"

NEW_SESSOES_URL = "/users/new?menu=administrativo&admin_tab=sessoes&sidebar_sections_tab=sessoes&target=admin-sidebar-sections-card#admin-sidebar-sections-card"
OLD_SESSOES_URL = "/users/new?menu=administrativo&admin_tab=contas#admin-sidebar-sections-card"

TOP_CACHE = "/static/js/modules/top_menu_active_v1.js?v=20260505-limpar-brigas-topcentral-v32"
SIDEBAR_CACHE = "/static/js/modules/sidebar_sections_layout_v1.js?v=20260505-limpar-brigas-topcentral-v32"


####################################################################################
# (1) UTILITARIOS
####################################################################################

def fail_v32(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


def read_text_v32(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text_v32(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def remove_js_marker_families_v32(content: str, families: list[str]) -> str:
    for family in families:
        pattern = re.compile(
            r"\n?//\s*(" + re.escape(family) + r"_V\d+)_START[\s\S]*?//\s*\1_END\s*\n?",
            re.S,
        )
        content = pattern.sub("\n", content)
    return content


def remove_html_marker_families_v32(content: str, families: list[str]) -> str:
    for family in families:
        pattern = re.compile(
            r"\n?\s*<!--\s*(" + re.escape(family) + r"_V\d+)_START\s*-->[\s\S]*?<!--\s*\1_END\s*-->\s*\n?",
            re.S | re.I,
        )
        content = pattern.sub("\n", content)
    return content


def find_menu_tabs_sections_v32(content: str):
    pattern = re.compile(
        r'\n?[ \t]*<section\b(?=[^>]*\bid\s*=\s*["\']menu-tabs-card["\'])[\s\S]*?</section>[ \t]*\n?',
        re.I,
    )
    return list(pattern.finditer(content))


def find_main_container_open_end_v32(content: str) -> int:
    main_match = re.search(
        r'<main\b(?=[^>]*\bclass\s*=\s*["\'][^"\']*\bcontent\b[^"\']*["\'])[^>]*>',
        content,
        re.I,
    )

    if not main_match:
        fail_v32('não foi encontrado <main class="content"> em templates/new_user.html')

    container_match = re.search(
        r'<div\b(?=[^>]*\bclass\s*=\s*["\'][^"\']*\bcontainer\b[^"\']*["\'])[^>]*>',
        content[main_match.end():],
        re.I,
    )

    if not container_match:
        fail_v32('não foi encontrado <div class="container"> dentro de <main class="content">')

    return main_match.end() + container_match.end()


def ensure_admin_sessoes_url_v32(content: str) -> str:
    content = content.replace(OLD_SESSOES_URL, NEW_SESSOES_URL)

    content = re.sub(
        r'sessoes:\s*"[^"]*admin-sidebar-sections-card[^"]*"',
        f'sessoes: "{NEW_SESSOES_URL}"',
        content,
        count=1,
    )

    if 'adminTab === "sessoes"' not in content:
        alvo = '    if (adminTab === "contas" && hash === "#admin-sidebar-sections-card") {'
        insercao = '''    if (adminTab === "sessoes" ||
      String(parametros.get("sidebar_sections_tab") || "").trim().toLowerCase() === "sessoes" ||
      parametros.has("sidebar_section_edit_key")) {
      return "sessoes";
    }

'''
        if alvo in content:
            content = content.replace(alvo, insercao + alvo, 1)

    return content


def remove_old_sidebar_guards_v32(content: str) -> str:
    content = re.sub(
        r'\n?\s*//\s*APPVERBO_GUARD_OBTER_CARD_CRIACAO_SESSOES_V\d+\s*\n'
        r'\s*if\s*\(\s*document\.getElementById\("admin-sidebar-sections-form-card"\)\s*\|\|\s*\n'
        r'\s*document\.querySelector\(\s*\'\[data-admin-tab-pane="sessoes"\]\'\s*\)\s*\)\s*\{\s*\n'
        r'\s*return\s+null;\s*\n'
        r'\s*\}\s*\n?',
        "\n",
        content,
        flags=re.S,
    )

    content = re.sub(
        r'\n?\s*//\s*APPVERBO_GUARD_MOVER_CARD_CRIACAO_SESSOES_V\d+\s*\n'
        r'\s*if\s*\(\s*document\.getElementById\("admin-sidebar-sections-form-card"\)\s*\|\|\s*\n'
        r'\s*document\.querySelector\(\s*\'\[data-admin-tab-pane="sessoes"\]\'\s*\)\s*\)\s*\{\s*\n'
        r'\s*return;\s*\n'
        r'\s*\}\s*\n?',
        "\n",
        content,
        flags=re.S,
    )

    return content


def insert_sidebar_server_render_guards_v32(content: str) -> str:
    if "function existeServerRenderSessoes_v32()" not in content:
        helper = r'''
  //###################################################################################
  // APPVERBO_SESSOES_SERVER_RENDER_GUARD_V32
  //###################################################################################

  function existeServerRenderSessoes_v32() {
    return Boolean(
      document.getElementById("admin-sidebar-sections-form-card") ||
      document.getElementById("admin-sidebar-sections-card") ||
      document.getElementById("admin-sidebar-sections-inactive-card") ||
      document.querySelector('[data-admin-tab-pane="sessoes"]')
    );
  }

'''
        content = content.replace(
            '  //###################################################################################\n  // (3) LOCALIZAR CARD E FORMULARIO\n  //###################################################################################',
            helper + '  //###################################################################################\n  // (3) LOCALIZAR CARD E FORMULARIO\n  //###################################################################################',
            1,
        )

    if (
        "function obterOuCriarCardCriacaoSessoes_v3(cardLista) {" in content
        and "APPVERBO_GUARD_OBTER_CARD_CRIACAO_SESSOES_V32" not in content
    ):
        content = content.replace(
            "function obterOuCriarCardCriacaoSessoes_v3(cardLista) {\n",
            '''function obterOuCriarCardCriacaoSessoes_v3(cardLista) {
    // APPVERBO_GUARD_OBTER_CARD_CRIACAO_SESSOES_V32
    if (typeof existeServerRenderSessoes_v32 === "function" && existeServerRenderSessoes_v32()) {
      return null;
    }

''',
            1,
        )

    if (
        "function moverBlocoCriacaoParaCardSeparadoSessoes_v3(cardLista, wrapper) {" in content
        and "APPVERBO_GUARD_MOVER_CARD_CRIACAO_SESSOES_V32" not in content
    ):
        content = content.replace(
            "function moverBlocoCriacaoParaCardSeparadoSessoes_v3(cardLista, wrapper) {\n",
            '''function moverBlocoCriacaoParaCardSeparadoSessoes_v3(cardLista, wrapper) {
    // APPVERBO_GUARD_MOVER_CARD_CRIACAO_SESSOES_V32
    if (typeof existeServerRenderSessoes_v32 === "function" && existeServerRenderSessoes_v32()) {
      return;
    }

''',
            1,
        )

    return content


####################################################################################
# (2) VALIDAR FICHEIROS
####################################################################################

for file_path in [TEMPLATE_PATH, TOP_MENU_JS_PATH, SIDEBAR_JS_PATH]:
    if not file_path.exists():
        fail_v32(f"ficheiro não encontrado: {file_path}")


####################################################################################
# (3) CORRIGIR TEMPLATE: TOPCENTRAL FIXO NO HTML, SEM ANTI-FLICKER LEGADO
####################################################################################

template_html = read_text_v32(TEMPLATE_PATH)

template_html = remove_html_marker_families_v32(
    template_html,
    [
        "APPVERBO_SESSOES_ANTI_FLICKER",
        "APPVERBO_ABAS_SUPERIORES_CONTAINER",
        "APPVERBO_TOPCENTRAL_ANTES_CRIAR",
    ],
)

tabs_sections = find_menu_tabs_sections_v32(template_html)

if tabs_sections:
    tabs_block = tabs_sections[0].group(0).strip()
    template_without_tabs = template_html

    for match in reversed(tabs_sections):
        template_without_tabs = template_without_tabs[:match.start()] + "\n" + template_without_tabs[match.end():]
else:
    tabs_block = '''<section id="menu-tabs-card" class="card menu-tabs-card">
          <div id="submenu-items" class="menu-tabs" role="tablist" aria-label="Abas do menu"></div>
        </section>'''
    template_without_tabs = template_html

container_open_end = find_main_container_open_end_v32(template_without_tabs)

template_html = (
    template_without_tabs[:container_open_end].rstrip() +
    "\n        " +
    tabs_block +
    "\n\n" +
    template_without_tabs[container_open_end:].lstrip()
)

write_text_v32(TEMPLATE_PATH, template_html)

print("OK: template corrigido; TopCentral fica fixo como primeiro card do container.")


####################################################################################
# (4) LIMPAR TOP MENU: REMOVER OBSERVERS DE POSICAO E MANTER APENAS ACTIVE/NAVEGACAO
####################################################################################

top_js = read_text_v32(TOP_MENU_JS_PATH)

top_js = remove_js_marker_families_v32(
    top_js,
    [
        "APPVERBO_SESSOES_ABAS_ACIMA",
        "APPVERBO_ABAS_SUPERIORES_CONTAINER",
        "APPVERBO_TOPCENTRAL_ANTES_CRIAR",
    ],
)

top_js = ensure_admin_sessoes_url_v32(top_js)

write_text_v32(TOP_MENU_JS_PATH, top_js)

print("OK: top_menu_active_v1.js limpo; sem corretores de posição do TopCentral.")


####################################################################################
# (5) LIMPAR SIDEBAR LEGADO: IMPEDIR CRIACAO/MOVIMENTO DO CARD CRIAR SESSAO
####################################################################################

sidebar_js = read_text_v32(SIDEBAR_JS_PATH)

sidebar_js = remove_js_marker_families_v32(
    sidebar_js,
    [
        "APPVERBO_SESSOES_LEGADO_NAO_REPOSICIONAR",
        "APPVERBO_ABAS_SUPERIORES_CONTAINER_SIDEBAR",
        "APPVERBO_TOPCENTRAL_ANTES_CRIAR_SIDEBAR",
    ],
)

sidebar_js = remove_old_sidebar_guards_v32(sidebar_js)
sidebar_js = sidebar_js.replace(OLD_SESSOES_URL, NEW_SESSOES_URL)
sidebar_js = insert_sidebar_server_render_guards_v32(sidebar_js)

write_text_v32(SIDEBAR_JS_PATH, sidebar_js)

print("OK: sidebar_sections_layout_v1.js limpo; legado não move/cria card de Sessões quando server-render existe.")


####################################################################################
# (6) ATUALIZAR CACHE BUSTER
####################################################################################

for template_file in (ROOT / "templates").rglob("*.html"):
    content = read_text_v32(template_file)
    original = content

    content = re.sub(
        r"/static/js/modules/top_menu_active_v1\.js(?:\?v=[^\"']*)?",
        TOP_CACHE,
        content,
    )

    content = re.sub(
        r"/static/js/modules/sidebar_sections_layout_v1\.js(?:\?v=[^\"']*)?",
        SIDEBAR_CACHE,
        content,
    )

    if content != original:
        write_text_v32(template_file, content)
        print(f"OK: cache buster atualizado em {template_file}")


####################################################################################
# (7) VALIDAR CONTEUDO FINAL
####################################################################################

template_validado = read_text_v32(TEMPLATE_PATH)
top_validado = read_text_v32(TOP_MENU_JS_PATH)
sidebar_validado = read_text_v32(SIDEBAR_JS_PATH)

familias_removidas_template = [
    "APPVERBO_SESSOES_ANTI_FLICKER",
    "APPVERBO_TOPCENTRAL_ANTES_CRIAR",
    "APPVERBO_ABAS_SUPERIORES_CONTAINER",
]

familias_removidas_top = [
    "APPVERBO_SESSOES_ABAS_ACIMA",
    "APPVERBO_TOPCENTRAL_ANTES_CRIAR",
    "APPVERBO_ABAS_SUPERIORES_CONTAINER",
]

familias_removidas_sidebar = [
    "APPVERBO_SESSOES_LEGADO_NAO_REPOSICIONAR",
    "APPVERBO_TOPCENTRAL_ANTES_CRIAR_SIDEBAR",
    "APPVERBO_ABAS_SUPERIORES_CONTAINER_SIDEBAR",
]

for termo in familias_removidas_template:
    if termo in template_validado:
        fail_v32(f"validação falhou: bloco legado ainda existe no template: {termo}")

for termo in familias_removidas_top:
    if termo in top_validado:
        fail_v32(f"validação falhou: bloco legado ainda existe no top_menu_active_v1.js: {termo}")

for termo in familias_removidas_sidebar:
    if termo in sidebar_validado:
        fail_v32(f"validação falhou: bloco legado ainda existe no sidebar_sections_layout_v1.js: {termo}")

tabs_sections_validado = find_menu_tabs_sections_v32(template_validado)

if len(tabs_sections_validado) != 1:
    fail_v32(f"deve existir exatamente 1 menu-tabs-card; encontrado: {len(tabs_sections_validado)}")

container_open_end_validado = find_main_container_open_end_v32(template_validado)
conteudo_entre_container_e_tabs = template_validado[container_open_end_validado:tabs_sections_validado[0].start()].strip()

if conteudo_entre_container_e_tabs:
    fail_v32("menu-tabs-card não está como primeiro elemento do container central.")

if NEW_SESSOES_URL not in top_validado:
    fail_v32("URL correta de Sessões ausente em top_menu_active_v1.js.")

if "APPVERBO_GUARD_OBTER_CARD_CRIACAO_SESSOES_V32" not in sidebar_validado:
    fail_v32("guard V32 ausente em obterOuCriarCardCriacaoSessoes_v3.")

if "APPVERBO_GUARD_MOVER_CARD_CRIACAO_SESSOES_V32" not in sidebar_validado:
    fail_v32("guard V32 ausente em moverBlocoCriacaoParaCardSeparadoSessoes_v3.")

print("OK: validações V32 concluídas.")
