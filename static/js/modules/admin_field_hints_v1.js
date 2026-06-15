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

  function formatFieldName(rawName) {
    // Strip array brackets: "items[]" -> "items", "rows[0][key]" -> "rows[0][key]" (kept as-is)
    return rawName.replace(/\[\]$/, "").trim();
  }

  function injectHints(root) {
    var fields = (root || document).querySelectorAll(FIELD_SELECTORS);
    for (var i = 0; i < fields.length; i++) {
      var field = fields[i];
      var input = field.querySelector(INPUT_QUERY);
      if (!input) continue;

      var rawName = (input.name || "").trim();
      if (!rawName) continue;

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
      if (!label) continue;

      // Avoid duplicate hints (manual server-side hints or previous JS run)
      if (label.querySelector("." + HINT_CLASS)) continue;

      var hint = document.createElement("span");
      hint.className = HINT_CLASS;
      hint.textContent = "(" + formatFieldName(rawName) + ")";
      label.appendChild(hint);
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
