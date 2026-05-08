from appverbo.core import SessionLocal
from sqlalchemy import text
import json

def run():
    with SessionLocal() as session:
        result = session.execute(text("SELECT menu_key, menu_label, is_active FROM sidebar_menu_settings ORDER BY id ASC"))
        rows = result.fetchall()
        
        print("\n## Menus (sidebar_menu_settings no Postgres)")
        print("| Chave | Nome | Estado |")
        print("|---|---|---|")
        for r in rows:
            status = 'Ativo' if r[2] else 'Inativo'
            print(f"| {r[0]} | {r[1]} | {status} |")

if __name__ == '__main__':
    run()
