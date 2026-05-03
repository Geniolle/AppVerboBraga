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

START_MARKER = "// APPVERBO_MEU_PERFIL_QUANTITY_READONLY_RENDERER_V1_START"
END_MARKER = "// APPVERBO_MEU_PERFIL_QUANTITY_READONLY_RENDERER_V1_END"


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
# (3) BLOCO JS READONLY
####################################################################################

READONLY_JS_BLOCK = r"""
// APPVERBO_MEU_PERFIL_QUANTITY_READONLY_RENDERER_V1_START
//###################################################################################
// (MEU_PERFIL_QUANTITY_READONLY_RENDERER_V1) VISUALIZACAO DOS CAMPOS QUANTIDADE
//###################################################################################

(function setupMeuPerfilQuantityReadonlyRendererV1() {
  "use strict";

  //###################################################################################
  // (1) HELPERS
  //###################################################################################

  function safeTextQuantityReadonlyV1(value) {
    return String(value === null || value === undefined ? "" : value);
  }

  function getMeuPerfilSettingQuantityReadonlyV1() {
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

  function getReadonlyGridQuantityReadonlyV1() {
    return document.querySelector("#perfil-pessoal-card .profile-readonly .personal-grid");
  }

  function getQuantityReadonlyValuesV1(ruleKey) {
    const cleanRuleKey = normalizeMenuKey(ruleKey);
    const valuesByMenu = (
      menuProcessQuantityValuesMap &&
      typeof menuProcessQuantityValuesMap === "object" &&
      !Array.isArray(menuProcessQuantityValuesMap)
    )
      ? menuProcessQuantityValuesMap[MEU_PERFIL_MENU_KEY]
      : null;

    if (!valuesByMenu || typeof valuesByMenu !== "object" || Array.isArray(valuesByMenu)) {
      return [];
    }

    return normalizeProcessQuantityItems(valuesByMenu[cleanRuleKey]);
  }

  function buildFieldMetaMapQuantityReadonlyV1(setting) {
    const metaMap = new Map();

    (Array.isArray(setting && setting.process_field_options) ? setting.process_field_options : []).forEach((option) => {
      const fieldKey = normalizeMenuKey(option && option.key);

      if (!fieldKey) {
        return;
      }

      metaMap.set(fieldKey, {
        key: fieldKey,
        label: toSentenceCaseText(option.label || fieldKey),
        fieldType: normalizeProcessFieldType(option.field_type)
      });
    });

    return metaMap;
  }

  function formatReadonlyValueQuantityReadonlyV1(value, fieldType) {
    const cleanValue = safeTextQuantityReadonlyV1(value).trim();

    if (!cleanValue) {
      return "-";
    }

    if (fieldType === "flag") {
      return ["1", "true", "sim", "yes", "on"].includes(cleanValue.toLowerCase())
        ? "Sim"
        : "Não";
    }

    return cleanValue;
  }

  function applyCurrentProfileSectionToQuantityReadonlyV1(host) {
    if (!host) {
      return;
    }

    const sectionInput = document.querySelector("[data-meu-perfil-section-input]");
    const currentSection = normalizeMenuKey(sectionInput ? sectionInput.value : "");
    const hostSection = normalizeMenuKey(host.dataset.profileSectionPane);

    if (!currentSection || !hostSection) {
      return;
    }

    host.style.display = currentSection === hostSection ? "" : "none";
  }

  function findInsertionPointQuantityReadonlyV1(grid, rule) {
    if (!grid || !rule) {
      return null;
    }

    const quantityFieldKey = normalizeMenuKey(rule.quantityFieldKey);

    if (!quantityFieldKey) {
      return null;
    }

    return grid.querySelector("[data-profile-field-key='" + quantityFieldKey + "']");
  }

  //###################################################################################
  // (2) RENDERIZAR REGRA READONLY
  //###################################################################################

  function renderReadonlyRuleQuantityReadonlyV1(grid, setting, rule, fieldMetaMap) {
    const values = getQuantityReadonlyValuesV1(rule.key);

    if (!Array.isArray(values) || !values.length) {
      return;
    }

    const host = document.createElement("div");

    host.className = "personal-item profile-quantity-readonly-v1";
    host.style.gridColumn = "1 / -1";
    host.dataset.profileQuantityReadonlyRuleKey = rule.key;
    host.dataset.profileSectionPane = rule.headerKey || "";

    const mainLabel = document.createElement("span");
    mainLabel.className = "personal-label";
    mainLabel.textContent = rule.label || rule.itemLabel || "Itens";
    host.appendChild(mainLabel);

    const listWrapper = document.createElement("div");
    listWrapper.className = "profile-quantity-readonly-list-v1";

    values.forEach((itemValues, itemIndex) => {
      const itemBlock = document.createElement("div");
      itemBlock.className = "profile-quantity-readonly-item-v1";

      const itemTitle = document.createElement("strong");
      itemTitle.className = "personal-value profile-quantity-readonly-title-v1";
      itemTitle.textContent = (rule.itemLabel || "Item") + " " + (itemIndex + 1);
      itemBlock.appendChild(itemTitle);

      const fieldsList = document.createElement("div");
      fieldsList.className = "profile-quantity-readonly-fields-v1";

      rule.repeatedFieldKeys.forEach((fieldKey) => {
        const cleanFieldKey = normalizeMenuKey(fieldKey);
        const fieldMeta = fieldMetaMap.get(cleanFieldKey) || {
          label: cleanFieldKey,
          fieldType: "text"
        };

        const row = document.createElement("div");
        row.className = "profile-quantity-readonly-field-v1";

        const label = document.createElement("span");
        label.className = "personal-label";
        label.textContent = fieldMeta.label || cleanFieldKey;

        const value = document.createElement("strong");
        value.className = "personal-value";
        value.textContent = formatReadonlyValueQuantityReadonlyV1(
          itemValues ? itemValues[cleanFieldKey] : "",
          fieldMeta.fieldType
        );

        row.appendChild(label);
        row.appendChild(value);
        fieldsList.appendChild(row);
      });

      itemBlock.appendChild(fieldsList);
      listWrapper.appendChild(itemBlock);
    });

    host.appendChild(listWrapper);

    const insertionPoint = findInsertionPointQuantityReadonlyV1(grid, rule);

    if (insertionPoint && insertionPoint.parentElement === grid) {
      insertionPoint.insertAdjacentElement("afterend", host);
    } else {
      grid.appendChild(host);
    }

    applyCurrentProfileSectionToQuantityReadonlyV1(host);
  }

  //###################################################################################
  // (3) RENDERIZAR TODAS AS REGRAS
  //###################################################################################

  function renderMeuPerfilQuantityReadonlyV1() {
    const grid = getReadonlyGridQuantityReadonlyV1();
    const setting = getMeuPerfilSettingQuantityReadonlyV1();

    if (!grid || !setting) {
      return;
    }

    Array.from(grid.querySelectorAll("[data-profile-quantity-readonly-rule-key]")).forEach((element) => {
      element.remove();
    });

    const rules = normalizeProcessQuantityRules(setting.process_quantity_fields);

    if (!rules.length) {
      return;
    }

    const fieldMetaMap = buildFieldMetaMapQuantityReadonlyV1(setting);

    rules.forEach((rule) => {
      renderReadonlyRuleQuantityReadonlyV1(grid, setting, rule, fieldMetaMap);
    });
  }

  //###################################################################################
  // (4) SINCRONIZAR COM AS ABAS DO MEU PERFIL
  //###################################################################################

  function refreshMeuPerfilQuantityReadonlyVisibilityV1() {
    document
      .querySelectorAll("[data-profile-quantity-readonly-rule-key]")
      .forEach(applyCurrentProfileSectionToQuantityReadonlyV1);
  }

  document.addEventListener("click", function () {
    window.setTimeout(refreshMeuPerfilQuantityReadonlyVisibilityV1, 0);
    window.setTimeout(refreshMeuPerfilQuantityReadonlyVisibilityV1, 80);
  });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", renderMeuPerfilQuantityReadonlyV1);
  } else {
    renderMeuPerfilQuantityReadonlyV1();
  }

  window.setTimeout(renderMeuPerfilQuantityReadonlyV1, 150);
  window.setTimeout(renderMeuPerfilQuantityReadonlyV1, 600);
})();

// APPVERBO_MEU_PERFIL_QUANTITY_READONLY_RENDERER_V1_END
"""


####################################################################################
# (4) PATCH new_user.js
####################################################################################

def patch_new_user_js_v1() -> None:
    content = read_text_v1(NEW_USER_JS_PATH)

    required_markers = [
        "const menuProcessQuantityValuesMap",
        "function normalizeProcessQuantityRules",
        "function normalizeProcessQuantityItems",
        "const MEU_PERFIL_MENU_KEY",
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
        READONLY_JS_BLOCK,
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
        "new_user.js?v=20260503-meu-perfil-quantity-readonly-v1",
        content,
    )

    if "new_user.js?v=20260503-meu-perfil-quantity-readonly-v1" not in content:
        raise RuntimeError("Cache buster do new_user.js nao foi atualizado.")

    write_text_v1(TEMPLATE_PATH, content)


####################################################################################
# (6) VALIDAR CONTEUDO
####################################################################################

def validate_v1() -> None:
    js_content = read_text_v1(NEW_USER_JS_PATH)
    template_content = read_text_v1(TEMPLATE_PATH)

    required_js_markers = [
        "APPVERBO_MEU_PERFIL_QUANTITY_READONLY_RENDERER_V1_START",
        "renderMeuPerfilQuantityReadonlyV1",
        "data-profile-quantity-readonly-rule-key",
        "menuProcessQuantityValuesMap",
        "normalizeProcessQuantityItems",
        "profile-quantity-readonly-v1",
    ]

    missing_js = [
        marker for marker in required_js_markers
        if marker not in js_content
    ]

    if missing_js:
        raise RuntimeError("Marcadores ausentes no new_user.js: " + ", ".join(missing_js))

    if "new_user.js?v=20260503-meu-perfil-quantity-readonly-v1" not in template_content:
        raise RuntimeError("Cache buster esperado nao encontrado no template.")

    print("OK: readonly renderer dos Campos Quantidade inserido no new_user.js.")
    print("OK: template atualizado com cache buster.")
    print("OK: validacao de conteudo concluida.")


####################################################################################
# (7) EXECUCAO
####################################################################################

def main() -> None:
    require_file_v1(NEW_USER_JS_PATH)
    require_file_v1(TEMPLATE_PATH)

    js_backup = backup_file_v1(NEW_USER_JS_PATH, "quantity_readonly_v1")
    template_backup = backup_file_v1(TEMPLATE_PATH, "quantity_readonly_v1")

    print(f"OK: backup criado: {js_backup}")
    print(f"OK: backup criado: {template_backup}")

    patch_new_user_js_v1()
    patch_template_v1()
    validate_v1()

    print("OK: patch readonly Campos Quantidade concluido.")


if __name__ == "__main__":
    main()
