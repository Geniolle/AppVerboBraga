// new_user/11_admin_users.js: Foto de perfil, logotipo de entidade, convites e editor de sessoes.
// Scripts classicos com escopo global partilhado; carregar pela ordem de templates/new_user.html.

// Foto de perfil (se existir) substitui as iniciais no avatar.
const profilePhotoMenuEl = document.getElementById("user-menu");
const profilePhotoUrl = profilePhotoMenuEl && profilePhotoMenuEl.dataset ? String(profilePhotoMenuEl.dataset.photoUrl || "").trim() : "";
const avatarDataUri = profilePhotoUrl || buildAvatarDataUri(currentUserName);

// Pre-visualizacao da foto escolhida no formulario de Dados pessoais.
const profilePhotoInputEl = document.getElementById("edit_profile_photo");
const profilePhotoPreviewEl = document.getElementById("edit_profile_photo_preview");
if (profilePhotoInputEl && profilePhotoPreviewEl) {
  profilePhotoInputEl.addEventListener("change", () => {
    const file = profilePhotoInputEl.files && profilePhotoInputEl.files[0];
    if (!file) {
      return;
    }
    profilePhotoPreviewEl.src = URL.createObjectURL(file);
    profilePhotoPreviewEl.hidden = false;
    const placeholderEl = profilePhotoPreviewEl.parentElement
      ? profilePhotoPreviewEl.parentElement.querySelector(".profile-photo-placeholder-v1")
      : null;
    if (placeholderEl) {
      placeholderEl.hidden = true;
    }
  });
}
// Seletor de imagem/icone da entidade (Dados da empresa e Editar entidade): clique na foto abre
// o menu "Selecionar imagem" / "Remover imagem". Mesmo comportamento para os dois formularios.
function bindEntityLogoPickerV1(prefix) {
  const inputEl = document.getElementById(`${prefix}_logo_file`);
  const previewEl = document.getElementById(`${prefix}_logo_preview`);
  const pickerEl = document.getElementById(`${prefix}_logo_picker`);
  const menuEl = document.getElementById(`${prefix}_logo_menu`);
  const removeEl = document.getElementById(`${prefix}_remove_logo`);
  if (!inputEl || !previewEl || !pickerEl || !menuEl || !removeEl) {
    return;
  }
  const placeholderEl = pickerEl.querySelector(".profile-photo-placeholder-v1");

  function setMenuOpen(open) {
    menuEl.hidden = !open;
    pickerEl.setAttribute("aria-expanded", open ? "true" : "false");
  }

  function showPreview(src) {
    previewEl.src = src;
    previewEl.hidden = false;
    if (placeholderEl) {
      placeholderEl.hidden = true;
    }
  }

  function clearPreview() {
    previewEl.removeAttribute("src");
    previewEl.hidden = true;
    if (placeholderEl) {
      placeholderEl.hidden = false;
    }
  }

  pickerEl.addEventListener("click", (event) => {
    event.stopPropagation();
    setMenuOpen(menuEl.hidden);
  });

  menuEl.addEventListener("click", (event) => {
    const action = event.target.closest("[data-logo-action]");
    if (!action || action.disabled) {
      return;
    }
    event.stopPropagation();
    setMenuOpen(false);
    if (action.dataset.logoAction === "select") {
      inputEl.click();
      return;
    }
    if (action.dataset.logoAction === "remove") {
      removeEl.value = "1";
      inputEl.value = "";
      clearPreview();
    }
  });

  inputEl.addEventListener("change", () => {
    const file = inputEl.files && inputEl.files[0];
    if (!file) {
      return;
    }
    removeEl.value = "";
    showPreview(URL.createObjectURL(file));
  });

  document.addEventListener("click", (event) => {
    if (!menuEl.hidden && !event.target.closest(`#${prefix}_logo_menu, #${prefix}_logo_picker`)) {
      setMenuOpen(false);
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      setMenuOpen(false);
    }
  });
}
bindEntityLogoPickerV1("empresa");
bindEntityLogoPickerV1("edit_entity");
if (userAvatarImageEl) {
  userAvatarImageEl.src = avatarDataUri;
}
if (dropdownAvatarImageEl) {
  dropdownAvatarImageEl.src = avatarDataUri;
}

if (
  appGenesisProcessMenuRuntimeV1 &&
  typeof appGenesisProcessMenuRuntimeV1.bindMenuButtonListeners === "function"
) {
  appGenesisProcessMenuRuntimeV1.bindMenuButtonListeners();
}

profileEditButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const cardId = button.getAttribute("data-edit-target");
    if (!cardId) {
      return;
    }
    closeAllProfileEdits();
    const card = document.getElementById(cardId);
    if (!card) {
      return;
    }
    card.classList.add("editing");
  });
});

if (dynamicProcessEditToggleEl) {
  dynamicProcessEditToggleEl.addEventListener("click", () => {
    // Esconde o botao enquanto o formulario esta aberto; restoreDynamicProcessEditToggleVisibility() reverte ao cancelar/fechar.
    setDynamicProcessEditToggleVisible(false);
    if (dynamicProcessHistoryActionInputEl) {
      dynamicProcessHistoryActionInputEl.value = "create";
    }
    if (dynamicProcessHistoryRecordIdInputEl) {
      dynamicProcessHistoryRecordIdInputEl.value = "";
    }
    if (dynamicProcessHistoryRecordStateInputEl) {
      dynamicProcessHistoryRecordStateInputEl.value = "";
    }
    if (dynamicProcessSubmitBtnEl) {
      dynamicProcessSubmitBtnEl.textContent = "Guardar";
    }
    if (dynamicProcessEditFormEl) {
      dynamicProcessEditFormEl.reset();
    }
    const currentMenuKey = normalizeMenuKey(dynamicProcessMenuKeyInputEl && dynamicProcessMenuKeyInputEl.value);
    const currentSetting = getSidebarMenuSetting(currentMenuKey);
    if (dynamicProcessTitleEl && currentSetting) {
      const layoutConfig = getDynamicProcessLayoutConfig(
        currentSetting,
        currentSetting.label || currentMenuKey,
        ""
      );
      if (layoutConfig.isListProcess) {
        dynamicProcessTitleEl.textContent = layoutConfig.createTitle;
      }
    }
  });
}

if (trainingOutrosEnabledEl) {
  trainingOutrosEnabledEl.addEventListener("change", () => {
    syncTrainingOutrosState();
  });
}

if (userMenuTriggerEl) {
  userMenuTriggerEl.addEventListener("click", (event) => {
    event.stopPropagation();
    toggleUserDropdown();
  });
}

userDropdownLinks.forEach((link) => {
  link.addEventListener("click", (event) => {
    event.preventDefault();
    const menuKey = normalizeMenuKey(link.getAttribute("data-dropdown-menu") || "perfil");
    const targetSelector = link.getAttribute("data-dropdown-target") || "";
    if (!menuConfig[menuKey]) {
      closeUserDropdown();
      return;
    }
    if (targetSelector) {
      selectedTargetByMenu[menuKey] = targetSelector;
    }
    activateMenuTarget(menuKey, targetSelector);
    closeUserDropdown();
  });
});

document.addEventListener("click", (event) => {
  if (!userMenuEl || !userDropdownEl || userDropdownEl.hidden) {
    return;
  }
  if (!userMenuEl.contains(event.target)) {
    closeUserDropdown();
  }
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    closeUserDropdown();
  }
});

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

// APPGENESIS_USER_CREATE_ACTION_MODE_V1_START
(function setupUserCreateActionModeV1() {
  "use strict";

  function syncUserCreateActionModeV1(root) {
    var scope = root || document;
    var card = scope.querySelector
      ? scope.querySelector("#create-user-card")
      : document.querySelector("#create-user-card");
    if (!card) {
      return;
    }
    var details = card.querySelector("#create-user-collapse");
    var isCreateOpen = Boolean(details && details.open);
    card
      .querySelectorAll("[data-appgenesis-hide-when-user-create-open='1']")
      .forEach(function (el) {
        el.hidden = isCreateOpen;
        el.setAttribute("aria-hidden", isCreateOpen ? "true" : "false");
      });
  }

  document.addEventListener("toggle", function (event) {
    if (
      event.target &&
      event.target.matches &&
      event.target.matches("#create-user-collapse")
    ) {
      syncUserCreateActionModeV1(document);
    }
  }, true);

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      syncUserCreateActionModeV1(document);
    });
  } else {
    syncUserCreateActionModeV1(document);
  }

  window.AppGenesisSyncUserCreateActionModeV1 = syncUserCreateActionModeV1;
})();
// APPGENESIS_USER_CREATE_ACTION_MODE_V1_END

function setupCreateUserGenerateLinkShortcut() {
  const shortcutButtonEl = document.getElementById("create-user-generate-link-shortcut-btn");
  if (!shortcutButtonEl) {
    return;
  }
  const linkSlotEl = document.querySelector(".entity-create-link-slot");

  if (linkSlotEl && !linkSlotEl.querySelector(".entity-create-link-output, .entity-create-link-message")) {
    linkSlotEl.style.display = "none";
  }

  function renderGenerateLinkContent(contentEl) {
    if (!linkSlotEl) {
      return;
    }
    linkSlotEl.innerHTML = "";
    linkSlotEl.appendChild(contentEl);
    linkSlotEl.style.display = "";
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

// APPGENESIS_UTILIZADOR_INVITE_LINK_HEADER_V1_START
// Reposiciona (nao clona) o botao "Gerar link de convite" e o seu slot de
// saida -- originalmente dentro de #create-user-card -- para dentro do
// cartao ativo de Utilizador (#admin-users-created-card). Necessario porque
// #create-user-card passou a ter data-admin-subprocess-inline-create-enabled
// e por isso fica display:none quando o formulario de criacao esta fechado
// (ver admin_subprocess_inline_create_v1.css), o que esconderia o botao e o
// link gerado independentemente do estado do formulario de criacao. O botao
// e marcado no template com data-admin-subprocess-inline-action="1" para ser
// recolocado no cabecalho pelo mecanismo generico ensureCardHeaderStructure
// (process_shell_runtime_v1.js) -- o mesmo que ja reposiciona o botao
// "+ Criar utilizador". Endpoint/logica de clique inalterados: apenas a
// posicao no DOM muda. Idempotente: seguro chamar mais de uma vez.
function relocateUtilizadorInviteLinkButtonV1() {
  const activeCard = document.getElementById("admin-users-created-card");
  const shortcutBtn = document.getElementById("create-user-generate-link-shortcut-btn");
  if (!activeCard || !shortcutBtn) {
    return;
  }
  if (shortcutBtn.parentElement !== activeCard) {
    activeCard.appendChild(shortcutBtn);
  }
  shortcutBtn.hidden = false;
}

function relocateUtilizadorInviteLinkSlotV1() {
  const activeCard = document.getElementById("admin-users-created-card");
  const linkSlotEl = document.querySelector(".entity-create-link-slot");
  if (!activeCard || !linkSlotEl) {
    return;
  }
  const headerEl = activeCard.querySelector(":scope > .appgenesis-card-header-v1");
  const desiredNextSibling = headerEl ? headerEl.nextSibling : activeCard.firstChild;
  if (linkSlotEl.parentElement !== activeCard || linkSlotEl.previousSibling !== headerEl) {
    activeCard.insertBefore(linkSlotEl, desiredNextSibling);
  }
  linkSlotEl.hidden = false;
}
// APPGENESIS_UTILIZADOR_INVITE_LINK_HEADER_V1_END

function setupSidebarSectionsEditor() {
  const sectionsBodyEl = document.getElementById("sidebar-sections-created-body");
  if (!sectionsBodyEl) {
    return;
  }

  const refreshActionStates = () => {
    const rows = Array.from(sectionsBodyEl.querySelectorAll("[data-sidebar-section-row]"));
    rows.forEach((rowEl, index) => {
      const upBtn = rowEl.querySelector("[data-sidebar-section-action='up']");
      const downBtn = rowEl.querySelector("[data-sidebar-section-action='down']");
      const removeBtn = rowEl.querySelector("[data-sidebar-section-action='remove']");
      const sectionKey = String(rowEl.getAttribute("data-sidebar-section-key") || "").trim().toLowerCase();
      const isProtected = sectionKey === "geral" || sectionKey === "igreja";

      if (upBtn) {
        upBtn.disabled = index === 0;
        upBtn.classList.toggle("table-icon-btn-disabled", upBtn.disabled);
      }
      if (downBtn) {
        downBtn.disabled = index === rows.length - 1;
        downBtn.classList.toggle("table-icon-btn-disabled", downBtn.disabled);
      }
      if (removeBtn) {
        removeBtn.disabled = rows.length <= 1 || isProtected;
        removeBtn.classList.toggle("table-icon-btn-disabled", removeBtn.disabled);
      }
    });
  };

  sectionsBodyEl.addEventListener("click", (event) => {
    const actionBtn = event.target.closest("[data-sidebar-section-action]");
    if (!actionBtn) {
      return;
    }
    const actionType = String(actionBtn.getAttribute("data-sidebar-section-action") || "").trim().toLowerCase();
    const rowEl = actionBtn.closest("[data-sidebar-section-row]");
    if (!rowEl || actionBtn.disabled) {
      return;
    }

    if (actionType === "up") {
      const previousRow = rowEl.previousElementSibling;
      if (previousRow) {
        sectionsBodyEl.insertBefore(rowEl, previousRow);
      }
      refreshActionStates();
      return;
    }

    if (actionType === "down") {
      const nextRow = rowEl.nextElementSibling;
      if (nextRow) {
        sectionsBodyEl.insertBefore(nextRow, rowEl);
      }
      refreshActionStates();
      return;
    }

    if (actionType === "remove") {
      rowEl.remove();
      refreshActionStates();
    }
  });

  refreshActionStates();
}
