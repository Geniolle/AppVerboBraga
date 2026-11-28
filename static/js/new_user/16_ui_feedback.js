// new_user/16_ui_feedback.js: Mensagens flash, indicadores de abas, overlay de gravacao e multi-dropdown.
// Scripts classicos com escopo global partilhado; carregar pela ordem de templates/new_user.html.

// APPGENESIS_MEU_PERFIL_SUBSEQUENT_VISIBILITY_V1_END
// Regra global: clicar numa linha de qualquer tabela abre a edicao do registo (ou a exibicao,
// se nao houver permissao de edicao). Botoes, links, campos e menus dentro da linha mantem a sua acao.
// As linhas de processo de lista (tr[data-record-id]) tem handler proprio.
document.addEventListener("click", (event) => {
  const row = event.target.closest ? event.target.closest("table tbody tr") : null;
  if (!row || row.dataset.recordId) {
    return;
  }
  if (event.target.closest("button, a, input, select, textarea, label, summary, [role='menu'], .table-actions")) {
    return;
  }
  const action =
    row.querySelector('.appgenesis-row-actions-item-edit-v1, a[href*="target=edit-"], a[href*="_edit_id="]:not([href*="_view=1"])') ||
    row.querySelector('.appgenesis-row-actions-item-view-v1, a[href*="_view=1"], a[title^="Exibir"]');
  if (action) {
    action.click();
  }
});

/* APPGENESIS_AUTO_DISMISS_FLASH_MESSAGES_V1_START */
function appgenesisAutoDismissFlashMessages_v1() {
  // Sucesso: 4 s. Erro: 8 s. Ambos desaparecem com fade.
  const flashAlerts = Array.from(document.querySelectorAll(".alert.ok, .alert.error"));

  flashAlerts.forEach((alertElement) => {
    if (!alertElement || alertElement.dataset.appgenesisAutoDismiss === "1") {
      return;
    }

    alertElement.dataset.appgenesisAutoDismiss = "1";
    const dismissMs = alertElement.classList.contains("error") ? 8000 : 4000;

    window.setTimeout(() => {
      alertElement.style.transition = "opacity 250ms ease, max-height 250ms ease, margin 250ms ease, padding 250ms ease";
      alertElement.style.opacity = "0";
      alertElement.style.maxHeight = "0";
      alertElement.style.marginTop = "0";
      alertElement.style.marginBottom = "0";
      alertElement.style.paddingTop = "0";
      alertElement.style.paddingBottom = "0";
      alertElement.style.overflow = "hidden";

      window.setTimeout(() => {
        alertElement.remove();
      }, 300);
    }, dismissMs);
  });

  const url = new URL(window.location.href);
  const transientParams = [
    "success",
    "profile_success",
    "settings_success",
  ];

  let changed = false;

  transientParams.forEach((paramName) => {
    if (url.searchParams.has(paramName)) {
      url.searchParams.delete(paramName);
      changed = true;
    }
  });

  if (changed) {
    const cleanUrl = `${url.pathname}${url.search}${url.hash}`;
    window.history.replaceState({}, document.title, cleanUrl);
  }
}

document.addEventListener("DOMContentLoaded", appgenesisAutoDismissFlashMessages_v1);
/* APPGENESIS_AUTO_DISMISS_FLASH_MESSAGES_V1_END */

// APPGENESIS_ADMIN_POPSTATE_NAV_V1_START
window.addEventListener("popstate", function () {
  try {
    const params = new URLSearchParams(window.location.search);
    const menuKeyFromUrl = normalizeMenuKey(String(params.get("menu") || "").trim());
    if (menuKeyFromUrl !== "administrativo" || !menuConfig["administrativo"]) {
      return;
    }
    const adminTab = String(params.get("admin_tab") || "").trim().toLowerCase();
    const resolvedTarget = resolveAdminSelectedTargetV1({
      initialAdminTab: adminTab,
      startupHash: "",
      initialMenuTarget: String(params.get("target") || ""),
      settingsEditKey: ""
    });
    if (!resolvedTarget) {
      return;
    }
    selectedTargetByMenu["administrativo"] = resolvedTarget;
    setActiveSubmenu(resolvedTarget);
    applyContentForMenuTarget("administrativo", resolvedTarget);
    if (resolvedTarget === "#dynamic-process-card") {
      const sectionKey = adminTab || String(selectedDynamicSectionByMenu["administrativo"] || "");
      if (sectionKey) {
        selectedDynamicSectionByMenu["administrativo"] = sectionKey;
      }
      renderDynamicProcessCard(
        "administrativo",
        String(selectedDynamicSectionByMenu["administrativo"] || "")
      );
    }
    debugTabsLogV1("popstate:admin-restored", { adminTab, resolvedTarget });
  } catch (_) {}
});
// APPGENESIS_ADMIN_POPSTATE_NAV_V1_END

// Indicador informativo: bolinha vermelha na aba quando ha campo obrigatorio vazio nessa aba.
// So altera o DOM quando o estado muda (evita piscar a cada tecla).
// Durante o carregamento os renderizadores de quantidade preenchem os inputs (150-600ms).
// Acender a bolinha antes disso e apaga-la depois causava o pisca: so se acende apos a pagina estabilizar.
const PROFILE_DOTS_SETTLE_MS_V1 = 1500;
let profileDotsSettleTimerV1 = 0;

function refreshProfileMissingTabDotsV1() {
  const formEl = document.querySelector("#perfil-pessoal-card .profile-edit-form");
  if (!formEl) {
    return;
  }
  if (performance.now() < PROFILE_DOTS_SETTLE_MS_V1) {
    if (!profileDotsSettleTimerV1) {
      profileDotsSettleTimerV1 = window.setTimeout(function () {
        profileDotsSettleTimerV1 = 0;
        refreshProfileMissingTabDotsV1();
      }, PROFILE_DOTS_SETTLE_MS_V1 - performance.now() + 20);
    }
    return;
  }
  const missingSections = new Set();
  formEl.querySelectorAll("[required]").forEach((controlEl) => {
    if (controlEl.disabled) {
      return;
    }
    const wrapperEl = controlEl.closest(".field, .personal-item");
    if (!wrapperEl) {
      return;
    }
    if (wrapperEl.dataset.profileSubsequentHiddenV1 === "1" || wrapperEl.dataset.profileQuantityOriginDuplicateV1 === "1") {
      return;
    }
    const filled = controlEl.type === "checkbox" ? controlEl.checked : String(controlEl.value || "").trim() !== "";
    if (filled) {
      return;
    }
    missingSections.add(normalizeMenuKey(wrapperEl.dataset.profileSectionPane || "custom_dados_pessoais"));
  });

  document.querySelectorAll(".submenu-item[data-profile-section]").forEach((linkEl) => {
    const sectionKey = normalizeMenuKey(linkEl.dataset.profileSection);
    const dotEl = linkEl.querySelector(":scope > .profile-tab-missing-dot-v1");
    const shouldShow = missingSections.has(sectionKey);
    if (shouldShow && !dotEl) {
      const newDotEl = document.createElement("span");
      newDotEl.className = "profile-tab-missing-dot-v1";
      newDotEl.setAttribute("role", "img");
      newDotEl.setAttribute("aria-label", "Campos obrigatorios em falta nesta aba");
      newDotEl.title = "Campos obrigatorios em falta nesta aba";
      linkEl.appendChild(newDotEl);
    } else if (!shouldShow && dotEl) {
      dotEl.remove();
    }
  });
}

document.addEventListener("input", refreshProfileMissingTabDotsV1, true);
document.addEventListener("change", refreshProfileMissingTabDotsV1, true);
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", refreshProfileMissingTabDotsV1);
} else {
  refreshProfileMissingTabDotsV1();
}

// Esconde o cartao de Dados pessoais ate o JS aplicar o estado (leitura/edicao) da pagina:
// evita a pintura inicial do HTML do servidor (botao Editar piscando apos Gravar).
// Fallback em 1500 ms para nunca ficar escondido se o JS falhar.
(function markProfileCardReadyV1() {
  const markReady = () => {
    const cardEl = document.getElementById("perfil-pessoal-card");
    if (cardEl) {
      cardEl.classList.add("profile-ready");
    }
  };
  // Com profile_section na URL (retorno de Gravar), revela so depois do estado da secao aplicado.
  const hasProfileSectionInUrl = new URL(window.location.href).searchParams.has("profile_section");
  if (hasProfileSectionInUrl) {
    // Espera o estado inicial assentar (leitura) antes de revelar: o HTML do servidor pode pintar em edicao por instantes.
    document.addEventListener("appgenesis:profile-section-restored", () => {
      window.setTimeout(() => window.requestAnimationFrame(markReady), 1000);
    }, { once: true });
  } else {
    window.setTimeout(markReady, 260);
  }
  window.setTimeout(markReady, 1500);
})();

// Enquanto Dados pessoais e gravado (POST + redirect), tapa o cartao com "A gravar..."
// para nao se ver a tela anterior durante o pedido.
(function bindProfileSavingOverlayV1() {
  const cardEl = document.getElementById("perfil-pessoal-card");
  const formEl = cardEl ? cardEl.querySelector(".profile-edit-form") : null;
  if (!formEl) {
    return;
  }
  formEl.addEventListener("submit", () => {
    cardEl.classList.add("profile-saving");
    formEl.querySelectorAll("button[type=submit]").forEach((btnEl) => {
      btnEl.disabled = true;
    });
  });
})();

// As abas sao reconstruidas por outros gestores depois do arranque (tabs_overflow_v1.js),
// o que apagava a bolinha. Recalcula sempre que o DOM muda (so mexe no DOM se o estado mudar).
(function keepProfileMissingTabDotsV1() {
  if (!document.getElementById("perfil-pessoal-card")) {
    return;
  }
  new MutationObserver(() => refreshProfileMissingTabDotsV1()).observe(document.body, {
    childList: true,
    subtree: true
  });
  window.setTimeout(refreshProfileMissingTabDotsV1, 300);
  window.setTimeout(refreshProfileMissingTabDotsV1, 1200);
})();

// Campo de selecao multipla (Autorizacao): abre/fecha a lista de interruptores e atualiza o resumo.
(function initMultiDropdownToggleV1() {
  function summaryFor(dropdownEl) {
    const labels = Array.from(dropdownEl.querySelectorAll("input[type='checkbox']:checked")).map((inputEl) => {
      const labelEl = inputEl.closest("label");
      const textEl = labelEl ? labelEl.querySelector(".admin-subprocess-toggle-label-v1") : null;
      return textEl ? textEl.textContent.trim() : inputEl.value;
    });
    const summaryEl = dropdownEl.querySelector("[data-multi-summary]");
    if (summaryEl) {
      summaryEl.textContent = labels.length ? labels.join(", ") : "Selecione";
    }
  }

  function closeAllPanels() {
    document.querySelectorAll(".admin-subprocess-multi-panel-v1").forEach((panelEl) => {
      panelEl.hidden = true;
      const dropdownEl = panelEl.closest("[data-multi-dropdown]");
      const triggerEl = dropdownEl ? dropdownEl.querySelector("[data-multi-trigger]") : null;
      if (triggerEl) {
        triggerEl.setAttribute("aria-expanded", "false");
      }
    });
  }

  document.addEventListener("click", (event) => {
    const triggerEl = event.target.closest ? event.target.closest("[data-multi-trigger]") : null;
    if (triggerEl) {
      const dropdownEl = triggerEl.closest("[data-multi-dropdown]");
      const panelEl = dropdownEl ? dropdownEl.querySelector(".admin-subprocess-multi-panel-v1") : null;
      if (!panelEl) {
        return;
      }
      const willOpen = panelEl.hidden;
      closeAllPanels();
      if (willOpen) {
        const rect = triggerEl.getBoundingClientRect();
        panelEl.style.top = `${rect.bottom + 4}px`;
        panelEl.style.left = `${rect.left}px`;
        panelEl.style.width = `${rect.width}px`;
      }
      panelEl.hidden = !willOpen;
      triggerEl.setAttribute("aria-expanded", String(willOpen));
      return;
    }
    if (!event.target.closest(".admin-subprocess-multi-dropdown-v1")) {
      closeAllPanels();
    }
  });

  window.addEventListener("scroll", closeAllPanels, true);
  window.addEventListener("resize", closeAllPanels);

  document.addEventListener("change", (event) => {
    const dropdownEl = event.target.closest ? event.target.closest("[data-multi-dropdown]") : null;
    if (dropdownEl && event.target.matches("input[type='checkbox']")) {
      summaryFor(dropdownEl);
    }
  });
})();
