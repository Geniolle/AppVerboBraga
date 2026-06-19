//###################################################################################
// APPVERBOBRAGA - ADMIN MENU FOOTER DEDUPE V1
//###################################################################################

(function () {
  "use strict";

  //###################################################################################
  // (1) FUNCOES BASE
  //###################################################################################

  function normalizarTextoMenuFooterDedupe_v1(value) {
    return String(value || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase()
      .trim();
  }

  function isCardMenuFooterDedupe_v1(cardEl) {
    if (!cardEl) {
      return false;
    }

    const titleEl = cardEl.querySelector("h2, h3");
    const titleText = normalizarTextoMenuFooterDedupe_v1(titleEl ? titleEl.textContent : "");

    return titleText.indexOf("menus ativos") >= 0 || titleText.indexOf("menus inativos") >= 0;
  }

  function getFooterRootMenuFooterDedupe_v1(element) {
    if (!element) {
      return null;
    }

    return element.closest(
      "[data-admin-table-footer-standard-v1='1'], " +
      ".admin-table-footer-standard-v1, " +
      ".admin-status-table-footer-v1, " +
      ".table-limiter, " +
      "[id$='-limiter']"
    );
  }

  function getFooterCandidatesMenuFooterDedupe_v1(cardEl) {
    if (!cardEl) {
      return [];
    }

    const selector = [
      "[data-admin-table-footer-standard-v1='1']",
      ".admin-table-footer-standard-v1",
      ".admin-status-table-footer-v1",
      ".table-limiter",
      "[id$='-limiter']"
    ].join(",");

    const rawCandidates = Array.from(cardEl.querySelectorAll(selector));
    const uniqueCandidates = [];

    rawCandidates.forEach(function (candidateEl) {
      const footerRoot = getFooterRootMenuFooterDedupe_v1(candidateEl);

      if (!footerRoot || footerRoot !== candidateEl) {
        return;
      }

      if (uniqueCandidates.indexOf(footerRoot) < 0) {
        uniqueCandidates.push(footerRoot);
      }
    });

    uniqueCandidates.sort(function (leftEl, rightEl) {
      if (leftEl === rightEl) {
        return 0;
      }

      if (leftEl.compareDocumentPosition(rightEl) & Node.DOCUMENT_POSITION_FOLLOWING) {
        return -1;
      }

      return 1;
    });

    return uniqueCandidates;
  }

  function showFooterMenuFooterDedupe_v1(footerEl) {
    if (!footerEl) {
      return;
    }

    footerEl.classList.remove("admin-menu-footer-duplicate-hidden-v1");
    footerEl.removeAttribute("data-admin-menu-footer-duplicate-hidden-v1");

    if (footerEl.style.display === "none") {
      footerEl.style.display = "";
    }
  }

  function hideFooterMenuFooterDedupe_v1(footerEl) {
    if (!footerEl) {
      return;
    }

    footerEl.classList.add("admin-menu-footer-duplicate-hidden-v1");
    footerEl.setAttribute("data-admin-menu-footer-duplicate-hidden-v1", "1");
    footerEl.style.display = "none";
  }

  //###################################################################################
  // (2) CORRIGIR DUPLICACAO SOMENTE NOS CARDS DO SUBPROCESSO MENU
  //###################################################################################

  function aplicarDedupeMenuFooterDedupe_v1(rootEl) {
    const scopeEl = rootEl || document;
    const cards = Array.from(scopeEl.querySelectorAll(".card, section, .admin-subprocess-table-card-v1"));

    cards.forEach(function (cardEl) {
      if (!isCardMenuFooterDedupe_v1(cardEl)) {
        return;
      }

      const footers = getFooterCandidatesMenuFooterDedupe_v1(cardEl);

      if (footers.length <= 1) {
        if (footers.length === 1) {
          showFooterMenuFooterDedupe_v1(footers[0]);
        }

        return;
      }

      footers.forEach(function (footerEl, index) {
        if (index === 0) {
          showFooterMenuFooterDedupe_v1(footerEl);
          return;
        }

        hideFooterMenuFooterDedupe_v1(footerEl);
      });
    });
  }

  //###################################################################################
  // (3) EXECUTAR APOS OUTROS MODULOS E REAPLICAR SE HOUVER RENDER DINAMICO
  //###################################################################################

  function scheduleDedupeMenuFooterDedupe_v1() {
    window.setTimeout(function () {
      aplicarDedupeMenuFooterDedupe_v1(document);
    }, 50);

    window.setTimeout(function () {
      aplicarDedupeMenuFooterDedupe_v1(document);
    }, 250);

    window.setTimeout(function () {
      aplicarDedupeMenuFooterDedupe_v1(document);
    }, 750);
  }

  function startObserverMenuFooterDedupe_v1() {
    if (!document.body || window.AppVerboAdminMenuFooterDedupeObserverStarted_v1) {
      return;
    }

    const observer = new MutationObserver(function () {
      scheduleDedupeMenuFooterDedupe_v1();
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });

    window.AppVerboAdminMenuFooterDedupeObserverStarted_v1 = true;
  }

  window.AppVerboAdminMenuFooterDedupe_v1 = {
    aplicarDedupeMenuFooterDedupe_v1: aplicarDedupeMenuFooterDedupe_v1
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      scheduleDedupeMenuFooterDedupe_v1();
      startObserverMenuFooterDedupe_v1();
    });
  } else {
    scheduleDedupeMenuFooterDedupe_v1();
    startObserverMenuFooterDedupe_v1();
  }

  window.addEventListener("load", scheduleDedupeMenuFooterDedupe_v1);
})();
