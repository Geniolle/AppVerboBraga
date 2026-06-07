from appverbo.core import SessionLocal
from sqlalchemy import text

def main():
    with SessionLocal() as session:
        res = session.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")).all()
        print("Tables:")
        print([r[0] for r in res])

if __name__ == '__main__':
    main()
