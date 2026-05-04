from __future__ import annotations

import re
from pathlib import Path


def read_text_v3(path: str) -> str:
    return Path(path).read_text(encoding="utf-8-sig")


def write_text_v3(path: str, content: str) -> None:
    Path(path).write_text(content.rstrip() + "\n", encoding="utf-8")


def require_v3(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def ensure_page_context_v3() -> None:
    path = "appverbo/services/page.py"
    content = read_text_v3(path)

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

    if "active_superuser_users = [" not in content:
        content = content.replace(
            '    superuser_users = [\n'
            '        row for row in all_users if str(row["profile_name"]).strip().upper() == "SUPER USER"\n'
            '    ]\n',
            '    superuser_users = [\n'
            '        row for row in all_users if str(row["profile_name"]).strip().upper() == "SUPER USER"\n'
            '    ]\n'
            '    active_superuser_users = [\n'
            '        row for row in superuser_users if row["account_status"] == UserAccountStatus.ACTIVE.value\n'
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

    if '"active_superuser_users": active_superuser_users,' not in content:
        content = content.replace(
            '        "superuser_users": superuser_users,\n',
            '        "superuser_users": superuser_users,\n'
            '        "active_superuser_users": active_superuser_users,\n',
            1,
        )

    require_v3("active_created_users = [" in content, "ERRO: active_created_users não existe no page.py.")
    require_v3("inactive_users = [" in content, "ERRO: inactive_users não existe no page.py.")
    require_v3("active_superuser_users = [" in content, "ERRO: active_superuser_users não existe no page.py.")
    require_v3('"active_created_users": active_created_users,' in content, "ERRO: active_created_users não está no contexto.")
    require_v3('"inactive_users": inactive_users,' in content, "ERRO: inactive_users não está no contexto.")
    require_v3('"active_superuser_users": active_superuser_users,' in content, "ERRO: active_superuser_users não está no contexto.")

    write_text_v3(path, content)


def find_section_v3(content: str, section_id: str) -> tuple[int, int]:
    start_match = re.search(
        r'<section\b[^>]*\bid="' + re.escape(section_id) + r'"[^>]*>',
        content,
        flags=re.I,
    )

    require_v3(start_match is not None, f"ERRO: section {section_id} não encontrada.")

    close_match = re.search(r'</section>', content[start_match.end():], flags=re.I)

    require_v3(close_match is not None, f"ERRO: fecho da section {section_id} não encontrado.")

    return start_match.start(), start_match.end() + close_match.end()


def active_users_section_v3() -> str:
    return '''        <!-- APPVERBO_ACTIVE_USERS_SECTION_V3_START -->
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
          <p class="empty">Sem utilizadores ativos.</p>
          {% endif %}

          <hr>
          <h3>SuperUsers de Entidade</h3>
          {% if active_superuser_users %}
            <ul>
              {% for row in active_superuser_users %}
                <li>
                  <strong>{{ row.full_name }}</strong> | {{ row.login_email }} | {{ row.entity_name }} | {{ row.account_status_label if row.account_status_label is defined else row.account_status }} | {{ row.created_at }}
                </li>
              {% endfor %}
            </ul>
          {% else %}
            <p class="empty">Sem SuperUsers ativos.</p>
          {% endif %}
        </section>
        <!-- APPVERBO_ACTIVE_USERS_SECTION_V3_END -->'''


def inactive_users_section_v3() -> str:
    return '''        <!-- APPVERBO_INACTIVE_USERS_SECTION_V3_START -->
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
        <!-- APPVERBO_INACTIVE_USERS_SECTION_V3_END -->'''


def patch_template_v3() -> None:
    path = "templates/new_user.html"
    content = read_text_v3(path)

    content = re.sub(
        r'\n\s*<!-- APPVERBO_ACTIVE_USERS_SECTION_V3_START -->.*?<!-- APPVERBO_ACTIVE_USERS_SECTION_V3_END -->\n?',
        "\n",
        content,
        flags=re.S,
    )

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

    content = re.sub(
        r'\n\s*<!-- APPVERBO_INACTIVE_USERS_SECTION_V3_START -->.*?<!-- APPVERBO_INACTIVE_USERS_SECTION_V3_END -->\n?',
        "\n",
        content,
        flags=re.S,
    )

    start_index, end_index = find_section_v3(content, "admin-users-created-card")

    replacement = active_users_section_v3() + "\n\n" + inactive_users_section_v3()

    content = content[:start_index] + replacement + content[end_index:]

    require_v3("APPVERBO_ACTIVE_USERS_SECTION_V3_START" in content, "ERRO: bloco ativo V3 não foi inserido.")
    require_v3("APPVERBO_INACTIVE_USERS_SECTION_V3_START" in content, "ERRO: bloco inativo V3 não foi inserido.")
    require_v3("{% for row in active_created_users %}" in content, "ERRO: loop ativo não usa active_created_users.")
    require_v3("{% for row in inactive_users %}" in content, "ERRO: loop inativo não usa inactive_users.")
    require_v3("entity-status-active" in content, "ERRO: badge verde não encontrado.")
    require_v3("entity-status-inactive" in content, "ERRO: badge vermelho não encontrado.")

    write_text_v3(path, content)


def validate_v3() -> None:
    page_service = read_text_v3("appverbo/services/page.py")
    template = read_text_v3("templates/new_user.html")

    checks = {
        "page active_created_users": "active_created_users = [" in page_service,
        "page inactive_users": "inactive_users = [" in page_service,
        "page active_superuser_users": "active_superuser_users = [" in page_service,
        "context active_created_users": '"active_created_users": active_created_users,' in page_service,
        "context inactive_users": '"inactive_users": inactive_users,' in page_service,
        "context active_superuser_users": '"active_superuser_users": active_superuser_users,' in page_service,
        "template active section": "APPVERBO_ACTIVE_USERS_SECTION_V3_START" in template,
        "template inactive section": "APPVERBO_INACTIVE_USERS_SECTION_V3_START" in template,
        "template active loop": "{% for row in active_created_users %}" in template,
        "template inactive loop": "{% for row in inactive_users %}" in template,
        "template green status": "entity-status-active" in template,
        "template red status": "entity-status-inactive" in template,
        "template inactive delete": 'action="/users/delete"' in template,
    }

    failed = [name for name, ok in checks.items() if not ok]
    require_v3(not failed, "Falha na validação: " + ", ".join(failed))


def main_v3() -> None:
    ensure_page_context_v3()
    patch_template_v3()
    validate_v3()


if __name__ == "__main__":
    main_v3()
