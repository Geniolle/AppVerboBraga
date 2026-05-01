from pathlib import Path
import re
import sys

ROOT = Path.cwd()

JS_PATH = ROOT / "static" / "js" / "modules" / "process_fields_config_manager_v5.js"
TEMPLATE_PATH = ROOT / "templates" / "new_user.html"


def fail(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


if not JS_PATH.exists():
    fail(f"ficheiro nao encontrado: {JS_PATH}")

if not TEMPLATE_PATH.exists():
    fail(f"ficheiro nao encontrado: {TEMPLATE_PATH}")


####################################################################################
# (1) LER FICHEIROS
####################################################################################

js = JS_PATH.read_text(encoding="utf-8")
template = TEMPLATE_PATH.read_text(encoding="utf-8")


####################################################################################
# (2) FORÇAR LAYOUT LADO A LADO NO JS
####################################################################################

old_style = r'''.process-fields-config-editor-row-v5 {
        display: grid !important;
        grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) !important;
        gap: 12px !important;
        align-items: end !important;
        width: 100% !important;
      }

      .process-fields-config-editor-row-v5 > * {
        min-width: 0 !important;
        width: 100% !important;
      }

      .process-fields-config-editor-row-v5 .field,
      .process-fields-config-header-editor-v5 {
        display: flex !important;
        flex-direction: column !important;
        gap: 6px !important;
        width: 100% !important;
        min-width: 0 !important;
        margin: 0 !important;
      }'''

new_style = r'''.process-fields-config-editor-row-v5 {
        display: grid !important;
        grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) !important;
        column-gap: 12px !important;
        row-gap: 0 !important;
        align-items: end !important;
        width: 100% !important;
        max-width: 100% !important;
        grid-column: 1 / -1 !important;
      }

      .process-fields-config-editor-row-v5 > * {
        min-width: 0 !important;
        width: 100% !important;
        max-width: 100% !important;
        grid-column: auto !important;
      }

      .process-fields-config-editor-row-v5 .field,
      .process-fields-config-header-editor-v5 {
        display: flex !important;
        flex-direction: column !important;
        gap: 6px !important;
        width: 100% !important;
        max-width: 100% !important;
        min-width: 0 !important;
        margin: 0 !important;
        grid-column: auto !important;
      }

      .process-fields-config-editor-row-v5 .field {
        grid-column: 1 !important;
      }

      .process-fields-config-editor-row-v5 .process-fields-config-header-editor-v5 {
        grid-column: 2 !important;
      }'''

if old_style not in js:
    fail("não encontrei o bloco CSS V5 antigo para substituir.")

js = js.replace(old_style, new_style)

old_insert = '''const row = document.createElement("div");
    row.className = "process-fields-config-editor-row-v5";'''

new_insert = '''const row = document.createElement("div");
    row.className = "process-fields-config-editor-row-v5";
    row.style.display = "grid";
    row.style.gridTemplateColumns = "minmax(0, 1fr) minmax(0, 1fr)";
    row.style.columnGap = "12px";
    row.style.alignItems = "end";
    row.style.width = "100%";
    row.style.maxWidth = "100%";'''

if old_insert not in js:
    fail("não encontrei criação da row V5.")

js = js.replace(old_insert, new_insert)

old_header_insert = '''headerWrapper.className = "process-fields-config-header-editor-v5";'''

new_header_insert = '''headerWrapper.className = "process-fields-config-header-editor-v5";
    headerWrapper.style.gridColumn = "2";'''

if old_header_insert not in js:
    fail("não encontrei headerWrapper V5.")

js = js.replace(old_header_insert, new_header_insert)

old_row_append = '''row.appendChild(editorField);
    row.appendChild(headerWrapper);'''

new_row_append = '''editorField.style.gridColumn = "1";
    editorField.style.width = "100%";
    editorField.style.maxWidth = "100%";
    row.appendChild(editorField);
    row.appendChild(headerWrapper);'''

if old_row_append not in js:
    fail("não encontrei append do editor/header V5.")

js = js.replace(old_row_append, new_row_append)

JS_PATH.write_text(js, encoding="utf-8")

print("OK: process_fields_config_manager_v5.js ajustado para layout lado a lado.")


####################################################################################
# (3) ATUALIZAR CACHE BUSTER
####################################################################################

template = re.sub(
    r'process_fields_config_manager_v5\.js\?v=[^"]+',
    'process_fields_config_manager_v5.js?v=20260430-fields-config-v5a-side-by-side',
    template,
)

TEMPLATE_PATH.write_text(template, encoding="utf-8")

print("OK: cache buster atualizado no template.")
print("OK: patch_process_fields_config_manager_v5a_side_by_side concluído.")
