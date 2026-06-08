
# ##################################################################################
# QUERY: Inspecionar estrutura de menus / processos relacionados com Tesouraria
# ##################################################################################
from appverbo.core import SessionLocal
from sqlalchemy import text
import json

def main():
    with SessionLocal() as session:

        # (1) COLUNAS DA TABELA sidebar_menu_settings
        cols = session.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='sidebar_menu_settings' ORDER BY ordinal_position"
        )).fetchall()
        print("=== COLUNAS sidebar_menu_settings ===")
        for c in cols:
            print(" ", c[0])

        # (2) TODOS OS MENU_KEY
        rows = session.execute(text(
            "SELECT menu_key FROM sidebar_menu_settings ORDER BY menu_key"
        )).fetchall()
        print("\n=== MENU KEYS ===")
        for r in rows:
            print(" ", r[0])

        # (3) CONFIG DE TESOURARIA (se existir)
        row = session.execute(text(
            "SELECT menu_key, menu_config FROM sidebar_menu_settings "
            "WHERE menu_key ILIKE '%tesouraria%' OR menu_key ILIKE '%extrato%'"
        )).fetchall()
        print("\n=== CONFIG TESOURARIA/EXTRATO ===")
        for r in row:
            print(f"\n--- {r[0]} ---")
            try:
                cfg = json.loads(r[1]) if r[1] else {}
                print(json.dumps(cfg, indent=2, ensure_ascii=False))
            except Exception as e:
                print("Erro ao parsear:", e)
                print(r[1])

        # (4) TABELAS COM "process" no nome
        tbls = session.execute(text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema='public' AND table_name ILIKE '%process%' ORDER BY table_name"
        )).fetchall()
        print("\n=== TABELAS COM 'process' ===")
        for t in tbls:
            print(" ", t[0])

        # (5) TABELAS COM "field" no nome
        tbls2 = session.execute(text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema='public' AND table_name ILIKE '%field%' ORDER BY table_name"
        )).fetchall()
        print("\n=== TABELAS COM 'field' ===")
        for t in tbls2:
            print(" ", t[0])

if __name__ == '__main__':
    main()
