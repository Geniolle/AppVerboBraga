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

JS_VERSION = "new_user.js?v=20260509-force-message-dismiss-static-js-v4"


####################################################################################
# (2) FUNCOES AUXILIARES
####################################################################################

def read_text_v4(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text_v4(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def remove_js_block_v4(content: str, start_marker: str, end_marker: str) -> str:
    pattern = re.compile(
        r"^[ \t]*//\s*" + re.escape(start_marker) + r".*?"
        + r"^[ \t]*//\s*" + re.escape(end_marker) + r"[^\r\n]*(?:\r?\n)?",
        flags=re.DOTALL | re.MULTILINE,
    )

    return pattern.sub("", content)


def remove_html_block_v4(content: str, start_marker: str, end_marker: str) -> str:
    pattern = re.compile(
        r"<!--\s*" + re.escape(start_marker) + r"\s*-->.*?"
        r"<!--\s*" + re.escape(end_marker) + r"\s*-->",
        flags=re.DOTALL,
    )

    return pattern.sub("", content)


####################################################################################
# (3) ENDPOINT DE DEBUG, CASO NAO EXISTA
####################################################################################

BACKEND_ENDPOINT_BLOCK = r'''
# APPVERBO_GLOBAL_MESSAGE_AUTO_DISMISS_DEBUG_ENDPOINT_V4_START
@router.post("/debug/global-message-auto-dismiss")
async def appverbo_global_message_auto_dismiss_debug_v4(request: Request) -> JSONResponse:
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
            "logger": "APPVERBO_GLOBAL_MESSAGE_AUTO_DISMISS_DEBUG_ENDPOINT_V4",
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
# APPVERBO_GLOBAL_MESSAGE_AUTO_DISMISS_DEBUG_ENDPOINT_V4_END
'''


####################################################################################
# (4) BLOCO JS GLOBAL
####################################################################################

JS_BLOCK = r'''
// APPVERBO_FORCE_MESSAGE_DISMISS_V4_START
//###################################################################################
// (FORCE_MESSAGE_DISMISS_V4) REGRA GLOBAL: MENSAGENS DESAPARECEM EM 3 SEGUNDOS
//###################################################################################

(function () {
  "use strict";

  const VERSION = "APPVERBO_FORCE_MESSAGE_DISMISS_V4";
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

  const MESSAGE_TEXT_HINTS = [
    "sucesso",
    "erro",
    "atualizado",
    "atualizada",
    "atualizados",
    "atualizadas",
    "criado",
    "criada",
    "eliminado",
    "eliminada",
    "gravado",
    "gravada",
    "guardado",
    "guardada",
    "inválido",
    "invalido",
    "obrigatório",
    "obrigatorio"
  ];

  const MESSAGE_SELECTOR = [
    "[role='alert']",
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
    "[class*='error']",
    "[class*='green']",
    "[class*='emerald']",
    "[class*='red']",
    "[class*='rose']",
    "[class*='yellow']",
    "[class*='amber']"
  ].join(",");

  function normalizeText(value) {
    return String(value || "")
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

  function readUrlMessagesFromLocation() {
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

  const initialUrlMessages = readUrlMessagesFromLocation();

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
      outerHTML: safeText(element.outerHTML || "", 1000),
      computedStyle: computedStyle
    };
  }

  function debugForceMessageDismiss(stage, data) {
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
      initialUrlMessages: initialUrlMessages,
      currentUrlMessages: readUrlMessagesFromLocation(),
      data: data || {}
    };

    window.__APPVERBO_FORCE_MESSAGE_DISMISS_V4_LOGS =
      window.__APPVERBO_FORCE_MESSAGE_DISMISS_V4_LOGS || [];
    window.__APPVERBO_FORCE_MESSAGE_DISMISS_V4_LOGS.push(payload);

    try {
      console.log("APPVERBO_FORCE_MESSAGE_DISMISS_V4", payload);
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

  function elementHasMessageSignal(element) {
    if (!element) {
      return false;
    }

    const role = String(element.getAttribute("role") || "").toLowerCase();

    if (role === "alert") {
      return true;
    }

    const classText = String(element.className || "").toLowerCase();

    if (
      classText.includes("alert") ||
      classText.includes("message") ||
      classText.includes("toast") ||
      classText.includes("success") ||
      classText.includes("error") ||
      classText.includes("notification") ||
      classText.includes("green") ||
      classText.includes("emerald") ||
      classText.includes("red") ||
      classText.includes("rose") ||
      classText.includes("yellow") ||
      classText.includes("amber")
    ) {
      return true;
    }

    return false;
  }

  function textHasMessageHint(text) {
    const normalizedText = normalizeText(text);

    if (!normalizedText) {
      return false;
    }

    const urlMessages = initialUrlMessages.concat(readUrlMessagesFromLocation());

    if (
      urlMessages.some(function (message) {
        return message.normalizedValue && normalizedText.includes(message.normalizedValue);
      })
    ) {
      return true;
    }

    return MESSAGE_TEXT_HINTS.some(function (hint) {
      return normalizedText.includes(normalizeText(hint));
    });
  }

  function findBestMessageContainer(element) {
    if (!element) {
      return null;
    }

    let current = element;
    let best = element;
    let depth = 0;

    while (current && current !== document.body && depth < 8) {
      const text = normalizeText(current.textContent || "");

      if (!text) {
        break;
      }

      if (elementHasMessageSignal(current)) {
        best = current;
        break;
      }

      if (text.length <= 350) {
        best = current;
      }

      current = current.parentElement;
      depth += 1;
    }

    return best;
  }

  function findMessagesByText() {
    const found = [];

    if (!document.body) {
      return found;
    }

    const allElements = Array.from(document.body.querySelectorAll("*"));

    allElements.forEach(function (element) {
      const tagName = String(element.tagName || "").toLowerCase();

      if (["script", "style", "svg", "path", "meta", "link", "option"].includes(tagName)) {
        return;
      }

      const text = element.textContent || "";

      if (!textHasMessageHint(text)) {
        return;
      }

      const normalizedText = normalizeText(text);

      if (normalizedText.length > 900) {
        return;
      }

      const container = findBestMessageContainer(element);

      if (container && !found.includes(container)) {
        found.push(container);
      }
    });

    return found;
  }

  function findMessagesBySelector() {
    if (!document.body) {
      return [];
    }

    const found = [];

    document.body.querySelectorAll(MESSAGE_SELECTOR).forEach(function (element) {
      const text = element.textContent || "";

      if (!textHasMessageHint(text)) {
        return;
      }

      const container = findBestMessageContainer(element);

      if (container && !found.includes(container)) {
        found.push(container);
      }
    });

    return found;
  }

  function collectMessageElements(reason) {
    const found = [];

    findMessagesBySelector().forEach(function (element) {
      if (element && !found.includes(element)) {
        found.push(element);
      }
    });

    findMessagesByText().forEach(function (element) {
      if (element && !found.includes(element)) {
        found.push(element);
      }
    });

    const finalElements = found.filter(function (element) {
      return element && element.isConnected && element.dataset.appverboForceMessageDismissV4 !== "1";
    });

    debugForceMessageDismiss("collect", {
      reason: reason || "",
      finalElementsCount: finalElements.length,
      finalElements: finalElements.slice(0, 12).map(getElementSnapshot)
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

        debugForceMessageDismiss("url_cleaned", {
          reason: reason || "",
          removed: removed,
          cleanUrl: cleanUrl
        });
      } else {
        debugForceMessageDismiss("url_no_message_params", {
          reason: reason || ""
        });
      }
    } catch (error) {
      debugForceMessageDismiss("url_clean_error", {
        reason: reason || "",
        error: String(error && error.message ? error.message : error)
      });
    }
  }

  function removeMessageElement(element, reason) {
    if (!element || !element.isConnected) {
      debugForceMessageDismiss("remove_skip_not_connected", {
        reason: reason || "",
        element: getElementSnapshot(element)
      });
      return;
    }

    element.dataset.appverboForceMessageDismissV4 = "1";

    debugForceMessageDismiss("remove_start", {
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

      debugForceMessageDismiss("remove_done", {
        reason: reason || "",
        wasConnected: wasConnected,
        isConnectedAfter: Boolean(element && element.isConnected)
      });
    }, REMOVE_ANIMATION_MS);
  }

  function runForceMessageDismiss(reason) {
    debugForceMessageDismiss("run_start", {
      reason: reason || ""
    });

    const elements = collectMessageElements(reason || "run");

    if (!elements.length) {
      debugForceMessageDismiss("run_no_elements", {
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

  function scheduleForceMessageDismiss(reason, delayMs) {
    debugForceMessageDismiss("schedule", {
      reason: reason || "",
      delayMs: delayMs
    });

    window.setTimeout(function () {
      runForceMessageDismiss(reason || "scheduled");
    }, delayMs);
  }

  function initForceMessageDismiss() {
    debugForceMessageDismiss("init", {
      bodyExists: Boolean(document.body),
      initialUrlMessages: initialUrlMessages
    });

    scheduleForceMessageDismiss("scheduled_3000ms", AUTO_DISMISS_MS);

    window.setTimeout(function () {
      collectMessageElements("diagnostic_500ms");
    }, 500);

    window.setTimeout(function () {
      collectMessageElements("diagnostic_1500ms");
    }, 1500);

    window.setTimeout(function () {
      runForceMessageDismiss("safety_3500ms");
    }, 3500);

    window.setTimeout(function () {
      runForceMessageDismiss("safety_5000ms");
    }, 5000);

    window.appverboForceMessageDismissV4 = {
      logs: window.__APPVERBO_FORCE_MESSAGE_DISMISS_V4_LOGS || [],
      collect: function () {
        return collectMessageElements("manual_collect");
      },
      runNow: function () {
        return runForceMessageDismiss("manual_run");
      }
    };
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initForceMessageDismiss);
  } else {
    initForceMessageDismiss();
  }
})();
// APPVERBO_FORCE_MESSAGE_DISMISS_V4_END
'''


####################################################################################
# (5) PATCH BACKEND
####################################################################################

def patch_backend_v4() -> None:
    content = read_text_v4(PROFILE_HANDLERS_PATH)

    if "/debug/global-message-auto-dismiss" in content:
        return

    content = content.rstrip() + "\n\n" + BACKEND_ENDPOINT_BLOCK.strip() + "\n"
    write_text_v4(PROFILE_HANDLERS_PATH, content)


####################################################################################
# (6) PATCH JS
####################################################################################

def patch_js_v4() -> None:
    content = read_text_v4(JS_PATH)

    removable_blocks = [
        ("APPVERBO_GLOBAL_MESSAGE_AUTO_DISMISS_V1_START", "APPVERBO_GLOBAL_MESSAGE_AUTO_DISMISS_V1_END"),
        ("APPVERBO_GLOBAL_MESSAGE_AUTO_DISMISS_DEBUG_V2_START", "APPVERBO_GLOBAL_MESSAGE_AUTO_DISMISS_DEBUG_V2_END"),
        ("APPVERBO_FORCE_MESSAGE_DISMISS_V4_START", "APPVERBO_FORCE_MESSAGE_DISMISS_V4_END"),
    ]

    for start_marker, end_marker in removable_blocks:
        content = remove_js_block_v4(content, start_marker, end_marker)

    content = content.rstrip() + "\n\n" + JS_BLOCK.strip() + "\n"

    required = [
        "APPVERBO_FORCE_MESSAGE_DISMISS_V4_START",
        "AUTO_DISMISS_MS = 3000",
        "initialUrlMessages",
        "collectMessageElements",
        "remove_start",
        "remove_done",
        "url_cleaned",
        "appverboForceMessageDismissV4",
    ]

    missing = [marker for marker in required if marker not in content]

    if missing:
        raise RuntimeError("Marcadores ausentes no JS: " + ", ".join(missing))

    write_text_v4(JS_PATH, content)


####################################################################################
# (7) PATCH TEMPLATE
####################################################################################

def patch_template_v4() -> None:
    content = read_text_v4(TEMPLATE_PATH)

    content = remove_html_block_v4(
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

    write_text_v4(TEMPLATE_PATH, content.rstrip() + "\n")


####################################################################################
# (8) EXECUCAO
####################################################################################

def main() -> None:
    patch_backend_v4()
    patch_js_v4()
    patch_template_v4()

    print("OK: regra global V4 inserida no static/js/new_user.js.")
    print("OK: loggers antigos de mensagem removidos do JS/template.")
    print("OK: cache buster atualizado:", JS_VERSION)


if __name__ == "__main__":
    main()
