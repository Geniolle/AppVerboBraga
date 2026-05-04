from __future__ import annotations

import re
from pathlib import Path


def read_text_v1(path: str) -> str:
    return Path(path).read_text(encoding="utf-8-sig")


def write_text_v1(path: str, content: str) -> None:
    Path(path).write_text(content.rstrip() + "\n", encoding="utf-8")


def require_v1(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


ENTITY_FORM_REFACTOR_BLOCK_V1 = r'''
# APPVERBO_ENTITY_FORM_REFACTOR_V1_START
ENTITY_FORM_FIELDS_V1: tuple[dict[str, Any], ...] = (
    {"key": "name", "label": "Nome da entidade", "required": True},
    {"key": "acronym", "label": "Acrónimo", "required": False},
    {"key": "tax_id", "label": "Nº Identificação Fiscal", "required": True},
    {"key": "profile_scope", "label": "Perfil da entidade", "required": True},
    {"key": "email", "label": "Email", "required": True},
    {"key": "phone", "label": "Telefone", "required": True},
    {"key": "responsible_name", "label": "Nome do responsável", "required": True},
    {"key": "address", "label": "Morada", "required": True},
    {"key": "door_number", "label": "Nº da porta", "required": True},
    {"key": "freguesia", "label": "Freguesia", "required": True},
    {"key": "postal_code", "label": "Código postal", "required": True},
    {"key": "city", "label": "Cidade", "required": True},
    {"key": "country", "label": "País", "required": True},
    {"key": "logo_url", "label": "Imagem/ícone da entidade", "required": False},
)

ENTITY_REQUIRED_FIELD_LABELS_V1: tuple[tuple[str, str], ...] = tuple(
    (str(field["key"]), str(field["label"]))
    for field in ENTITY_FORM_FIELDS_V1
    if bool(field.get("required")) and str(field.get("key")) != "profile_scope"
)

ENTITY_DATA_ASSIGNMENT_FIELDS_V1: tuple[str, ...] = (
    "name",
    "tax_id",
    "email",
    "responsible_name",
    "door_number",
    "address",
    "city",
    "freguesia",
    "postal_code",
    "country",
    "phone",
)


def normalize_entity_text_v1(value: Any) -> str:
    return str(value or "").strip()


def normalize_entity_profile_scope_v1(value: Any) -> tuple[str, bool]:
    clean_profile_scope = normalize_entity_text_v1(value).lower()
    invalid_profile_scope = clean_profile_scope not in ALLOWED_ENTITY_PROFILE_SCOPE

    if invalid_profile_scope:
        clean_profile_scope = ENTITY_PROFILE_SCOPE_LEGADO

    return clean_profile_scope, invalid_profile_scope


def clean_entity_form_data_v1(
    *,
    name: Any = "",
    acronym: Any = "",
    tax_id: Any = "",
    email: Any = "",
    responsible_name: Any = "",
    door_number: Any = "",
    address: Any = "",
    city: Any = "",
    freguesia: Any = "",
    postal_code: Any = "",
    country: Any = "",
    phone: Any = "",
    entity_profile_scope: Any = ENTITY_PROFILE_SCOPE_LEGADO,
    description: Any = None,
    created_at_text: str = "",
) -> tuple[dict[str, str], bool]:
    clean_profile_scope, invalid_profile_scope = normalize_entity_profile_scope_v1(
        entity_profile_scope
    )

    form_data = {
        "name": normalize_entity_text_v1(name),
        "acronym": normalize_entity_text_v1(acronym),
        "tax_id": normalize_entity_text_v1(tax_id),
        "email": normalize_entity_text_v1(email),
        "responsible_name": normalize_entity_text_v1(responsible_name),
        "door_number": normalize_entity_text_v1(door_number),
        "address": normalize_entity_text_v1(address),
        "city": normalize_entity_text_v1(city),
        "freguesia": normalize_entity_text_v1(freguesia),
        "postal_code": normalize_entity_text_v1(postal_code),
        "country": normalize_entity_text_v1(country),
        "phone": normalize_entity_text_v1(phone),
        "profile_scope": clean_profile_scope,
        "description": normalize_entity_text_v1(description),
        "created_at": created_at_text,
    }

    return form_data, invalid_profile_scope


def validate_entity_required_fields_v1(form_data: dict[str, str]) -> list[str]:
    missing_labels: list[str] = []

    for field_key, field_label in ENTITY_REQUIRED_FIELD_LABELS_V1:
        if not normalize_entity_text_v1(form_data.get(field_key)):
            missing_labels.append(field_label)

    return missing_labels


def apply_entity_form_data_v1(
    entity: Entity,
    form_data: dict[str, str],
    *,
    include_profile_scope: bool = True,
    include_description: bool = True,
) -> None:
    for field_key in ENTITY_DATA_ASSIGNMENT_FIELDS_V1:
        setattr(entity, field_key, normalize_entity_text_v1(form_data.get(field_key)) or None)

    entity.acronym = normalize_entity_text_v1(form_data.get("acronym")) or None

    if include_profile_scope:
        entity.profile_scope = normalize_entity_text_v1(
            form_data.get("profile_scope")
        ) or ENTITY_PROFILE_SCOPE_LEGADO

    if include_description:
        entity.description = normalize_entity_text_v1(form_data.get("description")) or None


def get_duplicate_entity_name_id_v1(
    session: Session,
    clean_name: str,
    *,
    ignore_entity_id: int | None = None,
) -> int | None:
    stmt = select(Entity.id).where(
        func.lower(Entity.name) == normalize_entity_text_v1(clean_name).lower()
    )

    if ignore_entity_id is not None:
        stmt = stmt.where(Entity.id != int(ignore_entity_id))

    raw_entity_id = session.scalar(stmt.limit(1))

    return int(raw_entity_id) if raw_entity_id is not None else None


def get_existing_owner_entity_id_v1(
    session: Session,
    *,
    ignore_entity_id: int | None = None,
) -> int | None:
    stmt = select(Entity.id).where(Entity.profile_scope == ENTITY_PROFILE_SCOPE_OWNER)

    if ignore_entity_id is not None:
        stmt = stmt.where(Entity.id != int(ignore_entity_id))

    raw_entity_id = session.scalar(stmt.limit(1))

    return int(raw_entity_id) if raw_entity_id is not None else None
# APPVERBO_ENTITY_FORM_REFACTOR_V1_END
'''


def patch_services_entities_v1() -> None:
    path = "appverbo/services/entities.py"
    content = read_text_v1(path)

    if "from typing import Any" not in content:
        content = content.replace(
            "from pathlib import Path\n",
            "from pathlib import Path\nfrom typing import Any\n",
            1,
        )

    content = re.sub(
        r"\n?# APPVERBO_ENTITY_FORM_REFACTOR_V1_START.*?# APPVERBO_ENTITY_FORM_REFACTOR_V1_END\n?",
        "\n",
        content,
        flags=re.S,
    )

    content = re.sub(
        r"\n__all__\s*=\s*\[.*?\]\s*\n?$",
        "",
        content,
        flags=re.S,
    )

    all_block = '''__all__ = [
    "save_entity_logo_upload",
    "ENTITY_FORM_FIELDS_V1",
    "ENTITY_REQUIRED_FIELD_LABELS_V1",
    "ENTITY_DATA_ASSIGNMENT_FIELDS_V1",
    "normalize_entity_text_v1",
    "normalize_entity_profile_scope_v1",
    "clean_entity_form_data_v1",
    "validate_entity_required_fields_v1",
    "apply_entity_form_data_v1",
    "get_duplicate_entity_name_id_v1",
    "get_existing_owner_entity_id_v1",
]
'''

    content = content.rstrip() + "\n\n" + ENTITY_FORM_REFACTOR_BLOCK_V1.strip() + "\n\n" + all_block

    write_text_v1(path, content)


def ensure_city_parameter_v1(content: str) -> str:
    if "city: str = Form" not in content:
        content = content.replace(
            "    address: str = Form(...),\n"
            "    freguesia: str = Form(...),",
            "    address: str = Form(...),\n"
            "    city: str = Form(...),\n"
            "    freguesia: str = Form(...),",
            1,
        )

    return content.replace(
        '    city: str = Form(""),',
        "    city: str = Form(...),",
    )


def replace_required_validation_v1(content: str) -> str:
    if "validate_entity_required_fields_v1(entity_form_data)" in content:
        return content

    pattern = (
        r"        required_field_labels = \[\]\n"
        r".*?"
        r"\n\n        if required_field_labels:"
    )
    replacement = (
        "        required_field_labels = validate_entity_required_fields_v1(entity_form_data)\n"
        "        if invalid_profile_scope:\n"
        '            required_field_labels.append("Perfil de partilha")\n\n'
        "        if required_field_labels:"
    )

    new_content, count = re.subn(pattern, replacement, content, count=1, flags=re.S)
    require_v1(count == 1, "ERRO: não foi possível substituir a validação obrigatória.")
    return new_content


def patch_create_handler_v1() -> None:
    path = "appverbo/routes/entities/create_handler.py"
    content = read_text_v1(path)
    content = ensure_city_parameter_v1(content)

    if "clean_entity_form_data_v1(" not in content:
        clean_block = '''    entity_form_data, invalid_profile_scope = clean_entity_form_data_v1(
        name=name,
        acronym=acronym,
        tax_id=tax_id,
        email=email,
        responsible_name=responsible_name,
        door_number=door_number,
        address=address,
        city=city,
        freguesia=freguesia,
        postal_code=postal_code,
        country=country,
        phone=phone,
        entity_profile_scope=entity_profile_scope,
        description=description,
        created_at_text=date.today().strftime("%d/%m/%Y"),
    )
    clean_name = entity_form_data["name"]
    clean_profile_scope = entity_form_data["profile_scope"]

    with SessionLocal() as session:'''

        content, count = re.subn(
            r"    clean_name = name\.strip\(\)\n.*?\n    with SessionLocal\(\) as session:",
            clean_block,
            content,
            count=1,
            flags=re.S,
        )
        require_v1(count == 1, "ERRO: não foi possível refatorar limpeza do create_handler.py.")

    content = replace_required_validation_v1(content)

    if "get_duplicate_entity_name_id_v1(session, clean_name)" not in content:
        content, count = re.subn(
            r"        existing_entity = session\.scalar\(\n.*?\n        \)\n        if existing_entity is not None:",
            "        existing_entity = get_duplicate_entity_name_id_v1(session, clean_name)\n"
            "        if existing_entity is not None:",
            content,
            count=1,
            flags=re.S,
        )
        require_v1(count == 1, "ERRO: não foi possível refatorar duplicidade no create_handler.py.")

    if "get_existing_owner_entity_id_v1(session)" not in content:
        content, count = re.subn(
            r"            existing_owner_id = session\.scalar\(\n.*?\n            \)\n            if existing_owner_id is not None:",
            "            existing_owner_id = get_existing_owner_entity_id_v1(session)\n"
            "            if existing_owner_id is not None:",
            content,
            count=1,
            flags=re.S,
        )
        require_v1(count == 1, "ERRO: não foi possível refatorar Owner único no create_handler.py.")

    if "apply_entity_form_data_v1(entity, entity_form_data)" not in content:
        entity_block = '''        entity = Entity(
            internal_number=next_entity_internal_number,
            logo_url=stored_logo_url or None,
            is_active=True,
        )
        apply_entity_form_data_v1(entity, entity_form_data)
        session.add(entity)'''

        content, count = re.subn(
            r"        entity = Entity\(\n.*?\n        session\.add\(entity\)",
            entity_block,
            content,
            count=1,
            flags=re.S,
        )
        require_v1(count == 1, "ERRO: não foi possível refatorar criação do Entity.")

    write_text_v1(path, content)


def patch_update_handler_v1() -> None:
    path = "appverbo/routes/entities/update_handler.py"
    content = read_text_v1(path)
    content = ensure_city_parameter_v1(content)

    if "clean_entity_form_data_v1(" not in content:
        clean_block = '''    clean_entity_id = entity_id.strip()
    entity_form_data, invalid_profile_scope = clean_entity_form_data_v1(
        name=name,
        acronym=acronym,
        tax_id=tax_id,
        email=email,
        responsible_name=responsible_name,
        door_number=door_number,
        address=address,
        city=city,
        freguesia=freguesia,
        postal_code=postal_code,
        country=country,
        phone=phone,
        entity_profile_scope=entity_profile_scope,
        description=description,
    )
    clean_name = entity_form_data["name"]
    clean_profile_scope = entity_form_data["profile_scope"]
    clean_status = entity_status.strip().lower()

    if not clean_entity_id.isdigit():'''

        content, count = re.subn(
            r"    clean_entity_id = entity_id\.strip\(\)\n.*?\n    if not clean_entity_id\.isdigit\(\):",
            clean_block,
            content,
            count=1,
            flags=re.S,
        )
        require_v1(count == 1, "ERRO: não foi possível refatorar limpeza do update_handler.py.")

    content = replace_required_validation_v1(content)

    if "get_duplicate_entity_name_id_v1(" not in content:
        content, count = re.subn(
            r"        duplicate_id = session\.scalar\(\n.*?\n        \)\n        if duplicate_id is not None:",
            "        duplicate_id = get_duplicate_entity_name_id_v1(\n"
            "            session,\n"
            "            clean_name,\n"
            "            ignore_entity_id=parsed_entity_id,\n"
            "        )\n"
            "        if duplicate_id is not None:",
            content,
            count=1,
            flags=re.S,
        )
        require_v1(count == 1, "ERRO: não foi possível refatorar duplicidade no update_handler.py.")

    if "get_existing_owner_entity_id_v1(" not in content:
        content, count = re.subn(
            r"            existing_owner_id = session\.scalar\(\n.*?\n            \)\n            if existing_owner_id is not None:",
            "            existing_owner_id = get_existing_owner_entity_id_v1(\n"
            "                session,\n"
            "                ignore_entity_id=parsed_entity_id,\n"
            "            )\n"
            "            if existing_owner_id is not None:",
            content,
            count=1,
            flags=re.S,
        )
        require_v1(count == 1, "ERRO: não foi possível refatorar Owner único no update_handler.py.")

    if "apply_entity_form_data_v1(" not in content:
        apply_block = '''        apply_entity_form_data_v1(
            entity,
            entity_form_data,
            include_description=isinstance(description, str),
        )
        if can_manage_all_entities:'''

        content, count = re.subn(
            r"        entity\.name = clean_name\n.*?\n        if can_manage_all_entities:",
            apply_block,
            content,
            count=1,
            flags=re.S,
        )
        require_v1(count == 1, "ERRO: não foi possível refatorar aplicação de dados no update_handler.py.")

    write_text_v1(path, content)


def validate_v1() -> None:
    services = read_text_v1("appverbo/services/entities.py")
    create_handler = read_text_v1("appverbo/routes/entities/create_handler.py")
    update_handler = read_text_v1("appverbo/routes/entities/update_handler.py")

    checks = {
        "catalogo campos": "ENTITY_FORM_FIELDS_V1" in services,
        "limpeza central": "clean_entity_form_data_v1" in services,
        "validacao central": "validate_entity_required_fields_v1" in services,
        "aplicacao central": "apply_entity_form_data_v1" in services,
        "duplicidade central": "get_duplicate_entity_name_id_v1" in services,
        "owner central": "get_existing_owner_entity_id_v1" in services,
        "create usa limpeza": "clean_entity_form_data_v1(" in create_handler,
        "create usa validacao": "validate_entity_required_fields_v1(entity_form_data)" in create_handler,
        "create usa duplicidade": "get_duplicate_entity_name_id_v1(session, clean_name)" in create_handler,
        "create usa owner": "get_existing_owner_entity_id_v1(session)" in create_handler,
        "create usa apply": "apply_entity_form_data_v1(entity, entity_form_data)" in create_handler,
        "update usa limpeza": "clean_entity_form_data_v1(" in update_handler,
        "update usa validacao": "validate_entity_required_fields_v1(entity_form_data)" in update_handler,
        "update usa duplicidade": "get_duplicate_entity_name_id_v1(" in update_handler,
        "update usa owner": "get_existing_owner_entity_id_v1(" in update_handler,
        "update usa apply": "apply_entity_form_data_v1(" in update_handler,
        "cidade obrigatoria create": "city: str = Form(...)" in create_handler,
        "cidade obrigatoria update": "city: str = Form(...)" in update_handler,
    }

    failed = [name for name, ok in checks.items() if not ok]
    require_v1(not failed, "Falha na validação: " + ", ".join(failed))


def main_v1() -> None:
    patch_services_entities_v1()
    patch_create_handler_v1()
    patch_update_handler_v1()
    validate_v1()


if __name__ == "__main__":
    main_v1()
