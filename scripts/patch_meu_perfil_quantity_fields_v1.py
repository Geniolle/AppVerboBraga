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
PAGE_SERVICE_PATH = PROJECT_ROOT / "appverbo" / "services" / "page.py"
TEMPLATE_PATH = PROJECT_ROOT / "templates" / "new_user.html"

MARKER_START = "// APPVERBO_MEU_PERFIL_QUANTITY_RENDERER_V1_START"
MARKER_END = "// APPVERBO_MEU_PERFIL_QUANTITY_RENDERER_V1_END"


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
# (3) BLOCO JS PARA RENDERIZAR CAMPOS QUANTIDADE NO MEU PERFIL
####################################################################################

MEU_PERFIL_QUANTITY_RENDERER_JS = r"""
// APPVERBO_MEU_PERFIL_QUANTITY_RENDERER_V1_START
//###################################################################################
// (MEU_PERFIL_QUANTITY_RENDERER_V1) CAMPOS QUANTIDADE NO FORMULARIO MEU PERFIL
//###################################################################################

(function setupMeuPerfilQuantityRendererV1() {
  "use strict";

  //###################################################################################
  // (1) HELPERS
  //###################################################################################

  function toSafeStringMeuPerfilQuantityV1(value) {
    return String(value === null || value === undefined ? "" : value);
  }

  function getMeuPerfilSettingQuantityV1() {
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

  function getFormControlByNameQuantityV1(form, name) {
    const cleanName = toSafeStringMeuPerfilQuantityV1(name);
    if (!form || !cleanName) {
      return null;
    }

    return Array.from(form.elements || []).find((element) => {
      return toSafeStringMeuPerfilQuantityV1(element.name) === cleanName;
    }) || null;
  }

  function getMeuPerfilQuantityFormV1() {
    return document.querySelector("form[action='/users/profile/personal']")
      || document.querySelector('form[action="/users/profile/personal"]');
  }

  function getMeuPerfilQuantityValuesV1(ruleKey) {
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

  function buildListOptionsMapQuantityV1(setting) {
    const optionsMap = new Map();

    (Array.isArray(setting && setting.process_lists) ? setting.process_lists : []).forEach((processList) => {
      const listKey = normalizeMenuKey(processList && processList.key);
      if (!listKey) {
        return;
      }

      optionsMap.set(
        listKey,
        Array.isArray(processList.items)
          ? processList.items.map((item) => toSafeStringMeuPerfilQuantityV1(item).trim()).filter(Boolean)
          : []
      );
    });

    return optionsMap;
  }

  function buildFieldMetaMapQuantityV1(setting) {
    const listOptionsByKey = buildListOptionsMapQuantityV1(setting);
    const fieldMetaMap = new Map();

    (Array.isArray(setting && setting.process_field_options) ? setting.process_field_options : []).forEach((option) => {
      const fieldKey = normalizeMenuKey(option && option.key);
      if (!fieldKey) {
        return;
      }

      const fieldType = normalizeProcessFieldType(option.field_type);
      const listKey = normalizeMenuKey(option.list_key || option.listKey);

      fieldMetaMap.set(fieldKey, {
        key: fieldKey,
        label: toSentenceCaseText(option.label || fieldKey),
        fieldType,
        size: normalizeProcessFieldSize(option.size, fieldType),
        isRequired: normalizeProcessFieldRequired(
          Object.prototype.hasOwnProperty.call(option, "is_required")
            ? option.is_required
            : option.required
        ),
        listKey,
        listOptions: listOptionsByKey.get(listKey) || []
      });
    });

    return fieldMetaMap;
  }

  function resolveQuantityControlNameV1(fieldKey) {
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

  function parseQuantityCountV1(rawValue, maxItems) {
    const parsedValue = Number.parseInt(toSafeStringMeuPerfilQuantityV1(rawValue).trim(), 10);
    const parsedMaxItems = Number.parseInt(toSafeStringMeuPerfilQuantityV1(maxItems || "1").trim(), 10);
    const safeMaxItems = Number.isFinite(parsedMaxItems) ? Math.min(Math.max(parsedMaxItems, 1), 50) : 1;

    if (!Number.isFinite(parsedValue) || parsedValue <= 0) {
      return 0;
    }

    return Math.min(parsedValue, safeMaxItems);
  }

  function readQuantityControlValueV1(control, fieldType) {
    if (!control) {
      return "";
    }

    if (fieldType === "flag") {
      return control.checked ? "1" : "0";
    }

    return toSafeStringMeuPerfilQuantityV1(control.value).trim();
  }

  function createQuantityFieldControlV1(rule, itemIndex, fieldMeta, existingValue) {
    const fieldType = normalizeProcessFieldType(fieldMeta.fieldType);
    const fieldName = "process_quantity_field__" + rule.key + "__" + itemIndex + "__" + fieldMeta.key;
    let control = null;

    if (fieldType === "list") {
      control = document.createElement("select");
      const emptyOption = document.createElement("option");
      emptyOption.value = "";
      emptyOption.textContent = "Selecione";
      control.appendChild(emptyOption);

      (Array.isArray(fieldMeta.listOptions) ? fieldMeta.listOptions : []).forEach((optionValue) => {
        const option = document.createElement("option");
        option.value = optionValue;
        option.textContent = optionValue;
        if (toSafeStringMeuPerfilQuantityV1(existingValue) === toSafeStringMeuPerfilQuantityV1(optionValue)) {
          option.selected = true;
        }
        control.appendChild(option);
      });
    } else {
      control = document.createElement("input");
      if (fieldType === "email") {
        control.type = "email";
      } else if (fieldType === "phone") {
        control.type = "tel";
      } else if (fieldType === "number") {
        control.type = "number";
      } else if (fieldType === "date") {
        control.type = "date";
      } else if (fieldType === "flag") {
        control.type = "checkbox";
        control.value = "1";
        control.checked = ["1", "true", "sim", "yes", "on"].includes(
          toSafeStringMeuPerfilQuantityV1(existingValue).trim().toLowerCase()
        );
      } else {
        control.type = "text";
      }

      if (fieldType !== "flag") {
        control.value = toSafeStringMeuPerfilQuantityV1(existingValue);
      }
    }

    control.name = fieldName;
    control.dataset.processQuantityRuleKey = rule.key;
    control.dataset.processQuantityItemIndex = String(itemIndex);
    control.dataset.processQuantityFieldKey = fieldMeta.key;

    if (fieldMeta.isRequired && fieldType !== "flag") {
      control.required = true;
    }

    if (fieldMeta.size && ["text", "email", "phone"].includes(fieldType)) {
      control.maxLength = fieldMeta.size;
    }

    return control;
  }

  function syncQuantityPayloadV1(rule, host) {
    const rows = Array.from(host.querySelectorAll("[data-process-quantity-item-index]"));
    const payload = [];

    rows.forEach((row) => {
      const item = {};

      Array.from(row.querySelectorAll("[data-process-quantity-field-key]")).forEach((control) => {
        const fieldKey = normalizeMenuKey(control.dataset.processQuantityFieldKey);
        if (!fieldKey) {
          return;
        }

        const fieldType = normalizeProcessFieldType(control.dataset.processQuantityFieldType || control.type);
        const value = readQuantityControlValueV1(control, fieldType);

        if (value) {
          item[fieldKey] = value;
        }
      });

      payload.push(item);
    });

    const payloadInput = host.querySelector("input[name='process_quantity_payload__" + rule.key + "']");
    if (payloadInput) {
      payloadInput.value = JSON.stringify(payload);
    }
  }

  //###################################################################################
  // (2) RENDERIZAR UMA REGRA
  //###################################################################################

  function setupMeuPerfilQuantityRuleV1(form, setting, rule, fieldMetaMap) {
    const quantityControlName = resolveQuantityControlNameV1(rule.quantityFieldKey);
    const quantityControl = getFormControlByNameQuantityV1(form, quantityControlName);

    if (!quantityControl) {
      return;
    }

    const quantityFieldWrapper = quantityControl.closest(".field") || quantityControl.parentElement;
    const personalGrid = quantityControl.closest(".personal-grid") || form.querySelector(".personal-grid") || form;
    const sectionPane = rule.headerKey
      || toSafeStringMeuPerfilQuantityV1(quantityFieldWrapper && quantityFieldWrapper.dataset.profileSectionPane)
      || "";

    let host = form.querySelector("[data-profile-quantity-rule-key='" + rule.key + "']");

    if (!host) {
      host = document.createElement("div");
      host.className = "field full profile-quantity-rule-v1";
      host.dataset.profileQuantityRuleKey = rule.key;
      host.dataset.profileSectionPane = sectionPane;

      if (quantityFieldWrapper && quantityFieldWrapper.parentElement) {
        quantityFieldWrapper.insertAdjacentElement("afterend", host);
      } else {
        personalGrid.appendChild(host);
      }
    }

    let payloadInput = host.querySelector("input[name='process_quantity_payload__" + rule.key + "']");

    if (!payloadInput) {
      payloadInput = document.createElement("input");
      payloadInput.type = "hidden";
      payloadInput.name = "process_quantity_payload__" + rule.key;
      payloadInput.value = "[]";
      host.appendChild(payloadInput);
    }

    function renderQuantityBlocksV1() {
      const existingItems = getMeuPerfilQuantityValuesV1(rule.key);
      const requestedCount = parseQuantityCountV1(quantityControl.value, rule.maxItems);
      const fallbackCount = requestedCount || existingItems.length;
      const count = parseQuantityCountV1(String(fallbackCount), rule.maxItems);

      Array.from(host.querySelectorAll(".profile-quantity-items-wrap-v1")).forEach((element) => {
        element.remove();
      });

      if (!count) {
        payloadInput.value = "[]";
        return;
      }

      const wrapper = document.createElement("div");
      wrapper.className = "profile-quantity-items-wrap-v1";
      wrapper.dataset.processQuantityRuleKey = rule.key;

      for (let itemIndex = 0; itemIndex < count; itemIndex += 1) {
        const itemValues = existingItems[itemIndex] || {};
        const itemBlock = document.createElement("div");
        itemBlock.className = "profile-quantity-item-v1";
        itemBlock.dataset.processQuantityItemIndex = String(itemIndex);

        const itemTitle = document.createElement("h4");
        itemTitle.className = "profile-quantity-item-title-v1";
        itemTitle.textContent = (rule.itemLabel || "Item") + " " + (itemIndex + 1);
        itemBlock.appendChild(itemTitle);

        const fieldsGrid = document.createElement("div");
        fieldsGrid.className = "personal-grid profile-quantity-item-grid-v1";

        rule.repeatedFieldKeys.forEach((fieldKey) => {
          const fieldMeta = fieldMetaMap.get(fieldKey);

          if (!fieldMeta) {
            return;
          }

          const fieldWrapper = document.createElement("div");
          fieldWrapper.className = "field";
          fieldWrapper.dataset.profileSectionPane = sectionPane;
          fieldWrapper.dataset.profileFieldKey = fieldKey;

          const label = document.createElement("label");
          label.textContent = fieldMeta.label + (fieldMeta.isRequired ? " *" : "");

          const control = createQuantityFieldControlV1(
            rule,
            itemIndex,
            fieldMeta,
            itemValues[fieldKey] || ""
          );

          control.dataset.processQuantityFieldType = fieldMeta.fieldType;

          control.addEventListener("input", function () {
            syncQuantityPayloadV1(rule, host);
          });
          control.addEventListener("change", function () {
            syncQuantityPayloadV1(rule, host);
          });

          fieldWrapper.appendChild(label);
          fieldWrapper.appendChild(control);
          fieldsGrid.appendChild(fieldWrapper);
        });

        itemBlock.appendChild(fieldsGrid);
        wrapper.appendChild(itemBlock);
      }

      host.appendChild(wrapper);
      syncQuantityPayloadV1(rule, host);
    }

    quantityControl.addEventListener("input", renderQuantityBlocksV1);
    quantityControl.addEventListener("change", renderQuantityBlocksV1);

    if (!toSafeStringMeuPerfilQuantityV1(quantityControl.value).trim()) {
      const existingItems = getMeuPerfilQuantityValuesV1(rule.key);
      if (existingItems.length) {
        quantityControl.value = String(Math.min(existingItems.length, rule.maxItems || existingItems.length));
      }
    }

    renderQuantityBlocksV1();
  }

  //###################################################################################
  // (3) INICIALIZAR TODAS AS REGRAS
  //###################################################################################

  function setupMeuPerfilQuantityRulesV1() {
    const form = getMeuPerfilQuantityFormV1();
    const setting = getMeuPerfilSettingQuantityV1();

    if (!form || !setting || form.dataset.meuPerfilQuantityRendererBoundV1 === "1") {
      return;
    }

    const rules = normalizeProcessQuantityRules(setting.process_quantity_fields);

    if (!rules.length) {
      return;
    }

    const fieldMetaMap = buildFieldMetaMapQuantityV1(setting);

    form.dataset.meuPerfilQuantityRendererBoundV1 = "1";

    rules.forEach((rule) => {
      setupMeuPerfilQuantityRuleV1(form, setting, rule, fieldMetaMap);
    });

    form.addEventListener("submit", function () {
      Array.from(form.querySelectorAll("[data-profile-quantity-rule-key]")).forEach((host) => {
        const ruleKey = normalizeMenuKey(host.dataset.profileQuantityRuleKey);
        const rule = rules.find((item) => item.key === ruleKey);
        if (rule) {
          syncQuantityPayloadV1(rule, host);
        }
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setupMeuPerfilQuantityRulesV1);
  } else {
    setupMeuPerfilQuantityRulesV1();
  }

  window.setTimeout(setupMeuPerfilQuantityRulesV1, 150);
  window.setTimeout(setupMeuPerfilQuantityRulesV1, 600);
})();

// APPVERBO_MEU_PERFIL_QUANTITY_RENDERER_V1_END
"""


####################################################################################
# (4) PATCH DO new_user.js
####################################################################################

def patch_new_user_js_v1() -> None:
    content = read_text_v1(NEW_USER_JS_PATH)

    required_markers = [
        "const menuProcessQuantityValuesMap",
        "function normalizeProcessQuantityRules",
        "function normalizeProcessQuantityItems",
        "function normalizeProcessFieldType",
        "function normalizeProcessFieldSize",
        "function normalizeProcessFieldRequired",
    ]

    missing = [
        marker for marker in required_markers
        if marker not in content
    ]

    if missing:
        raise RuntimeError("Marcadores obrigatorios ausentes no new_user.js: " + ", ".join(missing))

    content = replace_marker_block_v1(
        content,
        MARKER_START,
        MARKER_END,
        MEU_PERFIL_QUANTITY_RENDERER_JS,
    )

    write_text_v1(NEW_USER_JS_PATH, content)


####################################################################################
# (5) PATCH DO page.py PARA CARREGAR VALORES DO meu_perfil
####################################################################################

def patch_page_service_v1() -> None:
    content = read_text_v1(PAGE_SERVICE_PATH)

    old_text = 'if not menu_key or menu_key in {"home", "perfil", "administrativo", MENU_MEU_PERFIL_KEY}:'
    new_text = 'if not menu_key or menu_key in {"home", "perfil", "administrativo"}:'

    if old_text in content:
        content = content.replace(old_text, new_text, 1)
    elif new_text not in content:
        raise RuntimeError("Nao encontrei o filtro de menus no page.py para ajustar o carregamento do meu_perfil.")

    write_text_v1(PAGE_SERVICE_PATH, content)


####################################################################################
# (6) PATCH CACHE BUSTER DO new_user.js
####################################################################################

def patch_template_cache_buster_v1() -> None:
    content = read_text_v1(TEMPLATE_PATH)

    if "new_user.js" not in content:
        raise RuntimeError("Nao encontrei carregamento de new_user.js no template.")

    content = re.sub(
        r'new_user\.js\?v=[^"]+',
        "new_user.js?v=20260503-meu-perfil-quantity-renderer-v1",
        content,
    )

    if "new_user.js?v=20260503-meu-perfil-quantity-renderer-v1" not in content:
        raise RuntimeError("Cache buster do new_user.js nao foi atualizado.")

    write_text_v1(TEMPLATE_PATH, content)


####################################################################################
# (7) VALIDACAO DE CONTEUDO
####################################################################################

def validate_content_v1() -> None:
    js_content = read_text_v1(NEW_USER_JS_PATH)
    page_content = read_text_v1(PAGE_SERVICE_PATH)
    template_content = read_text_v1(TEMPLATE_PATH)

    required_js_markers = [
        "APPVERBO_MEU_PERFIL_QUANTITY_RENDERER_V1_START",
        "setupMeuPerfilQuantityRuleV1",
        "process_quantity_field__",
        "process_quantity_payload__",
        "quantityControl.addEventListener",
        "renderQuantityBlocksV1",
    ]

    missing_js = [
        marker for marker in required_js_markers
        if marker not in js_content
    ]

    if missing_js:
        raise RuntimeError("Marcadores ausentes no new_user.js: " + ", ".join(missing_js))

    if 'if not menu_key or menu_key in {"home", "perfil", "administrativo", MENU_MEU_PERFIL_KEY}:' in page_content:
        raise RuntimeError("page.py ainda ignora MENU_MEU_PERFIL_KEY no carregamento de valores de quantidade.")

    if "new_user.js?v=20260503-meu-perfil-quantity-renderer-v1" not in template_content:
        raise RuntimeError("Template nao esta com o cache buster esperado para new_user.js.")

    print("OK: renderer de Campos Quantidade do Meu perfil adicionado.")
    print("OK: page.py ajustado para carregar valores de quantidade do meu_perfil.")
    print("OK: cache buster do new_user.js atualizado.")


####################################################################################
# (8) EXECUCAO
####################################################################################

def main() -> None:
    require_file_v1(NEW_USER_JS_PATH)
    require_file_v1(PAGE_SERVICE_PATH)
    require_file_v1(TEMPLATE_PATH)

    js_backup = backup_file_v1(NEW_USER_JS_PATH, "meu_perfil_quantity_v1")
    page_backup = backup_file_v1(PAGE_SERVICE_PATH, "meu_perfil_quantity_v1")
    template_backup = backup_file_v1(TEMPLATE_PATH, "meu_perfil_quantity_v1")

    print(f"OK: backup criado: {js_backup}")
    print(f"OK: backup criado: {page_backup}")
    print(f"OK: backup criado: {template_backup}")

    patch_new_user_js_v1()
    patch_page_service_v1()
    patch_template_cache_buster_v1()
    validate_content_v1()

    print("OK: patch concluido.")


if __name__ == "__main__":
    main()
