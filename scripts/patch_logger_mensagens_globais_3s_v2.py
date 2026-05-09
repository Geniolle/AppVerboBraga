from __future__ import annotations

import re
from pathlib import Path


####################################################################################
# (1) CONFIGURACAO
####################################################################################

PROJECT_ROOT = Path.cwd()

PROFILE_HANDLERS_PATH = PROJECT_ROOT / "appverbo" / "routes" / "profile" / "profile_handlers.py"
JS_PATH = PROJECT_ROOT / "static" / "js" / "new_user.js"
TEMPLATE_PATH = PROJECT_ROOT / "templates" / "new_user.html"

JS_VERSION = "new_user.js?v=20260509-global-message-auto-dismiss-debug-v2"


####################################################################################
# (2) FUNCOES AUXILIARES
####################################################################################

def read_text_v2(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text_v2(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def remove_marked_block_v2(content: str, start_marker: str, end_marker: str) -> str:
    pattern = re.compile(
        r"^[ \t]*(?://|#)\s*" + re.escape(start_marker) + r".*?"
        + r"^[ \t]*(?://|#)\s*" + re.escape(end_marker) + r"[^\r\n]*(?:\r?\n)?",
        flags=re.DOTALL | re.MULTILINE,
    )

    return pattern.sub("", content)


####################################################################################
# (3) ENDPOINT BACKEND PARA RECEBER LOGS DO FRONTEND
####################################################################################

BACKEND_ENDPOINT_BLOCK = r'''
# APPVERBO_GLOBAL_MESSAGE_AUTO_DISMISS_DEBUG_ENDPOINT_V2_START
@router.post("/debug/global-message-auto-dismiss")
async def appverbo_global_message_auto_dismiss_debug_v2(request: Request) -> JSONResponse:
    import json
    import os
    from datetime import datetime, timezone
    from pathlib import Path

    try:
        try:
            payload = await request.json()
        except Exception as exc:
            payload = {
                "json_error": repr(exc),
            }

        request_url = ""
        request_path = ""
        request_client = ""

        try:
            request_url = str(request.url)
            request_path = str(request.url.path)
            request_client = str(getattr(request.client, "host", "") or "")
        except Exception:
            pass

        log_entry = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "logger": "APPVERBO_GLOBAL_MESSAGE_AUTO_DISMISS_DEBUG_V2",
            "request": {
                "method": str(request.method),
                "path": request_path,
                "url": request_url,
                "client": request_client,
            },
            "payload": payload,
        }

        log_dir = Path(
            os.environ.get(
                "APPVERBO_GLOBAL_MESSAGE_LOG_DIR",
                "appverbo_runtime_logs",
            )
        )
        log_dir.mkdir(parents=True, exist_ok=True)

        log_line = json.dumps(
            log_entry,
            ensure_ascii=False,
            default=str,
            sort_keys=True,
        )

        with (log_dir / "global_message_auto_dismiss_debug.log").open("a", encoding="utf-8") as log_file:
            log_file.write(log_line + "\n")

        print("APPVERBO_GLOBAL_MESSAGE_AUTO_DISMISS_DEBUG " + log_line, flush=True)

        return JSONResponse({"ok": True})

    except Exception as exc:
        print(
            "APPVERBO_GLOBAL_MESSAGE_AUTO_DISMISS_DEBUG_ERROR " + repr(exc),
            flush=True,
        )
        return JSONResponse(
            {
                "ok": False,
                "error": repr(exc),
            },
            status_code=500,
        )
# APPVERBO_GLOBAL_MESSAGE_AUTO_DISMISS_DEBUG_ENDPOINT_V2_END
'''


####################################################################################
# (4) BLOCO FRONTEND COM LOGGER E AUTO-DISMISS EM 3 SEGUNDOS
####################################################################################

JS_BLOCK = r'''
// APPVERBO_GLOBAL_MESSAGE_AUTO_DISMISS_DEBUG_V2_START
//###################################################################################
// (GLOBAL_MESSAGE_AUTO_DISMISS_DEBUG_V2) LOGGER E REMOCAO GLOBAL DE MENSAGENS EM 3S
//###################################################################################

(function () {
  "use strict";

  const startedAt = Date.now();
  const GLOBAL_MESSAGE_AUTO_DISMISS_MS = 3000;
  const DEBUG_ENDPOINT = "/debug/global-message-auto-dismiss";

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

  const MESSAGE_SELECTOR = [
    '[role="alert"]',
    ".alert",
    ".alert-success",
    ".alert-danger",
    ".flash",
    ".toast",
    ".notification",
    ".message",
    ".success-message",
    ".error-message",
    ".appverbo-message",
    ".appverbo-alert",
    ".form-message",
    ".status-message",
    "[data-message]",
    "[data-alert]",
    "[class*='alert']",
    "[class*='message']",
    "[class*='success']",
    "[class*='error']"
  ].join(",");

  window.__APPVERBO_GLOBAL_MESSAGE_AUTO_DISMISS_DEBUG_V2_LOGS =
    window.__APPVERBO_GLOBAL_MESSAGE_AUTO_DISMISS_DEBUG_V2_LOGS || [];

  function safeText(value, maxSize) {
    const cleanValue = String(value || "");
    const limit = maxSize || 500;

    if (cleanValue.length > limit) {
      return cleanValue.slice(0, limit) + "...[TRUNCATED]";
    }

    return cleanValue;
  }

  function normalizeMessageText(value) {
    return String(value || "")
      .replace(/\s+/g, " ")
      .trim()
      .toLowerCase();
  }

  function getElementSnapshot(element) {
    if (!element) {
      return null;
    }

    let computedStyle = null;

    try {
      const style = window.getComputedStyle(element);
      computedStyle = {
        display: style.display,
        visibility: style.visibility,
        opacity: style.opacity,
        backgroundColor: style.backgroundColor,
        color: style.color
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
      dataAutoDismissed: String(element.dataset ? element.dataset.appverboAutoDismissedV2 || "" : ""),
      text: safeText(element.textContent || "", 700),
      outerHTML: safeText(element.outerHTML || "", 900),
      computedStyle: computedStyle
    };
  }

  function debugGlobalMessageAutoDismiss(stage, data) {
    const entry = {
      stage: String(stage || ""),
      elapsedMs: Date.now() - startedAt,
      readyState: document.readyState,
      location: {
        href: window.location.href,
        pathname: window.location.pathname,
        search: window.location.search,
        hash: window.location.hash
      },
      data: data || {}
    };

    window.__APPVERBO_GLOBAL_MESSAGE_AUTO_DISMISS_DEBUG_V2_LOGS.push(entry);

    try {
      console.log("APPVERBO_GLOBAL_MESSAGE_AUTO_DISMISS_DEBUG", entry);
    } catch (error) {
      return;
    }

    try {
      fetch(DEBUG_ENDPOINT, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(entry),
        keepalive: true
      }).catch(function () {});
    } catch (error) {
      return;
    }
  }

  function getUrlMessageValues() {
    const values = [];
    const params = new URLSearchParams(window.location.search || "");

    MESSAGE_PARAM_NAMES.forEach(function (paramName) {
      const paramValue = params.get(paramName);

      if (paramValue && String(paramValue).trim() !== "") {
        values.push({
          paramName: paramName,
          paramValue: String(paramValue).trim()
        });
      }
    });

    return values;
  }

  function hasMessageSignal(element) {
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
      classText.includes("notification")
    );
  }

  function findBestDismissTarget(element) {
    if (!element) {
      return null;
    }

    if (hasMessageSignal(element)) {
      return element;
    }

    const closestMessage = element.closest(MESSAGE_SELECTOR);

    if (closestMessage) {
      return closestMessage;
    }

    let current = element.parentElement;

    while (current && current !== document.body) {
      if (hasMessageSignal(current)) {
        return current;
      }

      current = current.parentElement;
    }

    return element;
  }

  function findSmallestElementContainingText(messageText) {
    const normalizedNeedle = normalizeMessageText(messageText);

    if (!normalizedNeedle || !document.body) {
      return null;
    }

    const candidates = Array.from(document.body.querySelectorAll("*")).filter(function (element) {
      const tagName = String(element.tagName || "").toLowerCase();

      if (["script", "style", "svg", "path", "meta", "link", "option"].includes(tagName)) {
        return false;
      }

      const normalizedText = normalizeMessageText(element.textContent || "");

      if (!normalizedText || !normalizedText.includes(normalizedNeedle)) {
        return false;
      }

      return true;
    });

    if (!candidates.length) {
      return null;
    }

    candidates.sort(function (left, right) {
      const leftTextLength = normalizeMessageText(left.textContent || "").length;
      const rightTextLength = normalizeMessageText(right.textContent || "").length;

      return leftTextLength - rightTextLength;
    });

    return candidates[0];
  }

  function collectGlobalMessageElements(reason) {
    const elements = new Set();
    const selectorMatches = [];

    if (!document.body) {
      debugGlobalMessageAutoDismiss("collect_no_body", {
        reason: reason || ""
      });
      return [];
    }

    document.querySelectorAll(MESSAGE_SELECTOR).forEach(function (element) {
      const text = normalizeMessageText(element.textContent || "");

      if (!text) {
        return;
      }

      elements.add(findBestDismissTarget(element) || element);
      selectorMatches.push(getElementSnapshot(element));
    });

    const urlMessages = getUrlMessageValues();
    const textMatches = [];

    urlMessages.forEach(function (messageItem) {
      const foundElement = findSmallestElementContainingText(messageItem.paramValue);
      const targetElement = findBestDismissTarget(foundElement) || foundElement;

      if (targetElement) {
        elements.add(targetElement);
      }

      textMatches.push({
        paramName: messageItem.paramName,
        paramValue: messageItem.paramValue,
        foundElement: getElementSnapshot(foundElement),
        targetElement: getElementSnapshot(targetElement)
      });
    });

    const finalElements = Array.from(elements).filter(function (element) {
      return element && element.isConnected && element.dataset.appverboAutoDismissedV2 !== "1";
    });

    debugGlobalMessageAutoDismiss("collect_messages", {
      reason: reason || "",
      messageSelector: MESSAGE_SELECTOR,
      urlMessages: urlMessages,
      selectorMatchesCount: selectorMatches.length,
      textMatchesCount: textMatches.length,
      finalElementsCount: finalElements.length,
      selectorMatches: selectorMatches.slice(0, 10),
      textMatches: textMatches.slice(0, 10),
      finalElements: finalElements.slice(0, 10).map(getElementSnapshot)
    });

    return finalElements;
  }

  function cleanMessageParamsFromUrl(reason) {
    try {
      const url = new URL(window.location.href);
      let changed = false;
      const removedParams = [];

      MESSAGE_PARAM_NAMES.forEach(function (paramName) {
        if (url.searchParams.has(paramName)) {
          removedParams.push({
            paramName: paramName,
            paramValue: url.searchParams.get(paramName)
          });
          url.searchParams.delete(paramName);
          changed = true;
        }
      });

      if (changed) {
        const cleanUrl = `${url.pathname}${url.search}${url.hash}`;
        window.history.replaceState(window.history.state, document.title, cleanUrl);

        debugGlobalMessageAutoDismiss("url_params_cleaned", {
          reason: reason || "",
          removedParams: removedParams,
          cleanUrl: cleanUrl
        });
      } else {
        debugGlobalMessageAutoDismiss("url_params_not_found", {
          reason: reason || ""
        });
      }
    } catch (error) {
      debugGlobalMessageAutoDismiss("url_params_clean_error", {
        reason: reason || "",
        error: String(error && error.message ? error.message : error)
      });
    }
  }

  function dismissElement(element, reason) {
    if (!element || !element.isConnected) {
      debugGlobalMessageAutoDismiss("dismiss_skip_not_connected", {
        reason: reason || "",
        element: getElementSnapshot(element)
      });
      return;
    }

    debugGlobalMessageAutoDismiss("dismiss_start", {
      reason: reason || "",
      elementBefore: getElementSnapshot(element)
    });

    element.dataset.appverboAutoDismissedV2 = "1";
    element.style.transition = "opacity 250ms ease, max-height 250ms ease, margin 250ms ease, padding 250ms ease";
    element.style.overflow = "hidden";
    element.style.opacity = "0";
    element.style.maxHeight = "0";
    element.style.marginTop = "0";
    element.style.marginBottom = "0";
    element.style.paddingTop = "0";
    element.style.paddingBottom = "0";

    window.setTimeout(function () {
      const stillConnectedBeforeRemove = Boolean(element && element.isConnected);

      if (element && element.isConnected) {
        element.remove();
      }

      debugGlobalMessageAutoDismiss("dismiss_removed", {
        reason: reason || "",
        stillConnectedBeforeRemove: stillConnectedBeforeRemove,
        stillConnectedAfterRemove: Boolean(element && element.isConnected)
      });
    }, 300);
  }

  function runGlobalMessageAutoDismiss(reason) {
    debugGlobalMessageAutoDismiss("run_start", {
      reason: reason || "",
      urlMessages: getUrlMessageValues()
    });

    const elements = collectGlobalMessageElements(reason);

    if (!elements.length) {
      debugGlobalMessageAutoDismiss("run_no_elements_found", {
        reason: reason || "",
        urlMessages: getUrlMessageValues()
      });

      cleanMessageParamsFromUrl(reason || "no_elements_found");
      return;
    }

    elements.forEach(function (element) {
      dismissElement(element, reason || "auto");
    });

    cleanMessageParamsFromUrl(reason || "auto");
  }

  function scheduleGlobalMessageAutoDismiss(reason) {
    debugGlobalMessageAutoDismiss("schedule", {
      reason: reason || "",
      timeoutMs: GLOBAL_MESSAGE_AUTO_DISMISS_MS,
      urlMessages: getUrlMessageValues()
    });

    window.setTimeout(function () {
      runGlobalMessageAutoDismiss(reason || "scheduled_3000ms");
    }, GLOBAL_MESSAGE_AUTO_DISMISS_MS);
  }

  function initGlobalMessageAutoDismiss() {
    debugGlobalMessageAutoDismiss("init", {
      bodyExists: Boolean(document.body),
      urlMessages: getUrlMessageValues(),
      scriptVersion: "GLOBAL_MESSAGE_AUTO_DISMISS_DEBUG_V2"
    });

    scheduleGlobalMessageAutoDismiss("init");

    window.setTimeout(function () {
      collectGlobalMessageElements("diagnostic_250ms");
    }, 250);

    window.setTimeout(function () {
      collectGlobalMessageElements("diagnostic_1000ms");
    }, 1000);

    const observer = new MutationObserver(function () {
      debugGlobalMessageAutoDismiss("mutation_observed", {});
      scheduleGlobalMessageAutoDismiss("mutation_observed");
    });

    if (document.body) {
      observer.observe(document.body, {
        childList: true,
        subtree: true
      });

      window.setTimeout(function () {
        observer.disconnect();
        debugGlobalMessageAutoDismiss("observer_disconnected", {});
      }, 10000);
    }

    window.appverboGlobalMessageDebugV2 = {
      logs: window.__APPVERBO_GLOBAL_MESSAGE_AUTO_DISMISS_DEBUG_V2_LOGS,
      collect: function () {
        return collectGlobalMessageElements("manual_collect");
      },
      runNow: function () {
        return runGlobalMessageAutoDismiss("manual_run");
      }
    };
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initGlobalMessageAutoDismiss);
  } else {
    initGlobalMessageAutoDismiss();
  }
})();
// APPVERBO_GLOBAL_MESSAGE_AUTO_DISMISS_DEBUG_V2_END
'''


####################################################################################
# (5) PATCH BACKEND
####################################################################################

def patch_backend_v2() -> None:
    content = read_text_v2(PROFILE_HANDLERS_PATH)

    content = remove_marked_block_v2(
        content,
        "APPVERBO_GLOBAL_MESSAGE_AUTO_DISMISS_DEBUG_ENDPOINT_V2_START",
        "APPVERBO_GLOBAL_MESSAGE_AUTO_DISMISS_DEBUG_ENDPOINT_V2_END",
    )

    content = content.rstrip() + "\n\n" + BACKEND_ENDPOINT_BLOCK.strip() + "\n"

    required_markers = [
        "APPVERBO_GLOBAL_MESSAGE_AUTO_DISMISS_DEBUG_ENDPOINT_V2_START",
        "@router.post(\"/debug/global-message-auto-dismiss\")",
        "APPVERBO_GLOBAL_MESSAGE_AUTO_DISMISS_DEBUG",
        "global_message_auto_dismiss_debug.log",
    ]

    missing = [
        marker
        for marker in required_markers
        if marker not in content
    ]

    if missing:
        raise RuntimeError("Marcadores backend ausentes: " + ", ".join(missing))

    write_text_v2(PROFILE_HANDLERS_PATH, content)


####################################################################################
# (6) PATCH FRONTEND
####################################################################################

def patch_frontend_v2() -> None:
    content = read_text_v2(JS_PATH)

    content = remove_marked_block_v2(
        content,
        "APPVERBO_GLOBAL_MESSAGE_AUTO_DISMISS_V1_START",
        "APPVERBO_GLOBAL_MESSAGE_AUTO_DISMISS_V1_END",
    )

    content = remove_marked_block_v2(
        content,
        "APPVERBO_GLOBAL_MESSAGE_AUTO_DISMISS_DEBUG_V2_START",
        "APPVERBO_GLOBAL_MESSAGE_AUTO_DISMISS_DEBUG_V2_END",
    )

    content = content.rstrip() + "\n\n" + JS_BLOCK.strip() + "\n"

    required_markers = [
        "APPVERBO_GLOBAL_MESSAGE_AUTO_DISMISS_DEBUG_V2_START",
        "GLOBAL_MESSAGE_AUTO_DISMISS_MS = 3000",
        "APPVERBO_GLOBAL_MESSAGE_AUTO_DISMISS_DEBUG",
        "collect_messages",
        "dismiss_start",
        "dismiss_removed",
        "url_params_cleaned",
        "appverboGlobalMessageDebugV2",
    ]

    missing = [
        marker
        for marker in required_markers
        if marker not in content
    ]

    if missing:
        raise RuntimeError("Marcadores frontend ausentes: " + ", ".join(missing))

    write_text_v2(JS_PATH, content)


####################################################################################
# (7) PATCH TEMPLATE CACHE BUSTER
####################################################################################

def patch_template_v2() -> None:
    content = read_text_v2(TEMPLATE_PATH)

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

    write_text_v2(TEMPLATE_PATH, content.rstrip() + "\n")


####################################################################################
# (8) EXECUCAO
####################################################################################

def main() -> None:
    patch_backend_v2()
    patch_frontend_v2()
    patch_template_v2()

    print("OK: endpoint backend de logger criado.")
    print("OK: logger frontend de mensagens globais criado.")
    print("OK: cache buster atualizado:", JS_VERSION)


if __name__ == "__main__":
    main()
