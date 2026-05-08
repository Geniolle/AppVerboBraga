from appverbo.core import SessionLocal
from sqlalchemy import text

def run():
    with SessionLocal() as session:
        result = session.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'"))
        tables = [r[0] for r in result.fetchall()]
        
        for table in tables:
            try:
                result = session.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name='{table}' AND data_type IN ('text', 'character varying')"))
                columns = [r[0] for r in result.fetchall()]
                
                for col in columns:
                    try:
                        result = session.execute(text(f"SELECT * FROM {table} WHERE {col} ILIKE '%Empresa%'"))
                        rows = result.fetchall()
                        if rows:
                            print(f'Found Empresa in {table}.{col}: {rows}')
                    except Exception as e:
                        pass
            except Exception as e:
                pass

if __name__ == '__main__':
    run()
