from __future__ import annotations

import re
import shutil
from datetime import datetime
from pathlib import Path


####################################################################################
# (1) CONFIGURACAO
####################################################################################

PROJECT_ROOT = Path.cwd()

PAGE_HANDLER_PATH = PROJECT_ROOT / "appverbo" / "routes" / "profile" / "page_handler.py"
NEW_USER_JS_PATH = PROJECT_ROOT / "static" / "js" / "new_user.js"
TEMPLATE_PATH = PROJECT_ROOT / "templates" / "new_user.html"

PY_CONTEXT_MARKER_START = "# APPVERBO_PAGE_HANDLER_POST_SAVE_CONTEXT_V1_START"
PY_CONTEXT_MARKER_END = "# APPVERBO_PAGE_HANDLER_POST_SAVE_CONTEXT_V1_END"

JS_MARKER_START = "// APPVERBO_INITIAL_PROFILE_SECTION_FROM_URL_V1_START"
JS_MARKER_END = "// APPVERBO_INITIAL_PROFILE_SECTION_FROM_URL_V1_END"


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


def replace_marker_block_v1(content: str, start_marker: str, end_marker: str, new_block: str) -> str:
    pattern = re.compile(
        re.escape(start_marker) + r".*?" + re.escape(end_marker),
        flags=re.DOTALL,
    )

    if pattern.search(content):
        return pattern.sub(new_block.strip(), content)

    return content.rstrip() + "\n\n" + new_block.strip() + "\n"


####################################################################################
# (3) PATCH page_handler.py
####################################################################################

def patch_page_handler_signature_v1(content: str) -> str:
    if "profile_section: str = \"\"" not in content:
        old_signature_tail = '    settings_tab: str = "",\n) -> HTMLResponse:'
        new_signature_tail = '''    settings_tab: str = "",
    target: str = "",
    profile_section: str = "",
    dynamic_process_section: str = "",
    section_key: str = "",
    appverbo_after_save: str = "",
) -> HTMLResponse:'''

        if old_signature_tail not in content:
            raise RuntimeError("Nao encontrei a assinatura de new_user_page para adicionar parametros de contexto.")

        content = content.replace(old_signature_tail, new_signature_tail, 1)

    return content


def patch_page_handler_menu_guard_v1(content: str) -> str:
    old_guard = '''        if resolved_menu != "perfil" and resolved_menu not in visible_menu_keys:
            resolved_menu = "home"'''

    new_guard = '''        # APPVERBO_PAGE_HANDLER_ALLOW_MEU_PERFIL_V1_START
        # O menu "meu_perfil" e um processo especial que pode nao aparecer em
        # visible_sidebar_menu_keys, mas deve ser aceite quando vem no redirect
        # pos-save. Caso contrario, /users/new?menu=meu_perfil cai em Home.
        if (
            resolved_menu not in {"perfil", MENU_MEU_PERFIL_KEY}
            and resolved_menu not in visible_menu_keys
        ):
            resolved_menu = "home"
        # APPVERBO_PAGE_HANDLER_ALLOW_MEU_PERFIL_V1_END'''

    if old_guard in content:
        content = content.replace(old_guard, new_guard, 1)
    elif "APPVERBO_PAGE_HANDLER_ALLOW_MEU_PERFIL_V1_START" not in content:
        raise RuntimeError("Nao encontrei o guard de visible_menu_keys para ajustar meu_perfil.")

    return content


def patch_page_handler_context_block_v1(content: str) -> str:
    context_block = '''    # APPVERBO_PAGE_HANDLER_POST_SAVE_CONTEXT_V1_START
    clean_target_from_query = str(target or "").strip()
    clean_profile_section_from_query = str(profile_section or "").strip().lower()
    clean_dynamic_section_from_query = str(
        dynamic_process_section or section_key or ""
    ).strip()

    if clean_target_from_query:
        initial_menu_target = clean_target_from_query

    if resolved_menu == MENU_MEU_PERFIL_KEY:
        initial_menu_target = "#perfil-pessoal-card"

    if clean_dynamic_section_from_query:
        initial_dynamic_process_section = clean_dynamic_section_from_query

    is_post_save_return = str(appverbo_after_save or "").strip() == "1"
    # APPVERBO_PAGE_HANDLER_POST_SAVE_CONTEXT_V1_END


'''

    if PY_CONTEXT_MARKER_START in content:
        pattern = re.compile(
            re.escape(PY_CONTEXT_MARKER_START) + r".*?" + re.escape(PY_CONTEXT_MARKER_END) + r"\n\n",
            flags=re.DOTALL,
        )
        content = pattern.sub(context_block, content)
        return content

    anchor = "    context = {\n"

    if anchor not in content:
        raise RuntimeError("Nao encontrei o inicio do dict context em page_handler.py.")

    content = content.replace(anchor, context_block + anchor, 1)

    return content


def patch_page_handler_context_values_v1(content: str) -> str:
    if '"initial_profile_section": clean_profile_section_from_query,' not in content:
        anchor = '        "initial_dynamic_process_section": initial_dynamic_process_section,\n'
        insertion = '''        "initial_profile_section": clean_profile_section_from_query,
        "requested_profile_section": clean_profile_section_from_query,
        "requested_dynamic_process_section": clean_dynamic_section_from_query,
        "appverbo_after_save": is_post_save_return,
'''

        if anchor not in content:
            raise RuntimeError("Nao encontrei initial_dynamic_process_section no contexto.")

        content = content.replace(anchor, anchor + insertion, 1)

    return content


def patch_page_handler_v1() -> None:
    content = read_text_v1(PAGE_HANDLER_PATH)

    required_before = [
        "def new_user_page(",
        "menu: str = \"home\"",
        "visible_menu_keys",
        "_resolve_initial_menu_target",
        '"initial_menu": resolved_menu',
    ]

    missing_before = [
        marker for marker in required_before
        if marker not in content
    ]

    if missing_before:
        raise RuntimeError("Marcadores ausentes em page_handler.py: " + ", ".join(missing_before))

    content = patch_page_handler_signature_v1(content)
    content = patch_page_handler_menu_guard_v1(content)
    content = patch_page_handler_context_block_v1(content)
    content = patch_page_handler_context_values_v1(content)

    write_text_v1(PAGE_HANDLER_PATH, content)


####################################################################################
# (4) PATCH new_user.js PARA SELECIONAR ABA DO MEU PERFIL PELO profile_section
####################################################################################

JS_BLOCK = r'''
// APPVERBO_INITIAL_PROFILE_SECTION_FROM_URL_V1_START
//###################################################################################
// (INITIAL_PROFILE_SECTION_FROM_URL_V1) ATIVAR ABA DO MEU PERFIL APOS POS-SAVE
//###################################################################################

(function setupInitialProfileSectionFromUrlV1() {
  "use strict";

  function safeInitialProfileSectionTextV1(value) {
    return String(value === null || value === undefined ? "" : value);
  }

  function normalizeInitialProfileSectionKeyV1(value) {
    if (typeof normalizeMenuKey === "function") {
      return normalizeMenuKey(value);
    }

    return safeInitialProfileSectionTextV1(value).trim().toLowerCase();
  }

  function normalizeInitialProfileSectionLookupV1(value) {
    if (typeof normalizeLookupText === "function") {
      return normalizeLookupText(value);
    }

    return safeInitialProfileSectionTextV1(value)
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function readProfileSectionFromUrlV1() {
    try {
      const params = new URLSearchParams(window.location.search);
      return normalizeInitialProfileSectionKeyV1(params.get("profile_section"));
    } catch (error) {
      return "";
    }
  }

  function setProfileSectionInputsV1(sectionKey) {
    if (!sectionKey) {
      return;
    }

    const selectors = [
      "#perfil-pessoal-card input[name='profile_section']",
      "#perfil-pessoal-card [data-meu-perfil-section-input]",
      "#perfil-pessoal-card [data-profile-section-input]",
      "input[name='profile_section']",
      "[data-meu-perfil-section-input]",
      "[data-profile-section-input]"
    ];

    let changed = false;

    selectors.forEach((selector) => {
      document.querySelectorAll(selector).forEach((input) => {
        if (!input) {
          return;
        }

        input.value = sectionKey;
        input.dispatchEvent(new Event("input", { bubbles: true }));
        input.dispatchEvent(new Event("change", { bubbles: true }));
        changed = true;
      });
    });

    const form = document.querySelector("form[action='/users/profile/personal']")
      || document.querySelector('form[action="/users/profile/personal"]');

    if (form && !form.querySelector("input[name='profile_section']")) {
      const hidden = document.createElement("input");
      hidden.type = "hidden";
      hidden.name = "profile_section";
      hidden.value = sectionKey;
      form.appendChild(hidden);
      changed = true;
    }

    return changed;
  }

  function findProfileSectionTabByKeyOrLabelV1(sectionKey) {
    if (!sectionKey) {
      return null;
    }

    const sections = (typeof profilePersonalSections !== "undefined" && Array.isArray(profilePersonalSections))
      ? profilePersonalSections
      : [];

    const sectionMeta = sections.find((section) => {
      return normalizeInitialProfileSectionKeyV1(section && section.key) === sectionKey;
    }) || null;

    const sectionLabel = normalizeInitialProfileSectionLookupV1(sectionMeta && sectionMeta.label);

    const candidates = Array.from(
      document.querySelectorAll(
        "#perfil-pessoal-card [data-profile-section-tab], " +
        "#perfil-pessoal-card [data-profile-section-button], " +
        "#perfil-pessoal-card .profile-section-tab, " +
        "#perfil-pessoal-card button, " +
        "#perfil-pessoal-card a"
      )
    );

    return candidates.find((candidate) => {
      const dataKey = normalizeInitialProfileSectionKeyV1(
        candidate.dataset.profileSection ||
        candidate.dataset.profileSectionKey ||
        candidate.dataset.profileSectionTab ||
        candidate.dataset.sectionKey ||
        ""
      );

      if (dataKey && dataKey === sectionKey) {
        return true;
      }

      const textKey = normalizeInitialProfileSectionLookupV1(candidate.textContent);

      return Boolean(sectionLabel && textKey && textKey === sectionLabel);
    }) || null;
  }

  function activateProfileSectionFromUrlV1() {
    const sectionKey = readProfileSectionFromUrlV1();

    if (!sectionKey) {
      return;
    }

    setProfileSectionInputsV1(sectionKey);

    const tab = findProfileSectionTabByKeyOrLabelV1(sectionKey);

    if (tab && typeof tab.click === "function") {
      tab.click();
    }

    setProfileSectionInputsV1(sectionKey);

    document.dispatchEvent(
      new CustomEvent("appverbo:profile-section-restored", {
        detail: {
          sectionKey
        }
      })
    );
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", activateProfileSectionFromUrlV1);
  } else {
    activateProfileSectionFromUrlV1();
  }

  window.setTimeout(activateProfileSectionFromUrlV1, 100);
  window.setTimeout(activateProfileSectionFromUrlV1, 350);
  window.setTimeout(activateProfileSectionFromUrlV1, 900);
})();

// APPVERBO_INITIAL_PROFILE_SECTION_FROM_URL_V1_END
'''


def patch_new_user_js_v1() -> None:
    content = read_text_v1(NEW_USER_JS_PATH)

    content = replace_marker_block_v1(
        content,
        JS_MARKER_START,
        JS_MARKER_END,
        JS_BLOCK,
    )

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
        "new_user.js?v=20260503-page-handler-post-save-context-v1",
        content,
    )

    if "new_user.js?v=20260503-page-handler-post-save-context-v1" not in content:
        raise RuntimeError("Cache buster do new_user.js nao foi atualizado.")

    write_text_v1(TEMPLATE_PATH, content)


####################################################################################
# (6) VALIDAR PATCH
####################################################################################

def validate_v1() -> None:
    page_content = read_text_v1(PAGE_HANDLER_PATH)
    js_content = read_text_v1(NEW_USER_JS_PATH)
    template_content = read_text_v1(TEMPLATE_PATH)

    required_page = [
        "profile_section: str = \"\"",
        "dynamic_process_section: str = \"\"",
        "section_key: str = \"\"",
        "appverbo_after_save: str = \"\"",
        "APPVERBO_PAGE_HANDLER_ALLOW_MEU_PERFIL_V1_START",
        "resolved_menu not in {\"perfil\", MENU_MEU_PERFIL_KEY}",
        "APPVERBO_PAGE_HANDLER_POST_SAVE_CONTEXT_V1_START",
        '"initial_profile_section": clean_profile_section_from_query',
        '"requested_dynamic_process_section": clean_dynamic_section_from_query',
    ]

    missing_page = [
        marker for marker in required_page
        if marker not in page_content
    ]

    if missing_page:
        raise RuntimeError("Marcadores ausentes em page_handler.py: " + ", ".join(missing_page))

    required_js = [
        "APPVERBO_INITIAL_PROFILE_SECTION_FROM_URL_V1_START",
        "activateProfileSectionFromUrlV1",
        "profile_section",
        "appverbo:profile-section-restored",
    ]

    missing_js = [
        marker for marker in required_js
        if marker not in js_content
    ]

    if missing_js:
        raise RuntimeError("Marcadores ausentes em new_user.js: " + ", ".join(missing_js))

    if "new_user.js?v=20260503-page-handler-post-save-context-v1" not in template_content:
        raise RuntimeError("Cache buster esperado nao encontrado no template.")

    print("OK: page_handler.py agora aceita target/profile_section/dynamic_process_section.")
    print("OK: page_handler.py nao converte meu_perfil para home.")
    print("OK: new_user.js restaura a aba profile_section quando existir no URL.")
    print("OK: cache buster atualizado.")


####################################################################################
# (7) EXECUCAO
####################################################################################

def main() -> None:
    require_file_v1(PAGE_HANDLER_PATH)
    require_file_v1(NEW_USER_JS_PATH)
    require_file_v1(TEMPLATE_PATH)

    page_backup = backup_file_v1(PAGE_HANDLER_PATH, "page_handler_post_save_context_v1")
    js_backup = backup_file_v1(NEW_USER_JS_PATH, "page_handler_post_save_context_v1")
    template_backup = backup_file_v1(TEMPLATE_PATH, "page_handler_post_save_context_v1")

    print(f"OK: backup criado: {page_backup}")
    print(f"OK: backup criado: {js_backup}")
    print(f"OK: backup criado: {template_backup}")

    patch_page_handler_v1()
    patch_new_user_js_v1()
    patch_template_v1()
    validate_v1()

    print("OK: patch page_handler contexto pos-save concluido.")


if __name__ == "__main__":
    main()
