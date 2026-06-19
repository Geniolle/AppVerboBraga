from appverbo.db.session import SessionLocal
from sqlalchemy import text

with SessionLocal() as s:
    # Ver todas as colunas da tabela users
    cols = s.execute(text("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'users'
        ORDER BY ordinal_position
    """)).fetchall()
    print("Colunas de users:", [(c[0], c[1]) for c in cols])

    # Ver todos os utilizadores sem filtro
    rows = s.execute(text("SELECT * FROM users ORDER BY id")).fetchall()
    print(f"\nTotal rows em users: {len(rows)}")
    for r in rows:
        print(f"  {dict(zip([c[0] for c in cols], r))}")
