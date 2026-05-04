from __future__ import annotations

import re
from pathlib import Path


def read_text_v2(path: str) -> str:
    return Path(path).read_text(encoding="utf-8-sig")


def write_text_v2(path: str, content: str) -> None:
    Path(path).write_text(content.rstrip() + "\n", encoding="utf-8")


def require_v2(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def patch_page_service_v2() -> None:
    path = "appverbo/services/page.py"
    content = read_text_v2(path)

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
        content = content.replace(
            "    all_users = [\n",
            helper_block + "    all_users = [\n",
            1,
        )

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

    require_v2("active_created_users = [" in content, "ERRO: active_created_users não existe no page.py.")
    require_v2("inactive_users = [" in content, "ERRO: inactive_users não existe no page.py.")
    require_v2('"active_created_users": active_created_users,' in content, "ERRO: contexto active_created_users não existe.")
    require_v2('"inactive_users": inactive_users,' in content, "ERRO: contexto inactive_users não existe.")

    write_text_v2(path, content)


def find_section_range_v2(content: str, section_id: str) -> tuple[int, int]:
    start_match = re.search(
        r'<section\b[^>]*\bid="' + re.escape(section_id) + r'"[^>]*>',
        content,
        flags=re.I,
    )

    require_v2(start_match is not None, f"ERRO: section {section_id} não encontrada.")

    start_index = start_match.start()
    open_end_index = start_match.end()
    close_match = re.search(r'</section>', content[open_end_index:], flags=re.I)

    require_v2(close_match is not None, f"ERRO: fecho da section {section_id} não encontrado.")

    end_index = open_end_index + close_match.end()

    return start_index, end_index


def status_badge_v2() -> str:
    return '''<span class="entity-status {% if row.account_status_is_inactive or row.account_status == 'inactive' %}entity-status-inactive{% elif row.account_status_is_active or row.account_status == 'active' %}entity-status-active{% else %}entity-status-inactive{% endif %}">
                        {{ row.account_status_label if row.account_status_label is defined else row.account_status }}
                      </span>'''


def replace_status_cell_v2(section: str) -> str:
    expressions = [
        "{{ row.account_status_label if row.account_status_label is defined else row.account_status }}",
        "{{ row.account_status }}",
    ]

    for expression in expressions:
        section = re.sub(
            r"<td>\s*" + re.escape(expression) + r"\s*</td>",
            "<td>\n                      " + status_badge_v2() + "\n                    </td>",
            section,
            flags=re.S,
        )

    return section


def patch_active_users_section_v2(section: str) -> str:
    section = section.replace("<h2>Utilizadores criados</h2>", "<h2>Utilizadores criados</h2>")

    section = section.replace("{% if all_users %}", "{% if active_created_users %}")
    section = section.replace("{% if created_users %}", "{% if active_created_users %}")

    section = section.replace("{% for row in all_users %}", "{% for row in active_created_users %}")
    section = section.replace("{% for row in created_users %}", "{% for row in active_created_users %}")

    section = replace_status_cell_v2(section)

    if "{% if active_created_users %}" not in section:
        section = section.replace("<table>", "{% if active_created_users %}\n          <table>", 1)

    if "Sem utilizadores ativos." not in section:
        section = section.replace(
            "{% endif %}",
            "{% else %}\n          <p class=\"empty\">Sem utilizadores ativos.</p>\n          {% endif %}",
            1,
        )

    require_v2(
        "{% for row in active_created_users %}" in section,
        "ERRO: tabela de utilizadores ativos não usa active_created_users.",
    )

    require_v2(
        "entity-status-active" in section,
        "ERRO: badge verde não foi aplicado na tabela de utilizadores ativos.",
    )

    return section


def inactive_users_section_v2() -> str:
    return '''        <!-- APPVERBO_INACTIVE_USERS_SECTION_V2_START -->
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
        <!-- APPVERBO_INACTIVE_USERS_SECTION_V2_END -->
'''


def patch_template_v2() -> None:
    path = "templates/new_user.html"
    content = read_text_v2(path)

    content = re.sub(
        r'\n\s*<!-- APPVERBO_INACTIVE_USERS_SECTION_V1_START -->.*?<!-- APPVERBO_INACTIVE_USERS_SECTION_V1_END -->\n?',
        "\n",
        content,
        flags=re.S,
    )

    content = re.sub(
        r'\n\s*<!-- APPVERBO_INACTIVE_USERS_SECTION_V2_START -->.*?<!-- APPVERBO_INACTIVE_USERS_SECTION_V2_END -->\n?',
        "\n",
        content,
        flags=re.S,
    )

    start_index, end_index = find_section_range_v2(content, "admin-users-created-card")
    active_section = content[start_index:end_index]
    active_section = patch_active_users_section_v2(active_section)

    content = content[:start_index] + active_section + content[end_index:]

    start_index, end_index = find_section_range_v2(content, "admin-users-created-card")
    content = content[:end_index] + "\n\n" + inactive_users_section_v2() + content[end_index:]

    require_v2(
        "APPVERBO_INACTIVE_USERS_SECTION_V2_START" in content,
        "ERRO: bloco de utilizadores inativos não foi inserido.",
    )

    require_v2(
        "{% for row in active_created_users %}" in content,
        "ERRO: tabela ativa não usa active_created_users.",
    )

    require_v2(
        "{% for row in inactive_users %}" in content,
        "ERRO: tabela inativa não usa inactive_users.",
    )

    require_v2(
        "entity-status-active" in content and "entity-status-inactive" in content,
        "ERRO: cores do estado não foram aplicadas.",
    )

    write_text_v2(path, content)


def validate_v2() -> None:
    page_service = read_text_v2("appverbo/services/page.py")
    template = read_text_v2("templates/new_user.html")

    checks = {
        "page active_created_users": "active_created_users = [" in page_service,
        "page inactive_users": "inactive_users = [" in page_service,
        "context active_created_users": '"active_created_users": active_created_users,' in page_service,
        "context inactive_users": '"inactive_users": inactive_users,' in page_service,
        "template active loop": "{% for row in active_created_users %}" in template,
        "template inactive section": "APPVERBO_INACTIVE_USERS_SECTION_V2_START" in template,
        "template inactive loop": "{% for row in inactive_users %}" in template,
        "template inactive title": "Utilizadores inativos" in template,
        "template green status": "entity-status-active" in template,
        "template red status": "entity-status-inactive" in template,
        "template inactive delete": 'action="/users/delete"' in template and "row.account_status_is_inactive" in template,
    }

    failed = [name for name, ok in checks.items() if not ok]
    require_v2(not failed, "Falha na validação: " + ", ".join(failed))


def main_v2() -> None:
    patch_page_service_v2()
    patch_template_v2()
    validate_v2()


if __name__ == "__main__":
    main_v2()
