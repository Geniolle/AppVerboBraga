from appverbo.core import SessionLocal
from sqlalchemy import text
import json

def run():
    with SessionLocal() as session:
        # Fetch the menu configuration for 'meu_perfil'
        row = session.execute(
            text(
                """
                SELECT id, menu_config
                FROM sidebar_menu_settings
                WHERE lower(trim(menu_key)) = 'meu_perfil'
                LIMIT 1
                """
            )
        ).mappings().one_or_none()

        if row is None:
            print("ERROR: menu_key=meu_perfil not found in sidebar_menu_settings.")
            return

        menu_id = row["id"]
        config = json.loads(row["menu_config"] or "{}")
        if not isinstance(config, dict):
            config = {}

        changed = False

        # Ensure 'autorizacao_whatsapp' is in selectable options if we have custom options list
        # (Though it is statically defined in Python, sometimes it is cached in the DB)
        options = config.get("process_field_options", [])
        if isinstance(options, list):
            has_option = any(item.get("key") == "autorizacao_whatsapp" for item in options if isinstance(item, dict))
            if not has_option:
                # Add static option to DB config list if missing
                options.append({
                    "key": "autorizacao_whatsapp",
                    "label": "Autorização para avisos por WhatsApp"
                })
                config["process_field_options"] = options
                changed = True

        # Check visible_fields and process_visible_fields
        visible_fields = config.get("visible_fields", [])
        process_visible_fields = config.get("process_visible_fields", [])
        visible_field_headers = config.get("visible_field_headers", {})
        process_visible_field_rows = config.get("process_visible_field_rows", [])

        if not isinstance(visible_fields, list): visible_fields = []
        if not isinstance(process_visible_fields, list): process_visible_fields = []
        if not isinstance(visible_field_headers, dict): visible_field_headers = {}
        if not isinstance(process_visible_field_rows, list): process_visible_field_rows = []

        target_field = "autorizacao_whatsapp"
        target_header = "custom_dados_pessoais"

        # Ensure target_field is in process_visible_fields
        if target_field not in process_visible_fields:
            # Let's insert it after 'custom_tem_filhos' or 'whatsapp' if they exist, otherwise at the end
            inserted = False
            for ref_key in ["custom_tem_filhos", "whatsapp", "data_nascimento", "email"]:
                if ref_key in process_visible_fields:
                    idx = process_visible_fields.index(ref_key)
                    process_visible_fields.insert(idx + 1, target_field)
                    inserted = True
                    break
            if not inserted:
                process_visible_fields.append(target_field)
            config["process_visible_fields"] = process_visible_fields
            changed = True
            print(f"Added {target_field} to process_visible_fields.")

        # Ensure target_field is in visible_fields (legacy)
        if target_field not in visible_fields:
            inserted = False
            for ref_key in ["custom_tem_filhos", "whatsapp", "data_nascimento", "email"]:
                if ref_key in visible_fields:
                    idx = visible_fields.index(ref_key)
                    visible_fields.insert(idx + 1, target_field)
                    inserted = True
                    break
            if not inserted:
                visible_fields.append(target_field)
            config["visible_fields"] = visible_fields
            changed = True
            print(f"Added {target_field} to visible_fields.")

        # Ensure header mapping is set
        if visible_field_headers.get(target_field) != target_header:
            visible_field_headers[target_field] = target_header
            config["visible_field_headers"] = visible_field_headers
            changed = True
            print(f"Mapped {target_field} to header {target_header} in visible_field_headers.")

        # Ensure row exists in process_visible_field_rows
        has_row = any(
            isinstance(r, dict) and r.get("field_key") == target_field
            for r in process_visible_field_rows
        )
        if not has_row:
            row_item = {"field_key": target_field, "header_key": target_header}
            # Insert after reference row if possible
            inserted = False
            for ref_key in ["custom_tem_filhos", "whatsapp", "data_nascimento", "email"]:
                ref_idx = next((i for i, r in enumerate(process_visible_field_rows) if isinstance(r, dict) and r.get("field_key") == ref_key), None)
                if ref_idx is not None:
                    process_visible_field_rows.insert(ref_idx + 1, row_item)
                    inserted = True
                    break
            if not inserted:
                process_visible_field_rows.append(row_item)
            config["process_visible_field_rows"] = process_visible_field_rows
            changed = True
            print(f"Added row for {target_field} in process_visible_field_rows.")
        else:
            # Update header if it's empty
            for r in process_visible_field_rows:
                if isinstance(r, dict) and r.get("field_key") == target_field:
                    if r.get("header_key") != target_header:
                        r["header_key"] = target_header
                        config["process_visible_field_rows"] = process_visible_field_rows
                        changed = True
                        print(f"Updated row for {target_field} header to {target_header} in process_visible_field_rows.")

        if changed:
            session.execute(
                text(
                    """
                    UPDATE sidebar_menu_settings
                    SET menu_config = :menu_config
                    WHERE id = :id
                    """
                ),
                {
                    "id": menu_id,
                    "menu_config": json.dumps(config, ensure_ascii=False)
                }
            )
            session.commit()
            print("Successfully updated the database config.")
        else:
            print("The field is already fully configured in the database with the correct header.")

if __name__ == '__main__':
    run()
