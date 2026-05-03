from __future__ import annotations

import re
import shutil
from datetime import datetime
from pathlib import Path


####################################################################################
# (1) CONFIGURACAO
####################################################################################

PROJECT_ROOT = Path.cwd()

PROFILE_HANDLERS_PATH = PROJECT_ROOT / "appverbo" / "routes" / "profile" / "profile_handlers.py"
NEW_USER_JS_PATH = PROJECT_ROOT / "static" / "js" / "new_user.js"
TEMPLATE_PATH = PROJECT_ROOT / "templates" / "new_user.html"

JS_START_MARKER = "// APPVERBO_RETURN_URL_POST_SAVE_CAPTURE_V4_START"
JS_END_MARKER = "// APPVERBO_RETURN_URL_POST_SAVE_CAPTURE_V4_END"

PY_START_MARKER = "# APPVERBO_RETURN_URL_POST_SAVE_V4_START"
PY_END_MARKER = "# APPVERBO_RETURN_URL_POST_SAVE_V4_END"


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
# (3) HELPER PYTHON PARA RESPEITAR return_url
####################################################################################

PY_HELPER_BLOCK = r'''
# APPVERBO_RETURN_URL_POST_SAVE_V4_START
def _sanitize_users_new_return_url_post_save_v4(
    raw_return_url: Any,
    extra_params: dict[str, Any] | None = None,
) -> str:
    clean_return_url = str(raw_return_url or "").strip()

    if not clean_return_url:
        return ""

    try:
        parsed_url = urlsplit(clean_return_url)
    except Exception:
        return ""

    if parsed_url.scheme or parsed_url.netloc:
        return ""

    path = parsed_url.path or "/users/new"

    if path != "/users/new":
        return ""

    query_params = dict(parse_qsl(parsed_url.query, keep_blank_values=True))
    query_params["appverbo_after_save"] = "1"

    for raw_key, raw_value in (extra_params or {}).items():
        clean_key = str(raw_key or "").strip()
        clean_value = str(raw_value or "").strip()

        if clean_key and clean_value:
            query_params[clean_key] = clean_value

    query_string = urlencode(query_params)
    fragment = f"#{parsed_url.fragment}" if parsed_url.fragment else ""

    return f"{path}?{query_string}{fragment}" if query_string else f"{path}{fragment}"


def _append_after_save_marker_to_users_new_url_v4(raw_url: str) -> str:
    clean_url = str(raw_url or "").strip()

    if not clean_url:
        return clean_url

    try:
        parsed_url = urlsplit(clean_url)
    except Exception:
        return clean_url

    if parsed_url.scheme or parsed_url.netloc:
        return clean_url

    path = parsed_url.path or "/users/new"

    if path != "/users/new":
        return clean_url

    query_params = dict(parse_qsl(parsed_url.query, keep_blank_values=True))
    query_params["appverbo_after_save"] = "1"

    query_string = urlencode(query_params)
    fragment = f"#{parsed_url.fragment}" if parsed_url.fragment else ""

    return f"{path}?{query_string}{fragment}" if query_string else f"{path}{fragment}"


def _build_users_new_url_with_return_context_v4(
    submitted_form: Any,
    **params: Any,
) -> str:
    raw_return_url = ""

    if hasattr(submitted_form, "get"):
        raw_return_url = str(submitted_form.get("return_url") or "").strip()

    safe_return_url = _sanitize_users_new_return_url_post_save_v4(
        raw_return_url,
        params,
    )

    if safe_return_url:
        return safe_return_url

    return _append_after_save_marker_to_users_new_url_v4(
        build_users_new_url(**params)
    )
# APPVERBO_RETURN_URL_POST_SAVE_V4_END
'''


####################################################################################
# (4) BLOCO JS PARA ENVIAR return_url ANTES DO POST
####################################################################################

JS_CAPTURE_BLOCK = r'''
// APPVERBO_RETURN_URL_POST_SAVE_CAPTURE_V4_START
//###################################################################################
// (RETURN_URL_POST_SAVE_CAPTURE_V4) ENVIAR CONTEXTO ATUAL ANTES DO POST
//###################################################################################

(function setupReturnUrlPostSaveCaptureV4() {
  "use strict";

  //###################################################################################
  // (1) HELPERS
  //###################################################################################

  function safeReturnUrlTextV4(value) {
    return String(value === null || value === undefined ? "" : value);
  }

  function normalizeReturnUrlKeyV4(value) {
    if (typeof normalizeMenuKey === "function") {
      return normalizeMenuKey(value);
    }

    return safeReturnUrlTextV4(value).trim().toLowerCase();
  }

  function normalizeReturnUrlLookupV4(value) {
    if (typeof normalizeLookupText === "function") {
      return normalizeLookupText(value);
    }

    return safeReturnUrlTextV4(value)
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function ensureHiddenReturnUrlInputV4(form, name) {
    let input = form.querySelector("input[name='" + name + "']");

    if (!input) {
      input = document.createElement("input");
      input.type = "hidden";
      input.name = name;
      form.appendChild(input);
    }

    return input;
  }

  function getCurrentUrlReturnUrlV4() {
    try {
      return new URL(window.location.href);
    } catch (error) {
      return new URL("/users/new", window.location.origin);
    }
  }

  function getFormActionReturnUrlV4(form) {
    return safeReturnUrlTextV4(form && (form.getAttribute("action") || form.action));
  }

  function getFormMethodReturnUrlV4(form) {
    return safeReturnUrlTextV4(form && (form.getAttribute("method") || form.method || "post"))
      .trim()
      .toLowerCase();
  }

  function getFormValueReturnUrlV4(form, names) {
    if (!form) {
      return "";
    }

    for (const name of names) {
      const control = form.querySelector("[name='" + name + "']");

      if (!control) {
        continue;
      }

      const value = safeReturnUrlTextV4(control.value).trim();

      if (value) {
        return value;
      }
    }

    return "";
  }

  //###################################################################################
  // (2) DETECTAR ABA DO MEU PERFIL
  //###################################################################################

  function getProfileSectionFromInputReturnUrlV4() {
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
      const value = normalizeReturnUrlKeyV4(input ? input.value : "");

      if (value) {
        return value;
      }
    }

    return "";
  }

  function getProfileSectionFromActiveTabReturnUrlV4() {
    const sections = Array.isArray(window.profilePersonalSections || profilePersonalSections)
      ? (window.profilePersonalSections || profilePersonalSections)
      : [];

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

      const dataSection = normalizeReturnUrlKeyV4(
        activeElement.dataset.profileSection ||
        activeElement.dataset.profileSectionKey ||
        activeElement.dataset.profileSectionTab ||
        activeElement.dataset.sectionKey ||
        ""
      );

      if (dataSection) {
        return dataSection;
      }

      const activeLabel = normalizeReturnUrlLookupV4(activeElement.textContent);

      if (!activeLabel) {
        continue;
      }

      for (const section of sections) {
        const sectionLabel = normalizeReturnUrlLookupV4(section && section.label);

        if (sectionLabel && sectionLabel === activeLabel) {
          return normalizeReturnUrlKeyV4(section && section.key);
        }
      }
    }

    return "";
  }

  function getProfileSectionFromVisiblePaneReturnUrlV4() {
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

      const sectionKey = normalizeReturnUrlKeyV4(pane.dataset.profileSectionPane);

      if (sectionKey) {
        return sectionKey;
      }
    }

    return "";
  }

  function getCurrentProfileSectionReturnUrlV4() {
    return (
      getProfileSectionFromInputReturnUrlV4() ||
      getProfileSectionFromActiveTabReturnUrlV4() ||
      getProfileSectionFromVisiblePaneReturnUrlV4()
    );
  }

  //###################################################################################
  // (3) DETECTAR PROCESSO DINAMICO
  //###################################################################################

  function getCurrentMenuReturnUrlV4(form) {
    const url = getCurrentUrlReturnUrlV4();

    const formMenu = normalizeReturnUrlKeyV4(
      getFormValueReturnUrlV4(form, [
        "menu",
        "menu_key",
        "process_menu_key",
        "dynamic_menu_key"
      ])
    );

    if (formMenu) {
      return formMenu;
    }

    const urlMenu = normalizeReturnUrlKeyV4(url.searchParams.get("menu"));

    if (urlMenu) {
      return urlMenu;
    }

    if (typeof initialMenu !== "undefined") {
      return normalizeReturnUrlKeyV4(initialMenu);
    }

    return "";
  }

  function getCurrentDynamicSectionReturnUrlV4(menuKey) {
    const formSection = normalizeReturnUrlKeyV4(
      getFormValueReturnUrlV4(document, [
        "dynamic_process_section",
        "section_key",
        "process_section",
        "active_section"
      ])
    );

    if (formSection) {
      return formSection;
    }

    if (
      typeof selectedDynamicSectionByMenu === "object" &&
      selectedDynamicSectionByMenu !== null &&
      menuKey &&
      selectedDynamicSectionByMenu[menuKey]
    ) {
      return normalizeReturnUrlKeyV4(selectedDynamicSectionByMenu[menuKey]);
    }

    const activeElement = document.querySelector(
      "#dynamic-process-card .active, " +
      "#dynamic-process-card [aria-selected='true'], " +
      "[data-dynamic-process-section-key].active, " +
      "[data-dynamic-process-section-key][aria-selected='true']"
    );

    if (activeElement) {
      return normalizeReturnUrlKeyV4(
        activeElement.dataset.dynamicProcessSectionKey ||
        activeElement.dataset.sectionKey ||
        ""
      );
    }

    return "";
  }

  //###################################################################################
  // (4) CONSTRUIR return_url
  //###################################################################################

  function buildReturnUrlPostSaveV4(form) {
    const url = getCurrentUrlReturnUrlV4();
    const action = getFormActionReturnUrlV4(form);
    const actionLookup = normalizeReturnUrlLookupV4(action);

    url.pathname = "/users/new";

    if (actionLookup.includes("/users/profile/personal")) {
      const profileSection = getCurrentProfileSectionReturnUrlV4();

      url.searchParams.set("menu", "meu_perfil");
      url.searchParams.set("target", "#perfil-pessoal-card");
      url.searchParams.set("profile_tab", "pessoal");

      if (profileSection) {
        url.searchParams.set("profile_section", profileSection);
      }
    } else {
      const menuKey = getCurrentMenuReturnUrlV4(form);

      if (menuKey) {
        url.searchParams.set("menu", menuKey);
      }

      const target = getFormValueReturnUrlV4(form, ["target", "return_target"]);

      if (target) {
        url.searchParams.set("target", target);
      }

      const dynamicSection = getCurrentDynamicSectionReturnUrlV4(menuKey);

      if (dynamicSection) {
        url.searchParams.set("dynamic_process_section", dynamicSection);
      }
    }

    url.searchParams.set("appverbo_after_save", "1");

    return url.pathname + url.search + url.hash;
  }

  //###################################################################################
  // (5) SINCRONIZAR NO FORMULARIO
  //###################################################################################

  function syncReturnUrlPostSaveV4(form) {
    if (!form) {
      return;
    }

    const method = getFormMethodReturnUrlV4(form);

    if (method && method !== "post") {
      return;
    }

    const returnUrl = buildReturnUrlPostSaveV4(form);

    ensureHiddenReturnUrlInputV4(form, "return_url").value = returnUrl;
    ensureHiddenReturnUrlInputV4(form, "appverbo_after_save").value = "1";

    try {
      window.sessionStorage.setItem(
        "appverbo:return-url-post-save-v4",
        JSON.stringify({
          url: returnUrl,
          createdAt: Date.now()
        })
      );
    } catch (error) {
      // Ignora sessionStorage indisponivel.
    }
  }

  document.addEventListener("submit", function (event) {
    syncReturnUrlPostSaveV4(event.target);
  }, true);

  document.addEventListener("click", function (event) {
    const submitControl = event.target && event.target.closest
      ? event.target.closest("button[type='submit'], input[type='submit'], button:not([type])")
      : null;

    if (!submitControl || !submitControl.form) {
      return;
    }

    syncReturnUrlPostSaveV4(submitControl.form);
  }, true);

  document.addEventListener("formdata", function (event) {
    if (!event || !event.formData || !event.target) {
      return;
    }

    syncReturnUrlPostSaveV4(event.target);

    const returnUrlInput = event.target.querySelector("input[name='return_url']");
    const afterSaveInput = event.target.querySelector("input[name='appverbo_after_save']");

    if (returnUrlInput) {
      event.formData.set("return_url", returnUrlInput.value);
    }

    if (afterSaveInput) {
      event.formData.set("appverbo_after_save", afterSaveInput.value);
    }
  }, true);

  if (
    window.HTMLFormElement &&
    window.HTMLFormElement.prototype &&
    !window.HTMLFormElement.prototype.__appverboReturnUrlPostSavePatchedV4
  ) {
    const nativeSubmit = window.HTMLFormElement.prototype.submit;

    window.HTMLFormElement.prototype.submit = function patchedSubmitReturnUrlPostSaveV4() {
      syncReturnUrlPostSaveV4(this);
      return nativeSubmit.call(this);
    };

    window.HTMLFormElement.prototype.__appverboReturnUrlPostSavePatchedV4 = true;
  }
})();

// APPVERBO_RETURN_URL_POST_SAVE_CAPTURE_V4_END
'''


####################################################################################
# (5) PATCH profile_handlers.py
####################################################################################

def patch_profile_handlers_v1() -> None:
    content = read_text_v1(PROFILE_HANDLERS_PATH)

    if "from urllib.parse import parse_qsl, urlencode, urlsplit" not in content:
        content = content.replace(
            "from uuid import uuid4\n",
            "from uuid import uuid4\nfrom urllib.parse import parse_qsl, urlencode, urlsplit\n",
            1,
        )

    if PY_START_MARKER not in content:
        insertion_marker = "\n@router.post(\"/users/profile/personal\")"

        if insertion_marker not in content:
            raise RuntimeError("Nao encontrei o ponto de insercao antes de /users/profile/personal.")

        content = content.replace(
            insertion_marker,
            "\n\n" + PY_HELPER_BLOCK.strip() + "\n" + insertion_marker,
            1,
        )

    route_pattern = re.compile(
        r"(@router\.[\s\S]*?async def [\s\S]*?)(?=\n@router\.|\Z)",
        flags=re.DOTALL,
    )

    replacements = 0
    rebuilt_blocks: list[str] = []
    last_end = 0

    for match in route_pattern.finditer(content):
        rebuilt_blocks.append(content[last_end:match.start()])
        block = match.group(1)

        if "submitted_form = await request.form()" in block:
            before_block = block
            block = block.replace(
                "url=build_users_new_url(",
                "url=_build_users_new_url_with_return_context_v4(submitted_form,",
            )
            replacements += before_block.count("url=build_users_new_url(")

        rebuilt_blocks.append(block)
        last_end = match.end()

    rebuilt_blocks.append(content[last_end:])
    content = "".join(rebuilt_blocks)

    if replacements <= 0:
        raise RuntimeError("Nenhum build_users_new_url foi ajustado nos handlers com submitted_form.")

    required_markers = [
        PY_START_MARKER,
        "def _build_users_new_url_with_return_context_v4",
        "return_url",
        "appverbo_after_save",
        "_sanitize_users_new_return_url_post_save_v4",
    ]

    missing = [
        marker for marker in required_markers
        if marker not in content
    ]

    if missing:
        raise RuntimeError("Marcadores ausentes em profile_handlers.py: " + ", ".join(missing))

    write_text_v1(PROFILE_HANDLERS_PATH, content)
    print(f"OK: build_users_new_url ajustado em {replacements} chamadas dentro de handlers com submitted_form.")


####################################################################################
# (6) PATCH new_user.js
####################################################################################

def patch_new_user_js_v1() -> None:
    content = read_text_v1(NEW_USER_JS_PATH)

    content = replace_marker_block_v1(
        content,
        JS_START_MARKER,
        JS_END_MARKER,
        JS_CAPTURE_BLOCK,
    )

    required_markers = [
        JS_START_MARKER,
        "buildReturnUrlPostSaveV4",
        "syncReturnUrlPostSaveV4",
        "return_url",
        "appverbo_after_save",
        "document.addEventListener(\"formdata\"",
    ]

    missing = [
        marker for marker in required_markers
        if marker not in content
    ]

    if missing:
        raise RuntimeError("Marcadores ausentes em new_user.js: " + ", ".join(missing))

    write_text_v1(NEW_USER_JS_PATH, content)


####################################################################################
# (7) PATCH CACHE BUSTER
####################################################################################

def patch_template_v1() -> None:
    content = read_text_v1(TEMPLATE_PATH)

    if "new_user.js" not in content:
        raise RuntimeError("new_user.js nao encontrado no template.")

    content = re.sub(
        r'new_user\.js\?v=[^"]+',
        "new_user.js?v=20260503-return-url-post-save-v4",
        content,
    )

    if "new_user.js?v=20260503-return-url-post-save-v4" not in content:
        raise RuntimeError("Cache buster do new_user.js nao foi atualizado.")

    write_text_v1(TEMPLATE_PATH, content)


####################################################################################
# (8) VALIDACAO
####################################################################################

def validate_v1() -> None:
    profile_content = read_text_v1(PROFILE_HANDLERS_PATH)
    js_content = read_text_v1(NEW_USER_JS_PATH)
    template_content = read_text_v1(TEMPLATE_PATH)

    required_profile = [
        "from urllib.parse import parse_qsl, urlencode, urlsplit",
        "def _build_users_new_url_with_return_context_v4",
        "_build_users_new_url_with_return_context_v4(submitted_form,",
        "appverbo_after_save",
    ]

    missing_profile = [
        marker for marker in required_profile
        if marker not in profile_content
    ]

    if missing_profile:
        raise RuntimeError("Marcadores ausentes em profile_handlers.py: " + ", ".join(missing_profile))

    required_js = [
        "APPVERBO_RETURN_URL_POST_SAVE_CAPTURE_V4_START",
        "buildReturnUrlPostSaveV4",
        "syncReturnUrlPostSaveV4",
        "return_url",
        "appverbo_after_save",
        "document.addEventListener(\"formdata\"",
    ]

    missing_js = [
        marker for marker in required_js
        if marker not in js_content
    ]

    if missing_js:
        raise RuntimeError("Marcadores ausentes em new_user.js: " + ", ".join(missing_js))

    if "new_user.js?v=20260503-return-url-post-save-v4" not in template_content:
        raise RuntimeError("Cache buster esperado nao encontrado no template.")

    print("OK: backend respeita return_url seguro nos redirects pos-save.")
    print("OK: frontend envia return_url antes de qualquer POST.")
    print("OK: cache buster atualizado.")


####################################################################################
# (9) EXECUCAO
####################################################################################

def main() -> None:
    require_file_v1(PROFILE_HANDLERS_PATH)
    require_file_v1(NEW_USER_JS_PATH)
    require_file_v1(TEMPLATE_PATH)

    profile_backup = backup_file_v1(PROFILE_HANDLERS_PATH, "return_url_post_save_v4")
    js_backup = backup_file_v1(NEW_USER_JS_PATH, "return_url_post_save_v4")
    template_backup = backup_file_v1(TEMPLATE_PATH, "return_url_post_save_v4")

    print(f"OK: backup criado: {profile_backup}")
    print(f"OK: backup criado: {js_backup}")
    print(f"OK: backup criado: {template_backup}")

    patch_profile_handlers_v1()
    patch_new_user_js_v1()
    patch_template_v1()
    validate_v1()

    print("OK: patch return_url pos-save concluido.")


if __name__ == "__main__":
    main()
