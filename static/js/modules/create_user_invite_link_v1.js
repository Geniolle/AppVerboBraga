//###################################################################################
// (1) CREATE USER INVITE LINK V1
//###################################################################################
(function registerCreateUserInviteLinkV1() {
  "use strict";

  function setupGeneratedInviteLinkCopy() {
    const copyButtonEl = document.getElementById("generated-invite-link-copy-btn");
    if (!copyButtonEl) {
      return;
    }
    const targetId = String(copyButtonEl.getAttribute("data-copy-target") || "").trim();
    if (!targetId) {
      return;
    }
    const inputEl = document.getElementById(targetId);
    if (!inputEl) {
      return;
    }
    const defaultLabel = copyButtonEl.textContent || "Copiar";
    const showButtonFeedback = (label) => {
      copyButtonEl.textContent = label;
      window.setTimeout(() => {
        copyButtonEl.textContent = defaultLabel;
      }, 1200);
    };

    copyButtonEl.addEventListener("click", async () => {
      const copyValue = String(inputEl.value || "").trim();
      if (!copyValue) {
        showButtonFeedback("Sem link");
        return;
      }
      try {
        if (navigator.clipboard && typeof navigator.clipboard.writeText === "function") {
          await navigator.clipboard.writeText(copyValue);
        } else {
          inputEl.removeAttribute("readonly");
          inputEl.select();
          document.execCommand("copy");
          inputEl.setAttribute("readonly", "readonly");
        }
        showButtonFeedback("Copiado");
      } catch (_error) {
        showButtonFeedback("Falhou");
      }
    });
  }

  function setupCreateUserGenerateLinkShortcut(options = {}) {
    const shortcutButtonEl = document.getElementById("create-user-generate-link-shortcut-btn");
    if (!shortcutButtonEl) {
      return;
    }

    const currentEntityId = Number.parseInt(
      String(options.currentEntityId || "").trim(),
      10
    );
    const linkSlotEl = document.querySelector(".entity-create-link-slot");

    function renderGenerateLinkContent(contentEl) {
      if (!linkSlotEl) {
        return;
      }
      linkSlotEl.innerHTML = "";
      linkSlotEl.appendChild(contentEl);
    }

    function showGenerateLinkMessage(message) {
      const messageEl = document.createElement("div");
      messageEl.className = "entity-create-link-message";
      messageEl.textContent = message;
      renderGenerateLinkContent(messageEl);
    }

    function showGeneratedSignupLink(signupLink) {
      const outputEl = document.createElement("div");
      outputEl.className = "entity-create-link-output";

      const inputEl = document.createElement("input");
      inputEl.id = "generated-invite-link-input";
      inputEl.type = "text";
      inputEl.className = "readonly-field";
      inputEl.value = signupLink;
      inputEl.readOnly = true;

      const copyButtonEl = document.createElement("button");
      copyButtonEl.id = "generated-invite-link-copy-btn";
      copyButtonEl.type = "button";
      copyButtonEl.className = "action-btn-secondary entity-create-link-copy-btn";
      copyButtonEl.setAttribute("data-copy-target", "generated-invite-link-input");
      copyButtonEl.textContent = "Copiar";

      outputEl.appendChild(inputEl);
      outputEl.appendChild(copyButtonEl);
      renderGenerateLinkContent(outputEl);
      setupGeneratedInviteLinkCopy();
    }

    shortcutButtonEl.addEventListener("click", (event) => {
      event.preventDefault();
      if (!Number.isFinite(currentEntityId) || currentEntityId <= 0) {
        showGenerateLinkMessage("Selecione uma entidade antes de gerar o link.");
        return;
      }
      const signupUrl = new URL("/login", window.location.origin);
      signupUrl.searchParams.set("mode", "signup");
      signupUrl.searchParams.set("entity_id", String(currentEntityId));
      showGeneratedSignupLink(signupUrl.toString());
    });
  }

  window.APPVERBO_SETUP_GENERATED_INVITE_LINK_COPY_V1 = setupGeneratedInviteLinkCopy;
  window.APPVERBO_SETUP_CREATE_USER_GENERATE_LINK_SHORTCUT_V1 = setupCreateUserGenerateLinkShortcut;
})();
