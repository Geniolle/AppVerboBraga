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
PROFILE_HANDLERS_PATH = PROJECT_ROOT / "appverbo" / "routes" / "profile" / "profile_handlers.py"
TEMPLATE_PATH = PROJECT_ROOT / "templates" / "new_user.html"

START_MARKER = "// APPVERBO_KEEP_CURRENT_PROCESS_AFTER_PROFILE_SAVE_V1_START"
END_MARKER = "// APPVERBO_KEEP_CURRENT_PROCESS_AFTER_PROFILE_SAVE_V1_END"


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
# (3) BLOCO JS PARA GUARDAR CONTEXTO DO FORMULARIO
####################################################################################

KEEP_PROCESS_JS = r"""
// APPVERBO_KEEP_CURRENT_PROCESS_AFTER_PROFILE_SAVE_V1_START
//###################################################################################
// (KEEP_CURRENT_PROCESS_AFTER_PROFILE_SAVE_V1) MANTER PROCESSO/ABA APOS GRAVAR
//###################################################################################

(function setupKeepCurrentProcessAfterProfileSaveV1() {
  "use strict";

  //###################################################################################
  // (1) HELPERS
  //###################################################################################

  function safeKeepProcessTextV1(value) {
    return String(value === null || value === undefined ? "" : value);
  }

  function normalizeKeepProcessKeyV1(value) {
    if (typeof normalizeMenuKey === "function") {
      return normalizeMenuKey(value);
    }

    return safeKeepProcessTextV1(value).trim().toLowerCase();
  }

  function normalizeKeepProcessLookupV1(value) {
    if (typeof normalizeLookupText === "function") {
      return normalizeLookupText(value);
    }

    return safeKeepProcessTextV1(value)
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function getProfilePersonalFormKeepProcessV1() {
    return document.querySelector("form[action='/users/profile/personal']")
      || document.querySelector('form[action="/users/profile/personal"]');
  }

  function ensureHiddenInputKeepProcessV1(form, name) {
    let input = form.querySelector("input[name='" + name + "']");

    if (!input) {
      input = document.createElement("input");
      input.type = "hidden";
      input.name = name;
      form.appendChild(input);
    }

    return input;
  }

  function getSectionFromKnownInputKeepProcessV1() {
    const selectors = [
      "input[name='profile_section']",
      "[data-meu-perfil-section-input]",
      "[data-profile-section-input]"
    ];

    for (const selector of selectors) {
      const input = document.querySelector(selector);
      const value = normalizeKeepProcessKeyV1(input ? input.value : "");

      if (value) {
        return value;
      }
    }

    return "";
  }

  function getSectionFromActiveTabKeepProcessV1() {
    const sections = Array.isArray(profilePersonalSections) ? profilePersonalSections : [];

    const activeSelectors = [
      "[data-profile-section-tab].active",
      "[data-profile-section-tab][aria-selected='true']",
      "[data-profile-section-button].active",
      "[data-profile-section-button][aria-selected='true']",
      ".profile-section-tab.active",
      ".profile-section-tab[aria-selected='true']",
      "#perfil-pessoal-card .active"
    ];

    for (const selector of activeSelectors) {
      const activeElement = document.querySelector(selector);

      if (!activeElement) {
        continue;
      }

      const datasetValue = (
        activeElement.dataset.profileSection ||
        activeElement.dataset.profileSectionKey ||
        activeElement.dataset.profileSectionTab ||
        activeElement.dataset.sectionKey ||
        ""
      );

      const datasetSection = normalizeKeepProcessKeyV1(datasetValue);

      if (datasetSection) {
        return datasetSection;
      }

      const activeLabel = normalizeKeepProcessLookupV1(activeElement.textContent);

      if (!activeLabel) {
        continue;
      }

      for (const section of sections) {
        const sectionLabel = normalizeKeepProcessLookupV1(section && section.label);

        if (sectionLabel && sectionLabel === activeLabel) {
          return normalizeKeepProcessKeyV1(section && section.key);
        }
      }
    }

    return "";
  }

  function getSectionFromVisiblePaneKeepProcessV1(form) {
    const panes = Array.from(
      form.querySelectorAll("[data-profile-section-pane]")
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

      const sectionKey = normalizeKeepProcessKeyV1(pane.dataset.profileSectionPane);

      if (sectionKey) {
        return sectionKey;
      }
    }

    return "";
  }

  function getCurrentProfileSectionKeepProcessV1(form) {
    return (
      getSectionFromKnownInputKeepProcessV1() ||
      getSectionFromActiveTabKeepProcessV1() ||
      getSectionFromVisiblePaneKeepProcessV1(form) ||
      (
        Array.isArray(profilePersonalSections) && profilePersonalSections.length
          ? normalizeKeepProcessKeyV1(profilePersonalSections[0].key)
          : ""
      )
    );
  }

  //###################################################################################
  // (2) SINCRONIZAR CONTEXTO ANTES DE GRAVAR
  //###################################################################################

  function syncProfileSaveContextKeepProcessV1(form) {
    if (!form) {
      return;
    }

    const action = safeKeepProcessTextV1(form.getAttribute("action") || form.action);

    if (!action.includes("/users/profile/personal")) {
      return;
    }

    const currentSection = getCurrentProfileSectionKeepProcessV1(form);

    ensureHiddenInputKeepProcessV1(form, "menu").value = MEU_PERFIL_MENU_KEY;
    ensureHiddenInputKeepProcessV1(form, "target").value = "#perfil-pessoal-card";

    if (currentSection) {
      ensureHiddenInputKeepProcessV1(form, "profile_section").value = currentSection;
    }

    ensureHiddenInputKeepProcessV1(form, "appverbo_after_save").value = "1";
  }

  function bindProfileSaveContextKeepProcessV1() {
    const form = getProfilePersonalFormKeepProcessV1();

    if (!form || form.dataset.keepCurrentProcessAfterProfileSaveV1 === "1") {
      return;
    }

    form.dataset.keepCurrentProcessAfterProfileSaveV1 = "1";

    form.addEventListener("submit", function () {
      syncProfileSaveContextKeepProcessV1(form);
    }, true);

    form.addEventListener("click", function (event) {
      const submitControl = event.target && event.target.closest
        ? event.target.closest("button[type='submit'], input[type='submit'], button:not([type])")
        : null;

      if (!submitControl) {
        return;
      }

      syncProfileSaveContextKeepProcessV1(form);
    }, true);
  }

  //###################################################################################
  // (3) COBRIR SUBMIT NATIVO/PROGRAMATICO
  //###################################################################################

  if (
    window.HTMLFormElement &&
    window.HTMLFormElement.prototype &&
    !window.HTMLFormElement.prototype.__appverboKeepProcessSubmitPatchedV1
  ) {
    const nativeSubmit = window.HTMLFormElement.prototype.submit;

    window.HTMLFormElement.prototype.submit = function patchedSubmitKeepProcessV1() {
      syncProfileSaveContextKeepProcessV1(this);
      return nativeSubmit.call(this);
    };

    window.HTMLFormElement.prototype.__appverboKeepProcessSubmitPatchedV1 = true;
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bindProfileSaveContextKeepProcessV1);
  } else {
    bindProfileSaveContextKeepProcessV1();
  }

  window.setTimeout(bindProfileSaveContextKeepProcessV1, 150);
  window.setTimeout(bindProfileSaveContextKeepProcessV1, 600);
})();

// APPVERBO_KEEP_CURRENT_PROCESS_AFTER_PROFILE_SAVE_V1_END
"""


####################################################################################
# (4) PATCH new_user.js
####################################################################################

def patch_new_user_js_v1() -> None:
    content = read_text_v1(NEW_USER_JS_PATH)

    required_markers = [
        "const MEU_PERFIL_MENU_KEY",
        "const profilePersonalSections",
    ]

    missing = [
        marker for marker in required_markers
        if marker not in content
    ]

    if missing:
        raise RuntimeError("Marcadores ausentes no new_user.js: " + ", ".join(missing))

    content = replace_marker_block_v1(
        content,
        START_MARKER,
        END_MARKER,
        KEEP_PROCESS_JS,
    )

    write_text_v1(NEW_USER_JS_PATH, content)


####################################################################################
# (5) PATCH profile_handlers.py
####################################################################################

def patch_profile_handlers_v1() -> None:
    content = read_text_v1(PROFILE_HANDLERS_PATH)

    old_block = '''    redirect_menu = str(submitted_form.get("menu") or MENU_MEU_PERFIL_KEY).strip().lower() or MENU_MEU_PERFIL_KEY
    redirect_target = str(submitted_form.get("target") or "#perfil-pessoal-card").strip() or "#perfil-pessoal-card"
    redirect_profile_section = str(submitted_form.get("profile_section") or "").strip().lower()
'''

    new_block = '''    # APPVERBO_KEEP_CURRENT_PROCESS_AFTER_PROFILE_SAVE_V1_START
    # Este endpoint grava sempre dados do Meu perfil. Depois de gravar,
    # o utilizador deve continuar no Meu perfil e na aba onde estava.
    redirect_menu = MENU_MEU_PERFIL_KEY
    redirect_target = str(submitted_form.get("target") or "#perfil-pessoal-card").strip() or "#perfil-pessoal-card"
    redirect_profile_section = str(submitted_form.get("profile_section") or "").strip().lower()
    # APPVERBO_KEEP_CURRENT_PROCESS_AFTER_PROFILE_SAVE_V1_END
'''

    if old_block in content:
        content = content.replace(old_block, new_block, 1)
    elif "APPVERBO_KEEP_CURRENT_PROCESS_AFTER_PROFILE_SAVE_V1_START" not in content:
        raise RuntimeError("Bloco inicial de redirect_menu nao encontrado em profile_handlers.py.")

    if "redirect_menu = MENU_MEU_PERFIL_KEY" not in content:
        raise RuntimeError("profile_handlers.py nao foi ajustado para voltar ao Meu perfil.")

    write_text_v1(PROFILE_HANDLERS_PATH, content)


####################################################################################
# (6) PATCH CACHE BUSTER
####################################################################################

def patch_template_v1() -> None:
    content = read_text_v1(TEMPLATE_PATH)

    if "new_user.js" not in content:
        raise RuntimeError("new_user.js nao encontrado no template.")

    content = re.sub(
        r'new_user\.js\?v=[^"]+',
        "new_user.js?v=20260503-keep-current-process-after-profile-save-v1",
        content,
    )

    if "new_user.js?v=20260503-keep-current-process-after-profile-save-v1" not in content:
        raise RuntimeError("Cache buster do new_user.js nao foi atualizado.")

    write_text_v1(TEMPLATE_PATH, content)


####################################################################################
# (7) VALIDAR CONTEUDO
####################################################################################

def validate_v1() -> None:
    js_content = read_text_v1(NEW_USER_JS_PATH)
    profile_content = read_text_v1(PROFILE_HANDLERS_PATH)
    template_content = read_text_v1(TEMPLATE_PATH)

    required_js = [
        "APPVERBO_KEEP_CURRENT_PROCESS_AFTER_PROFILE_SAVE_V1_START",
        "syncProfileSaveContextKeepProcessV1",
        "ensureHiddenInputKeepProcessV1(form, \"menu\").value = MEU_PERFIL_MENU_KEY",
        "ensureHiddenInputKeepProcessV1(form, \"profile_section\").value = currentSection",
        "appverbo_after_save",
    ]

    missing_js = [
        marker for marker in required_js
        if marker not in js_content
    ]

    if missing_js:
        raise RuntimeError("Marcadores ausentes no new_user.js: " + ", ".join(missing_js))

    required_profile = [
        "APPVERBO_KEEP_CURRENT_PROCESS_AFTER_PROFILE_SAVE_V1_START",
        "redirect_menu = MENU_MEU_PERFIL_KEY",
        "redirect_profile_section",
    ]

    missing_profile = [
        marker for marker in required_profile
        if marker not in profile_content
    ]

    if missing_profile:
        raise RuntimeError("Marcadores ausentes no profile_handlers.py: " + ", ".join(missing_profile))

    if "new_user.js?v=20260503-keep-current-process-after-profile-save-v1" not in template_content:
        raise RuntimeError("Cache buster esperado nao encontrado no template.")

    print("OK: frontend grava contexto menu/aba antes do submit.")
    print("OK: backend força retorno ao Meu perfil.")
    print("OK: template atualizado com cache buster.")


####################################################################################
# (8) EXECUCAO
####################################################################################

def main() -> None:
    require_file_v1(NEW_USER_JS_PATH)
    require_file_v1(PROFILE_HANDLERS_PATH)
    require_file_v1(TEMPLATE_PATH)

    js_backup = backup_file_v1(NEW_USER_JS_PATH, "keep_current_process_after_profile_save_v1")
    profile_backup = backup_file_v1(PROFILE_HANDLERS_PATH, "keep_current_process_after_profile_save_v1")
    template_backup = backup_file_v1(TEMPLATE_PATH, "keep_current_process_after_profile_save_v1")

    print(f"OK: backup criado: {js_backup}")
    print(f"OK: backup criado: {profile_backup}")
    print(f"OK: backup criado: {template_backup}")

    patch_new_user_js_v1()
    patch_profile_handlers_v1()
    patch_template_v1()
    validate_v1()

    print("OK: patch manter processo apos gravar concluido.")


if __name__ == "__main__":
    main()
