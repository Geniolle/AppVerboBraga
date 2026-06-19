from __future__ import annotations

import re
import shutil
from pathlib import Path


ROOT = Path.cwd()
BACKUP_ROOT = ROOT / "backups" / ("refatorar_utilizador_js_navegacao_v1_" + "20260513_091347")


####################################################################################
# (1) HELPERS DE FICHEIRO
####################################################################################

def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def backup_file(path: Path) -> None:
    if not path.exists():
        return

    backup_path = BACKUP_ROOT / path.relative_to(ROOT)
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, backup_path)
    print(f"Backup criado: {rel(backup_path)}")


def write_changed(path: Path, content: str) -> bool:
    old = read_text(path) if path.exists() else None

    if old == content:
        print(f"Sem alteração: {rel(path)}")
        return False

    backup_file(path)
    write_text(path, content)
    print(f"Atualizado: {rel(path)}")
    return True


####################################################################################
# (2) CONTEÚDO DO NOVO MÓDULO DE NAVEGAÇÃO
####################################################################################

NAVIGATION_JS = r'''/* APPVERBO_ADMIN_USER_ACTION_NAVIGATION_V1
 * Responsabilidade única:
 * - navegar para Exibir/Editar/Fechar do subprocesso Utilizador;
 * - não renderiza tabela;
 * - não filtra tabela;
 * - não pagina tabela;
 * - não altera layout visual.
 */
(function () {
  "use strict";

  //###################################################################################
  // (1) CONSTANTES DO SUBPROCESSO UTILIZADOR
  //###################################################################################

  const MODULE_NAME_V1 = "APPVERBO_ADMIN_USER_ACTION_NAVIGATION_V1";
  const USER_PATH_V1 = "/users/new";
  const USER_TAB_V1 = "utilizador";
  const USER_TARGET_V1 = "edit-user-card";

  //###################################################################################
  // (2) HELPERS DE URL
  //###################################################################################

  function normalizarUrlAcaoUtilizador_v1(rawHref) {
    if (!rawHref) {
      return null;
    }

    try {
      return new URL(String(rawHref), window.location.origin);
    } catch (error) {
      return null;
    }
  }

  function isUrlAcaoUtilizador_v1(url) {
    if (!url) {
      return false;
    }

    if (url.pathname !== USER_PATH_V1) {
      return false;
    }

    if (url.searchParams.get("menu") !== "administrativo") {
      return false;
    }

    if (url.searchParams.get("admin_tab") !== USER_TAB_V1) {
      return false;
    }

    const hasViewOrEdit = Boolean(url.searchParams.get("user_edit_id"));
    const isClose = !url.searchParams.has("user_edit_id") && !url.searchParams.has("user_view");

    return hasViewOrEdit || isClose;
  }

  function normalizarDestinoUtilizador_v1(url) {
    if (!url) {
      return "";
    }

    if (url.searchParams.get("user_edit_id")) {
      url.searchParams.set("target", USER_TARGET_V1);

      if (!url.hash) {
        url.hash = USER_TARGET_V1;
      }
    }

    return url.pathname + url.search + url.hash;
  }

  //###################################################################################
  // (3) DETEÇÃO DO ELEMENTO CLICADO
  //###################################################################################

  function localizarLinkAcaoUtilizador_v1(eventTarget) {
    if (!eventTarget || !document.documentElement.contains(eventTarget)) {
      return null;
    }

    const element = eventTarget.nodeType === 1 ? eventTarget : eventTarget.parentElement;

    if (!element) {
      return null;
    }

    return element.closest(
      "a[href], button[data-href], [data-user-action-url], [data-admin-user-action-url]"
    );
  }

  function extrairHrefAcaoUtilizador_v1(actionElement) {
    if (!actionElement) {
      return "";
    }

    const dataUserActionUrl = actionElement.getAttribute("data-user-action-url") || "";
    if (dataUserActionUrl.trim()) {
      return dataUserActionUrl.trim();
    }

    const dataAdminUserActionUrl = actionElement.getAttribute("data-admin-user-action-url") || "";
    if (dataAdminUserActionUrl.trim()) {
      return dataAdminUserActionUrl.trim();
    }

    const dataHref = actionElement.getAttribute("data-href") || "";
    if (dataHref.trim()) {
      return dataHref.trim();
    }

    const href = actionElement.getAttribute("href") || "";
    return href.trim();
  }

  //###################################################################################
  // (4) NAVEGAÇÃO CONTROLADA
  //###################################################################################

  function navegarParaAcaoUtilizador_v1(event) {
    if (!event || event.defaultPrevented) {
      return;
    }

    if (event.button !== undefined && event.button !== 0) {
      return;
    }

    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) {
      return;
    }

    const actionElement = localizarLinkAcaoUtilizador_v1(event.target);

    if (!actionElement) {
      return;
    }

    const href = extrairHrefAcaoUtilizador_v1(actionElement);
    const url = normalizarUrlAcaoUtilizador_v1(href);

    if (!isUrlAcaoUtilizador_v1(url)) {
      return;
    }

    const destino = normalizarDestinoUtilizador_v1(url);

    if (!destino) {
      return;
    }

    event.preventDefault();
    event.stopPropagation();

    window.location.assign(destino);
  }

  //###################################################################################
  // (5) INICIALIZAÇÃO
  //###################################################################################

  function inicializarNavegacaoAcoesUtilizador_v1() {
    if (window.__APPVERBO_ADMIN_USER_ACTION_NAVIGATION_V1_BOUND__) {
      return;
    }

    window.__APPVERBO_ADMIN_USER_ACTION_NAVIGATION_V1_BOUND__ = true;
    document.addEventListener("click", navegarParaAcaoUtilizador_v1, true);
  }

  inicializarNavegacaoAcoesUtilizador_v1();

  window.APPVERBO_ADMIN_USER_ACTION_NAVIGATION_V1 = {
    moduleName: MODULE_NAME_V1,
    isUrlAcaoUtilizador_v1,
    normalizarDestinoUtilizador_v1,
  };
})();
'''


CONTRACT_PY = r'''from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


####################################################################################
# (1) HELPERS
####################################################################################

def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


####################################################################################
# (2) CONTRATO DO JAVASCRIPT DO SUBPROCESSO UTILIZADOR
####################################################################################

def main() -> None:
    table_js = read("static/js/modules/admin_user_shadow_table_v1.js")
    navigation_js = read("static/js/modules/admin_user_action_navigation_v1.js")
    partial = read("templates/partials/admin_user_shadow_readonly_v1.html")

    assert_true(
        "APPVERBO_ADMIN_USER_ACTION_NAVIGATION_V1" in navigation_js,
        "Módulo de navegação do Utilizador deve identificar APPVERBO_ADMIN_USER_ACTION_NAVIGATION_V1.",
    )

    assert_true(
        "navegarParaAcaoUtilizador_v1" in navigation_js,
        "Módulo de navegação deve conter navegarParaAcaoUtilizador_v1.",
    )

    assert_true(
        "document.addEventListener(\"click\", navegarParaAcaoUtilizador_v1, true)" in navigation_js,
        "Módulo de navegação deve ligar clique em capture phase.",
    )

    forbidden_table_patterns = (
        "APPVERBO_UTILIZADOR_ACTION_ICON_CLICK",
        "APPVERBO_UTILIZADOR_ACTION_CLICK_BRIDGE",
        "navigatetoUserAction",
        "navigateToUserAction",
        "navegarParaAcaoUtilizador",
        "window.location.assign(href)",
        "window.location.href = href",
    )

    for pattern in forbidden_table_patterns:
        assert_true(
            pattern not in table_js,
            f"admin_user_shadow_table_v1.js não deve conter lógica de navegação: {pattern}",
        )

    assert_true(
        "admin_user_shadow_table_v1.js" in partial,
        "Partial deve carregar módulo de tabela do Utilizador.",
    )

    assert_true(
        "admin_user_action_navigation_v1.js" in partial,
        "Partial deve carregar módulo isolado de navegação do Utilizador.",
    )

    table_script_index = partial.find("admin_user_shadow_table_v1.js")
    navigation_script_index = partial.find("admin_user_action_navigation_v1.js")

    assert_true(
        table_script_index >= 0 and navigation_script_index >= 0,
        "Scripts de tabela e navegação devem existir no partial.",
    )

    assert_true(
        table_script_index < navigation_script_index,
        "Módulo de tabela deve carregar antes do módulo de navegação.",
    )

    assert_true(
        re.search(r'row\.get\(["\']view_url["\']\)', partial) is not None,
        "Partial deve usar view_url vindo do repository.",
    )

    assert_true(
        re.search(r'row\.get\(["\']edit_url["\']\)', partial) is not None,
        "Partial deve usar edit_url vindo do repository.",
    )

    print("OK: contrato JS do subprocesso Utilizador validado com sucesso.")


if __name__ == "__main__":
    main()
'''


####################################################################################
# (3) PATCH DO MÓDULO DE TABELA
####################################################################################

def remover_blocos_navegacao_do_modulo_tabela() -> None:
    path = ROOT / "static/js/modules/admin_user_shadow_table_v1.js"

    if not path.exists():
        raise RuntimeError("Módulo de tabela do Utilizador não encontrado.")

    text = read_text(path)
    original = text

    marker_patterns = (
        r"\n?\s*//\s*APPVERBO_UTILIZADOR_ACTION_ICON_CLICK_V\d+_START.*?//\s*APPVERBO_UTILIZADOR_ACTION_ICON_CLICK_V\d+_END\s*\n?",
        r"\n?\s*//\s*APPVERBO_UTILIZADOR_ACTION_CLICK_BRIDGE_V\d+_START.*?//\s*APPVERBO_UTILIZADOR_ACTION_CLICK_BRIDGE_V\d+_END\s*\n?",
        r"\n?\s*//\s*APPVERBO_UTILIZADOR_ACTION_NAVIGATION_V\d+_START.*?//\s*APPVERBO_UTILIZADOR_ACTION_NAVIGATION_V\d+_END\s*\n?",
        r"\n?\s*/\*\s*APPVERBO_UTILIZADOR_ACTION_ICON_CLICK_V\d+_START\s*\*/.*?/\*\s*APPVERBO_UTILIZADOR_ACTION_ICON_CLICK_V\d+_END\s*\*/\s*\n?",
        r"\n?\s*/\*\s*APPVERBO_UTILIZADOR_ACTION_CLICK_BRIDGE_V\d+_START\s*\*/.*?/\*\s*APPVERBO_UTILIZADOR_ACTION_CLICK_BRIDGE_V\d+_END\s*\*/\s*\n?",
    )

    for pattern in marker_patterns:
        text = re.sub(pattern, "\n", text, flags=re.DOTALL | re.IGNORECASE)

    fallback_patterns = (
        r"\n?\s*function\s+navigateToUserAction_v\d+\s*\([^)]*\)\s*\{.*?\}\s*document\.addEventListener\(\s*[\"']click[\"']\s*,\s*navigateToUserAction_v\d+\s*,\s*true\s*\)\s*;?\s*\n?",
        r"\n?\s*function\s+navegarParaAcaoUtilizador_v\d+\s*\([^)]*\)\s*\{.*?\}\s*document\.addEventListener\(\s*[\"']click[\"']\s*,\s*navegarParaAcaoUtilizador_v\d+\s*,\s*true\s*\)\s*;?\s*\n?",
    )

    for pattern in fallback_patterns:
        text = re.sub(pattern, "\n", text, flags=re.DOTALL)

    text = re.sub(r"\n{4,}", "\n\n\n", text).strip() + "\n"

    if text != original:
        write_changed(path, text)
    else:
        print(f"Sem blocos de navegação antigos para remover: {rel(path)}")


####################################################################################
# (4) CRIAR MÓDULO ISOLADO DE NAVEGAÇÃO
####################################################################################

def criar_modulo_navegacao() -> None:
    path = ROOT / "static/js/modules/admin_user_action_navigation_v1.js"
    write_changed(path, NAVIGATION_JS)


####################################################################################
# (5) ATUALIZAR PARTIAL PARA CARREGAR OS DOIS MÓDULOS
####################################################################################

def atualizar_partial_scripts() -> None:
    path = ROOT / "templates/partials/admin_user_shadow_readonly_v1.html"

    if not path.exists():
        raise RuntimeError("Partial do Utilizador não encontrado.")

    text = read_text(path)

    script_table = '<script src="/static/js/modules/admin_user_shadow_table_v1.js?v=20260513-utilizador-shadow-table-only-v18" defer></script>'
    script_nav = '<script src="/static/js/modules/admin_user_action_navigation_v1.js?v=20260513-utilizador-action-navigation-v1" defer></script>'
    script_block = script_table + "\n" + script_nav

    text = re.sub(
        r'\s*<script[^>]+src="/static/js/modules/admin_user_shadow_table_v1\.js\?v=[^"]+"[^>]*>\s*</script>',
        "\n" + script_block,
        text,
        count=1,
    )

    if "admin_user_shadow_table_v1.js" not in text:
        if "</div>" in text:
            text = text.rstrip() + "\n" + script_block + "\n"
        else:
            text = text.rstrip() + "\n" + script_block + "\n"

    if "admin_user_action_navigation_v1.js" not in text:
        table_script_pattern = re.compile(
            r'(<script[^>]+src="/static/js/modules/admin_user_shadow_table_v1\.js\?v=[^"]+"[^>]*>\s*</script>)'
        )
        text = table_script_pattern.sub(r"\1\n" + script_nav, text, count=1)

    text = re.sub(
        r'(<script[^>]+src="/static/js/modules/admin_user_action_navigation_v1\.js\?v=[^"]+"[^>]*>\s*</script>)(\s*\1)+',
        r"\1",
        text,
    )

    write_changed(path, text)


####################################################################################
# (6) CRIAR CONTRATO JS
####################################################################################

def criar_contrato_js() -> None:
    path = ROOT / "scripts/check_utilizador_js_contract_v1.py"
    write_changed(path, CONTRACT_PY)


####################################################################################
# (7) EXECUÇÃO
####################################################################################

def main() -> None:
    remover_blocos_navegacao_do_modulo_tabela()
    criar_modulo_navegacao()
    atualizar_partial_scripts()
    criar_contrato_js()


if __name__ == "__main__":
    main()
