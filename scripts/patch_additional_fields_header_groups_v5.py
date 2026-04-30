from pathlib import Path
import re

ROOT = Path.cwd()

# ###################################################################################
# (1) CAMINHOS
# ###################################################################################

template_path = ROOT / "templates" / "new_user.html"
group_js_path = ROOT / "static" / "js" / "modules" / "additional_fields_header_groups_v5.js"

# ###################################################################################
# (2) REESCREVER FICHEIRO JS COMPLETO
# ###################################################################################

group_js_content = '''//###################################################################################
// APPVERBOBRAGA - AGRUPAR CAMPOS ADICIONAIS EM CABEÇALHOS E CAMPOS - V5
//###################################################################################

(function () {
  "use strict";

  let aplicandoAgrupamento_v5 = false;

  //###################################################################################
  // (1) NORMALIZAÇÃO
  //###################################################################################

  function normalizarTexto_v5(valor) {
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

  function obterFormularioCamposAdicionais_v5() {
    const formularios = Array.from(document.querySelectorAll("form"));

    return formularios.find(function (formulario) {
      const action = String(formulario.getAttribute("action") || "");

      if (action.includes("/settings/menu/process-additional-fields")) {
        return true;
      }

      if (
        formulario.querySelector("input[name='additional_field_label']") ||
        formulario.querySelector("input[name='additional_field_label[]']") ||
        formulario.querySelector("select[name='additional_field_type']") ||
        formulario.querySelector("select[name='additional_field_type[]']")
      ) {
        return true;
      }

      const texto = normalizarTexto_v5(formulario.textContent);

      return (
        texto.includes("nome do campo adicional") &&
        texto.includes("tipo do campo") &&
        texto.includes("obrigatorio")
      );
    }) || null;
  }

  function obterContainerCampos_v5(formulario) {
    return (
      formulario.querySelector(".additional-fields-grid") ||
      formulario.querySelector(".form-grid") ||
      formulario.querySelector(".personal-grid") ||
      formulario
    );
  }

  //###################################################################################
  // (3) IDENTIFICAR ELEMENTOS
  //###################################################################################

  function obterTextoLabel_v5(elemento) {
    const label = elemento ? elemento.querySelector("label") : null;
    return normalizarTexto_v5(label ? label.textContent : "");
  }

  function elementoEhCampoNome_v5(elemento) {
    if (!elemento) {
      return false;
    }

    if (obterTextoLabel_v5(elemento).includes("nome do campo adicional")) {
      return true;
    }

    return Boolean(
      elemento.querySelector &&
      (
        elemento.querySelector("input[name='additional_field_label']") ||
        elemento.querySelector("input[name='additional_field_label[]']")
      )
    );
  }

  function elementoEhBotaoRemover_v5(elemento) {
    if (!elemento) {
      return false;
    }

    const botao = elemento.matches && elemento.matches("button")
      ? elemento
      : elemento.querySelector && elemento.querySelector("button");

    if (!botao) {
      return false;
    }

    const texto = normalizarTexto_v5(botao.textContent);
    const titulo = normalizarTexto_v5(botao.getAttribute("title"));

    return (
      texto === "x" ||
      texto === "×" ||
      titulo.includes("remover") ||
      titulo.includes("excluir") ||
      botao.classList.contains("remove-field-btn") ||
      botao.classList.contains("btn-danger")
    );
  }

  function elementoEhBotaoAdicionar_v5(elemento) {
    if (!elemento) {
      return false;
    }

    const botao = elemento.matches && elemento.matches("button")
      ? elemento
      : elemento.querySelector && elemento.querySelector("button");

    if (!botao) {
      return false;
    }

    return normalizarTexto_v5(botao.textContent) === "+";
  }

  function elementoEhAcoesFormulario_v5(elemento) {
    if (!elemento) {
      return false;
    }

    if (elemento.classList && elemento.classList.contains("form-action-row")) {
      return true;
    }

    if (elemento.classList && elemento.classList.contains("profile-edit-actions")) {
      return true;
    }

    return Boolean(elemento.querySelector && elemento.querySelector("button[type='submit']"));
  }

  //###################################################################################
  // (4) DESMONTAR AGRUPAMENTOS ANTERIORES
  //###################################################################################

  function desmontarGruposExistentes_v5(container) {
    const grupos = Array.from(
      container.querySelectorAll(
        ".additional-fields-group-v3, .additional-fields-group-v4, .additional-fields-group-v5"
      )
    );

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
  // (5) MONTAR LINHAS QUANDO A TELA AINDA ESTÁ EM GRID SOLTO
  //###################################################################################

  function montarLinhasEqualizadasSeNecessario_v5(container) {
    if (container.querySelector(".additional-field-row-equalized")) {
      return;
    }

    const filhos = Array.from(container.children);
    let indice = 0;

    while (indice < filhos.length) {
      const elementoAtual = filhos[indice];

      if (!elementoAtual || !elementoEhCampoNome_v5(elementoAtual)) {
        indice += 1;
        continue;
      }

      const elementosDaLinha = [elementoAtual];
      let proximoIndice = indice + 1;

      while (proximoIndice < filhos.length) {
        const proximoElemento = filhos[proximoIndice];

        if (!proximoElemento) {
          break;
        }

        if (elementoEhCampoNome_v5(proximoElemento)) {
          break;
        }

        if (elementoEhBotaoAdicionar_v5(proximoElemento) || elementoEhAcoesFormulario_v5(proximoElemento)) {
          break;
        }

        elementosDaLinha.push(proximoElemento);
        proximoIndice += 1;

        if (elementoEhBotaoRemover_v5(proximoElemento)) {
          break;
        }
      }

      const linha = document.createElement("div");
      linha.className = "additional-field-row-equalized additional-field-row-generated-v5";
      linha.setAttribute("data-additional-field-row", "1");

      container.insertBefore(linha, elementoAtual);

      elementosDaLinha.forEach(function (elemento) {
        linha.appendChild(elemento);
      });

      indice = proximoIndice;
    }
  }

  function obterLinhasCamposAdicionais_v5(container) {
    return Array.from(container.querySelectorAll(".additional-field-row-equalized"));
  }

  //###################################################################################
  // (6) IDENTIFICAR CABEÇALHO
  //###################################################################################

  function obterSelectTipoDaLinha_v5(linha) {
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
        return normalizarTexto_v5(label ? label.textContent : "").includes("tipo do campo");
      }) ||
      null
    );
  }

  function linhaEhCabecalho_v5(linha) {
    const selectTipo = obterSelectTipoDaLinha_v5(linha);

    if (!selectTipo) {
      return false;
    }

    const option = selectTipo.options[selectTipo.selectedIndex];
    const valor = normalizarTexto_v5(selectTipo.value);
    const texto = normalizarTexto_v5(option ? option.textContent : "");

    return (
      valor === "header" ||
      valor.includes("header") ||
      valor.includes("cabecalho") ||
      texto.includes("cabecalho")
    );
  }

  //###################################################################################
  // (7) CSS DOS DOIS GRUPOS
  //###################################################################################

  function injetarCssGrupos_v5() {
    const styleId = "additional-fields-header-groups-style-v5";

    if (document.getElementById(styleId)) {
      return;
    }

    const style = document.createElement("style");
    style.id = styleId;

    style.textContent = [
      ".additional-fields-group-v5 {",
      "  grid-column: 1 / -1 !important;",
      "  width: 100% !important;",
      "  box-sizing: border-box !important;",
      "  margin: 16px 0 18px 0 !important;",
      "  padding: 0 !important;",
      "}",

      ".additional-fields-group-title-v5 {",
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

      ".additional-fields-group-badge-v5 {",
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

      ".additional-fields-group-body-v5 {",
      "  display: flex !important;",
      "  flex-direction: column !important;",
      "  gap: 8px !important;",
      "  padding: 10px 0 0 0 !important;",
      "  width: 100% !important;",
      "}",

      ".additional-fields-group-v5 .additional-field-row-equalized {",
      "  display: grid !important;",
      "  grid-template-columns: minmax(220px, 1.6fr) minmax(180px, 1.1fr) minmax(120px, 0.8fr) minmax(120px, 0.7fr) minmax(220px, 1.3fr) auto auto auto !important;",
      "  gap: 8px !important;",
      "  align-items: end !important;",
      "  width: 100% !important;",
      "  box-sizing: border-box !important;",
      "  margin: 0 !important;",
      "}",

      ".additional-fields-group-headers-v5 {",
      "  padding-bottom: 18px !important;",
      "  border-bottom: 2px solid #d7e1f5 !important;",
      "}",

      ".additional-fields-group-headers-v5 .additional-field-row-equalized {",
      "  padding: 8px !important;",
      "  border: 1px solid #d7e1f5 !important;",
      "  border-radius: 10px !important;",
      "  background: #f8fbff !important;",
      "}",

      ".additional-fields-group-fields-v5 {",
      "  margin-top: 20px !important;",
      "}",

      ".additional-fields-group-fields-v5 .additional-field-row-equalized {",
      "  padding-left: 10px !important;",
      "  border-left: 4px solid #edf3ff !important;",
      "}",

      ".additional-fields-group-headers-v5 input,",
      ".additional-fields-group-headers-v5 label {",
      "  font-weight: 800 !important;",
      "}",

      ".additional-fields-group-v3,",
      ".additional-fields-group-v4,",
      ".additional-fields-subgroup-marker-v2,",
      ".additional-field-row-is-header-v1::before {",
      "  display: none !important;",
      "  content: none !important;",
      "}",

      "@media (max-width: 1100px) {",
      "  .additional-fields-group-v5 .additional-field-row-equalized {",
      "    grid-template-columns: 1fr !important;",
      "  }",
      "}"
    ].join("\\n");

    document.head.appendChild(style);
  }

  //###################################################################################
  // (8) CRIAR GRUPO
  //###################################################################################

  function criarGrupo_v5(classeExtra, titulo, totalTexto) {
    const grupo = document.createElement("div");
    grupo.className = "additional-fields-group-v5 " + classeExtra;

    grupo.innerHTML = [
      '<div class="additional-fields-group-title-v5">',
      '  <span>' + titulo + '</span>',
      '  <span class="additional-fields-group-badge-v5">' + totalTexto + '</span>',
      '</div>',
      '<div class="additional-fields-group-body-v5"></div>'
    ].join("");

    return grupo;
  }

  function obterCorpoGrupo_v5(grupo) {
    return grupo.querySelector(".additional-fields-group-body-v5");
  }

  //###################################################################################
  // (9) APLICAR AGRUPAMENTO
  //###################################################################################

  function aplicarAgrupamento_v5() {
    if (aplicandoAgrupamento_v5) {
      return;
    }

    const formulario = obterFormularioCamposAdicionais_v5();

    if (!formulario) {
      return;
    }

    const container = obterContainerCampos_v5(formulario);

    if (!container) {
      return;
    }

    aplicandoAgrupamento_v5 = true;

    try {
      injetarCssGrupos_v5();
      desmontarGruposExistentes_v5(container);
      montarLinhasEqualizadasSeNecessario_v5(container);

      const linhas = obterLinhasCamposAdicionais_v5(container);

      if (!linhas.length) {
        return;
      }

      const linhasCabecalho = [];
      const linhasCampos = [];

      linhas.forEach(function (linha) {
        if (linhaEhCabecalho_v5(linha)) {
          linhasCabecalho.push(linha);
        } else {
          linhasCampos.push(linha);
        }
      });

      const primeiraLinha = linhas[0];

      const grupoCabecalhos = criarGrupo_v5(
        "additional-fields-group-headers-v5",
        "Grupo Cabeçalho da aba:",
        String(linhasCabecalho.length) + " cabeçalho(s)"
      );

      const grupoCampos = criarGrupo_v5(
        "additional-fields-group-fields-v5",
        "Grupo de campos:",
        String(linhasCampos.length) + " campo(s)"
      );

      container.insertBefore(grupoCabecalhos, primeiraLinha);
      container.insertBefore(grupoCampos, primeiraLinha);

      const corpoCabecalhos = obterCorpoGrupo_v5(grupoCabecalhos);
      const corpoCampos = obterCorpoGrupo_v5(grupoCampos);

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
      aplicandoAgrupamento_v5 = false;
    }
  }

  //###################################################################################
  // (10) OBSERVAR ALTERAÇÕES
  //###################################################################################

  function observarAlteracoes_v5() {
    const formulario = obterFormularioCamposAdicionais_v5();

    if (!formulario || formulario.dataset.headerGroupsObserverV5 === "1") {
      return;
    }

    formulario.dataset.headerGroupsObserverV5 = "1";

    formulario.addEventListener("change", function () {
      window.setTimeout(aplicarAgrupamento_v5, 50);
    });

    formulario.addEventListener("input", function () {
      window.setTimeout(aplicarAgrupamento_v5, 50);
    });
  }

  //###################################################################################
  // (11) INICIALIZAÇÃO
  //###################################################################################

  function inicializar_v5() {
    aplicarAgrupamento_v5();
    observarAlteracoes_v5();

    window.setTimeout(aplicarAgrupamento_v5, 100);
    window.setTimeout(aplicarAgrupamento_v5, 400);
    window.setTimeout(aplicarAgrupamento_v5, 1000);
    window.setTimeout(aplicarAgrupamento_v5, 1800);
    window.setTimeout(aplicarAgrupamento_v5, 3000);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", inicializar_v5);
  } else {
    inicializar_v5();
  }
})();
'''

group_js_path.write_text(group_js_content, encoding="utf-8")

# ###################################################################################
# (3) TROCAR SCRIPTS ANTIGOS PELO V5 NO TEMPLATE
# ###################################################################################

template_content = template_path.read_text(encoding="utf-8")

template_content = re.sub(
    r'\\s*<script src="/static/js/modules/additional_fields_header_groups_v[345]\\.js\\?[^"]*"></script>',
    '',
    template_content
)

template_content = re.sub(
    r'\\s*<script src="/static/js/modules/additional_fields_header_separators_v[12]\\.js\\?[^"]*"></script>',
    '',
    template_content
)

new_script = '<script src="/static/js/modules/additional_fields_header_groups_v5.js?v=20260429-header-groups-v5"></script>'

marker = "process_lists_runtime_v5.js"
marker_index = template_content.find(marker)

if marker_index >= 0:
    script_end = template_content.find("</script>", marker_index)

    if script_end >= 0:
        script_end += len("</script>")
        template_content = template_content[:script_end] + "\n  " + new_script + template_content[script_end:]
else:
    template_content = template_content.replace(
        "{% endblock %}",
        "  " + new_script + "\n{% endblock %}",
        1
    )

template_path.write_text(template_content, encoding="utf-8")

print("OK: agrupamento v5 aplicado.")
