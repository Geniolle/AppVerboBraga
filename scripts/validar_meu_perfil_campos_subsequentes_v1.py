from __future__ import annotations

####################################################################################
# (1) BOOTSTRAP DO PROJETO
####################################################################################

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


####################################################################################
# (2) IMPORTS
####################################################################################

import json
from typing import Any

from sqlalchemy import text

from appverbo.core import SessionLocal


####################################################################################
# (3) CONSTANTES
####################################################################################

MENU_KEY = "meu_perfil"
LEGACY_MENU_KEY = "documentos"

ALLOWED_OPERATORS = {
    "equals": "Igual a",
    "not_equals": "Diferente de",
    "is_empty": "Vazio",
    "is_not_empty": "Diferente de vazio",
}

SYSTEM_FIELD_LABELS = {
    "nome": "Nome",
    "telefone": "Telefone",
    "email": "Email",
    "pais": "País",
    "data_nascimento": "Data de nascimento",
    "whatsapp": "WhatsApp",
    "autorizacao_whatsapp": "Autorização para avisos por WhatsApp",
    "conta": "Conta",
    "estado_membro": "Estado de membro",
    "colaborador": "Colaborador",
    "entidades": "Entidades",
    "ultima_verificacao_whatsapp": "Última verificação WhatsApp",
    "detalhe_verificacao": "Detalhe da verificação",
}


####################################################################################
# (4) FUNÇÕES AUXILIARES
####################################################################################

def normalize_key(value: Any) -> str:
    return str(value or "").strip().lower()


def safe_json_loads(raw_value: Any, fallback: Any) -> Any:
    if raw_value is None:
        return fallback

    if isinstance(raw_value, (dict, list)):
        return raw_value

    clean_value = str(raw_value or "").strip()

    if not clean_value:
        return fallback

    try:
        parsed_value = json.loads(clean_value)
    except Exception:
        return fallback

    return parsed_value


def format_value(value: Any) -> str:
    clean_value = str(value or "").strip()
    return clean_value if clean_value else "-"


def get_label(field_key: str, labels_by_key: dict[str, str]) -> str:
    clean_key = normalize_key(field_key)
    return labels_by_key.get(clean_key) or clean_key or "-"


def get_operator_label(operator: str) -> str:
    clean_operator = normalize_key(operator)
    return ALLOWED_OPERATORS.get(clean_operator, clean_operator or "-")


def unique_keep_order(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()

    for raw_value in values:
        clean_value = normalize_key(raw_value)

        if not clean_value or clean_value in seen:
            continue

        seen.add(clean_value)
        result.append(clean_value)

    return result


####################################################################################
# (5) EXTRAIR CONFIGURAÇÃO DO MENU
####################################################################################

def extract_menu_config_data(menu_config: dict[str, Any]) -> dict[str, Any]:
    additional_fields_raw = menu_config.get("additional_fields", [])
    visible_fields_raw = menu_config.get("process_visible_fields", [])
    visible_rows_raw = menu_config.get("process_visible_field_rows", [])
    header_map_raw = menu_config.get("process_visible_field_header_map", {})
    process_lists_raw = menu_config.get("process_lists", [])

    if not isinstance(additional_fields_raw, list):
        additional_fields_raw = []

    if not isinstance(visible_fields_raw, list):
        visible_fields_raw = []

    if not isinstance(visible_rows_raw, list):
        visible_rows_raw = []

    if not isinstance(header_map_raw, dict):
        header_map_raw = {}

    if not isinstance(process_lists_raw, list):
        process_lists_raw = []

    labels_by_key: dict[str, str] = dict(SYSTEM_FIELD_LABELS)
    types_by_key: dict[str, str] = {}
    list_key_by_field: dict[str, str] = {}
    list_items_by_key: dict[str, list[str]] = {}
    header_keys: set[str] = set()
    created_field_keys: set[str] = set()

    for raw_list in process_lists_raw:
        if not isinstance(raw_list, dict):
            continue

        list_key = normalize_key(raw_list.get("key"))

        if not list_key:
            continue

        raw_items = raw_list.get("items", [])

        if not isinstance(raw_items, list):
            raw_items = []

        list_items_by_key[list_key] = [
            str(item or "").strip()
            for item in raw_items
            if str(item or "").strip()
        ]

    for raw_field in additional_fields_raw:
        if not isinstance(raw_field, dict):
            continue

        field_key = normalize_key(raw_field.get("key"))
        field_label = str(raw_field.get("label") or "").strip()
        field_type = normalize_key(raw_field.get("field_type") or raw_field.get("type") or "text")
        list_key = normalize_key(raw_field.get("list_key"))

        if not field_key:
            continue

        created_field_keys.add(field_key)

        if field_label:
            labels_by_key[field_key] = field_label

        types_by_key[field_key] = field_type

        if list_key:
            list_key_by_field[field_key] = list_key

        if field_type == "header":
            header_keys.add(field_key)

    visible_field_keys: list[str] = []
    header_by_field: dict[str, str] = {}

    for raw_key in visible_fields_raw:
        field_key = normalize_key(raw_key)

        if field_key:
            visible_field_keys.append(field_key)

    for raw_row in visible_rows_raw:
        if not isinstance(raw_row, dict):
            continue

        field_key = normalize_key(raw_row.get("field_key"))
        header_key = normalize_key(raw_row.get("header_key"))

        if not field_key:
            continue

        visible_field_keys.append(field_key)

        if header_key:
            header_by_field[field_key] = header_key

    for raw_field_key, raw_header_key in header_map_raw.items():
        field_key = normalize_key(raw_field_key)
        header_key = normalize_key(raw_header_key)

        if field_key and header_key:
            header_by_field[field_key] = header_key

    visible_field_keys = unique_keep_order(visible_field_keys)

    visible_or_header_keys = set(visible_field_keys) | header_keys | set(SYSTEM_FIELD_LABELS.keys())

    return {
        "labels_by_key": labels_by_key,
        "types_by_key": types_by_key,
        "list_key_by_field": list_key_by_field,
        "list_items_by_key": list_items_by_key,
        "header_keys": header_keys,
        "created_field_keys": created_field_keys,
        "visible_field_keys": visible_field_keys,
        "header_by_field": header_by_field,
        "visible_or_header_keys": visible_or_header_keys,
    }


####################################################################################
# (6) NORMALIZAR REGRAS DE CAMPOS SUBSEQUENTES
####################################################################################

def normalize_subsequent_rule(raw_rule: Any, index: int) -> dict[str, str]:
    if not isinstance(raw_rule, dict):
        return {
            "key": "",
            "trigger_field": "",
            "field_key": "",
            "operator": "",
            "trigger_value": "",
        }

    rule_key = normalize_key(raw_rule.get("key") or f"sub_{index + 1}")
    trigger_field = normalize_key(raw_rule.get("trigger_field"))
    field_key = normalize_key(raw_rule.get("field_key") or raw_rule.get("subsequent_field"))
    operator = normalize_key(raw_rule.get("operator") or raw_rule.get("condition") or "equals")
    trigger_value = str(raw_rule.get("trigger_value") or "").strip()

    if operator in {"is_empty", "is_not_empty"}:
        trigger_value = ""

    return {
        "key": rule_key,
        "trigger_field": trigger_field,
        "field_key": field_key,
        "operator": operator,
        "trigger_value": trigger_value,
    }


####################################################################################
# (7) VALIDAR REGRAS
####################################################################################

def validate_rule(
    rule: dict[str, str],
    index: int,
    config_data: dict[str, Any],
    seen_rule_keys: set[str],
    seen_rule_signatures: set[tuple[str, str, str, str]],
) -> list[str]:
    issues: list[str] = []

    rule_key = rule["key"]
    trigger_field = rule["trigger_field"]
    field_key = rule["field_key"]
    operator = rule["operator"]
    trigger_value = rule["trigger_value"]

    visible_field_keys = set(config_data["visible_field_keys"])
    visible_or_header_keys = set(config_data["visible_or_header_keys"])
    header_keys = set(config_data["header_keys"])
    labels_by_key = dict(config_data["labels_by_key"])
    types_by_key = dict(config_data["types_by_key"])
    list_key_by_field = dict(config_data["list_key_by_field"])
    list_items_by_key = dict(config_data["list_items_by_key"])

    if not rule_key:
        issues.append("regra sem key")

    if rule_key in seen_rule_keys:
        issues.append(f"key duplicada: {rule_key}")

    seen_rule_keys.add(rule_key)

    if not trigger_field:
        issues.append("campo acionador vazio")
    elif trigger_field not in visible_or_header_keys:
        issues.append(f"campo acionador inexistente na configuração: {trigger_field}")
    elif trigger_field not in visible_field_keys and trigger_field not in SYSTEM_FIELD_LABELS:
        issues.append(f"campo acionador não está visível no processo: {trigger_field}")

    if not field_key:
        issues.append("campo subsequente vazio")
    elif field_key not in visible_or_header_keys:
        issues.append(f"campo subsequente inexistente na configuração: {field_key}")

    if operator not in ALLOWED_OPERATORS:
        issues.append(f"operador inválido: {operator}")

    if operator in {"equals", "not_equals"} and not trigger_value:
        issues.append("operador exige valor acionador, mas o valor está vazio")

    if operator in {"is_empty", "is_not_empty"} and trigger_value:
        issues.append("operador de vazio não deve ter valor acionador preenchido")

    if trigger_field and field_key and trigger_field == field_key:
        issues.append("campo acionador e campo subsequente são iguais")

    signature = (trigger_field, field_key, operator, trigger_value)

    if signature in seen_rule_signatures:
        issues.append("regra duplicada com mesmo acionador, campo subsequente, operador e valor")

    seen_rule_signatures.add(signature)

    trigger_type = types_by_key.get(trigger_field, "")

    if trigger_type == "list" and operator in {"equals", "not_equals"}:
        list_key = list_key_by_field.get(trigger_field, "")
        allowed_values = list_items_by_key.get(list_key, [])

        if allowed_values and trigger_value not in allowed_values:
            issues.append(
                "valor acionador não existe na lista do campo acionador: "
                + f"{trigger_value} | lista={list_key} | valores={', '.join(allowed_values)}"
            )

    if field_key in header_keys:
        children = [
            child_key
            for child_key, header_key in config_data["header_by_field"].items()
            if header_key == field_key
        ]

        if not children:
            issues.append(f"campo subsequente é cabeçalho sem campos associados: {field_key}")

    return issues


####################################################################################
# (8) PROCESSO PRINCIPAL
####################################################################################

def main() -> None:
    with SessionLocal() as session:
        menu_row = session.execute(
            text(
                """
                SELECT id, menu_key, menu_label, menu_config
                FROM sidebar_menu_settings
                WHERE lower(trim(menu_key)) IN (:menu_key, :legacy_menu_key)
                ORDER BY CASE WHEN lower(trim(menu_key)) = :menu_key THEN 0 ELSE 1 END
                LIMIT 1
                """
            ),
            {
                "menu_key": MENU_KEY,
                "legacy_menu_key": LEGACY_MENU_KEY,
            },
        ).mappings().first()

        if menu_row is None:
            raise SystemExit("ERRO: menu Meu perfil não encontrado em sidebar_menu_settings.")

        menu_config = safe_json_loads(menu_row.get("menu_config"), {})

        if not isinstance(menu_config, dict):
            raise SystemExit("ERRO: menu_config do Meu perfil não é um JSON válido.")

        config_data = extract_menu_config_data(menu_config)

        raw_rules = menu_config.get("process_subsequent_fields", [])

        if not isinstance(raw_rules, list):
            raw_rules = []

        normalized_rules = [
            normalize_subsequent_rule(raw_rule, index)
            for index, raw_rule in enumerate(raw_rules)
        ]

        seen_rule_keys: set[str] = set()
        seen_rule_signatures: set[tuple[str, str, str, str]] = set()
        all_issues: list[dict[str, Any]] = []

        print("")
        print("===== CONFIGURAÇÃO DO MENU =====")
        print(f"Menu encontrado: {menu_row.get('menu_key')} - {menu_row.get('menu_label')}")

        print("")
        print("===== CAMPOS VISÍVEIS DISPONÍVEIS PARA REGRAS =====")
        for field_key in config_data["visible_field_keys"]:
            header_key = config_data["header_by_field"].get(field_key, "")
            header_label = get_label(header_key, config_data["labels_by_key"]) if header_key else "-"
            field_label = get_label(field_key, config_data["labels_by_key"])
            print(f"- {field_key}: {field_label} | cabeçalho={header_key or '-'} {header_label}")

        print("")
        print("===== CABEÇALHOS DISPONÍVEIS COMO ALVO =====")
        if config_data["header_keys"]:
            for header_key in sorted(config_data["header_keys"]):
                print(f"- {header_key}: {get_label(header_key, config_data['labels_by_key'])}")
        else:
            print("- Nenhum cabeçalho configurado.")

        print("")
        print("===== CONFIGURAÇÕES CRIADAS EM CAMPOS SUBSEQUENTES =====")
        if not normalized_rules:
            print("- Nenhuma regra de campo subsequente criada.")

        for index, rule in enumerate(normalized_rules):
            issues = validate_rule(
                rule,
                index,
                config_data,
                seen_rule_keys,
                seen_rule_signatures,
            )

            if issues:
                all_issues.append(
                    {
                        "rule": rule,
                        "issues": issues,
                    }
                )

            trigger_label = get_label(rule["trigger_field"], config_data["labels_by_key"])
            target_label = get_label(rule["field_key"], config_data["labels_by_key"])
            operator_label = get_operator_label(rule["operator"])

            print("")
            print(f"Regra #{index + 1}")
            print(f"- key: {format_value(rule['key'])}")
            print(f"- campo acionador: {format_value(rule['trigger_field'])} - {trigger_label}")
            print(f"- operador: {format_value(rule['operator'])} - {operator_label}")
            print(f"- valor acionador: {format_value(rule['trigger_value'])}")
            print(f"- campo subsequente/alvo: {format_value(rule['field_key'])} - {target_label}")

            if rule["field_key"] in config_data["header_keys"]:
                children = [
                    child_key
                    for child_key, header_key in config_data["header_by_field"].items()
                    if header_key == rule["field_key"]
                ]

                print(f"- alvo é cabeçalho: sim")
                print(f"- campos impactados pelo cabeçalho: {', '.join(children) if children else '-'}")
            else:
                print("- alvo é cabeçalho: não")

            if issues:
                print("- validação: ERRO/AVISO")
                for issue in issues:
                    print(f"  - {issue}")
            else:
                print("- validação: OK")

        print("")
        print("===== PROBLEMAS ENCONTRADOS =====")
        if not all_issues:
            print("- Nenhum problema encontrado nas regras de campos subsequentes.")
        else:
            for item in all_issues:
                rule = item["rule"]
                print(f"- Regra {rule.get('key') or '-'}")
                for issue in item["issues"]:
                    print(f"  - {issue}")

        print("")
        print("===== RESUMO =====")
        print(f"Regras criadas: {len(normalized_rules)}")
        print(f"Regras com problema: {len(all_issues)}")
        print("OK: validação concluída. Nenhum dado foi alterado.")


if __name__ == "__main__":
    main()
