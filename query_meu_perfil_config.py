from appverbo.core import SessionLocal
from appverbo.models import Member
from sqlalchemy import select
import json

def run():
    with SessionLocal() as session:
        members = session.execute(select(Member)).scalars().all()
        print(f"Total members: {len(members)}")
        for m in members:
            print(f"ID: {m.id} | Name: {m.full_name} | Custom Fields:")
            try:
                cf = json.loads(m.profile_custom_fields or "{}")
                print(json.dumps(cf, indent=2, ensure_ascii=False))
            except Exception as e:
                print(f"  Raw: {m.profile_custom_fields} (Error: {e})")

if __name__ == '__main__':
    run()
