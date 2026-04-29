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


def load_config(raw_config):
    if isinstance(raw_config, dict):
        return dict(raw_config)
    if isinstance(raw_config, str) and raw_config.strip():
        try:
            parsed = json.loads(raw_config)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


with SessionLocal() as session:
    rows = session.execute(
        text("""
            SELECT menu_key, menu_label, menu_config
            FROM sidebar_menu_settings
            ORDER BY menu_key
        """)
    ).all()

    print("MENUS ENCONTRADOS:")
    for row in rows:
        print(f"- key={row.menu_key} | label={row.menu_label}")

    print("")
    print("PROCURANDO CAMPO ESTADO CIVIL...")

    target_row = None
    target_config = None

    for row in rows:
        config = load_config(row.menu_config)
        additional_fields = config.get("additional_fields") or []

        for field in additional_fields:
            if not isinstance(field, dict):
                continue

            label = str(field.get("label") or "").strip()
            field_type = str(field.get("field_type") or field.get("type") or "").strip().lower()

            if normalize_key(label) == "estado_civil" and field_type == "list":
                target_row = row
                target_config = config
                break

        if target_row is not None:
            break

    if target_row is None:
        raise RuntimeError("Não encontrei nenhum campo do tipo Lista com label Estado civil.")

    print("")
    print(f"PROCESSO ENCONTRADO:")
    print(f"- key={target_row.menu_key}")
    print(f"- label={target_row.menu_label}")

    process_lists = target_config.get("process_lists") or []
    additional_fields = target_config.get("additional_fields") or []

    list_by_key = {
        normalize_key(item.get("key") or item.get("label")): item
        for item in process_lists
        if isinstance(item, dict)
    }

    estado_civil_list_key = ""

    for item in process_lists:
        if not isinstance(item, dict):
            continue

        item_key = normalize_key(item.get("key") or item.get("label"))
        item_label = normalize_key(item.get("label"))

        if item_key == "estado_civil" or item_label == "estado_civil":
            estado_civil_list_key = item_key
            break

    if not estado_civil_list_key:
        estado_civil_list_key = "estado_civil"
        process_lists.append(
            {
                "key": "estado_civil",
                "label": "Estado civil",
                "items": [
                    "Solteiro",
                    "Casado",
                    "Divorciado",
                    "Viúvo",
                    "União de facto"
                ],
            }
        )
        target_config["process_lists"] = process_lists
        print("")
        print("LISTA ESTADO CIVIL NÃO EXISTIA. Foi criada com opções padrão.")

    changed = False

    for field in additional_fields:
        if not isinstance(field, dict):
            continue

        label = str(field.get("label") or "").strip()
        field_type = str(field.get("field_type") or field.get("type") or "").strip().lower()

        if normalize_key(label) == "estado_civil" and field_type == "list":
            old_list_key = normalize_key(field.get("list_key"))
            field["list_key"] = estado_civil_list_key
            changed = True
            print("")
            print("CAMPO CORRIGIDO:")
            print(f"- label={label}")
            print(f"- list_key antigo={old_list_key}")
            print(f"- list_key novo={estado_civil_list_key}")

    target_config["additional_fields"] = additional_fields

    if changed:
        session.execute(
            text("""
                UPDATE sidebar_menu_settings
                SET menu_config = :menu_config
                WHERE menu_key = :menu_key
            """),
            {
                "menu_key": target_row.menu_key,
                "menu_config": json.dumps(target_config, ensure_ascii=False),
            },
        )
        session.commit()
        print("")
        print("OK: menu_config atualizado com sucesso.")
    else:
        print("")
        print("Nenhuma alteração aplicada.")

    print("")
    print("DIAGNÓSTICO FINAL:")
    print("LISTAS:")
    for item in target_config.get("process_lists", []):
        if normalize_key(item.get("label")) == "estado_civil" or normalize_key(item.get("key")) == "estado_civil":
            print(item)

    print("")
    print("CAMPO ESTADO CIVIL:")
    for item in target_config.get("additional_fields", []):
        if normalize_key(item.get("label")) == "estado_civil":
            print(item)
