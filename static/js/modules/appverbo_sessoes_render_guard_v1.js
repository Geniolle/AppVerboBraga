/* APPVERBO_SESSOES_RENDER_GUARD_SAFE_V2_START */
/*
  Guard seguro da aba Sessoes.

  Regras:
  - Nao executa recarregamento automatico.
  - Nao executa redirecionamento automatico.
  - Nao usa intervalo recorrente.
  - Apenas marca no HTML se o conteudo da aba Sessoes foi encontrado.
*/

(function () {
  "use strict";

  function normalizarTextoSessoesRenderGuardSafe_v2(valor) {
    return String(valor || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase()
      .replace(/\s+/g, " ")
      .trim();
  }

  function obterUrlAtualSessoesRenderGuardSafe_v2() {
    try {
      return new URL(String(window.location));
    }
    catch (erro) {
      return null;
    }
  }

  function estaNaAbaSessoesRenderGuardSafe_v2() {
    var url = obterUrlAtualSessoesRenderGuardSafe_v2();

    if (!url) {
      return false;
    }

    return url.searchParams.get("admin_tab") === "sessoes";
  }

  function encontrarConteudoSessoesRenderGuardSafe_v2() {
    var seletores = [
      "#admin-subprocess-card",
      ".admin-subprocess-card-v1",
      ".admin-subprocess-table-card-v1",
      "[data-admin-subprocess-key='sessoes']",
      "[data-admin-process-key='sessoes']"
    ];

    var indice;
    var elemento;
    var textoPagina;

    for (indice = 0; indice < seletores.length; indice += 1) {
      elemento = document.querySelector(seletores[indice]);

      if (elemento) {
        return elemento;
      }
    }

    textoPagina = normalizarTextoSessoesRenderGuardSafe_v2(
      document.body ? document.body.textContent : ""
    );

    if (
      textoPagina.indexOf("sessoes ativas") >= 0 ||
      textoPagina.indexOf("sessoes inativas") >= 0 ||
      textoPagina.indexOf("criar sessao") >= 0
    ) {
      return document.body;
    }

    return null;
  }

  function marcarEstadoSessoesRenderGuardSafe_v2() {
    var conteudo;

    if (!document.documentElement) {
      return;
    }

    if (!estaNaAbaSessoesRenderGuardSafe_v2()) {
      document.documentElement.removeAttribute("data-appverbo-sessoes-sem-conteudo-v2");
      document.documentElement.removeAttribute("data-appverbo-sessoes-com-conteudo-v2");
      return;
    }

    conteudo = encontrarConteudoSessoesRenderGuardSafe_v2();

    if (conteudo) {
      document.documentElement.setAttribute("data-appverbo-sessoes-com-conteudo-v2", "1");
      document.documentElement.removeAttribute("data-appverbo-sessoes-sem-conteudo-v2");
      return;
    }

    document.documentElement.setAttribute("data-appverbo-sessoes-sem-conteudo-v2", "1");
    document.documentElement.removeAttribute("data-appverbo-sessoes-com-conteudo-v2");

    console.warn(
      "APPVERBO_SESSOES_RENDER_GUARD_SAFE_V2: aba sessoes sem conteudo renderizado. O guard nao altera a navegacao automaticamente."
    );
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", marcarEstadoSessoesRenderGuardSafe_v2, { once: true });
  }
  else {
    marcarEstadoSessoesRenderGuardSafe_v2();
  }

  window.addEventListener("load", marcarEstadoSessoesRenderGuardSafe_v2, { once: true });
})();

/* APPVERBO_SESSOES_RENDER_GUARD_SAFE_V2_END */
