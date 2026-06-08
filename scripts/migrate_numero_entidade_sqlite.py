import sqlite3
from pathlib import Path

DB_PATH = Path("app.db")

if not DB_PATH.exists():
    print("app.db não encontrado. Migração não executada.")
    raise SystemExit(0)

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
tables = [row[0] for row in cursor.fetchall()]

changed_tables = []

for table in tables:
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]

    if "estado" in columns and "numero_entidade" not in columns:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN numero_entidade TEXT NOT NULL DEFAULT ''")
        cursor.execute(
            f"""
            CREATE UNIQUE INDEX IF NOT EXISTS ux_{table}_numero_entidade
            ON {table}(numero_entidade)
            WHERE numero_entidade <> ''
            """
        )
        changed_tables.append(table)

connection.commit()
connection.close()

if changed_tables:
    print("Campo numero_entidade criado nas tabelas:")
    for table in changed_tables:
        print(f"- {table}")
else:
    print("Nenhuma tabela precisou de alteração.")