from __future__ import annotations

import re
from pathlib import Path


####################################################################################
# (1) CONFIGURAÇÃO
####################################################################################

NEW_USER_JS_PATH = Path("static/js/new_user.js")
PROFILE_HANDLERS_PATH = Path("appverbo/routes/profile/profile_handlers.py")
TEMPLATE_PATH = Path("templates/new_user.html")

JS_SCOPE_START = "// APPVERBO_MEU_PERFIL_POST_SAVE_SCOPE_FIX_V5_START"
JS_SCOPE_END = "// APPVERBO_MEU_PERFIL_POST_SAVE_SCOPE_FIX_V5_END"
BACKEND_START = "# APPVERBO_MEU_PERFIL_RETURN_URL_CLEAN_CONTEXT_V5_START"
BACKEND_END = "# APPVERBO_MEU_PERFIL_RETURN_URL_CLEAN_CONTEXT_V5_END"


####################################################################################
# (2) FUNÇÕES AUXILIARES
####################################################################################

def read_text_v1(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text_v1(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def require_text_v1(content: str, marker: str, path: Path) -> None:
    if marker not in content:
        raise RuntimeError(f"Marcador obrigatório não encontrado em {path}: {marker}")


def replace_marker_block_v1(content: str, start_marker: str, end_marker: str, new_block: str) -> str:
    pattern = re.compile(
        re.escape(start_marker) + r".*?" + re.escape(end_marker),
        flags=re.DOTALL,
    )

    if pattern.search(content):
        return pattern.sub(new_block.strip(), content)

    return content.rstrip() + "\n\n" + new_block.strip() + "\n"


####################################################################################
# (3) NOVA FUNÇÃO FRONTEND PARA URL LIMPA DO MEU PERFIL
####################################################################################

BUILD_RETURN_URL_V5 = r'''  function buildPostSaveReturnUrlV5(form) {
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
    // (1) DETETAR ENDPOINTS DO MEU PERFIL
    //###################################################################################

    function getProfileEndpointContextPostSaveV5() {
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

    function getDynamicSectionScopedPostSaveV5(cleanMenuKey) {
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
    // (3) CONSTRUIR URL DO PROCESSO CORRETO, SEM HERDAR PARÂMETROS EXTERNOS
    //###################################################################################

    const profileContext = getProfileEndpointContextPostSaveV5();

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

      const dynamicSection = getDynamicSectionScopedPostSaveV5(menuKey);

      if (dynamicSection) {
        currentUrl.searchParams.set("dynamic_process_section", dynamicSection);
      }
    }

    currentUrl.searchParams.set("appverbo_after_save", "1");

    return currentUrl.pathname + currentUrl.search + currentUrl.hash;
  }'''


####################################################################################
# (4) BLOCO FRONTEND PARA ESCONDER CARDS FORA DO MEU PERFIL APÓS GRAVAR
####################################################################################

JS_SCOPE_FIX_V5 = r'''// APPVERBO_MEU_PERFIL_POST_SAVE_SCOPE_FIX_V5_START
//###################################################################################
// (MEU_PERFIL_POST_SAVE_SCOPE_FIX_V5) MANTER APENAS O CARD DO PROCESSO APÓS GUARDAR
//###################################################################################

(function setupMeuPerfilPostSaveScopeFixV5() {
  "use strict";

  //###################################################################################
  // (1) HELPERS
  //###################################################################################

  function safeTextV5(value) {
    return String(value === null || value === undefined ? "" : value);
  }

  function normalizeKeyV5(value) {
    if (typeof normalizeMenuKey === "function") {
      return normalizeMenuKey(value);
    }

    return safeTextV5(value).trim().toLowerCase();
  }

  function getCurrentUrlV5() {
    try {
      return new URL(window.location.href);
    } catch (error) {
      return null;
    }
  }

  function isMeuPerfilContextV5(url) {
    if (!url) {
      return false;
    }

    const menuKey = normalizeKeyV5(url.searchParams.get("menu"));
    const target = safeTextV5(url.searchParams.get("target")).trim();
    const hasProfileParam = Boolean(
      safeTextV5(url.searchParams.get("profile_tab")).trim() ||
      safeTextV5(url.searchParams.get("profile_section")).trim() ||
      safeTextV5(url.searchParams.get("profile_success")).trim() ||
      safeTextV5(url.searchParams.get("profile_error")).trim() ||
      target.startsWith("#perfil-") ||
      target === "#dados-treinamento-card"
    );

    return (menuKey === "meu_perfil" || menuKey === "documentos") && hasProfileParam;
  }

  function hideElementV5(element) {
    if (!element) {
      return;
    }

    element.hidden = true;
    element.style.display = "none";
  }

  function showElementV5(element) {
    if (!element) {
      return;
    }

    element.hidden = false;
    element.style.display = "";
  }

  function getTargetSelectorV5(url) {
    const rawTarget = safeTextV5(url && url.searchParams.get("target")).trim();
    const profileTab = normalizeKeyV5(url && url.searchParams.get("profile_tab"));

    if (
      rawTarget === "#perfil-pessoal-card" ||
      rawTarget === "#perfil-morada-card" ||
      rawTarget === "#dados-treinamento-card"
    ) {
      return rawTarget;
    }

    if (profileTab === "morada") {
      return "#perfil-morada-card";
    }

    if (profileTab === "treinamento") {
      return "#dados-treinamento-card";
    }

    return "#perfil-pessoal-card";
  }

  //###################################################################################
  // (2) LIMPAR PARÂMETROS DE OUTROS PROCESSOS NA URL VISÍVEL
  //###################################################################################

  function cleanVisibleProfileUrlV5(url) {
    if (!url || !window.history || typeof window.history.replaceState !== "function") {
      return;
    }

    const keysToRemove = [
      "admin_tab",
      "settings_action",
      "settings_edit_key",
      "settings_tab",
      "dynamic_process_section",
      "entity_id",
      "member_id",
      "user_id"
    ];

    let changed = false;

    keysToRemove.forEach((key) => {
      if (url.searchParams.has(key)) {
        url.searchParams.delete(key);
        changed = true;
      }
    });

    url.searchParams.set("menu", "meu_perfil");

    if (!url.searchParams.get("target")) {
      url.searchParams.set("target", getTargetSelectorV5(url));
      changed = true;
    }

    if (!changed) {
      return;
    }

    const cleanQuery = url.searchParams.toString();
    const cleanUrl = url.pathname + (cleanQuery ? "?" + cleanQuery : "") + url.hash;

    window.history.replaceState(window.history.state, document.title, cleanUrl);
  }

  //###################################################################################
  // (3) APLICAR ESCOPO VISUAL DO MEU PERFIL
  //###################################################################################

  function applyMeuPerfilScopeV5() {
    const url = getCurrentUrlV5();

    if (!isMeuPerfilContextV5(url)) {
      return;
    }

    cleanVisibleProfileUrlV5(url);

    const targetSelector = getTargetSelectorV5(url);
    const profileCards = [
      "#perfil-pessoal-card",
      "#perfil-morada-card",
      "#dados-treinamento-card"
    ];

    profileCards.forEach((selector) => {
      const card = document.querySelector(selector);

      if (selector === targetSelector) {
        showElementV5(card);
      } else {
        hideElementV5(card);
      }
    });

    [
      "#home-summary-card",
      "#sessao-card",
      "#dynamic-process-card",
      "#settings-menu-edit-card",
      "#entities-card",
      "#entity-card",
      "#users-card",
      "#user-list-card"
    ].forEach((selector) => {
      const element = document.querySelector(selector);

      if (element && selector !== targetSelector) {
        hideElementV5(element);
      }
    });

    const targetElement = document.querySelector(targetSelector);

    if (targetElement) {
      showElementV5(targetElement);
    }

    const profileSection = normalizeKeyV5(url.searchParams.get("profile_section"));

    if (profileSection && targetSelector === "#perfil-pessoal-card") {
      document
        .querySelectorAll("#perfil-pessoal-card [data-profile-section-pane]")
        .forEach((pane) => {
          const paneKey = normalizeKeyV5(
            pane.dataset.profileSectionPane ||
            pane.dataset.profileSectionKey ||
            pane.dataset.sectionKey ||
            ""
          );

          if (paneKey && paneKey !== profileSection) {
            hideElementV5(pane);
          } else {
            showElementV5(pane);
          }
        });

      document
        .querySelectorAll(
          "#perfil-pessoal-card [data-profile-section-tab], " +
          "#perfil-pessoal-card [data-profile-section-button]"
        )
        .forEach((button) => {
          const buttonKey = normalizeKeyV5(
            button.dataset.profileSection ||
            button.dataset.profileSectionKey ||
            button.dataset.profileSectionTab ||
            button.dataset.sectionKey ||
            ""
          );

          const isActive = Boolean(buttonKey && buttonKey === profileSection);

          button.classList.toggle("active", isActive);
          button.setAttribute("aria-selected", isActive ? "true" : "false");
        });
    }
  }

  //###################################################################################
  // (4) EXECUTAR APÓS O CARREGAMENTO E APÓS OUTRAS ROTINAS DO ECRÃ
  //###################################################################################

  function scheduleMeuPerfilScopeV5() {
    applyMeuPerfilScopeV5();
    window.setTimeout(applyMeuPerfilScopeV5, 50);
    window.setTimeout(applyMeuPerfilScopeV5, 250);
    window.setTimeout(applyMeuPerfilScopeV5, 800);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", scheduleMeuPerfilScopeV5);
  } else {
    scheduleMeuPerfilScopeV5();
  }
})();

// APPVERBO_MEU_PERFIL_POST_SAVE_SCOPE_FIX_V5_END'''


####################################################################################
# (5) PATCH FRONTEND
####################################################################################

def patch_new_user_js_v1() -> None:
    content = read_text_v1(NEW_USER_JS_PATH)

    require_text_v1(content, "APPVERBO_POST_SAVE_CONTEXT_CAPTURE_V3_START", NEW_USER_JS_PATH)
    require_text_v1(content, "function storePostSaveContextV3(form)", NEW_USER_JS_PATH)

    patterns = [
        re.compile(
            r"  function buildPostSaveReturnUrlV5\(form\) \{.*?\n"
            r"  //###################################################################################\n"
            r"  // \(3\) GUARDAR CONTEXTO",
            flags=re.DOTALL,
        ),
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
                BUILD_RETURN_URL_V5.rstrip()
                + "\n\n  //###################################################################################\n"
                + "  // (3) GUARDAR CONTEXTO",
                content,
                count=1,
            )
            replaced = True
            break

    if not replaced:
        raise RuntimeError("Não foi possível localizar buildPostSaveReturnUrlV3/V4/V5 no new_user.js.")

    content = re.sub(
        r"const returnUrl = buildPostSaveReturnUrlV[345]\(form\);",
        "const returnUrl = buildPostSaveReturnUrlV5(form);",
        content,
        count=1,
    )

    content = replace_marker_block_v1(
        content,
        JS_SCOPE_START,
        JS_SCOPE_END,
        JS_SCOPE_FIX_V5,
    )

    required_markers = [
        "function buildPostSaveReturnUrlV5(form)",
        "getProfileEndpointContextPostSaveV5",
        "currentUrl = new URL(\"/users/new\", window.location.origin)",
        "const returnUrl = buildPostSaveReturnUrlV5(form);",
        "APPVERBO_MEU_PERFIL_POST_SAVE_SCOPE_FIX_V5_START",
        "cleanVisibleProfileUrlV5",
        "admin_tab",
        "#home-summary-card",
        "#perfil-morada-card",
        "#dados-treinamento-card",
    ]

    missing = [marker for marker in required_markers if marker not in content]

    if missing:
        raise RuntimeError("Patch frontend incompleto. Marcadores ausentes: " + ", ".join(missing))

    write_text_v1(NEW_USER_JS_PATH, content)


####################################################################################
# (6) PATCH BACKEND PARA LIMPAR RETURN_URL DO MEU PERFIL
####################################################################################

BACKEND_CLEAN_BLOCK_V5 = r'''    # APPVERBO_MEU_PERFIL_RETURN_URL_CLEAN_CONTEXT_V5_START
    # Quando o POST pertence ao Meu perfil, a return_url não pode carregar
    # parâmetros de Administrativo/Home/Processos dinâmicos, pois isso faz
    # aparecer cards aleatórios após Guardar.
    has_meu_perfil_context_v5 = any(
        str((extra_params or {}).get(key) or "").strip()
        for key in (
            "profile_success",
            "profile_error",
            "profile_tab",
            "profile_section",
        )
    )

    if has_meu_perfil_context_v5:
        for stale_key in (
            "admin_tab",
            "settings_action",
            "settings_edit_key",
            "settings_tab",
            "dynamic_process_section",
            "entity_id",
            "member_id",
            "user_id",
        ):
            query_params.pop(stale_key, None)

        profile_tab_v5 = str(
            (extra_params or {}).get("profile_tab")
            or query_params.get("profile_tab")
            or "pessoal"
        ).strip().lower()

        if profile_tab_v5 == "morada":
            profile_target_v5 = "#perfil-morada-card"
        elif profile_tab_v5 == "treinamento":
            profile_target_v5 = "#dados-treinamento-card"
        else:
            profile_tab_v5 = "pessoal"
            profile_target_v5 = "#perfil-pessoal-card"

        query_params["menu"] = MENU_MEU_PERFIL_KEY
        query_params["target"] = profile_target_v5
        query_params["profile_tab"] = profile_tab_v5
    # APPVERBO_MEU_PERFIL_RETURN_URL_CLEAN_CONTEXT_V5_END'''


def patch_profile_handlers_v1() -> None:
    content = read_text_v1(PROFILE_HANDLERS_PATH)

    require_text_v1(content, "def _sanitize_users_new_return_url_post_save_v6(", PROFILE_HANDLERS_PATH)
    require_text_v1(content, "query_params = dict(parse_qsl(parsed_url.query, keep_blank_values=True))", PROFILE_HANDLERS_PATH)

    content = re.sub(
        re.escape(BACKEND_START) + r".*?" + re.escape(BACKEND_END) + r"\n?",
        "",
        content,
        flags=re.DOTALL,
    )

    target = "    query_params = dict(parse_qsl(parsed_url.query, keep_blank_values=True))\n\n"
    replacement = target + BACKEND_CLEAN_BLOCK_V5 + "\n\n"

    if target not in content:
        raise RuntimeError("Ponto de inserção backend não encontrado.")

    content = content.replace(target, replacement, 1)

    required_markers = [
        "APPVERBO_MEU_PERFIL_RETURN_URL_CLEAN_CONTEXT_V5_START",
        "has_meu_perfil_context_v5",
        "query_params.pop(stale_key, None)",
        "query_params[\"menu\"] = MENU_MEU_PERFIL_KEY",
        "profile_target_v5 = \"#perfil-pessoal-card\"",
    ]

    missing = [marker for marker in required_markers if marker not in content]

    if missing:
        raise RuntimeError("Patch backend incompleto. Marcadores ausentes: " + ", ".join(missing))

    write_text_v1(PROFILE_HANDLERS_PATH, content)


####################################################################################
# (7) PATCH CACHE BUSTER
####################################################################################

def patch_template_v1() -> None:
    content = read_text_v1(TEMPLATE_PATH)

    require_text_v1(content, "new_user.js", TEMPLATE_PATH)

    updated = re.sub(
        r'new_user\.js\?v=[^"\']+',
        "new_user.js?v=20260506-meu-perfil-post-save-scope-v5",
        content,
    )

    if updated == content:
        updated = content.replace(
            "new_user.js",
            "new_user.js?v=20260506-meu-perfil-post-save-scope-v5",
            1,
        )

    require_text_v1(
        updated,
        "new_user.js?v=20260506-meu-perfil-post-save-scope-v5",
        TEMPLATE_PATH,
    )

    write_text_v1(TEMPLATE_PATH, updated)


####################################################################################
# (8) EXECUÇÃO
####################################################################################

def main() -> None:
    patch_new_user_js_v1()
    patch_profile_handlers_v1()
    patch_template_v1()

    print("OK: frontend corrigido para gerar return_url limpa do Meu perfil.")
    print("OK: backend corrigido para remover admin_tab/settings/dynamic da return_url do Meu perfil.")
    print("OK: cache buster atualizado.")


if __name__ == "__main__":
    main()
