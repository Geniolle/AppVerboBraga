import sqlite3

conn = sqlite3.connect('app.db')
c = conn.cursor()

c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in c.fetchall()]

for table in tables:
    try:
        c.execute(f"PRAGMA table_info({table})")
        columns = [r[1] for r in c.fetchall()]
        
        for col in columns:
            try:
                c.execute(f"SELECT * FROM {table} WHERE CAST({col} AS TEXT) LIKE '%Empresa%'")
                rows = c.fetchall()
                if rows:
                    print(f"Found 'Empresa' in table {table}, column {col}:")
                    for row in rows:
                        print(row)
            except Exception as e:
                pass
    except Exception as e:
        pass

conn.close()
