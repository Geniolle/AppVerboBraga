from appverbo.db.session import SessionLocal
from sqlalchemy import text
import json

def main():
    keys = ["empresa", "contacto_geral", "departamentos", "ensaio", "adicionar_musica", "contactos", "meu_perfil"]
    
    with SessionLocal() as session:
        # 1. Update sidebar_menu_settings
        print("=== UPDATING SIDEBAR MENU SETTINGS ===")
        for k in keys:
            row = session.execute(
                text("SELECT menu_config FROM sidebar_menu_settings WHERE menu_key = :key"), 
                {"key": k}
            ).fetchone()
            
            if row and row[0]:
                cfg = json.loads(row[0]) if isinstance(row[0], str) else row[0]
                overrides = cfg.get("entity_scoped_overrides_v1")
                
                # If there's an override for Entity 8, remove it
                if overrides and "8" in overrides:
                    print(f"Removing Entity 8 override for: {k}")
                    del overrides["8"]
                    cfg["entity_scoped_overrides_v1"] = overrides
                    
                    session.execute(
                        text("UPDATE sidebar_menu_settings SET menu_config = :cfg WHERE menu_key = :key"),
                        {"cfg": json.dumps(cfg, ensure_ascii=False), "key": k}
                    )
            else:
                print(f"Key: {k} | No row or config found.")
        
        # 2. Update admin_definitions
        print("\n=== UPDATING ADMIN DEFINITIONS ===")
        # Find count first
        count = session.execute(
            text("SELECT count(*) FROM admin_definitions WHERE process_name IN ('Dados gerais', 'Igreja')")
        ).scalar()
        print(f"Found {count} admin_definitions to update to entity_id = 19.")
        
        result = session.execute(
            text("UPDATE admin_definitions SET entity_id = 19 WHERE process_name IN ('Dados gerais', 'Igreja')")
        )
        print(f"Updated {result.rowcount} rows in admin_definitions.")
        
        session.commit()
        print("\nDatabase changes committed successfully!")

if __name__ == '__main__':
    main()
