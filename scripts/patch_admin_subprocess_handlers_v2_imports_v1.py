from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path


####################################################################################
# (1) CONFIGURACAO
####################################################################################

PROJECT_ROOT = Path.cwd()

HANDLER_PATH = PROJECT_ROOT / "appverbo" / "routes" / "profile" / "admin_subprocess_handlers_v2.py"


####################################################################################
# (2) FUNCOES AUXILIARES
####################################################################################

def now_stamp_v1() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def read_text_v1(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text_v1(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def backup_file_v1(path: Path, suffix: str) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"Ficheiro nao encontrado para backup: {path}")

    backup_path = path.with_name(path.name + f".bak_{suffix}_{now_stamp_v1()}")
    shutil.copy2(path, backup_path)
    return backup_path


def require_file_v1(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Ficheiro obrigatorio nao encontrado: {path}")


####################################################################################
# (3) PATCH IMPORTS EXPLICITOS
####################################################################################

def patch_imports_v1() -> None:
    content = read_text_v1(HANDLER_PATH)

    required_anchor = "from appverbo.core import *  # noqa: F403,F401\n"

    if required_anchor not in content:
        raise RuntimeError("Nao encontrei import de appverbo.core em admin_subprocess_handlers_v2.py.")

    import_block = """from appverbo.services.auth import is_admin_user
from appverbo.services.session import get_current_user
"""

    if "from appverbo.services.session import get_current_user" not in content:
        content = content.replace(required_anchor, required_anchor + import_block, 1)

    if "from appverbo.services.auth import is_admin_user" not in content:
        content = content.replace(required_anchor, required_anchor + "from appverbo.services.auth import is_admin_user\n", 1)

    required = [
        "from appverbo.services.session import get_current_user",
        "from appverbo.services.auth import is_admin_user",
        "def get_current_admin_user_or_redirect_v2",
    ]

    missing = [marker for marker in required if marker not in content]

    if missing:
        raise RuntimeError("Marcadores ausentes em admin_subprocess_handlers_v2.py: " + ", ".join(missing))

    write_text_v1(HANDLER_PATH, content)


####################################################################################
# (4) VALIDAR
####################################################################################

def validate_v1() -> None:
    content = read_text_v1(HANDLER_PATH)

    if "from appverbo.services.session import get_current_user" not in content:
        raise RuntimeError("Import get_current_user nao encontrado.")

    if "from appverbo.services.auth import is_admin_user" not in content:
        raise RuntimeError("Import is_admin_user nao encontrado.")

    print("OK: get_current_user importado explicitamente.")
    print("OK: is_admin_user importado explicitamente.")
    print("OK: handler V2 deixa de depender de import wildcard para autenticacao.")


####################################################################################
# (5) EXECUCAO
####################################################################################

def main() -> None:
    require_file_v1(HANDLER_PATH)

    backup_path = backup_file_v1(HANDLER_PATH, "imports_v1")
    print(f"OK: backup criado: {backup_path}")

    patch_imports_v1()
    validate_v1()

    print("OK: patch imports handlers V2 concluido.")


if __name__ == "__main__":
    main()
