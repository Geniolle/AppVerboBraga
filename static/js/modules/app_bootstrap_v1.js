//###################################################################################
// APPGENESIS - APP BOOTSTRAP V1
// Le os dados iniciais da pagina do bloco JSON #appgenesis-bootstrap (gerado pelo
// template com tojson, que escapa <, > e &). Substitui o JS inline anterior.
//###################################################################################

(function (window, document) {
  "use strict";

  var dados = {};
  var bloco = document.getElementById("appgenesis-bootstrap");

  if (bloco) {
    try {
      dados = JSON.parse(bloco.textContent || "{}");
    } catch (error) {
      dados = {};
    }
  }

  window.__APPGENESIS_BOOTSTRAP__ = dados;
})(window, document);
