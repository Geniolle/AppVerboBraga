from appverbo.core import SessionLocal
from sqlalchemy import text
import json
import re
import unicodedata


def normalize_key(value):
    value = str(value or "").strip().lower()
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^a-z0-9_]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value


with SessionLocal() as session:
    row = session.execute(
        text("""
            SELECT menu_key, menu_config
            FROM sidebar_menu_settings
            WHERE lower(trim(menu_key)) = 'meu_perfil'
            LIMIT 1
        """)
    ).one_or_none()

    if row is None:
        raise RuntimeError("Menu Meu perfil não encontrado.")

    raw_config = row.menu_config

    if isinstance(raw_config, dict):
        config = dict(raw_config)
    elif isinstance(raw_config, str) and raw_config.strip():
        config = json.loads(raw_config)
    else:
        config = {}

    process_lists = config.get("process_lists") or []
    additional_fields = config.get("additional_fields") or []

    list_keys = {
        normalize_key(item.get("key") or item.get("label")): item
        for item in process_lists
        if isinstance(item, dict)
    }

    changed = False

    for field in additional_fields:
        if not isinstance(field, dict):
            continue

        label = str(field.get("label") or "").strip()
        field_type = str(field.get("field_type") or field.get("type") or "").strip().lower()

        if field_type != "list":
            continue

        current_list_key = normalize_key(field.get("list_key"))

        if current_list_key and current_list_key in list_keys:
            field["list_key"] = current_list_key
            continue

        candidate_key = normalize_key(label)

        if candidate_key in list_keys:
            field["list_key"] = candidate_key
            changed = True
            print(f"Corrigido: {label} -> list_key={candidate_key}")

    config["additional_fields"] = additional_fields

    if changed:
        session.execute(
            text("""
                UPDATE sidebar_menu_settings
                SET menu_config = :menu_config
                WHERE lower(trim(menu_key)) = 'meu_perfil'
            """),
            {"menu_config": json.dumps(config, ensure_ascii=False)}
        )
        session.commit()
        print("OK: menu_config atualizado.")
    else:
        print("Nenhuma alteração necessária. Verifique se existe lista criada com o nome Estado civil.")
