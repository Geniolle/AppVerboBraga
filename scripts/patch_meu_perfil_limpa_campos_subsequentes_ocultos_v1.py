from __future__ import annotations

####################################################################################
# (1) IMPORTS
####################################################################################

from pathlib import Path
from datetime import datetime


####################################################################################
# (2) CAMINHOS
####################################################################################

ROOT = Path.cwd()

SERVICE_PROFILE_PATH = ROOT / "appverbo" / "services" / "profile.py"
PROFILE_HANDLERS_PATH = ROOT / "appverbo" / "routes" / "profile" / "profile_handlers.py"


####################################################################################
# (3) FUNÇÕES AUXILIARES
####################################################################################

def backup_file(path: Path) -> None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = path.with_suffix(path.suffix + f".bak_{timestamp}")
    backup_path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"OK: backup criado: {backup_path}")


def replace_required(content: str, old: str, new: str, label: str) -> str:
    if old not in content:
        print(f"INFO: bloco não encontrado ou já alterado: {label}")
        return content

    print(f"OK: patch aplicado: {label}")
    return content.replace(old, new, 1)


####################################################################################
# (4) PATCH EM appverbo/services/profile.py
####################################################################################

if not SERVICE_PROFILE_PATH.exists():
    raise SystemExit(f"ERRO: ficheiro não encontrado: {SERVICE_PROFILE_PATH}")

backup_file(SERVICE_PROFILE_PATH)

service_content = SERVICE_PROFILE_PATH.read_text(encoding="utf-8")

old_trigger = '        trigger_field = str(raw_rule.get("trigger_field") or "").strip().lower()'
new_trigger = '''        trigger_field = str(
            raw_rule.get("trigger_field")
            or raw_rule.get("trigger_field_key")
            or raw_rule.get("subsequent_trigger_field")
            or raw_rule.get("triggerField")
            or raw_rule.get("triggerFieldKey")
            or ""
        ).strip().lower()'''

old_target = '        target_field = str(raw_rule.get("field_key") or raw_rule.get("subsequent_field") or "").strip().lower()'
new_target = '''        target_field = str(
            raw_rule.get("field_key")
            or raw_rule.get("subsequent_field")
            or raw_rule.get("subsequent_field_key")
            or raw_rule.get("fieldKey")
            or raw_rule.get("target_field")
            or raw_rule.get("targetFieldKey")
            or ""
        ).strip().lower()'''

old_value = '        trigger_value = str(raw_rule.get("trigger_value") or "").strip()'
new_value = '''        trigger_value = str(
            raw_rule.get("trigger_value")
            or raw_rule.get("subsequent_trigger_value")
            or raw_rule.get("triggerValue")
            or ""
        ).strip()'''

service_content = replace_required(
    service_content,
    old_trigger,
    new_trigger,
    "profile.py normalizar trigger_field incluindo trigger_field_key",
)

service_content = replace_required(
    service_content,
    old_target,
    new_target,
    "profile.py normalizar field_key incluindo subsequent_field_key",
)

service_content = replace_required(
    service_content,
    old_value,
    new_value,
    "profile.py normalizar trigger_value incluindo subsequent_trigger_value",
)

SERVICE_PROFILE_PATH.write_text(service_content, encoding="utf-8")


####################################################################################
# (5) PATCH EM appverbo/routes/profile/profile_handlers.py
####################################################################################

if not PROFILE_HANDLERS_PATH.exists():
    raise SystemExit(f"ERRO: ficheiro não encontrado: {PROFILE_HANDLERS_PATH}")

backup_file(PROFILE_HANDLERS_PATH)

handlers_content = PROFILE_HANDLERS_PATH.read_text(encoding="utf-8")

helper_marker = "APPVERBO_MEU_PERFIL_SUBSEQUENT_RULES_RESOLVER_V1_START"

helper_block = '''
# APPVERBO_MEU_PERFIL_SUBSEQUENT_RULES_RESOLVER_V1_START
def _resolve_process_subsequent_rules_from_setting_v1(
    process_setting: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    if not isinstance(process_setting, dict):
        return []

    resolved_rules: list[dict[str, Any]] = []

    for storage_key in (
        "process_subsequent_fields",
        "subsequent_fields",
        "process_subsequent_rules",
    ):
        raw_rules = process_setting.get(storage_key)

        if not isinstance(raw_rules, list):
            continue

        for raw_rule in raw_rules:
            if isinstance(raw_rule, dict):
                resolved_rules.append(raw_rule)

    return resolved_rules
# APPVERBO_MEU_PERFIL_SUBSEQUENT_RULES_RESOLVER_V1_END


'''

if helper_marker not in handlers_content:
    insert_before = "\n\ndef _normalize_process_quantity_rules(raw_rules: Any) -> list[dict[str, Any]]:"
    if insert_before not in handlers_content:
        raise SystemExit("ERRO: ponto de inserção do helper não encontrado em profile_handlers.py")

    handlers_content = handlers_content.replace(
        insert_before,
        "\n\n" + helper_block + "def _normalize_process_quantity_rules(raw_rules: Any) -> list[dict[str, Any]]:",
        1,
    )
    print("OK: helper para ler todas as chaves de campos subsequentes inserido.")
else:
    print("INFO: helper de campos subsequentes já existe.")

old_hidden_call = '''        hidden_meu_perfil_targets = get_hidden_process_targets_from_rules(
            (meu_perfil_setting or {}).get("process_subsequent_fields"),
            current_meu_perfil_values,
        )'''

new_hidden_call = '''        meu_perfil_subsequent_rules = _resolve_process_subsequent_rules_from_setting_v1(
            meu_perfil_setting
        )
        hidden_meu_perfil_targets = get_hidden_process_targets_from_rules(
            meu_perfil_subsequent_rules,
            current_meu_perfil_values,
        )'''

handlers_content = replace_required(
    handlers_content,
    old_hidden_call,
    new_hidden_call,
    "profile_handlers.py usar subsequent_fields/process_subsequent_fields/process_subsequent_rules",
)

old_hidden_preserve = '''        for hidden_custom_key in visible_custom_keys:
            if hidden_custom_key in active_custom_keys_set:
                continue
            if hidden_custom_key in existing_custom_fields:
                updated_custom_fields[hidden_custom_key] = existing_custom_fields[hidden_custom_key]'''

new_hidden_preserve = '''        # APPVERBO_MEU_PERFIL_CLEAR_HIDDEN_SUBSEQUENT_VALUES_V1_START
        # Quando um campo fica oculto por regra de Campos Subsequentes,
        # o valor antigo deve ser removido para não apresentar informação incorreta.
        for hidden_custom_key in visible_custom_keys:
            if hidden_custom_key in active_custom_keys_set:
                continue

            updated_custom_fields.pop(hidden_custom_key, None)
        # APPVERBO_MEU_PERFIL_CLEAR_HIDDEN_SUBSEQUENT_VALUES_V1_END'''

handlers_content = replace_required(
    handlers_content,
    old_hidden_preserve,
    new_hidden_preserve,
    "profile_handlers.py limpar valores de campos ocultos em vez de preservar",
)

old_quantity_hidden = '''            if (
                quantity_field_key in hidden_meu_perfil_targets
                or visible_field_section_map.get(quantity_field_key) in hidden_meu_perfil_targets
            ):
                continue'''

new_quantity_hidden = '''            if (
                quantity_field_key in hidden_meu_perfil_targets
                or visible_field_section_map.get(quantity_field_key) in hidden_meu_perfil_targets
            ):
                storage_key = build_menu_process_quantity_storage_key(MENU_MEU_PERFIL_KEY, rule_key)

                if storage_key:
                    updated_quantity_values.pop(storage_key, None)

                continue'''

handlers_content = replace_required(
    handlers_content,
    old_quantity_hidden,
    new_quantity_hidden,
    "profile_handlers.py limpar valores de quantidade quando regra ficar oculta",
)

PROFILE_HANDLERS_PATH.write_text(handlers_content, encoding="utf-8")

print("OK: patch concluído.")
