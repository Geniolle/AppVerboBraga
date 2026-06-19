from __future__ import annotations

import re
from pathlib import Path


####################################################################################
# (1) UTILITÁRIOS
####################################################################################

ROOT = Path(__file__).resolve().parents[1]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def remove_marked_block(content: str, start_marker: str, end_marker: str) -> str:
    while start_marker in content and end_marker in content:
        start_index = content.index(start_marker)
        end_index = content.index(end_marker, start_index)
        line_end_index = content.find("\n", end_index)

        if line_end_index == -1:
            line_end_index = len(content)
        else:
            line_end_index += 1

        content = content[:start_index] + content[line_end_index:]

    return content


####################################################################################
# (2) REMOVER DEBUG TEMPORÁRIO DO PAGE_HANDLER, MANTENDO O TARGET GUARD
####################################################################################

page_handler_path = ROOT / "appverbo" / "routes" / "profile" / "page_handler.py"
page_content = read_text(page_handler_path)

page_content = remove_marked_block(
    page_content,
    "    # APPVERBO_UTILIZADOR_ACTION_DEBUG_V1_START",
    "    # APPVERBO_UTILIZADOR_ACTION_DEBUG_V1_END",
)

page_content = remove_marked_block(
    page_content,
    "    # APPVERBO_UTILIZADOR_ACTION_DEBUG_V2_START",
    "    # APPVERBO_UTILIZADOR_ACTION_DEBUG_V2_END",
)

if "APPVERBO_UTILIZADOR_ACTION_DEBUG_V1" in page_content:
    raise RuntimeError("Debug temporário V1 ainda existe no page_handler.py.")

if "APPVERBO_UTILIZADOR_ACTION_DEBUG_V2" in page_content:
    raise RuntimeError("Debug temporário V2 ainda existe no page_handler.py.")

if "APPVERBO_PAGE_HANDLER_UTILIZADOR_EDIT_TARGET_V2_START" not in page_content:
    raise RuntimeError("Target guard do Utilizador não encontrado no page_handler.py.")

if 'initial_menu_target = "#edit-user-card"' not in page_content:
    raise RuntimeError("Target #edit-user-card não encontrado no page_handler.py.")

write_text(page_handler_path, page_content)


####################################################################################
# (3) GARANTIR CACHE BUST V14 E TEXTO FINAL NO PARTIAL
####################################################################################

partial_path = ROOT / "templates" / "partials" / "admin_user_shadow_readonly_v1.html"
partial_content = read_text(partial_path)

partial_content = re.sub(
    r'admin_user_shadow_table_v1\.js\?v=[^"]+',
    '$120260513-utilizador-view-toggle-v5',
    partial_content,
)

partial_content = re.sub(
    r'admin_user_shadow_table_v1\.css\?v=[^"]+',
    'admin_user_shadow_table_v1.css?v=20260512-utilizador-shadow-layout-v14',
    partial_content,
)

partial_content = partial_content.replace(
    "Validação do novo processo único. Este bloco usa a leitura nativa com pesquisa, paginação e ações legadas.",
    "Leitura nativa do processo Utilizador com pesquisa, paginação, visualização e edição.",
)

required_partial_tokens = (
    "data-admin-user-shadow-real-link=\"view\"",
    "data-admin-user-shadow-real-link=\"edit\"",
    "user_view=1&target=edit-user-card#edit-user-card",
    "user_edit_id=",
    "target=edit-user-card#edit-user-card",
    "utilizador-shadow-table-v14",
)

missing_partial_tokens = [
    token
    for token in required_partial_tokens
    if token not in partial_content
]

if missing_partial_tokens:
    raise RuntimeError(
        "Tokens esperados ausentes no partial nativo do Utilizador: "
        + ", ".join(missing_partial_tokens)
    )

write_text(partial_path, partial_content)


####################################################################################
# (4) GARANTIR JS COM NAVEGAÇÃO FORÇADA E FOCO NO CARD DE EDIÇÃO
####################################################################################

js_path = ROOT / "static" / "js" / "modules" / "admin_user_shadow_table_v1.js"
js_content = read_text(js_path)

required_js_tokens = (
    "forceNativeActionNavigation",
    "window.location.assign",
    "focusEditUserCardFromQuery",
    "edit-user-card",
    "scrollIntoView",
    'document.addEventListener("click", forceNativeActionNavigation, true)',
)

missing_js_tokens = [
    token
    for token in required_js_tokens
    if token not in js_content
]

if missing_js_tokens:
    raise RuntimeError(
        "Tokens esperados ausentes no JS nativo do Utilizador: "
        + ", ".join(missing_js_tokens)
    )

write_text(js_path, js_content)


####################################################################################
# (5) ATUALIZAR VALIDAÇÃO DO TEMPLATE E JS
####################################################################################

check_template_path = ROOT / "scripts" / "check_template_jinja_utilizador_shadow_v1.py"

check_template_content = '''\
from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

root = Path.cwd()
env = Environment(loader=FileSystemLoader(str(root / "templates")))

env.get_template("new_user.html")
env.get_template("partials/admin_user_shadow_readonly_v1.html")

page_handler_source = (root / "appverbo" / "routes" / "profile" / "page_handler.py").read_text(
    encoding="utf-8"
)
partial_source = (root / "templates" / "partials" / "admin_user_shadow_readonly_v1.html").read_text(
    encoding="utf-8"
)
js_source = (root / "static" / "js" / "modules" / "admin_user_shadow_table_v1.js").read_text(
    encoding="utf-8"
)

if "APPVERBO_UTILIZADOR_ACTION_DEBUG_V1" in page_handler_source:
    raise RuntimeError("Debug temporário V1 ainda existe no page_handler.py.")

if "APPVERBO_UTILIZADOR_ACTION_DEBUG_V2" in page_handler_source:
    raise RuntimeError("Debug temporário V2 ainda existe no page_handler.py.")

required_page_tokens = (
    "APPVERBO_PAGE_HANDLER_UTILIZADOR_EDIT_TARGET_V2_START",
    "resolved_admin_tab == \\"utilizador\\"",
    "parsed_user_edit_id is not None",
    "initial_menu_target = \\"#edit-user-card\\"",
)

required_partial_tokens = (
    "render_admin_user_shadow_readonly_v12",
    "data-admin-user-shadow-real-link=\\"view\\"",
    "data-admin-user-shadow-real-link=\\"edit\\"",
    "user_view=1&target=edit-user-card#edit-user-card",
    "user_edit_id=",
    "target=edit-user-card#edit-user-card",
    "utilizador-shadow-table-v14",
)

required_js_tokens = (
    "forceNativeActionNavigation",
    "window.location.assign",
    "focusEditUserCardFromQuery",
    "edit-user-card",
    "scrollIntoView",
    "document.addEventListener(\\"click\\", forceNativeActionNavigation, true)",
)

missing_page_tokens = [
    token
    for token in required_page_tokens
    if token not in page_handler_source
]

missing_partial_tokens = [
    token
    for token in required_partial_tokens
    if token not in partial_source
]

missing_js_tokens = [
    token
    for token in required_js_tokens
    if token not in js_source
]

if missing_page_tokens:
    raise RuntimeError(
        "Tokens esperados ausentes no page_handler.py: "
        + ", ".join(missing_page_tokens)
    )

if missing_partial_tokens:
    raise RuntimeError(
        "Tokens esperados ausentes no partial nativo do Utilizador: "
        + ", ".join(missing_partial_tokens)
    )

if missing_js_tokens:
    raise RuntimeError(
        "Tokens esperados ausentes no JS nativo do Utilizador: "
        + ", ".join(missing_js_tokens)
    )

print("OK: templates Jinja carregados com sucesso.")
print("OK: Utilizador nativo validado com visualizar, editar e sem debug temporário.")
'''

write_text(check_template_path, check_template_content)


####################################################################################
# (6) ATUALIZAR VALIDAÇÃO DOS HREFS RENDERIZADOS
####################################################################################

render_check_path = ROOT / "scripts" / "check_render_utilizador_shadow_links_v1.py"

render_check_content = '''\
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from jinja2 import Environment, FileSystemLoader

root = Path.cwd()
env = Environment(loader=FileSystemLoader(str(root / "templates")))
template = env.get_template("partials/admin_user_shadow_readonly_v1.html")

columns = (
    SimpleNamespace(label="ID", source="id"),
    SimpleNamespace(label="NOME", source="full_name"),
    SimpleNamespace(label="EMAIL", source="login_email"),
    SimpleNamespace(label="ESTADO", source="status_label"),
)

state = SimpleNamespace(
    config=SimpleNamespace(
        active_title="Utilizadores ativos",
        inactive_title="Utilizadores inativos",
        columns=columns,
    ),
    active_rows=[
        {
            "id": 25,
            "full_name": "Teste Utilizador",
            "login_email": "teste@appverbo.local",
            "status": "active",
            "status_label": "Ativo",
        }
    ],
    inactive_rows=[],
)

html = template.module.render_admin_user_shadow_readonly_v12(state)

expected_view_href = (
    "/users/new?menu=administrativo&admin_tab=utilizador"
    "&user_edit_id=25&user_view=1&target=edit-user-card#edit-user-card"
)

expected_edit_href = (
    "/users/new?menu=administrativo&admin_tab=utilizador"
    "&user_edit_id=25&target=edit-user-card#edit-user-card"
)

required_fragments = (
    expected_view_href,
    expected_edit_href,
    'data-admin-user-shadow-real-link="view"',
    'data-admin-user-shadow-real-link="edit"',
)

missing_fragments = [
    fragment
    for fragment in required_fragments
    if fragment not in html
]

if missing_fragments:
    raise RuntimeError(
        "Links renderizados ausentes: "
        + ", ".join(missing_fragments)
    )

print("OK: href do olho renderizado corretamente.")
print("OK: href do lápis renderizado corretamente.")
'''

write_text(render_check_path, render_check_content)


####################################################################################
# (7) RESULTADO
####################################################################################

print("OK: debug temporário removido do page_handler.py.")
print("OK: target guard para #edit-user-card mantido.")
print("OK: href do lápis e do olho preservados.")
print("OK: validações atualizadas.")
