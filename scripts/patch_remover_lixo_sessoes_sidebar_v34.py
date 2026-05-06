from pathlib import Path
import re
import sys
import unicodedata

ROOT = Path.cwd()

TEMPLATE_PATH = ROOT / "templates" / "new_user.html"
SIDEBAR_JS_PATH = ROOT / "static" / "js" / "modules" / "sidebar_sections_layout_v1.js"
TOP_MENU_JS_PATH = ROOT / "static" / "js" / "modules" / "top_menu_active_v1.js"

NEW_SESSOES_URL = "/users/new?menu=administrativo&admin_tab=sessoes&sidebar_sections_tab=sessoes&target=admin-sidebar-sections-card#admin-sidebar-sections-card"
OLD_SESSOES_URL = "/users/new?menu=administrativo&admin_tab=contas#admin-sidebar-sections-card"

TOP_CACHE = "/static/js/modules/top_menu_active_v1.js?v=20260505-remover-lixo-sessoes-sidebar-v34"
SIDEBAR_CACHE = "/static/js/modules/sidebar_sections_layout_v1.js?v=20260505-remover-lixo-sessoes-sidebar-v34"


####################################################################################
# (1) UTILITARIOS
####################################################################################

def fail_v34(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


def read_text_v34(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text_v34(path: Path, content: str) -> None:
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def normalizar_texto_v34(valor: str) -> str:
    texto = str(valor or "")
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(ch for ch in texto if unicodedata.category(ch) != "Mn")
    return texto.strip().lower()


def strip_tags_v34(html: str) -> str:
    return re.sub(r"<[^>]+>", " ", html)


def find_menu_tabs_sections_v34(content: str):
    pattern = re.compile(
        r'\n?[ \t]*<section\b(?=[^>]*\bid\s*=\s*["\']menu-tabs-card["\'])[\s\S]*?</section>[ \t]*\n?',
        re.I,
    )
    return list(pattern.finditer(content))


def find_main_container_open_end_v34(content: str) -> int:
    main_match = re.search(
        r'<main\b(?=[^>]*\bclass\s*=\s*["\'][^"\']*\bcontent\b[^"\']*["\'])[^>]*>',
        content,
        re.I,
    )

    if not main_match:
        fail_v34('não foi encontrado <main class="content"> em templates/new_user.html')

    container_match = re.search(
        r'<div\b(?=[^>]*\bclass\s*=\s*["\'][^"\']*\bcontainer\b[^"\']*["\'])[^>]*>',
        content[main_match.end():],
        re.I,
    )

    if not container_match:
        fail_v34('não foi encontrado <div class="container"> dentro de <main class="content">')

    return main_match.end() + container_match.end()


def garantir_topcentral_primeiro_card_v34(template_html: str) -> str:
    tabs_sections = find_menu_tabs_sections_v34(template_html)

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

    container_open_end = find_main_container_open_end_v34(template_without_tabs)

    return (
        template_without_tabs[:container_open_end].rstrip() +
        "\n        " +
        tabs_block +
        "\n\n" +
        template_without_tabs[container_open_end:].lstrip()
    )


####################################################################################
# (2) VALIDAR FICHEIROS
####################################################################################

for file_path in [TEMPLATE_PATH, SIDEBAR_JS_PATH, TOP_MENU_JS_PATH]:
    if not file_path.exists():
        fail_v34(f"ficheiro não encontrado: {file_path}")


####################################################################################
# (3) REMOVER BLOCO LEGADO SESSOES DO SIDEBAR DO TEMPLATE
####################################################################################

template_html = read_text_v34(TEMPLATE_PATH)
original_template = template_html

removed_count = 0

marker_pattern = re.compile(
    r'\n?\s*<!--\s*APPVERBO_SESSOES_SERVER_RENDER_[A-Z0-9_]*_START\s*-->[\s\S]*?'
    r'<!--\s*APPVERBO_SESSOES_SERVER_RENDER_[A-Z0-9_]*_END\s*-->\s*\n?',
    re.I,
)

def remove_marker_block_if_legacy_v34(match: re.Match) -> str:
    global removed_count
    bloco = match.group(0)
    texto = normalizar_texto_v34(strip_tags_v34(bloco))

    if (
        "sessoes do sidebar" in texto or
        "admin-sidebar-sections-card" in bloco or
        "admin-sidebar-sections-form-card" in bloco or
        "admin-sidebar-sections-inactive-card" in bloco
    ):
        removed_count += 1
        return "\n"

    return bloco

template_html = marker_pattern.sub(remove_marker_block_if_legacy_v34, template_html)

section_pattern = re.compile(r'\n?[ \t]*<section\b[\s\S]*?</section>[ \t]*\n?', re.I)

def section_is_legacy_sessoes_v34(section_html: str) -> bool:
    raw = section_html.lower()
    texto = normalizar_texto_v34(strip_tags_v34(section_html))

    has_legacy_title = "sessoes do sidebar" in texto

    has_legacy_id = (
        'id="admin-sidebar-sections-form-card"' in raw or
        "id='admin-sidebar-sections-form-card'" in raw or
        'id="admin-sidebar-sections-card"' in raw or
        "id='admin-sidebar-sections-card'" in raw or
        'id="admin-sidebar-sections-inactive-card"' in raw or
        "id='admin-sidebar-sections-inactive-card'" in raw or
        'id="admin-sidebar-sections-create-card"' in raw or
        "id='admin-sidebar-sections-create-card'" in raw
    )

    has_legacy_class_or_action = (
        "appverbo-sessoes-card" in raw or
        "appverbo-sidebar-sections-layout" in raw or
        "/settings/menu/sidebar-section" in raw or
        "sidebar-section-save" in raw or
        "sidebar-section-move-one" in raw
    )

    if has_legacy_title:
        return True

    if has_legacy_id and has_legacy_class_or_action:
        return True

    return False


def remove_legacy_section_v34(match: re.Match) -> str:
    global removed_count
    section_html = match.group(0)

    if section_is_legacy_sessoes_v34(section_html):
        removed_count += 1
        return "\n"

    return section_html

template_html = section_pattern.sub(remove_legacy_section_v34, template_html)

template_html = garantir_topcentral_primeiro_card_v34(template_html)

write_text_v34(TEMPLATE_PATH, template_html)

print(f"OK: blocos legados de Sessões removidos do template: {removed_count}")


####################################################################################
# (4) REFORCAR GUARDA NO SIDEBAR LEGADO
####################################################################################

sidebar_js = read_text_v34(SIDEBAR_JS_PATH)
sidebar_js = sidebar_js.replace(OLD_SESSOES_URL, NEW_SESSOES_URL)

new_guard = r'''function existeServerRenderSessoes_v32() {
    const porEstruturaNova = Boolean(
      document.querySelector('[data-admin-tab-pane="sessoes"]') ||
      document.querySelector('[data-admin-subprocess-key="sessoes"]') ||
      document.querySelector('[data-subprocess-key="sessoes"]')
    );

    if (porEstruturaNova) {
      return true;
    }

    try {
      const url = new URL(window.location.href);
      const adminTab = String(url.searchParams.get("admin_tab") || "").trim().toLowerCase();
      const sidebarTab = String(url.searchParams.get("sidebar_sections_tab") || "").trim().toLowerCase();

      if (adminTab === "sessoes" || sidebarTab === "sessoes") {
        return true;
      }
    } catch (erro) {
    }

    const cards = Array.from(document.querySelectorAll("section.card, section, .card"));

    return cards.some(function (card) {
      const texto = String(card && card.textContent || "")
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .trim()
        .toLowerCase();

      return texto.indexOf("sessoes ativas") >= 0 ||
        texto.indexOf("sessoes inativas") >= 0;
    });
  }'''

if "function existeServerRenderSessoes_v32()" in sidebar_js:
    sidebar_js = re.sub(
        r'function\s+existeServerRenderSessoes_v32\s*\(\)\s*\{[\s\S]*?\n  \}',
        new_guard,
        sidebar_js,
        count=1,
    )
else:
    insert_anchor = '  //###################################################################################\n  // (3) LOCALIZAR CARD E FORMULARIO\n  //###################################################################################'
    helper_block = (
        '  //###################################################################################\n'
        '  // APPVERBO_SESSOES_SERVER_RENDER_GUARD_V32\n'
        '  //###################################################################################\n\n'
        '  ' + new_guard.replace("\n", "\n  ") + '\n\n'
    )

    if insert_anchor in sidebar_js:
        sidebar_js = sidebar_js.replace(insert_anchor, helper_block + insert_anchor, 1)
    else:
        sidebar_js = sidebar_js.replace('"use strict";', '"use strict";\n\n' + helper_block, 1)

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

write_text_v34(SIDEBAR_JS_PATH, sidebar_js)

print("OK: guarda do sidebar legado reforçada para não recriar Sessões do sidebar.")


####################################################################################
# (5) GARANTIR URL CORRETA DA ABA SESSOES NO TOP MENU
####################################################################################

top_menu_js = read_text_v34(TOP_MENU_JS_PATH)
top_menu_js = top_menu_js.replace(OLD_SESSOES_URL, NEW_SESSOES_URL)

top_menu_js = re.sub(
    r'sessoes:\s*"[^"]*admin-sidebar-sections-card[^"]*"',
    f'sessoes: "{NEW_SESSOES_URL}"',
    top_menu_js,
    count=1,
)

if 'adminTab === "sessoes"' not in top_menu_js:
    alvo = '    if (adminTab === "contas" && hash === "#admin-sidebar-sections-card") {'
    insercao = '''    if (adminTab === "sessoes" ||
      String(parametros.get("sidebar_sections_tab") || "").trim().toLowerCase() === "sessoes" ||
      parametros.has("sidebar_section_edit_key")) {
      return "sessoes";
    }

'''
    if alvo in top_menu_js:
        top_menu_js = top_menu_js.replace(alvo, insercao + alvo, 1)

write_text_v34(TOP_MENU_JS_PATH, top_menu_js)

print("OK: top_menu_active_v1.js validado com URL correta de Sessões.")


####################################################################################
# (6) ATUALIZAR CACHE BUSTER
####################################################################################

for template_file in (ROOT / "templates").rglob("*.html"):
    content = read_text_v34(template_file)
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
        write_text_v34(template_file, content)
        print(f"OK: cache buster atualizado em {template_file}")


####################################################################################
# (7) VALIDAR CONTEUDO FINAL
####################################################################################

template_validado = read_text_v34(TEMPLATE_PATH)
sidebar_validado = read_text_v34(SIDEBAR_JS_PATH)
top_validado = read_text_v34(TOP_MENU_JS_PATH)

template_normalizado = normalizar_texto_v34(strip_tags_v34(template_validado))

if "sessoes do sidebar" in template_normalizado:
    fail_v34("texto legado 'Sessões do sidebar' ainda existe no template.")

if "APPVERBO_SESSOES_SERVER_RENDER" in template_validado and "sessoes do sidebar" in normalizar_texto_v34(template_validado):
    fail_v34("bloco server-render legado de Sessões ainda existe no template.")

tabs_sections = find_menu_tabs_sections_v34(template_validado)

if len(tabs_sections) != 1:
    fail_v34(f"deve existir exatamente 1 menu-tabs-card; encontrado: {len(tabs_sections)}")

container_open_end = find_main_container_open_end_v34(template_validado)
conteudo_entre_container_e_tabs = template_validado[container_open_end:tabs_sections[0].start()].strip()

if conteudo_entre_container_e_tabs:
    fail_v34("menu-tabs-card não está como primeiro elemento do container central.")

if NEW_SESSOES_URL not in top_validado:
    fail_v34("URL correta de Sessões ausente em top_menu_active_v1.js.")

if "function existeServerRenderSessoes_v32()" not in sidebar_validado:
    fail_v34("função existeServerRenderSessoes_v32 ausente em sidebar_sections_layout_v1.js.")

if "APPVERBO_GUARD_OBTER_CARD_CRIACAO_SESSOES_V32" not in sidebar_validado:
    fail_v34("guard obter card de criação V32 ausente em sidebar_sections_layout_v1.js.")

if "APPVERBO_GUARD_MOVER_CARD_CRIACAO_SESSOES_V32" not in sidebar_validado:
    fail_v34("guard mover card de criação V32 ausente em sidebar_sections_layout_v1.js.")

for file_path in [TEMPLATE_PATH, SIDEBAR_JS_PATH, TOP_MENU_JS_PATH]:
    content = read_text_v34(file_path)
    if not content.endswith("\n"):
        fail_v34(f"ficheiro sem newline final: {file_path}")
    if content.endswith("\n\n"):
        fail_v34(f"ficheiro com linha em branco extra no EOF: {file_path}")

print("OK: validações V34 concluídas.")
