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

START_MARKER = "// APPVERBO_MEU_PERFIL_EDIT_SECTION_FILTER_V1_START"
END_MARKER = "// APPVERBO_MEU_PERFIL_EDIT_SECTION_FILTER_V1_END"


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
# (3) BLOCO JS DE FILTRO POR ABA
####################################################################################

EDIT_SECTION_FILTER_JS = r"""
// APPVERBO_MEU_PERFIL_EDIT_SECTION_FILTER_V1_START
//###################################################################################
// (MEU_PERFIL_EDIT_SECTION_FILTER_V1) FILTRAR CAMPOS DO EDITAR POR ABA/CABECALHO
//###################################################################################

(function setupMeuPerfilEditSectionFilterV1() {
  "use strict";

  //###################################################################################
  // (1) HELPERS
  //###################################################################################

  function safeEditSectionTextV1(value) {
    return String(value === null || value === undefined ? "" : value);
  }

  function normalizeEditSectionKeyV1(value) {
    if (typeof normalizeMenuKey === "function") {
      return normalizeMenuKey(value);
    }

    return safeEditSectionTextV1(value).trim().toLowerCase();
  }

  function normalizeEditSectionLookupV1(value) {
    if (typeof normalizeLookupText === "function") {
      return normalizeLookupText(value);
    }

    return safeEditSectionTextV1(value)
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function getMeuPerfilEditFormV1() {
    return document.querySelector("form[action='/users/profile/personal']")
      || document.querySelector('form[action="/users/profile/personal"]');
  }

  function sectionKeyFromLabelV1(label) {
    const cleanLabel = normalizeEditSectionLookupV1(label);

    if (!cleanLabel) {
      return "";
    }

    const sections = Array.isArray(profilePersonalSections) ? profilePersonalSections : [];

    for (const section of sections) {
      const sectionLabel = normalizeEditSectionLookupV1(section && section.label);

      if (sectionLabel && sectionLabel === cleanLabel) {
        return normalizeEditSectionKeyV1(section && section.key);
      }
    }

    return "";
  }

  function getCurrentProfileSectionFromInputV1() {
    const selectors = [
      "input[name='profile_section']",
      "[data-meu-perfil-section-input]",
      "[data-profile-section-input]"
    ];

    for (const selector of selectors) {
      const input = document.querySelector(selector);
      const value = normalizeEditSectionKeyV1(input ? input.value : "");

      if (value) {
        return value;
      }
    }

    return "";
  }

  function getCurrentProfileSectionFromActiveTabV1() {
    const activeSelectors = [
      "[data-profile-section-tab].active",
      "[data-profile-section-tab][aria-selected='true']",
      "[data-profile-section-button].active",
      "[data-profile-section-button][aria-selected='true']",
      ".profile-section-tab.active",
      ".profile-section-tab[aria-selected='true']",
      "#perfil-pessoal-card .tab.active",
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

      const datasetSection = normalizeEditSectionKeyV1(datasetValue);

      if (datasetSection) {
        return datasetSection;
      }

      const textSection = sectionKeyFromLabelV1(activeElement.textContent);

      if (textSection) {
        return textSection;
      }
    }

    return "";
  }

  function getCurrentProfileSectionV1() {
    return (
      getCurrentProfileSectionFromInputV1() ||
      getCurrentProfileSectionFromActiveTabV1() ||
      (
        Array.isArray(profilePersonalSections) &&
        profilePersonalSections.length
          ? normalizeEditSectionKeyV1(profilePersonalSections[0].key)
          : ""
      )
    );
  }

  function getElementSectionPaneV1(element) {
    if (!element) {
      return "";
    }

    return normalizeEditSectionKeyV1(
      element.dataset.profileSectionPane ||
      element.dataset.profileSection ||
      element.dataset.sectionKey ||
      ""
    );
  }

  function getVisibilityWrapperV1(element) {
    if (!element) {
      return null;
    }

    if (
      element.classList &&
      (
        element.classList.contains("field") ||
        element.classList.contains("profile-quantity-rule-v1") ||
        element.classList.contains("profile-quantity-readonly-v1")
      )
    ) {
      return element;
    }

    return (
      element.closest(".field") ||
      element.closest("[data-profile-quantity-rule-key]") ||
      element.closest("[data-profile-quantity-readonly-rule-key]") ||
      element
    );
  }

  function isDuplicateOriginWrapperV1(wrapper) {
    if (!wrapper || !wrapper.dataset) {
      return false;
    }

    return wrapper.dataset.profileQuantityOriginDuplicateV1 === "1";
  }

  function setWrapperVisibleBySectionV1(wrapper, currentSection, expectedSection) {
    if (!wrapper || !currentSection || !expectedSection) {
      return;
    }

    if (isDuplicateOriginWrapperV1(wrapper)) {
      wrapper.hidden = true;
      wrapper.style.display = "none";
      return;
    }

    if (currentSection === expectedSection) {
      wrapper.hidden = false;
      wrapper.style.display = "";
      return;
    }

    wrapper.hidden = true;
    wrapper.style.display = "none";
  }

  function applyQuantityHostsSectionV1(form) {
    if (!form || typeof getSidebarMenuSetting !== "function" || typeof normalizeProcessQuantityRules !== "function") {
      return;
    }

    const setting = getSidebarMenuSetting(MEU_PERFIL_MENU_KEY);

    if (!setting) {
      return;
    }

    const rules = normalizeProcessQuantityRules(setting.process_quantity_fields);

    rules.forEach((rule) => {
      const ruleKey = normalizeEditSectionKeyV1(rule.key);
      const headerKey = normalizeEditSectionKeyV1(rule.headerKey);

      if (!ruleKey || !headerKey) {
        return;
      }

      const hosts = form.querySelectorAll(
        "[data-profile-quantity-rule-key='" + ruleKey + "'], " +
        "[data-profile-quantity-readonly-rule-key='" + ruleKey + "']"
      );

      hosts.forEach((host) => {
        host.dataset.profileSectionPane = headerKey;
      });
    });
  }

  //###################################################################################
  // (2) APLICAR FILTRO NO FORMULARIO EDITAR
  //###################################################################################

  function applyMeuPerfilEditSectionFilterV1() {
    const form = getMeuPerfilEditFormV1();

    if (!form) {
      return;
    }

    const currentSection = getCurrentProfileSectionV1();

    if (!currentSection) {
      return;
    }

    applyQuantityHostsSectionV1(form);

    const wrappers = new Set();

    Array.from(
      form.querySelectorAll("[data-profile-section-pane], [data-profile-section], [data-section-key]")
    ).forEach((element) => {
      const wrapper = getVisibilityWrapperV1(element);

      if (!wrapper || !form.contains(wrapper)) {
        return;
      }

      wrappers.add(wrapper);
    });

    Array.from(
      form.querySelectorAll("[data-profile-quantity-rule-key]")
    ).forEach((element) => {
      const wrapper = getVisibilityWrapperV1(element);

      if (!wrapper || !form.contains(wrapper)) {
        return;
      }

      wrappers.add(wrapper);
    });

    wrappers.forEach((wrapper) => {
      const wrapperSection = getElementSectionPaneV1(wrapper);

      if (!wrapperSection) {
        return;
      }

      setWrapperVisibleBySectionV1(wrapper, currentSection, wrapperSection);
    });
  }

  function scheduleMeuPerfilEditSectionFilterV1() {
    window.setTimeout(applyMeuPerfilEditSectionFilterV1, 0);
    window.setTimeout(applyMeuPerfilEditSectionFilterV1, 80);
    window.setTimeout(applyMeuPerfilEditSectionFilterV1, 250);
  }

  //###################################################################################
  // (3) EVENTOS
  //###################################################################################

  document.addEventListener("click", scheduleMeuPerfilEditSectionFilterV1, true);
  document.addEventListener("input", scheduleMeuPerfilEditSectionFilterV1, true);
  document.addEventListener("change", scheduleMeuPerfilEditSectionFilterV1, true);

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", scheduleMeuPerfilEditSectionFilterV1);
  } else {
    scheduleMeuPerfilEditSectionFilterV1();
  }

  window.setTimeout(scheduleMeuPerfilEditSectionFilterV1, 150);
  window.setTimeout(scheduleMeuPerfilEditSectionFilterV1, 600);
  window.setTimeout(scheduleMeuPerfilEditSectionFilterV1, 1200);
})();

// APPVERBO_MEU_PERFIL_EDIT_SECTION_FILTER_V1_END
"""


####################################################################################
# (4) PATCH new_user.js
####################################################################################

def patch_new_user_js_v1() -> None:
    content = read_text_v1(NEW_USER_JS_PATH)

    required_markers = [
        "const MEU_PERFIL_MENU_KEY",
        "const profilePersonalSections",
        "function normalizeMenuKey",
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
        EDIT_SECTION_FILTER_JS,
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
        "new_user.js?v=20260503-meu-perfil-edit-section-filter-v1",
        content,
    )

    if "new_user.js?v=20260503-meu-perfil-edit-section-filter-v1" not in content:
        raise RuntimeError("Cache buster do new_user.js nao foi atualizado.")

    write_text_v1(TEMPLATE_PATH, content)


####################################################################################
# (6) VALIDAR CONTEUDO
####################################################################################

def validate_v1() -> None:
    js_content = read_text_v1(NEW_USER_JS_PATH)
    template_content = read_text_v1(TEMPLATE_PATH)

    required_js_markers = [
        "APPVERBO_MEU_PERFIL_EDIT_SECTION_FILTER_V1_START",
        "applyMeuPerfilEditSectionFilterV1",
        "getCurrentProfileSectionV1",
        "applyQuantityHostsSectionV1",
        "setWrapperVisibleBySectionV1",
        "data-profile-section-pane",
    ]

    missing_js = [
        marker for marker in required_js_markers
        if marker not in js_content
    ]

    if missing_js:
        raise RuntimeError("Marcadores ausentes no new_user.js: " + ", ".join(missing_js))

    if "new_user.js?v=20260503-meu-perfil-edit-section-filter-v1" not in template_content:
        raise RuntimeError("Cache buster esperado nao encontrado no template.")

    print("OK: filtro de campos por aba inserido no modo editar.")
    print("OK: Campos Quantidade passam a respeitar o cabeçalho configurado.")
    print("OK: template atualizado com cache buster.")


####################################################################################
# (7) EXECUCAO
####################################################################################

def main() -> None:
    require_file_v1(NEW_USER_JS_PATH)
    require_file_v1(TEMPLATE_PATH)

    js_backup = backup_file_v1(NEW_USER_JS_PATH, "meu_perfil_edit_section_filter_v1")
    template_backup = backup_file_v1(TEMPLATE_PATH, "meu_perfil_edit_section_filter_v1")

    print(f"OK: backup criado: {js_backup}")
    print(f"OK: backup criado: {template_backup}")

    patch_new_user_js_v1()
    patch_template_v1()
    validate_v1()

    print("OK: patch filtro de abas Meu perfil concluido.")


if __name__ == "__main__":
    main()
