from __future__ import annotations

import re
from pathlib import Path


def read_text_v8(path: str) -> str:
    return Path(path).read_text(encoding="utf-8-sig")


def write_text_v8(path: str, content: str) -> None:
    Path(path).write_text(content.rstrip() + "\n", encoding="utf-8")


def require_v8(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def patch_template_cache_v8() -> None:
    path = "templates/new_user.html"
    content = read_text_v8(path)

    content = re.sub(
        r'/static/js/new_user\.js\?v=[^"]+',
        '/static/js/new_user.js?v=20260504-users-inactive-visible-v8',
        content,
        count=1,
    )

    content = re.sub(
        r'/static/css/new_user\.css\?v=[^"]+',
        '/static/css/new_user.css?v=20260504-users-active-inactive-card-v7',
        content,
        count=1,
    )

    require_v8(
        "new_user.js?v=20260504-users-inactive-visible-v8" in content,
        "ERRO: versão do JS não foi atualizada no template.",
    )

    require_v8(
        "APPVERBO_ADMIN_USERS_ACTIVE_SECTION_V7_START" in content,
        "ERRO: bloco de utilizadores ativos V7 não encontrado no template.",
    )

    require_v8(
        "APPVERBO_ADMIN_USERS_INACTIVE_SECTION_V7_START" in content,
        "ERRO: bloco de utilizadores inativos V7 não encontrado no template.",
    )

    require_v8(
        '<section id="inactive-users-card" class="card"' in content,
        "ERRO: card separado inactive-users-card não encontrado no template.",
    )

    require_v8(
        "SuperUsers de Entidade" not in content,
        "ERRO: bloco SuperUsers de Entidade ainda existe no template.",
    )

    require_v8(
        "entity-status-inactive{% else %}" not in content,
        "ERRO: ainda existe Jinja quebrado no template.",
    )

    write_text_v8(path, content)


def patch_new_user_js_v8() -> None:
    path = "static/js/new_user.js"
    content = read_text_v8(path)

    content = re.sub(
        r'\n?// APPVERBO_ADMIN_INACTIVE_USERS_VISIBILITY_V8_START[\s\S]*?// APPVERBO_ADMIN_INACTIVE_USERS_VISIBILITY_V8_END\n?',
        "\n",
        content,
        flags=re.S,
    )

    block = r'''
// APPVERBO_ADMIN_INACTIVE_USERS_VISIBILITY_V8_START
//###################################################################################
// (ADMIN_INACTIVE_USERS_VISIBILITY_V8) MANTER CARD DE UTILIZADORES INATIVOS VISÍVEL
//###################################################################################

function appverboNormalizeAdminInactiveUsersText_v8(value) {
  return String(value || "")
    .trim()
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}

function appverboIsAdminUserTabActive_v8() {
  const bootstrapData = window.__APPVERBO_BOOTSTRAP__ || {};
  const currentUrl = new URL(window.location.href);

  const menuFromUrl = appverboNormalizeAdminInactiveUsersText_v8(
    currentUrl.searchParams.get("menu") || bootstrapData.initialMenu || ""
  );

  if (menuFromUrl !== "administrativo") {
    return false;
  }

  const adminTabFromUrl = appverboNormalizeAdminInactiveUsersText_v8(
    currentUrl.searchParams.get("admin_tab") || bootstrapData.initialAdminTab || "utilizador"
  );

  if (["entidade", "menu", "sessoes", "sessões", "contas"].includes(adminTabFromUrl)) {
    return false;
  }

  const activeTabButton = document.querySelector(
    "#submenu-items .active, #submenu-items [aria-selected='true'], #submenu-items button.active"
  );

  if (activeTabButton) {
    const activeTabText = appverboNormalizeAdminInactiveUsersText_v8(activeTabButton.textContent || "");
    if (activeTabText && activeTabText !== "utilizador") {
      return false;
    }
  }

  return true;
}

function appverboShowInactiveUsersCard_v8() {
  const inactiveUsersCard = document.getElementById("inactive-users-card");
  const activeUsersCard = document.getElementById("admin-users-created-card");

  if (!inactiveUsersCard || !activeUsersCard) {
    return;
  }

  if (!appverboIsAdminUserTabActive_v8()) {
    return;
  }

  inactiveUsersCard.hidden = false;
  inactiveUsersCard.removeAttribute("hidden");
  inactiveUsersCard.style.removeProperty("display");

  activeUsersCard.hidden = false;
  activeUsersCard.removeAttribute("hidden");
  activeUsersCard.style.removeProperty("display");
}

function appverboInstallInactiveUsersVisibilityGuard_v8() {
  appverboShowInactiveUsersCard_v8();

  window.setTimeout(appverboShowInactiveUsersCard_v8, 0);
  window.setTimeout(appverboShowInactiveUsersCard_v8, 100);
  window.setTimeout(appverboShowInactiveUsersCard_v8, 300);

  document.addEventListener("click", function appverboInactiveUsersClickGuard_v8() {
    window.setTimeout(appverboShowInactiveUsersCard_v8, 0);
    window.setTimeout(appverboShowInactiveUsersCard_v8, 100);
  });

  const inactiveUsersCard = document.getElementById("inactive-users-card");

  if (inactiveUsersCard && typeof MutationObserver !== "undefined") {
    const observer = new MutationObserver(function appverboInactiveUsersObserver_v8() {
      if (appverboIsAdminUserTabActive_v8()) {
        window.setTimeout(appverboShowInactiveUsersCard_v8, 0);
      }
    });

    observer.observe(inactiveUsersCard, {
      attributes: true,
      attributeFilter: ["style", "class", "hidden"]
    });
  }
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", appverboInstallInactiveUsersVisibilityGuard_v8);
} else {
  appverboInstallInactiveUsersVisibilityGuard_v8();
}

window.addEventListener("load", appverboShowInactiveUsersCard_v8);
// APPVERBO_ADMIN_INACTIVE_USERS_VISIBILITY_V8_END
'''

    content = content.rstrip() + "\n\n" + block.strip() + "\n"

    require_v8(
        "appverboShowInactiveUsersCard_v8" in content,
        "ERRO: função de visibilidade V8 não foi inserida no JS.",
    )

    require_v8(
        "APPVERBO_ADMIN_INACTIVE_USERS_VISIBILITY_V8_START" in content,
        "ERRO: marcador START V8 não foi inserido no JS.",
    )

    write_text_v8(path, content)


def validate_v8() -> None:
    template = read_text_v8("templates/new_user.html")
    js = read_text_v8("static/js/new_user.js")
    page_service = read_text_v8("appverbo/services/page.py")
    delete_handler = read_text_v8("appverbo/routes/users/delete_handler.py")

    checks = {
        "template js cache v8": "new_user.js?v=20260504-users-inactive-visible-v8" in template,
        "template ativo V7": "APPVERBO_ADMIN_USERS_ACTIVE_SECTION_V7_START" in template,
        "template inativo V7": "APPVERBO_ADMIN_USERS_INACTIVE_SECTION_V7_START" in template,
        "template inactive card": '<section id="inactive-users-card" class="card"' in template,
        "template sem SuperUsers": "SuperUsers de Entidade" not in template,
        "template sem Jinja quebrado": "entity-status-inactive{% else %}" not in template,
        "js guard V8": "APPVERBO_ADMIN_INACTIVE_USERS_VISIBILITY_V8_START" in js,
        "js função show V8": "appverboShowInactiveUsersCard_v8" in js,
        "js função tab V8": "appverboIsAdminUserTabActive_v8" in js,
        "page inactive_users": "inactive_users = [" in page_service,
        "page context inactive_users": '"inactive_users": inactive_users,' in page_service,
        "backend delete inactive only": "Só é permitido eliminar utilizadores inativos." in delete_handler,
    }

    failed = [name for name, ok in checks.items() if not ok]
    require_v8(not failed, "Falha na validação: " + ", ".join(failed))


def main_v8() -> None:
    patch_template_cache_v8()
    patch_new_user_js_v8()
    validate_v8()


if __name__ == "__main__":
    main_v8()
