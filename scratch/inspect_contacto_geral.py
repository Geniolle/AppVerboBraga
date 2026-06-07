# ###################################################################################
# INSPECT CONTACTO_GERAL CONFIG
# ###################################################################################
import json
from appverbo.db.session import SessionLocal
from sqlalchemy import text

def main():
    with SessionLocal() as session:
        row = session.execute(text("select menu_config from sidebar_menu_settings where menu_key='contacto_geral'")).scalar()
        if not row:
            print("No menu config found for contacto_geral.")
            return
        
        try:
            config = json.loads(row) if isinstance(row, str) else row
            print(json.dumps(config, indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"Error parsing: {e}")
            print(row)

if __name__ == "__main__":
    main()
