from __future__ import annotations

import re
from pathlib import Path


####################################################################################
# (1) CONFIGURACAO
####################################################################################

PROJECT_ROOT = Path.cwd()
TEMPLATE_PATH = PROJECT_ROOT / "templates" / "new_user.html"


####################################################################################
# (2) FUNCOES AUXILIARES
####################################################################################

def read_text_v3(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text_v3(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def remove_existing_block_v3(content: str) -> str:
    pattern = re.compile(
        r"<!--\s*APPVERBO_TEMPLATE_MESSAGE_AUTODISMISS_V3_START\s*-->.*?"
        r"<!--\s*APPVERBO_TEMPLATE_MESSAGE_AUTODISMISS_V3_END\s*-->",
        flags=re.DOTALL,
    )

    return pattern.sub("", content)


####################################################################################
# (3) BLOCO INLINE DE AUTO-DISMISS GLOBAL
####################################################################################

INLINE_BLOCK = r'''
<!-- APPVERBO_TEMPLATE_MESSAGE_AUTODISMISS_V3_START -->
<script>
(function () {
  "use strict";

  const AUTO_DISMISS_MS = 3000;
  const REMOVE_ANIMATION_MS = 250;
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
    "[class*='error']"
  ].join(",");

  const startedAt = Date.now();
  let alreadyScheduled = false;
  let observer = null;

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
    const limit = maxSize || 600;

    if (cleanValue.length > limit) {
      return cleanValue.slice(0, limit) + "...[TRUNCATED]";
    }

    return cleanValue;
  }

  function getUrlMessages() {
    const urlMessages = [];
    const params = new URLSearchParams(window.location.search || "");

    MESSAGE_PARAM_NAMES.forEach(function (paramName) {
      const value = params.get(paramName);

      if (value && String(value).trim() !== "") {
        urlMessages.push({
          paramName: paramName,
          value: String(value).trim(),
          normalizedValue: normalizeText(value)
        });
      }
    });

    return urlMessages;
  }

  function getElementSnapshot(element) {
    if (!element) {
      return null;
    }

    let computed = {};

    try {
      const style = window.getComputedStyle(element);
      computed = {
        display: style.display,
        visibility: style.visibility,
        opacity: style.opacity,
        backgroundColor: style.backgroundColor,
        color: style.color,
        borderColor: style.borderColor
      };
    } catch (error) {
      computed = {
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
      computedStyle: computed
    };
  }

  function debugTemplateAutoDismiss(stage, data) {
    const payload = {
      stage: stage,
      elapsedMs: Date.now() - startedAt,
      location: {
        href: window.location.href,
        pathname: window.location.pathname,
        search: window.location.search,
        hash: window.location.hash
      },
      readyState: document.readyState,
      data: data || {}
    };

    try {
      console.log("APPVERBO_TEMPLATE_MESSAGE_AUTODISMISS_V3", payload);
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
          logger: "APPVERBO_TEMPLATE_MESSAGE_AUTODISMISS_V3",
          payload: payload
        }),
        keepalive: true
      }).catch(function () {});
    } catch (error) {
      return;
    }
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

    if (
      classText.includes("alert") ||
      classText.includes("message") ||
      classText.includes("toast") ||
      classText.includes("success") ||
      classText.includes("error") ||
      classText.includes("notification")
    ) {
      return true;
    }

    const text = normalizeText(element.textContent || "");

    return MESSAGE_TEXT_HINTS.some(function (hint) {
      return text.includes(normalizeText(hint));
    });
  }

  function findBestContainer(element) {
    if (!element) {
      return null;
    }

    let current = element;

    while (current && current !== document.body) {
      if (hasMessageSignal(current)) {
        return current;
      }

      current = current.parentElement;
    }

    return element;
  }

  function findElementsByUrlMessages(urlMessages) {
    const found = [];

    if (!document.body) {
      return found;
    }

    const candidates = Array.from(document.body.querySelectorAll("*")).filter(function (element) {
      const tagName = String(element.tagName || "").toLowerCase();

      if (["script", "style", "svg", "path", "meta", "link", "option"].includes(tagName)) {
        return false;
      }

      const text = normalizeText(element.textContent || "");

      if (!text) {
        return false;
      }

      return urlMessages.some(function (message) {
        return message.normalizedValue && text.includes(message.normalizedValue);
      });
    });

    candidates.sort(function (left, right) {
      const leftLength = normalizeText(left.textContent || "").length;
      const rightLength = normalizeText(right.textContent || "").length;
      return leftLength - rightLength;
    });

    candidates.forEach(function (element) {
      const container = findBestContainer(element);

      if (container && !found.includes(container)) {
        found.push(container);
      }
    });

    return found;
  }

  function findElementsBySelectors() {
    if (!document.body) {
      return [];
    }

    return Array.from(document.body.querySelectorAll(MESSAGE_SELECTOR)).filter(function (element) {
      const text = normalizeText(element.textContent || "");

      if (!text) {
        return false;
      }

      return (
        MESSAGE_TEXT_HINTS.some(function (hint) {
          return text.includes(normalizeText(hint));
        }) ||
        getUrlMessages().some(function (message) {
          return message.normalizedValue && text.includes(message.normalizedValue);
        })
      );
    });
  }

  function collectMessageElements(reason) {
    const urlMessages = getUrlMessages();
    const collected = [];

    findElementsBySelectors().forEach(function (element) {
      const container = findBestContainer(element);

      if (container && !collected.includes(container)) {
        collected.push(container);
      }
    });

    findElementsByUrlMessages(urlMessages).forEach(function (element) {
      if (element && !collected.includes(element)) {
        collected.push(element);
      }
    });

    const finalElements = collected.filter(function (element) {
      return element && element.isConnected && element.dataset.appverboTemplateAutoDismissV3 !== "1";
    });

    debugTemplateAutoDismiss("collect", {
      reason: reason || "",
      urlMessages: urlMessages,
      finalElementsCount: finalElements.length,
      finalElements: finalElements.slice(0, 8).map(getElementSnapshot)
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

        debugTemplateAutoDismiss("url_cleaned", {
          reason: reason || "",
          cleanUrl: cleanUrl,
          removed: removed
        });
      }
    } catch (error) {
      debugTemplateAutoDismiss("url_clean_error", {
        reason: reason || "",
        error: String(error && error.message ? error.message : error)
      });
    }
  }

  function removeMessageElement(element, reason) {
    if (!element || !element.isConnected) {
      return;
    }

    element.dataset.appverboTemplateAutoDismissV3 = "1";

    debugTemplateAutoDismiss("remove_start", {
      reason: reason || "",
      element: getElementSnapshot(element)
    });

    element.style.transition = "opacity 250ms ease, max-height 250ms ease, margin 250ms ease, padding 250ms ease";
    element.style.overflow = "hidden";
    element.style.opacity = "0";
    element.style.maxHeight = "0";
    element.style.marginTop = "0";
    element.style.marginBottom = "0";
    element.style.paddingTop = "0";
    element.style.paddingBottom = "0";

    window.setTimeout(function () {
      const wasConnected = Boolean(element && element.isConnected);

      if (element && element.isConnected) {
        element.remove();
      }

      debugTemplateAutoDismiss("remove_done", {
        reason: reason || "",
        wasConnected: wasConnected,
        isConnectedAfter: Boolean(element && element.isConnected)
      });
    }, REMOVE_ANIMATION_MS);
  }

  function runAutoDismiss(reason) {
    const elements = collectMessageElements(reason || "run");

    if (!elements.length) {
      debugTemplateAutoDismiss("no_elements", {
        reason: reason || "",
        urlMessages: getUrlMessages()
      });
      cleanMessageParamsFromUrl(reason || "no_elements");
      return;
    }

    elements.forEach(function (element) {
      removeMessageElement(element, reason || "run");
    });

    cleanMessageParamsFromUrl(reason || "removed");
  }

  function scheduleAutoDismiss(reason) {
    if (alreadyScheduled) {
      return;
    }

    alreadyScheduled = true;

    debugTemplateAutoDismiss("scheduled", {
      reason: reason || "",
      timeoutMs: AUTO_DISMISS_MS,
      urlMessages: getUrlMessages()
    });

    window.setTimeout(function () {
      runAutoDismiss(reason || "scheduled_3s");
    }, AUTO_DISMISS_MS);
  }

  function init() {
    debugTemplateAutoDismiss("init", {
      urlMessages: getUrlMessages(),
      bodyExists: Boolean(document.body)
    });

    scheduleAutoDismiss("init");

    window.setTimeout(function () {
      collectMessageElements("diagnostic_500ms");
    }, 500);

    window.setTimeout(function () {
      collectMessageElements("diagnostic_1500ms");
    }, 1500);

    if (document.body) {
      observer = new MutationObserver(function () {
        const urlMessages = getUrlMessages();

        if (urlMessages.length) {
          debugTemplateAutoDismiss("mutation_with_url_message", {
            urlMessages: urlMessages
          });
          scheduleAutoDismiss("mutation_with_url_message");
        }
      });

      observer.observe(document.body, {
        childList: true,
        subtree: true
      });

      window.setTimeout(function () {
        if (observer) {
          observer.disconnect();
        }

        debugTemplateAutoDismiss("observer_disconnected", {});
      }, 8000);
    }

    window.appverboTemplateMessageAutoDismissV3 = {
      runNow: function () {
        runAutoDismiss("manual_run");
      },
      collect: function () {
        return collectMessageElements("manual_collect");
      }
    };
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
</script>
<!-- APPVERBO_TEMPLATE_MESSAGE_AUTODISMISS_V3_END -->
'''


####################################################################################
# (4) APLICAR PATCH
####################################################################################

def main() -> None:
    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"Ficheiro nao encontrado: {TEMPLATE_PATH}")

    content = read_text_v3(TEMPLATE_PATH)
    content = remove_existing_block_v3(content)

    if "</body>" in content:
        content = content.replace("</body>", INLINE_BLOCK + "\n</body>", 1)
    elif "</html>" in content:
        content = content.replace("</html>", INLINE_BLOCK + "\n</html>", 1)
    else:
        content = content.rstrip() + "\n" + INLINE_BLOCK + "\n"

    required_markers = [
        "APPVERBO_TEMPLATE_MESSAGE_AUTODISMISS_V3_START",
        "AUTO_DISMISS_MS = 3000",
        "APPVERBO_TEMPLATE_MESSAGE_AUTODISMISS_V3",
        "profile_success",
        "profile_error",
        "appverboTemplateMessageAutoDismissV3",
        "url_cleaned",
        "remove_start",
        "remove_done",
    ]

    missing = [
        marker
        for marker in required_markers
        if marker not in content
    ]

    if missing:
        raise RuntimeError("Marcadores ausentes depois do patch: " + ", ".join(missing))

    write_text_v3(TEMPLATE_PATH, content.rstrip() + "\n")

    print("OK: auto-dismiss inline V3 inserido no template.")
    print("OK: mensagens globais devem desaparecer em 3 segundos.")
    print("OK: logs aparecem com APPVERBO_TEMPLATE_MESSAGE_AUTODISMISS_V3.")


if __name__ == "__main__":
    main()
