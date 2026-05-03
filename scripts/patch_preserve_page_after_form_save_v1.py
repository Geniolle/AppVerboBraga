from __future__ import annotations

import re
import shutil
from datetime import datetime
from pathlib import Path


####################################################################################
# (1) CONFIGURACAO
####################################################################################

PROJECT_ROOT = Path.cwd()

NEW_USER_JS_PATH = PROJECT_ROOT / "static" / "js" / "new_user.js"
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
        raise FileNotFoundError(f"Ficheiro nao encontrado: {path}")

    backup_path = path.with_name(path.name + f".bak_{suffix}_{now_stamp_v1()}")
    shutil.copy2(path, backup_path)
    return backup_path


def require_file_v1(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Ficheiro obrigatorio nao encontrado: {path}")


####################################################################################
# (3) NOVO BLOCO DE NAVEGACAO
####################################################################################

NAVIGATION_BLOCK_V1 = r'''// APPVERBO_FORM_SAVE_NAVIGATION_GUARD_V1_START
const APPVERBO_FORM_SAVE_NAVIGATION_MARKER_V1 = "appverbo:form-save-navigation-v1";

function readAndClearAppVerboFormSaveNavigationMarkerV1() {
  try {
    const markerValue = window.sessionStorage.getItem(APPVERBO_FORM_SAVE_NAVIGATION_MARKER_V1) || "";
    if (markerValue) {
      window.sessionStorage.removeItem(APPVERBO_FORM_SAVE_NAVIGATION_MARKER_V1);
    }
    return markerValue;
  } catch (error) {
    return "";
  }
}

function markAppVerboFormSaveNavigationV1(form) {
  if (!form) {
    return;
  }

  const method = String(form.getAttribute("method") || form.method || "").trim().toLowerCase();

  if (method && method !== "post") {
    return;
  }

  try {
    window.sessionStorage.setItem(APPVERBO_FORM_SAVE_NAVIGATION_MARKER_V1, "1");

    window.setTimeout(() => {
      try {
        if (document.visibilityState !== "hidden") {
          window.sessionStorage.removeItem(APPVERBO_FORM_SAVE_NAVIGATION_MARKER_V1);
        }
      } catch (error) {
        // Ignora falhas de sessionStorage.
      }
    }, 5000);
  } catch (error) {
    // Ignora falhas de sessionStorage.
  }
}

document.addEventListener("submit", (event) => {
  markAppVerboFormSaveNavigationV1(event.target);
}, true);

document.addEventListener("click", (event) => {
  const submitControl = event.target && event.target.closest
    ? event.target.closest("button[type='submit'], input[type='submit'], button:not([type])")
    : null;

  if (!submitControl || !submitControl.form) {
    return;
  }

  markAppVerboFormSaveNavigationV1(submitControl.form);
}, true);

const appverboFormSaveNavigationMarkerV1 = readAndClearAppVerboFormSaveNavigationMarkerV1();

const navigationEntries = (
  typeof window !== "undefined" &&
  window.performance &&
  typeof window.performance.getEntriesByType === "function"
)
  ? window.performance.getEntriesByType("navigation")
  : [];
const navigationType = navigationEntries.length
  ? String(navigationEntries[0].type || "")
  : "";

if (
  navigationType === "reload" &&
  window.location.pathname === "/users/new" &&
  appverboFormSaveNavigationMarkerV1 !== "1"
) {
  const homeUrl = "/users/new?menu=home";
  const currentPathAndQuery = `${window.location.pathname}${window.location.search}`;
  if (currentPathAndQuery !== homeUrl || window.location.hash) {
    window.location.replace(homeUrl);
  }
}
// APPVERBO_FORM_SAVE_NAVIGATION_GUARD_V1_END'''


####################################################################################
# (4) PATCH DO new_user.js
####################################################################################

def patch_new_user_js_v1() -> None:
    content = read_text_v1(NEW_USER_JS_PATH)

    if "const bootstrap = window.__APPVERBO_BOOTSTRAP__ || {};" not in content:
        raise RuntimeError("Marcador const bootstrap nao encontrado no new_user.js.")

    existing_marker_pattern = re.compile(
        r"// APPVERBO_FORM_SAVE_NAVIGATION_GUARD_V1_START.*?// APPVERBO_FORM_SAVE_NAVIGATION_GUARD_V1_END\s*",
        flags=re.DOTALL,
    )

    if existing_marker_pattern.search(content):
        content = existing_marker_pattern.sub(NAVIGATION_BLOCK_V1 + "\n\n", content)
    else:
        old_navigation_pattern = re.compile(
            r"^const navigationEntries = \([\s\S]*?\n"
            r"if \(navigationType === \"reload\" && window\.location\.pathname === \"/users/new\"\) \{\n"
            r"[\s\S]*?\n"
            r"\}\n\n",
            flags=re.MULTILINE,
        )

        if not old_navigation_pattern.search(content):
            raise RuntimeError("Bloco antigo de navigation reload nao encontrado no new_user.js.")

        content = old_navigation_pattern.sub(NAVIGATION_BLOCK_V1 + "\n\n", content, count=1)

    required_markers = [
        "APPVERBO_FORM_SAVE_NAVIGATION_GUARD_V1_START",
        "APPVERBO_FORM_SAVE_NAVIGATION_MARKER_V1",
        "markAppVerboFormSaveNavigationV1",
        "appverboFormSaveNavigationMarkerV1 !== \"1\"",
        "navigationType === \"reload\"",
    ]

    missing = [
        marker for marker in required_markers
        if marker not in content
    ]

    if missing:
        raise RuntimeError("Marcadores ausentes no new_user.js: " + ", ".join(missing))

    write_text_v1(NEW_USER_JS_PATH, content)


####################################################################################
# (5) PATCH CACHE BUSTER
####################################################################################

def patch_template_v1() -> None:
    content = read_text_v1(TEMPLATE_PATH)

    if "new_user.js" not in content:
        raise RuntimeError("new_user.js nao encontrado no template.")

    content = re.sub(
        r'new_user\.js\?v=[^"]+',
        "new_user.js?v=20260503-preserve-page-after-form-save-v1",
        content,
    )

    if "new_user.js?v=20260503-preserve-page-after-form-save-v1" not in content:
        raise RuntimeError("Cache buster do new_user.js nao foi atualizado.")

    write_text_v1(TEMPLATE_PATH, content)


####################################################################################
# (6) VALIDAR CONTEUDO
####################################################################################

def validate_v1() -> None:
    js_content = read_text_v1(NEW_USER_JS_PATH)
    template_content = read_text_v1(TEMPLATE_PATH)

    required_js_markers = [
        "APPVERBO_FORM_SAVE_NAVIGATION_GUARD_V1_START",
        "readAndClearAppVerboFormSaveNavigationMarkerV1",
        "document.addEventListener(\"submit\"",
        "document.addEventListener(\"click\"",
        "appverboFormSaveNavigationMarkerV1 !== \"1\"",
        "window.location.replace(homeUrl)",
    ]

    missing_js = [
        marker for marker in required_js_markers
        if marker not in js_content
    ]

    if missing_js:
        raise RuntimeError("Marcadores ausentes no JS: " + ", ".join(missing_js))

    if "new_user.js?v=20260503-preserve-page-after-form-save-v1" not in template_content:
        raise RuntimeError("Cache buster esperado nao encontrado no template.")

    print("OK: guarda de navegacao apos submit adicionada.")
    print("OK: reload manual continua a redirecionar para Home.")
    print("OK: cache buster atualizado.")


####################################################################################
# (7) EXECUCAO
####################################################################################

def main() -> None:
    require_file_v1(NEW_USER_JS_PATH)
    require_file_v1(TEMPLATE_PATH)

    js_backup = backup_file_v1(NEW_USER_JS_PATH, "preserve_page_after_form_save_v1")
    template_backup = backup_file_v1(TEMPLATE_PATH, "preserve_page_after_form_save_v1")

    print(f"OK: backup criado: {js_backup}")
    print(f"OK: backup criado: {template_backup}")

    patch_new_user_js_v1()
    patch_template_v1()
    validate_v1()

    print("OK: patch preserve page after form save concluido.")


if __name__ == "__main__":
    main()
