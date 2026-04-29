from pathlib import Path

ROOT = Path.cwd()

# ###################################################################################
# (1) CAMINHOS DOS FICHEIROS
# ###################################################################################

MENU_SETTINGS_PATH = ROOT / "appverbo" / "menu_settings.py"
SETTINGS_HANDLERS_PATH = ROOT / "appverbo" / "routes" / "profile" / "settings_handlers.py"
PROCESS_LISTS_RUNTIME_PATH = ROOT / "static" / "js" / "modules" / "process_lists_runtime_v5.js"

# ###################################################################################
# (2) CORRIGIR REDIRECT DA ABA CAMPOS SUBSEQUENTES
# ###################################################################################

settings_handlers_content = SETTINGS_HANDLERS_PATH.read_text(encoding="utf-8")

settings_handlers_content = settings_handlers_content.replace(
    'settings_tab="campos-subsequentes"',
    'settings_tab="campos_subsequentes"'
)

SETTINGS_HANDLERS_PATH.write_text(settings_handlers_content, encoding="utf-8")

# ###################################################################################
# (3) CORRIGIR VALOR PADRÃO DA CONDIÇÃO NO JAVASCRIPT
# ###################################################################################

if PROCESS_LISTS_RUNTIME_PATH.exists():
    runtime_content = PROCESS_LISTS_RUNTIME_PATH.read_text(encoding="utf-8")

    runtime_content = runtime_content.replace(
        'operatorSelect.value = "equals";',
        'operatorSelect.value = "is_empty";'
    )

    PROCESS_LISTS_RUNTIME_PATH.write_text(runtime_content, encoding="utf-8")

# ###################################################################################
# (4) REESCREVER NORMALIZAÇÃO DOS CAMPOS SUBSEQUENTES
# ###################################################################################

menu_settings_content = MENU_SETTINGS_PATH.read_text(encoding="utf-8")

patch_marker = "# (CAMPOS SUBSEQUENTES V3) NORMALIZAR E GRAVAR CAMPOS SUBSEQUENTES"

patch_content = r'''

####################################################################################
# (CAMPOS SUBSEQUENTES V3) NORMALIZAR E GRAVAR CAMPOS SUBSEQUENTES
####################################################################################

def _normalize_subsequent_field_operator_v3(raw_operator: Any) -> str:
    clean_operator = str(raw_operator or "").strip().lower()
    clean_operator = clean_operator.replace("-", "_")
    clean_operator = clean_operator.replace(" ", "_")

    operator_aliases = {
        "": "is_empty",

        "vazio": "is_empty",
        "empty": "is_empty",
        "blank": "is_empty",
        "is_empty": "is_empty",
        "esta_vazio": "is_empty",

        "preenchido": "is_not_empty",
        "not_empty": "is_not_empty",
        "filled": "is_not_empty",
        "is_filled": "is_not_empty",
        "is_not_empty": "is_not_empty",
        "esta_preenchido": "is_not_empty",

        "igual": "equals",
        "igual_a": "equals",
        "equals": "equals",
        "equal": "equals",
        "eq": "equals",

        "diferente": "not_equals",
        "diferente_de": "not_equals",
        "not_equal": "not_equals",
        "not_equals": "not_equals",
        "neq": "not_equals",
    }

    return operator_aliases.get(clean_operator, "is_empty")


def _build_subsequent_field_key_v3(
    trigger_field_key: str,
    subsequent_field_key: str,
    operator: str,
    trigger_value: str,
) -> str:
    base_key = "_".join(
        [
            str(trigger_field_key or "").strip().lower(),
            str(subsequent_field_key or "").strip().lower(),
            str(operator or "").strip().lower(),
            str(trigger_value or "").strip().lower(),
        ]
    )
    base_key = re.sub(r"[^a-z0-9_]+", "_", base_key)
    base_key = re.sub(r"_+", "_", base_key).strip("_")

    if not base_key:
        return ""

    return f"subseq_{base_key}"


def normalize_menu_process_subsequent_fields(raw_fields: Any) -> list[dict[str, str]]:
    if not isinstance(raw_fields, (list, tuple)):
        return []

    allowed_operators = {
        "is_empty",
        "is_not_empty",
        "equals",
        "not_equals",
    }

    normalized_fields: list[dict[str, str]] = []
    seen_fields: set[tuple[str, str, str, str]] = set()

    for raw_field in raw_fields:
        if not isinstance(raw_field, dict):
            continue

        trigger_field_key = _normalize_menu_key(
            raw_field.get("trigger_field")
            or raw_field.get("trigger_field_key")
            or raw_field.get("triggerField")
            or raw_field.get("triggerFieldKey")
            or raw_field.get("campo_acionador")
            or raw_field.get("campoAcionador")
        )

        subsequent_field_key = _normalize_menu_key(
            raw_field.get("field_key")
            or raw_field.get("subsequent_field")
            or raw_field.get("subsequent_field_key")
            or raw_field.get("subsequentField")
            or raw_field.get("subsequentFieldKey")
            or raw_field.get("target_field_key")
            or raw_field.get("targetFieldKey")
            or raw_field.get("campo_subsequente")
            or raw_field.get("campoSubsequente")
        )

        operator = _normalize_subsequent_field_operator_v3(
            raw_field.get("operator")
            or raw_field.get("condition")
            or raw_field.get("condicao")
            or raw_field.get("condição")
        )

        trigger_value = str(
            raw_field.get("trigger_value")
            or raw_field.get("triggerValue")
            or raw_field.get("value")
            or raw_field.get("valor_acionador")
            or raw_field.get("valorAcionador")
            or ""
        ).strip()

        if operator not in allowed_operators:
            operator = "is_empty"

        if operator in {"is_empty", "is_not_empty"}:
            trigger_value = ""

        if operator in {"equals", "not_equals"} and not trigger_value:
            operator = "is_empty"
            trigger_value = ""

        if not trigger_field_key or not subsequent_field_key:
            continue

        clean_key = _normalize_menu_key(
            raw_field.get("key")
            or raw_field.get("subsequent_field_key")
            or raw_field.get("id")
        )

        if not clean_key:
            clean_key = _build_subsequent_field_key_v3(
                trigger_field_key,
                subsequent_field_key,
                operator,
                trigger_value,
            )

        field_signature = (
            trigger_field_key,
            subsequent_field_key,
            operator,
            trigger_value,
        )

        if field_signature in seen_fields:
            continue

        seen_fields.add(field_signature)

        normalized_fields.append(
            {
                "key": clean_key,
                "trigger_field": trigger_field_key,
                "trigger_field_key": trigger_field_key,
                "field_key": subsequent_field_key,
                "subsequent_field": subsequent_field_key,
                "subsequent_field_key": subsequent_field_key,
                "operator": operator,
                "condition": operator,
                "trigger_value": trigger_value,
            }
        )

    return normalized_fields
'''

if patch_marker not in menu_settings_content:
    menu_settings_content = menu_settings_content.rstrip() + "\n" + patch_content + "\n"

MENU_SETTINGS_PATH.write_text(menu_settings_content, encoding="utf-8")

print("OK: Campos Subsequentes corrigido.")
print(" - Redirect ajustado para settings_tab=campos_subsequentes")
print(" - Condição padrão ajustada para Vazio")
print(" - Normalização passa a gravar is_empty/is_not_empty/equals/not_equals")
