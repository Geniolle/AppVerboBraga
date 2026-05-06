from pathlib import Path
import re
import sys
import unicodedata

ROOT = Path.cwd()

TEMPLATE_PATH = ROOT / "templates" / "new_user.html"
TOP_MENU_JS_PATH = ROOT / "static" / "js" / "modules" / "top_menu_active_v1.js"
SIDEBAR_JS_PATH = ROOT / "static" / "js" / "modules" / "sidebar_sections_layout_v1.js"

NEW_SESSOES_URL = "/users/new?menu=administrativo&admin_tab=sessoes&sidebar_sections_tab=sessoes&target=admin-sidebar-sections-card#admin-sidebar-sections-card"
OLD_SESSOES_URL = "/users/new?menu=administrativo&admin_tab=contas#admin-sidebar-sections-card"

TOP_CACHE = "/static/js/modules/top_menu_active_v1.js?v=20260505-topcentral-acima-sessoes-v36"
SIDEBAR_CACHE = "/static/js/modules/sidebar_sections_layout_v1.js?v=20260505-topcentral-acima-sessoes-v36"
ADMIN_CSS_CACHE = "/static/css/modules/admin_subprocesses_v1.css?v=20260505-topcentral-acima-sessoes-v36"
ADMIN_JS_CACHE = "/static/js/modules/admin_subprocesses_v1.js?v=20260505-topcentral-acima-sessoes-v36"

TEMPLATE_MARKER_START = "<!-- APPVERBO_TOPCENTRAL_ACIMA_SESSOES_V36_START -->"
TEMPLATE_MARKER_END = "<!-- APPVERBO_TOPCENTRAL_ACIMA_SESSOES_V36_END -->"


####################################################################################
# (1) UTILITARIOS
####################################################################################

def fail_v36(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


def read_text_v36(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text_v36(path: Path, content: str) -> None:
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def normalizar_texto_v36(valor: str) -> str:
    texto = str(valor or "")
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(ch for ch in texto if unicodedata.category(ch) != "Mn")
    return texto.strip().lower()


def strip_tags_v36(html: str) -> str:
    return re.sub(r"<[^>]+>", " ", html)


def remove_marked_html_family_v36(content: str, family: str) -> str:
    pattern = re.compile(
        r'\n?\s*<!--\s*(' + re.escape(family) + r'_V\d+)_START\s*-->[\s\S]*?<!--\s*\1_END\s*-->\s*\n?',
        re.I,
    )
    return pattern.sub("\n", content)


def remove_marked_js_family_v36(content: str, family: str) -> str:
    pattern = re.compile(
        r'\n?//\s*(' + re.escape(family) + r'_V\d+)_START[\s\S]*?//\s*\1_END\s*\n?',
        re.S,
    )
    return pattern.sub("\n", content)


def find_main_container_open_end_v36(content: str) -> int:
    main_match = re.search(
        r'<main\b(?=[^>]*\bclass\s*=\s*["\'][^"\']*\bcontent\b[^"\']*["\'])[^>]*>',
        content,
        re.I,
    )

    if not main_match:
        fail_v36('não foi encontrado <main class="content"> em templates/new_user.html')

    container_match = re.search(
        r'<div\b(?=[^>]*\bclass\s*=\s*["\'][^"\']*\bcontainer\b[^"\']*["\'])[^>]*>',
        content[main_match.end():],
        re.I,
    )

    if not container_match:
        fail_v36('não foi encontrado <div class="container"> dentro de <main class="content">')

    return main_match.end() + container_match.end()


def find_section_bounds_by_id_v36(content: str, section_id: str):
    open_pattern = re.compile(
        r'<section\b(?=[^>]*\bid\s*=\s*["\']' + re.escape(section_id) + r'["\'])[^>]*>',
        re.I,
    )

    open_match = open_pattern.search(content)

    if not open_match:
        return None

    tag_pattern = re.compile(r'</?section\b[^>]*>', re.I)
    depth = 0

    for tag_match in tag_pattern.finditer(content, open_match.start()):
        token = tag_match.group(0)
        is_close = token.lower().startswith("</section")

        if not is_close:
            depth += 1
        else:
            depth -= 1
            if depth == 0:
                return open_match.start(), tag_match.end()

    fail_v36(f"section sem fechamento: {section_id}")


def find_menu_tabs_sections_v36(content: str):
    pattern = re.compile(
        r'\n?[ \t]*<section\b(?=[^>]*\bid\s*=\s*["\']menu-tabs-card["\'])[\s\S]*?</section>[ \t]*\n?',
        re.I,
    )
    return list(pattern.finditer(content))


def remove_section_by_id_v36(content: str, section_id: str) -> str:
    bounds = find_section_bounds_by_id_v36(content, section_id)

    while bounds:
        start, end = bounds
        content = content[:start] + "\n" + content[end:]
        bounds = find_section_bounds_by_id_v36(content, section_id)

    return content


def remove_sections_containing_v36(content: str, terms: list[str]) -> str:
    section_pattern = re.compile(r'\n?[ \t]*<section\b[\s\S]*?</section>[ \t]*\n?', re.I)

    def repl(match: re.Match) -> str:
        section_html = match.group(0)
        raw = section_html.lower()
        clean = normalizar_texto_v36(strip_tags_v36(section_html))

        for term in terms:
            term_clean = normalizar_texto_v36(term)

            if term.lower() in raw or term_clean in clean:
                return "\n"

        return section_html

    return section_pattern.sub(repl, content)


def ensure_macro_import_v36(content: str) -> str:
    macro_import = '{% from "macros/admin_subprocess.html" import render_admin_subprocess_state %}'

    if macro_import in content:
        return content

    extends_match = re.search(r'({%\s*extends[^\n]+%}\s*)', content)

    if extends_match:
        return content[:extends_match.end()] + "\n" + macro_import + "\n" + content[extends_match.end():]

    return macro_import + "\n" + content


def ensure_head_asset_v36(content: str, asset_html: str, asset_name: str) -> str:
    content = re.sub(
        r'\s*<link[^>]+href=["\'][^"\']*' + re.escape(asset_name) + r'[^"\']*["\'][^>]*>',
        "",
        content,
    )

    content = re.sub(
        r'\s*<script[^>]+src=["\'][^"\']*' + re.escape(asset_name) + r'[^"\']*["\'][^>]*>\s*</script>',
        "",
        content,
    )

    head_match = re.search(r'({%\s*block\s+head_extra\s*%})([\s\S]*?)({%\s*endblock\s*%})', content)

    if head_match:
        insert_at = head_match.start(3)
        return content[:insert_at] + "  " + asset_html + "\n" + content[insert_at:]

    fail_v36(f"não encontrei bloco head_extra para inserir {asset_name}")


def remove_bare_admin_subprocess_if_v36(content: str) -> str:
    pattern = re.compile(
        r'\n?\s*{%\s*if\s+admin_tab\s*==\s*["\']sessoes["\']\s+and\s+admin_subprocess_state\s*%}\s*'
        r'{{\s*render_admin_subprocess_state\(admin_subprocess_state\)\s*}}\s*'
        r'{%\s*endif\s*%}\s*\n?',
        re.I,
    )
    return pattern.sub("\n", content)


def remove_orphan_admin_subprocess_macro_v36(content: str) -> str:
    pattern = re.compile(
        r'\n?\s*{{\s*render_admin_subprocess_state\(admin_subprocess_state\)\s*}}\s*\n?',
        re.I,
    )
    return pattern.sub("\n", content)


def ensure_single_menu_tabs_first_v36(content: str) -> str:
    tabs_sections = find_menu_tabs_sections_v36(content)

    if tabs_sections:
        tabs_block = tabs_sections[0].group(0).strip()
        without_tabs = content

        for match in reversed(tabs_sections):
            without_tabs = without_tabs[:match.start()] + "\n" + without_tabs[match.end():]
    else:
        tabs_block = '''<section id="menu-tabs-card" class="card menu-tabs-card">
          <div id="submenu-items" class="menu-tabs" role="tablist" aria-label="Abas do menu"></div>
        </section>'''
        without_tabs = content

    container_open_end = find_main_container_open_end_v36(without_tabs)

    return (
        without_tabs[:container_open_end].rstrip() +
        "\n        " +
        tabs_block +
        "\n\n" +
        without_tabs[container_open_end:].lstrip()
    )


def insert_sessoes_after_tabs_v36(content: str) -> str:
    bounds = find_section_bounds_by_id_v36(content, "menu-tabs-card")

    if not bounds:
        fail_v36("menu-tabs-card ausente ao inserir subprocesso Sessões.")

    _, tabs_end = bounds

    block = f'''
        {TEMPLATE_MARKER_START}
        {{% if admin_tab == "sessoes" and admin_subprocess_state %}}
          {{{{ render_admin_subprocess_state(admin_subprocess_state) }}}}
        {{% endif %}}
        {TEMPLATE_MARKER_END}
'''

    return content[:tabs_end] + block + content[tabs_end:]


####################################################################################
# (2) VALIDAR FICHEIROS
####################################################################################

for file_path in [TEMPLATE_PATH, TOP_MENU_JS_PATH, SIDEBAR_JS_PATH]:
    if not file_path.exists():
        fail_v36(f"ficheiro não encontrado: {file_path}")


####################################################################################
# (3) CORRIGIR TEMPLATE: TOPCENTRAL PRIMEIRO, SESSOES DEPOIS
####################################################################################

template = read_text_v36(TEMPLATE_PATH)

for family in [
    "APPVERBO_TOPCENTRAL_ACIMA_SESSOES",
    "APPVERBO_CORRIGIR_ORDEM_ABAS_SESSOES_ADMIN_SUBPROCESS",
    "APPVERBO_MIGRAR_SESSOES_ADMIN_SUBPROCESS",
    "APPVERBO_SESSOES_SERVER_RENDER_IGUAL_ENTIDADE",
    "APPVERBO_SESSOES_SERVER_RENDER_UNICO",
    "APPVERBO_SESSOES_CORRIGIR_V28_REMOVER_DUPLICADOS",
    "APPVERBO_SESSOES_FLUXO_NATIVO_IGUAL_ENTIDADE",
    "APPVERBO_SESSOES_ANTI_FLICKER",
]:
    template = remove_marked_html_family_v36(template, family)

template = remove_bare_admin_subprocess_if_v36(template)
template = remove_orphan_admin_subprocess_macro_v36(template)

for section_id in [
    "admin-sidebar-sections-form-card",
    "admin-sidebar-sections-create-card",
    "admin-sidebar-sections-card",
    "admin-sidebar-sections-inactive-card",
]:
    template = remove_section_by_id_v36(template, section_id)

template = remove_sections_containing_v36(
    template,
    [
        'data-admin-subprocess="sessoes"',
        "data-admin-subprocess='sessoes'",
        "appverbo-sessoes-card",
        "appverbo-sessoes-form-card",
        "appverbo-sessoes-list-card",
        "appverbo-sessoes-inactive-card",
        "Sessões do sidebar",
    ],
)

template = ensure_macro_import_v36(template)
template = ensure_single_menu_tabs_first_v36(template)
template = insert_sessoes_after_tabs_v36(template)

template = ensure_head_asset_v36(
    template,
    f'<link rel="stylesheet" href="{ADMIN_CSS_CACHE}">',
    "admin_subprocesses_v1.css",
)

template = ensure_head_asset_v36(
    template,
    f'<script src="{ADMIN_JS_CACHE}" defer></script>',
    "admin_subprocesses_v1.js",
)

write_text_v36(TEMPLATE_PATH, template)

print("OK: template corrigido: TopCentral antes de Sessões.")


####################################################################################
# (4) CORRIGIR TOP MENU: URL E ACTIVE CORRETOS
####################################################################################

top_js = read_text_v36(TOP_MENU_JS_PATH)

for family in [
    "APPVERBO_SESSOES_ABAS_ACIMA",
    "APPVERBO_ABAS_SUPERIORES_CONTAINER",
    "APPVERBO_TOPCENTRAL_ANTES_CRIAR",
]:
    top_js = remove_marked_js_family_v36(top_js, family)

top_js = top_js.replace(OLD_SESSOES_URL, NEW_SESSOES_URL)

top_js = re.sub(
    r'sessoes:\s*"[^"]*admin-sidebar-sections-card[^"]*"',
    f'sessoes: "{NEW_SESSOES_URL}"',
    top_js,
    count=1,
)

top_js = re.sub(
    r'menu:\s*"[^"]*"',
    'menu: "/users/new?menu=administrativo&admin_tab=menu"',
    top_js,
    count=1,
)

if 'adminTab === "menu"' not in top_js:
    alvo = '    if (adminTab === "contas" || adminTab === "definicoes") {\n      return "menu";\n    }'
    substituto = '''    if (adminTab === "menu" || adminTab === "contas" || adminTab === "definicoes") {
      return "menu";
    }'''

    if alvo in top_js:
        top_js = top_js.replace(alvo, substituto, 1)

if 'adminTab === "sessoes"' not in top_js:
    alvo = '    if (adminTab === "contas" && hash === "#admin-sidebar-sections-card") {'
    insercao = '''    if (adminTab === "sessoes" ||
      String(parametros.get("sidebar_sections_tab") || "").trim().toLowerCase() === "sessoes" ||
      parametros.has("sidebar_section_edit_key")) {
      return "sessoes";
    }

'''
    if alvo in top_js:
        top_js = top_js.replace(alvo, insercao + alvo, 1)

write_text_v36(TOP_MENU_JS_PATH, top_js)

print("OK: top_menu_active_v1.js corrigido para Menu e Sessões.")


####################################################################################
# (5) REFORCAR GUARDA DO SIDEBAR LEGADO
####################################################################################

sidebar_js = read_text_v36(SIDEBAR_JS_PATH)

for family in [
    "APPVERBO_SESSOES_LEGADO_NAO_REPOSICIONAR",
    "APPVERBO_ABAS_SUPERIORES_CONTAINER_SIDEBAR",
    "APPVERBO_TOPCENTRAL_ANTES_CRIAR_SIDEBAR",
]:
    sidebar_js = remove_marked_js_family_v36(sidebar_js, family)

sidebar_js = sidebar_js.replace(OLD_SESSOES_URL, NEW_SESSOES_URL)

guard = '''function existeServerRenderSessoes_v32() {
    try {
      const url = new URL(window.location.href);
      const adminTab = String(url.searchParams.get("admin_tab") || "").trim().toLowerCase();
      const sidebarTab = String(url.searchParams.get("sidebar_sections_tab") || "").trim().toLowerCase();

      if (adminTab === "sessoes" || sidebarTab === "sessoes") {
        return true;
      }
    } catch (erro) {
    }

    return Boolean(
      document.querySelector('[data-admin-subprocess="sessoes"]') ||
      document.querySelector('[data-admin-subprocess-key="sessoes"]') ||
      document.querySelector('[data-subprocess-key="sessoes"]') ||
      document.querySelector('[data-admin-tab-pane="sessoes"]')
    );
  }'''

if "function existeServerRenderSessoes_v32()" in sidebar_js:
    sidebar_js = re.sub(
        r'function\s+existeServerRenderSessoes_v32\s*\(\)\s*\{[\s\S]*?\n  \}',
        lambda match: guard,
        sidebar_js,
        count=1,
    )
else:
    anchor = '  //###################################################################################\n  // (3) LOCALIZAR CARD E FORMULARIO\n  //###################################################################################'
    helper = (
        '  //###################################################################################\n'
        '  // APPVERBO_SESSOES_SERVER_RENDER_GUARD_V32\n'
        '  //###################################################################################\n\n'
        '  ' + guard.replace("\n", "\n  ") + "\n\n"
    )

    if anchor in sidebar_js:
        sidebar_js = sidebar_js.replace(anchor, helper + anchor, 1)
    else:
        sidebar_js = sidebar_js.replace('"use strict";', '"use strict";\n\n' + helper, 1)

if (
    "function obterOuCriarCardCriacaoSessoes_v3(cardLista) {" in sidebar_js
    and "APPVERBO_GUARD_OBTER_CARD_CRIACAO_SESSOES_V32" not in sidebar_js
):
    sidebar_js = sidebar_js.replace(
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
    "function moverBlocoCriacaoParaCardSeparadoSessoes_v3(cardLista, wrapper) {" in sidebar_js
    and "APPVERBO_GUARD_MOVER_CARD_CRIACAO_SESSOES_V32" not in sidebar_js
):
    sidebar_js = sidebar_js.replace(
        "function moverBlocoCriacaoParaCardSeparadoSessoes_v3(cardLista, wrapper) {\n",
        '''function moverBlocoCriacaoParaCardSeparadoSessoes_v3(cardLista, wrapper) {
    // APPVERBO_GUARD_MOVER_CARD_CRIACAO_SESSOES_V32
    if (typeof existeServerRenderSessoes_v32 === "function" && existeServerRenderSessoes_v32()) {
      return;
    }

''',
        1,
    )

write_text_v36(SIDEBAR_JS_PATH, sidebar_js)

print("OK: sidebar_sections_layout_v1.js protegido contra legado.")


####################################################################################
# (6) ATUALIZAR CACHE BUSTER
####################################################################################

for template_file in (ROOT / "templates").rglob("*.html"):
    content = read_text_v36(template_file)
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
        write_text_v36(template_file, content)
        print(f"OK: cache buster atualizado em {template_file}")


####################################################################################
# (7) VALIDAR CONTEUDO FINAL
####################################################################################

template_validado = read_text_v36(TEMPLATE_PATH)
top_validado = read_text_v36(TOP_MENU_JS_PATH)
sidebar_validado = read_text_v36(SIDEBAR_JS_PATH)

tabs = find_menu_tabs_sections_v36(template_validado)

if len(tabs) != 1:
    fail_v36(f"deve existir exatamente 1 menu-tabs-card; encontrado: {len(tabs)}")

if TEMPLATE_MARKER_START not in template_validado:
    fail_v36("marcador V36 ausente no template.")

tabs_bounds = find_section_bounds_by_id_v36(template_validado, "menu-tabs-card")
macro_index = template_validado.find(TEMPLATE_MARKER_START)

if not tabs_bounds:
    fail_v36("menu-tabs-card ausente no template.")

_, tabs_end = tabs_bounds

if macro_index < tabs_end:
    fail_v36("bloco de Sessões está antes ou dentro do menu-tabs-card.")

container_open_end = find_main_container_open_end_v36(template_validado)
conteudo_entre_container_e_tabs = template_validado[container_open_end:tabs[0].start()].strip()

if conteudo_entre_container_e_tabs:
    fail_v36("menu-tabs-card não está como primeiro elemento do container central.")

template_normalizado = normalizar_texto_v36(strip_tags_v36(template_validado))

if "sessoes do sidebar" in template_normalizado:
    fail_v36("texto legado 'Sessões do sidebar' ainda existe no template.")

for forbidden in [
    'id="admin-sidebar-sections-form-card"',
    "id='admin-sidebar-sections-form-card'",
    'id="admin-sidebar-sections-card"',
    "id='admin-sidebar-sections-card'",
    'id="admin-sidebar-sections-inactive-card"',
    "id='admin-sidebar-sections-inactive-card'",
    "appverbo-sessoes-card",
    "APPVERBO_SESSOES_ANTI_FLICKER",
    "APPVERBO_SESSOES_ABAS_ACIMA",
    "APPVERBO_TOPCENTRAL_ANTES_CRIAR",
]:
    if forbidden in template_validado or forbidden in top_validado or forbidden in sidebar_validado:
        fail_v36(f"conteúdo legado ainda existe: {forbidden}")

if NEW_SESSOES_URL not in top_validado:
    fail_v36("URL correta de Sessões ausente em top_menu_active_v1.js.")

if 'menu: "/users/new?menu=administrativo&admin_tab=menu"' not in top_validado:
    fail_v36("URL correta de Menu ausente em top_menu_active_v1.js.")

if 'adminTab === "menu"' not in top_validado:
    fail_v36("active de admin_tab=menu ausente em top_menu_active_v1.js.")

if "function existeServerRenderSessoes_v32()" not in sidebar_validado:
    fail_v36("função existeServerRenderSessoes_v32 ausente no sidebar JS.")

if "APPVERBO_GUARD_OBTER_CARD_CRIACAO_SESSOES_V32" not in sidebar_validado:
    fail_v36("guard obter card V32 ausente no sidebar JS.")

if "APPVERBO_GUARD_MOVER_CARD_CRIACAO_SESSOES_V32" not in sidebar_validado:
    fail_v36("guard mover card V32 ausente no sidebar JS.")

for file_path in [TEMPLATE_PATH, TOP_MENU_JS_PATH, SIDEBAR_JS_PATH]:
    content = read_text_v36(file_path)

    if not content.endswith("\n"):
        fail_v36(f"ficheiro sem newline final: {file_path}")

    if content.endswith("\n\n"):
        fail_v36(f"ficheiro com linha em branco extra no EOF: {file_path}")

print("OK: validações V36 concluídas.")
