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

TOP_START = "// APPVERBO_POST_SAVE_CONTEXT_NAVIGATION_GUARD_V3_START"
TOP_END = "// APPVERBO_POST_SAVE_CONTEXT_NAVIGATION_GUARD_V3_END"

CAPTURE_START = "// APPVERBO_POST_SAVE_CONTEXT_CAPTURE_V3_START"
CAPTURE_END = "// APPVERBO_POST_SAVE_CONTEXT_CAPTURE_V3_END"


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


def replace_marker_block_v1(content: str, start_marker: str, end_marker: str, new_block: str) -> str:
    pattern = re.compile(
        re.escape(start_marker) + r".*?" + re.escape(end_marker),
        flags=re.DOTALL,
    )

    if pattern.search(content):
        return pattern.sub(new_block.strip(), content)

    return content.rstrip() + "\n\n" + new_block.strip() + "\n"


####################################################################################
# (3) BLOCO DE GUARD GLOBAL NO TOPO DO new_user.js
####################################################################################

TOP_GUARD_JS = r'''// APPVERBO_POST_SAVE_CONTEXT_NAVIGATION_GUARD_V3_START
//###################################################################################
// (POST_SAVE_CONTEXT_NAVIGATION_GUARD_V3) RETORNO POS-SAVE VS REFRESH MANUAL
//###################################################################################

const APPVERBO_POST_SAVE_CONTEXT_KEY_V3 = "appverbo:post-save-context-v3";
const APPVERBO_POST_SAVE_CONTEXT_MAX_AGE_MS_V3 = 120000;

function getAppVerboCurrentUrlPostSaveV3() {
  try {
    return new URL(window.location.href);
  } catch (error) {
    return null;
  }
}

function isAppVerboPostSaveFeedbackUrlV3(url) {
  if (!url) {
    return false;
  }

  if (url.searchParams.get("appverbo_after_save") === "1") {
    return true;
  }

  for (const rawKey of url.searchParams.keys()) {
    const key = String(rawKey || "").trim().toLowerCase();

    if (
      key === "success" ||
      key === "error" ||
      key.endsWith("_success") ||
      key.endsWith("_error")
    ) {
      return true;
    }
  }

  return false;
}

function readAndClearAppVerboPostSaveContextV3() {
  try {
    const rawValue = window.sessionStorage.getItem(APPVERBO_POST_SAVE_CONTEXT_KEY_V3) || "";

    if (!rawValue) {
      return null;
    }

    window.sessionStorage.removeItem(APPVERBO_POST_SAVE_CONTEXT_KEY_V3);

    const parsedValue = JSON.parse(rawValue);
    const createdAt = Number(parsedValue && parsedValue.createdAt || 0);

    if (!createdAt || Date.now() - createdAt > APPVERBO_POST_SAVE_CONTEXT_MAX_AGE_MS_V3) {
      return null;
    }

    if (!parsedValue || typeof parsedValue.url !== "string" || !parsedValue.url.trim()) {
      return null;
    }

    return parsedValue;
  } catch (error) {
    return null;
  }
}

function copyPostSaveFeedbackParamsV3(sourceUrl, targetUrl) {
  if (!sourceUrl || !targetUrl) {
    return;
  }

  Array.from(sourceUrl.searchParams.keys()).forEach((rawKey) => {
    const key = String(rawKey || "").trim().toLowerCase();

    if (
      key === "success" ||
      key === "error" ||
      key.endsWith("_success") ||
      key.endsWith("_error")
    ) {
      targetUrl.searchParams.set(rawKey, sourceUrl.searchParams.get(rawKey) || "");
    }
  });
}

function clearPostSaveFeedbackMarkersFromUrlV3() {
  const url = getAppVerboCurrentUrlPostSaveV3();

  if (!url) {
    return;
  }

  let changed = false;

  Array.from(url.searchParams.keys()).forEach((rawKey) => {
    const key = String(rawKey || "").trim().toLowerCase();

    if (key === "appverbo_after_save") {
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

function redirectToStoredPostSaveContextV3(storedContext) {
  const currentUrl = getAppVerboCurrentUrlPostSaveV3();

  if (!storedContext || !storedContext.url || !currentUrl || currentUrl.pathname !== "/users/new") {
    return false;
  }

  let targetUrl = null;

  try {
    targetUrl = new URL(storedContext.url, window.location.origin);
  } catch (error) {
    return false;
  }

  if (targetUrl.pathname !== "/users/new") {
    return false;
  }

  targetUrl.searchParams.set("appverbo_after_save", "1");
  copyPostSaveFeedbackParamsV3(currentUrl, targetUrl);

  const targetPath = targetUrl.pathname + targetUrl.search + targetUrl.hash;
  const currentPath = currentUrl.pathname + currentUrl.search + currentUrl.hash;

  if (targetPath === currentPath) {
    return false;
  }

  window.location.replace(targetPath);
  return true;
}

const appverboStoredPostSaveContextV3 = readAndClearAppVerboPostSaveContextV3();

if (redirectToStoredPostSaveContextV3(appverboStoredPostSaveContextV3)) {
  // A navegacao continua no mesmo processo/aba onde o POST foi executado.
} else {
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

  const currentUrlForRefreshGuard = getAppVerboCurrentUrlPostSaveV3();
  const isPostSaveFeedbackUrl = isAppVerboPostSaveFeedbackUrlV3(currentUrlForRefreshGuard);

  if (
    navigationType === "reload" &&
    window.location.pathname === "/users/new" &&
    !isPostSaveFeedbackUrl
  ) {
    const homeUrl = "/users/new?menu=home";
    const currentPathAndQuery = `${window.location.pathname}${window.location.search}`;

    if (currentPathAndQuery !== homeUrl || window.location.hash) {
      window.location.replace(homeUrl);
    }
  }

  if (isPostSaveFeedbackUrl) {
    window.setTimeout(clearPostSaveFeedbackMarkersFromUrlV3, 600);
  }
}
// APPVERBO_POST_SAVE_CONTEXT_NAVIGATION_GUARD_V3_END'''


####################################################################################
# (4) BLOCO DE CAPTURA GLOBAL ANTES DO POST
####################################################################################

CAPTURE_JS = r'''// APPVERBO_POST_SAVE_CONTEXT_CAPTURE_V3_START
//###################################################################################
// (POST_SAVE_CONTEXT_CAPTURE_V3) GUARDAR PROCESSO/ABA ANTES DE QUALQUER POST
//###################################################################################

(function setupAppVerboPostSaveContextCaptureV3() {
  "use strict";

  //###################################################################################
  // (1) HELPERS
  //###################################################################################

  function safePostSaveTextV3(value) {
    return String(value === null || value === undefined ? "" : value);
  }

  function normalizePostSaveKeyV3(value) {
    if (typeof normalizeMenuKey === "function") {
      return normalizeMenuKey(value);
    }

    return safePostSaveTextV3(value).trim().toLowerCase();
  }

  function normalizePostSaveLookupV3(value) {
    if (typeof normalizeLookupText === "function") {
      return normalizeLookupText(value);
    }

    return safePostSaveTextV3(value)
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function ensureHiddenPostSaveInputV3(form, name) {
    let input = form.querySelector("input[name='" + name + "']");

    if (!input) {
      input = document.createElement("input");
      input.type = "hidden";
      input.name = name;
      form.appendChild(input);
    }

    return input;
  }

  function getFormActionPostSaveV3(form) {
    return safePostSaveTextV3(form && (form.getAttribute("action") || form.action));
  }

  function getFormMethodPostSaveV3(form) {
    return safePostSaveTextV3(form && (form.getAttribute("method") || form.method || "post"))
      .trim()
      .toLowerCase();
  }

  function readFirstFormValuePostSaveV3(form, names) {
    if (!form) {
      return "";
    }

    for (const name of names) {
      const control = form.querySelector("[name='" + name + "']");

      if (!control) {
        continue;
      }

      const value = safePostSaveTextV3(control.value).trim();

      if (value) {
        return value;
      }
    }

    return "";
  }

  function getCurrentUrlPostSaveV3() {
    try {
      return new URL(window.location.href);
    } catch (error) {
      return new URL("/users/new", window.location.origin);
    }
  }

  function getProfileSectionFromInputPostSaveV3() {
    const selectors = [
      "#perfil-pessoal-card input[name='profile_section']",
      "#perfil-pessoal-card [data-meu-perfil-section-input]",
      "#perfil-pessoal-card [data-profile-section-input]",
      "input[name='profile_section']",
      "[data-meu-perfil-section-input]",
      "[data-profile-section-input]"
    ];

    for (const selector of selectors) {
      const input = document.querySelector(selector);
      const value = normalizePostSaveKeyV3(input ? input.value : "");

      if (value) {
        return value;
      }
    }

    return "";
  }

  function getProfileSectionFromActiveTabPostSaveV3() {
    const sections = Array.isArray(profilePersonalSections) ? profilePersonalSections : [];

    const activeSelectors = [
      "#perfil-pessoal-card [data-profile-section-tab].active",
      "#perfil-pessoal-card [data-profile-section-tab][aria-selected='true']",
      "#perfil-pessoal-card [data-profile-section-button].active",
      "#perfil-pessoal-card [data-profile-section-button][aria-selected='true']",
      "#perfil-pessoal-card .profile-section-tab.active",
      "#perfil-pessoal-card .profile-section-tab[aria-selected='true']",
      "#perfil-pessoal-card .active"
    ];

    for (const selector of activeSelectors) {
      const activeElement = document.querySelector(selector);

      if (!activeElement) {
        continue;
      }

      const datasetSection = normalizePostSaveKeyV3(
        activeElement.dataset.profileSection ||
        activeElement.dataset.profileSectionKey ||
        activeElement.dataset.profileSectionTab ||
        activeElement.dataset.sectionKey ||
        ""
      );

      if (datasetSection) {
        return datasetSection;
      }

      const activeLabel = normalizePostSaveLookupV3(activeElement.textContent);

      if (!activeLabel) {
        continue;
      }

      for (const section of sections) {
        const sectionLabel = normalizePostSaveLookupV3(section && section.label);

        if (sectionLabel && sectionLabel === activeLabel) {
          return normalizePostSaveKeyV3(section && section.key);
        }
      }
    }

    return "";
  }

  function getProfileSectionFromVisiblePanePostSaveV3() {
    const panes = Array.from(
      document.querySelectorAll("#perfil-pessoal-card [data-profile-section-pane]")
    );

    for (const pane of panes) {
      const style = window.getComputedStyle ? window.getComputedStyle(pane) : null;

      if (
        pane.hidden ||
        pane.style.display === "none" ||
        (style && style.display === "none")
      ) {
        continue;
      }

      const sectionKey = normalizePostSaveKeyV3(pane.dataset.profileSectionPane);

      if (sectionKey) {
        return sectionKey;
      }
    }

    return "";
  }

  function getCurrentProfileSectionPostSaveV3() {
    return (
      getProfileSectionFromInputPostSaveV3() ||
      getProfileSectionFromActiveTabPostSaveV3() ||
      getProfileSectionFromVisiblePanePostSaveV3() ||
      (
        Array.isArray(profilePersonalSections) && profilePersonalSections.length
          ? normalizePostSaveKeyV3(profilePersonalSections[0].key)
          : ""
      )
    );
  }

  function getDynamicSectionPostSaveV3(menuKey) {
    const formValue = readFirstFormValuePostSaveV3(document, [
      "dynamic_process_section",
      "section_key",
      "process_section",
      "active_section",
      "settings_tab"
    ]);

    if (formValue) {
      return normalizePostSaveKeyV3(formValue);
    }

    if (
      typeof selectedDynamicSectionByMenu === "object" &&
      selectedDynamicSectionByMenu !== null &&
      menuKey &&
      selectedDynamicSectionByMenu[menuKey]
    ) {
      return normalizePostSaveKeyV3(selectedDynamicSectionByMenu[menuKey]);
    }

    const activeElement = document.querySelector(
      "#dynamic-process-card .active, " +
      "#dynamic-process-card [aria-selected='true'], " +
      "[data-dynamic-process-section-key].active, " +
      "[data-dynamic-process-section-key][aria-selected='true']"
    );

    if (activeElement) {
      const datasetSection = normalizePostSaveKeyV3(
        activeElement.dataset.dynamicProcessSectionKey ||
        activeElement.dataset.sectionKey ||
        ""
      );

      if (datasetSection) {
        return datasetSection;
      }
    }

    return "";
  }

  function currentMenuFromUrlOrBootstrapPostSaveV3(form) {
    const currentUrl = getCurrentUrlPostSaveV3();

    const formMenu = normalizePostSaveKeyV3(
      readFirstFormValuePostSaveV3(form, [
        "menu",
        "menu_key",
        "process_menu_key",
        "dynamic_menu_key",
        "settings_edit_key"
      ])
    );

    if (formMenu) {
      return formMenu;
    }

    const urlMenu = normalizePostSaveKeyV3(currentUrl.searchParams.get("menu"));

    if (urlMenu) {
      return urlMenu;
    }

    if (typeof initialMenu !== "undefined") {
      const bootstrapMenu = normalizePostSaveKeyV3(initialMenu);

      if (bootstrapMenu) {
        return bootstrapMenu;
      }
    }

    return "";
  }

  //###################################################################################
  // (2) CONSTRUIR URL DE RETORNO
  //###################################################################################

  function buildPostSaveReturnUrlV3(form) {
    const currentUrl = getCurrentUrlPostSaveV3();

    currentUrl.pathname = "/users/new";

    const action = getFormActionPostSaveV3(form);
    const actionLookup = normalizePostSaveLookupV3(action);
    let menuKey = currentMenuFromUrlOrBootstrapPostSaveV3(form);

    if (actionLookup.includes("/users/profile/personal")) {
      menuKey = MEU_PERFIL_MENU_KEY;
      currentUrl.searchParams.set("menu", MEU_PERFIL_MENU_KEY);
      currentUrl.searchParams.set("target", "#perfil-pessoal-card");
      currentUrl.searchParams.set("profile_tab", "pessoal");

      const profileSection = getCurrentProfileSectionPostSaveV3();

      if (profileSection) {
        currentUrl.searchParams.set("profile_section", profileSection);
      }
    } else {
      if (menuKey) {
        currentUrl.searchParams.set("menu", menuKey);
      }

      const formTarget = readFirstFormValuePostSaveV3(form, ["target", "return_target"]);

      if (formTarget) {
        currentUrl.searchParams.set("target", formTarget);
      }

      const settingsEditKey = normalizePostSaveKeyV3(
        readFirstFormValuePostSaveV3(form, ["settings_edit_key", "menu_key"])
      );
      const settingsAction = normalizePostSaveKeyV3(
        readFirstFormValuePostSaveV3(form, ["settings_action"])
      );
      const settingsTab = normalizePostSaveKeyV3(
        readFirstFormValuePostSaveV3(form, ["settings_tab"])
      );

      if (settingsEditKey && currentUrl.searchParams.get("menu") === "administrativo") {
        currentUrl.searchParams.set("settings_edit_key", settingsEditKey);
        currentUrl.searchParams.set("settings_action", settingsAction || "edit");

        if (settingsTab) {
          currentUrl.searchParams.set("settings_tab", settingsTab);
        }

        if (!currentUrl.searchParams.get("target")) {
          currentUrl.searchParams.set("target", "#settings-menu-edit-card");
        }
      }

      const dynamicSection = getDynamicSectionPostSaveV3(menuKey);

      if (dynamicSection) {
        currentUrl.searchParams.set("dynamic_process_section", dynamicSection);
      }
    }

    currentUrl.searchParams.set("appverbo_after_save", "1");

    return currentUrl.pathname + currentUrl.search + currentUrl.hash;
  }

  //###################################################################################
  // (3) GUARDAR CONTEXTO
  //###################################################################################

  function storePostSaveContextV3(form) {
    if (!form) {
      return;
    }

    const method = getFormMethodPostSaveV3(form);

    if (method && method !== "post") {
      return;
    }

    const returnUrl = buildPostSaveReturnUrlV3(form);

    try {
      window.sessionStorage.setItem(
        APPVERBO_POST_SAVE_CONTEXT_KEY_V3,
        JSON.stringify({
          url: returnUrl,
          createdAt: Date.now()
        })
      );
    } catch (error) {
      // Ignora falhas de sessionStorage.
    }

    ensureHiddenPostSaveInputV3(form, "appverbo_after_save").value = "1";
    ensureHiddenPostSaveInputV3(form, "return_url").value = returnUrl;
  }

  function bindPostSaveContextCaptureV3() {
    document.addEventListener("submit", function (event) {
      storePostSaveContextV3(event.target);
    }, true);

    document.addEventListener("click", function (event) {
      const submitControl = event.target && event.target.closest
        ? event.target.closest("button[type='submit'], input[type='submit'], button:not([type])")
        : null;

      if (!submitControl || !submitControl.form) {
        return;
      }

      storePostSaveContextV3(submitControl.form);
    }, true);

    if (
      window.HTMLFormElement &&
      window.HTMLFormElement.prototype &&
      !window.HTMLFormElement.prototype.__appverboPostSaveContextPatchedV3
    ) {
      const nativeSubmit = window.HTMLFormElement.prototype.submit;

      window.HTMLFormElement.prototype.submit = function patchedSubmitPostSaveContextV3() {
        storePostSaveContextV3(this);
        return nativeSubmit.call(this);
      };

      window.HTMLFormElement.prototype.__appverboPostSaveContextPatchedV3 = true;
    }
  }

  bindPostSaveContextCaptureV3();
})();

// APPVERBO_POST_SAVE_CONTEXT_CAPTURE_V3_END'''


####################################################################################
# (5) PATCH new_user.js
####################################################################################

def patch_new_user_js_v1() -> None:
    content = read_text_v1(NEW_USER_JS_PATH)

    bootstrap_marker = "const bootstrap = window.__APPVERBO_BOOTSTRAP__ || {};"

    if bootstrap_marker not in content:
        raise RuntimeError("Marcador bootstrap nao encontrado no new_user.js.")

    top_patterns = [
        re.compile(
            r"// APPVERBO_POST_SAVE_CONTEXT_NAVIGATION_GUARD_V3_START.*?// APPVERBO_POST_SAVE_CONTEXT_NAVIGATION_GUARD_V3_END\s*",
            flags=re.DOTALL,
        ),
        re.compile(
            r"// APPVERBO_SAVE_RETURN_REFRESH_GUARD_V2_START.*?// APPVERBO_SAVE_RETURN_REFRESH_GUARD_V2_END\s*",
            flags=re.DOTALL,
        ),
        re.compile(
            r"// APPVERBO_FORM_SAVE_NAVIGATION_GUARD_V1_START.*?// APPVERBO_FORM_SAVE_NAVIGATION_GUARD_V1_END\s*",
            flags=re.DOTALL,
        ),
    ]

    replaced_top = False

    for pattern in top_patterns:
        if pattern.search(content):
            content = pattern.sub(TOP_GUARD_JS + "\n\n", content, count=1)
            replaced_top = True
            break

    if not replaced_top:
        bootstrap_index = content.find(bootstrap_marker)
        prefix = content[:bootstrap_index]
        suffix = content[bootstrap_index:]

        if "navigationType" in prefix and "window.location.replace(homeUrl)" in prefix:
            content = TOP_GUARD_JS + "\n\n" + suffix
        else:
            content = content.replace(bootstrap_marker, TOP_GUARD_JS + "\n\n" + bootstrap_marker, 1)

    content = replace_marker_block_v1(
        content,
        CAPTURE_START,
        CAPTURE_END,
        CAPTURE_JS,
    )

    write_text_v1(NEW_USER_JS_PATH, content)


####################################################################################
# (6) PATCH CACHE BUSTER
####################################################################################

def patch_template_v1() -> None:
    content = read_text_v1(TEMPLATE_PATH)

    if "new_user.js" not in content:
        raise RuntimeError("new_user.js nao encontrado no template.")

    content = re.sub(
        r'new_user\.js\?v=[^"]+',
        "new_user.js?v=20260503-global-post-save-context-v3",
        content,
    )

    if "new_user.js?v=20260503-global-post-save-context-v3" not in content:
        raise RuntimeError("Cache buster do new_user.js nao foi atualizado.")

    write_text_v1(TEMPLATE_PATH, content)


####################################################################################
# (7) VALIDACAO
####################################################################################

def validate_v1() -> None:
    js_content = read_text_v1(NEW_USER_JS_PATH)
    template_content = read_text_v1(TEMPLATE_PATH)

    required_js_markers = [
        "APPVERBO_POST_SAVE_CONTEXT_NAVIGATION_GUARD_V3_START",
        "APPVERBO_POST_SAVE_CONTEXT_CAPTURE_V3_START",
        "APPVERBO_POST_SAVE_CONTEXT_KEY_V3",
        "redirectToStoredPostSaveContextV3",
        "storePostSaveContextV3",
        "buildPostSaveReturnUrlV3",
        "appverbo_after_save",
        "navigationType === \"reload\"",
        "window.location.replace(homeUrl)",
    ]

    missing_js_markers = [
        marker for marker in required_js_markers
        if marker not in js_content
    ]

    if missing_js_markers:
        raise RuntimeError("Marcadores ausentes no new_user.js: " + ", ".join(missing_js_markers))

    if js_content.find("APPVERBO_POST_SAVE_CONTEXT_NAVIGATION_GUARD_V3_START") > js_content.find("const bootstrap = window.__APPVERBO_BOOTSTRAP__ || {};"):
        raise RuntimeError("O guard global precisa ficar antes do bootstrap.")

    if "new_user.js?v=20260503-global-post-save-context-v3" not in template_content:
        raise RuntimeError("Cache buster esperado nao encontrado no template.")

    print("OK: guard global V3 inserido antes do bootstrap.")
    print("OK: captura global V3 inserida para qualquer POST.")
    print("OK: cache buster atualizado.")


####################################################################################
# (8) EXECUCAO
####################################################################################

def main() -> None:
    require_file_v1(NEW_USER_JS_PATH)
    require_file_v1(TEMPLATE_PATH)

    js_backup = backup_file_v1(NEW_USER_JS_PATH, "global_post_save_context_v3")
    template_backup = backup_file_v1(TEMPLATE_PATH, "global_post_save_context_v3")

    print(f"OK: backup criado: {js_backup}")
    print(f"OK: backup criado: {template_backup}")

    patch_new_user_js_v1()
    patch_template_v1()
    validate_v1()

    print("OK: patch global pos-save concluido.")


if __name__ == "__main__":
    main()
