from __future__ import annotations

import re
from pathlib import Path


def read_text_v5(path: str) -> str:
    return Path(path).read_text(encoding="utf-8-sig")


def write_text_v5(path: str, content: str) -> None:
    Path(path).write_text(content.rstrip() + "\n", encoding="utf-8")


def require_v5(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def ensure_typing_any_v5(content: str) -> str:
    if "Any" in content:
        return content

    match = re.search(r"from typing import (?P<imports>[^\n]+)", content)
    if not match:
        return content

    imports = [item.strip() for item in match.group("imports").split(",") if item.strip()]
    if "Any" not in imports:
        imports.append("Any")

    imports_text = ", ".join(sorted(set(imports)))
    return content[:match.start()] + f"from typing import {imports_text}" + content[match.end():]


def ensure_page_context_v5() -> None:
    path = "appverbo/services/page.py"
    content = read_text_v5(path)
    content = ensure_typing_any_v5(content)

    if "APPVERBO_USER_STATUS_LABEL_PT_V1_START" not in content:
        helper_block = '''    # APPVERBO_USER_STATUS_LABEL_PT_V1_START
    def normalize_user_account_status_v1(raw_status: Any) -> str:
        return str(raw_status or "").strip().lower()

    def user_account_status_label_pt_v1(raw_status: Any) -> str:
        normalized_status = normalize_user_account_status_v1(raw_status)
        status_label_map = {
            UserAccountStatus.ACTIVE.value: "Ativo",
            UserAccountStatus.PENDING.value: "Pendente",
            UserAccountStatus.INACTIVE.value: "Inativo",
            UserAccountStatus.BLOCKED.value: "Bloqueado",
        }
        return status_label_map.get(normalized_status, normalized_status or "-")
    # APPVERBO_USER_STATUS_LABEL_PT_V1_END

'''
        content = content.replace("    all_users = [\n", helper_block + "    all_users = [\n", 1)

    if '"account_status_label": user_account_status_label_pt_v1(row.account_status),' not in content:
        content = content.replace(
            '            "account_status": row.account_status,\n',
            '            "account_status": normalize_user_account_status_v1(row.account_status),\n'
            '            "account_status_label": user_account_status_label_pt_v1(row.account_status),\n'
            '            "account_status_is_active": normalize_user_account_status_v1(row.account_status) == UserAccountStatus.ACTIVE.value,\n'
            '            "account_status_is_inactive": normalize_user_account_status_v1(row.account_status) == UserAccountStatus.INACTIVE.value,\n',
            1,
        )

    if '"account_status_is_active": normalize_user_account_status_v1(row.account_status) == UserAccountStatus.ACTIVE.value,' not in content:
        content = content.replace(
            '            "account_status_label": user_account_status_label_pt_v1(row.account_status),\n',
            '            "account_status_label": user_account_status_label_pt_v1(row.account_status),\n'
            '            "account_status_is_active": normalize_user_account_status_v1(row.account_status) == UserAccountStatus.ACTIVE.value,\n',
            1,
        )

    if '"account_status_is_inactive": normalize_user_account_status_v1(row.account_status) == UserAccountStatus.INACTIVE.value,' not in content:
        content = content.replace(
            '            "account_status_is_active": normalize_user_account_status_v1(row.account_status) == UserAccountStatus.ACTIVE.value,\n',
            '            "account_status_is_active": normalize_user_account_status_v1(row.account_status) == UserAccountStatus.ACTIVE.value,\n'
            '            "account_status_is_inactive": normalize_user_account_status_v1(row.account_status) == UserAccountStatus.INACTIVE.value,\n',
            1,
        )

    if "active_created_users = [" not in content:
        created_users_pattern = re.compile(
            r'    created_users = \[\n'
            r'        row for row in all_users if row\["account_status"\] != UserAccountStatus\.PENDING\.value\n'
            r'    \]\n',
            flags=re.S,
        )

        replacement = '''    created_users = [
        row for row in all_users if row["account_status"] != UserAccountStatus.PENDING.value
    ]
    active_created_users = [
        row for row in created_users if row["account_status"] == UserAccountStatus.ACTIVE.value
    ]
    inactive_users = [
        row for row in all_users if row["account_status"] == UserAccountStatus.INACTIVE.value
    ]
'''

        content, count = created_users_pattern.subn(replacement, content, count=1)
        require_v5(count == 1, "ERRO: não foi possível inserir active_created_users e inactive_users no page.py.")

    if '"active_created_users": active_created_users,' not in content:
        content = content.replace(
            '        "created_users": created_users,\n',
            '        "created_users": created_users,\n'
            '        "active_created_users": active_created_users,\n'
            '        "inactive_users": inactive_users,\n',
            1,
        )

    write_text_v5(path, content)


def ensure_delete_backend_rule_v5() -> None:
    path = "appverbo/routes/users/delete_handler.py"
    content = read_text_v5(path)

    if "APPVERBO_DELETE_ONLY_INACTIVE_USER_V1_START" in content:
        write_text_v5(path, content)
        return

    guard_block = '''        # APPVERBO_DELETE_ONLY_INACTIVE_USER_V1_START
        if str(user.account_status or "").strip().lower() != UserAccountStatus.INACTIVE.value:
            return RedirectResponse(
                url=build_users_new_url(
                    error="Só é permitido eliminar utilizadores inativos.",
                    menu="administrativo",
                    admin_tab="utilizador",
                )
                + "#create-user-card",
                status_code=status.HTTP_303_SEE_OTHER,
            )
        # APPVERBO_DELETE_ONLY_INACTIVE_USER_V1_END

'''

    pattern = re.compile(
        r'(?P<permission_block>'
        r'        if not _member_is_within_permissions\(\n'
        r'[\s\S]*?'
        r'            \)\n'
        r'\n'
        r')'
        r'(?P<next_block>        target_is_active_admin = \()',
        flags=re.S,
    )

    new_content, count = pattern.subn(
        lambda match: match.group("permission_block") + guard_block + match.group("next_block"),
        content,
        count=1,
    )

    require_v5(count == 1, "ERRO: não foi possível inserir regra global de delete apenas para inativos.")
    write_text_v5(path, new_content)


def admin_users_card_v5() -> str:
    return '''        <!-- APPVERBO_ADMIN_USERS_ACTIVE_INACTIVE_SECTION_V5_START -->
        <section id="admin-users-created-card" class="card" data-menu-scope="administrativo">
          <h2>Utilizadores criados</h2>
          {% if active_created_users %}
          <table id="admin-users-table">
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
              {% for row in active_created_users %}
              <tr>
                <td>{{ row.id }}</td>
                <td>{{ row.full_name }}</td>
                <td>{{ row.login_email }}</td>
                <td>{{ row.primary_phone }}</td>
                <td>{{ row.entity_name }}</td>
                <td>{{ row.profile_name }}</td>
                <td>
                  <span class="entity-status entity-status-active">
                    {{ row.account_status_label if row.account_status_label is defined else "Ativo" }}
                  </span>
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
                  </div>
                </td>
              </tr>
              {% endfor %}
            </tbody>
          </table>
          <div class="table-footer admin-users-table-footer">
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
          <p class="empty">Sem utilizadores ativos.</p>
          {% endif %}

          <div id="inactive-users-card" class="admin-users-inactive-section">
            <h2>Utilizadores inativos</h2>
            {% if inactive_users %}
            <table id="inactive-users-table">
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
                {% for row in inactive_users %}
                <tr>
                  <td>{{ row.id }}</td>
                  <td>{{ row.full_name }}</td>
                  <td>{{ row.login_email }}</td>
                  <td>{{ row.primary_phone }}</td>
                  <td>{{ row.entity_name }}</td>
                  <td>{{ row.profile_name }}</td>
                  <td>
                    <span class="entity-status entity-status-inactive">
                      {{ row.account_status_label if row.account_status_label is defined else "Inativo" }}
                    </span>
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
                    </div>
                  </td>
                </tr>
                {% endfor %}
              </tbody>
            </table>
            <div class="table-footer admin-users-table-footer">
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
            <p class="empty">Sem utilizadores inativos.</p>
            {% endif %}
          </div>
        </section>
        <!-- APPVERBO_ADMIN_USERS_ACTIVE_INACTIVE_SECTION_V5_END -->'''


def remove_old_user_sections_v5(content: str) -> str:
    content = re.sub(
        r'\n\s*<!-- APPVERBO_INACTIVE_USERS_SECTION_V[0-9]+_START -->[\s\S]*?<!-- APPVERBO_INACTIVE_USERS_SECTION_V[0-9]+_END -->\n?',
        "\n",
        content,
        flags=re.S,
    )

    content = re.sub(
        r'\n\s*<!-- APPVERBO_ADMIN_USERS_ACTIVE_INACTIVE_SECTION_V5_START -->[\s\S]*?<!-- APPVERBO_ADMIN_USERS_ACTIVE_INACTIVE_SECTION_V5_END -->\n?',
        "\n",
        content,
        flags=re.S,
    )

    content = re.sub(
        r'\n\s*<!-- APPVERBO_ACTIVE_USERS_SECTION_V[0-9]+_START -->\n?',
        "\n",
        content,
        flags=re.S,
    )

    content = re.sub(
        r'\n\s*<!-- APPVERBO_ACTIVE_USERS_SECTION_V[0-9]+_END -->\n?',
        "\n",
        content,
        flags=re.S,
    )

    return content


def find_section_range_v5(content: str, section_id: str) -> tuple[int, int]:
    start_match = re.search(
        r'<section\b(?=[^>]*\bid=(["\'])' + re.escape(section_id) + r'\1)[^>]*>',
        content,
        flags=re.I,
    )

    require_v5(start_match is not None, f"ERRO: section {section_id} não encontrada.")

    close_match = re.search(r'</section>', content[start_match.end():], flags=re.I)
    require_v5(close_match is not None, f"ERRO: fecho da section {section_id} não encontrado.")

    return start_match.start(), start_match.end() + close_match.end()


def patch_template_v5() -> None:
    path = "templates/new_user.html"
    content = read_text_v5(path)

    content = remove_old_user_sections_v5(content)

    start_index, end_index = find_section_range_v5(content, "admin-users-created-card")
    content = content[:start_index] + admin_users_card_v5() + content[end_index:]

    content = re.sub(
        r'new_user\.css\?v=[^"]+',
        'new_user.css?v=20260504-users-active-inactive-card-v5',
        content,
        count=1,
    )

    require_v5("SuperUsers de Entidade" not in content, "ERRO: bloco SuperUsers de Entidade ainda existe.")
    require_v5("APPVERBO_ADMIN_USERS_ACTIVE_INACTIVE_SECTION_V5_START" in content, "ERRO: bloco V5 não foi inserido.")
    require_v5("{% for row in active_created_users %}" in content, "ERRO: loop ativo não usa active_created_users.")
    require_v5("{% for row in inactive_users %}" in content, "ERRO: loop inativo não usa inactive_users.")
    require_v5("entity-status-active" in content, "ERRO: badge ativo verde não encontrado.")
    require_v5("entity-status-inactive" in content, "ERRO: badge inativo vermelho não encontrado.")
    require_v5("entity-status-inactive{% else %}" not in content, "ERRO: Jinja quebrado ainda existe.")

    write_text_v5(path, content)


def patch_css_v5() -> None:
    path = "static/css/new_user.css"
    content = read_text_v5(path)

    block = '''
/* APPVERBO_ADMIN_USERS_ACTIVE_INACTIVE_LAYOUT_V5_START */
#admin-users-created-card .admin-users-inactive-section {
  border-top: 1px solid #d1d9e6;
  margin-top: 18px;
  padding-top: 18px;
}

#admin-users-created-card .admin-users-inactive-section h2 {
  margin-top: 0;
}

#admin-users-created-card .admin-users-table-footer {
  align-items: center;
  display: flex;
  gap: 8px;
  margin-top: 10px;
}

#admin-users-created-card .admin-users-table-footer select {
  max-width: 72px;
  min-width: 64px;
  width: auto;
}

#admin-users-created-card .admin-users-table-footer .pagination {
  margin-left: auto;
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
/* APPVERBO_ADMIN_USERS_ACTIVE_INACTIVE_LAYOUT_V5_END */
'''

    content = re.sub(
        r'/\* APPVERBO_ADMIN_USERS_ACTIVE_INACTIVE_LAYOUT_V5_START \*/[\s\S]*?/\* APPVERBO_ADMIN_USERS_ACTIVE_INACTIVE_LAYOUT_V5_END \*/',
        '',
        content,
        flags=re.S,
    )

    content = content.rstrip() + "\n\n" + block.strip() + "\n"
    write_text_v5(path, content)


def validate_v5() -> None:
    page_service = read_text_v5("appverbo/services/page.py")
    template = read_text_v5("templates/new_user.html")
    delete_handler = read_text_v5("appverbo/routes/users/delete_handler.py")
    css = read_text_v5("static/css/new_user.css")

    active_section = re.search(
        r'APPVERBO_ADMIN_USERS_ACTIVE_INACTIVE_SECTION_V5_START[\s\S]*?<div id="inactive-users-card"',
        template,
        flags=re.S,
    )

    inactive_section = re.search(
        r'<div id="inactive-users-card"[\s\S]*?APPVERBO_ADMIN_USERS_ACTIVE_INACTIVE_SECTION_V5_END',
        template,
        flags=re.S,
    )

    require_v5(active_section is not None, "ERRO: parte ativa do bloco V5 não encontrada.")
    require_v5(inactive_section is not None, "ERRO: parte inativa do bloco V5 não encontrada.")

    require_v5('action="/users/delete"' not in active_section.group(0), "ERRO: eliminar apareceu no bloco ativo.")
    require_v5('action="/users/delete"' in inactive_section.group(0), "ERRO: eliminar não apareceu no bloco inativo.")

    checks = {
        "page active_created_users": "active_created_users = [" in page_service,
        "page inactive_users": "inactive_users = [" in page_service,
        "context active_created_users": '"active_created_users": active_created_users,' in page_service,
        "context inactive_users": '"inactive_users": inactive_users,' in page_service,
        "template sem SuperUsers": "SuperUsers de Entidade" not in template,
        "template bloco V5": "APPVERBO_ADMIN_USERS_ACTIVE_INACTIVE_SECTION_V5_START" in template,
        "template loop ativo": "{% for row in active_created_users %}" in template,
        "template loop inativo": "{% for row in inactive_users %}" in template,
        "template badge ativo": "entity-status-active" in template,
        "template badge inativo": "entity-status-inactive" in template,
        "template cache css": "new_user.css?v=20260504-users-active-inactive-card-v5" in template,
        "backend delete inativo": "Só é permitido eliminar utilizadores inativos." in delete_handler,
        "css layout": "APPVERBO_ADMIN_USERS_ACTIVE_INACTIVE_LAYOUT_V5_START" in css,
        "sem jinja quebrado": "entity-status-inactive{% else %}" not in template,
    }

    failed = [name for name, ok in checks.items() if not ok]
    require_v5(not failed, "Falha na validação: " + ", ".join(failed))


def main_v5() -> None:
    ensure_page_context_v5()
    ensure_delete_backend_rule_v5()
    patch_template_v5()
    patch_css_v5()
    validate_v5()


if __name__ == "__main__":
    main_v5()
