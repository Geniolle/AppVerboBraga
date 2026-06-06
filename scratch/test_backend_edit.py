# ###################################################################################
# (1) DIAGNOSE BACKEND SESSION EDIT STATE
# ###################################################################################
import sys
from appverbo.core import SessionLocal
from appverbo.admin_subprocesses.registry import get_admin_subprocess_config
from appverbo.admin_subprocesses.runtime import build_admin_subprocess_state_from_repository
from appverbo.models.user import User

def test():
    with SessionLocal() as session:
        # Load user
        admin = session.query(User).filter_by(login_email="admin@appverbo.local").first()
        if not admin:
            print("Admin user not found")
            return
            
        config = get_admin_subprocess_config("sessoes")
        if not config:
            print("Config for sessoes not found")
            return
            
        keys_to_test = ["sistema", "geral", "tesouraria", "clayton"]
        for key in keys_to_test:
            print(f"Testing edit_key: '{key}'")
            state = build_admin_subprocess_state_from_repository(
                config=config,
                session=session,
                edit_key=key,
                success="",
                error="",
                return_url="/users/new",
                context={
                    "current_user": {
                        "id": admin.id,
                        "login_email": admin.login_email,
                    },
                    "selected_entity_id": 2, # entity ID from database
                    "allowed_entity_ids": [2],
                    "can_manage_all_entities": True,
                    "current_entity_scope": "all",
                }
            )
            if state:
                print(f"  Result: is_editing={state.is_editing} | edit_key={state.edit_key} | edit_data={state.edit_data is not None}")
            else:
                print("  Result: State is None")

if __name__ == '__main__':
    test()
