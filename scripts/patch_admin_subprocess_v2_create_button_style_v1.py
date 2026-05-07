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

STYLE_START = "/* APPVERBO_ADMIN_SUBPROCESS_V2_CREATE_BUTTON_STYLE_V1_START */"
STYLE_END = "/* APPVERBO_ADMIN_SUBPROCESS_V2_CREATE_BUTTON_STYLE_V1_END */"


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
# (3) PATCH CSS DO BOTAO CRIAR ENTIDADE V2
####################################################################################

CSS_BLOCK = r'''
/* APPVERBO_ADMIN_SUBPROCESS_V2_CREATE_BUTTON_STYLE_V1_START */

/*
  Botao "Criar entidade" do Admin Subprocess V2.
  Deve seguir o mesmo tamanho/formatação textual do botão legado.
*/
.admin-subprocess-create-collapse-v2 > summary {
  min-width: 112px;
  width: auto;
  min-height: 38px;
  height: 38px;
  padding: 0 14px;
  box-sizing: border-box;
  font-family: inherit;
  font-size: 13px;
  line-height: 1;
  font-weight: 700;
  letter-spacing: 0;
  white-space: nowrap;
}

/* APPVERBO_ADMIN_SUBPROCESS_V2_CREATE_BUTTON_STYLE_V1_END */
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
        "admin_subprocesses_v2.css?v=20260507-create-button-style-v1",
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
        ".admin-subprocess-create-collapse-v2 > summary",
        "font-size: 13px",
        "font-weight: 700",
        "height: 38px",
        "line-height: 1",
    ]

    missing_css = [marker for marker in required_css if marker not in css_content]

    if missing_css:
        raise RuntimeError("Marcadores ausentes no CSS V2: " + ", ".join(missing_css))

    if "admin_subprocesses_v2.css?v=20260507-create-button-style-v1" not in new_user_content:
        raise RuntimeError("Cache buster CSS V2 nao atualizado em new_user.html.")

    if "admin_subprocesses_v2.css?v=20260507-create-button-style-v1" not in standalone_content:
        raise RuntimeError("Cache buster CSS V2 nao atualizado em admin_subprocess_v2_standalone.html.")

    print("OK: estilo do botao Criar entidade V2 aplicado.")
    print("OK: botao V2 usa tamanho/formatação textual compatível com o botão legado.")
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
        backup_path = backup_file_v1(path, "admin_subprocess_v2_create_button_style_v1")
        print(f"OK: backup criado: {backup_path}")

    patch_css_v1()
    patch_cache_buster_v1(NEW_USER_TEMPLATE_PATH)
    patch_cache_buster_v1(STANDALONE_TEMPLATE_PATH)
    validate_v1()

    print("OK: patch do botao Criar entidade V2 concluido.")


if __name__ == "__main__":
    main()
