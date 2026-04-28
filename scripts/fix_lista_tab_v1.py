from __future__ import annotations

from pathlib import Path
from datetime import datetime
import shutil
import subprocess
import sys


####################################################################################
# (1) CONFIGURAÇÃO INICIAL
####################################################################################

ROOT = Path.cwd()
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

TEMPLATE_PATH = ROOT / "templates" / "new_user.html"
JS_PATH = ROOT / "static" / "js" / "modules" / "force_lista_tab_v1.js"


####################################################################################
# (2) FUNÇÕES AUXILIARES
####################################################################################

def read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def backup_file(path: Path) -> None:
    if path.exists():
        backup_path = path.with_name(f"{path.name}.bak_force_lista_tab_v1_{TIMESTAMP}")
        shutil.copy2(path, backup_path)
        print(f"BACKUP: {backup_path}")


def run_command(command: list[str]) -> None:
    print("EXEC:", " ".join(command))
    result = subprocess.run(command, cwd=ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Comando falhou: {' '.join(command)}")


####################################################################################
# (3) VALIDAR PROJETO
####################################################################################

def validate_project_v1() -> None:
    if not (ROOT / "appverbo").exists():
        raise FileNotFoundError("Execute dentro da pasta raiz do AppVerboBraga.")

    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError("templates/new_user.html não encontrado.")

    print("OK: projeto validado.")


####################################################################################
# (4) CRIAR JS QUE FORÇA A ABA LISTA
####################################################################################

def create_force_lista_tab_js_v1() -> None:
    content = r'''//###################################################################################
// APPVERBOBRAGA - FORÇAR ABA LISTA NO EDITAR PROCESSO
//###################################################################################

(function () {
  "use strict";

  //###################################################################################
  // (1) FUNÇÕES AUXILIARES
  //###################################################################################

  function normalizeKey(value) {
    return String(value || "")
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9_]+/g, "_")
      .replace(/_+/g, "_")
      .replace(/^_|_$/g, "");
  }

  function getUrl() {
    return new URL(window.location.href);
  }

  function getParam(name) {
    try {
      return getUrl().searchParams.get(name) || "";
    } catch (error) {
      return "";
    }
  }

  function isEditingProcess() {
    return Boolean(getParam("settings_edit_key"));
  }

  function getSettingsEditKey() {
    return normalizeKey(getParam("settings_edit_key"));
  }

  function getCurrentTab() {
    return String(getParam("settings_tab") || "")
      .trim()
      .toLowerCase()
      .replace(/_/g, "-");
  }

  function buildListaHref() {
    const url = getUrl();
    url.searchParams.set("menu", "administrativo");
    url.searchParams.set("settings_action", "edit");
    url.searchParams.set("settings_tab", "lista");

    const key = getSettingsEditKey();
    if (key) {
      url.searchParams.set("settings_edit_key", key);
    }

    url.hash = "settings-menu-edit-card";
    return `${url.pathname}${url.search}${url.hash}`;
  }

  //###################################################################################
  // (2) GARANTIR QUE A ABA LISTA APARECE
  //###################################################################################

  function ensureListaTab_v1() {
    if (!isEditingProcess()) {
      return;
    }

    if (document.querySelector("[data-settings-tab='lista'], a[href*='settings_tab=lista']")) {
      return;
    }

    const tabCandidates = Array.from(
      document.querySelectorAll("a[href*='settings_tab='], button[data-settings-tab], [data-settings-tab]")
    );

    if (!tabCandidates.length) {
      return;
    }

    const camposAdicionaisTab = tabCandidates.find(function (element) {
      const href = String(element.getAttribute("href") || "");
      const dataTab = String(element.getAttribute("data-settings-tab") || "");

      return href.includes("settings_tab=campos-adicionais") ||
        dataTab === "campos-adicionais" ||
        element.textContent.trim().toLowerCase().includes("campos adicionais");
    });

    const reference = camposAdicionaisTab || tabCandidates[tabCandidates.length - 1];

    const listaTab = reference.cloneNode(true);
    listaTab.textContent = "Lista";
    listaTab.setAttribute("data-settings-tab", "lista");

    if (listaTab.tagName && listaTab.tagName.toLowerCase() === "a") {
      listaTab.setAttribute("href", buildListaHref());
    }

    listaTab.classList.remove("active", "is-active", "selected");

    if (getCurrentTab() === "lista") {
      listaTab.classList.add("active");
    }

    reference.insertAdjacentElement("afterend", listaTab);
  }

  //###################################################################################
  // (3) LOCALIZAR INFORMAÇÕES DO PROCESSO
  //###################################################################################

  function getBootstrap() {
    return window.__APPVERBO_BOOTSTRAP__ || {};
  }

  function getCurrentSetting() {
    const key = getSettingsEditKey();
    const settings = Array.isArray(getBootstrap().sidebarMenuSettings)
      ? getBootstrap().sidebarMenuSettings
      : [];

    return settings.find(function (setting) {
      return normalizeKey(setting.key) === key;
    }) || null;
  }

  function getProcessLists() {
    const setting = getCurrentSetting();

    return setting && Array.isArray(setting.process_lists)
      ? setting.process_lists
      : [];
  }

  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/"/g, "&quot;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  //###################################################################################
  // (4) CRIAR LINHA DA LISTA
  //###################################################################################

  function buildListRow_v1(item) {
    const row = document.createElement("div");
    row.className = "process-list-row-v1";

    const itemsCsv = item.items_csv || (Array.isArray(item.items) ? item.items.join(", ") : "");

    row.innerHTML = [
      `<input type="hidden" name="process_list_key" value="${escapeHtml(item.key || "")}">`,
      `<div class="field">`,
      `  <label>Nome da lista</label>`,
      `  <input name="process_list_label" value="${escapeHtml(item.label || "")}" placeholder="Ex.: Estado">`,
      `</div>`,
      `<div class="field full">`,
      `  <label>Itens da lista separados por vírgula</label>`,
      `  <input name="process_list_items_csv" value="${escapeHtml(itemsCsv)}" placeholder="Ativo, Inativo, Pendente, Em acompanhamento">`,
      `</div>`,
      `<div class="field process-list-actions-v1">`,
      `  <button type="button" class="action-btn-cancel" data-remove-process-list>Remover</button>`,
      `</div>`
    ].join("");

    row.querySelector("[data-remove-process-list]").addEventListener("click", function () {
      row.remove();
    });

    return row;
  }

  //###################################################################################
  // (5) RENDERIZAR CONTEÚDO DA ABA LISTA
  //###################################################################################

  function renderListaTab_v1() {
    if (getCurrentTab() !== "lista") {
      return;
    }

    const key = getSettingsEditKey();
    const card = document.getElementById("settings-menu-edit-card");

    if (!key || !card) {
      return;
    }

    if (card.querySelector("[data-force-lista-pane-v1]")) {
      return;
    }

    Array.from(card.querySelectorAll("form")).forEach(function (form) {
      if (!String(form.getAttribute("action") || "").includes("/settings/menu/process-lists")) {
        form.style.display = "none";
      }
    });

    const pane = document.createElement("section");
    pane.className = "admin-subsection";
    pane.setAttribute("data-force-lista-pane-v1", "1");

    const lists = getProcessLists();
    const rows = lists.length ? lists : [{ key: "", label: "", items_csv: "" }];

    pane.innerHTML = [
      `<h3>Lista</h3>`,
      `<p class="muted">Crie listas reutilizáveis. Separe os itens por vírgula. Ex.: Ativo, Inativo, Pendente, Em acompanhamento.</p>`,
      `<form method="post" action="/settings/menu/process-lists" id="process-lists-form-v1">`,
      `  <input type="hidden" name="menu_key" value="${escapeHtml(key)}">`,
      `  <input type="hidden" name="redirect_menu" value="administrativo">`,
      `  <input type="hidden" name="redirect_target" value="#settings-menu-edit-card">`,
      `  <div id="process-lists-rows-v1" class="process-lists-rows-v1"></div>`,
      `  <div class="form-action-row">`,
      `    <button type="button" class="action-btn-secondary" id="add-process-list-v1">Adicionar lista</button>`,
      `    <button type="submit" class="action-btn">Guardar listas</button>`,
      `  </div>`,
      `</form>`
    ].join("");

    const rowsContainer = pane.querySelector("#process-lists-rows-v1");

    rows.forEach(function (item) {
      rowsContainer.appendChild(buildListRow_v1(item));
    });

    pane.querySelector("#add-process-list-v1").addEventListener("click", function () {
      rowsContainer.appendChild(buildListRow_v1({ key: "", label: "", items_csv: "" }));
    });

    const tabBar = card.querySelector(".settings-tabs, .process-tabs, nav, .tabs");
    if (tabBar) {
      tabBar.insertAdjacentElement("afterend", pane);
    } else {
      card.prepend(pane);
    }
  }

  //###################################################################################
  // (6) INICIALIZAÇÃO
  //###################################################################################

  function run_v1() {
    ensureListaTab_v1();
    renderListaTab_v1();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", run_v1);
  } else {
    run_v1();
  }

  window.setTimeout(run_v1, 100);
  window.setTimeout(run_v1, 400);
  window.setTimeout(run_v1, 1000);
  window.setTimeout(run_v1, 1800);
})();
'''
    write_file(JS_PATH, content)
    print(f"OK: criado {JS_PATH}")


####################################################################################
# (5) INJETAR JS NO TEMPLATE
####################################################################################

def inject_script_v1() -> None:
    content = read_file(TEMPLATE_PATH)
    script_tag = '<script src="/static/js/modules/force_lista_tab_v1.js?v=20260428a"></script>'

    if "force_lista_tab_v1.js" in content:
        print("AVISO: force_lista_tab_v1.js já está no template.")
        return

    marker = '<script src="/static/js/modules/process_lists_v1.js'
    index = content.find(marker)

    if index >= 0:
        insert_at = content.find("</script>", index)
        if insert_at >= 0:
            insert_at += len("</script>")
            content = content[:insert_at] + "\n  " + script_tag + content[insert_at:]
            write_file(TEMPLATE_PATH, content)
            print("OK: script injetado após process_lists_v1.js.")
            return

    marker = '<script src="/static/js/new_user.js'
    index = content.find(marker)

    if index >= 0:
        insert_at = content.find("</script>", index)
        if insert_at >= 0:
            insert_at += len("</script>")
            content = content[:insert_at] + "\n  " + script_tag + content[insert_at:]
            write_file(TEMPLATE_PATH, content)
            print("OK: script injetado após new_user.js.")
            return

    last_endblock = content.rfind("{% endblock %}")
    if last_endblock >= 0:
        content = content[:last_endblock] + "  " + script_tag + "\n" + content[last_endblock:]
    else:
        content = content + "\n" + script_tag + "\n"

    write_file(TEMPLATE_PATH, content)
    print("OK: script injetado no fim do template.")


####################################################################################
# (6) EXECUÇÃO
####################################################################################

def main() -> None:
    validate_project_v1()

    backup_file(TEMPLATE_PATH)
    backup_file(JS_PATH)

    create_force_lista_tab_js_v1()
    inject_script_v1()

    print("OK: correção da aba Lista aplicada.")


if __name__ == "__main__":
    main()