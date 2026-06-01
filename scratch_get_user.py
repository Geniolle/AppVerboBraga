from appverbo.core import SessionLocal
from appverbo.models import User
from sqlalchemy import select

def run():
    with SessionLocal() as session:
        users = session.execute(select(User)).scalars().all()
        for u in users:
            print(f"ID: {u.id} | Email: {u.login_email} | Member ID: {u.member_id} | Status: {u.account_status}")

if __name__ == '__main__':
    run()
