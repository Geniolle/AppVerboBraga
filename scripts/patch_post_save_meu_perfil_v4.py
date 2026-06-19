from __future__ import annotations

import re
from pathlib import Path


####################################################################################
# (1) CONFIGURAÇÃO
####################################################################################

NEW_USER_JS_PATH = Path("static/js/new_user.js")


####################################################################################
# (2) FUNÇÕES AUXILIARES
####################################################################################

def read_text_v1(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text_v1(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def require_text_v1(content: str, marker: str) -> None:
    if marker not in content:
        raise RuntimeError(f"Marcador obrigatório não encontrado: {marker}")


####################################################################################
# (3) NOVA FUNÇÃO DE RETORNO PÓS-GUARDAR
####################################################################################

BUILD_POST_SAVE_RETURN_URL_V4 = r'''  function buildPostSaveReturnUrlV4(form) {
    const sourceUrl = getCurrentUrlPostSaveV3();
    const currentUrl = new URL("/users/new", window.location.origin);

    if (sourceUrl && sourceUrl.hash) {
      currentUrl.hash = sourceUrl.hash;
    }

    const action = getFormActionPostSaveV3(form);
    const actionLookup = normalizePostSaveLookupV3(action);
    const formMenuKey = normalizePostSaveKeyV3(
      readFirstFormValuePostSaveV3(form, [
        "menu",
        "menu_key",
        "process_menu_key",
        "dynamic_menu_key",
        "settings_edit_key"
      ])
    );
    const activeMenuCandidate = normalizePostSaveKeyV3(
      typeof activeMenuKey !== "undefined" ? activeMenuKey : ""
    );
    let menuKey = formMenuKey || activeMenuCandidate || currentMenuFromUrlOrBootstrapPostSaveV3(form);

    //###################################################################################
    // (1) DETETAR ROTAS DO MEU PERFIL
    //###################################################################################

    function getProfileEndpointContextPostSaveV4() {
      if (actionLookup.includes("/users/profile/personal")) {
        return {
          tab: "pessoal",
          target: "#perfil-pessoal-card",
          keepProfileSection: true
        };
      }

      if (actionLookup.includes("/users/profile/address")) {
        return {
          tab: "morada",
          target: "#perfil-morada-card",
          keepProfileSection: false
        };
      }

      if (actionLookup.includes("/users/profile/training")) {
        return {
          tab: "treinamento",
          target: "#dados-treinamento-card",
          keepProfileSection: false
        };
      }

      if (actionLookup.includes("/users/profile/whatsapp/verify")) {
        return {
          tab: "pessoal",
          target: "#perfil-pessoal-card",
          keepProfileSection: true
        };
      }

      return null;
    }

    //###################################################################################
    // (2) LER ABA DINÂMICA APENAS DO FORM SUBMETIDO
    //###################################################################################

    function getDynamicSectionScopedPostSaveV4(cleanMenuKey) {
      const formValue = readFirstFormValuePostSaveV3(form, [
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
        cleanMenuKey &&
        selectedDynamicSectionByMenu[cleanMenuKey]
      ) {
        return normalizePostSaveKeyV3(selectedDynamicSectionByMenu[cleanMenuKey]);
      }

      const activeElement = form && form.querySelector
        ? form.querySelector(
            "[data-dynamic-process-section-key].active, " +
            "[data-dynamic-process-section-key][aria-selected='true'], " +
            "[data-section-key].active, " +
            "[data-section-key][aria-selected='true']"
          )
        : null;

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

    //###################################################################################
    // (3) CONSTRUIR URL LIMPA DO PROCESSO CORRETO
    //###################################################################################

    const profileContext = getProfileEndpointContextPostSaveV4();

    if (profileContext) {
      menuKey = MEU_PERFIL_MENU_KEY;

      currentUrl.searchParams.set("menu", MEU_PERFIL_MENU_KEY);
      currentUrl.searchParams.set("target", profileContext.target);
      currentUrl.searchParams.set("profile_tab", profileContext.tab);

      if (profileContext.keepProfileSection) {
        const profileSection = (
          normalizePostSaveKeyV3(readFirstFormValuePostSaveV3(form, ["profile_section"])) ||
          getCurrentProfileSectionPostSaveV3()
        );

        if (profileSection) {
          currentUrl.searchParams.set("profile_section", profileSection);
        }
      }
    } else {
      if (menuKey) {
        currentUrl.searchParams.set("menu", menuKey);
      }

      const formTarget = readFirstFormValuePostSaveV3(form, ["target", "return_target"]);

      if (formTarget) {
        currentUrl.searchParams.set("target", formTarget);
      } else if (
        menuKey &&
        typeof selectedTargetByMenu === "object" &&
        selectedTargetByMenu !== null &&
        selectedTargetByMenu[menuKey]
      ) {
        currentUrl.searchParams.set("target", selectedTargetByMenu[menuKey]);
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

      const dynamicSection = getDynamicSectionScopedPostSaveV4(menuKey);

      if (dynamicSection) {
        currentUrl.searchParams.set("dynamic_process_section", dynamicSection);
      }
    }

    currentUrl.searchParams.set("appverbo_after_save", "1");

    return currentUrl.pathname + currentUrl.search + currentUrl.hash;
  }'''


####################################################################################
# (4) APLICAR PATCH
####################################################################################

def patch_new_user_js_v1() -> None:
    content = read_text_v1(NEW_USER_JS_PATH)

    require_text_v1(content, "APPVERBO_POST_SAVE_CONTEXT_CAPTURE_V3_START")
    require_text_v1(content, "function storePostSaveContextV3(form)")
    require_text_v1(content, "const returnUrl = buildPostSaveReturnUrlV3(form);")

    patterns = [
        re.compile(
            r"  function buildPostSaveReturnUrlV4\(form\) \{.*?\n"
            r"  //###################################################################################\n"
            r"  // \(3\) GUARDAR CONTEXTO",
            flags=re.DOTALL,
        ),
        re.compile(
            r"  function buildPostSaveReturnUrlV3\(form\) \{.*?\n"
            r"  //###################################################################################\n"
            r"  // \(3\) GUARDAR CONTEXTO",
            flags=re.DOTALL,
        ),
    ]

    replaced = False

    for pattern in patterns:
        if pattern.search(content):
            content = pattern.sub(
                BUILD_POST_SAVE_RETURN_URL_V4.rstrip()
                + "\n\n  //###################################################################################\n"
                + "  // (3) GUARDAR CONTEXTO",
                content,
                count=1,
            )
            replaced = True
            break

    if not replaced:
        raise RuntimeError("Não foi possível localizar buildPostSaveReturnUrlV3/V4 no new_user.js.")

    content = content.replace(
        "const returnUrl = buildPostSaveReturnUrlV3(form);",
        "const returnUrl = buildPostSaveReturnUrlV4(form);",
    )

    required_after_patch = [
        "function buildPostSaveReturnUrlV4(form)",
        "getProfileEndpointContextPostSaveV4",
        "/users/profile/address",
        "/users/profile/training",
        "/users/profile/whatsapp/verify",
        "getDynamicSectionScopedPostSaveV4",
        "const returnUrl = buildPostSaveReturnUrlV4(form);",
    ]

    missing = [marker for marker in required_after_patch if marker not in content]

    if missing:
        raise RuntimeError("Patch incompleto. Marcadores ausentes: " + ", ".join(missing))

    write_text_v1(NEW_USER_JS_PATH, content)


####################################################################################
# (5) EXECUÇÃO
####################################################################################

def main() -> None:
    patch_new_user_js_v1()
    print("OK: new_user.js corrigido para manter o contexto correto após Guardar.")


if __name__ == "__main__":
    main()
