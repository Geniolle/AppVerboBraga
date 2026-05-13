from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(".")


def read_text_v1(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8-sig")


def write_text_v1(path: str, content: str) -> None:
    file_path = ROOT / path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content.strip() + "\n", encoding="utf-8")


def require_v1(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


####################################################################################
# (3.1) CRIAR JS QUE INJETA BOTÃO ELIMINAR NOS UTILIZADORES INATIVOS
####################################################################################

write_text_v1(
    "static/js/modules/admin_user_inactive_delete_button_v1.js",
    r'''
(function () {
  "use strict";

  var FLAG = "APPVERBO_ADMIN_USER_INACTIVE_DELETE_BUTTON_V1";

  if (window[FLAG]) {
    return;
  }

  window[FLAG] = true;

  function logDebug(stage, data) {
    try {
      console.log("APPVERBO_ADMIN_USER_INACTIVE_DELETE_BUTTON_V1", stage, data || {});
    } catch (error) {
      // noop
    }
  }

  function normalizeText(value) {
    return String(value || "").trim().toLowerCase();
  }

  function closestInactiveContainer(row) {
    if (!row || !row.closest) {
      return null;
    }

    return row.closest(
      "#admin-user-shadow-inactive-card, #inactive-users-card, [data-admin-subprocess-shadow='utilizador-inactive']"
    );
  }

  function parseUserIdFromHref(href) {
    var cleanHref = String(href || "");
    var match = cleanHref.match(/[?&]user_edit_id=(\d+)/);

    if (match && match[1]) {
      return match[1];
    }

    return "";
  }

  function findUserId(row) {
    var links = row.querySelectorAll("a[href*='user_edit_id=']");
    var index;

    for (index = 0; index < links.length; index += 1) {
      var userId = parseUserIdFromHref(links[index].getAttribute("href"));

      if (userId) {
        return userId;
      }
    }

    if (row.cells && row.cells.length > 0) {
      var firstCellText = normalizeText(row.cells[0].textContent);

      if (/^\d+$/.test(firstCellText)) {
        return firstCellText;
      }
    }

    return "";
  }

  function findUserEmail(row) {
    var cells = row.cells || [];
    var index;

    for (index = 0; index < cells.length; index += 1) {
      var text = String(cells[index].textContent || "").trim();

      if (text.indexOf("@") >= 0) {
        return text;
      }
    }

    return "";
  }

  function rowLooksInactive(row) {
    if (closestInactiveContainer(row)) {
      return true;
    }

    var text = normalizeText(row.textContent);

    return text.indexOf("inativo") >= 0 || text.indexOf("inactive") >= 0;
  }

  function findActionCell(row) {
    var actionBox = row.querySelector(".table-actions");

    if (actionBox) {
      return actionBox;
    }

    if (row.cells && row.cells.length > 0) {
      return row.cells[row.cells.length - 1];
    }

    return null;
  }

  function createDeleteForm(userId, userEmail) {
    var form = document.createElement("form");
    form.id = "delete-user-form-" + userId;
    form.className = "admin-user-delete-form-v1";
    form.method = "post";
    form.action = "/users/delete";
    form.setAttribute("data-user-id", userId);
    form.setAttribute("data-user-email", userEmail || "");
    form.setAttribute("data-appverbo-delete-injected", "1");
    form.style.display = "inline-flex";
    form.style.margin = "0";
    form.style.padding = "0";

    var input = document.createElement("input");
    input.type = "hidden";
    input.name = "user_id";
    input.value = userId;

    var button = document.createElement("button");
    button.type = "submit";
    button.className = "table-icon-btn table-icon-btn-danger admin-user-delete-button-v1";
    button.title = "Eliminar utilizador";
    button.setAttribute("aria-label", "Eliminar utilizador " + (userEmail || userId));
    button.innerHTML = "&#128465;";

    form.appendChild(input);
    form.appendChild(button);

    return form;
  }

  function ensureDeleteButtonForRow(row) {
    if (!row || !row.querySelectorAll) {
      return false;
    }

    if (!rowLooksInactive(row)) {
      return false;
    }

    if (row.querySelector(".admin-user-delete-form-v1, .admin-user-delete-button-v1")) {
      return false;
    }

    var userId = findUserId(row);

    if (!userId) {
      return false;
    }

    var actionCell = findActionCell(row);

    if (!actionCell) {
      return false;
    }

    var userEmail = findUserEmail(row);
    var form = createDeleteForm(userId, userEmail);

    actionCell.appendChild(form);

    logDebug("button-added", {
      userId: userId,
      userEmail: userEmail
    });

    return true;
  }

  function scanInactiveTables() {
    var containers = document.querySelectorAll(
      "#admin-user-shadow-inactive-card, #inactive-users-card, [data-admin-subprocess-shadow='utilizador-inactive']"
    );
    var totalAdded = 0;
    var containerIndex;

    for (containerIndex = 0; containerIndex < containers.length; containerIndex += 1) {
      var rows = containers[containerIndex].querySelectorAll("tbody tr");
      var rowIndex;

      for (rowIndex = 0; rowIndex < rows.length; rowIndex += 1) {
        if (ensureDeleteButtonForRow(rows[rowIndex])) {
          totalAdded += 1;
        }
      }
    }

    var inactiveTable = document.querySelector("#inactive-users-table");

    if (inactiveTable) {
      var tableRows = inactiveTable.querySelectorAll("tbody tr");
      var tableRowIndex;

      for (tableRowIndex = 0; tableRowIndex < tableRows.length; tableRowIndex += 1) {
        if (ensureDeleteButtonForRow(tableRows[tableRowIndex])) {
          totalAdded += 1;
        }
      }
    }

    if (totalAdded > 0) {
      logDebug("scan-complete", { added: totalAdded });
    }
  }

  document.addEventListener(
    "click",
    function (event) {
      var button = event.target.closest(".admin-user-delete-button-v1");

      if (!button) {
        return;
      }

      var form = button.closest("form.admin-user-delete-form-v1");

      if (!form) {
        return;
      }

      event.preventDefault();
      event.stopPropagation();

      var userId = form.getAttribute("data-user-id") || "";
      var userEmail = form.getAttribute("data-user-email") || "";
      var message = "Tem a certeza que pretende eliminar este utilizador inativo?";

      if (userEmail) {
        message = message + "\n\n" + userEmail;
      }

      if (!window.confirm(message)) {
        return;
      }

      logDebug("submit-delete", {
        userId: userId,
        userEmail: userEmail
      });

      form.submit();
    },
    true
  );

  function startObserver() {
    if (!document.body) {
      return;
    }

    var observer = new MutationObserver(function () {
      scanInactiveTables();
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });
  }

  function boot() {
    scanInactiveTables();
    startObserver();

    window.setTimeout(scanInactiveTables, 300);
    window.setTimeout(scanInactiveTables, 1000);
    window.setTimeout(scanInactiveTables, 2500);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
''',
)


####################################################################################
# (3.2) INCLUIR JS NO NEW_USER.HTML
####################################################################################

new_user_path = "templates/new_user.html"
new_user = read_text_v1(new_user_path)

script_tag = '<script src="/static/js/modules/admin_user_inactive_delete_button_v1.js?v=20260513-delete-utilizador-shadow-v1"></script>'

if "admin_user_inactive_delete_button_v1.js" not in new_user:
    pattern = re.compile(
        r'(<script[^>]+admin_user_action_navigation_v1\.js[^>]*></script>)',
        re.IGNORECASE,
    )
    if pattern.search(new_user):
        new_user = pattern.sub(r"\1\n" + script_tag, new_user, count=1)
    else:
        endblock_index = new_user.rfind("{% endblock")
        if endblock_index >= 0:
            new_user = new_user[:endblock_index] + script_tag + "\n" + new_user[endblock_index:]
        else:
            new_user = new_user + "\n" + script_tag + "\n"

write_text_v1(new_user_path, new_user)


####################################################################################
# (3.3) GARANTIR QUE O PARTIAL REUTILIZÁVEL CONTINUA COM DELETE
####################################################################################

partial_path = "templates/partials/admin_user_table_v1.html"
partial = read_text_v1(partial_path)

if "admin-user-delete-button-v1" not in partial:
    partial = partial.replace(
        "</div>\n      </td>",
        '''
          {% if allow_delete %}
          <form
            class="admin-user-delete-form-v1"
            method="post"
            action="/users/delete"
            style="display:inline-flex;margin:0;padding:0;"
            data-user-id="{{ row.id }}"
            data-user-email="{{ row.login_email }}"
          >
            <input type="hidden" name="user_id" value="{{ row.id }}">
            <button
              type="submit"
              class="table-icon-btn table-icon-btn-danger admin-user-delete-button-v1"
              title="Eliminar utilizador"
              aria-label="Eliminar utilizador {{ row.login_email }}"
            >&#128465;</button>
          </form>
          {% endif %}
        </div>
      </td>''',
    )

write_text_v1(partial_path, partial)


####################################################################################
# (3.4) VALIDAÇÕES
####################################################################################

js_content = read_text_v1("static/js/modules/admin_user_inactive_delete_button_v1.js")
new_user_updated = read_text_v1("templates/new_user.html")
partial_updated = read_text_v1("templates/partials/admin_user_table_v1.html")

require_v1("APPVERBO_ADMIN_USER_INACTIVE_DELETE_BUTTON_V1" in js_content, "ERRO: JS de delete shadow não foi criado.")
require_v1("admin-user-delete-button-v1" in js_content, "ERRO: JS não cria botão de delete.")
require_v1("/users/delete" in js_content, "ERRO: JS não aponta para /users/delete.")
require_v1("admin_user_inactive_delete_button_v1.js" in new_user_updated, "ERRO: new_user.html não inclui o JS novo.")
require_v1("admin-user-delete-button-v1" in partial_updated, "ERRO: partial reutilizável sem botão delete.")

print("OK: delete em tabela shadow/inativos corrigido.")
