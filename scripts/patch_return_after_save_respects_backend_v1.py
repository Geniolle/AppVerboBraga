from __future__ import annotations

import re
import shutil
from datetime import datetime
from pathlib import Path


####################################################################################
# (1) CONFIGURACAO
####################################################################################

PROJECT_ROOT = Path.cwd()

RETURN_AFTER_SAVE_PATH = PROJECT_ROOT / "static" / "js" / "modules" / "return_after_save.js"
TEMPLATE_PATH = PROJECT_ROOT / "templates" / "new_user.html"


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
# (3) PATCH DO return_after_save.js
####################################################################################

def patch_return_after_save_v1() -> None:
    content = read_text_v1(RETURN_AFTER_SAVE_PATH)

    required_markers = [
        "const STORAGE_KEY",
        "function restoreAfterSave()",
        "sessionStorage.removeItem(STORAGE_KEY);",
        "window.location.replace(finalUrl);",
    ]

    missing = [
        marker for marker in required_markers
        if marker not in content
    ]

    if missing:
        raise RuntimeError("Marcadores ausentes em return_after_save.js: " + ", ".join(missing))

    if "function isBackendPostSaveReturnUrl" not in content:
        helper_anchor = """  function mergeMessageParams(targetUrl, currentUrl) {
"""
        helper_block = """  function isBackendPostSaveReturnUrl(value) {
    try {
      const url = new URL(String(value || ""), window.location.origin);
      return url.searchParams.get("appverbo_after_save") === "1";
    } catch (error) {
      return false;
    }
  }

"""

        if helper_anchor not in content:
            raise RuntimeError("Nao encontrei ponto para inserir isBackendPostSaveReturnUrl.")

        content = content.replace(helper_anchor, helper_block + helper_anchor, 1)

    old_block = """    sessionStorage.removeItem(STORAGE_KEY);
    sessionStorage.removeItem(STORAGE_TIME_KEY);

    if (!savedUrl || !savedTime) {
      return;
    }
"""

    new_block = """    sessionStorage.removeItem(STORAGE_KEY);
    sessionStorage.removeItem(STORAGE_TIME_KEY);

    //###################################################################################
    // (5.1) BACKEND COMO FONTE DE VERDADE POS-SAVE
    //###################################################################################
    // Quando o backend ja devolveu appverbo_after_save=1, a pagina atual e a correta.
    // Nao devemos restaurar URL antiga do sessionStorage, pois ela pode ter sido capturada
    // antes da navegacao interna do menu lateral e apontar para menu=home.
    if (isBackendPostSaveReturnUrl(currentUrl)) {
      return;
    }

    if (!savedUrl || !savedTime) {
      return;
    }
"""

    if old_block in content:
        content = content.replace(old_block, new_block, 1)
    elif "BACKEND COMO FONTE DE VERDADE POS-SAVE" not in content:
        raise RuntimeError("Nao encontrei bloco de limpeza de sessionStorage em restoreAfterSave.")

    write_text_v1(RETURN_AFTER_SAVE_PATH, content)


####################################################################################
# (4) PATCH CACHE BUSTER DO TEMPLATE
####################################################################################

def patch_template_v1() -> None:
    content = read_text_v1(TEMPLATE_PATH)

    if "return_after_save.js" not in content:
        raise RuntimeError("return_after_save.js nao encontrado no template.")

    content = re.sub(
        r'return_after_save\.js\?v=[^"]+',
        "return_after_save.js?v=20260503-respect-backend-post-save-v1",
        content,
    )

    if "return_after_save.js?v=20260503-respect-backend-post-save-v1" not in content:
        raise RuntimeError("Cache buster do return_after_save.js nao foi atualizado.")

    write_text_v1(TEMPLATE_PATH, content)


####################################################################################
# (5) VALIDAR CONTEUDO
####################################################################################

def validate_v1() -> None:
    js_content = read_text_v1(RETURN_AFTER_SAVE_PATH)
    template_content = read_text_v1(TEMPLATE_PATH)

    required_js = [
        "function isBackendPostSaveReturnUrl",
        "appverbo_after_save",
        "BACKEND COMO FONTE DE VERDADE POS-SAVE",
        "if (isBackendPostSaveReturnUrl(currentUrl))",
        "window.location.replace(finalUrl);",
    ]

    missing_js = [
        marker for marker in required_js
        if marker not in js_content
    ]

    if missing_js:
        raise RuntimeError("Marcadores ausentes em return_after_save.js: " + ", ".join(missing_js))

    if "return_after_save.js?v=20260503-respect-backend-post-save-v1" not in template_content:
        raise RuntimeError("Cache buster esperado nao encontrado no template.")

    print("OK: return_after_save.js deixa de sobrescrever retorno correto do backend.")
    print("OK: se appverbo_after_save=1 estiver na URL, nao redireciona para URL antiga.")
    print("OK: cache buster atualizado.")


####################################################################################
# (6) EXECUCAO
####################################################################################

def main() -> None:
    require_file_v1(RETURN_AFTER_SAVE_PATH)
    require_file_v1(TEMPLATE_PATH)

    js_backup = backup_file_v1(RETURN_AFTER_SAVE_PATH, "respect_backend_post_save_v1")
    template_backup = backup_file_v1(TEMPLATE_PATH, "respect_backend_post_save_v1")

    print(f"OK: backup criado: {js_backup}")
    print(f"OK: backup criado: {template_backup}")

    patch_return_after_save_v1()
    patch_template_v1()
    validate_v1()

    print("OK: patch return_after_save concluido.")


if __name__ == "__main__":
    main()
