from __future__ import annotations

from sqlalchemy import inspect, text

from appverbo.db.session import SessionLocal, engine

replacements = {
    "ConfiguraÃ§Ã£o dos campos": "Configuração dos campos",
    "ConfiguraÃ§Ãµes": "Configurações",
    "ConfiguraÃ§Ã£o": "Configuração",
    "CabeÃ§alho": "Cabeçalho",
    "Sem cabeÃ§alho": "Sem cabeçalho",
    "DefiniÃ§Ãµes": "Definições",
    "sÃ³": "só",
    "AÃ‡Ã•ES": "AÇÕES",
    "pÃ¡gina": "página",
    "Ãšltimas entidades criadas": "Entidades criadas",
}

targets = {
    "sidebar_menu_settings": ["menu_label", "menu_config"],
    "app_modules": ["module_name", "description", "menu_group", "icon"],
    "sidebar_menu_items": ["group_key", "item_key", "label", "icon"],
}

inspector = inspect(engine)
existing_tables = set(inspector.get_table_names())

changed = []

with SessionLocal() as session:
    for table_name, columns in targets.items():
        if table_name not in existing_tables:
            continue

        rows = session.execute(
            text(f"SELECT id, {', '.join(columns)} FROM {table_name} ORDER BY id")
        ).mappings().all()

        for row in rows:
            updates = {}

            for column in columns:
                old_value = row.get(column)

                if old_value is None:
                    continue

                new_value = str(old_value)

                for wrong_text, correct_text in replacements.items():
                    new_value = new_value.replace(wrong_text, correct_text)

                new_value = new_value.replace("campos_adicionais", "campos-adicionais")

                if new_value != old_value:
                    updates[column] = new_value

            if not updates:
                continue

            set_clause = ", ".join([f"{column} = :{column}" for column in updates])
            params = dict(updates)
            params["id"] = row["id"]

            session.execute(
                text(f"UPDATE {table_name} SET {set_clause} WHERE id = :id"),
                params,
            )

            changed.append(f"{table_name}[id={row['id']}]")

    session.commit()

print("Registos corrigidos no banco:")
if changed:
    for item in changed:
        print(f"- {item}")
else:
    print("- Nenhum")
