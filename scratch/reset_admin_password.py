# ###################################################################################
# (1) RESET ADMIN PASSWORD
# ###################################################################################
from appverbo.core import SessionLocal
from appverbo.models.user import User
from appverbo.services.auth import hash_password

with SessionLocal() as session:
    admin = session.query(User).filter_by(login_email="admin@appverbo.local").first()
    if admin:
        admin.password_hash = hash_password("admin")
        session.commit()
        print("Admin password updated to 'admin'")
    else:
        print("Admin user not found")
