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

START_MARKER = "// APPVERBO_MEU_PERFIL_QUANTITY_ORIGIN_DEDUP_V1_START"
END_MARKER = "// APPVERBO_MEU_PERFIL_QUANTITY_ORIGIN_DEDUP_V1_END"


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
# (3) BLOCO JS DE DEDUPLICACAO
####################################################################################

DEDUP_JS_BLOCK = r"""
// APPVERBO_MEU_PERFIL_QUANTITY_ORIGIN_DEDUP_V1_START
//###################################################################################
// (MEU_PERFIL_QUANTITY_ORIGIN_DEDUP_V1) EVITAR DUPLICACAO DO CAMPO ORIGEM
//###################################################################################

(function setupMeuPerfilQuantityOriginDedupV1() {
  "use strict";

  //###################################################################################
  // (1) HELPERS
  //###################################################################################

  function safeQuantityOriginDedupTextV1(value) {
    return String(value === null || value === undefined ? "" : value);
  }

  function getMeuPerfilQuantityOriginSettingV1() {
    if (typeof getSidebarMenuSetting === "function") {
      const foundSetting = getSidebarMenuSetting(MEU_PERFIL_MENU_KEY);
      if (foundSetting) {
        return foundSetting;
      }
    }

    return (Array.isArray(sidebarMenuSettings) ? sidebarMenuSettings : []).find((setting) => {
      return normalizeMenuKey(setting && setting.key) === MEU_PERFIL_MENU_KEY;
    }) || null;
  }

  function getMeuPerfilQuantityOriginFormV1() {
    return document.querySelector("form[action='/users/profile/personal']")
      || document.querySelector('form[action="/users/profile/personal"]');
  }

  function resolveQuantityOriginControlNameV1(fieldKey) {
    const cleanFieldKey = normalizeMenuKey(fieldKey);

    if (!cleanFieldKey) {
      return "";
    }

    if (cleanFieldKey.startsWith("custom_")) {
      return "custom_field__" + cleanFieldKey;
    }

    const builtinNames = {
      nome: "full_name",
      telefone: "primary_phone",
      email: "login_email",
      pais: "country",
      data_nascimento: "birth_date",
      autorizacao_whatsapp: "whatsapp_notice_opt_in"
    };

    return builtinNames[cleanFieldKey] || cleanFieldKey;
  }

  function getQuantityOriginCurrentSectionV1() {
    const sectionInput = document.querySelector("[data-meu-perfil-section-input]");
    return normalizeMenuKey(sectionInput ? sectionInput.value : "");
  }

  function getQuantityOriginWrapperV1(control) {
    if (!control) {
      return null;
    }

    return control.closest(".field")
      || control.closest("[data-profile-field-key]")
      || control.parentElement;
  }

  function getControlsByNameV1(form, controlName) {
    if (!form || !controlName) {
      return [];
    }

    return Array.from(form.elements || []).filter((control) => {
      return safeQuantityOriginDedupTextV1(control.name) === controlName;
    });
  }

  function disableDuplicateWrapperV1(wrapper, fieldKey) {
    if (!wrapper) {
      return;
    }

    wrapper.dataset.profileQuantityOriginDuplicateV1 = "1";
    wrapper.dataset.profileFieldKey = normalizeMenuKey(fieldKey);
    wrapper.hidden = true;
    wrapper.style.display = "none";

    Array.from(wrapper.querySelectorAll("input, select, textarea, button")).forEach((control) => {
      control.disabled = true;
      control.dataset.profileQuantityOriginDuplicateDisabledV1 = "1";
    });
  }

  function enableKeptWrapperV1(wrapper, rule) {
    if (!wrapper || !rule) {
      return;
    }

    wrapper.dataset.profileQuantityOriginKeepV1 = "1";
    wrapper.dataset.profileFieldKey = normalizeMenuKey(rule.quantityFieldKey);

    if (rule.headerKey) {
      wrapper.dataset.profileSectionPane = rule.headerKey;
    }

    wrapper.hidden = false;

    Array.from(wrapper.querySelectorAll("input, select, textarea, button")).forEach((control) => {
      if (control.dataset.profileQuantityOriginDuplicateDisabledV1 === "1") {
        return;
      }

      control.disabled = false;
    });
  }

  function applyQuantityOriginVisibilityV1(wrapper, rule) {
    if (!wrapper || !rule) {
      return;
    }

    const currentSection = getQuantityOriginCurrentSectionV1();
    const targetSection = normalizeMenuKey(rule.headerKey || wrapper.dataset.profileSectionPane || "");

    if (!currentSection || !targetSection) {
      wrapper.style.display = "";
      return;
    }

    wrapper.style.display = currentSection === targetSection ? "" : "none";
  }

  //###################################################################################
  // (2) DEDUP POR REGRA
  //###################################################################################

  function dedupQuantityOriginRuleV1(form, rule) {
    const quantityFieldKey = normalizeMenuKey(rule && rule.quantityFieldKey);
    const controlName = resolveQuantityOriginControlNameV1(quantityFieldKey);

    if (!quantityFieldKey || !controlName) {
      return;
    }

    const controls = getControlsByNameV1(form, controlName);

    if (!controls.length) {
      return;
    }

    const wrappers = [];
    const seenWrappers = new Set();

    controls.forEach((control) => {
      const wrapper = getQuantityOriginWrapperV1(control);

      if (!wrapper || seenWrappers.has(wrapper)) {
        return;
      }

      seenWrappers.add(wrapper);
      wrappers.push(wrapper);
    });

    if (!wrappers.length) {
      return;
    }

    const targetSection = normalizeMenuKey(rule.headerKey);

    let keepWrapper = null;

    if (targetSection) {
      keepWrapper = wrappers.find((wrapper) => {
        return normalizeMenuKey(wrapper.dataset.profileSectionPane) === targetSection;
      }) || null;
    }

    if (!keepWrapper) {
      keepWrapper = wrappers[0];
    }

    enableKeptWrapperV1(keepWrapper, rule);

    wrappers.forEach((wrapper) => {
      if (wrapper === keepWrapper) {
        return;
      }

      disableDuplicateWrapperV1(wrapper, quantityFieldKey);
    });

    applyQuantityOriginVisibilityV1(keepWrapper, rule);
  }

  //###################################################################################
  // (3) DEDUP GLOBAL
  //###################################################################################

  function dedupMeuPerfilQuantityOriginsV1() {
    const form = getMeuPerfilQuantityOriginFormV1();
    const setting = getMeuPerfilQuantityOriginSettingV1();

    if (!form || !setting) {
      return;
    }

    const rules = normalizeProcessQuantityRules(setting.process_quantity_fields);

    if (!rules.length) {
      return;
    }

    rules.forEach((rule) => {
      dedupQuantityOriginRuleV1(form, rule);
    });
  }

  function scheduleDedupMeuPerfilQuantityOriginsV1() {
    window.setTimeout(dedupMeuPerfilQuantityOriginsV1, 0);
    window.setTimeout(dedupMeuPerfilQuantityOriginsV1, 80);
    window.setTimeout(dedupMeuPerfilQuantityOriginsV1, 250);
  }

  document.addEventListener("click", scheduleDedupMeuPerfilQuantityOriginsV1, true);
  document.addEventListener("input", scheduleDedupMeuPerfilQuantityOriginsV1, true);
  document.addEventListener("change", scheduleDedupMeuPerfilQuantityOriginsV1, true);

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", scheduleDedupMeuPerfilQuantityOriginsV1);
  } else {
    scheduleDedupMeuPerfilQuantityOriginsV1();
  }

  window.setTimeout(scheduleDedupMeuPerfilQuantityOriginsV1, 150);
  window.setTimeout(scheduleDedupMeuPerfilQuantityOriginsV1, 600);
})();

// APPVERBO_MEU_PERFIL_QUANTITY_ORIGIN_DEDUP_V1_END
"""


####################################################################################
# (4) PATCH new_user.js
####################################################################################

def patch_new_user_js_v1() -> None:
    content = read_text_v1(NEW_USER_JS_PATH)

    required_markers = [
        "const MEU_PERFIL_MENU_KEY",
        "function normalizeProcessQuantityRules",
        "function normalizeMenuKey",
        "function getSidebarMenuSetting",
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
        DEDUP_JS_BLOCK,
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
        "new_user.js?v=20260503-quantity-origin-dedup-v1",
        content,
    )

    if "new_user.js?v=20260503-quantity-origin-dedup-v1" not in content:
        raise RuntimeError("Cache buster do new_user.js nao foi atualizado.")

    write_text_v1(TEMPLATE_PATH, content)


####################################################################################
# (6) VALIDAR CONTEUDO
####################################################################################

def validate_v1() -> None:
    js_content = read_text_v1(NEW_USER_JS_PATH)
    template_content = read_text_v1(TEMPLATE_PATH)

    required_js_markers = [
        "APPVERBO_MEU_PERFIL_QUANTITY_ORIGIN_DEDUP_V1_START",
        "dedupMeuPerfilQuantityOriginsV1",
        "profileQuantityOriginDuplicateV1",
        "profileQuantityOriginKeepV1",
        "resolveQuantityOriginControlNameV1",
        "normalizeProcessQuantityRules",
    ]

    missing_js = [
        marker for marker in required_js_markers
        if marker not in js_content
    ]

    if missing_js:
        raise RuntimeError("Marcadores ausentes no new_user.js: " + ", ".join(missing_js))

    if "new_user.js?v=20260503-quantity-origin-dedup-v1" not in template_content:
        raise RuntimeError("Cache buster esperado nao encontrado no template.")

    print("OK: deduplicacao do campo origem dos Campos Quantidade inserida.")
    print("OK: template atualizado com cache buster.")
    print("OK: validacao de conteudo concluida.")


####################################################################################
# (7) EXECUCAO
####################################################################################

def main() -> None:
    require_file_v1(NEW_USER_JS_PATH)
    require_file_v1(TEMPLATE_PATH)

    js_backup = backup_file_v1(NEW_USER_JS_PATH, "quantity_origin_dedup_v1")
    template_backup = backup_file_v1(TEMPLATE_PATH, "quantity_origin_dedup_v1")

    print(f"OK: backup criado: {js_backup}")
    print(f"OK: backup criado: {template_backup}")

    patch_new_user_js_v1()
    patch_template_v1()
    validate_v1()

    print("OK: patch quantity origin dedup concluido.")


if __name__ == "__main__":
    main()
