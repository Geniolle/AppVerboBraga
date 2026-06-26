/* tabs_overflow_v1.js — responsive tab bar with "Mais" overflow dropdown */
(function () {
  "use strict";

  // Pixel buffer between last visible tab and "Mais" button
  var SAFETY_PX = 4;
  // Gap between button bottom and dropdown top
  var MENU_OFFSET_Y = 4;

  // Tab groups to manage. Add entries here to extend to other containers.
  var TAB_GROUPS = [
    {
      containerSelector: "#process-edit-tabs",
      itemSelector: ".process-edit-tab-link",
      activeClass: "active"
    },
    {
      containerSelector: "#submenu-items.menu-tabs",
      itemSelector: ".submenu-item",
      activeClass: "active"
    }
  ];

  // ================================================================
  // OVERFLOW CONTROLLER
  // ================================================================

  function createOverflowController(container, itemSelector, activeClass) {
    var destroyed = false;
    var moreBtn = null;
    var moreMenu = null;
    var isMenuOpen = false;
    var resizeObs = null;
    var mutObs = null;
    var recalcTimer = null;

    // Returns all tab items (excludes the "Mais" button itself)
    function getAllTabs() {
      return Array.from(container.querySelectorAll(itemSelector)).filter(function (el) {
        return !el.classList.contains("appverbo-tabs-more-btn-v1");
      });
    }

    // Position the dropdown below the "Mais" button using fixed coordinates
    function positionMenu() {
      if (!moreBtn || !moreMenu) return;
      var r = moreBtn.getBoundingClientRect();
      moreMenu.style.top = (r.bottom + MENU_OFFSET_Y) + "px";
      moreMenu.style.right = (window.innerWidth - r.right) + "px";
    }

    function closeMenu() {
      if (!isMenuOpen || !moreMenu || !moreBtn) return;
      moreMenu.style.display = "none";
      moreBtn.setAttribute("aria-expanded", "false");
      isMenuOpen = false;
    }

    function openMenu() {
      if (isMenuOpen || !moreMenu || !moreBtn) return;
      positionMenu();
      moreMenu.style.display = "block";
      moreBtn.setAttribute("aria-expanded", "true");
      isMenuOpen = true;
    }

    function onMoreBtnClick(e) {
      e.stopPropagation();
      isMenuOpen ? closeMenu() : openMenu();
    }

    // Close when clicking outside both the button and the dropdown
    function onDocClick(e) {
      if (!isMenuOpen) return;
      if (moreBtn && moreBtn.contains(e.target)) return;
      if (moreMenu && moreMenu.contains(e.target)) return;
      closeMenu();
    }

    function onDocKeydown(e) {
      if (e.key === "Escape" && isMenuOpen) {
        closeMenu();
        if (moreBtn) moreBtn.focus();
      }
    }

    // Reposition dropdown on scroll or resize while open
    function onScrollOrResize() {
      if (isMenuOpen) positionMenu();
    }

    // Sync active class on dropdown items after a tab has been activated
    function refreshDropdownActiveStates() {
      if (!moreMenu || !moreBtn) return;
      var hiddenTabs = getAllTabs().filter(function (t) {
        return t.dataset.tabsOverflowHidden === "1";
      });
      var items = Array.from(moreMenu.querySelectorAll(".appverbo-tabs-more-item-v1"));
      var hasActive = false;
      hiddenTabs.forEach(function (tab, i) {
        var isActive = tab.classList.contains(activeClass);
        if (isActive) hasActive = true;
        if (items[i]) items[i].classList.toggle(activeClass, isActive);
      });
      moreBtn.classList.toggle("appverbo-tabs-more-btn-active-v1", hasActive);
    }

    function buildDropdown(hiddenTabs) {
      if (!moreMenu) return;
      moreMenu.innerHTML = "";
      hiddenTabs.forEach(function (tab) {
        var btn = document.createElement("button");
        btn.type = "button";
        btn.className = "appverbo-tabs-more-item-v1";
        btn.setAttribute("role", "menuitem");
        btn.textContent = tab.textContent.trim();
        if (tab.classList.contains(activeClass)) btn.classList.add(activeClass);
        btn.addEventListener("click", function (e) {
          e.stopPropagation();
          // Fire click on the original (hidden) tab element.
          // For #process-edit-tabs: activateProcessTab() is called via the tab's own listener.
          // For #submenu-items: handleContainerClick() in createTopSubmenuController
          //   uses event delegation and receives bubbled events from hidden elements too.
          tab.click();
          closeMenu();
          setTimeout(refreshDropdownActiveStates, 30);
        });
        moreMenu.appendChild(btn);
      });
    }

    // Re-append moreBtn to container if it was removed by render()/replaceChildren()
    function ensureButtonInContainer() {
      if (moreBtn && !container.contains(moreBtn)) {
        container.appendChild(moreBtn);
      }
    }

    function recalculate() {
      if (destroyed) return;

      // Restore the button if a render() call removed it
      ensureButtonInContainer();

      var tabs = getAllTabs();
      if (!tabs.length) {
        if (moreBtn) moreBtn.style.display = "none";
        return;
      }

      // 1. Reset: show all tabs, hide "Mais"
      tabs.forEach(function (t) {
        t.style.display = "";
        delete t.dataset.tabsOverflowHidden;
      });
      if (moreBtn) moreBtn.style.display = "none";

      // 2. Guard: container must be rendered and have width
      var containerRect = container.getBoundingClientRect();
      if (!containerRect.width) return;

      // 3. Detect overflow: any tab whose right edge exceeds the container right
      //    Works because .appverbo-tabs-overflow-v1 sets flex-wrap:nowrap on the container
      var anyOverflow = tabs.some(function (t) {
        return t.getBoundingClientRect().right > containerRect.right + 1;
      });
      if (!anyOverflow) return;

      // 4. Show "Mais" button to measure its natural width
      if (!moreBtn) return;
      moreBtn.style.display = "";
      var moreBtnWidth = moreBtn.getBoundingClientRect().width || 70;

      // 5. The right boundary beyond which a tab is considered overflowing
      var reservedRight = containerRect.right - moreBtnWidth - SAFETY_PX;

      // 6. Find the first tab that exceeds the reserved boundary
      var cutIndex = -1;
      for (var i = 0; i < tabs.length; i++) {
        if (tabs[i].getBoundingClientRect().right > reservedRight + 1) {
          cutIndex = Math.max(i, 1); // always keep at least one tab visible
          break;
        }
      }

      // All tabs fit within the reserved space — no overflow needed
      if (cutIndex < 0) {
        moreBtn.style.display = "none";
        return;
      }

      // 7. Hide overflow tabs
      var hiddenTabs = [];
      for (var j = cutIndex; j < tabs.length; j++) {
        tabs[j].style.display = "none";
        tabs[j].dataset.tabsOverflowHidden = "1";
        hiddenTabs.push(tabs[j]);
      }

      // 8. Build dropdown and sync active indicator on "Mais" button
      buildDropdown(hiddenTabs);
      var hasActive = hiddenTabs.some(function (t) { return t.classList.contains(activeClass); });
      moreBtn.classList.toggle("appverbo-tabs-more-btn-active-v1", hasActive);
    }

    function scheduleRecalculate() {
      clearTimeout(recalcTimer);
      recalcTimer = setTimeout(recalculate, 80);
    }

    function init() {
      container.dataset.tabsOverflowBound = "1";
      container.classList.add("appverbo-tabs-overflow-v1");

      // "Mais" button lives inside the container.
      // For #submenu-items, render() may remove it via replaceChildren() —
      // the MutationObserver below detects this and re-appends it.
      moreBtn = document.createElement("button");
      moreBtn.type = "button";
      moreBtn.className = "appverbo-tabs-more-btn-v1";
      moreBtn.setAttribute("aria-haspopup", "menu");
      moreBtn.setAttribute("aria-expanded", "false");
      moreBtn.innerHTML = 'Mais <span class="appverbo-tabs-more-arrow-v1" aria-hidden="true">&#9660;</span>';
      moreBtn.style.display = "none";
      container.appendChild(moreBtn);

      // Dropdown is appended to document.body with position:fixed so it is
      // never clipped by parent overflow:hidden/auto containers.
      moreMenu = document.createElement("div");
      moreMenu.className = "appverbo-tabs-more-menu-v1";
      moreMenu.setAttribute("role", "menu");
      moreMenu.style.display = "none";
      document.body.appendChild(moreMenu);

      // Event listeners
      moreBtn.addEventListener("click", onMoreBtnClick);
      document.addEventListener("click", onDocClick);
      document.addEventListener("keydown", onDocKeydown);
      window.addEventListener("scroll", onScrollOrResize, true);

      // MutationObserver watches for:
      // childList — render() / replaceChildren() removing the "Mais" button (top submenu)
      // attributes(class) — tab activation to keep dropdown state in sync
      mutObs = new MutationObserver(function (mutations) {
        // If moreBtn was swept out by replaceChildren / innerHTML = "", re-attach it
        if (moreBtn && !container.contains(moreBtn)) {
          container.appendChild(moreBtn);
          scheduleRecalculate();
          return;
        }

        var childrenChanged = mutations.some(function (m) { return m.type === "childList"; });
        var classChanged = mutations.some(function (m) {
          return m.type === "attributes" && m.attributeName === "class" &&
            m.target !== moreBtn;
        });

        if (childrenChanged) {
          scheduleRecalculate();
        } else if (classChanged) {
          refreshDropdownActiveStates();
        }
      });

      mutObs.observe(container, {
        childList: true,
        attributes: true,
        subtree: true,
        attributeFilter: ["class"]
      });

      // ResizeObserver for container width changes (e.g., sidebar open/close)
      if (typeof ResizeObserver !== "undefined") {
        resizeObs = new ResizeObserver(scheduleRecalculate);
        resizeObs.observe(container);
      }

      recalculate();
    }

    function destroy() {
      if (destroyed) return;
      destroyed = true;
      clearTimeout(recalcTimer);
      document.removeEventListener("click", onDocClick);
      document.removeEventListener("keydown", onDocKeydown);
      window.removeEventListener("scroll", onScrollOrResize, true);
      if (mutObs) { mutObs.disconnect(); mutObs = null; }
      if (resizeObs) { resizeObs.disconnect(); resizeObs = null; }
      getAllTabs().forEach(function (t) {
        t.style.display = "";
        delete t.dataset.tabsOverflowHidden;
      });
      container.classList.remove("appverbo-tabs-overflow-v1");
      delete container.dataset.tabsOverflowBound;
      if (moreBtn) { moreBtn.remove(); moreBtn = null; }
      if (moreMenu) { moreMenu.remove(); moreMenu = null; } // body-appended
    }

    init();
    return { recalculate: recalculate, destroy: destroy };
  }

  // ================================================================
  // MANAGER
  // ================================================================

  var _controllers = [];
  var _winResizeTimer = null;

  // Init controllers for any new containers not yet managed
  function ensureAll() {
    TAB_GROUPS.forEach(function (group) {
      Array.from(document.querySelectorAll(group.containerSelector)).forEach(function (container) {
        if (container.dataset.tabsOverflowBound === "1") return;
        _controllers.push(
          createOverflowController(container, group.itemSelector, group.activeClass)
        );
      });
    });
  }

  function scheduleRecalculateAll() {
    clearTimeout(_winResizeTimer);
    _winResizeTimer = setTimeout(function () {
      _controllers.forEach(function (c) { c.recalculate(); });
    }, 100);
  }

  function start() {
    ensureAll();
    window.addEventListener("resize", scheduleRecalculateAll);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }

  // Extra passes: new_user.js (non-deferred) runs before this deferred script
  // and populates #submenu-items. Extra passes catch any late renders.
  setTimeout(ensureAll, 150);
  setTimeout(function () {
    ensureAll();
    _controllers.forEach(function (c) { c.recalculate(); });
  }, 600);

  // Public API
  window.AppVerboTabsOverflowV1 = {
    recalculate: function () {
      _controllers.forEach(function (c) { c.recalculate(); });
    },
    reinit: ensureAll
  };

})();
