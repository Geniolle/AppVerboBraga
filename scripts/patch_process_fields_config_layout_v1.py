from pathlib import Path
import re
import sys

ROOT = Path.cwd()

CSS_PATH = ROOT / "static" / "css" / "new_user.css"
TEMPLATE_PATH = ROOT / "templates" / "new_user.html"


def fail(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


if not CSS_PATH.exists():
    fail(f"ficheiro nao encontrado: {CSS_PATH}")

if not TEMPLATE_PATH.exists():
    fail(f"ficheiro nao encontrado: {TEMPLATE_PATH}")


####################################################################################
# (1) LER FICHEIROS
####################################################################################

css = CSS_PATH.read_text(encoding="utf-8")
template = TEMPLATE_PATH.read_text(encoding="utf-8")


####################################################################################
# (2) APLICAR CSS DEFINITIVO PARA CONFIGURAÇÃO DOS CAMPOS
####################################################################################

marker_start = "/* APPVERBO_PROCESS_FIELDS_CONFIG_LAYOUT_V1_START */"
marker_end = "/* APPVERBO_PROCESS_FIELDS_CONFIG_LAYOUT_V1_END */"

layout_css = r'''
/* APPVERBO_PROCESS_FIELDS_CONFIG_LAYOUT_V1_START */

/* ###################################################################################
   ADMINISTRATIVO > MENU > CONFIGURAÇÃO DOS CAMPOS
   Nome do campo e Cabeçalho do campo lado a lado
   ################################################################################### */

.process-fields-config-editor-v1,
.process-fields-config-editor-grid-v1 {
  width: 100% !important;
  max-width: 100% !important;
}

/* O bloco gerado pelo gestor JS deve ser sempre 2 colunas */
.process-fields-config-editor-row-v5,
.process-fields-config-editor-row-v4,
.process-fields-config-editor-row-v3,
.process-fields-config-editor-row-v2 {
  display: grid !important;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) !important;
  gap: 12px !important;
  align-items: end !important;
  width: 100% !important;
  max-width: 100% !important;
  grid-column: 1 / -1 !important;
}

/* Cada coluna ocupa somente a sua metade */
.process-fields-config-editor-row-v5 > *,
.process-fields-config-editor-row-v4 > *,
.process-fields-config-editor-row-v3 > *,
.process-fields-config-editor-row-v2 > * {
  min-width: 0 !important;
  width: 100% !important;
  max-width: 100% !important;
}

/* Coluna 1: Nome do campo */
.process-fields-config-editor-row-v5 > .field,
.process-fields-config-editor-row-v4 > .field,
.process-fields-config-editor-row-v3 > .field,
.process-fields-config-editor-row-v2 > .field {
  grid-column: 1 !important;
  display: flex !important;
  flex-direction: column !important;
  gap: 6px !important;
  margin: 0 !important;
}

/* Coluna 2: Cabeçalho do campo */
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
  display: flex !important;
  flex-direction: column !important;
  gap: 6px !important;
  width: 100% !important;
  max-width: 100% !important;
  min-width: 0 !important;
  margin: 0 !important;
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
  font-size: 11px !important;
  font-weight: 700 !important;
  text-transform: uppercase !important;
}

/* Selects com a mesma altura e largura */
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
  height: 38px !important;
  min-height: 38px !important;
  box-sizing: border-box !important;
}

/* Botões sempre abaixo das duas colunas */
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
  margin-top: 12px !important;
  grid-column: 1 / -1 !important;
}

/* Evita que qualquer regra global esconda os botões */
.process-fields-config-actions-v5 button,
.process-fields-config-actions-v4 button,
.process-fields-config-actions-v3 button,
.process-fields-config-actions-v2 button,
.process-fields-config-editor-v1 [data-process-fields-config-submit],
.process-fields-config-editor-v1 [data-process-fields-config-cancel] {
  display: inline-flex !important;
  visibility: visible !important;
}

/* Em ecrãs pequenos volta para uma coluna */
@media (max-width: 900px) {
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
  .process-fields-config-header-editor-v2 {
    grid-column: 1 !important;
  }
}

/* APPVERBO_PROCESS_FIELDS_CONFIG_LAYOUT_V1_END */
'''

pattern = re.escape(marker_start) + r"[\s\S]*?" + re.escape(marker_end)

if marker_start in css:
    css = re.sub(pattern, layout_css.strip(), css, count=1)
    print("OK: bloco CSS existente substituido.")
else:
    css = css.rstrip() + "\n\n" + layout_css.strip() + "\n"
    print("OK: bloco CSS adicionado.")

CSS_PATH.write_text(css, encoding="utf-8")


####################################################################################
# (3) ATUALIZAR CACHE BUSTER DO new_user.css
####################################################################################

template = re.sub(
    r'new_user\.css\?v=[^"]+',
    'new_user.css?v=20260430-process-fields-config-layout-v1',
    template,
)

TEMPLATE_PATH.write_text(template, encoding="utf-8")

print("OK: cache buster do new_user.css atualizado.")
print("OK: patch_process_fields_config_layout_v1 concluido.")
