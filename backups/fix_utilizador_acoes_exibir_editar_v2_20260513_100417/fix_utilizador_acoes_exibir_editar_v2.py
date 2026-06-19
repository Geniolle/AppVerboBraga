from __future__ import annotations

import re
import sys
import py_compile
from pathlib import Path


ROOT = Path.cwd()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text_if_changed(path: Path, content: str) -> bool:
    old = path.read_text(encoding="utf-8") if path.exists() else ""
    if old == content:
        print(f"Sem alteração: {path}")
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")
    print(f"Atualizado: {path}")
    return True


def require_file(path: Path) -> None:
    if not path.exists():
        raise RuntimeError(f"ERRO: ficheiro obrigatório não encontrado: {path}")


def remove_old_navigation_blocks(js_text: str) -> str:
    patterns = [
        r"\n?// APPVERBO_UTILIZADOR_ACTION_ICON_CLICK_V\d+_START[\s\S]*?// APPVERBO_UTILIZADOR_ACTION_ICON_CLICK_V\d+_END\n?",
        r"\n?// APPVERBO_UTILIZADOR_ACTION_CLICK_BRIDGE_V\d+_START[\s\S]*?// APPVERBO_UTILIZADOR_ACTION_CLICK_BRIDGE_V\d+_END\n?",
        r"\n?// APPVERBO_ADMIN_USER_ACTION_NAVIGATION_INLINE_V\d+_START[\s\S]*?// APPVERBO_ADMIN_USER_ACTION_NAVIGATION_INLINE_V\d+_END\n?",
    ]

    updated = js_text
    for pattern in patterns:
        updated = re.sub(pattern, "\n", updated, flags=re.MULTILINE)

    updated = re.sub(r"\n{3,}", "\n\n", updated)
    return updated


def build_navigation_js() -> str:
    return r'''/* APPVERBO_ADMIN_USER_ACTION_NAVIGATION_V2
 * Responsabilidade única:
 * - garantir que os ícones Exibir/Editar do subprocesso Utilizador navegam para a URL canónica;
 * - executar antes de outros handlers que possam bloquear o clique;
 * - não montar regra de negócio: apenas normaliza e navega.
 */
(function () {
  "use strict";

  const MODULE_NAME_V2 = "APPVERBO_ADMIN_USER_ACTION_NAVIGATION_V2";
  const BOUND_FLAG_V2 = "__APPVERBO_ADMIN_USER_ACTION_NAVIGATION_V2_BOUND__";
  const ACTION_SELECTOR_V2 = [
    'a[data-admin-user-action-link="1"]',
    'a[href*="admin_tab=utilizador"][href*="user_edit_id="]',
    'button[data-admin-user-action-link="1"]'
  ].join(",");

  function isModifiedClick_v2(event) {
    return Boolean(event.metaKey || event.ctrlKey || event.shiftKey || event.altKey);
  }

  function hasUsableTarget_v2(event) {
    if (!event) {
      return false;
    }

    if (event.type === "click" && typeof event.button === "number" && event.button !== 0) {
      return false;
    }

    return true;
  }

  function asAbsoluteUrl_v2(rawHref) {
    const cleanHref = String(rawHref || "").trim();

    if (!cleanHref || cleanHref === "#" || cleanHref.toLowerCase().startsWith("javascript:")) {
      return null;
    }

    try {
      return new URL(cleanHref, window.location.origin);
    }
    catch (_error) {
      return null;
    }
  }

  function isUtilizadorActionUrl_v2(url) {
    if (!url) {
      return false;
    }

    if (url.origin !== window.location.origin) {
      return false;
    }

    if (url.pathname !== "/users/new") {
      return false;
    }

    if (url.searchParams.get("admin_tab") !== "utilizador") {
      return false;
    }

    const userEditId = String(url.searchParams.get("user_edit_id") || "").trim();

    return /^\d+$/.test(userEditId);
  }

  function resolveActionMode_v2(actionElement, url) {
    const dataAction = String(actionElement.getAttribute("data-admin-user-action") || "").trim().toLowerCase();

    if (dataAction === "view" || dataAction === "exibir") {
      return "1";
    }

    if (dataAction === "edit" || dataAction === "editar" || dataAction === "modificar") {
      return "0";
    }

    const currentMode = String(url.searchParams.get("user_view") || "").trim();

    if (currentMode === "1") {
      return "1";
    }

    return "0";
  }

  function normalizarDestinoUtilizador_v2(rawHref, actionElement) {
    const url = asAbsoluteUrl_v2(rawHref);

    if (!isUtilizadorActionUrl_v2(url)) {
      return "";
    }

    url.searchParams.set("menu", "administrativo");
    url.searchParams.set("admin_tab", "utilizador");
    url.searchParams.set("user_view", resolveActionMode_v2(actionElement, url));
    url.searchParams.set("target", "edit-user-card");
    url.hash = "#edit-user-card";

    return url.pathname + url.search + url.hash;
  }

  function localizarAcaoUtilizador_v2(eventTarget) {
    if (!eventTarget || typeof eventTarget.closest !== "function") {
      return null;
    }

    return eventTarget.closest(ACTION_SELECTOR_V2);
  }

  function extractHref_v2(actionElement) {
    if (!actionElement) {
      return "";
    }

    return (
      actionElement.getAttribute("href") ||
      actionElement.getAttribute("data-href") ||
      actionElement.getAttribute("data-url") ||
      ""
    );
  }

  function bloquearOutrosHandlers_v2(event) {
    event.preventDefault();
    event.stopPropagation();

    if (typeof event.stopImmediatePropagation === "function") {
      event.stopImmediatePropagation();
    }
  }

  function navegarParaAcaoUtilizador_v2(event) {
    if (!hasUsableTarget_v2(event)) {
      return;
    }

    if (isModifiedClick_v2(event)) {
      return;
    }

    const actionElement = localizarAcaoUtilizador_v2(event.target);

    if (!actionElement) {
      return;
    }

    const destino = normalizarDestinoUtilizador_v2(extractHref_v2(actionElement), actionElement);

    if (!destino) {
      return;
    }

    bloquearOutrosHandlers_v2(event);
    window.location.assign(destino);
  }

  function navegarPorTeclado_v2(event) {
    const key = String(event.key || "");

    if (key !== "Enter" && key !== " ") {
      return;
    }

    const actionElement = localizarAcaoUtilizador_v2(event.target);

    if (!actionElement) {
      return;
    }

    const destino = normalizarDestinoUtilizador_v2(extractHref_v2(actionElement), actionElement);

    if (!destino) {
      return;
    }

    bloquearOutrosHandlers_v2(event);
    window.location.assign(destino);
  }

  function inicializarNavegacaoAcoesUtilizador_v2() {
    if (window[BOUND_FLAG_V2]) {
      return;
    }

    window[BOUND_FLAG_V2] = true;

    document.addEventListener("click", navegarParaAcaoUtilizador_v2, true);
    document.addEventListener("keydown", navegarPorTeclado_v2, true);
  }

  inicializarNavegacaoAcoesUtilizador_v2();

  window.APPVERBO_ADMIN_USER_ACTION_NAVIGATION_V2 = {
    moduleName: MODULE_NAME_V2,
    normalizarDestinoUtilizador_v2,
    inicializarNavegacaoAcoesUtilizador_v2
  };
})();
'''


def build_urls_py() -> str:
    return '''from __future__ import annotations

from typing import Any


USER_ADMIN_BASE_URL_V1 = "/users/new"
USER_ADMIN_MENU_V1 = "administrativo"
USER_ADMIN_TAB_V1 = "utilizador"
USER_EDIT_TARGET_V1 = "edit-user-card"


def _normalizar_user_id_v1(user_id: Any) -> str:
    clean_user_id = str(user_id or "").strip()

    if not clean_user_id.isdigit():
        return ""

    return clean_user_id


def montar_url_exibir_utilizador_v1(user_id: Any) -> str:
    clean_user_id = _normalizar_user_id_v1(user_id)

    if not clean_user_id:
        return ""

    return (
        f"{USER_ADMIN_BASE_URL_V1}"
        f"?menu={USER_ADMIN_MENU_V1}"
        f"&admin_tab={USER_ADMIN_TAB_V1}"
        f"&user_edit_id={clean_user_id}"
        f"&user_view=1"
        f"&target={USER_EDIT_TARGET_V1}"
        f"#{USER_EDIT_TARGET_V1}"
    )


def montar_url_editar_utilizador_v1(user_id: Any) -> str:
    clean_user_id = _normalizar_user_id_v1(user_id)

    if not clean_user_id:
        return ""

    return (
        f"{USER_ADMIN_BASE_URL_V1}"
        f"?menu={USER_ADMIN_MENU_V1}"
        f"&admin_tab={USER_ADMIN_TAB_V1}"
        f"&user_edit_id={clean_user_id}"
        f"&user_view=0"
        f"&target={USER_EDIT_TARGET_V1}"
        f"#{USER_EDIT_TARGET_V1}"
    )


def montar_url_fechar_utilizador_v1() -> str:
    return f"{USER_ADMIN_BASE_URL_V1}?menu={USER_ADMIN_MENU_V1}&admin_tab={USER_ADMIN_TAB_V1}"


__all__ = (
    "USER_ADMIN_BASE_URL_V1",
    "USER_ADMIN_MENU_V1",
    "USER_ADMIN_TAB_V1",
    "USER_EDIT_TARGET_V1",
    "montar_url_exibir_utilizador_v1",
    "montar_url_editar_utilizador_v1",
    "montar_url_fechar_utilizador_v1",
)
'''


def patch_shadow_partial(path: Path) -> None:
    if not path.exists():
        print(f"AVISO: partial shadow não encontrado: {path}")
        return

    text = read_text(path)

    macro_match = re.search(
        r"{%\s*macro\s+(render_admin_user_shadow_actions_v\d+)\(row\)\s*%}[\s\S]*?{%\s*endmacro\s*%}",
        text,
    )

    if not macro_match:
        raise RuntimeError(f"ERRO: macro render_admin_user_shadow_actions_vN não encontrada em {path}")

    macro_name = macro_match.group(1)

    new_macro = f'''{{% macro {macro_name}(row) %}}
  {{% set user_id = row.get('id', '') %}}
  {{% set view_url = row.get("view_url") or "/users/new?menu=administrativo&admin_tab=utilizador&user_edit_id=" ~ user_id ~ "&user_view=1&target=edit-user-card#edit-user-card" %}}
  {{% set edit_url = row.get("edit_url") or "/users/new?menu=administrativo&admin_tab=utilizador&user_edit_id=" ~ user_id ~ "&user_view=0&target=edit-user-card#edit-user-card" %}}
  {{% set close_url = row.get("close_url") or "/users/new?menu=administrativo&admin_tab=utilizador" %}}
  <div class="table-actions" data-admin-user-actions="1">
    <a
      class="table-icon-btn admin-user-action-link-v2"
      href="{{{{ view_url }}}}"
      data-admin-user-action-link="1"
      data-admin-user-action="view"
      data-user-id="{{{{ user_id }}}}"
      title="Exibir utilizador"
      aria-label="Exibir utilizador"
    >
      &#128065;
    </a>
    <a
      class="table-icon-btn admin-user-action-link-v2"
      href="{{{{ edit_url }}}}"
      data-admin-user-action-link="1"
      data-admin-user-action="edit"
      data-user-id="{{{{ user_id }}}}"
      title="Modificar utilizador"
      aria-label="Modificar utilizador"
    >
      &#9998;
    </a>
    <a
      class="table-icon-btn"
      href="{{{{ close_url }}}}"
      title="Fechar seleção do utilizador"
      aria-label="Fechar seleção do utilizador"
    >
      &#10005;
    </a>
  </div>
{{% endmacro %}}'''

    text = text[: macro_match.start()] + new_macro + text[macro_match.end() :]

    text = re.sub(
        r'\s*<script\s+src="/static/js/modules/admin_user_action_navigation_v1\.js[^"]*"\s+defer>\s*</script>',
        "",
        text,
    )

    text = re.sub(
        r'admin_user_shadow_table_v1\.js\?v=[^"]+',
        'admin_user_shadow_table_v1.js?v=20260513-utilizador-shadow-table-only-v19',
        text,
    )

    write_text_if_changed(path, text)


def patch_legacy_partial(path: Path) -> None:
    if not path.exists():
        print(f"AVISO: partial legado não encontrado: {path}")
        return

    text = read_text(path)

    text = re.sub(
        r'href="/users/new\?menu=administrativo&admin_tab=utilizador&user_edit_id=\{\{\s*row\.id\s*\}\}&user_view=1(?:&target=edit-user-card)?#edit-user-card"',
        'href="/users/new?menu=administrativo&admin_tab=utilizador&user_edit_id={{ row.id }}&user_view=1&target=edit-user-card#edit-user-card"',
        text,
    )

    text = re.sub(
        r'href="/users/new\?menu=administrativo&admin_tab=utilizador&user_edit_id=\{\{\s*row\.id\s*\}\}(?:&user_view=0)?(?:&target=edit-user-card)?#edit-user-card"',
        'href="/users/new?menu=administrativo&admin_tab=utilizador&user_edit_id={{ row.id }}&user_view=0&target=edit-user-card#edit-user-card"',
        text,
    )

    text = re.sub(
        r'(<a\s+class="table-icon-btn"\s+href="/users/new\?menu=administrativo&admin_tab=utilizador&user_edit_id=\{\{\s*row\.id\s*\}\}&user_view=1&target=edit-user-card#edit-user-card"\s+)(title="Exibir utilizador")',
        r'\1data-admin-user-action-link="1"\n            data-admin-user-action="view"\n            data-user-id="{{ row.id }}"\n            \2',
        text,
    )

    text = re.sub(
        r'(<a\s+class="table-icon-btn"\s+href="/users/new\?menu=administrativo&admin_tab=utilizador&user_edit_id=\{\{\s*row\.id\s*\}\}&user_view=0&target=edit-user-card#edit-user-card"\s+)(title="Modificar utilizador")',
        r'\1data-admin-user-action-link="1"\n            data-admin-user-action="edit"\n            data-user-id="{{ row.id }}"\n            \2',
        text,
    )

    write_text_if_changed(path, text)


def patch_new_user_head(path: Path) -> None:
    require_file(path)
    text = read_text(path)

    text = re.sub(
        r'\n?\s*<!-- APPVERBO_ADMIN_USER_ACTION_NAVIGATION_HEAD_V\d+_START -->[\s\S]*?<!-- APPVERBO_ADMIN_USER_ACTION_NAVIGATION_HEAD_V\d+_END -->\s*\n?',
        "\n",
        text,
    )

    text = re.sub(
        r'\n?\s*<script\s+(?:defer\s+)?src="/static/js/modules/admin_user_action_navigation_v1\.js[^"]*"(?:\s+defer)?>\s*</script>\s*\n?',
        "\n",
        text,
    )

    block = '''  <!-- APPVERBO_ADMIN_USER_ACTION_NAVIGATION_HEAD_V2_START -->
  <script defer src="/static/js/modules/admin_user_action_navigation_v1.js?v=20260513-utilizador-action-navigation-head-v2"></script>
  <!-- APPVERBO_ADMIN_USER_ACTION_NAVIGATION_HEAD_V2_END -->
'''

    head_extra_pattern = re.compile(r"({%\s*block\s+head_extra\s*%})([\s\S]*?)({%\s*endblock\s*%})", re.MULTILINE)
    match = head_extra_pattern.search(text)

    if not match:
        raise RuntimeError("ERRO: bloco head_extra não encontrado em templates/new_user.html")

    head_body = match.group(2)
    new_head_body = head_body.rstrip() + "\n" + block + "\n"

    text = text[: match.start(2)] + new_head_body + text[match.end(2) :]

    write_text_if_changed(path, text)


def patch_user_repository(path: Path) -> None:
    if not path.exists():
        print(f"AVISO: user_repository.py não encontrado: {path}")
        return

    text = read_text(path)

    import_block = '''from appverbo.admin_subprocesses.utilizador.urls import (
    montar_url_editar_utilizador_v1,
    montar_url_exibir_utilizador_v1,
    montar_url_fechar_utilizador_v1,
)
'''

    if "montar_url_exibir_utilizador_v1" not in text:
        marker = "from appverbo.admin_subprocesses.repositories.base import BaseAdminSubprocessRepository\n"
        if marker not in text:
            raise RuntimeError("ERRO: não foi possível localizar import base em user_repository.py")
        text = text.replace(marker, marker + import_block, 1)

    if '"view_url"' not in text and "'view_url'" not in text:
        patterns = [
            r'("created_at"\s*:\s*[^,\n]+,)',
            r'("account_status_label"\s*:\s*[^,\n]+,)',
            r'("status_label"\s*:\s*[^,\n]+,)',
        ]

        inserted = False

        for pattern in patterns:
            if re.search(pattern, text):
                text = re.sub(
                    pattern,
                    r'''\1
            "view_url": montar_url_exibir_utilizador_v1(user_id),
            "edit_url": montar_url_editar_utilizador_v1(user_id),
            "close_url": montar_url_fechar_utilizador_v1(),''',
                    text,
                    count=1,
                )
                inserted = True
                break

        if not inserted:
            print("AVISO: não foi possível inserir view_url/edit_url automaticamente em user_repository.py; validação posterior vai indicar se já existe por outro caminho.")

    write_text_if_changed(path, text)


def validate_content() -> None:
    new_user = read_text(ROOT / "templates/new_user.html")
    shadow = read_text(ROOT / "templates/partials/admin_user_shadow_readonly_v1.html")
    nav_js = read_text(ROOT / "static/js/modules/admin_user_action_navigation_v1.js")
    urls = read_text(ROOT / "appverbo/admin_subprocesses/utilizador/urls.py")

    required_pairs = [
        ("new_user.html", "APPVERBO_ADMIN_USER_ACTION_NAVIGATION_HEAD_V2_START", new_user),
        ("new_user.html", "admin_user_action_navigation_v1.js?v=20260513-utilizador-action-navigation-head-v2", new_user),
        ("admin_user_shadow_readonly_v1.html", 'data-admin-user-action-link="1"', shadow),
        ("admin_user_shadow_readonly_v1.html", 'data-admin-user-action="view"', shadow),
        ("admin_user_shadow_readonly_v1.html", 'data-admin-user-action="edit"', shadow),
        ("admin_user_shadow_readonly_v1.html", "row.get(\"view_url\")", shadow),
        ("admin_user_shadow_readonly_v1.html", "row.get(\"edit_url\")", shadow),
        ("admin_user_action_navigation_v1.js", "APPVERBO_ADMIN_USER_ACTION_NAVIGATION_V2", nav_js),
        ("admin_user_action_navigation_v1.js", "document.addEventListener(\"click\", navegarParaAcaoUtilizador_v2, true)", nav_js),
        ("admin_user_action_navigation_v1.js", "stopImmediatePropagation", nav_js),
        ("urls.py", "montar_url_exibir_utilizador_v1", urls),
        ("urls.py", "montar_url_editar_utilizador_v1", urls),
        ("urls.py", "target={USER_EDIT_TARGET_V1}", urls),
    ]

    for file_name, needle, haystack in required_pairs:
        if needle not in haystack:
            raise RuntimeError(f"ERRO: validação falhou em {file_name}; não encontrou: {needle}")

    print("OK: conteúdo validado com sucesso.")


def compile_python(path: Path) -> None:
    if path.exists():
        py_compile.compile(str(path), doraise=True)
        print(f"py_compile OK: {path}")


def main() -> None:
    new_user_path = ROOT / "templates/new_user.html"
    shadow_partial_path = ROOT / "templates/partials/admin_user_shadow_readonly_v1.html"
    legacy_partial_path = ROOT / "templates/partials/admin_user_table_v1.html"
    nav_js_path = ROOT / "static/js/modules/admin_user_action_navigation_v1.js"
    table_js_path = ROOT / "static/js/modules/admin_user_shadow_table_v1.js"
    urls_path = ROOT / "appverbo/admin_subprocesses/utilizador/urls.py"
    repository_path = ROOT / "appverbo/admin_subprocesses/repositories/user_repository.py"

    require_file(new_user_path)

    write_text_if_changed(urls_path, build_urls_py())
    write_text_if_changed(nav_js_path, build_navigation_js())

    patch_shadow_partial(shadow_partial_path)
    patch_legacy_partial(legacy_partial_path)
    patch_new_user_head(new_user_path)
    patch_user_repository(repository_path)

    if table_js_path.exists():
        table_js_text = read_text(table_js_path)
        clean_table_js_text = remove_old_navigation_blocks(table_js_text)
        write_text_if_changed(table_js_path, clean_table_js_text)

    validate_content()

    compile_python(urls_path)
    compile_python(repository_path)

    print("OK: patch de ações Exibir/Editar aplicado com sucesso.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(str(exc))
        sys.exit(1)
