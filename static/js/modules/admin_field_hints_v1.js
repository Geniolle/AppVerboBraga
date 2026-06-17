(function () {
  "use strict";

  if (!window.APPVERBO_ADMIN_FIELD_HINTS_V1) return;

  var HINT_CLASS = "admin-field-input-hint-v1";
  var FIELD_SELECTORS = ".field, .admin-subprocess-field-v1";
  var INPUT_QUERY = [
    'input:not([type="hidden"]):not([type="submit"]):not([type="button"]):not([type="reset"])[name]',
    "select[name]",
    "textarea[name]",
  ].join(", ");

  var PROCESS_FIELD_PREFIX = "process_field__";

  // Maps "menuKey|sectionKey" → DB table name for dynamic process form fields
  var DYNAMIC_PROCESS_TABLE_MAP = {
    "administrativo|custom_perfil_de_autorizacao": "process_view_authorization_rules",
    "perfil_de_autorizacao|custom_objeto_de_autorizacao": "process_view_authorization_rules",
  };

  // Fallback: maps menuKey alone → table name when section key is unknown
  var DYNAMIC_PROCESS_MENU_TABLE_MAP = {
    "perfil_de_autorizacao": "process_view_authorization_rules",
  };

  // Maps custom field key → actual DB column name, per table.
  // Custom keys are config identifiers (sidebar_menu_settings), NOT column names.
  var DYNAMIC_PROCESS_COLUMN_MAP = {
    "process_view_authorization_rules": {
      // Separador "Perfil"
      "custom_perfil":           "profile_name (perfil_header)",
      "custom_nome_do_perfil":   "profile_name",
      "custom_entidade":    "entity_id",
      "process_state":      "status",
      "numero_entidade":    "entity_id",
      // Separador "Objeto de autorização"
      "custom_processo":    "process_label",
      "custom_subprocesso": "subprocess_label",
      "custom_departamento":"department_name",
      "custom_visibilidade":"visibility_scope_mode",
      "__estado":           "status",
    },
  };

  function formatFieldName(rawName) {
    // Strip array brackets: "items[]" -> "items"
    return rawName.replace(/\[\]$/, "").trim();
  }

  function buildHintText(rawName, fieldEl) {
    var cleaned = formatFieldName(rawName);

    if (cleaned.indexOf(PROCESS_FIELD_PREFIX) === 0) {
      var fieldKey = cleaned.slice(PROCESS_FIELD_PREFIX.length);
      var form = fieldEl.closest ? fieldEl.closest("#dynamic-process-edit-form") : null;
      if (form) {
        var menuKeyEl = document.getElementById("dynamic-process-menu-key");
        var sectionKeyEl = document.getElementById("dynamic-process-section-key");
        var menuKeyVal = menuKeyEl ? menuKeyEl.value : "";
        var sectionKeyVal = sectionKeyEl ? sectionKeyEl.value : "";
        var mapKey = menuKeyVal + "|" + sectionKeyVal;
        var tableName =
          DYNAMIC_PROCESS_TABLE_MAP[mapKey] ||
          DYNAMIC_PROCESS_MENU_TABLE_MAP[menuKeyVal];
        if (tableName) {
          // Resolve actual DB column name when the field key is a config alias
          var columnMap = DYNAMIC_PROCESS_COLUMN_MAP[tableName];
          var columnName = (columnMap && columnMap[fieldKey]) || fieldKey;
          return "(" + columnName + ")";
        }
        return "(" + fieldKey + ")";
      }
      return "(" + fieldKey + ")";
    }

    return "(" + cleaned + ")";
  }

  function processFieldEl(field) {
    var input = field.querySelector(INPUT_QUERY);
    if (!input) return;

    var rawName = (input.name || "").trim();
    if (!rawName) return;

    var label = null;
    if (input.id) {
      try {
        label = field.querySelector('label[for="' + CSS.escape(input.id) + '"]');
      } catch (_) {
        label = null;
      }
    }
    if (!label) {
      label = field.querySelector("label");
    }
    if (!label) return;

    // Avoid duplicate hints (server-side hints or previous JS run)
    if (label.querySelector("." + HINT_CLASS)) return;

    var hint = document.createElement("span");
    hint.className = HINT_CLASS;
    hint.textContent = buildHintText(rawName, field);
    label.appendChild(hint);
  }

  function injectHints(root) {
    // Also check the root element itself in case it matches (e.g., dynamically added .field)
    if (root !== document && root.matches && root.matches(FIELD_SELECTORS)) {
      processFieldEl(root);
    }
    var fields = (root || document).querySelectorAll(FIELD_SELECTORS);
    for (var i = 0; i < fields.length; i++) {
      processFieldEl(fields[i]);
    }
  }

  function init() {
    injectHints(document);

    if (!window.MutationObserver) return;

    var observer = new MutationObserver(function (mutations) {
      for (var i = 0; i < mutations.length; i++) {
        var added = mutations[i].addedNodes;
        for (var j = 0; j < added.length; j++) {
          if (added[j].nodeType === 1) {
            injectHints(added[j]);
          }
        }
      }
    });

    observer.observe(document.body, { childList: true, subtree: true });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
