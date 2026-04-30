from pathlib import Path

ROOT = Path.cwd()

# ###################################################################################
# (1) CAMINHOS
# ###################################################################################

template_path = ROOT / "templates" / "new_user.html"
separator_js_path = ROOT / "static" / "js" / "modules" / "additional_fields_header_separators_v1.js"

# ###################################################################################
# (2) REESCREVER FICHEIRO JS COMPLETO
# ###################################################################################

separator_js_content = '''//###################################################################################
// APPVERBOBRAGA - SEPARADOR VISUAL DOS CABEÇALHOS DOS CAMPOS ADICIONAIS - V1
//###################################################################################

(function () {
  "use strict";

  //###################################################################################
  // (1) NORMALIZAÇÃO
  //###################################################################################

  function normalizarTexto_v1(valor) {
    return String(valor || "")
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\\u0300-\\u036f]/g, "")
      .replace(/\\s+/g, " ");
  }

  //###################################################################################
  // (2) LOCALIZAR FORMULÁRIO DOS CAMPOS ADICIONAIS
  //###################################################################################

  function obterFormularioCamposAdicionais_v1() {
    const formularios = Array.from(document.querySelectorAll("form"));

    return formularios.find(function (formulario) {
      const action = String(formulario.getAttribute("action") || "");

      if (action.includes("/settings/menu/process-additional-fields")) {
        return true;
      }

      const texto = normalizarTexto_v1(formulario.textContent);

      return (
        texto.includes("campos adicionais") &&
        texto.includes("nome do campo adicional") &&
        texto.includes("tipo do campo")
      );
    }) || null;
  }

  //###################################################################################
  // (3) LOCALIZAR LINHAS DOS CAMPOS ADICIONAIS
  //###################################################################################

  function obterLinhasCamposAdicionais_v1(formulario) {
    if (!formulario) {
      return [];
    }

    const linhasEqualizadas = Array.from(
      formulario.querySelectorAll(".additional-field-row-equalized")
    );

    if (linhasEqualizadas.length) {
      return linhasEqualizadas;
    }

    return Array.from(
      formulario.querySelectorAll(".process-additional-field-row, [data-additional-field-row]")
    );
  }

  //###################################################################################
  // (4) IDENTIFICAR SE A LINHA É CABEÇALHO
  //###################################################################################

  function obterSelectTipoDaLinha_v1(linha) {
    if (!linha) {
      return null;
    }

    return (
      linha.querySelector("select[name='additional_field_type']") ||
      linha.querySelector(".additional-field-type-col select") ||
      Array.from(linha.querySelectorAll("select")).find(function (select) {
        const field = select.closest(".field");
        const label = field ? field.querySelector("label") : null;
        return normalizarTexto_v1(label ? label.textContent : "").includes("tipo do campo");
      }) ||
      null
    );
  }

  function linhaEhCabecalho_v1(linha) {
    const selectTipo = obterSelectTipoDaLinha_v1(linha);

    if (!selectTipo) {
      return false;
    }

    const option = selectTipo.options[selectTipo.selectedIndex];
    const valor = normalizarTexto_v1(selectTipo.value);
    const texto = normalizarTexto_v1(option ? option.textContent : "");

    return (
      valor === "header" ||
      valor.includes("cabecalho") ||
      texto.includes("cabecalho") ||
      texto.includes("cabeçalho")
    );
  }

  //###################################################################################
  // (5) INJETAR CSS DOS SEPARADORES
  //###################################################################################

  function injetarCssSeparadores_v1() {
    const styleId = "additional-fields-header-separators-style-v1";

    if (document.getElementById(styleId)) {
      return;
    }

    const style = document.createElement("style");
    style.id = styleId;

    style.textContent = [
      ".additional-field-row-equalized.additional-field-row-is-header-v1 {",
      "  position: relative !important;",
      "  margin-top: 18px !important;",
      "  padding-top: 16px !important;",
      "  padding-bottom: 10px !important;",
      "  border-top: 2px solid #b8c8ed !important;",
      "  border-bottom: 1px solid #d7e1f5 !important;",
      "  background: linear-gradient(180deg, rgba(238, 244, 255, 0.75), rgba(255, 255, 255, 0)) !important;",
      "}",

      ".additional-field-row-equalized.additional-field-row-is-header-v1:first-of-type {",
      "  margin-top: 4px !important;",
      "}",

      ".additional-field-row-equalized.additional-field-row-is-header-v1::before {",
      "  content: 'Cabeçalho da aba' !important;",
      "  position: absolute !important;",
      "  top: -10px !important;",
      "  left: 0 !important;",
      "  display: inline-flex !important;",
      "  align-items: center !important;",
      "  height: 18px !important;",
      "  padding: 0 8px !important;",
      "  border: 1px solid #b8c8ed !important;",
      "  border-radius: 999px !important;",
      "  background: #eef4ff !important;",
      "  color: #1f4f9d !important;",
      "  font-size: 10px !important;",
      "  font-weight: 700 !important;",
      "  line-height: 1 !important;",
      "  text-transform: uppercase !important;",
      "  letter-spacing: 0.02em !important;",
      "}",

      ".additional-field-row-equalized.additional-field-row-after-header-v1 {",
      "  padding-top: 4px !important;",
      "}",

      ".additional-field-row-equalized.additional-field-row-inside-section-v1 {",
      "  border-left: 3px solid #edf3ff !important;",
      "  padding-left: 8px !important;",
      "}",

      ".additional-field-row-equalized.additional-field-row-is-header-v1 input[name='additional_field_label'],",
      ".additional-field-row-equalized.additional-field-row-is-header-v1 input[name='additional_field_label[]'],",
      ".additional-field-row-equalized.additional-field-row-is-header-v1 input {",
      "  font-weight: 700 !important;",
      "}",

      ".additional-field-row-equalized.additional-field-row-is-header-v1 label {",
      "  font-weight: 800 !important;",
      "}",

      ".additional-field-row-equalized.additional-field-row-is-header-v1 + .additional-field-row-equalized:not(.additional-field-row-is-header-v1) {",
      "  margin-top: 2px !important;",
      "}",

      "@media (max-width: 900px) {",
      "  .additional-field-row-equalized.additional-field-row-is-header-v1 {",
      "    padding-top: 18px !important;",
      "  }",
      "}"
    ].join("\\n");

    document.head.appendChild(style);
  }

  //###################################################################################
  // (6) APLICAR CLASSES NAS LINHAS
  //###################################################################################

  function limparClassesSeparadores_v1(linha) {
    linha.classList.remove(
      "additional-field-row-is-header-v1",
      "additional-field-row-after-header-v1",
      "additional-field-row-inside-section-v1"
    );
  }

  function aplicarSeparadores_v1() {
    const formulario = obterFormularioCamposAdicionais_v1();

    if (!formulario) {
      return;
    }

    injetarCssSeparadores_v1();

    const linhas = obterLinhasCamposAdicionais_v1(formulario);

    if (!linhas.length) {
      return;
    }

    let dentroDeCabecalho = false;
    let linhaAnteriorEraCabecalho = false;

    linhas.forEach(function (linha) {
      limparClassesSeparadores_v1(linha);

      const isCabecalho = linhaEhCabecalho_v1(linha);

      if (isCabecalho) {
        linha.classList.add("additional-field-row-is-header-v1");
        dentroDeCabecalho = true;
        linhaAnteriorEraCabecalho = true;
        return;
      }

      if (linhaAnteriorEraCabecalho) {
        linha.classList.add("additional-field-row-after-header-v1");
      }

      if (dentroDeCabecalho) {
        linha.classList.add("additional-field-row-inside-section-v1");
      }

      linhaAnteriorEraCabecalho = false;
    });
  }

  //###################################################################################
  // (7) OBSERVAR ALTERAÇÕES NA TELA
  //###################################################################################

  function observarAlteracoes_v1() {
    const formulario = obterFormularioCamposAdicionais_v1();

    if (!formulario || formulario.dataset.headerSeparatorsObserverV1 === "1") {
      return;
    }

    formulario.dataset.headerSeparatorsObserverV1 = "1";

    const observer = new MutationObserver(function () {
      window.requestAnimationFrame(aplicarSeparadores_v1);
    });

    observer.observe(formulario, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ["value", "class"]
    });

    formulario.addEventListener("change", aplicarSeparadores_v1);
    formulario.addEventListener("input", aplicarSeparadores_v1);
  }

  //###################################################################################
  // (8) INICIALIZAÇÃO
  //###################################################################################

  function inicializar_v1() {
    aplicarSeparadores_v1();
    observarAlteracoes_v1();

    window.setTimeout(aplicarSeparadores_v1, 100);
    window.setTimeout(aplicarSeparadores_v1, 400);
    window.setTimeout(aplicarSeparadores_v1, 1000);
    window.setTimeout(aplicarSeparadores_v1, 1800);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", inicializar_v1);
  } else {
    inicializar_v1();
  }
})();
'''

separator_js_path.write_text(separator_js_content, encoding="utf-8")

# ###################################################################################
# (3) INCLUIR SCRIPT NO TEMPLATE
# ###################################################################################

template_content = template_path.read_text(encoding="utf-8")

script_tag = '<script src="/static/js/modules/additional_fields_header_separators_v1.js?v=20260429-header-separators-v1"></script>'

if "additional_fields_header_separators_v1.js" not in template_content:
    markers = [
        "additional_fields_hierarchy_v3.js",
        "additional_fields_equal_rows.js",
        "process_lists_runtime_v5.js",
        "/static/js/new_user.js"
    ]

    inserted = False

    for marker in markers:
        marker_index = template_content.find(marker)

        if marker_index >= 0:
            script_end = template_content.find("</script>", marker_index)

            if script_end >= 0:
                script_end += len("</script>")
                template_content = (
                    template_content[:script_end]
                    + "\\n  "
                    + script_tag
                    + template_content[script_end:]
                )
                inserted = True
                break

    if not inserted:
        template_content = template_content.replace(
            "{% endblock %}",
            "  " + script_tag + "\\n{% endblock %}",
            1
        )

template_path.write_text(template_content, encoding="utf-8")

print("OK: separadores dos cabeçalhos dos campos adicionais aplicados.")
