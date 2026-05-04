from __future__ import annotations

import re
from pathlib import Path


def read_text_v1(path: str) -> str:
    return Path(path).read_text(encoding="utf-8-sig")


def write_text_v1(path: str, content: str) -> None:
    Path(path).write_text(content.rstrip() + "\n", encoding="utf-8")


def require_v1(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def patch_page_service_v1() -> None:
    path = "appverbo/services/page.py"
    content = read_text_v1(path)

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

    write_text_v1(path, content)


USER_STATUS_BADGE_BLOCK_V1 = '''<span class="entity-status {% if row.account_status_is_inactive or row.account_status == 'inactive' %}entity-status-inactive{% elif row.account_status_is_active or row.account_status == 'active' %}entity-status-active{% else %}entity-status-inactive{% endif %}">
                        {{ row.account_status_label if row.account_status_label is defined else row.account_status }}
                      </span>'''


INACTIVE_USERS_SECTION_V1 = '''        <!-- APPVERBO_INACTIVE_USERS_SECTION_V1_START -->
        <section id="inactive-users-card" class="card" data-menu-scope="administrativo">
          <h2>Utilizadores inativos</h2>
          {% if inactive_users %}
          <table>
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
                    {% if row.account_status_is_inactive or row.account_status == 'inactive' %}
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
          <div class="table-footer">
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
        <!-- APPVERBO_INACTIVE_USERS_SECTION_V1_END -->
'''


def replace_user_status_cells_v1(content: str) -> str:
    status_expr = "{{ row.account_status_label if row.account_status_label is defined else row.account_status }}"
    pattern = re.compile(
        r"<td>\s*"
        + re.escape(status_expr)
        + r"\s*</td>",
        re.S,
    )

    replacement = "<td>\n                      " + USER_STATUS_BADGE_BLOCK_V1 + "\n                    </td>"
    content = pattern.sub(replacement, content)

    return content


def patch_template_v1() -> None:
    path = "templates/new_user.html"
    content = read_text_v1(path)

    content = content.replace(
        "{% for row in created_users %}",
        "{% for row in active_created_users if active_created_users is defined else created_users %}",
        1,
    )

    content = replace_user_status_cells_v1(content)

    if "APPVERBO_INACTIVE_USERS_SECTION_V1_START" not in content:
        active_section_match = re.search(
            r'(?P<section>[ \t]*<section\s+id="admin-users-created-card"[\s\S]*?</section>)',
            content,
            flags=re.S,
        )

        require_v1(
            active_section_match is not None,
            "ERRO: não foi possível localizar a section admin-users-created-card.",
        )

        insert_position = active_section_match.end()
        content = content[:insert_position] + "\n\n" + INACTIVE_USERS_SECTION_V1 + content[insert_position:]

    require_v1(
        "active_created_users" in content,
        "ERRO: tabela de utilizadores criados não usa active_created_users.",
    )

    require_v1(
        "inactive_users" in content,
        "ERRO: bloco de utilizadores inativos não usa inactive_users.",
    )

    require_v1(
        "entity-status-active" in content,
        "ERRO: badge verde entity-status-active não encontrado.",
    )

    require_v1(
        "entity-status-inactive" in content,
        "ERRO: badge vermelho entity-status-inactive não encontrado.",
    )

    write_text_v1(path, content)


def validate_v1() -> None:
    page_service = read_text_v1("appverbo/services/page.py")
    template = read_text_v1("templates/new_user.html")

    checks = {
        "page active_created_users": "active_created_users = [" in page_service,
        "page inactive_users": "inactive_users = [" in page_service,
        "context active_created_users": '"active_created_users": active_created_users,' in page_service,
        "context inactive_users": '"inactive_users": inactive_users,' in page_service,
        "template active loop": "active_created_users" in template,
        "template inactive section": "APPVERBO_INACTIVE_USERS_SECTION_V1_START" in template,
        "template inactive title": "Utilizadores inativos" in template,
        "template green status": "entity-status-active" in template,
        "template red status": "entity-status-inactive" in template,
        "template inactive delete": 'action="/users/delete"' in template and "row.account_status_is_inactive" in template,
    }

    failed = [name for name, ok in checks.items() if not ok]
    require_v1(not failed, "Falha na validação: " + ", ".join(failed))


def main_v1() -> None:
    patch_page_service_v1()
    patch_template_v1()
    validate_v1()


if __name__ == "__main__":
    main_v1()
