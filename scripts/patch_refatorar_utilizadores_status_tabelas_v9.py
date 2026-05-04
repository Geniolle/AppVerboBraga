from __future__ import annotations

import re
from pathlib import Path


####################################################################################
# (1) UTILITÁRIOS
####################################################################################

def read_text_v9(path: str) -> str:
    return Path(path).read_text(encoding="utf-8-sig")


def write_text_v9(path: str, content: str) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content.rstrip() + "\n", encoding="utf-8")


def require_v9(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


####################################################################################
# (2) CRIAR SERVIÇO REUTILIZÁVEL DE STATUS
####################################################################################

def write_user_status_service_v9() -> None:
    content = '''from __future__ import annotations

from typing import Any


####################################################################################
# (1) CONSTANTES CANÓNICAS DE STATUS DE UTILIZADOR
####################################################################################

USER_ACCOUNT_STATUS_ACTIVE_V1 = "active"
USER_ACCOUNT_STATUS_PENDING_V1 = "pending"
USER_ACCOUNT_STATUS_INACTIVE_V1 = "inactive"
USER_ACCOUNT_STATUS_BLOCKED_V1 = "blocked"


####################################################################################
# (2) NORMALIZAÇÃO E LABELS DE STATUS
####################################################################################

def normalize_user_account_status_v1(raw_status: Any) -> str:
    value = str(raw_status or "").strip().lower()

    status_aliases = {
        "ativo": USER_ACCOUNT_STATUS_ACTIVE_V1,
        "activa": USER_ACCOUNT_STATUS_ACTIVE_V1,
        "ativa": USER_ACCOUNT_STATUS_ACTIVE_V1,
        "inativo": USER_ACCOUNT_STATUS_INACTIVE_V1,
        "inactiva": USER_ACCOUNT_STATUS_INACTIVE_V1,
        "inativa": USER_ACCOUNT_STATUS_INACTIVE_V1,
        "pendente": USER_ACCOUNT_STATUS_PENDING_V1,
        "bloqueado": USER_ACCOUNT_STATUS_BLOCKED_V1,
        "bloqueada": USER_ACCOUNT_STATUS_BLOCKED_V1,
    }

    return status_aliases.get(value, value)


def user_account_status_label_pt_v1(raw_status: Any) -> str:
    normalized_status = normalize_user_account_status_v1(raw_status)

    status_label_map = {
        USER_ACCOUNT_STATUS_ACTIVE_V1: "Ativo",
        USER_ACCOUNT_STATUS_PENDING_V1: "Pendente",
        USER_ACCOUNT_STATUS_INACTIVE_V1: "Inativo",
        USER_ACCOUNT_STATUS_BLOCKED_V1: "Bloqueado",
    }

    return status_label_map.get(normalized_status, normalized_status or "-")


####################################################################################
# (3) PREDICADOS REUTILIZÁVEIS
####################################################################################

def is_user_account_status_active_v1(raw_status: Any) -> bool:
    return normalize_user_account_status_v1(raw_status) == USER_ACCOUNT_STATUS_ACTIVE_V1


def is_user_account_status_pending_v1(raw_status: Any) -> bool:
    return normalize_user_account_status_v1(raw_status) == USER_ACCOUNT_STATUS_PENDING_V1


def is_user_account_status_inactive_v1(raw_status: Any) -> bool:
    return normalize_user_account_status_v1(raw_status) == USER_ACCOUNT_STATUS_INACTIVE_V1


def is_user_account_status_blocked_v1(raw_status: Any) -> bool:
    return normalize_user_account_status_v1(raw_status) == USER_ACCOUNT_STATUS_BLOCKED_V1
'''

    write_text_v9("appverbo/services/user_status.py", content)


####################################################################################
# (3) CRIAR PARTIAL REUTILIZÁVEL DA TABELA DE UTILIZADORES
####################################################################################

def write_admin_user_table_partial_v9() -> None:
    content = '''{% macro render_admin_user_table_v1(rows, table_id, empty_message, allow_delete=False) %}
{% if rows %}
<table id="{{ table_id }}">
  <thead>
    <tr>
      <th>ID</th>
      <th>Nome</th>
      <th>Email</th>
      <th>Telefone</th>
      <th>Entidade</th>
      <th>Perfil</th>
      <th>Estado</th>
      <th>Criado em</th>
      <th>Ações</th>
    </tr>
  </thead>
  <tbody>
    {% for row in rows %}
    <tr>
      <td>{{ row.id }}</td>
      <td>{{ row.full_name }}</td>
      <td>{{ row.login_email }}</td>
      <td>{{ row.primary_phone }}</td>
      <td>{{ row.entity_name }}</td>
      <td>{{ row.profile_name }}</td>
      <td>
        {% if row.account_status_is_active or row.account_status == "active" %}
        <span class="entity-status entity-status-active">
          {{ row.account_status_label if row.account_status_label is defined else "Ativo" }}
        </span>
        {% elif row.account_status_is_inactive or row.account_status == "inactive" %}
        <span class="entity-status entity-status-inactive">
          {{ row.account_status_label if row.account_status_label is defined else "Inativo" }}
        </span>
        {% else %}
        <span class="entity-status entity-status-inactive">
          {{ row.account_status_label if row.account_status_label is defined else row.account_status }}
        </span>
        {% endif %}
      </td>
      <td>{{ row.created_at }}</td>
      <td>
        <div class="table-actions">
          <a
            class="table-icon-btn"
            href="/users/new?menu=administrativo&admin_tab=utilizador&user_edit_id={{ row.id }}&user_view=1#edit-user-card"
            title="Exibir utilizador"
          >
            &#128065;
          </a>
          <a
            class="table-icon-btn"
            href="/users/new?menu=administrativo&admin_tab=utilizador&user_edit_id={{ row.id }}#edit-user-card"
            title="Modificar utilizador"
          >
            &#9998;
          </a>
          {% if allow_delete %}
          <form method="post" action="/users/delete" onsubmit="return confirm('Tem a certeza que pretende eliminar este utilizador');">
            <input type="hidden" name="user_id" value="{{ row.id }}">
            <button
              type="submit"
              class="table-icon-btn table-icon-btn-danger"
              title="Eliminar utilizador"
            >
              &#128465;
            </button>
          </form>
          {% endif %}
        </div>
      </td>
    </tr>
    {% endfor %}
  </tbody>
</table>
<div class="table-footer admin-status-table-footer-v1">
  <select aria-label="Entradas por página">
    <option selected>5</option>
  </select>
  <span>entradas por página</span>
  <div class="pagination">
    <button type="button" disabled>&lsaquo;</button>
    <button type="button" class="active">1</button>
    <button type="button" disabled>&rsaquo;</button>
  </div>
</div>
{% else %}
<p class="empty">{{ empty_message }}</p>
{% endif %}
{% endmacro %}
'''

    write_text_v9("templates/partials/admin_user_table_v1.html", content)


####################################################################################
# (4) CRIAR CSS MODULAR REUTILIZÁVEL
####################################################################################

def write_admin_status_tables_css_v9() -> None:
    content = '''/* APPVERBO_ADMIN_STATUS_TABLES_V1_START */

.admin-status-table-footer-v1 {
  align-items: center;
  border-top: 1px solid #d8e0ec;
  display: flex;
  gap: 8px;
  justify-content: flex-start;
  margin-top: 10px;
  padding-top: 10px;
}

.admin-status-table-footer-v1 select {
  max-width: 72px;
  min-width: 64px;
  width: auto;
}

.admin-status-table-footer-v1 .pagination {
  margin-left: auto;
}

.admin-status-table-footer-v1 .pagination button {
  align-items: center;
  border-radius: 999px;
  display: inline-flex;
  font-size: 12px;
  height: 22px;
  justify-content: center;
  min-width: 26px;
  padding: 0 8px;
}

.entity-status {
  align-items: center;
  border-radius: 999px;
  display: inline-flex;
  font-size: 11px;
  font-weight: 700;
  line-height: 1;
  padding: 4px 8px;
  white-space: nowrap;
}

.entity-status-active {
  background: #e6f7ec;
  border: 1px solid #a9dfbd;
  color: #087333;
}

.entity-status-inactive {
  background: #fdeaea;
  border: 1px solid #f1b4b4;
  color: #b42318;
}

/* APPVERBO_ADMIN_STATUS_TABLES_V1_END */
'''

    write_text_v9("static/css/modules/admin_status_tables_v1.css", content)


####################################################################################
# (5) PATCH DO PAGE SERVICE PARA USAR SERVIÇO REUTILIZÁVEL
####################################################################################

def patch_page_service_v9() -> None:
    path = "appverbo/services/page.py"
    content = read_text_v9(path)

    import_block = '''from appverbo.services.user_status import (
    is_user_account_status_active_v1,
    is_user_account_status_inactive_v1,
    normalize_user_account_status_v1,
    user_account_status_label_pt_v1,
)
'''

    if "from appverbo.services.user_status import (" not in content:
        content = content.replace(
            "from appverbo.services.permissions import get_user_entity_permissions\n",
            "from appverbo.services.permissions import get_user_entity_permissions\n" + import_block,
            1,
        )

    content = re.sub(
        r'\n\s*# APPVERBO_USER_STATUS_LABEL_PT_V1_START[\s\S]*?# APPVERBO_USER_STATUS_LABEL_PT_V1_END\n?',
        "\n",
        content,
        flags=re.S,
    )

    content = content.replace(
        "normalize_user_account_status_v1(row.account_status) == UserAccountStatus.ACTIVE.value",
        "is_user_account_status_active_v1(row.account_status)",
    )

    content = content.replace(
        "normalize_user_account_status_v1(row.account_status) == UserAccountStatus.INACTIVE.value",
        "is_user_account_status_inactive_v1(row.account_status)",
    )

    content = content.replace(
        'row["account_status"] == UserAccountStatus.ACTIVE.value',
        'is_user_account_status_active_v1(row["account_status"])',
    )

    content = content.replace(
        'row["account_status"] == UserAccountStatus.INACTIVE.value',
        'is_user_account_status_inactive_v1(row["account_status"])',
    )

    require_v9(
        "from appverbo.services.user_status import (" in content,
        "ERRO: import do serviço user_status não foi inserido em page.py.",
    )

    require_v9(
        "APPVERBO_USER_STATUS_LABEL_PT_V1_START" not in content,
        "ERRO: helper antigo de status ainda existe dentro de page.py.",
    )

    require_v9(
        "is_user_account_status_active_v1" in content,
        "ERRO: page.py não usa is_user_account_status_active_v1.",
    )

    require_v9(
        "is_user_account_status_inactive_v1" in content,
        "ERRO: page.py não usa is_user_account_status_inactive_v1.",
    )

    require_v9(
        "active_created_users = [" in content and "inactive_users = [" in content,
        "ERRO: listas active_created_users/inactive_users não foram encontradas em page.py.",
    )

    write_text_v9(path, content)


####################################################################################
# (6) PATCH DO DELETE HANDLER PARA USAR SERVIÇO REUTILIZÁVEL
####################################################################################

def patch_delete_handler_v9() -> None:
    path = "appverbo/routes/users/delete_handler.py"
    content = read_text_v9(path)

    if "from appverbo.services.user_status import is_user_account_status_inactive_v1" not in content:
        import_anchor = "from appverbo.services"
        first_service_import = content.find(import_anchor)

        require_v9(
            first_service_import >= 0,
            "ERRO: não foi possível encontrar imports de services em delete_handler.py.",
        )

        line_start = content.rfind("\n", 0, first_service_import) + 1
        content = (
            content[:line_start]
            + "from appverbo.services.user_status import is_user_account_status_inactive_v1\n"
            + content[line_start:]
        )

    content = content.replace(
        'str(user.account_status or "").strip().lower() != UserAccountStatus.INACTIVE.value',
        "not is_user_account_status_inactive_v1(user.account_status)",
    )

    require_v9(
        "Só é permitido eliminar utilizadores inativos." in content,
        "ERRO: regra de eliminação apenas para inativos não encontrada.",
    )

    require_v9(
        "not is_user_account_status_inactive_v1(user.account_status)" in content,
        "ERRO: delete_handler.py não usa is_user_account_status_inactive_v1.",
    )

    write_text_v9(path, content)


####################################################################################
# (7) PATCH DO TEMPLATE PARA USAR PARTIAL REUTILIZÁVEL
####################################################################################

def active_users_section_v9() -> str:
    return '''        <!-- APPVERBO_ADMIN_USERS_ACTIVE_SECTION_V9_START -->
        <section id="admin-users-created-card" class="card" data-menu-scope="administrativo">
          <h2>Utilizadores criados</h2>
          {{ render_admin_user_table_v1(
            active_created_users,
            "admin-users-table",
            "Sem utilizadores ativos.",
            false
          ) }}
        </section>
        <!-- APPVERBO_ADMIN_USERS_ACTIVE_SECTION_V9_END -->'''


def inactive_users_section_v9() -> str:
    return '''        <!-- APPVERBO_ADMIN_USERS_INACTIVE_SECTION_V9_START -->
        <section id="inactive-users-card" class="card" data-menu-scope="administrativo">
          <h2>Utilizadores inativos</h2>
          {{ render_admin_user_table_v1(
            inactive_users,
            "inactive-users-table",
            "Sem utilizadores inativos.",
            true
          ) }}
        </section>
        <!-- APPVERBO_ADMIN_USERS_INACTIVE_SECTION_V9_END -->'''


def patch_template_v9() -> None:
    path = "templates/new_user.html"
    content = read_text_v9(path)

    macro_import = '{% from "partials/admin_user_table_v1.html" import render_admin_user_table_v1 %}'

    if macro_import not in content:
        content = content.replace(
            '{% extends "base.html" %}',
            '{% extends "base.html" %}\n' + macro_import,
            1,
        )

    css_links = [
        '<link rel="stylesheet" href="/static/css/modules/admin_status_tables_v1.css?v=20260504-admin-status-tables-v1">',
    ]

    for css_link in css_links:
        if css_link not in content:
            content = content.replace(
                '<link rel="stylesheet" href="/static/css/new_user.css?v=',
                css_link + '\n  <link rel="stylesheet" href="/static/css/new_user.css?v=',
                1,
            )

    content = re.sub(
        r'/static/js/new_user\.js\?v=[^"]+',
        '/static/js/new_user.js?v=20260504-users-refactor-v9',
        content,
        count=1,
    )

    replacement = active_users_section_v9() + "\n\n" + inactive_users_section_v9()

    old_combined_patterns = [
        r'\n?\s*<!-- APPVERBO_ADMIN_USERS_ACTIVE_SECTION_V7_START -->[\s\S]*?<!-- APPVERBO_ADMIN_USERS_INACTIVE_SECTION_V7_END -->\n?',
        r'\n?\s*<!-- APPVERBO_ADMIN_USERS_ACTIVE_SECTION_V6_START -->[\s\S]*?<!-- APPVERBO_ADMIN_USERS_INACTIVE_SECTION_V6_END -->\n?',
        r'\n?\s*<!-- APPVERBO_ADMIN_USERS_ACTIVE_INACTIVE_SECTION_V5_START -->[\s\S]*?<!-- APPVERBO_ADMIN_USERS_ACTIVE_INACTIVE_SECTION_V5_END -->\n?',
        r'\n?\s*<!-- APPVERBO_ADMIN_USERS_ACTIVE_SECTION_V9_START -->[\s\S]*?<!-- APPVERBO_ADMIN_USERS_INACTIVE_SECTION_V9_END -->\n?',
    ]

    replaced = False

    for pattern in old_combined_patterns:
        if re.search(pattern, content, flags=re.S):
            content = re.sub(pattern, "\n" + replacement + "\n", content, count=1, flags=re.S)
            replaced = True
            break

    if not replaced:
        section_match = re.search(
            r'\n?\s*<section\b[^>]*\bid=(["\'])admin-users-created-card\1[^>]*>[\s\S]*?</section>\n?',
            content,
            flags=re.S | re.I,
        )

        require_v9(
            section_match is not None,
            "ERRO: não foi possível localizar bloco admin-users-created-card para substituir.",
        )

        content = content[: section_match.start()] + "\n" + replacement + "\n" + content[section_match.end():]

    legacy_markers = [
        ("APPVERBO_ADMIN_USERS_ACTIVE_SECTION_V7_START", "APPVERBO_ADMIN_USERS_ACTIVE_SECTION_V7_END"),
        ("APPVERBO_ADMIN_USERS_INACTIVE_SECTION_V7_START", "APPVERBO_ADMIN_USERS_INACTIVE_SECTION_V7_END"),
        ("APPVERBO_ADMIN_USERS_ACTIVE_SECTION_V6_START", "APPVERBO_ADMIN_USERS_ACTIVE_SECTION_V6_END"),
        ("APPVERBO_ADMIN_USERS_INACTIVE_SECTION_V6_START", "APPVERBO_ADMIN_USERS_INACTIVE_SECTION_V6_END"),
        ("APPVERBO_ADMIN_USERS_ACTIVE_INACTIVE_SECTION_V5_START", "APPVERBO_ADMIN_USERS_ACTIVE_INACTIVE_SECTION_V5_END"),
        ("APPVERBO_ACTIVE_USERS_SECTION_V4_START", "APPVERBO_ACTIVE_USERS_SECTION_V4_END"),
        ("APPVERBO_INACTIVE_USERS_SECTION_V4_START", "APPVERBO_INACTIVE_USERS_SECTION_V4_END"),
        ("APPVERBO_INACTIVE_USERS_SECTION_V3_START", "APPVERBO_INACTIVE_USERS_SECTION_V3_END"),
        ("APPVERBO_INACTIVE_USERS_SECTION_V2_START", "APPVERBO_INACTIVE_USERS_SECTION_V2_END"),
        ("APPVERBO_INACTIVE_USERS_SECTION_V1_START", "APPVERBO_INACTIVE_USERS_SECTION_V1_END"),
    ]

    for start_marker, end_marker in legacy_markers:
        content = re.sub(
            r'\n?\s*<!-- ' + re.escape(start_marker) + r' -->[\s\S]*?<!-- ' + re.escape(end_marker) + r' -->\n?',
            "\n",
            content,
            flags=re.S,
        )

    require_v9(
        "APPVERBO_ADMIN_USERS_ACTIVE_SECTION_V9_START" in content,
        "ERRO: bloco ativo V9 não foi inserido.",
    )

    require_v9(
        "APPVERBO_ADMIN_USERS_INACTIVE_SECTION_V9_START" in content,
        "ERRO: bloco inativo V9 não foi inserido.",
    )

    require_v9(
        "render_admin_user_table_v1" in content,
        "ERRO: template não usa partial render_admin_user_table_v1.",
    )

    require_v9(
        '<section id="inactive-users-card" class="card"' in content,
        "ERRO: inativos não estão em card separado.",
    )

    require_v9(
        "SuperUsers de Entidade" not in content,
        "ERRO: bloco SuperUsers de Entidade ainda existe.",
    )

    require_v9(
        "entity-status-inactive{% else %}" not in content,
        "ERRO: ainda existe Jinja quebrado no template.",
    )

    write_text_v9(path, content)


####################################################################################
# (8) PATCH DO JS PARA REMOVER GUARD E CORRIGIR A CAUSA
####################################################################################

def patch_new_user_js_v9() -> None:
    path = "static/js/new_user.js"
    content = read_text_v9(path)

    content = re.sub(
        r'\n?// APPVERBO_ADMIN_INACTIVE_USERS_VISIBILITY_V8_START[\s\S]*?// APPVERBO_ADMIN_INACTIVE_USERS_VISIBILITY_V8_END\n?',
        "\n",
        content,
        flags=re.S,
    )

    if 'card.id === "inactive-users-card"' not in content:
        content = content.replace(
            'card.id === "admin-users-created-card"',
            'card.id === "admin-users-created-card" ||\n        card.id === "inactive-users-card"',
            1,
        )

    require_v9(
        'card.id === "inactive-users-card"' in content,
        "ERRO: inactive-users-card não foi incluído na lógica principal do JS.",
    )

    require_v9(
        "APPVERBO_ADMIN_INACTIVE_USERS_VISIBILITY_V8_START" not in content,
        "ERRO: guard V8 ainda existe no JS.",
    )

    write_text_v9(path, content)


####################################################################################
# (9) LIMPAR CSS ANTIGO NO new_user.css
####################################################################################

def patch_new_user_css_v9() -> None:
    path = "static/css/new_user.css"
    content = read_text_v9(path)

    marker_prefixes = [
        "APPVERBO_ADMIN_USERS_ACTIVE_INACTIVE_LAYOUT_V5",
        "APPVERBO_ADMIN_USERS_SEPARATE_CARDS_LAYOUT_V6",
        "APPVERBO_ADMIN_USERS_SEPARATE_CARDS_LAYOUT_V7",
    ]

    for marker_prefix in marker_prefixes:
        content = re.sub(
            r'/\* ' + re.escape(marker_prefix) + r'_START \*/[\s\S]*?/\* ' + re.escape(marker_prefix) + r'_END \*/',
            "",
            content,
            flags=re.S,
        )

    write_text_v9(path, content)


####################################################################################
# (10) ATUALIZAR AGENTS.md COM A REGRA DA NOVA ESTRUTURA
####################################################################################

def patch_agents_v9() -> None:
    path = "AGENTS.md"
    content = read_text_v9(path)

    block = '''
<!-- APPVERBO_RULE_USER_STATUS_REFACTOR_V1_START -->
## Regra padrão: reutilização de status e tabelas administrativas

Sempre que houver listagens administrativas com status de utilizador:

1. A normalização e tradução visual do status do utilizador devem ficar em `appverbo/services/user_status.py`.
2. Não duplicar lógica de status diretamente em `page.py`, handlers ou templates.
3. O banco deve guardar valores canónicos em inglês:
   - `active`
   - `inactive`
   - `pending`
   - `blocked`
4. O português deve ser apenas label visual:
   - `Ativo`
   - `Inativo`
   - `Pendente`
   - `Bloqueado`
5. Tabelas administrativas de utilizadores devem usar partial reutilizável em `templates/partials/admin_user_table_v1.html`.
6. CSS de rodapé, paginação e badges de status deve ficar em módulo reutilizável dentro de `static/css/modules`.
7. Não criar guard JavaScript para reexibir card oculto se a causa puder ser corrigida na lista principal de cards da aba.
8. Se uma nova listagem tiver ativos/inativos, usar cards separados e reutilizar a estrutura existente antes de criar novo HTML duplicado.
<!-- APPVERBO_RULE_USER_STATUS_REFACTOR_V1_END -->
'''

    if "APPVERBO_RULE_USER_STATUS_REFACTOR_V1_START" not in content:
        content = content.rstrip() + "\n\n" + block.strip() + "\n"

    write_text_v9(path, content)


####################################################################################
# (11) VALIDAÇÕES DO PATCH
####################################################################################

def validate_v9() -> None:
    status_service = read_text_v9("appverbo/services/user_status.py")
    page_service = read_text_v9("appverbo/services/page.py")
    delete_handler = read_text_v9("appverbo/routes/users/delete_handler.py")
    template = read_text_v9("templates/new_user.html")
    partial = read_text_v9("templates/partials/admin_user_table_v1.html")
    js = read_text_v9("static/js/new_user.js")
    css_module = read_text_v9("static/css/modules/admin_status_tables_v1.css")
    agents = read_text_v9("AGENTS.md")

    checks = {
        "service normalize": "def normalize_user_account_status_v1" in status_service,
        "service label": "def user_account_status_label_pt_v1" in status_service,
        "service active predicate": "def is_user_account_status_active_v1" in status_service,
        "service inactive predicate": "def is_user_account_status_inactive_v1" in status_service,
        "page imports service": "from appverbo.services.user_status import (" in page_service,
        "page no nested old helper": "APPVERBO_USER_STATUS_LABEL_PT_V1_START" not in page_service,
        "page active list": "active_created_users = [" in page_service,
        "page inactive list": "inactive_users = [" in page_service,
        "delete uses service": "not is_user_account_status_inactive_v1(user.account_status)" in delete_handler,
        "template imports macro": "partials/admin_user_table_v1.html" in template,
        "template active V9": "APPVERBO_ADMIN_USERS_ACTIVE_SECTION_V9_START" in template,
        "template inactive V9": "APPVERBO_ADMIN_USERS_INACTIVE_SECTION_V9_START" in template,
        "template uses macro": "render_admin_user_table_v1" in template,
        "template inactive separate card": '<section id="inactive-users-card" class="card"' in template,
        "template no SuperUsers": "SuperUsers de Entidade" not in template,
        "partial macro": "macro render_admin_user_table_v1" in partial,
        "partial delete conditional": "{% if allow_delete %}" in partial,
        "js inactive card in main logic": 'card.id === "inactive-users-card"' in js,
        "js no V8 guard": "APPVERBO_ADMIN_INACTIVE_USERS_VISIBILITY_V8_START" not in js,
        "css module": "APPVERBO_ADMIN_STATUS_TABLES_V1_START" in css_module,
        "agents rule": "APPVERBO_RULE_USER_STATUS_REFACTOR_V1_START" in agents,
        "no broken jinja": "entity-status-inactive{% else %}" not in template,
    }

    failed = [name for name, ok in checks.items() if not ok]

    require_v9(
        not failed,
        "Falha na validação: " + ", ".join(failed),
    )


####################################################################################
# (12) MAIN
####################################################################################

def main_v9() -> None:
    write_user_status_service_v9()
    write_admin_user_table_partial_v9()
    write_admin_status_tables_css_v9()
    patch_page_service_v9()
    patch_delete_handler_v9()
    patch_template_v9()
    patch_new_user_js_v9()
    patch_new_user_css_v9()
    patch_agents_v9()
    validate_v9()


if __name__ == "__main__":
    main_v9()
