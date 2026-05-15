(function () {
    "use strict";

    //###################################################################################
    // (1) IDENTIFICACAO
    //###################################################################################

    var MARKER = "APPVERBO_ADMIN_TABS_EMERGENCY_UNLOCK_V4";

    if (window[MARKER]) {
        return;
    }

    window[MARKER] = true;

    //###################################################################################
    // (2) FUNCOES BASE
    //###################################################################################

    function normalizeText(value) {
        return String(value || "")
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "")
            .toLowerCase()
            .replace(/\s+/g, " ")
            .trim();
    }

    function isAdminPage() {
        var pathname = String(window.location.pathname || "");
        var search = String(window.location.search || "");
        return pathname === "/users/new" && search.indexOf("menu=administrativo") !== -1;
    }

    function getDirectTabName(element) {
        if (!element || !element.getAttribute) {
            return "";
        }

        var directValue =
            element.getAttribute("data-admin-tab") ||
            element.getAttribute("data-admin-tab-target") ||
            element.getAttribute("data-tab") ||
            element.getAttribute("data-key") ||
            element.getAttribute("data-subprocess-key") ||
            "";

        if (directValue) {
            return normalizeText(directValue);
        }

        var href = element.getAttribute("href") || "";

        if (href.indexOf("admin_tab=") !== -1) {
            try {
                var url = new URL(href, window.location.origin);
                return normalizeText(url.searchParams.get("admin_tab") || "");
            }
            catch (error) {
                return "";
            }
        }

        return "";
    }

    function getTabNameByText(element) {
        if (!element) {
            return "";
        }

        var text = normalizeText(element.textContent || element.innerText || "");

        if (!text) {
            return "";
        }

        if (text === "entidade") {
            return "entidade";
        }

        if (text === "utilizador") {
            return "utilizador";
        }

        if (text === "sessoes" || text === "sessao" || text === "sessões") {
            return "sessoes";
        }

        if (text === "menu") {
            return "menu";
        }

        return "";
    }

    function isVisible(element) {
        if (!element || !element.getBoundingClientRect) {
            return false;
        }

        var rect = element.getBoundingClientRect();

        return rect.width > 0 && rect.height > 0;
    }

    function pointInside(element, clientX, clientY) {
        if (!isVisible(element)) {
            return false;
        }

        var rect = element.getBoundingClientRect();

        return (
            clientX >= rect.left &&
            clientX <= rect.right &&
            clientY >= rect.top &&
            clientY <= rect.bottom
        );
    }

    //###################################################################################
    // (3) DETETAR ABA MESMO QUANDO O TARGET VEM COMO TABLIST
    //###################################################################################

    function findTabByCoordinates(event) {
        var selectors = [
            "#submenu-items",
            ".menu-tabs",
            ".admin-tabs",
            ".admin-subprocess-tabs",
            "[role='tablist']"
        ].join(",");

        var containers = Array.prototype.slice.call(document.querySelectorAll(selectors));

        for (var i = 0; i < containers.length; i += 1) {
            var container = containers[i];

            if (!pointInside(container, event.clientX, event.clientY)) {
                continue;
            }

            var candidates = Array.prototype.slice.call(
                container.querySelectorAll(
                    "a, button, [role='tab'], [data-admin-tab], [data-admin-tab-target], [data-tab], [data-key], [data-subprocess-key], .admin-tab, .admin-subprocess-tab, .menu-tab, li, span, div"
                )
            );

            for (var j = 0; j < candidates.length; j += 1) {
                var candidate = candidates[j];

                if (candidate === container) {
                    continue;
                }

                if (!pointInside(candidate, event.clientX, event.clientY)) {
                    continue;
                }

                var directName = getDirectTabName(candidate) || getTabNameByText(candidate);

                if (directName) {
                    return directName;
                }
            }

            var containerText = normalizeText(container.textContent || "");

            if (
                containerText.indexOf("entidade") !== -1 &&
                containerText.indexOf("utilizador") !== -1 &&
                containerText.indexOf("sessoes") !== -1 &&
                containerText.indexOf("menu") !== -1
            ) {
                var rect = container.getBoundingClientRect();
                var relativeX = event.clientX - rect.left;
                var ratio = relativeX / Math.max(rect.width, 1);
                var index = Math.floor(ratio * 4);
                var orderedTabs = ["entidade", "utilizador", "sessoes", "menu"];

                if (index < 0) {
                    index = 0;
                }

                if (index > 3) {
                    index = 3;
                }

                return orderedTabs[index];
            }
        }

        return "";
    }

    function findAdminTabElement(startElement) {
        var current = startElement;
        var depth = 0;

        while (current && current !== document && current !== window && depth < 10) {
            if (current.matches) {
                if (
                    current.matches("a[href*='admin_tab=']") ||
                    current.matches("button[data-admin-tab]") ||
                    current.matches("[data-admin-tab]") ||
                    current.matches("[data-admin-tab-target]") ||
                    current.matches("[data-tab]") ||
                    current.matches("[data-key]") ||
                    current.matches("[data-subprocess-key]") ||
                    current.matches(".admin-tab") ||
                    current.matches(".admin-subprocess-tab") ||
                    current.matches(".menu-tab") ||
                    current.matches("[role='tab']")
                ) {
                    return current;
                }
            }

            current = current.parentNode;
            depth += 1;
        }

        return null;
    }

    function isClickWithinAdminTabUi(event) {
        var target = event && event.target ? event.target : null;

        if (!target || !target.closest) {
            return false;
        }

        return Boolean(
            target.closest(
                "#submenu-items, .menu-tabs, .admin-tabs, .admin-subprocess-tabs, [role='tablist']"
            )
        );
    }

    function resolveTabName(event) {
        var tabElement = findAdminTabElement(event.target);

        if (tabElement) {
            return getDirectTabName(tabElement) || getTabNameByText(tabElement);
        }

        return getTabNameByText(event.target) || findTabByCoordinates(event);
    }

    //###################################################################################
    // (4) NAVEGACAO SEGURA ENTRE ABAS ADMINISTRATIVAS
    //###################################################################################

    function navigateToAdminTab(tabName) {
        if (!tabName) {
            return false;
        }

        var allowedTabs = {
            entidade: true,
            utilizador: true,
            sessoes: true,
            menu: true
        };

        if (!allowedTabs[tabName]) {
            return false;
        }

        var url = new URL(window.location.href);

        url.searchParams.set("menu", "administrativo");
        url.searchParams.set("admin_tab", tabName);
        url.searchParams.delete("sidebar_sections_tab");
        url.searchParams.delete("target");

        if (tabName === "entidade") {
            url.searchParams.set("target", "create-entity-card");
            url.hash = "create-entity-card";
        }
        else if (tabName === "sessoes") {
            url.searchParams.set("sidebar_sections_tab", "sessoes");
            url.searchParams.set("target", "admin-sidebar-sections-card");
            url.hash = "admin-sidebar-sections-card";
        }
        else {
            url.hash = "";
        }

        window.location.assign(url.toString());
        return true;
    }

    function handleAdminTabClick(event) {
        if (!isAdminPage()) {
            return;
        }

        if (!isClickWithinAdminTabUi(event)) {
            return;
        }

        var tabName = resolveTabName(event);

        if (!tabName) {
            return;
        }

        event.preventDefault();

        if (typeof event.stopImmediatePropagation === "function") {
            event.stopImmediatePropagation();
        }
        else if (typeof event.stopPropagation === "function") {
            event.stopPropagation();
        }

        navigateToAdminTab(tabName);
    }

    //###################################################################################
    // (5) ATIVACAO
    //###################################################################################

    function activateUnlock() {
        if (!document.body) {
            return;
        }

        document.body.classList.add("appverbo-admin-tabs-emergency-unlock-active");
    }

    document.addEventListener("click", handleAdminTabClick, true);

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", activateUnlock, { once: true });
    }
    else {
        activateUnlock();
    }

    window.APPVERBO_ADMIN_TABS_EMERGENCY_UNLOCK_HANDLE_CLICK_V4 = handleAdminTabClick;
})();
