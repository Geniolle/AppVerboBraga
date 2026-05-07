from __future__ import annotations

import re
import shutil
from datetime import datetime
from pathlib import Path


####################################################################################
# (1) CONFIGURACAO
####################################################################################

PROJECT_ROOT = Path.cwd()

CSS_PATH = PROJECT_ROOT / "static" / "css" / "modules" / "admin_subprocesses_v2.css"
NEW_USER_TEMPLATE_PATH = PROJECT_ROOT / "templates" / "new_user.html"
STANDALONE_TEMPLATE_PATH = PROJECT_ROOT / "templates" / "admin_subprocess_v2_standalone.html"

STYLE_START = "/* APPVERBO_ADMIN_SUBPROCESS_V2_CARD_TITLE_STYLE_V2_START */"
STYLE_END = "/* APPVERBO_ADMIN_SUBPROCESS_V2_CARD_TITLE_STYLE_V2_END */"


####################################################################################
# (2) FUNCOES AUXILIARES
####################################################################################

def now_stamp_v1() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def require_file_v1(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Ficheiro obrigatorio nao encontrado: {path}")


def read_text_v1(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text_v1(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def backup_file_v1(path: Path, suffix: str) -> Path:
    backup_path = path.with_name(path.name + f".bak_{suffix}_{now_stamp_v1()}")
    shutil.copy2(path, backup_path)
    return backup_path


####################################################################################
# (3) PATCH CSS DOS TITULOS
####################################################################################

CSS_BLOCK = r'''
/* APPVERBO_ADMIN_SUBPROCESS_V2_CARD_TITLE_STYLE_V2_START */

/*
  Títulos dos cards V2 no padrão visual do "Acesso rápido":
  - usado em Entidades ativas
  - usado em Entidades inativas
  - reutilizável para outros subprocessos V2
*/
.admin-subprocess-table-card-v2 > h2,
.admin-subprocess-table-card-v2 .admin-subprocess-table-header-v2 > h2 {
  margin: 0;
  color: #0f2940;
  font-size: 1.125rem;
  line-height: 1.25;
  font-weight: 700;
  letter-spacing: -0.01em;
}

.admin-subprocess-table-header-v2 {
  align-items: center;
}

/* APPVERBO_ADMIN_SUBPROCESS_V2_CARD_TITLE_STYLE_V2_END */
'''


def patch_css_v1() -> None:
    content = read_text_v1(CSS_PATH)

    pattern = re.compile(
        re.escape(STYLE_START) + r".*?" + re.escape(STYLE_END),
        flags=re.DOTALL,
    )

    if pattern.search(content):
        content = pattern.sub(lambda _match: CSS_BLOCK.strip(), content)
    else:
        content = content.rstrip() + "\n\n" + CSS_BLOCK.strip() + "\n"

    write_text_v1(CSS_PATH, content)


####################################################################################
# (4) ATUALIZAR CACHE BUSTER DO CSS V2
####################################################################################

def patch_cache_buster_v1(path: Path) -> None:
    content = read_text_v1(path)

    if "admin_subprocesses_v2.css" not in content:
        print(f"AVISO: {path} nao referencia admin_subprocesses_v2.css")
        return

    content = re.sub(
        r'admin_subprocesses_v2\.css\?v=[^"]+',
        "admin_subprocesses_v2.css?v=20260507-card-title-style-v2",
        content,
    )

    write_text_v1(path, content)


####################################################################################
# (5) VALIDAR
####################################################################################

def validate_v1() -> None:
    css_content = read_text_v1(CSS_PATH)
    new_user_content = read_text_v1(NEW_USER_TEMPLATE_PATH)
    standalone_content = read_text_v1(STANDALONE_TEMPLATE_PATH)

    required_css = [
        STYLE_START,
        STYLE_END,
        ".admin-subprocess-table-card-v2 > h2",
        ".admin-subprocess-table-card-v2 .admin-subprocess-table-header-v2 > h2",
        "font-size: 1.125rem",
        "font-weight: 700",
        "color: #0f2940",
    ]

    missing_css = [marker for marker in required_css if marker not in css_content]

    if missing_css:
        raise RuntimeError("Marcadores ausentes no CSS V2: " + ", ".join(missing_css))

    if "admin_subprocesses_v2.css?v=20260507-card-title-style-v2" not in new_user_content:
        raise RuntimeError("Cache buster CSS V2 nao atualizado em new_user.html.")

    if "admin_subprocesses_v2.css?v=20260507-card-title-style-v2" not in standalone_content:
        raise RuntimeError("Cache buster CSS V2 nao atualizado em admin_subprocess_v2_standalone.html.")

    print("OK: estilo dos titulos dos cards V2 aplicado.")
    print("OK: Entidades ativas/inativas usam fonte no padrao Acesso rapido.")
    print("OK: cache buster CSS atualizado.")


####################################################################################
# (6) EXECUCAO
####################################################################################

def main() -> None:
    required_files = [
        CSS_PATH,
        NEW_USER_TEMPLATE_PATH,
        STANDALONE_TEMPLATE_PATH,
    ]

    for path in required_files:
        require_file_v1(path)
        backup_path = backup_file_v1(path, "admin_subprocess_v2_card_titles_css_v2")
        print(f"OK: backup criado: {backup_path}")

    patch_css_v1()
    patch_cache_buster_v1(NEW_USER_TEMPLATE_PATH)
    patch_cache_buster_v1(STANDALONE_TEMPLATE_PATH)
    validate_v1()

    print("OK: patch CSS dos titulos dos cards V2 concluido.")


if __name__ == "__main__":
    main()
