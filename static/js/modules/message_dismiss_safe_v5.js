// APPVERBO_MESSAGE_DISMISS_SAFE_V5_MODULE_START
(function registerMessageDismissSafeV5Module() {
  "use strict";

  window.APPVERBO_SETUP_MESSAGE_DISMISS_SAFE_V5 = function setupMessageDismissSafeV5(options) {
    const deps = options && typeof options === "object" ? options : {};
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
  const PROTECTED_STRUCTURAL_TAGS = new Set([
    "section",
    "article",
    "main",
    "aside",
    "nav",
    "form",
    "details",
    "fieldset",
    "table",
    "thead",
    "tbody",
    "tfoot",
    "tr",
    "td",
    "th",
    "ul",
    "ol",
    "li"
  ]);

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

  function hasExplicitDismissibleMessageClass(element) {
    if (!element) {
      return false;
    }

    const classText = String(element.className || "").toLowerCase();

    return (
      classText.includes("alert") ||
      classText.includes("toast") ||
      classText.includes("message") ||
      classText.includes("notification") ||
      classText.includes("flash")
    );
  }

  function isDismissibleMessageContainer(element) {
    if (!element || !hasMessageStyleSignal(element)) {
      return false;
    }

    const role = String(element.getAttribute("role") || "").toLowerCase();
    const tagName = String(element.tagName || "").toLowerCase();

    if (role === "alert") {
      return true;
    }

    if (!hasExplicitDismissibleMessageClass(element)) {
      return false;
    }

    if (PROTECTED_STRUCTURAL_TAGS.has(tagName)) {
      return false;
    }

    return true;
  }

  function findBestMessageContainer(element, normalizedMessageText) {
    if (!element) {
      return null;
    }

    let current = element;
    let depth = 0;

    while (current && current !== document.body && depth < 6) {
      const text = normalizeText(current.textContent || "");

      if (!text || !text.includes(normalizedMessageText)) {
        break;
      }

      if (isDismissibleMessageContainer(current)) {
        return current;
      }

      current = current.parentElement;
      depth += 1;
    }

    return null;
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
  };
})();
// APPVERBO_MESSAGE_DISMISS_SAFE_V5_MODULE_END
