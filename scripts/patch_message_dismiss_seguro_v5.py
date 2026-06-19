from __future__ import annotations

import re
from pathlib import Path


####################################################################################
# (1) CONFIGURACAO
####################################################################################

PROJECT_ROOT = Path.cwd()

JS_PATH = PROJECT_ROOT / "static" / "js" / "new_user.js"
TEMPLATE_PATH = PROJECT_ROOT / "templates" / "new_user.html"
PROFILE_HANDLERS_PATH = PROJECT_ROOT / "appverbo" / "routes" / "profile" / "profile_handlers.py"

JS_VERSION = "new_user.js?v=20260509-message-dismiss-safe-v5"


####################################################################################
# (2) FUNCOES AUXILIARES
####################################################################################

def read_text_v5(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text_v5(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def remove_js_block_v5(content: str, start_marker: str, end_marker: str) -> str:
    pattern = re.compile(
        r"^[ \t]*//\s*" + re.escape(start_marker) + r".*?"
        + r"^[ \t]*//\s*" + re.escape(end_marker) + r"[^\r\n]*(?:\r?\n)?",
        flags=re.DOTALL | re.MULTILINE,
    )

    return pattern.sub("", content)


def remove_html_block_v5(content: str, start_marker: str, end_marker: str) -> str:
    pattern = re.compile(
        r"<!--\s*" + re.escape(start_marker) + r"\s*-->.*?"
        r"<!--\s*" + re.escape(end_marker) + r"\s*-->",
        flags=re.DOTALL,
    )

    return pattern.sub("", content)


####################################################################################
# (3) JS V5 SEGURO
####################################################################################

JS_BLOCK = r'''
// APPVERBO_MESSAGE_DISMISS_SAFE_V5_START
//###################################################################################
// (MESSAGE_DISMISS_SAFE_V5) REGRA GLOBAL SEGURA: MENSAGENS SOMEM EM 3 SEGUNDOS
//###################################################################################

(function () {
  "use strict";

  const VERSION = "APPVERBO_MESSAGE_DISMISS_SAFE_V5";
  const AUTO_DISMISS_MS = 3000;
  const REMOVE_ANIMATION_MS = 250;
  const DEBUG_ENDPOINT = "/debug/global-message-auto-dismiss";
  const startedAt = Date.now();

  const MESSAGE_PARAM_NAMES = [
    "success",
    "error",
    "entity_success",
    "entity_error",
    "profile_success",
    "profile_error",
    "settings_success",
    "settings_error",
    "invite_link"
  ];

  function normalizeText(value) {
    return String(value || "")
      .replace(/\+/g, " ")
      .replace(/\s+/g, " ")
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function safeText(value, maxSize) {
    const cleanValue = String(value || "");
    const limit = maxSize || 700;

    if (cleanValue.length > limit) {
      return cleanValue.slice(0, limit) + "...[TRUNCATED]";
    }

    return cleanValue;
  }

  function readMessageParams() {
    const messages = [];
    const params = new URLSearchParams(window.location.search || "");

    MESSAGE_PARAM_NAMES.forEach(function (paramName) {
      const value = params.get(paramName);

      if (value && String(value).trim() !== "") {
        messages.push({
          paramName: paramName,
          value: String(value).trim(),
          normalizedValue: normalizeText(value)
        });
      }
    });

    return messages;
  }

  const initialMessageParams = readMessageParams();

  function getActiveMessageParams() {
    const currentMessageParams = readMessageParams();
    const merged = [];

    initialMessageParams.concat(currentMessageParams).forEach(function (messageItem) {
      if (
        messageItem &&
        messageItem.normalizedValue &&
        !merged.some(function (existing) {
          return (
            existing.paramName === messageItem.paramName &&
            existing.normalizedValue === messageItem.normalizedValue
          );
        })
      ) {
        merged.push(messageItem);
      }
    });

    return merged;
  }

  function getElementSnapshot(element) {
    if (!element) {
      return null;
    }

    let computedStyle = {};

    try {
      const style = window.getComputedStyle(element);
      computedStyle = {
        display: style.display,
        visibility: style.visibility,
        opacity: style.opacity,
        backgroundColor: style.backgroundColor,
        color: style.color,
        borderColor: style.borderColor,
        height: style.height,
        width: style.width
      };
    } catch (error) {
      computedStyle = {
        error: String(error && error.message ? error.message : error)
      };
    }

    return {
      tagName: String(element.tagName || ""),
      id: String(element.id || ""),
      className: String(element.className || ""),
      role: String(element.getAttribute("role") || ""),
      text: safeText(element.textContent || "", 700),
      outerHTML: safeText(element.outerHTML || "", 900),
      computedStyle: computedStyle
    };
  }

  function debugSafeDismiss(stage, data) {
    const payload = {
      version: VERSION,
      stage: String(stage || ""),
      elapsedMs: Date.now() - startedAt,
      readyState: document.readyState,
      location: {
        href: window.location.href,
        pathname: window.location.pathname,
        search: window.location.search,
        hash: window.location.hash
      },
      initialMessageParams: initialMessageParams,
      currentMessageParams: readMessageParams(),
      activeMessageParams: getActiveMessageParams(),
      data: data || {}
    };

    window.__APPVERBO_MESSAGE_DISMISS_SAFE_V5_LOGS =
      window.__APPVERBO_MESSAGE_DISMISS_SAFE_V5_LOGS || [];
    window.__APPVERBO_MESSAGE_DISMISS_SAFE_V5_LOGS.push(payload);

    try {
      console.log("APPVERBO_MESSAGE_DISMISS_SAFE_V5", payload);
    } catch (error) {
      return;
    }

    try {
      fetch(DEBUG_ENDPOINT, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          logger: VERSION,
          payload: payload
        }),
        keepalive: true
      }).catch(function () {});
    } catch (error) {
      return;
    }
  }

  function isVisibleElement(element) {
    if (!element || !element.isConnected) {
      return false;
    }

    try {
      const style = window.getComputedStyle(element);

      if (
        style.display === "none" ||
        style.visibility === "hidden" ||
        Number(style.opacity || "1") === 0
      ) {
        return false;
      }

      const rect = element.getBoundingClientRect();

      if (rect.width <= 0 || rect.height <= 0) {
        return false;
      }

      return true;
    } catch (error) {
      return false;
    }
  }

  function hasMessageStyleSignal(element) {
    if (!element) {
      return false;
    }

    const role = String(element.getAttribute("role") || "").toLowerCase();

    if (role === "alert") {
      return true;
    }

    const classText = String(element.className || "").toLowerCase();

    return (
      classText.includes("alert") ||
      classText.includes("message") ||
      classText.includes("toast") ||
      classText.includes("success") ||
      classText.includes("error") ||
      classText.includes("notification") ||
      classText.includes("flash")
    );
  }

  function findBestMessageContainer(element, normalizedMessageText) {
    if (!element) {
      return null;
    }

    let current = element;
    let best = element;
    let depth = 0;

    while (current && current !== document.body && depth < 6) {
      const text = normalizeText(current.textContent || "");

      if (!text || !text.includes(normalizedMessageText)) {
        break;
      }

      if (hasMessageStyleSignal(current)) {
        return current;
      }

      if (text.length <= 260) {
        best = current;
      }

      current = current.parentElement;
      depth += 1;
    }

    return best;
  }

  function collectMessageElements(reason) {
    const activeMessageParams = getActiveMessageParams();
    const found = [];

    if (!activeMessageParams.length) {
      debugSafeDismiss("collect_skipped_no_message_params", {
        reason: reason || ""
      });
      return [];
    }

    if (!document.body) {
      debugSafeDismiss("collect_skipped_no_body", {
        reason: reason || ""
      });
      return [];
    }

    const allElements = Array.from(document.body.querySelectorAll("*"));

    activeMessageParams.forEach(function (messageItem) {
      const normalizedMessageText = messageItem.normalizedValue;

      if (!normalizedMessageText) {
        return;
      }

      allElements.forEach(function (element) {
        const tagName = String(element.tagName || "").toLowerCase();

        if (["script", "style", "svg", "path", "meta", "link", "option"].includes(tagName)) {
          return;
        }

        if (!isVisibleElement(element)) {
          return;
        }

        const normalizedElementText = normalizeText(element.textContent || "");

        if (!normalizedElementText.includes(normalizedMessageText)) {
          return;
        }

        if (normalizedElementText.length > 350) {
          return;
        }

        const container = findBestMessageContainer(element, normalizedMessageText);

        if (
          container &&
          isVisibleElement(container) &&
          !found.includes(container) &&
          normalizeText(container.textContent || "").includes(normalizedMessageText)
        ) {
          found.push(container);
        }
      });
    });

    const finalElements = found.filter(function (element) {
      return element && element.isConnected && element.dataset.appverboMessageDismissSafeV5 !== "1";
    });

    debugSafeDismiss("collect", {
      reason: reason || "",
      finalElementsCount: finalElements.length,
      finalElements: finalElements.slice(0, 10).map(getElementSnapshot)
    });

    return finalElements;
  }

  function cleanMessageParamsFromUrl(reason) {
    try {
      const url = new URL(window.location.href);
      const removed = [];

      MESSAGE_PARAM_NAMES.forEach(function (paramName) {
        if (url.searchParams.has(paramName)) {
          removed.push({
            paramName: paramName,
            value: url.searchParams.get(paramName)
          });
          url.searchParams.delete(paramName);
        }
      });

      if (removed.length) {
        const cleanUrl = `${url.pathname}${url.search}${url.hash}`;
        window.history.replaceState(window.history.state, document.title, cleanUrl);

        debugSafeDismiss("url_cleaned", {
          reason: reason || "",
          removed: removed,
          cleanUrl: cleanUrl
        });
      } else {
        debugSafeDismiss("url_no_message_params", {
          reason: reason || ""
        });
      }
    } catch (error) {
      debugSafeDismiss("url_clean_error", {
        reason: reason || "",
        error: String(error && error.message ? error.message : error)
      });
    }
  }

  function removeMessageElement(element, reason) {
    if (!element || !element.isConnected) {
      debugSafeDismiss("remove_skip_not_connected", {
        reason: reason || "",
        element: getElementSnapshot(element)
      });
      return;
    }

    element.dataset.appverboMessageDismissSafeV5 = "1";

    debugSafeDismiss("remove_start", {
      reason: reason || "",
      element: getElementSnapshot(element)
    });

    element.style.transition = "opacity 250ms ease, max-height 250ms ease, margin 250ms ease, padding 250ms ease, border-width 250ms ease";
    element.style.overflow = "hidden";
    element.style.opacity = "0";
    element.style.maxHeight = "0";
    element.style.marginTop = "0";
    element.style.marginBottom = "0";
    element.style.paddingTop = "0";
    element.style.paddingBottom = "0";
    element.style.borderTopWidth = "0";
    element.style.borderBottomWidth = "0";

    window.setTimeout(function () {
      const wasConnected = Boolean(element && element.isConnected);

      if (element && element.isConnected) {
        element.remove();
      }

      debugSafeDismiss("remove_done", {
        reason: reason || "",
        wasConnected: wasConnected,
        isConnectedAfter: Boolean(element && element.isConnected)
      });
    }, REMOVE_ANIMATION_MS);
  }

  function runSafeDismiss(reason) {
    const activeMessageParams = getActiveMessageParams();

    debugSafeDismiss("run_start", {
      reason: reason || "",
      activeMessageParamsCount: activeMessageParams.length
    });

    if (!activeMessageParams.length) {
      return;
    }

    const elements = collectMessageElements(reason || "run");

    if (!elements.length) {
      debugSafeDismiss("run_no_elements", {
        reason: reason || ""
      });
      cleanMessageParamsFromUrl(reason || "no_elements");
      return;
    }

    elements.forEach(function (element) {
      removeMessageElement(element, reason || "run");
    });

    cleanMessageParamsFromUrl(reason || "removed");
  }

  function scheduleSafeDismiss(reason, delayMs) {
    debugSafeDismiss("schedule", {
      reason: reason || "",
      delayMs: delayMs
    });

    window.setTimeout(function () {
      runSafeDismiss(reason || "scheduled");
    }, delayMs);
  }

  function initSafeDismiss() {
    debugSafeDismiss("init", {
      bodyExists: Boolean(document.body),
      initialMessageParams: initialMessageParams
    });

    if (!getActiveMessageParams().length) {
      return;
    }

    scheduleSafeDismiss("scheduled_3000ms", AUTO_DISMISS_MS);

    window.setTimeout(function () {
      collectMessageElements("diagnostic_500ms");
    }, 500);

    window.setTimeout(function () {
      collectMessageElements("diagnostic_1500ms");
    }, 1500);

    window.setTimeout(function () {
      runSafeDismiss("safety_3500ms");
    }, 3500);

    window.appverboMessageDismissSafeV5 = {
      logs: window.__APPVERBO_MESSAGE_DISMISS_SAFE_V5_LOGS || [],
      collect: function () {
        return collectMessageElements("manual_collect");
      },
      runNow: function () {
        return runSafeDismiss("manual_run");
      }
    };
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initSafeDismiss);
  } else {
    initSafeDismiss();
  }
})();
// APPVERBO_MESSAGE_DISMISS_SAFE_V5_END
'''


####################################################################################
# (4) PATCH JS
####################################################################################

def patch_js_v5() -> None:
    content = read_text_v5(JS_PATH)

    removable_blocks = [
        ("APPVERBO_GLOBAL_MESSAGE_AUTO_DISMISS_V1_START", "APPVERBO_GLOBAL_MESSAGE_AUTO_DISMISS_V1_END"),
        ("APPVERBO_GLOBAL_MESSAGE_AUTO_DISMISS_DEBUG_V2_START", "APPVERBO_GLOBAL_MESSAGE_AUTO_DISMISS_DEBUG_V2_END"),
        ("APPVERBO_FORCE_MESSAGE_DISMISS_V4_START", "APPVERBO_FORCE_MESSAGE_DISMISS_V4_END"),
        ("APPVERBO_MESSAGE_DISMISS_SAFE_V5_START", "APPVERBO_MESSAGE_DISMISS_SAFE_V5_END"),
    ]

    for start_marker, end_marker in removable_blocks:
        content = remove_js_block_v5(content, start_marker, end_marker)

    content = content.rstrip() + "\n\n" + JS_BLOCK.strip() + "\n"

    required_markers = [
        "APPVERBO_MESSAGE_DISMISS_SAFE_V5_START",
        "AUTO_DISMISS_MS = 3000",
        "collect_skipped_no_message_params",
        "activeMessageParams",
        "remove_start",
        "remove_done",
        "url_cleaned",
        "appverboMessageDismissSafeV5",
    ]

    missing = [
        marker
        for marker in required_markers
        if marker not in content
    ]

    if missing:
        raise RuntimeError("Marcadores ausentes no JS: " + ", ".join(missing))

    write_text_v5(JS_PATH, content)


####################################################################################
# (5) PATCH TEMPLATE
####################################################################################

def patch_template_v5() -> None:
    content = read_text_v5(TEMPLATE_PATH)

    content = remove_html_block_v5(
        content,
        "APPVERBO_TEMPLATE_MESSAGE_AUTODISMISS_V3_START",
        "APPVERBO_TEMPLATE_MESSAGE_AUTODISMISS_V3_END",
    )

    if "new_user.js?v=" not in content:
        raise RuntimeError("Referencia new_user.js?v= nao encontrada no template.")

    content = re.sub(
        "new_user\\.js\\?v=[^\"']+",
        JS_VERSION,
        content,
        count=1,
    )

    if JS_VERSION not in content:
        raise RuntimeError("Cache buster novo nao encontrado no template.")

    write_text_v5(TEMPLATE_PATH, content.rstrip() + "\n")


####################################################################################
# (6) EXECUCAO
####################################################################################

def main() -> None:
    patch_js_v5()
    patch_template_v5()

    print("OK: V4 removida.")
    print("OK: V5 segura inserida.")
    print("OK: a V5 so remove mensagem quando existir parametro de mensagem na URL.")
    print("OK: cache buster atualizado:", JS_VERSION)


if __name__ == "__main__":
    main()
