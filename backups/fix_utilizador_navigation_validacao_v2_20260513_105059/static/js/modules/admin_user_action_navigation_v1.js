"use strict";

/*
 * APPVERBO_ADMIN_USER_ACTION_NAVIGATION_V1
 *
 * Responsabilidade única:
 * - capturar cliques nos ícones/links de ação do subprocesso Utilizador;
 * - validar se o destino pertence ao subprocesso Utilizador;
 * - normalizar a URL para Exibir/Editar;
 * - navegar sem depender de handlers genéricos da página.
 */
(function () {
    const MODULE_NAME_V1 = "APPVERBO_ADMIN_USER_ACTION_NAVIGATION_V1";
    const BOUND_FLAG_V1 = "__APPVERBO_ADMIN_USER_ACTION_NAVIGATION_V1_BOUND__";

    function normalizarUrlAcaoUtilizador_v1(rawHref) {
        if (!rawHref) {
            return null;
        }

        try {
            return new URL(String(rawHref), window.location.origin);
        } catch (error) {
            return null;
        }
    }

    function isUrlAcaoUtilizador_v1(url) {
        if (!url) {
            return false;
        }

        if (url.pathname !== "/users/new") {
            return false;
        }

        if (url.searchParams.get("menu") !== "administrativo") {
            return false;
        }

        if (url.searchParams.get("admin_tab") !== "utilizador") {
            return false;
        }

        if (!url.searchParams.get("user_edit_id")) {
            return false;
        }

        const userView = url.searchParams.get("user_view");
        return userView === "1" || userView === "0";
    }

    function normalizarDestinoUtilizador_v1(url) {
        const destino = new URL("/users/new", window.location.origin);

        destino.searchParams.set("menu", "administrativo");
        destino.searchParams.set("admin_tab", "utilizador");
        destino.searchParams.set("user_edit_id", url.searchParams.get("user_edit_id"));
        destino.searchParams.set("user_view", url.searchParams.get("user_view"));
        destino.searchParams.set("target", "edit-user-card");
        destino.hash = "edit-user-card";

        return destino.pathname + destino.search + destino.hash;
    }

    function localizarLinkAcaoUtilizador_v1(eventTarget) {
        if (!eventTarget || typeof eventTarget.closest !== "function") {
            return null;
        }

        return eventTarget.closest(
            'a[href][data-appverbo-user-action], ' +
            'a[href].appverbo-user-action-link, ' +
            'a[href].table-icon-btn, ' +
            'a[href][title="Exibir"], ' +
            'a[href][title="Editar"]'
        );
    }

    function extrairHrefAcaoUtilizador_v1(actionElement) {
        if (!actionElement) {
            return "";
        }

        const href = actionElement.getAttribute("href") || "";
        return String(href).trim();
    }

    function deveIgnorarCliqueEspecial_v1(event) {
        if (!event) {
            return true;
        }

        if (event.defaultPrevented) {
            return true;
        }

        if (event.button && event.button !== 0) {
            return true;
        }

        return Boolean(event.metaKey || event.ctrlKey || event.shiftKey || event.altKey);
    }

    function navegarParaAcaoUtilizador_v1(event) {
        if (deveIgnorarCliqueEspecial_v1(event)) {
            return;
        }

        const actionElement = localizarLinkAcaoUtilizador_v1(event.target);
        if (!actionElement) {
            return;
        }

        const href = extrairHrefAcaoUtilizador_v1(actionElement);
        const url = normalizarUrlAcaoUtilizador_v1(href);

        if (!isUrlAcaoUtilizador_v1(url)) {
            return;
        }

        const destino = normalizarDestinoUtilizador_v1(url);
        if (!destino) {
            return;
        }

        event.preventDefault();
        event.stopPropagation();

        if (typeof event.stopImmediatePropagation === "function") {
            event.stopImmediatePropagation();
        }

        window.location.assign(destino);
    }

    function inicializarNavegacaoAcoesUtilizador_v1() {
        if (window[BOUND_FLAG_V1]) {
            return;
        }

        window[BOUND_FLAG_V1] = true;
        document.addEventListener("click", navegarParaAcaoUtilizador_v1, true);
    }

    inicializarNavegacaoAcoesUtilizador_v1();

    window.APPVERBO_ADMIN_USER_ACTION_NAVIGATION_V1 = {
        moduleName: MODULE_NAME_V1,
        normalizarUrlAcaoUtilizador_v1,
        isUrlAcaoUtilizador_v1,
        normalizarDestinoUtilizador_v1,
        localizarLinkAcaoUtilizador_v1,
        extrairHrefAcaoUtilizador_v1,
        navegarParaAcaoUtilizador_v1,
        inicializarNavegacaoAcoesUtilizador_v1
    };
})();