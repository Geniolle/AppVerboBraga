
(function () {
  "use strict";

  //###################################################################################
  // (1) CONFIGURACOES GERAIS
  //###################################################################################

  var STORAGE_KEY = "appverbo_admin_sessoes_tab_reloaded_v3";
  var navegacaoEmCurso = false;

  //###################################################################################
  // (2) NORMALIZACAO DE TEXTO
  //###################################################################################

  function normalizarTextoSessoesTab_v3(valor) {
    return String(valor || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/\s+/g, " ")
      .trim()
      .toLowerCase();
  }

  //###################################################################################
  // (3) VALIDAR URL DA ABA SESSOES
  //###################################################################################

  function criarUrlSessoesTab_v3(valor) {
    try {
      return new URL(valor || window.location.href, window.location.origin);
    } catch (erro) {
      return new URL(window.location.href);
    }
  }

  function urlRepresentaSessoesTab_v3(valor) {
    var url = criarUrlSessoesTab_v3(valor);
    var adminTab = normalizarTextoSessoesTab_v3(url.searchParams.get("admin_tab"));
    return adminTab === "sessoes" || adminTab === "sessões";
  }

  //###################################################################################
  // (4) DETECTAR CONTEUDO REAL DE SESSOES
  //###################################################################################

  function conteudoSessoesEstaRenderizado_v3() {
    var textoPagina = normalizarTextoSessoesTab_v3(document.body ? document.body.innerText : "");

    if (
      textoPagina.indexOf("criar sessao") >= 0 ||
      textoPagina.indexOf("editar sessao") >= 0 ||
      textoPagina.indexOf("sessoes ativas") >= 0 ||
      textoPagina.indexOf("sessoes inativas") >= 0 ||
      textoPagina.indexOf("sessoes do sidebar") >= 0
    ) {
      return true;
    }

    return Boolean(
      document.querySelector("#admin-sidebar-sections-form-card") ||
      document.querySelector("#admin-sidebar-sections-card") ||
      document.querySelector("#admin-sidebar-sections-active-card-v23") ||
      document.querySelector("#admin-sidebar-sections-inactive-card-v23") ||
      document.querySelector('[data-admin-subprocess-v2="sidebar_section"]') ||
      document.querySelector('[data-admin-subprocess-v2="sessoes"]')
    );
  }

  //###################################################################################
  // (5) FORCAR RELOAD QUANDO A URL ESTA EM SESSOES MAS O CONTEUDO FICOU VAZIO
  //###################################################################################

  function recarregarSeSessoesFicouVazio_v3(origem) {
    if (!urlRepresentaSessoesTab_v3(window.location.href)) {
      return;
    }

    window.setTimeout(function () {
      var urlAtual = window.location.href;

      if (conteudoSessoesEstaRenderizado_v3()) {
        try {
          window.sessionStorage.removeItem(STORAGE_KEY);
        } catch (erroStorageLimpar) {}
        return;
      }

      try {
        if (window.sessionStorage.getItem(STORAGE_KEY) === urlAtual) {
          return;
        }

        window.sessionStorage.setItem(STORAGE_KEY, urlAtual);
      } catch (erroStorage) {}

      window.location.reload();
    }, 250);
  }

  //###################################################################################
  // (6) IDENTIFICAR ELEMENTO CLICAVEL DA ABA SESSOES
  //###################################################################################

  function obterElementoClicavelSessoesTab_v3(alvo) {
    if (!alvo || typeof alvo.closest !== "function") {
      return null;
    }

    return alvo.closest(
      [
        'a[href*="admin_tab=sessoes"]',
        'a[href*="admin_tab=sess%C3%B5es"]',
        'a[href*="admin_tab=sessões"]',
        "button",
        '[role="tab"]',
        "[data-admin-tab]",
        "[data-tab]",
        ".admin-tab",
        ".tab"
      ].join(", ")
    );
  }

  function elementoRepresentaSessoesTab_v3(elemento) {
    if (!elemento) {
      return false;
    }

    var href = elemento.getAttribute("href") || "";
    var dataAdminTab = elemento.getAttribute("data-admin-tab") || "";
    var dataTab = elemento.getAttribute("data-tab") || "";
    var ariaControls = elemento.getAttribute("aria-controls") || "";
    var id = elemento.getAttribute("id") || "";
    var classes = elemento.getAttribute("class") || "";
    var texto = normalizarTextoSessoesTab_v3(elemento.textContent || elemento.innerText || "");

    var combinado = normalizarTextoSessoesTab_v3(
      [href, dataAdminTab, dataTab, ariaControls, id, classes, texto].join(" ")
    );

    return (
      combinado.indexOf("admin_tab=sessoes") >= 0 ||
      combinado.indexOf("admin_tab=sessoes") >= 0 ||
      combinado.indexOf("sidebar_section") >= 0 ||
      combinado.indexOf("sessoes") >= 0 ||
      texto === "sessoes"
    );
  }

  //###################################################################################
  // (7) MONTAR URL FINAL DA ABA SESSOES
  //###################################################################################

  function montarUrlSessoesTab_v3(elemento) {
    var href = elemento && elemento.getAttribute ? elemento.getAttribute("href") : "";
    var url;

    if (href && href !== "#" && href.toLowerCase().indexOf("javascript:") !== 0) {
      url = criarUrlSessoesTab_v3(href);
    } else {
      url = criarUrlSessoesTab_v3(window.location.href);
    }

    if (!url.pathname || url.pathname === "/") {
      url.pathname = "/users/new";
    }

    if (!url.searchParams.get("menu")) {
      url.searchParams.set("menu", "administrativo");
    }

    url.searchParams.set("admin_tab", "sessoes");

    return url;
  }

  //###################################################################################
  // (8) IGNORAR CLIQUES ESPECIAIS
  //###################################################################################

  function deveIgnorarCliqueSessoesTab_v3(evento) {
    return (
      evento.defaultPrevented ||
      evento.button !== 0 ||
      evento.metaKey ||
      evento.ctrlKey ||
      evento.shiftKey ||
      evento.altKey
    );
  }

  //###################################################################################
  // (9) TRATAR CLIQUE DA ABA SESSOES COM NAVEGACAO REAL
  //###################################################################################

  function navegarParaSessoesTab_v3(destino) {
    if (navegacaoEmCurso) {
      return;
    }

    navegacaoEmCurso = true;

    var destinoTexto = destino.toString();

    if (window.location.href === destinoTexto) {
      if (!conteudoSessoesEstaRenderizado_v3()) {
        window.location.reload();
      }
      return;
    }

    window.location.assign(destinoTexto);
  }

  function tratarCliqueAbaSessoes_v3(evento) {
    if (deveIgnorarCliqueSessoesTab_v3(evento)) {
      return;
    }

    var elemento = obterElementoClicavelSessoesTab_v3(evento.target);

    if (!elementoRepresentaSessoesTab_v3(elemento)) {
      return;
    }

    var destino = montarUrlSessoesTab_v3(elemento);

    evento.preventDefault();
    evento.stopPropagation();

    if (typeof evento.stopImmediatePropagation === "function") {
      evento.stopImmediatePropagation();
    }

    navegarParaSessoesTab_v3(destino);
  }

  //###################################################################################
  // (10) INTERCEPTAR HISTORY API QUANDO OUTRO SCRIPT MUDA A URL SEM RELOAD
  //###################################################################################

  function instalarInterceptadorHistorySessoes_v3() {
    var pushStateOriginal = window.history.pushState;
    var replaceStateOriginal = window.history.replaceState;

    window.history.pushState = function () {
      var retorno = pushStateOriginal.apply(window.history, arguments);
      recarregarSeSessoesFicouVazio_v3("pushState");
      return retorno;
    };

    window.history.replaceState = function () {
      var retorno = replaceStateOriginal.apply(window.history, arguments);
      recarregarSeSessoesFicouVazio_v3("replaceState");
      return retorno;
    };

    window.addEventListener("popstate", function () {
      recarregarSeSessoesFicouVazio_v3("popstate");
    });
  }

  //###################################################################################
  // (11) ATIVAR CORRECAO
  //###################################################################################

  window.addEventListener("click", tratarCliqueAbaSessoes_v3, true);
  document.addEventListener("click", tratarCliqueAbaSessoes_v3, true);

  instalarInterceptadorHistorySessoes_v3();

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      recarregarSeSessoesFicouVazio_v3("DOMContentLoaded");
    });
  } else {
    recarregarSeSessoesFicouVazio_v3("readyState");
  }

  window.addEventListener("load", function () {
    recarregarSeSessoesFicouVazio_v3("load");
  });
})();
