from pathlib import Path
import re
import sys

ROOT = Path.cwd()

TEMPLATE_PATH = ROOT / "templates" / "new_user.html"
CSS_PATH = ROOT / "static" / "css" / "modules" / "process_fields_header_alignment_v1.css"


def fail(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


####################################################################################
# (1) VALIDAR FICHEIROS
####################################################################################

if not TEMPLATE_PATH.exists():
    fail(f"ficheiro nao encontrado: {TEMPLATE_PATH}")


####################################################################################
# (2) CRIAR CSS DE ALINHAMENTO
####################################################################################

css_content = r'''/* APPVERBO_PROCESS_FIELDS_HEADER_ALIGNMENT_V1_START */

/* ###################################################################################
   CONFIGURAÇÃO DOS CAMPOS - ALINHAR NOME DO CAMPO E CABEÇALHO DO CAMPO
   ################################################################################### */

.process-fields-picker-row-v4 {
  display: grid !important;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) !important;
  gap: 12px !important;
  align-items: end !important;
  width: 100% !important;
  max-width: 100% !important;
}

.process-fields-picker-row-v4 > * {
  min-width: 0 !important;
  width: 100% !important;
}

.process-fields-picker-row-v4 .field,
.process-fields-picker-row-v4 .process-field-header-picker-v4 {
  display: flex !important;
  flex-direction: column !important;
  gap: 6px !important;
  width: 100% !important;
  min-width: 0 !important;
  margin: 0 !important;
}

.process-fields-picker-row-v4 label,
.process-field-header-picker-v4 label {
  min-height: 14px !important;
  line-height: 14px !important;
  margin: 0 !important;
}

.process-fields-picker-row-v4 select,
.process-field-header-picker-v4 select {
  width: 100% !important;
  min-width: 0 !important;
  max-width: 100% !important;
  min-height: 38px !important;
  height: 38px !important;
  box-sizing: border-box !important;
}

@media (max-width: 900px) {
  .process-fields-picker-row-v4 {
    grid-template-columns: 1fr !important;
  }
}

/* APPVERBO_PROCESS_FIELDS_HEADER_ALIGNMENT_V1_END */
'''

CSS_PATH.write_text(css_content, encoding="utf-8")

print("OK: CSS de alinhamento criado.")


####################################################################################
# (3) INCLUIR CSS NO TEMPLATE
####################################################################################

template = TEMPLATE_PATH.read_text(encoding="utf-8")

css_tag = '<link rel="stylesheet" href="/static/css/modules/process_fields_header_alignment_v1.css?v=20260430-fields-header-align-v1">'

if "process_fields_header_alignment_v1.css" not in template:
    head_block_pattern = re.compile(
        r"(?P<start>\{% block head_extra %\}[\s\S]*?)(?P<end>\n\{% endblock %\})",
        re.S,
    )

    match = head_block_pattern.search(template)

    if not match:
        fail("não encontrei o bloco head_extra em new_user.html.")

    template = (
        template[:match.end("start")]
        + "\n  "
        + css_tag
        + template[match.end("start"):]
    )

    print("OK: CSS de alinhamento incluído em new_user.html.")
else:
    template = re.sub(
        r'/static/css/modules/process_fields_header_alignment_v1\.css\?v=[^"]+',
        '/static/css/modules/process_fields_header_alignment_v1.css?v=20260430-fields-header-align-v1',
        template,
    )

    print("OK: cache buster do CSS de alinhamento atualizado.")

TEMPLATE_PATH.write_text(template, encoding="utf-8")

print("OK: new_user.html atualizado.")
print("OK: patch_process_fields_header_alignment_v1 concluído.")
