from __future__ import annotations

####################################################################################
# (1) BOOTSTRAP DO PROJETO
####################################################################################

from pathlib import Path
import json
import sys
import unicodedata
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


####################################################################################
# (2) IMPORTS DO PROJETO
####################################################################################

from sqlalchemy import text

from appgenesis.core import SessionLocal


####################################################################################
# (3) CONSTANTES DA VALIDAÇÃO
####################################################################################

MENU_KEY = "meu_perfil"
LEGACY_MENU_KEY = "documentos"

TRIGGER_FIELD = "custom_estado_civil"
TARGET_FIELD = "custom_nome_do_conjuge"

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
# (4) FUNÇÕES AUXILIARES V2
####################################################################################

def normalize_key_v2(value: Any) -> str:
    return str(value or "").strip().lower()


def normalize_lookup_text_v2(value: Any) -> str:
    clean_value = str(value or "").strip().lower()

    if not clean_value:
        return ""

    normalized_value = unicodedata.normalize("NFD", clean_value)

    return "".join(
        char
        for char in normalized_value
        if unicodedata.category(char) != "Mn"
    )


def safe_json_loads_v2(raw_value: Any, fallback: Any) -> Any:
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


def format_value_v2(value: Any) -> str:
    clean_value = str(value or "").strip()
    return clean_value if clean_value else "-"


def get_operator_label_v2(operator: str) -> str:
    clean_operator = normalize_key_v2(operator)
    return OPERATOR_LABELS.get(clean_operator, clean_operator or "-")


def is_rule_met_v2(operator: str, current_value: Any, trigger_value: Any) -> bool:
    clean_operator = normalize_key_v2(operator)

    current_text = str(current_value or "").strip()
    trigger_text = str(trigger_value or "").strip()

    normalized_current = normalize_lookup_text_v2(current_text)
    normalized_trigger = normalize_lookup_text_v2(trigger_text)

    if clean_operator == "is_empty":
        return current_text == ""

    if clean_operator == "is_not_empty":
        return current_text != ""

    if clean_operator == "not_equals":
        return normalized_current != normalized_trigger

    return normalized_current == normalized_trigger


####################################################################################
# (5) EXTRAIR CAMPOS E REGRAS DO MENU V2
####################################################################################

def extract_field_metadata_v2(menu_config: dict[str, Any]) -> dict[str, Any]:
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
    required_by_key: dict[str, bool] = {}
    type_by_key: dict[str, str] = {}
    header_by_field: dict[str, str] = {}
    header_keys: set[str] = set()

    for raw_field in additional_fields_raw:
        if not isinstance(raw_field, dict):
            continue

        field_key = normalize_key_v2(raw_field.get("key"))
        field_label = str(raw_field.get("label") or "").strip()
        field_type = normalize_key_v2(raw_field.get("field_type") or raw_field.get("type") or "text")
        is_required_raw = normalize_key_v2(raw_field.get("is_required"))

        if not field_key:
            continue

        if field_label:
            labels_by_key[field_key] = field_label

        type_by_key[field_key] = field_type
        required_by_key[field_key] = is_required_raw in {"1", "true", "sim", "yes", "on", "required"}

        if field_type == "header":
            header_keys.add(field_key)

    visible_field_keys: list[str] = []
    seen_visible: set[str] = set()

    for raw_key in visible_fields_raw:
        field_key = normalize_key_v2(raw_key)

        if field_key and field_key not in seen_visible:
            seen_visible.add(field_key)
            visible_field_keys.append(field_key)

    for raw_row in visible_rows_raw:
        if not isinstance(raw_row, dict):
            continue

        field_key = normalize_key_v2(raw_row.get("field_key"))
        header_key = normalize_key_v2(raw_row.get("header_key"))

        if field_key and field_key not in seen_visible:
            seen_visible.add(field_key)
            visible_field_keys.append(field_key)

        if field_key and header_key:
            header_by_field[field_key] = header_key

    for raw_field_key, raw_header_key in header_map_raw.items():
        field_key = normalize_key_v2(raw_field_key)
        header_key = normalize_key_v2(raw_header_key)

        if field_key and header_key:
            header_by_field[field_key] = header_key

    return {
        "labels_by_key": labels_by_key,
        "required_by_key": required_by_key,
        "type_by_key": type_by_key,
        "visible_field_keys": visible_field_keys,
        "header_by_field": header_by_field,
        "header_keys": header_keys,
    }


def normalize_rule_v2(raw_rule: Any, index: int, source_key: str) -> dict[str, str]:
    if not isinstance(raw_rule, dict):
        return {
            "source_key": source_key,
            "key": f"{source_key}_{index + 1}",
            "trigger_field": "",
            "field_key": "",
            "operator": "",
            "trigger_value": "",
        }

    rule_key = normalize_key_v2(
        raw_rule.get("key")
        or raw_rule.get("subsequent_field_key")
        or raw_rule.get("id")
        or f"{source_key}_{index + 1}"
    )

    trigger_field = normalize_key_v2(
        raw_rule.get("trigger_field")
        or raw_rule.get("trigger_field_key")
        or raw_rule.get("subsequent_trigger_field")
        or raw_rule.get("triggerField")
    )

    field_key = normalize_key_v2(
        raw_rule.get("field_key")
        or raw_rule.get("subsequent_field")
        or raw_rule.get("subsequent_field_key")
        or raw_rule.get("fieldKey")
        or raw_rule.get("target_field")
    )

    operator = normalize_key_v2(
        raw_rule.get("operator")
        or raw_rule.get("condition")
        or raw_rule.get("subsequent_operator")
        or "equals"
    )

    trigger_value = str(
        raw_rule.get("trigger_value")
        or raw_rule.get("subsequent_trigger_value")
        or raw_rule.get("triggerValue")
        or ""
    ).strip()

    if operator in {"is_empty", "is_not_empty"}:
        trigger_value = ""

    return {
        "source_key": source_key,
        "key": rule_key,
        "trigger_field": trigger_field,
        "field_key": field_key,
        "operator": operator,
        "trigger_value": trigger_value,
    }


def extract_subsequent_rules_v2(menu_config: dict[str, Any]) -> list[dict[str, str]]:
    rules: list[dict[str, str]] = []

    for source_key in SUBSEQUENT_KEYS_TO_CHECK:
        raw_rules = menu_config.get(source_key)

        if not isinstance(raw_rules, list):
            continue

        for index, raw_rule in enumerate(raw_rules):
            rules.append(normalize_rule_v2(raw_rule, index, source_key))

    return rules


def find_target_rules_v2(rules: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        rule
        for rule in rules
        if rule.get("trigger_field") == TRIGGER_FIELD
        and rule.get("field_key") == TARGET_FIELD
    ]


def should_show_target_v2(rules: list[dict[str, str]], estado_civil: str) -> bool:
    if not rules:
        return False

    return any(
        is_rule_met_v2(
            rule.get("operator"),
            estado_civil,
            rule.get("trigger_value"),
        )
        for rule in rules
    )


####################################################################################
# (6) VALIDAR DADOS GRAVADOS DOS MEMBROS V2
####################################################################################

def get_custom_field_value_v2(profile_custom_fields: dict[str, Any], field_key: str) -> str:
    clean_key = normalize_key_v2(field_key)
    value = profile_custom_fields.get(clean_key, "")
    return str(value or "").strip()


def classify_member_status_v2(
    estado_civil: str,
    nome_conjuge: str,
    matched_rules: list[dict[str, str]],
    target_required: bool,
) -> tuple[str, str]:
    should_show_target = should_show_target_v2(matched_rules, estado_civil)
    has_nome_conjuge = bool(str(nome_conjuge or "").strip())

    if should_show_target and has_nome_conjuge:
        return (
            "OK_VISIVEL_COM_VALOR",
            "A configuração atual manda mostrar Nome do conjuge e existe valor gravado.",
        )

    if should_show_target and not has_nome_conjuge:
        if target_required:
            return (
                "ERRO_VISIVEL_SEM_VALOR_OBRIGATORIO",
                "A configuração atual manda mostrar Nome do conjuge, o campo é obrigatório, mas não existe valor gravado.",
            )

        return (
            "AVISO_VISIVEL_SEM_VALOR",
            "A configuração atual manda mostrar Nome do conjuge, mas não existe valor gravado. Como o campo não está marcado como obrigatório, pode estar correto.",
        )

    if not should_show_target and has_nome_conjuge:
        return (
            "ERRO_OCULTO_COM_VALOR",
            "A configuração atual manda ocultar Nome do conjuge, mas existe valor gravado.",
        )

    return (
        "OK_OCULTO_SEM_VALOR",
        "A configuração atual manda ocultar Nome do conjuge e não existe valor gravado.",
    )


####################################################################################
# (7) PROCESSO PRINCIPAL V2
####################################################################################

def main_v2() -> None:
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

        menu_config = safe_json_loads_v2(menu_row.get("menu_config"), {})

        if not isinstance(menu_config, dict):
            raise SystemExit("ERRO: menu_config do Meu perfil não é um JSON válido.")

        field_metadata = extract_field_metadata_v2(menu_config)
        all_rules = extract_subsequent_rules_v2(menu_config)
        matched_rules = find_target_rules_v2(all_rules)

        print("")
        print("===== CAMINHO VALIDADO =====")
        print("Sistema > Administrativo > Menu > Editar processo: Meu perfil > Campos Subsequentes")

        print("")
        print("===== REGRAS ATUAIS ENCONTRADAS PARA ESTADO CIVIL -> NOME DO CONJUGE =====")

        if not matched_rules:
            print("- Nenhuma regra atual encontrada para Estado civil -> Nome do conjuge.")
        else:
            for index, rule in enumerate(matched_rules, start=1):
                print("")
                print(f"Regra #{index}")
                print(f"- origem: {rule.get('source_key')}")
                print(f"- key: {rule.get('key')}")
                print(f"- campo acionador: {rule.get('trigger_field')} - {field_metadata['labels_by_key'].get(rule.get('trigger_field'), rule.get('trigger_field'))}")
                print(f"- operador: {rule.get('operator')} - {get_operator_label_v2(rule.get('operator', ''))}")
                print(f"- valor acionador: {format_value_v2(rule.get('trigger_value'))}")
                print(f"- campo subsequente: {rule.get('field_key')} - {field_metadata['labels_by_key'].get(rule.get('field_key'), rule.get('field_key'))}")

        target_required = bool(field_metadata["required_by_key"].get(TARGET_FIELD, False))

        print("")
        print("===== METADADOS DO CAMPO SUBSEQUENTE =====")
        print(f"Campo: {TARGET_FIELD} - {field_metadata['labels_by_key'].get(TARGET_FIELD, TARGET_FIELD)}")
        print(f"Tipo: {field_metadata['type_by_key'].get(TARGET_FIELD, '-')}")
        print(f"Obrigatório: {'SIM' if target_required else 'NÃO'}")
        print(f"Cabeçalho: {field_metadata['header_by_field'].get(TARGET_FIELD, '-')}")

        member_rows = session.execute(
            text(
                """
                SELECT id, full_name, email, profile_custom_fields
                FROM members
                ORDER BY id
                """
            )
        ).mappings().all()

        result_counts: dict[str, int] = {}
        validation_rows: list[dict[str, str]] = []

        for member_row in member_rows:
            profile_custom_fields = safe_json_loads_v2(member_row.get("profile_custom_fields"), {})

            if not isinstance(profile_custom_fields, dict):
                profile_custom_fields = {}

            estado_civil = get_custom_field_value_v2(profile_custom_fields, TRIGGER_FIELD)
            nome_conjuge = get_custom_field_value_v2(profile_custom_fields, TARGET_FIELD)
            should_show_target = should_show_target_v2(matched_rules, estado_civil)

            status_code, status_message = classify_member_status_v2(
                estado_civil,
                nome_conjuge,
                matched_rules,
                target_required,
            )

            result_counts[status_code] = result_counts.get(status_code, 0) + 1

            validation_rows.append(
                {
                    "member_id": str(member_row.get("id")),
                    "full_name": str(member_row.get("full_name") or ""),
                    "email": str(member_row.get("email") or ""),
                    "estado_civil": estado_civil,
                    "nome_conjuge": nome_conjuge,
                    "should_show_target": "SIM" if should_show_target else "NÃO",
                    "status_code": status_code,
                    "status_message": status_message,
                }
            )

        print("")
        print("===== VALIDAÇÃO DOS DADOS GRAVADOS =====")

        if not validation_rows:
            print("- Nenhum membro encontrado.")

        for row in validation_rows:
            print("")
            print(f"Membro #{row['member_id']}")
            print(f"- Nome: {row['full_name']}")
            print(f"- Email: {row['email']}")
            print(f"- Estado civil gravado: {format_value_v2(row['estado_civil'])}")
            print(f"- Nome do conjuge gravado: {format_value_v2(row['nome_conjuge'])}")
            print(f"- Pela configuração atual, Nome do conjuge deve aparecer? {row['should_show_target']}")
            print(f"- Resultado: {row['status_code']}")
            print(f"- Análise: {row['status_message']}")

        print("")
        print("===== RESUMO POR RESULTADO =====")

        if not result_counts:
            print("- Nenhum resultado.")

        for status_code in sorted(result_counts.keys()):
            print(f"- {status_code}: {result_counts[status_code]}")

        total_errors = sum(
            count
            for status_code, count in result_counts.items()
            if status_code.startswith("ERRO")
        )

        total_warnings = sum(
            count
            for status_code, count in result_counts.items()
            if status_code.startswith("AVISO")
        )

        print("")
        print("===== CONCLUSÃO =====")
        print(f"Total de regras atuais avaliadas: {len(matched_rules)}")
        print(f"Total de membros avaliados: {len(validation_rows)}")
        print(f"Erros encontrados: {total_errors}")
        print(f"Avisos encontrados: {total_warnings}")

        if total_errors:
            print("RESULTADO FINAL: EXISTEM dados gravados que não respeitam a configuração atual.")
        elif total_warnings:
            print("RESULTADO FINAL: Não há erro obrigatório, mas existem avisos para revisão.")
        else:
            print("RESULTADO FINAL: Os dados gravados respeitam a configuração atual.")

        print("")
        print("OK: validação concluída. Nenhum dado foi alterado.")


if __name__ == "__main__":
    main_v2()
