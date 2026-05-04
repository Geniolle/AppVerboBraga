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
PAGE_SERVICE_PATH = ROOT / "appverbo" / "services" / "page.py"


####################################################################################
# (3) FUNÇÕES AUXILIARES
####################################################################################

def backup_file_v1(path: Path) -> None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = path.with_suffix(path.suffix + f".bak_{timestamp}")
    backup_path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"OK: backup criado: {backup_path}")


def replace_required_v1(content: str, old: str, new: str, label: str) -> str:
    if old not in content:
        print(f"INFO: bloco não encontrado ou já alterado: {label}")
        return content

    print(f"OK: patch aplicado: {label}")
    return content.replace(old, new, 1)


####################################################################################
# (4) VALIDAR FICHEIRO
####################################################################################

if not PAGE_SERVICE_PATH.exists():
    raise SystemExit(f"ERRO: ficheiro não encontrado: {PAGE_SERVICE_PATH}")

backup_file_v1(PAGE_SERVICE_PATH)

content = PAGE_SERVICE_PATH.read_text(encoding="utf-8")


####################################################################################
# (5) AJUSTAR IMPORTS DO PROFILE SERVICE
####################################################################################

old_import = '''from appverbo.services.profile import (
    build_menu_process_records_storage_key,
    build_menu_process_field_storage_key,
    build_menu_process_quantity_storage_key,
    get_menu_process_quantity_repeated_field_keys,
    is_meu_perfil_builtin_duplicate_field,
    resolve_meu_perfil_builtin_duplicate_field_key,
    parse_menu_process_records,
    parse_menu_process_quantity_values,
    parse_member_profile_fields,
)'''

new_import = '''from appverbo.services.profile import (
    build_menu_process_records_storage_key,
    build_menu_process_field_storage_key,
    build_menu_process_quantity_storage_key,
    filter_process_fields_by_hidden_targets,
    get_hidden_process_targets_from_rules,
    get_menu_process_quantity_repeated_field_keys,
    is_meu_perfil_builtin_duplicate_field,
    resolve_meu_perfil_builtin_duplicate_field_key,
    parse_menu_process_records,
    parse_menu_process_quantity_values,
    parse_member_profile_fields,
)'''

content = replace_required_v1(
    content,
    old_import,
    new_import,
    "page.py imports para regras de campos subsequentes",
)


####################################################################################
# (6) INSERIR HELPERS PARA VISIBILIDADE DO MEU PERFIL
####################################################################################

helper_marker = "APPVERBO_MEU_PERFIL_SUBSEQUENT_VISIBILITY_PAGE_V1_START"

helper_block = '''
# APPVERBO_MEU_PERFIL_SUBSEQUENT_VISIBILITY_PAGE_V1_START
def _format_profile_visibility_date_v1(raw_value: Any) -> str:
    if raw_value is None:
        return ""

    if hasattr(raw_value, "strftime"):
        return raw_value.strftime("%d/%m/%Y")

    return str(raw_value or "").strip()


def _collect_meu_perfil_subsequent_rules_v1(sidebar_item: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(sidebar_item, dict):
        return []

    collected_rules: list[dict[str, Any]] = []

    for storage_key in (
        "process_subsequent_fields",
        "subsequent_fields",
        "process_subsequent_rules",
    ):
        raw_rules = sidebar_item.get(storage_key)

        if not isinstance(raw_rules, list):
            continue

        for raw_rule in raw_rules:
            if isinstance(raw_rule, dict):
                collected_rules.append(raw_rule)

    return collected_rules


def _build_meu_perfil_visibility_values_v1(
    session: Session,
    actor_user_id: int | None,
    actor_profile_fields: dict[str, str],
) -> dict[str, str]:
    values_by_field: dict[str, str] = dict(actor_profile_fields or {})

    if actor_user_id is None:
        return values_by_field

    row = session.execute(
        select(
            Member.full_name,
            Member.primary_phone,
            Member.email,
            Member.country,
            Member.birth_date,
            User.login_email,
        )
        .join(User, User.member_id == Member.id)
        .where(User.id == actor_user_id)
        .limit(1)
    ).one_or_none()

    if row is None:
        return values_by_field

    values_by_field["nome"] = str(row.full_name or "").strip()
    values_by_field["telefone"] = str(row.primary_phone or "").strip()
    values_by_field["email"] = str(row.login_email or row.email or "").strip().lower()
    values_by_field["pais"] = str(row.country or "").strip()
    values_by_field["data_nascimento"] = _format_profile_visibility_date_v1(row.birth_date)

    return values_by_field


def _apply_meu_perfil_subsequent_visibility_v1(
    session: Session,
    actor_user_id: int | None,
    sidebar_item: dict[str, Any] | None,
    actor_profile_fields: dict[str, str],
    visible_fields: list[str],
    field_header_map: dict[str, str],
) -> list[str]:
    if not visible_fields:
        return []

    rules = _collect_meu_perfil_subsequent_rules_v1(sidebar_item)

    if not rules:
        return visible_fields

    values_by_field = _build_meu_perfil_visibility_values_v1(
        session,
        actor_user_id,
        actor_profile_fields,
    )

    hidden_targets = get_hidden_process_targets_from_rules(
        rules,
        values_by_field,
    )

    if not hidden_targets:
        return visible_fields

    return filter_process_fields_by_hidden_targets(
        visible_fields,
        hidden_targets,
        field_header_map,
    )
# APPVERBO_MEU_PERFIL_SUBSEQUENT_VISIBILITY_PAGE_V1_END


'''

if helper_marker not in content:
    insert_before = "\ndef get_page_data("
    if insert_before not in content:
        raise SystemExit("ERRO: ponto de inserção do helper não encontrado em page.py")

    content = content.replace(
        insert_before,
        "\n" + helper_block + "def get_page_data(",
        1,
    )
    print("OK: helpers de visibilidade inseridos.")
else:
    print("INFO: helpers de visibilidade já existem.")


####################################################################################
# (7) APLICAR FILTRO DE VISIBILIDADE ANTES DE DEFINIR profile_personal_visible_fields
####################################################################################

old_block = '''        if visible_fields:
            profile_personal_visible_fields = visible_fields
        elif profile_personal_field_labels:'''

new_block = '''        if visible_fields:
            visible_fields = _apply_meu_perfil_subsequent_visibility_v1(
                session=session,
                actor_user_id=actor_user_id,
                sidebar_item=sidebar_item,
                actor_profile_fields=actor_profile_fields,
                visible_fields=visible_fields,
                field_header_map=profile_personal_field_header_map,
            )
            profile_personal_visible_fields = visible_fields
        elif profile_personal_field_labels:'''

content = replace_required_v1(
    content,
    old_block,
    new_block,
    "page.py filtrar campos visíveis conforme Campos Subsequentes",
)


####################################################################################
# (8) GRAVAR FICHEIRO
####################################################################################

PAGE_SERVICE_PATH.write_text(content, encoding="utf-8")

print("OK: patch de visibilidade concluído.")
