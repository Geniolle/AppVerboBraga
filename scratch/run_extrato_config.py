import sys, os, json
sys.path.append('/app')
from appverbo.core import SessionLocal
from sqlalchemy import text

def main():
    with SessionLocal() as session:
        rows = session.execute(text("SELECT menu_key, menu_config FROM sidebar_menu_settings WHERE menu_key ILIKE '%extrato%'")).fetchall()
        if not rows:
            print('Nenhum registro encontrado para extrato')
        for r in rows:
            print('Key:', r[0])
            try:
                cfg = json.loads(r[1])
                print(json.dumps(cfg, indent=2, ensure_ascii=False))
            except Exception as e:
                print('Parse error', e)
                print(r[1])

if __name__ == '__main__':
    main()
