from pathlib import Path
import re
import sys

ROOT = Path.cwd()

CSS_PATH = ROOT / "static" / "css" / "modules" / "configurable_items_manager_v1.css"
TEMPLATE_PATH = ROOT / "templates" / "new_user.html"


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


####################################################################################
# (2) LER FICHEIROS
####################################################################################

css = CSS_PATH.read_text(encoding="utf-8")
template = TEMPLATE_PATH.read_text(encoding="utf-8")


####################################################################################
# (3) APLICAR MESMA LOGICA DE GRID DOS CAMPOS ADICIONAIS
####################################################################################

marker_start = "/* APPVERBO_PROCESS_FIELDS_CONFIG_SAME_GRID_V1_START */"
marker_end = "/* APPVERBO_PROCESS_FIELDS_CONFIG_SAME_GRID_V1_END */"

grid_css = r'''
/* APPVERBO_PROCESS_FIELDS_CONFIG_SAME_GRID_V1_START */

/* ###################################################################################
   CONFIGURACAO DOS CAMPOS - MESMA LOGICA DE ALINHAMENTO DOS CAMPOS ADICIONAIS
   ################################################################################### */

/*
  Regra equivalente a:
  [data-process-additional-fields-manager-v3="1"] [data-additional-field-editor-block]

  Objetivo:
  - Nome do campo e Cabeçalho do campo lado a lado
  - selects com mesma altura/largura
  - botões abaixo dos campos
*/

.process-fields-config-editor-v1,
.process-fields-config-editor-grid-v1 {
  width: 100% !important;
  max-width: 100% !important;
}

/* Bloco original da aba Configuração dos campos */
.process-fields-config-editor-grid-v1 {
  display: grid !important;
  grid-template-columns:
    minmax(260px, 1fr)
    minmax(260px, 1fr) !important;
  gap: 12px !important;
  align-items: end !important;
}

/* Blocos criados pelas versões do gestor JS */
.process-fields-config-editor-row-v5,
.process-fields-config-editor-row-v4,
.process-fields-config-editor-row-v3,
.process-fields-config-editor-row-v2 {
  display: grid !important;
  grid-template-columns:
    minmax(260px, 1fr)
    minmax(260px, 1fr) !important;
  gap: 12px !important;
  align-items: end !important;
  width: 100% !important;
  max-width: 100% !important;
  grid-column: 1 / -1 !important;
}

/* Campos dentro do grid */
.process-fields-config-editor-grid-v1 .field,
.process-fields-config-editor-row-v5 .field,
.process-fields-config-editor-row-v4 .field,
.process-fields-config-editor-row-v3 .field,
.process-fields-config-editor-row-v2 .field {
  min-width: 0 !important;
  margin: 0 !important;
  width: 100% !important;
  max-width: 100% !important;
}

/* Nome do campo fica na primeira coluna */
.process-fields-config-editor-row-v5 > .field,
.process-fields-config-editor-row-v4 > .field,
.process-fields-config-editor-row-v3 > .field,
.process-fields-config-editor-row-v2 > .field {
  grid-column: 1 !important;
}

/* Cabeçalho do campo fica na segunda coluna */
.process-fields-config-header-editor-v5,
.process-fields-config-header-editor-v4,
.process-fields-config-header-editor-v3,
.process-fields-config-header-editor-v2,
.process-field-header-picker-v6,
.process-field-header-picker-v5,
.process-field-header-picker-v4,
.process-field-header-picker-v3,
.process-field-header-picker-v2,
.process-field-header-picker-v1 {
  grid-column: 2 !important;
  min-width: 0 !important;
  margin: 0 !important;
  width: 100% !important;
  max-width: 100% !important;
  display: flex !important;
  flex-direction: column !important;
  gap: 6px !important;
}

/* Labels com o mesmo comportamento visual dos campos adicionais */
.process-fields-config-editor-grid-v1 label,
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

/* Selects iguais: largura total e mesma altura */
.process-fields-config-editor-grid-v1 select,
.process-fields-config-editor-row-v5 select,
.process-fields-config-editor-row-v4 select,
.process-fields-config-editor-row-v3 select,
.process-fields-config-editor-row-v2 select,
.process-fields-config-header-editor-v5 select,
.process-fields-config-header-editor-v4 select,
.process-fields-config-header-editor-v3 select,
.process-fields-config-header-editor-v2 select {
  width: 100% !important;
  min-width: 0 !important;
  max-width: 100% !important;
  min-height: 38px !important;
  height: 38px !important;
  box-sizing: border-box !important;
}

/* Botões Guardar / Cancelar sempre abaixo das duas colunas */
.process-fields-config-actions-v5,
.process-fields-config-actions-v4,
.process-fields-config-actions-v3,
.process-fields-config-actions-v2,
.process-fields-config-editor-grid-v1 .form-action-row,
.process-fields-config-editor-v1 .form-action-row {
  grid-column: 1 / -1 !important;
  display: flex !important;
  align-items: center !important;
  justify-content: flex-start !important;
  gap: 8px !important;
  width: 100% !important;
  margin-top: 4px !important;
}

/* Garantir que botões não ficam escondidos */
.process-fields-config-editor-v1 [data-process-fields-config-submit],
.process-fields-config-editor-v1 [data-process-fields-config-cancel],
.process-fields-config-actions-v5 button,
.process-fields-config-actions-v4 button,
.process-fields-config-actions-v3 button,
.process-fields-config-actions-v2 button {
  display: inline-flex !important;
  visibility: visible !important;
}

/* Mesma lógica responsiva dos campos adicionais */
@media (max-width: 1180px) {
  .process-fields-config-editor-grid-v1,
  .process-fields-config-editor-row-v5,
  .process-fields-config-editor-row-v4,
  .process-fields-config-editor-row-v3,
  .process-fields-config-editor-row-v2 {
    grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
  }
}

@media (max-width: 720px) {
  .process-fields-config-editor-grid-v1,
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
  .process-fields-config-header-editor-v5,
  .process-fields-config-header-editor-v4,
  .process-fields-config-header-editor-v3,
  .process-fields-config-header-editor-v2,
  .process-field-header-picker-v6,
  .process-field-header-picker-v5,
  .process-field-header-picker-v4,
  .process-field-header-picker-v3,
  .process-field-header-picker-v2,
  .process-field-header-picker-v1 {
    grid-column: 1 !important;
  }
}

/* APPVERBO_PROCESS_FIELDS_CONFIG_SAME_GRID_V1_END */
'''

pattern = re.escape(marker_start) + r"[\s\S]*?" + re.escape(marker_end)

if marker_start in css:
    css = re.sub(pattern, grid_css.strip(), css, count=1)
    print("OK: bloco CSS de alinhamento existente substituido.")
else:
    css = css.rstrip() + "\n\n" + grid_css.strip() + "\n"
    print("OK: bloco CSS de alinhamento adicionado.")

CSS_PATH.write_text(css, encoding="utf-8")


####################################################################################
# (4) ATUALIZAR CACHE BUSTER DO CSS DO MODULO
####################################################################################

template = re.sub(
    r'configurable_items_manager_v1\.css\?v=[^"]+',
    'configurable_items_manager_v1.css?v=20260430-fields-config-same-grid-v1',
    template,
)

TEMPLATE_PATH.write_text(template, encoding="utf-8")

print("OK: cache buster do configurable_items_manager_v1.css atualizado.")
print("OK: patch_process_fields_config_same_grid_v1 concluido.")
