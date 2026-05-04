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

SUBSEQUENT_KEYS_TO_CHECK = [
    "process_subsequent_fields",
    "subsequent_fields",
    "process_subsequent_rules",
]

OPERATOR_LABELS = {
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

def normalize_key_v1(value: Any) -> str:
    return str(value or "").strip().lower()


def safe_json_loads_v1(raw_value: Any, fallback: Any) -> Any:
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


def format_value_v1(value: Any) -> str:
    clean_value = str(value or "").strip()
    return clean_value if clean_value else "-"


def get_operator_label_v1(operator: str) -> str:
    clean_operator = normalize_key_v1(operator)
    return OPERATOR_LABELS.get(clean_operator, clean_operator or "-")


def unique_keep_order_v1(values: list[str]) -> list[str]:
    result: list[str] = []
    seen_values: set[str] = set()

    for raw_value in values:
        clean_value = normalize_key_v1(raw_value)

        if not clean_value:
            continue

        if clean_value in seen_values:
            continue

        seen_values.add(clean_value)
        result.append(clean_value)

    return result


####################################################################################
# (5) LER CAMPOS DISPONÍVEIS NA CONFIGURAÇÃO DO MEU PERFIL
####################################################################################

def extract_available_fields_v1(menu_config: dict[str, Any]) -> dict[str, Any]:
    additional_fields_raw = menu_config.get("additional_fields", [])
    visible_fields_raw = menu_config.get("process_visible_fields", [])
    visible_rows_raw = menu_config.get("process_visible_field_rows", [])
    header_map_raw = menu_config.get("process_visible_field_header_map", {})

    if not isinstance(additional_fields_raw, list):
        additional_fields_raw = []

    if not isinstance(visible_fields_raw, list):
        visible_fields_raw = []

    if not isinstance(visible_rows_raw, list):
        visible_rows_raw = []

    if not isinstance(header_map_raw, dict):
        header_map_raw = {}

    labels_by_key: dict[str, str] = dict(SYSTEM_FIELD_LABELS)
    created_field_keys: set[str] = set()
    header_keys: set[str] = set()

    for raw_field in additional_fields_raw:
        if not isinstance(raw_field, dict):
            continue

        field_key = normalize_key_v1(raw_field.get("key"))
        field_label = str(raw_field.get("label") or "").strip()
        field_type = normalize_key_v1(raw_field.get("field_type") or raw_field.get("type") or "text")

        if not field_key:
            continue

        created_field_keys.add(field_key)

        if field_label:
            labels_by_key[field_key] = field_label

        if field_type == "header":
            header_keys.add(field_key)

    visible_field_keys: list[str] = []
    header_by_field: dict[str, str] = {}

    for raw_key in visible_fields_raw:
        field_key = normalize_key_v1(raw_key)

        if field_key:
            visible_field_keys.append(field_key)

    for raw_row in visible_rows_raw:
        if not isinstance(raw_row, dict):
            continue

        field_key = normalize_key_v1(raw_row.get("field_key"))
        header_key = normalize_key_v1(raw_row.get("header_key"))

        if not field_key:
            continue

        visible_field_keys.append(field_key)

        if header_key:
            header_by_field[field_key] = header_key

    for raw_field_key, raw_header_key in header_map_raw.items():
        field_key = normalize_key_v1(raw_field_key)
        header_key = normalize_key_v1(raw_header_key)

        if field_key and header_key:
            header_by_field[field_key] = header_key

    visible_field_keys = unique_keep_order_v1(visible_field_keys)

    return {
        "labels_by_key": labels_by_key,
        "created_field_keys": created_field_keys,
        "header_keys": header_keys,
        "visible_field_keys": visible_field_keys,
        "header_by_field": header_by_field,
    }


####################################################################################
# (6) NORMALIZAR REGRAS EXISTENTES
####################################################################################

def normalize_rule_v1(raw_rule: Any, index: int) -> dict[str, str]:
    if not isinstance(raw_rule, dict):
        return {
            "key": "",
            "trigger_field": "",
            "field_key": "",
            "operator": "",
            "trigger_value": "",
        }

    rule_key = normalize_key_v1(raw_rule.get("key") or raw_rule.get("subsequent_field_key") or f"sub_{index + 1}")
    trigger_field = normalize_key_v1(raw_rule.get("trigger_field") or raw_rule.get("subsequent_trigger_field"))
    field_key = normalize_key_v1(raw_rule.get("field_key") or raw_rule.get("subsequent_field"))
    operator = normalize_key_v1(raw_rule.get("operator") or raw_rule.get("condition") or raw_rule.get("subsequent_operator") or "equals")
    trigger_value = str(raw_rule.get("trigger_value") or raw_rule.get("subsequent_trigger_value") or "").strip()

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
# (7) VALIDAR SE EXISTE CONFIGURAÇÃO DE CAMPOS SUBSEQUENTES
####################################################################################

def main_v1() -> None:
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

        menu_config = safe_json_loads_v1(menu_row.get("menu_config"), {})

        if not isinstance(menu_config, dict):
            raise SystemExit("ERRO: menu_config do Meu perfil não é um JSON válido.")

        available_fields = extract_available_fields_v1(menu_config)

        existing_subsequent_storage_keys = [
            key
            for key in SUBSEQUENT_KEYS_TO_CHECK
            if key in menu_config
        ]

        raw_rules = menu_config.get("process_subsequent_fields", [])

        if not isinstance(raw_rules, list):
            raw_rules = []

        normalized_rules = [
            normalize_rule_v1(raw_rule, index)
            for index, raw_rule in enumerate(raw_rules)
        ]

        print("")
        print("===== CAMINHO VALIDADO =====")
        print("Sistema > Administrativo > Menu > Editar processo: Meu perfil > Campos Subsequentes")

        print("")
        print("===== MENU ENCONTRADO NA BASE =====")
        print(f"id: {menu_row.get('id')}")
        print(f"menu_key: {menu_row.get('menu_key')}")
        print(f"menu_label: {menu_row.get('menu_label')}")

        print("")
        print("===== CHAVES DE CAMPOS SUBSEQUENTES NO menu_config =====")
        if existing_subsequent_storage_keys:
            for key in existing_subsequent_storage_keys:
                value = menu_config.get(key)
                value_type = type(value).__name__
                value_count = len(value) if isinstance(value, list) else "-"
                print(f"- {key}: tipo={value_type} | quantidade={value_count}")
        else:
            print("- Nenhuma chave de campos subsequentes encontrada no menu_config.")

        print("")
        print("===== RESULTADO PRINCIPAL =====")
        if normalized_rules:
            print(f"EXISTE configuração criada em Campos Subsequentes.")
            print(f"Quantidade de regras criadas: {len(normalized_rules)}")
        else:
            print("NÃO EXISTE configuração criada em Campos Subsequentes.")
            print("Quantidade de regras criadas: 0")

        print("")
        print("===== REGRAS CRIADAS =====")
        if not normalized_rules:
            print("- Nenhuma regra criada.")
        else:
            for index, rule in enumerate(normalized_rules, start=1):
                trigger_label = available_fields["labels_by_key"].get(rule["trigger_field"], rule["trigger_field"])
                field_label = available_fields["labels_by_key"].get(rule["field_key"], rule["field_key"])

                print("")
                print(f"Regra #{index}")
                print(f"- key: {format_value_v1(rule['key'])}")
                print(f"- campo acionador: {format_value_v1(rule['trigger_field'])} - {format_value_v1(trigger_label)}")
                print(f"- condição: {format_value_v1(rule['operator'])} - {get_operator_label_v1(rule['operator'])}")
                print(f"- valor acionador: {format_value_v1(rule['trigger_value'])}")
                print(f"- campo subsequente: {format_value_v1(rule['field_key'])} - {format_value_v1(field_label)}")

        print("")
        print("===== CAMPOS DISPONÍVEIS PARA CRIAR CAMPOS SUBSEQUENTES =====")
        if available_fields["visible_field_keys"]:
            for field_key in available_fields["visible_field_keys"]:
                field_label = available_fields["labels_by_key"].get(field_key, field_key)
                header_key = available_fields["header_by_field"].get(field_key, "")
                header_label = available_fields["labels_by_key"].get(header_key, header_key)
                print(
                    f"- {field_key}: {field_label} | "
                    f"cabeçalho={header_key or '-'} {header_label or ''}".rstrip()
                )
        else:
            print("- Nenhum campo visível encontrado.")

        print("")
        print("===== RESUMO =====")
        print(f"Existe Campos Subsequentes criado: {'SIM' if normalized_rules else 'NÃO'}")
        print(f"Quantidade de regras: {len(normalized_rules)}")
        print("OK: validação concluída. Nenhum dado foi alterado.")


if __name__ == "__main__":
    main_v1()
