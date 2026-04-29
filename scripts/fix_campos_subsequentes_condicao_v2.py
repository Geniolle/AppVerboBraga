from pathlib import Path

ROOT = Path.cwd()
MENU_SETTINGS_PATH = ROOT / "appverbo" / "menu_settings.py"

content = MENU_SETTINGS_PATH.read_text(encoding="utf-8")

patch = r'''

####################################################################################
# (CAMPOS SUBSEQUENTES V2) NORMALIZAR CONDICAO DE CAMPOS SUBSEQUENTES
####################################################################################

def _normalize_subsequent_field_operator_v2(raw_operator: Any) -> str:
    clean_operator = str(raw_operator or "").strip().lower()
    clean_operator = clean_operator.replace("-", "_")
    clean_operator = clean_operator.replace(" ", "_")

    operator_aliases = {
        "": "vazio",
        "vazio": "vazio",
        "empty": "vazio",
        "blank": "vazio",
        "is_empty": "vazio",
        "esta_vazio": "vazio",

        "preenchido": "preenchido",
        "not_empty": "preenchido",
        "filled": "preenchido",
        "is_filled": "preenchido",
        "esta_preenchido": "preenchido",

        "igual": "igual",
        "igual_a": "igual",
        "equals": "igual",
        "equal": "igual",
        "eq": "igual",

        "diferente": "diferente",
        "diferente_de": "diferente",
        "not_equal": "diferente",
        "neq": "diferente",

        "contem": "contem",
        "contém": "contem",
        "contains": "contem",

        "nao_contem": "nao_contem",
        "não_contém": "nao_contem",
        "not_contains": "nao_contem",
    }

    return operator_aliases.get(clean_operator, "vazio")


####################################################################################
# (CAMPOS SUBSEQUENTES V2) NORMALIZAR LISTA DE CAMPOS SUBSEQUENTES
####################################################################################

def normalize_menu_process_subsequent_fields(raw_fields: Any) -> list[dict[str, str]]:
    if not isinstance(raw_fields, (list, tuple)):
        return []

    allowed_operators = {
        "vazio",
        "preenchido",
        "igual",
        "diferente",
        "contem",
        "nao_contem",
    }

    normalized_fields: list[dict[str, str]] = []
    seen_fields: set[tuple[str, str, str, str]] = set()

    for raw_field in raw_fields:
        if not isinstance(raw_field, dict):
            continue

        trigger_field_key = _normalize_menu_key(
            raw_field.get("trigger_field_key")
            or raw_field.get("triggerFieldKey")
            or raw_field.get("field_key")
            or raw_field.get("fieldKey")
            or raw_field.get("campo_acionador")
            or raw_field.get("campoAcionador")
        )

        subsequent_field_key = _normalize_menu_key(
            raw_field.get("subsequent_field_key")
            or raw_field.get("subsequentFieldKey")
            or raw_field.get("target_field_key")
            or raw_field.get("targetFieldKey")
            or raw_field.get("campo_subsequente")
            or raw_field.get("campoSubsequente")
        )

        operator = _normalize_subsequent_field_operator_v2(
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
            operator = "vazio"

        if operator == "igual" and not trigger_value:
            operator = "vazio"

        if operator in {"vazio", "preenchido"}:
            trigger_value = ""

        if not trigger_field_key or not subsequent_field_key:
            continue

        field_key = (
            trigger_field_key,
            subsequent_field_key,
            operator,
            trigger_value,
        )

        if field_key in seen_fields:
            continue

        seen_fields.add(field_key)

        normalized_fields.append(
            {
                "trigger_field_key": trigger_field_key,
                "subsequent_field_key": subsequent_field_key,
                "operator": operator,
                "condition": operator,
                "trigger_value": trigger_value,
            }
        )

    return normalized_fields
'''

marker = "# (CAMPOS SUBSEQUENTES V2) NORMALIZAR CONDICAO DE CAMPOS SUBSEQUENTES"

if marker not in content:
    content = content.rstrip() + "\n" + patch + "\n"

MENU_SETTINGS_PATH.write_text(content, encoding="utf-8")

print("OK: normalização de condição dos Campos Subsequentes corrigida.")
