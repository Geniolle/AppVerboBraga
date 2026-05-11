
(function () {
  function liberarTelaAppVerboV2() {
    if (!document.body) {
      return;
    }

    document.body.classList.remove("appverbo-booting");
    document.body.classList.add("appverbo-ready");
  }

  window.APPVERBO_LIBERAR_TELA_V2 = liberarTelaAppVerboV2;

  if (document.readyState === "complete" || document.readyState === "interactive") {
    window.requestAnimationFrame(liberarTelaAppVerboV2);
  } else {
    document.addEventListener("DOMContentLoaded", function () {
      window.requestAnimationFrame(liberarTelaAppVerboV2);
    }, { once: true });
  }

  window.addEventListener("load", liberarTelaAppVerboV2, { once: true });
  window.setTimeout(liberarTelaAppVerboV2, 1400);
})();
