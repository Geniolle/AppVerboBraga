from pathlib import Path
import re

ROOT = Path.cwd()

# ###################################################################################
# (1) CAMINHOS
# ###################################################################################

template_path = ROOT / "templates" / "new_user.html"
group_js_path = ROOT / "static" / "js" / "modules" / "additional_fields_header_groups_v3.js"

# ###################################################################################
# (2) REESCREVER FICHEIRO JS COMPLETO
# ###################################################################################

group_js_content = '''//###################################################################################
// APPVERBOBRAGA - AGRUPAR CAMPOS ADICIONAIS EM CABEÇALHOS E CAMPOS - V3
//###################################################################################

(function () {
  "use strict";

  let isApplyingGroups_v3 = false;

  //###################################################################################
  // (1) NORMALIZAÇÃO
  //###################################################################################

  function normalizarTexto_v3(valor) {
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

  function obterFormularioCamposAdicionais_v3() {
    const formularios = Array.from(document.querySelectorAll("form"));

    return formularios.find(function (formulario) {
      const action = String(formulario.getAttribute("action") || "");

      if (action.includes("/settings/menu/process-additional-fields")) {
        return true;
      }

      const texto = normalizarTexto_v3(formulario.textContent);

      return (
        texto.includes("campos adicionais") &&
        texto.includes("nome do campo adicional") &&
        texto.includes("tipo do campo")
      );
    }) || null;
  }

  function obterContainerCampos_v3(formulario) {
    return (
      formulario.querySelector(".additional-fields-grid") ||
      formulario.querySelector(".form-grid") ||
      formulario.querySelector(".personal-grid") ||
      formulario
    );
  }

  //###################################################################################
  // (3) LOCALIZAR LINHAS DOS CAMPOS ADICIONAIS
  //###################################################################################

  function obterLinhasCamposAdicionais_v3(formulario) {
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
  // (4) IDENTIFICAR TIPO DA LINHA
  //###################################################################################

  function obterSelectTipoDaLinha_v3(linha) {
    if (!linha) {
      return null;
    }

    return (
      linha.querySelector("select[name='additional_field_type']") ||
      linha.querySelector("select[name='additional_field_type[]']") ||
      linha.querySelector(".additional-field-type-col select") ||
      Array.from(linha.querySelectorAll("select")).find(function (select) {
        const field = select.closest(".field");
        const label = field ? field.querySelector("label") : null;
        return normalizarTexto_v3(label ? label.textContent : "").includes("tipo do campo");
      }) ||
      null
    );
  }

  function linhaEhCabecalho_v3(linha) {
    const selectTipo = obterSelectTipoDaLinha_v3(linha);

    if (!selectTipo) {
      return false;
    }

    const option = selectTipo.options[selectTipo.selectedIndex];
    const valor = normalizarTexto_v3(selectTipo.value);
    const texto = normalizarTexto_v3(option ? option.textContent : "");

    return (
      valor === "header" ||
      valor.includes("cabecalho") ||
      texto.includes("cabecalho")
    );
  }

  //###################################################################################
  // (5) CSS DOS GRUPOS
  //###################################################################################

  function injetarCssGrupos_v3() {
    const styleId = "additional-fields-header-groups-style-v3";

    if (document.getElementById(styleId)) {
      return;
    }

    const style = document.createElement("style");
    style.id = styleId;

    style.textContent = [
      ".additional-fields-group-v3 {",
      "  grid-column: 1 / -1 !important;",
      "  width: 100% !important;",
      "  margin: 14px 0 10px 0 !important;",
      "}",

      ".additional-fields-group-title-v3 {",
      "  display: flex !important;",
      "  align-items: center !important;",
      "  justify-content: space-between !important;",
      "  gap: 10px !important;",
      "  padding: 10px 12px !important;",
      "  border: 1px solid #b8c8ed !important;",
      "  border-left: 5px solid #244db3 !important;",
      "  border-radius: 10px !important;",
      "  background: #eef4ff !important;",
      "  color: #0f1f3d !important;",
      "  font-size: 13px !important;",
      "  font-weight: 800 !important;",
      "}",

      ".additional-fields-group-badge-v3 {",
      "  display: inline-flex !important;",
      "  align-items: center !important;",
      "  justify-content: center !important;",
      "  min-height: 20px !important;",
      "  padding: 2px 8px !important;",
      "  border: 1px solid #b8c8ed !important;",
      "  border-radius: 999px !important;",
      "  background: #ffffff !important;",
      "  color: #244db3 !important;",
      "  font-size: 10px !important;",
      "  font-weight: 800 !important;",
      "  text-transform: uppercase !important;",
      "  white-space: nowrap !important;",
      "}",

      ".additional-fields-group-body-v3 {",
      "  display: flex !important;",
      "  flex-direction: column !important;",
      "  gap: 8px !important;",
      "  padding: 10px 0 0 0 !important;",
      "}",

      ".additional-fields-group-body-v3 > .additional-field-row-equalized {",
      "  width: 100% !important;",
      "  margin-bottom: 0 !important;",
      "}",

      ".additional-fields-group-headers-v3 .additional-field-row-equalized {",
      "  padding: 8px !important;",
      "  border: 1px solid #d7e1f5 !important;",
      "  border-radius: 10px !important;",
      "  background: #f8fbff !important;",
      "}",

      ".additional-fields-group-fields-v3 {",
      "  margin-top: 18px !important;",
      "  padding-top: 18px !important;",
      "  border-top: 2px solid #d7e1f5 !important;",
      "}",

      ".additional-fields-group-fields-v3 .additional-field-row-equalized {",
      "  padding-left: 10px !important;",
      "  border-left: 4px solid #edf3ff !important;",
      "}",

      ".additional-fields-group-headers-v3 input,",
      ".additional-fields-group-headers-v3 label {",
      "  font-weight: 800 !important;",
      "}",

      ".additional-fields-subgroup-marker-v2,",
      ".additional-field-row-is-header-v1::before {",
      "  display: none !important;",
      "  content: none !important;",
      "}",

      "@media (max-width: 900px) {",
      "  .additional-fields-group-title-v3 {",
      "    align-items: flex-start !important;",
      "    flex-direction: column !important;",
      "  }",
      "}"
    ].join("\\n");

    document.head.appendChild(style);
  }

  //###################################################################################
  // (6) CRIAR GRUPO
  //###################################################################################

  function criarGrupo_v3(classeExtra, titulo, badge) {
    const grupo = document.createElement("div");
    grupo.className = "additional-fields-group-v3 " + classeExtra;

    grupo.innerHTML = [
      '<div class="additional-fields-group-title-v3">',
      '  <span>' + titulo + '</span>',
      '  <span class="additional-fields-group-badge-v3">' + badge + '</span>',
      '</div>',
      '<div class="additional-fields-group-body-v3"></div>'
    ].join("");

    return grupo;
  }

  function obterCorpoGrupo_v3(grupo) {
    return grupo.querySelector(".additional-fields-group-body-v3");
  }

  //###################################################################################
  // (7) DESAGRUPAR PARA REAPLICAR SEM DUPLICAR
  //###################################################################################

  function desmontarGruposExistentes_v3(container) {
    const grupos = Array.from(container.querySelectorAll(".additional-fields-group-v3"));

    grupos.forEach(function (grupo) {
      const linhas = Array.from(grupo.querySelectorAll(".additional-field-row-equalized"));

      linhas.forEach(function (linha) {
        container.insertBefore(linha, grupo);
      });

      grupo.remove();
    });

    Array.from(container.querySelectorAll(".additional-fields-subgroup-marker-v2")).forEach(function (marker) {
      marker.remove();
    });
  }

  //###################################################################################
  // (8) APLICAR GRUPOS CABEÇALHO E CAMPOS
  //###################################################################################

  function aplicarGrupos_v3() {
    if (isApplyingGroups_v3) {
      return;
    }

    const formulario = obterFormularioCamposAdicionais_v3();

    if (!formulario) {
      return;
    }

    const container = obterContainerCampos_v3(formulario);

    if (!container) {
      return;
    }

    isApplyingGroups_v3 = true;

    try {
      injetarCssGrupos_v3();
      desmontarGruposExistentes_v3(container);

      const linhas = obterLinhasCamposAdicionais_v3(formulario);

      if (!linhas.length) {
        return;
      }

      const linhasCabecalho = [];
      const linhasCampos = [];

      linhas.forEach(function (linha) {
        if (linhaEhCabecalho_v3(linha)) {
          linhasCabecalho.push(linha);
        } else {
          linhasCampos.push(linha);
        }
      });

      const primeiraLinha = linhas[0];

      const grupoCabecalhos = criarGrupo_v3(
        "additional-fields-group-headers-v3",
        "Grupo Cabeçalho da aba:",
        String(linhasCabecalho.length) + " cabeçalho(s)"
      );

      const grupoCampos = criarGrupo_v3(
        "additional-fields-group-fields-v3",
        "Grupo de campos:",
        String(linhasCampos.length) + " campo(s)"
      );

      container.insertBefore(grupoCabecalhos, primeiraLinha);
      container.insertBefore(grupoCampos, primeiraLinha);

      const corpoCabecalhos = obterCorpoGrupo_v3(grupoCabecalhos);
      const corpoCampos = obterCorpoGrupo_v3(grupoCampos);

      linhasCabecalho.forEach(function (linha) {
        corpoCabecalhos.appendChild(linha);
      });

      linhasCampos.forEach(function (linha) {
        corpoCampos.appendChild(linha);
      });

      if (!linhasCabecalho.length) {
        grupoCabecalhos.style.display = "none";
      }

      if (!linhasCampos.length) {
        grupoCampos.style.display = "none";
      }
    } finally {
      isApplyingGroups_v3 = false;
    }
  }

  //###################################################################################
  // (9) OBSERVAR ALTERAÇÕES NA TELA
  //###################################################################################

  function observarAlteracoes_v3() {
    const formulario = obterFormularioCamposAdicionais_v3();

    if (!formulario || formulario.dataset.headerGroupsObserverV3 === "1") {
      return;
    }

    formulario.dataset.headerGroupsObserverV3 = "1";

    const observer = new MutationObserver(function () {
      if (isApplyingGroups_v3) {
        return;
      }

      window.requestAnimationFrame(aplicarGrupos_v3);
    });

    observer.observe(formulario, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ["value", "class"]
    });

    formulario.addEventListener("change", aplicarGrupos_v3);
    formulario.addEventListener("input", aplicarGrupos_v3);
  }

  //###################################################################################
  // (10) INICIALIZAÇÃO
  //###################################################################################

  function inicializar_v3() {
    aplicarGrupos_v3();
    observarAlteracoes_v3();

    window.setTimeout(aplicarGrupos_v3, 100);
    window.setTimeout(aplicarGrupos_v3, 400);
    window.setTimeout(aplicarGrupos_v3, 1000);
    window.setTimeout(aplicarGrupos_v3, 1800);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", inicializar_v3);
  } else {
    inicializar_v3();
  }
})();
'''

group_js_path.write_text(group_js_content, encoding="utf-8")

# ###################################################################################
# (3) REMOVER SCRIPTS ANTIGOS E INCLUIR V3 NO TEMPLATE
# ###################################################################################

template_content = template_path.read_text(encoding="utf-8")

template_content = re.sub(
    r'\\s*<script src="/static/js/modules/additional_fields_header_separators_v[12]\\.js\\?[^"]*"></script>',
    '',
    template_content
)

template_content = re.sub(
    r'\\s*<script src="/static/js/modules/additional_fields_header_groups_v3\\.js\\?[^"]*"></script>',
    '',
    template_content
)

new_script = '<script src="/static/js/modules/additional_fields_header_groups_v3.js?v=20260429-header-groups-v3"></script>'

marker = "process_lists_runtime_v5.js"
marker_index = template_content.find(marker)

if marker_index >= 0:
    script_end = template_content.find("</script>", marker_index)

    if script_end >= 0:
        script_end += len("</script>")
        template_content = template_content[:script_end] + "\\n  " + new_script + template_content[script_end:]
else:
    template_content = template_content.replace(
        "{% endblock %}",
        "  " + new_script + "\\n{% endblock %}",
        1
    )

template_content = template_content.replace("</script>\\n  <script", "</script>\n  <script")
template_path.write_text(template_content, encoding="utf-8")

print("OK: Campos adicionais agrupados em Cabeçalhos da aba e Campos.")
