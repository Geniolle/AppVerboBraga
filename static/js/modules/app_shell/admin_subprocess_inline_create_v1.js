// APPGENESIS_ADMIN_SUBPROCESS_INLINE_CREATE_V1_START
(function () {
  "use strict";

  //###################################################################################
  // (1) GATILHO INLINE DE CRIACAO NO CABECALHO DO CARTAO ATIVO
  // Componente reutilizavel: nao duplica logica de criacao. Para qualquer
  // subprocesso administrativo com create_toggle_in_active_header=True, apenas
  // localiza o <summary> original (ja renderizado por
  // templates/macros/admin_subprocess.html dentro do <details>
  // admin-subprocess-create-collapse-v1 do proprio subprocesso) e sintetiza um
  // clique nele -- o MESMO gatilho nativo que o card de criacao isolado usava.
  // Delegado em document (nao vinculado por elemento) porque os cartoes destes
  // subprocessos podem ser substituidos via replaceWith() apos guardar por AJAX.
  //###################################################################################

  function instalarAdminSubprocessInlineCreateV1() {
    if (window.__appgenesisAdminSubprocessInlineCreateToggleV1 === true) {
      return;
    }

    window.__appgenesisAdminSubprocessInlineCreateToggleV1 = true;

    document.addEventListener("click", function (event) {
      const button = event.target.closest("[data-admin-subprocess-inline-create]");

      if (!button) {
        return;
      }

      const subprocessKey = button.getAttribute("data-admin-subprocess-inline-create") || "";
      const summaryEl = document.querySelector(
        '[data-admin-subprocess="' + subprocessKey + '"][data-admin-subprocess-role="form"] .admin-subprocess-create-collapse-v1 > summary'
      );

      if (!summaryEl) {
        console.warn(
          "[admin_subprocess_inline_create_v1] summary original nao encontrado para o subprocesso '" + subprocessKey + "'; botao inline ignorado."
        );
        return;
      }

      summaryEl.click();
    });
  }

  //###################################################################################
  // (2) INICIAR
  //###################################################################################

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", instalarAdminSubprocessInlineCreateV1);
  }
  else {
    instalarAdminSubprocessInlineCreateV1();
  }
})();
// APPGENESIS_ADMIN_SUBPROCESS_INLINE_CREATE_V1_END
