from appverbo.core import SessionLocal
from appverbo.services.page import get_page_data
import json

def run():
    with SessionLocal() as session:
        data = get_page_data(session=session, actor_user_id=1)
        print("profile_personal_field_section_map:")
        print(json.dumps(data.get("profile_personal_field_section_map", {}), indent=2, ensure_ascii=False))

if __name__ == '__main__':
    run()
