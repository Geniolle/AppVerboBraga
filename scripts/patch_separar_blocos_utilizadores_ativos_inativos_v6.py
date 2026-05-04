from __future__ import annotations

import re
from pathlib import Path


def read_text_v6(path: str) -> str:
    return Path(path).read_text(encoding="utf-8-sig")


def write_text_v6(path: str, content: str) -> None:
    Path(path).write_text(content.rstrip() + "\n", encoding="utf-8")


def require_v6(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def ensure_page_context_v6() -> None:
    path = "appverbo/services/page.py"
    content = read_text_v6(path)

    if '"account_status_is_active"' not in content:
        content = content.replace(
            '            "account_status_label": user_account_status_label_pt_v1(row.account_status),\n',
            '            "account_status_label": user_account_status_label_pt_v1(row.account_status),\n'
            '            "account_status_is_active": normalize_user_account_status_v1(row.account_status) == UserAccountStatus.ACTIVE.value,\n',
            1,
        )

    if '"account_status_is_inactive"' not in content:
        content = content.replace(
            '            "account_status_is_active": normalize_user_account_status_v1(row.account_status) == UserAccountStatus.ACTIVE.value,\n',
            '            "account_status_is_active": normalize_user_account_status_v1(row.account_status) == UserAccountStatus.ACTIVE.value,\n'
            '            "account_status_is_inactive": normalize_user_account_status_v1(row.account_status) == UserAccountStatus.INACTIVE.value,\n',
            1,
        )

    if "active_created_users = [" not in content:
        content = content.replace(
            '    created_users = [\n'
            '        row for row in all_users if row["account_status"] != UserAccountStatus.PENDING.value\n'
            '    ]\n',
            '    created_users = [\n'
            '        row for row in all_users if row["account_status"] != UserAccountStatus.PENDING.value\n'
            '    ]\n'
            '    active_created_users = [\n'
            '        row for row in created_users if row["account_status"] == UserAccountStatus.ACTIVE.value\n'
            '    ]\n'
            '    inactive_users = [\n'
            '        row for row in all_users if row["account_status"] == UserAccountStatus.INACTIVE.value\n'
            '    ]\n',
            1,
        )

    if '"active_created_users": active_created_users,' not in content:
        content = content.replace(
            '        "created_users": created_users,\n',
            '        "created_users": created_users,\n'
            '        "active_created_users": active_created_users,\n'
            '        "inactive_users": inactive_users,\n',
            1,
        )

    require_v6("active_created_users = [" in content, "ERRO: active_created_users não existe no page.py.")
    require_v6("inactive_users = [" in content, "ERRO: inactive_users não existe no page.py.")
    require_v6('"active_created_users": active_created_users,' in content, "ERRO: active_created_users não está no contexto.")
    require_v6('"inactive_users": inactive_users,' in content, "ERRO: inactive_users não está no contexto.")

    write_text_v6(path, content)


def active_users_section_v6() -> str:
    return '''        <!-- APPVERBO_ADMIN_USERS_ACTIVE_SECTION_V6_START -->
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
        </section>
        <!-- APPVERBO_ADMIN_USERS_ACTIVE_SECTION_V6_END -->'''


def inactive_users_section_v6() -> str:
    return '''        <!-- APPVERBO_ADMIN_USERS_INACTIVE_SECTION_V6_START -->
        <section id="inactive-users-card" class="card" data-menu-scope="administrativo">
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
        </section>
        <!-- APPVERBO_ADMIN_USERS_INACTIVE_SECTION_V6_END -->'''


def remove_old_user_sections_v6(content: str) -> str:
    marker_pairs = [
        ("APPVERBO_ADMIN_USERS_ACTIVE_INACTIVE_SECTION_V5_START", "APPVERBO_ADMIN_USERS_ACTIVE_INACTIVE_SECTION_V5_END"),
        ("APPVERBO_ADMIN_USERS_ACTIVE_SECTION_V6_START", "APPVERBO_ADMIN_USERS_ACTIVE_SECTION_V6_END"),
        ("APPVERBO_ADMIN_USERS_INACTIVE_SECTION_V6_START", "APPVERBO_ADMIN_USERS_INACTIVE_SECTION_V6_END"),
        ("APPVERBO_ACTIVE_USERS_SECTION_V4_START", "APPVERBO_ACTIVE_USERS_SECTION_V4_END"),
        ("APPVERBO_INACTIVE_USERS_SECTION_V4_START", "APPVERBO_INACTIVE_USERS_SECTION_V4_END"),
        ("APPVERBO_INACTIVE_USERS_SECTION_V3_START", "APPVERBO_INACTIVE_USERS_SECTION_V3_END"),
        ("APPVERBO_INACTIVE_USERS_SECTION_V2_START", "APPVERBO_INACTIVE_USERS_SECTION_V2_END"),
        ("APPVERBO_INACTIVE_USERS_SECTION_V1_START", "APPVERBO_INACTIVE_USERS_SECTION_V1_END"),
    ]

    for start_marker, end_marker in marker_pairs:
        content = re.sub(
            r'\n?\s*<!-- ' + re.escape(start_marker) + r' -->[\s\S]*?<!-- ' + re.escape(end_marker) + r' -->\n?',
            "\n",
            content,
            flags=re.S,
        )

    return content


def find_section_range_v6(content: str, section_id: str) -> tuple[int, int]:
    section_start = re.search(
        r'<section\b[^>]*\bid=(["\'])' + re.escape(section_id) + r'\1[^>]*>',
        content,
        flags=re.I,
    )

    require_v6(section_start is not None, f"ERRO: section {section_id} não encontrada.")

    start_index = section_start.start()
    open_end_index = section_start.end()

    close_match = re.search(r'</section>', content[open_end_index:], flags=re.I)
    require_v6(close_match is not None, f"ERRO: fecho da section {section_id} não encontrado.")

    end_index = open_end_index + close_match.end()

    return start_index, end_index


def patch_template_v6() -> None:
    path = "templates/new_user.html"
    content = read_text_v6(path)

    content = re.sub(
        r'/static/css/new_user\.css\?v=[^"]+',
        '/static/css/new_user.css?v=20260504-users-active-inactive-card-v6',
        content,
        count=1,
    )

    old_v5_block = re.search(
        r'\n?\s*<!-- APPVERBO_ADMIN_USERS_ACTIVE_INACTIVE_SECTION_V5_START -->[\s\S]*?<!-- APPVERBO_ADMIN_USERS_ACTIVE_INACTIVE_SECTION_V5_END -->\n?',
        content,
        flags=re.S,
    )

    replacement = active_users_section_v6() + "\n\n" + inactive_users_section_v6()

    if old_v5_block:
        content = content[: old_v5_block.start()] + "\n" + replacement + "\n" + content[old_v5_block.end():]
    else:
        content = remove_old_user_sections_v6(content)
        start_index, end_index = find_section_range_v6(content, "admin-users-created-card")
        content = content[:start_index] + replacement + content[end_index:]

    content = remove_old_user_sections_v6(content)
    content = content.replace("\n" + replacement + "\n", "\n" + replacement + "\n")

    if "APPVERBO_ADMIN_USERS_ACTIVE_SECTION_V6_START" not in content:
        start_index, end_index = find_section_range_v6(content, "admin-users-created-card")
        content = content[:start_index] + replacement + content[end_index:]

    require_v6("APPVERBO_ADMIN_USERS_ACTIVE_SECTION_V6_START" in content, "ERRO: bloco ativo V6 não foi inserido.")
    require_v6("APPVERBO_ADMIN_USERS_INACTIVE_SECTION_V6_START" in content, "ERRO: bloco inativo V6 não foi inserido.")
    require_v6("<section id=\"inactive-users-card\" class=\"card\"" in content, "ERRO: inativos não estão em section/card separado.")
    require_v6("<div id=\"inactive-users-card\" class=\"admin-users-inactive-section\">" not in content, "ERRO: inativos continuam dentro do card de ativos.")
    require_v6("SuperUsers de Entidade" not in content, "ERRO: bloco SuperUsers de Entidade ainda existe.")
    require_v6("entity-status-inactive{% else %}" not in content, "ERRO: ainda existe Jinja quebrado.")
    require_v6("{% for row in active_created_users %}" in content, "ERRO: loop ativo não usa active_created_users.")
    require_v6("{% for row in inactive_users %}" in content, "ERRO: loop inativo não usa inactive_users.")

    active_block = re.search(
        r'APPVERBO_ADMIN_USERS_ACTIVE_SECTION_V6_START[\s\S]*?APPVERBO_ADMIN_USERS_ACTIVE_SECTION_V6_END',
        content,
    )
    inactive_block = re.search(
        r'APPVERBO_ADMIN_USERS_INACTIVE_SECTION_V6_START[\s\S]*?APPVERBO_ADMIN_USERS_INACTIVE_SECTION_V6_END',
        content,
    )

    require_v6(active_block is not None, "ERRO: bloco ativo V6 não encontrado.")
    require_v6(inactive_block is not None, "ERRO: bloco inativo V6 não encontrado.")
    require_v6('action="/users/delete"' not in active_block.group(0), "ERRO: eliminar apareceu no bloco ativo.")
    require_v6('action="/users/delete"' in inactive_block.group(0), "ERRO: eliminar não apareceu no bloco inativo.")

    write_text_v6(path, content)


def patch_css_v6() -> None:
    path = "static/css/new_user.css"
    content = read_text_v6(path)

    for marker in [
        "APPVERBO_ADMIN_USERS_ACTIVE_INACTIVE_LAYOUT_V5",
        "APPVERBO_ADMIN_USERS_SEPARATE_CARDS_LAYOUT_V6",
    ]:
        content = re.sub(
            r'/\* ' + marker + r'_START \*/[\s\S]*?/\* ' + marker + r'_END \*/',
            "",
            content,
            flags=re.S,
        )

    block = '''
/* APPVERBO_ADMIN_USERS_SEPARATE_CARDS_LAYOUT_V6_START */
#inactive-users-card {
  margin-top: 14px;
}

#admin-users-created-card .admin-users-table-footer,
#inactive-users-card .admin-users-table-footer {
  align-items: center;
  display: flex;
  gap: 8px;
  justify-content: flex-start;
}

#admin-users-created-card .admin-users-table-footer select,
#inactive-users-card .admin-users-table-footer select {
  max-width: 72px;
  min-width: 64px;
  width: auto;
}

#admin-users-created-card .admin-users-table-footer .pagination,
#inactive-users-card .admin-users-table-footer .pagination {
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
/* APPVERBO_ADMIN_USERS_SEPARATE_CARDS_LAYOUT_V6_END */
'''

    content = content.rstrip() + "\n\n" + block.strip() + "\n"
    write_text_v6(path, content)


def validate_backend_delete_rule_v6() -> None:
    content = read_text_v6("appverbo/routes/users/delete_handler.py")

    require_v6(
        "Só é permitido eliminar utilizadores inativos." in content,
        "ERRO: backend não contém bloqueio para eliminar apenas utilizadores inativos.",
    )

    require_v6(
        "UserAccountStatus.INACTIVE.value" in content,
        "ERRO: backend não compara com UserAccountStatus.INACTIVE.value.",
    )


def validate_v6() -> None:
    page_service = read_text_v6("appverbo/services/page.py")
    template = read_text_v6("templates/new_user.html")
    css = read_text_v6("static/css/new_user.css")

    active_section = re.search(
        r'APPVERBO_ADMIN_USERS_ACTIVE_SECTION_V6_START[\s\S]*?APPVERBO_ADMIN_USERS_ACTIVE_SECTION_V6_END',
        template,
    )
    inactive_section = re.search(
        r'APPVERBO_ADMIN_USERS_INACTIVE_SECTION_V6_START[\s\S]*?APPVERBO_ADMIN_USERS_INACTIVE_SECTION_V6_END',
        template,
    )

    require_v6(active_section is not None, "ERRO: bloco ativo V6 não encontrado.")
    require_v6(inactive_section is not None, "ERRO: bloco inativo V6 não encontrado.")
    require_v6('action="/users/delete"' not in active_section.group(0), "ERRO: eliminar apareceu nos ativos.")
    require_v6('action="/users/delete"' in inactive_section.group(0), "ERRO: eliminar não apareceu nos inativos.")

    checks = {
        "page active_created_users": "active_created_users = [" in page_service,
        "page inactive_users": "inactive_users = [" in page_service,
        "context active_created_users": '"active_created_users": active_created_users,' in page_service,
        "context inactive_users": '"inactive_users": inactive_users,' in page_service,
        "template active section": "APPVERBO_ADMIN_USERS_ACTIVE_SECTION_V6_START" in template,
        "template inactive section": "APPVERBO_ADMIN_USERS_INACTIVE_SECTION_V6_START" in template,
        "template inactive separate section": '<section id="inactive-users-card" class="card"' in template,
        "template no inactive div inside active card": '<div id="inactive-users-card" class="admin-users-inactive-section">' not in template,
        "template sem SuperUsers": "SuperUsers de Entidade" not in template,
        "template css cache": "new_user.css?v=20260504-users-active-inactive-card-v6" in template,
        "css layout V6": "APPVERBO_ADMIN_USERS_SEPARATE_CARDS_LAYOUT_V6_START" in css,
        "template no broken jinja": "entity-status-inactive{% else %}" not in template,
    }

    failed = [name for name, ok in checks.items() if not ok]
    require_v6(not failed, "Falha na validação: " + ", ".join(failed))


def main_v6() -> None:
    ensure_page_context_v6()
    validate_backend_delete_rule_v6()
    patch_template_v6()
    patch_css_v6()
    validate_v6()


if __name__ == "__main__":
    main_v6()
