from __future__ import annotations

import json

from sqlalchemy import inspect, text

from appverbo.db.session import SessionLocal, engine


# ###################################################################################
# (1) FUNCOES AUXILIARES
# ###################################################################################

def normalize_key(value: object) -> str:
    return str(value or "").strip().lower()


def insert_after(values: list[str], after_key: str, new_key: str) -> list[str]:
    clean_values = [normalize_key(value) for value in values if normalize_key(value)]

    if new_key in clean_values:
        return clean_values

    if after_key in clean_values:
        index = clean_values.index(after_key)
        clean_values.insert(index + 1, new_key)
        return clean_values

    clean_values.append(new_key)
    return clean_values


# ###################################################################################
# (2) ATUALIZAR CONFIGURACAO DO MENU DOCUMENTOS
# ###################################################################################

inspector = inspect(engine)
tables = set(inspector.get_table_names())

if "sidebar_menu_settings" not in tables:
    raise SystemExit("ERRO: tabela sidebar_menu_settings nao existe.")

with SessionLocal() as session:
    row = session.execute(
        text(
            """
            SELECT id, menu_config
            FROM sidebar_menu_settings
            WHERE lower(trim(menu_key)) = 'documentos'
            LIMIT 1
            """
        )
    ).mappings().one_or_none()

    if row is None:
        print("AVISO: menu_key=documentos nao encontrado em sidebar_menu_settings.")
        raise SystemExit(0)

    try:
        config = json.loads(row["menu_config"] or "{}")
    except json.JSONDecodeError:
        config = {}

    if not isinstance(config, dict):
        config = {}

    options = config.get("process_field_options")
    if not isinstance(options, list):
        options = []

    has_pais_option = any(normalize_key(item.get("key")) == "pais" for item in options if isinstance(item, dict))

    if not has_pais_option:
        pais_option = {
            "key": "pais",
            "label": "País",
            "field_type": "text",
            "size": 120,
            "is_required": False,
        }

        telefone_index = next(
            (
                index
                for index, item in enumerate(options)
                if isinstance(item, dict) and normalize_key(item.get("key")) == "telefone"
            ),
            None,
        )

        if telefone_index is None:
            options.append(pais_option)
        else:
            options.insert(telefone_index + 1, pais_option)

    config["process_field_options"] = options

    visible_fields = config.get("process_visible_fields")
    if not isinstance(visible_fields, list):
        visible_fields = []

    config["process_visible_fields"] = insert_after(visible_fields, "telefone", "pais")

    visible_rows = config.get("process_visible_field_rows")
    if isinstance(visible_rows, list):
        has_pais_row = any(
            isinstance(item, dict) and normalize_key(item.get("field_key")) == "pais"
            for item in visible_rows
        )

        if not has_pais_row:
            telefone_row = next(
                (
                    item
                    for item in visible_rows
                    if isinstance(item, dict) and normalize_key(item.get("field_key")) == "telefone"
                ),
                {},
            )

            header_key = ""
            if isinstance(telefone_row, dict):
                header_key = normalize_key(telefone_row.get("header_key"))

            pais_row = {
                "field_key": "pais",
                "header_key": header_key,
            }

            telefone_index = next(
                (
                    index
                    for index, item in enumerate(visible_rows)
                    if isinstance(item, dict) and normalize_key(item.get("field_key")) == "telefone"
                ),
                None,
            )

            if telefone_index is None:
                visible_rows.append(pais_row)
            else:
                visible_rows.insert(telefone_index + 1, pais_row)

        config["process_visible_field_rows"] = visible_rows

    header_map = config.get("process_visible_field_header_map")
    if isinstance(header_map, dict) and "pais" not in header_map:
        telefone_header = normalize_key(header_map.get("telefone"))
        if telefone_header:
            header_map["pais"] = telefone_header
            config["process_visible_field_header_map"] = header_map

    session.execute(
        text(
            """
            UPDATE sidebar_menu_settings
            SET menu_config = :menu_config
            WHERE id = :id
            """
        ),
        {
            "id": row["id"],
            "menu_config": json.dumps(config, ensure_ascii=False),
        },
    )

    session.commit()

print("OK: configuracao do menu documentos atualizada com o campo País.")
