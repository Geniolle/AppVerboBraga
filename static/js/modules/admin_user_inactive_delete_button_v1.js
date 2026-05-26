(function () {
  "use strict";

  var FLAG = "APPVERBO_ADMIN_USER_ACTION_GUARD_V6";
  var DELETE_RETURN_TARGET = "admin-user-shadow-inactive-card";
  var DELETE_POST_SAVE_STORAGE_KEYS = [
    "appverbo:post-save-context-v3",
    "appverbo:return-url-post-save-v4",
    "appverbo:return_after_save",
    "appverbo:return_after_save_time"
  ];

  if (window[FLAG]) {
    return;
  }

  window[FLAG] = true;

  function logDebug(stage, data) {
    try {
      console.log("APPVERBO_ADMIN_USER_ACTION_GUARD_V6", stage, data || {});
    } catch (error) {
      // noop
    }
  }

  function normalizeText(value) {
    return String(value || "").trim().toLowerCase();
  }

  function isUserEditHref(href) {
    var cleanHref = String(href || "");
    return cleanHref.indexOf("/users/new") >= 0 && cleanHref.indexOf("user_edit_id=") >= 0;
  }

  function parseUserIdFromHref(href) {
    var cleanHref = String(href || "");
    var match = cleanHref.match(/[?&]user_edit_id=(\d+)/);

    if (match && match[1]) {
      return match[1];
    }

    return "";
  }

  function closestInactiveContainer(row) {
    if (!row || !row.closest) {
      return null;
    }

    return row.closest(
      "#admin-user-shadow-inactive-card, #inactive-users-card, [data-admin-subprocess-shadow='utilizador-inactive']"
    );
  }

  function rowLooksInactive(row) {
    if (closestInactiveContainer(row)) {
      return true;
    }

    var text = normalizeText(row.textContent);
    return text.indexOf("inativo") >= 0 || text.indexOf("inactive") >= 0;
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
    button.className = "table-icon-btn admin-user-delete-button-v1";
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

    // Evita duplicacao quando o backend ja renderizou um botao de eliminar
    // com classes/atributos diferentes entre layouts legados e novos.
    if (
      row.querySelector(
        ".admin-user-delete-form-v1, " +
        ".admin-user-delete-button-v1, " +
        ".table-icon-btn-danger, " +
        ".admin-subprocess-action-btn-danger-v1, " +
        "[data-appverbo-user-action='delete'], " +
        "[title*='Eliminar'], " +
        "[aria-label*='Eliminar']"
      )
    ) {
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

  function cleanupInjectedDeleteDuplicatesV1(row) {
    if (!row || !row.querySelectorAll) {
      return 0;
    }

    var hasNativeDelete = Boolean(
      row.querySelector(
        ".table-icon-btn-danger, " +
        ".admin-subprocess-action-btn-danger-v1, " +
        "[data-appverbo-user-action='delete']"
      )
    );

    if (!hasNativeDelete) {
      return 0;
    }

    var injectedForms = row.querySelectorAll("form[data-appverbo-delete-injected='1']");
    var removedCount = 0;
    var index;

    for (index = 0; index < injectedForms.length; index += 1) {
      var form = injectedForms[index];
      if (form && form.parentNode) {
        form.parentNode.removeChild(form);
        removedCount += 1;
      }
    }

    return removedCount;
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
        cleanupInjectedDeleteDuplicatesV1(rows[rowIndex]);
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
        cleanupInjectedDeleteDuplicatesV1(tableRows[tableRowIndex]);
        if (ensureDeleteButtonForRow(tableRows[tableRowIndex])) {
          totalAdded += 1;
        }
      }
    }

    if (totalAdded > 0) {
      logDebug("scan-complete", { added: totalAdded });
    }
  }

  function submitDeleteForm(form) {
    submitDeleteFormSemConfirmacao_v1(form);
  }

  function buildDeleteReturnPath_v1() {
    var url = new URL("/users/new", window.location.origin);

    url.searchParams.set("menu", "administrativo");
    url.searchParams.set("admin_tab", "utilizador");
    url.searchParams.set("target", DELETE_RETURN_TARGET);
    url.hash = DELETE_RETURN_TARGET;

    return url.pathname + url.search + url.hash;
  }

  function normalizeDeleteReturnContext_v1() {
    if (!window.history || typeof window.history.replaceState !== "function") {
      return "";
    }

    var returnPath = buildDeleteReturnPath_v1();

    try {
      window.history.replaceState(window.history.state || {}, document.title, returnPath);
    } catch (error) {
      return "";
    }

    return returnPath;
  }

  function clearDeletePostSaveContext_v1() {
    var index;
    var key;

    try {
      for (index = 0; index < DELETE_POST_SAVE_STORAGE_KEYS.length; index += 1) {
        window.sessionStorage.removeItem(DELETE_POST_SAVE_STORAGE_KEYS[index]);
      }

      for (index = window.sessionStorage.length - 1; index >= 0; index -= 1) {
        key = String(window.sessionStorage.key(index) || "");

        if (
          key.indexOf("appverbo:post-save-context") >= 0 ||
          key.indexOf("appverbo:return-url-post-save") >= 0
        ) {
          window.sessionStorage.removeItem(key);
        }
      }
    } catch (error) {
      // sessionStorage pode estar indisponivel em alguns contextos do browser.
    }
  }

  function submitDeleteFormSemConfirmacao_v1(form) {
    var userId = form.getAttribute("data-user-id") || "";
    var userEmail = form.getAttribute("data-user-email") || "";

    clearDeletePostSaveContext_v1();

    var returnPath = normalizeDeleteReturnContext_v1();

    logDebug("submit-delete-direct", {
      userId: userId,
      userEmail: userEmail,
      returnPath: returnPath
    });

    HTMLFormElement.prototype.submit.call(form);
  }

  function navigateUserAction(link) {
    var href = link.getAttribute("href");

    if (!href) {
      return;
    }

    logDebug("navigate-user-action", {
      href: href,
      title: link.getAttribute("title") || ""
    });

    window.location.assign(href);
  }

  document.addEventListener(
    "click",
    function (event) {
      var target = event.target;

      if (!target || !target.closest) {
        return;
      }

      var deleteButton = target.closest(".admin-user-delete-button-v1");

      if (deleteButton) {
        var deleteForm = deleteButton.closest("form.admin-user-delete-form-v1");

        if (!deleteForm) {
          return;
        }

        event.preventDefault();
        event.stopPropagation();
        event.stopImmediatePropagation();

        submitDeleteFormSemConfirmacao_v1(deleteForm);
        return;
      }

      var actionLink = target.closest("a[href*='user_edit_id=']");

      if (actionLink && isUserEditHref(actionLink.getAttribute("href"))) {
        event.preventDefault();
        event.stopPropagation();
        event.stopImmediatePropagation();

        navigateUserAction(actionLink);
      }
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

    window.setTimeout(scanInactiveTables, 100);
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
