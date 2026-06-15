from appverbo.db.session import SessionLocal
from appverbo.admin_subprocesses.repositories.profile_repository import ProfileAdminRepository
from appverbo.admin_subprocesses.registry import get_admin_subprocess_config

config = get_admin_subprocess_config("perfil")
repo = ProfileAdminRepository(config)

with SessionLocal() as s:
    rows = repo.list_rows(s)
    print("Profiles found:", len(rows))
    for r in rows[:10]:
        print(" -", r["id"], r["name"], r["visibility_scope_mode"], r["status"])
