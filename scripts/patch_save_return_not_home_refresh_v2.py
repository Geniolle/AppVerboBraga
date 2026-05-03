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

START_MARKER = "// APPVERBO_SAVE_RETURN_REFRESH_GUARD_V2_START"
END_MARKER = "// APPVERBO_SAVE_RETURN_REFRESH_GUARD_V2_END"


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
# (3) NOVO BLOCO JS
####################################################################################

NAVIGATION_GUARD_V2 = r'''// APPVERBO_SAVE_RETURN_REFRESH_GUARD_V2_START
//###################################################################################
// (SAVE_RETURN_REFRESH_GUARD_V2) DIFERENCIAR RETORNO DE GRAVACAO DE REFRESH MANUAL
//###################################################################################

function getAppVerboCurrentUrlV2() {
  try {
    return new URL(window.location.href);
  } catch (error) {
    return null;
  }
}

function isAppVerboSaveReturnUrlV2() {
  const url = getAppVerboCurrentUrlV2();

  if (!url) {
    return false;
  }

  if (url.searchParams.get("appverbo_after_save") === "1") {
    return true;
  }

  const feedbackSuffixes = ["_success", "_error"];

  for (const rawKey of url.searchParams.keys()) {
    const key = String(rawKey || "").trim().toLowerCase();

    if (key === "success" || key === "error") {
      return true;
    }

    if (feedbackSuffixes.some((suffix) => key.endsWith(suffix))) {
      return true;
    }
  }

  return false;
}

function clearAppVerboSaveReturnMarkersV2() {
  const url = getAppVerboCurrentUrlV2();

  if (!url) {
    return;
  }

  let changed = false;

  Array.from(url.searchParams.keys()).forEach((rawKey) => {
    const key = String(rawKey || "").trim().toLowerCase();

    if (
      key === "appverbo_after_save" ||
      key === "success" ||
      key === "error" ||
      key.endsWith("_success") ||
      key.endsWith("_error")
    ) {
      url.searchParams.delete(rawKey);
      changed = true;
    }
  });

  if (!changed || !window.history || typeof window.history.replaceState !== "function") {
    return;
  }

  const cleanQuery = url.searchParams.toString();
  const cleanUrl = url.pathname + (cleanQuery ? "?" + cleanQuery : "") + url.hash;

  window.history.replaceState(window.history.state, document.title, cleanUrl);
}

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

const appverboIsSaveReturnUrlV2 = isAppVerboSaveReturnUrlV2();

if (
  navigationType === "reload" &&
  window.location.pathname === "/users/new" &&
  !appverboIsSaveReturnUrlV2
) {
  const homeUrl = "/users/new?menu=home";
  const currentPathAndQuery = `${window.location.pathname}${window.location.search}`;

  if (currentPathAndQuery !== homeUrl || window.location.hash) {
    window.location.replace(homeUrl);
  }
}

if (appverboIsSaveReturnUrlV2) {
  window.setTimeout(clearAppVerboSaveReturnMarkersV2, 250);
}
// APPVERBO_SAVE_RETURN_REFRESH_GUARD_V2_END'''


####################################################################################
# (4) PATCH DO new_user.js
####################################################################################

def patch_new_user_js_v1() -> None:
    content = read_text_v1(NEW_USER_JS_PATH)

    if "const bootstrap = window.__APPVERBO_BOOTSTRAP__ || {};" not in content:
        raise RuntimeError("Marcador const bootstrap nao encontrado no new_user.js.")

    patterns = [
        re.compile(
            r"// APPVERBO_SAVE_RETURN_REFRESH_GUARD_V2_START.*?// APPVERBO_SAVE_RETURN_REFRESH_GUARD_V2_END\s*",
            flags=re.DOTALL,
        ),
        re.compile(
            r"// APPVERBO_FORM_SAVE_NAVIGATION_GUARD_V1_START.*?// APPVERBO_FORM_SAVE_NAVIGATION_GUARD_V1_END\s*",
            flags=re.DOTALL,
        ),
    ]

    replaced = False

    for pattern in patterns:
        if pattern.search(content):
            content = pattern.sub(NAVIGATION_GUARD_V2 + "\n\n", content, count=1)
            replaced = True
            break

    if not replaced:
        old_navigation_pattern = re.compile(
            r"^const navigationEntries = \([\s\S]*?"
            r"if \(navigationType === \"reload\" && window\.location\.pathname === \"/users/new\"\) \{\n"
            r"[\s\S]*?\n"
            r"\}\n\n",
            flags=re.MULTILINE,
        )

        if old_navigation_pattern.search(content):
            content = old_navigation_pattern.sub(NAVIGATION_GUARD_V2 + "\n\n", content, count=1)
            replaced = True

    if not replaced:
        content = content.replace(
            "const bootstrap = window.__APPVERBO_BOOTSTRAP__ || {};",
            NAVIGATION_GUARD_V2 + "\n\nconst bootstrap = window.__APPVERBO_BOOTSTRAP__ || {};",
            1,
        )

    required_markers = [
        "APPVERBO_SAVE_RETURN_REFRESH_GUARD_V2_START",
        "isAppVerboSaveReturnUrlV2",
        "clearAppVerboSaveReturnMarkersV2",
        "appverboIsSaveReturnUrlV2",
        "navigationType === \"reload\"",
        "!appverboIsSaveReturnUrlV2",
    ]

    missing = [
        marker for marker in required_markers
        if marker not in content
    ]

    if missing:
        raise RuntimeError("Marcadores ausentes no new_user.js: " + ", ".join(missing))

    write_text_v1(NEW_USER_JS_PATH, content)


####################################################################################
# (5) PATCH CACHE BUSTER DO TEMPLATE
####################################################################################

def patch_template_v1() -> None:
    content = read_text_v1(TEMPLATE_PATH)

    if "new_user.js" not in content:
        raise RuntimeError("new_user.js nao encontrado no template.")

    content = re.sub(
        r'new_user\.js\?v=[^"]+',
        "new_user.js?v=20260503-save-return-not-home-refresh-v2",
        content,
    )

    if "new_user.js?v=20260503-save-return-not-home-refresh-v2" not in content:
        raise RuntimeError("Cache buster do new_user.js nao foi atualizado.")

    write_text_v1(TEMPLATE_PATH, content)


####################################################################################
# (6) VALIDAR CONTEUDO
####################################################################################

def validate_v1() -> None:
    js_content = read_text_v1(NEW_USER_JS_PATH)
    template_content = read_text_v1(TEMPLATE_PATH)

    required_js_markers = [
        "APPVERBO_SAVE_RETURN_REFRESH_GUARD_V2_START",
        "isAppVerboSaveReturnUrlV2",
        "clearAppVerboSaveReturnMarkersV2",
        "key.endsWith(\"_success\")",
        "key.endsWith(\"_error\")",
        "!appverboIsSaveReturnUrlV2",
        "window.location.replace(homeUrl)",
    ]

    missing_js = [
        marker for marker in required_js_markers
        if marker not in js_content
    ]

    if missing_js:
        raise RuntimeError("Marcadores ausentes no new_user.js: " + ", ".join(missing_js))

    if "new_user.js?v=20260503-save-return-not-home-refresh-v2" not in template_content:
        raise RuntimeError("Cache buster esperado nao encontrado no template.")

    print("OK: retorno apos gravar nao sera tratado como refresh manual.")
    print("OK: refresh manual continua a redirecionar para Home.")
    print("OK: marcadores de success/error sao removidos do URL apos carregar.")
    print("OK: cache buster atualizado.")


####################################################################################
# (7) EXECUCAO
####################################################################################

def main() -> None:
    require_file_v1(NEW_USER_JS_PATH)
    require_file_v1(TEMPLATE_PATH)

    js_backup = backup_file_v1(NEW_USER_JS_PATH, "save_return_not_home_refresh_v2")
    template_backup = backup_file_v1(TEMPLATE_PATH, "save_return_not_home_refresh_v2")

    print(f"OK: backup criado: {js_backup}")
    print(f"OK: backup criado: {template_backup}")

    patch_new_user_js_v1()
    patch_template_v1()
    validate_v1()

    print("OK: patch save return vs browser refresh concluido.")


if __name__ == "__main__":
    main()
