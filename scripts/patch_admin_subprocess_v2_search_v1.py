from __future__ import annotations

import re
import shutil
from datetime import datetime
from pathlib import Path


####################################################################################
# (1) CONFIGURACAO
####################################################################################

PROJECT_ROOT = Path.cwd()

MACRO_PATH = PROJECT_ROOT / "templates" / "macros" / "admin_subprocess_v2.html"
CSS_PATH = PROJECT_ROOT / "static" / "css" / "modules" / "admin_subprocesses_v2.css"
JS_PATH = PROJECT_ROOT / "static" / "js" / "modules" / "admin_subprocesses_v2.js"
NEW_USER_TEMPLATE_PATH = PROJECT_ROOT / "templates" / "new_user.html"
STANDALONE_TEMPLATE_PATH = PROJECT_ROOT / "templates" / "admin_subprocess_v2_standalone.html"


####################################################################################
# (2) FUNCOES AUXILIARES
####################################################################################

def now_stamp_v1() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def read_text_v1(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text_v1(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def backup_file_v1(path: Path, suffix: str) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"Ficheiro nao encontrado para backup: {path}")

    backup_path = path.with_name(path.name + f".bak_{suffix}_{now_stamp_v1()}")
    shutil.copy2(path, backup_path)
    return backup_path


def require_file_v1(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Ficheiro obrigatorio nao encontrado: {path}")


####################################################################################
# (3) PATCH MACRO: ADICIONAR TOOLBAR COM PESQUISA
####################################################################################

def patch_macro_v1() -> None:
    content = read_text_v1(MACRO_PATH)

    if "data-admin-subprocess-v2-search" in content:
        print("OK: macro V2 ja contem pesquisa.")
        return

    old_block = '''  <section
    class="card admin-subprocess-card-v2 admin-subprocess-table-card-v2"
    data-admin-subprocess-v2="{{ state.config.key }}"
    data-admin-subprocess-v2-status="{{ status_value }}"
  >
    <h2>{{ title }}</h2>

    {% if rows %}'''

    new_block = '''  <section
    class="card admin-subprocess-card-v2 admin-subprocess-table-card-v2"
    data-admin-subprocess-v2="{{ state.config.key }}"
    data-admin-subprocess-v2-status="{{ status_value }}"
  >
    <div class="admin-subprocess-table-header-v2">
      <h2>{{ title }}</h2>

      {% if rows %}
        <div class="admin-subprocess-table-search-wrap-v2">
          <label class="sr-only" for="admin_subprocess_v2_search_{{ state.config.key }}_{{ status_value }}">
            Procurar
          </label>
          <input
            id="admin_subprocess_v2_search_{{ state.config.key }}_{{ status_value }}"
            class="admin-subprocess-search-v2"
            type="search"
            placeholder="Procurar"
            autocomplete="off"
            data-admin-subprocess-v2-search
          >
        </div>
      {% endif %}
    </div>

    {% if rows %}'''

    if old_block not in content:
        raise RuntimeError("Nao encontrei o bloco da tabela V2 para inserir pesquisa.")

    content = content.replace(old_block, new_block, 1)

    if "data-admin-subprocess-v2-search" not in content:
        raise RuntimeError("Pesquisa nao foi inserida na macro V2.")

    write_text_v1(MACRO_PATH, content)


####################################################################################
# (4) PATCH CSS: FORMATAÇÃO DA PESQUISA
####################################################################################

CSS_BLOCK = r'''
/* APPVERBO_ADMIN_SUBPROCESS_V2_SEARCH_START */

.admin-subprocess-table-header-v2 {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 12px;
}

.admin-subprocess-table-header-v2 h2 {
  margin: 0;
}

.admin-subprocess-table-search-wrap-v2 {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  min-width: 240px;
}

.admin-subprocess-search-v2 {
  width: min(260px, 100%);
  min-height: 34px;
  border: 1px solid #c6d0e2;
  border-radius: 999px;
  background: #ffffff;
  color: #12213a;
  padding: 7px 12px;
  box-sizing: border-box;
  font-size: 13px;
}

.admin-subprocess-search-v2:focus {
  outline: none;
  border-color: #7fa8f2;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12);
}

.admin-subprocess-no-search-results-v2 {
  display: none;
  padding: 14px 12px;
  color: #5d6b82;
  font-size: 13px;
}

.admin-subprocess-no-search-results-v2.is-visible {
  display: block;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

@media (max-width: 760px) {
  .admin-subprocess-table-header-v2 {
    align-items: stretch;
    flex-direction: column;
  }

  .admin-subprocess-table-search-wrap-v2 {
    justify-content: stretch;
    min-width: 0;
  }

  .admin-subprocess-search-v2 {
    width: 100%;
  }
}

/* APPVERBO_ADMIN_SUBPROCESS_V2_SEARCH_END */
'''


def patch_css_v1() -> None:
    content = read_text_v1(CSS_PATH)

    start_marker = "/* APPVERBO_ADMIN_SUBPROCESS_V2_SEARCH_START */"
    end_marker = "/* APPVERBO_ADMIN_SUBPROCESS_V2_SEARCH_END */"

    pattern = re.compile(
        re.escape(start_marker) + r".*?" + re.escape(end_marker),
        flags=re.DOTALL,
    )

    if pattern.search(content):
        content = pattern.sub(lambda _match: CSS_BLOCK.strip(), content)
    else:
        content = content.rstrip() + "\n\n" + CSS_BLOCK.strip() + "\n"

    write_text_v1(CSS_PATH, content)


####################################################################################
# (5) PATCH JS: FILTRO DE PESQUISA POR TABELA
####################################################################################

JS_FUNCTION = r'''
  //###################################################################################
  // (5) PESQUISA NAS TABELAS
  //###################################################################################

  function normalizeSearchTextV2(value) {
    return safeTextV2(value)
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function getRowSearchTextV2(row) {
    if (!row) {
      return "";
    }

    if (!row.dataset.adminSubprocessSearchTextV2) {
      row.dataset.adminSubprocessSearchTextV2 = normalizeSearchTextV2(row.textContent);
    }

    return row.dataset.adminSubprocessSearchTextV2;
  }

  function ensureNoResultsElementV2(card) {
    let element = card.querySelector("[data-admin-subprocess-v2-no-search-results]");

    if (element) {
      return element;
    }

    element = document.createElement("p");
    element.className = "admin-subprocess-no-search-results-v2";
    element.dataset.adminSubprocessV2NoSearchResults = "1";
    element.textContent = "Sem resultados para a pesquisa.";

    const tableWrap = card.querySelector(".admin-subprocess-table-wrap-v2");

    if (tableWrap && tableWrap.parentNode) {
      tableWrap.parentNode.insertBefore(element, tableWrap.nextSibling);
    } else {
      card.appendChild(element);
    }

    return element;
  }

  function applyTableSearchV2(input) {
    const card = input.closest(".admin-subprocess-table-card-v2");

    if (!card) {
      return;
    }

    const query = normalizeSearchTextV2(input.value);
    const rows = Array.from(card.querySelectorAll("tbody tr"));
    let visibleCount = 0;

    rows.forEach(function (row) {
      const rowText = getRowSearchTextV2(row);
      const isVisible = !query || rowText.includes(query);

      row.hidden = !isVisible;
      row.style.display = isVisible ? "" : "none";

      if (isVisible) {
        visibleCount += 1;
      }
    });

    const noResults = ensureNoResultsElementV2(card);
    const hasNoResults = rows.length > 0 && visibleCount === 0;

    noResults.classList.toggle("is-visible", hasNoResults);

    const tableWrap = card.querySelector(".admin-subprocess-table-wrap-v2");

    if (tableWrap) {
      tableWrap.hidden = hasNoResults;
      tableWrap.style.display = hasNoResults ? "none" : "";
    }
  }

  function setupTableSearchV2() {
    document.addEventListener("input", function (event) {
      const input = event.target.closest("[data-admin-subprocess-v2-search]");

      if (!input) {
        return;
      }

      applyTableSearchV2(input);
    }, true);

    document.querySelectorAll("[data-admin-subprocess-v2-search]").forEach(function (input) {
      applyTableSearchV2(input);
    });
  }
'''


def patch_js_v1() -> None:
    content = read_text_v1(JS_PATH)

    if "function setupTableSearchV2()" not in content:
        anchor = "  //###################################################################################\n  // (5) INICIAR\n  //###################################################################################"

        if anchor not in content:
            raise RuntimeError("Nao encontrei ponto para inserir setupTableSearchV2 no JS V2.")

        content = content.replace(anchor, JS_FUNCTION.rstrip() + "\n\n" + anchor, 1)

    if "setupTableSearchV2();" not in content:
        old_block = '''    setupViewActionsV2();
    setupCancelCreateV2();
    setupConfirmActionsV2();'''

        new_block = '''    setupViewActionsV2();
    setupCancelCreateV2();
    setupConfirmActionsV2();
    setupTableSearchV2();'''

        if old_block not in content:
            raise RuntimeError("Nao encontrei setupAdminSubprocessesV2 para chamar setupTableSearchV2.")

        content = content.replace(old_block, new_block, 1)

    required = [
        "function setupTableSearchV2()",
        "function applyTableSearchV2",
        "data-admin-subprocess-v2-search",
        "setupTableSearchV2();",
    ]

    missing = [marker for marker in required if marker not in content]

    if missing:
        raise RuntimeError("Marcadores ausentes no JS V2: " + ", ".join(missing))

    write_text_v1(JS_PATH, content)


####################################################################################
# (6) PATCH CACHE BUSTER
####################################################################################

def patch_cache_buster_v1(path: Path) -> None:
    content = read_text_v1(path)

    content = re.sub(
        r'admin_subprocesses_v2\.css\?v=[^"]+',
        "admin_subprocesses_v2.css?v=20260507-admin-subprocess-v2-search-v1",
        content,
    )

    content = re.sub(
        r'admin_subprocesses_v2\.js\?v=[^"]+',
        "admin_subprocesses_v2.js?v=20260507-admin-subprocess-v2-search-v1",
        content,
    )

    write_text_v1(path, content)


####################################################################################
# (7) VALIDAR CONTEUDO
####################################################################################

def validate_v1() -> None:
    macro_content = read_text_v1(MACRO_PATH)
    css_content = read_text_v1(CSS_PATH)
    js_content = read_text_v1(JS_PATH)
    new_user_content = read_text_v1(NEW_USER_TEMPLATE_PATH)
    standalone_content = read_text_v1(STANDALONE_TEMPLATE_PATH)

    required_macro = [
        "admin-subprocess-table-header-v2",
        "admin-subprocess-search-v2",
        "data-admin-subprocess-v2-search",
        "placeholder=\"Procurar\"",
    ]

    missing_macro = [marker for marker in required_macro if marker not in macro_content]

    if missing_macro:
        raise RuntimeError("Marcadores ausentes na macro V2: " + ", ".join(missing_macro))

    required_css = [
        "APPVERBO_ADMIN_SUBPROCESS_V2_SEARCH_START",
        "admin-subprocess-search-v2",
        "admin-subprocess-no-search-results-v2",
    ]

    missing_css = [marker for marker in required_css if marker not in css_content]

    if missing_css:
        raise RuntimeError("Marcadores ausentes no CSS V2: " + ", ".join(missing_css))

    required_js = [
        "function setupTableSearchV2()",
        "function applyTableSearchV2",
        "setupTableSearchV2();",
        "Sem resultados para a pesquisa.",
    ]

    missing_js = [marker for marker in required_js if marker not in js_content]

    if missing_js:
        raise RuntimeError("Marcadores ausentes no JS V2: " + ", ".join(missing_js))

    if "admin_subprocesses_v2.css?v=20260507-admin-subprocess-v2-search-v1" not in new_user_content:
        raise RuntimeError("Cache buster CSS V2 nao atualizado em new_user.html.")

    if "admin_subprocesses_v2.js?v=20260507-admin-subprocess-v2-search-v1" not in new_user_content:
        raise RuntimeError("Cache buster JS V2 nao atualizado em new_user.html.")

    if "admin_subprocesses_v2.css?v=20260507-admin-subprocess-v2-search-v1" not in standalone_content:
        raise RuntimeError("Cache buster CSS V2 nao atualizado no standalone.")

    if "admin_subprocesses_v2.js?v=20260507-admin-subprocess-v2-search-v1" not in standalone_content:
        raise RuntimeError("Cache buster JS V2 nao atualizado no standalone.")

    print("OK: pesquisa adicionada ao renderer V2.")
    print("OK: CSS da pesquisa V2 validado.")
    print("OK: JS de filtro por tabela validado.")
    print("OK: cache buster atualizado.")


####################################################################################
# (8) EXECUCAO
####################################################################################

def main() -> None:
    required_files = [
        MACRO_PATH,
        CSS_PATH,
        JS_PATH,
        NEW_USER_TEMPLATE_PATH,
        STANDALONE_TEMPLATE_PATH,
    ]

    for path in required_files:
        require_file_v1(path)
        backup_path = backup_file_v1(path, "admin_subprocess_v2_search_v1")
        print(f"OK: backup criado: {backup_path}")

    patch_macro_v1()
    patch_css_v1()
    patch_js_v1()
    patch_cache_buster_v1(NEW_USER_TEMPLATE_PATH)
    patch_cache_buster_v1(STANDALONE_TEMPLATE_PATH)
    validate_v1()

    print("OK: patch pesquisa Admin Subprocess V2 concluido.")


if __name__ == "__main__":
    main()
