from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
####################################################################################
# (1) IMPORTS
####################################################################################

import json
import unicodedata
from typing import Any

from sqlalchemy import text

from appgenesis.core import SessionLocal


####################################################################################
# (2) CONSTANTES DO PROCESSO
####################################################################################

MENU_KEY = "meu_perfil"
LEGACY_MENU_KEY = "documentos"

SYSTEM_REQUIRED_FIELDS = {
    "nome": "Nome",
    "telefone": "Telefone",
    "email": "Email",
    "pais": "País",
}

SYSTEM_OPTIONAL_FIELDS = {
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

SYSTEM_ALL_FIELDS = {
    **SYSTEM_REQUIRED_FIELDS,
    **SYSTEM_OPTIONAL_FIELDS,
}


####################################################################################
# (3) FUNÇÕES AUXILIARES
####################################################################################

def normalize_key(value: Any) -> str:
    return str(value or "").strip().lower()


def normalize_lookup(value: Any) -> str:
    raw_text = str(value or "").strip().lower()
    normalized = unicodedata.normalize("NFD", raw_text)
    normalized = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    normalized = normalized.replace("_", " ").replace("-", " ")
    return " ".join(normalized.split())


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


def is_duplicate_of_system_field(field_key: str, field_label: str) -> bool:
    clean_key = normalize_key(field_key)

    if not clean_key.startswith("custom_"):
        return False

    lookup_values = set()

    for system_key, system_label in SYSTEM_ALL_FIELDS.items():
        lookup_values.add(normalize_lookup(system_key))
        lookup_values.add(normalize_lookup(system_label))

    custom_key_lookup = normalize_lookup(clean_key.removeprefix("custom_"))
    custom_label_lookup = normalize_lookup(field_label)

    return custom_key_lookup in lookup_values or custom_label_lookup in lookup_values


def format_csv(values: list[str] | set[str]) -> str:
    clean_values = sorted({normalize_key(value) for value in values if normalize_key(value)})
    return ", ".join(clean_values) if clean_values else "-"


####################################################################################
# (4) LER CONFIGURAÇÃO DO MENU MEU PERFIL
####################################################################################

with SessionLocal() as session:
    menu_row = session.execute(
        text(
            """
            SELECT menu_key, menu_label, menu_config
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
        raise SystemExit("ERRO: configuração do menu Meu perfil não encontrada em sidebar_menu_settings.")

    menu_config = safe_json_loads(menu_row.get("menu_config"), {})

    if not isinstance(menu_config, dict):
        raise SystemExit("ERRO: menu_config do Meu perfil não é um JSON válido.")


####################################################################################
# (5) EXTRAIR CAMPOS CRIADOS, CABEÇALHOS E CAMPOS VISÍVEIS
####################################################################################

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

created_fields: dict[str, dict[str, str]] = {}
header_fields: dict[str, dict[str, str]] = {}

for raw_field in additional_fields_raw:
    if not isinstance(raw_field, dict):
        continue

    field_key = normalize_key(raw_field.get("key"))
    field_label = str(raw_field.get("label") or "").strip()
    field_type = normalize_key(raw_field.get("field_type") or raw_field.get("type") or "text")

    if not field_key:
        continue

    created_fields[field_key] = {
        "key": field_key,
        "label": field_label,
        "field_type": field_type,
    }

    if field_type == "header":
        header_fields[field_key] = {
            "key": field_key,
            "label": field_label,
            "field_type": field_type,
        }

visible_field_keys: list[str] = []
visible_header_by_field: dict[str, str] = {}

for raw_key in visible_fields_raw:
    field_key = normalize_key(raw_key)

    if field_key and field_key not in visible_field_keys:
        visible_field_keys.append(field_key)

for raw_row in visible_rows_raw:
    if not isinstance(raw_row, dict):
        continue

    field_key = normalize_key(raw_row.get("field_key"))
    header_key = normalize_key(raw_row.get("header_key"))

    if not field_key:
        continue

    if field_key not in visible_field_keys:
        visible_field_keys.append(field_key)

    if header_key:
        visible_header_by_field[field_key] = header_key

for raw_field_key, raw_header_key in header_map_raw.items():
    field_key = normalize_key(raw_field_key)
    header_key = normalize_key(raw_header_key)

    if field_key and header_key:
        visible_header_by_field[field_key] = header_key


####################################################################################
# (6) DEFINIR CAMPOS PERSONALIZADOS VÁLIDOS NO BLOCO DADOS PESSOAIS
####################################################################################

valid_custom_fields: set[str] = set()
invalid_config_fields: list[dict[str, str]] = []

for field_key in visible_field_keys:
    if field_key in SYSTEM_REQUIRED_FIELDS:
        continue

    if field_key in SYSTEM_OPTIONAL_FIELDS:
        header_key = visible_header_by_field.get(field_key, "")

        if not header_key:
            invalid_config_fields.append(
                {
                    "field_key": field_key,
                    "reason": "campo opcional de sistema visível sem cabeçalho",
                }
            )
            continue

        if header_key not in header_fields:
            invalid_config_fields.append(
                {
                    "field_key": field_key,
                    "reason": f"campo opcional de sistema aponta para cabeçalho inexistente: {header_key}",
                }
            )
            continue

        continue

    if not field_key.startswith("custom_"):
        invalid_config_fields.append(
            {
                "field_key": field_key,
                "reason": "campo não é sistema nem campo custom_ criado",
            }
        )
        continue

    created_meta = created_fields.get(field_key)

    if created_meta is None:
        invalid_config_fields.append(
            {
                "field_key": field_key,
                "reason": "campo aparece como visível, mas não existe em additional_fields",
            }
        )
        continue

    if created_meta.get("field_type") == "header":
        continue

    if is_duplicate_of_system_field(field_key, created_meta.get("label", "")):
        invalid_config_fields.append(
            {
                "field_key": field_key,
                "reason": "campo custom_ duplica campo de sistema",
            }
        )
        continue

    header_key = visible_header_by_field.get(field_key, "")

    if not header_key:
        invalid_config_fields.append(
            {
                "field_key": field_key,
                "reason": "campo custom_ visível sem cabeçalho",
            }
        )
        continue

    if header_key not in header_fields:
        invalid_config_fields.append(
            {
                "field_key": field_key,
                "reason": f"campo custom_ aponta para cabeçalho inexistente: {header_key}",
            }
        )
        continue

    valid_custom_fields.add(field_key)


####################################################################################
# (7) LER CAMPOS EXISTENTES EM members.profile_custom_fields
####################################################################################

member_rows = session.execute(
    text(
        """
        SELECT id, full_name, email, profile_custom_fields
        FROM members
        WHERE profile_custom_fields IS NOT NULL
          AND trim(profile_custom_fields) <> ''
        ORDER BY id
        """
    )
).mappings().all()

stored_custom_usage: dict[str, list[dict[str, str]]] = {}

for member_row in member_rows:
    parsed_fields = safe_json_loads(member_row.get("profile_custom_fields"), {})

    if not isinstance(parsed_fields, dict):
        continue

    for raw_key, raw_value in parsed_fields.items():
        field_key = normalize_key(raw_key)

        if not field_key.startswith("custom_"):
            continue

        clean_value = str(raw_value or "").strip()

        if not clean_value:
            continue

        stored_custom_usage.setdefault(field_key, []).append(
            {
                "member_id": str(member_row.get("id")),
                "full_name": str(member_row.get("full_name") or ""),
                "email": str(member_row.get("email") or ""),
                "value": clean_value,
            }
        )


####################################################################################
# (8) IDENTIFICAR CAMPOS A ELIMINAR DA BASE
####################################################################################

fields_to_delete_from_profile_custom_fields: dict[str, list[dict[str, str]]] = {}

for field_key, usage_rows in stored_custom_usage.items():
    created_meta = created_fields.get(field_key, {})
    field_label = created_meta.get("label", "")

    delete_reason = ""

    if field_key not in created_fields:
        delete_reason = "não existe em Administrativo > Menu > Meu perfil > campos adicionais"
    elif field_key not in visible_field_keys:
        delete_reason = "existe em campos adicionais, mas não está visível no processo Meu perfil"
    elif field_key not in valid_custom_fields:
        header_key = visible_header_by_field.get(field_key, "")
        if not header_key:
            delete_reason = "não tem cabeçalho configurado"
        elif header_key not in header_fields:
            delete_reason = f"cabeçalho configurado não existe: {header_key}"
        elif is_duplicate_of_system_field(field_key, field_label):
            delete_reason = "duplica campo de sistema"
        else:
            delete_reason = "não cumpre a regra de configuração do processo"

    if delete_reason:
        fields_to_delete_from_profile_custom_fields[field_key] = [
            {
                **usage_row,
                "reason": delete_reason,
            }
            for usage_row in usage_rows
        ]


####################################################################################
# (9) IMPRIMIR RELATÓRIO
####################################################################################

print("")
print("===== CONFIGURAÇÃO DO MENU =====")
print(f"Menu encontrado: {menu_row.get('menu_key')} - {menu_row.get('menu_label')}")

print("")
print("===== CAMPOS DE SISTEMA MANTIDOS SEMPRE =====")
for field_key, field_label in SYSTEM_REQUIRED_FIELDS.items():
    print(f"- {field_key}: {field_label}")

print("")
print("===== CABEÇALHOS CONFIGURADOS =====")
if header_fields:
    for header_key, meta in sorted(header_fields.items()):
        print(f"- {header_key}: {meta.get('label') or header_key}")
else:
    print("- Nenhum cabeçalho configurado.")

print("")
print("===== CAMPOS CRIADOS EM additional_fields =====")
if created_fields:
    for field_key, meta in sorted(created_fields.items()):
        print(f"- {field_key}: {meta.get('label') or field_key} | tipo={meta.get('field_type')}")
else:
    print("- Nenhum campo adicional criado.")

print("")
print("===== CAMPOS VISÍVEIS NO PROCESSO MEU PERFIL =====")
if visible_field_keys:
    for field_key in visible_field_keys:
        header_key = visible_header_by_field.get(field_key, "")
        header_label = header_fields.get(header_key, {}).get("label", "")
        header_text = f"{header_key} - {header_label}" if header_key else "SEM CABEÇALHO"
        print(f"- {field_key} | cabeçalho: {header_text}")
else:
    print("- Nenhum campo visível configurado.")

print("")
print("===== CAMPOS CUSTOM_ VÁLIDOS PARA MANTER EM members.profile_custom_fields =====")
if valid_custom_fields:
    for field_key in sorted(valid_custom_fields):
        header_key = visible_header_by_field.get(field_key, "")
        field_label = created_fields.get(field_key, {}).get("label", field_key)
        header_label = header_fields.get(header_key, {}).get("label", header_key)
        print(f"- {field_key}: {field_label} | cabeçalho={header_key}: {header_label}")
else:
    print("- Nenhum campo custom_ válido encontrado.")

print("")
print("===== PROBLEMAS NA CONFIGURAÇÃO DO PROCESSO =====")
if invalid_config_fields:
    for item in invalid_config_fields:
        print(f"- REMOVER/AJUSTAR CONFIG: {item['field_key']} | motivo: {item['reason']}")
else:
    print("- Nenhum problema encontrado na configuração.")

print("")
print("===== CAMPOS EXISTENTES NA BASE QUE DEVEM SER ELIMINADOS DE members.profile_custom_fields =====")
if fields_to_delete_from_profile_custom_fields:
    for field_key, usage_rows in sorted(fields_to_delete_from_profile_custom_fields.items()):
        first_reason = usage_rows[0]["reason"] if usage_rows else "motivo não identificado"
        print(f"")
        print(f"- ELIMINAR: {field_key}")
        print(f"  Motivo: {first_reason}")
        print(f"  Utilizadores afetados: {len(usage_rows)}")

        for usage_row in usage_rows[:20]:
            print(
                "  "
                + f"member_id={usage_row['member_id']} | "
                + f"nome={usage_row['full_name']} | "
                + f"email={usage_row['email']} | "
                + f"valor={usage_row['value']}"
            )

        if len(usage_rows) > 20:
            print(f"  ... mais {len(usage_rows) - 20} utilizadores omitidos no resumo.")
else:
    print("- Nenhum campo órfão encontrado para eliminar.")

print("")
print("===== RESUMO =====")
print(f"Campos criados: {len(created_fields)}")
print(f"Cabeçalhos criados: {len(header_fields)}")
print(f"Campos visíveis: {len(visible_field_keys)}")
print(f"Campos custom_ válidos: {len(valid_custom_fields)}")
print(f"Campos custom_ na base: {len(stored_custom_usage)}")
print(f"Campos custom_ a eliminar: {len(fields_to_delete_from_profile_custom_fields)}")

print("")
print("OK: validação concluída. Nenhum dado foi alterado.")

