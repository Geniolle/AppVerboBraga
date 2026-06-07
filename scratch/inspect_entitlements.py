from appverbo.core import SessionLocal
from sqlalchemy import text

def main():
    with SessionLocal() as session:
        print("=== APP_MODULES ===")
        modules = session.execute(text("SELECT * FROM app_modules")).mappings().all()
        for m in modules:
            print(dict(m))
            
        print("\n=== ENTITY_MODULE_ENTITLEMENTS ===")
        entitlements = session.execute(text("SELECT * FROM entity_module_entitlements")).mappings().all()
        for e in entitlements:
            print(dict(e))

if __name__ == '__main__':
    main()
