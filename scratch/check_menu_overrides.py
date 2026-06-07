from appverbo.db.session import SessionLocal
from sqlalchemy import text
import json

def main():
    keys = ["empresa", "contacto_geral", "departamentos", "ensaio", "adicionar_musica", "contactos", "meu_perfil"]
    with SessionLocal() as session:
        for k in keys:
            row = session.execute(text("SELECT menu_key, menu_label, menu_config FROM sidebar_menu_settings WHERE menu_key = :key"), {"key": k}).fetchone()
            if row:
                print(f"Key: {row[0]} | Label: {row[1]}")
                cfg = json.loads(row[2]) if isinstance(row[2], str) else row[2]
                print(f"  Sidebar Section: {cfg.get('sidebar_section')}")
                print(f"  Overrides: {json.dumps(cfg.get('entity_scoped_overrides_v1'), indent=2)}")
            else:
                print(f"Key: {k} | NOT FOUND")
            print("-" * 50)

if __name__ == '__main__':
    main()
