from pathlib import Path
import re
import sys

ROOT = Path.cwd()

CSS_PATH = ROOT / "static" / "css" / "modules" / "configurable_items_manager_v1.css"
TEMPLATE_PATH = ROOT / "templates" / "new_user.html"
JS_PATH = ROOT / "static" / "js" / "modules" / "process_fields_config_manager_v5.js"


def fail(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


####################################################################################
# (1) VALIDAR FICHEIROS
####################################################################################

if not CSS_PATH.exists():
    fail(f"ficheiro nao encontrado: {CSS_PATH}")

if not TEMPLATE_PATH.exists():
    fail(f"ficheiro nao encontrado: {TEMPLATE_PATH}")

if not JS_PATH.exists():
    fail(f"ficheiro nao encontrado: {JS_PATH}")


####################################################################################
# (2) LER FICHEIROS
####################################################################################

css = CSS_PATH.read_text(encoding="utf-8")
template = TEMPLATE_PATH.read_text(encoding="utf-8")
js = JS_PATH.read_text(encoding="utf-8")


####################################################################################
# (3) APLICAR CSS CORRETO
####################################################################################

marker_start = "/* APPVERBO_PROCESS_FIELDS_CONFIG_LAYOUT_V2_START */"
marker_end = "/* APPVERBO_PROCESS_FIELDS_CONFIG_LAYOUT_V2_END */"

layout_css = r'''
/* APPVERBO_PROCESS_FIELDS_CONFIG_LAYOUT_V2_START */

/* ###################################################################################
   CONFIGURACAO DOS CAMPOS - CORRECAO DEFINITIVA DO GRID
   ################################################################################### */

/*
  Regra principal:
  - O bloco externo NAO pode ser grid de duas colunas.
  - O bloco interno .process-fields-config-editor-row-v5 e que deve ser o grid.
*/

.process-fields-config-editor-v1 {
  width: 100% !important;
  max-width: 100% !important;
}

/* Bloco externo: ocupa a largura total e nao divide os filhos em colunas */
.process-fields-config-editor-grid-v1 {
  display: block !important;
  width: 100% !important;
  max-width: 100% !important;
}

/* Bloco interno criado pelo gestor V5: aqui sim ficam as duas colunas */
.process-fields-config-editor-row-v5 {
  display: grid !important;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) !important;
  column-gap: 12px !important;
  row-gap: 0 !important;
  align-items: end !important;
  width: 100% !important;
  max-width: 100% !important;
  min-width: 0 !important;
  margin: 0 !important;
  grid-column: 1 / -1 !important;
}

/* Compatibilidade com tentativas anteriores */
.process-fields-config-editor-row-v4,
.process-fields-config-editor-row-v3,
.process-fields-config-editor-row-v2 {
  display: grid !important;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) !important;
  column-gap: 12px !important;
  row-gap: 0 !important;
  align-items: end !important;
  width: 100% !important;
  max-width: 100% !important;
  min-width: 0 !important;
}

/* Coluna 1: Nome do campo */
.process-fields-config-editor-row-v5 > .field,
.process-fields-config-editor-row-v4 > .field,
.process-fields-config-editor-row-v3 > .field,
.process-fields-config-editor-row-v2 > .field {
  grid-column: 1 !important;
  width: 100% !important;
  max-width: 100% !important;
  min-width: 0 !important;
  margin: 0 !important;
  display: flex !important;
  flex-direction: column !important;
  gap: 6px !important;
}

/* Coluna 2: Cabeçalho do campo */
.process-fields-config-editor-row-v5 > .process-fields-config-header-editor-v5,
.process-fields-config-editor-row-v4 > .process-fields-config-header-editor-v4,
.process-fields-config-editor-row-v3 > .process-fields-config-header-editor-v3,
.process-fields-config-editor-row-v2 > .process-fields-config-header-editor-v2 {
  grid-column: 2 !important;
  width: 100% !important;
  max-width: 100% !important;
  min-width: 0 !important;
  margin: 0 !important;
  display: flex !important;
  flex-direction: column !important;
  gap: 6px !important;
}

/* Labels alinhadas */
.process-fields-config-editor-row-v5 label,
.process-fields-config-editor-row-v4 label,
.process-fields-config-editor-row-v3 label,
.process-fields-config-editor-row-v2 label,
.process-fields-config-header-editor-v5 label,
.process-fields-config-header-editor-v4 label,
.process-fields-config-header-editor-v3 label,
.process-fields-config-header-editor-v2 label {
  min-height: 14px !important;
  line-height: 14px !important;
  margin: 0 !important;
  color: #334155 !important;
  font-size: 12px !important;
  font-weight: 700 !important;
  text-transform: uppercase !important;
}

/* Selects com mesma largura e altura */
.process-fields-config-editor-row-v5 select,
.process-fields-config-editor-row-v4 select,
.process-fields-config-editor-row-v3 select,
.process-fields-config-editor-row-v2 select,
.process-fields-config-header-editor-v5 select,
.process-fields-config-header-editor-v4 select,
.process-fields-config-header-editor-v3 select,
.process-fields-config-header-editor-v2 select {
  width: 100% !important;
  max-width: 100% !important;
  min-width: 0 !important;
  height: 38px !important;
  min-height: 38px !important;
  box-sizing: border-box !important;
}

/* Botões abaixo das duas colunas */
.process-fields-config-actions-v5,
.process-fields-config-actions-v4,
.process-fields-config-actions-v3,
.process-fields-config-actions-v2,
.process-fields-config-editor-v1 .form-action-row {
  display: flex !important;
  align-items: center !important;
  justify-content: flex-start !important;
  gap: 8px !important;
  width: 100% !important;
  max-width: 100% !important;
  margin-top: 12px !important;
  grid-column: 1 / -1 !important;
}

/* Garantir que Guardar e Cancelar aparecem */
.process-fields-config-editor-v1 [data-process-fields-config-submit],
.process-fields-config-editor-v1 [data-process-fields-config-cancel],
.process-fields-config-actions-v5 button,
.process-fields-config-actions-v4 button,
.process-fields-config-actions-v3 button,
.process-fields-config-actions-v2 button {
  display: inline-flex !important;
  visibility: visible !important;
}

/* Responsivo */
@media (max-width: 720px) {
  .process-fields-config-editor-row-v5,
  .process-fields-config-editor-row-v4,
  .process-fields-config-editor-row-v3,
  .process-fields-config-editor-row-v2 {
    grid-template-columns: 1fr !important;
  }

  .process-fields-config-editor-row-v5 > .field,
  .process-fields-config-editor-row-v4 > .field,
  .process-fields-config-editor-row-v3 > .field,
  .process-fields-config-editor-row-v2 > .field,
  .process-fields-config-editor-row-v5 > .process-fields-config-header-editor-v5,
  .process-fields-config-editor-row-v4 > .process-fields-config-header-editor-v4,
  .process-fields-config-editor-row-v3 > .process-fields-config-header-editor-v3,
  .process-fields-config-editor-row-v2 > .process-fields-config-header-editor-v2 {
    grid-column: 1 !important;
  }
}

/* APPVERBO_PROCESS_FIELDS_CONFIG_LAYOUT_V2_END */
'''

pattern_v2 = re.escape(marker_start) + r"[\s\S]*?" + re.escape(marker_end)

if marker_start in css:
    css = re.sub(pattern_v2, layout_css.strip(), css, count=1)
    print("OK: bloco CSS V2 existente substituido.")
else:
    css = css.rstrip() + "\n\n" + layout_css.strip() + "\n"
    print("OK: bloco CSS V2 adicionado.")

CSS_PATH.write_text(css, encoding="utf-8")


####################################################################################
# (4) AJUSTAR JS PARA NAO LIMITAR O WRAPPER A UMA COLUNA
####################################################################################

js = js.replace(
    'row.style.gridTemplateColumns = "minmax(0, 1fr) minmax(0, 1fr)";',
    'row.style.gridTemplateColumns = "minmax(0, 1fr) minmax(0, 1fr)";\n    row.style.gridColumn = "1 / -1";'
)

js = js.replace(
    'row.style.maxWidth = "100%";',
    'row.style.maxWidth = "100%";\n    row.style.minWidth = "0";'
)

js = js.replace(
    'editorField.style.gridColumn = "1";',
    'editorField.style.gridColumn = "1";\n    editorField.style.minWidth = "0";'
)

js = js.replace(
    'headerWrapper.style.gridColumn = "2";',
    'headerWrapper.style.gridColumn = "2";\n    headerWrapper.style.minWidth = "0";'
)

JS_PATH.write_text(js, encoding="utf-8")

print("OK: process_fields_config_manager_v5.js reforçado para grid interno.")


####################################################################################
# (5) ATUALIZAR CACHE BUSTERS
####################################################################################

template = re.sub(
    r'configurable_items_manager_v1\.css\?v=[^"]+',
    'configurable_items_manager_v1.css?v=20260430-process-fields-config-layout-v2',
    template,
)

template = re.sub(
    r'process_fields_config_manager_v5\.js\?v=[^"]+',
    'process_fields_config_manager_v5.js?v=20260430-fields-config-v5b-grid-fix',
    template,
)

TEMPLATE_PATH.write_text(template, encoding="utf-8")

print("OK: cache busters atualizados no template.")
print("OK: patch_process_fields_config_layout_v2 concluido.")
