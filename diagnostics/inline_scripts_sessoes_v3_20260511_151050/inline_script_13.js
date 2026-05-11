
(function () {
  "use strict";

  document.addEventListener("click", function (event) {
    var button = event.target && event.target.closest
      ? event.target.closest("[data-menu-view-label]")
      : null;

    if (!button) {
      return;
    }

    alert(
      "Menu: " + (button.getAttribute("data-menu-view-label") || "") + "\n" +
      "Sistema: " + (button.getAttribute("data-menu-view-scope") || "") + "\n" +
      "Estado: " + (button.getAttribute("data-menu-view-status") || "")
    );
  }, true);
})();
