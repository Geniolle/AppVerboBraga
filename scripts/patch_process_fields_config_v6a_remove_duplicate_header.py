from pathlib import Path
import re
import sys

ROOT = Path.cwd()

TEMPLATE_PATH = ROOT / "templates" / "new_user.html"
JS_PATH = ROOT / "static" / "js" / "modules" / "process_fields_config_manager_v6.js"


def fail(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


####################################################################################
# (1) VALIDAR FICHEIROS
####################################################################################

if not TEMPLATE_PATH.exists():
    fail(f"ficheiro nao encontrado: {TEMPLATE_PATH}")

if not JS_PATH.exists():
    fail(f"ficheiro nao encontrado: {JS_PATH}")


####################################################################################
# (2) LER FICHEIROS
####################################################################################

template = TEMPLATE_PATH.read_text(encoding="utf-8")
js = JS_PATH.read_text(encoding="utf-8")


####################################################################################
# (3) REMOVER BLOCO EXTRA ANTIGO NO TEMPLATE
####################################################################################

# Mantém apenas o campo oficial V6:
# data-process-fields-config-header-editor-key
#
# Remove blocos antigos gerados por tentativas anteriores:
# - data-process-fields-config-header-editor-v2/v3/v4/v5
# - data-process-field-header-picker
# - data-main-header-picker
# - data-main-header-select
# - data-configured-field-header-picker

old_header_block_patterns = [
    r'\s*<div[^>]*class="[^"]*process-fields-config-header-editor-v[2345][^"]*"[\s\S]*?</div>',
    r'\s*<div[^>]*class="[^"]*process-field-header-picker-v[123456][^"]*"[\s\S]*?</div>',
    r'\s*<div[^>]*data-process-field-header-picker[^>]*>[\s\S]*?</div>',
    r'\s*<div[^>]*data-configured-field-header-picker[^>]*>[\s\S]*?</div>',
    r'\s*<div[^>]*data-main-header-picker-v[23456][^>]*>[\s\S]*?</div>',
]

for pattern in old_header_block_patterns:
    template = re.sub(pattern, "", template, flags=re.S)

# Se por algum motivo o campo oficial V6 foi duplicado, mantém apenas a primeira ocorrência.
official_select = 'data-process-fields-config-header-editor-key'
occurrences = [m.start() for m in re.finditer(re.escape(official_select), template)]

if len(occurrences) > 1:
    first_pos = occurrences[0]

    def remove_duplicate_official_blocks(match: re.Match) -> str:
        block = match.group(0)
        block_start = match.start()

        if official_select not in block:
            return block

        if block_start <= first_pos <= match.end():
            return block

        return ""

    template = re.sub(
        r'\s*<div class="field process-fields-config-header-field-v6">[\s\S]*?</div>',
        remove_duplicate_official_blocks,
        template,
        flags=re.S,
    )

print("OK: template limpo de campos de cabeçalho duplicados.")


####################################################################################
# (4) INSERIR LIMPEZA RUNTIME NO JS V6
####################################################################################

cleanup_function = r'''
  //###################################################################################
  // (2A) LIMPAR CABEÇALHOS DUPLICADOS DE PATCHES ANTIGOS
  //###################################################################################

  function removerCabecalhosDuplicados_v6(form, elements) {
    const officialHeader = elements.headerKey;

    if (!officialHeader) {
      return;
    }

    const officialWrapper =
      officialHeader.closest(".process-fields-config-header-field-v6") ||
      officialHeader.closest(".field") ||
      officialHeader.parentElement;

    const duplicateSelectors = [
      "[data-process-fields-config-header-editor-v2]",
      "[data-process-fields-config-header-editor-v3]",
      "[data-process-fields-config-header-editor-v4]",
      "[data-process-fields-config-header-editor-v5]",
      "[data-process-field-header-picker]",
      "[data-configured-field-header-picker]",
      "[data-main-header-picker-v2]",
      "[data-main-header-picker-v3]",
      "[data-main-header-select-v4]",
      "[data-main-header-select-v5]",
      "[data-main-header-select-v6]",
      ".process-fields-config-header-editor-v2",
      ".process-fields-config-header-editor-v3",
      ".process-fields-config-header-editor-v4",
      ".process-fields-config-header-editor-v5",
      ".process-field-header-picker-v1",
      ".process-field-header-picker-v2",
      ".process-field-header-picker-v3",
      ".process-field-header-picker-v4",
      ".process-field-header-picker-v5",
      ".process-field-header-picker-v6"
    ];

    duplicateSelectors.forEach(function (selector) {
      form.querySelectorAll(selector).forEach(function (element) {
        const wrapper =
          element.closest(".process-fields-config-header-editor-v2") ||
          element.closest(".process-fields-config-header-editor-v3") ||
          element.closest(".process-fields-config-header-editor-v4") ||
          element.closest(".process-fields-config-header-editor-v5") ||
          element.closest(".process-field-header-picker-v1") ||
          element.closest(".process-field-header-picker-v2") ||
          element.closest(".process-field-header-picker-v3") ||
          element.closest(".process-field-header-picker-v4") ||
          element.closest(".process-field-header-picker-v5") ||
          element.closest(".process-field-header-picker-v6") ||
          element.closest(".field") ||
          element;

        if (wrapper && wrapper !== officialWrapper && !wrapper.contains(officialHeader)) {
          wrapper.remove();
        }
      });
    });

    const headerSelects = Array.from(
      form.querySelectorAll("select")
    ).filter(function (select) {
      if (select === officialHeader) {
        return false;
      }

      const label =
        select.closest(".field")?.querySelector("label") ||
        select.parentElement?.querySelector("label");

      return label && normalizarTexto_v6(label.textContent) === "cabecalho do campo";
    });

    headerSelects.forEach(function (select) {
      const wrapper =
        select.closest(".field") ||
        select.parentElement;

      if (wrapper && wrapper !== officialWrapper && !wrapper.contains(officialHeader)) {
        wrapper.remove();
      }
    });
  }
'''

if "function removerCabecalhosDuplicados_v6" not in js:
    insert_after = "  function elementosValidos_v6(elements) {"
    insert_index = js.find(insert_after)

    if insert_index == -1:
        fail("não encontrei ponto para inserir removerCabecalhosDuplicados_v6.")

    # inserir antes do bloco (3) OPÇÕES para manter organização
    marker = "  //###################################################################################\n  // (3) OPÇÕES"
    marker_index = js.find(marker)

    if marker_index == -1:
        fail("não encontrei marcador (3) OPÇÕES no JS V6.")

    js = js[:marker_index] + cleanup_function + "\n" + js[marker_index:]
    print("OK: função removerCabecalhosDuplicados_v6 adicionada.")
else:
    print("OK: função removerCabecalhosDuplicados_v6 já existia.")


old_init = '''    form.dataset.processFieldsConfigManagerBoundV6 = "1";

    const originalOptions = lerOpcoesOriginais_v6(elements);'''

new_init = '''    form.dataset.processFieldsConfigManagerBoundV6 = "1";

    removerCabecalhosDuplicados_v6(form, elements);

    const originalOptions = lerOpcoesOriginais_v6(elements);'''

if old_init in js:
    js = js.replace(old_init, new_init, 1)
    print("OK: limpeza de duplicados ligada na inicialização V6.")
elif "removerCabecalhosDuplicados_v6(form, elements);" in js:
    print("OK: limpeza de duplicados já estava ligada.")
else:
    fail("não encontrei ponto de inicialização para ligar a limpeza.")


####################################################################################
# (5) ATUALIZAR CACHE BUSTER
####################################################################################

template = re.sub(
    r'process_fields_config_manager_v6\.js\?v=[^"]+',
    'process_fields_config_manager_v6.js?v=20260430-fields-config-v6a-remove-duplicate-header',
    template,
)

TEMPLATE_PATH.write_text(template, encoding="utf-8")
JS_PATH.write_text(js, encoding="utf-8")

print("OK: cache buster JS V6A atualizado.")
print("OK: patch_process_fields_config_v6a_remove_duplicate_header concluído.")
