from __future__ import annotations

import re
from pathlib import Path


ROOT = Path.cwd()


####################################################################################
# (1) FUNCOES BASE
####################################################################################

def read_text_v1(relative_path: str) -> str:
    path = ROOT / relative_path
    if not path.exists():
        raise FileNotFoundError(f"Ficheiro nao encontrado: {relative_path}")
    return path.read_text(encoding="utf-8")


def write_text_v1(relative_path: str, content: str) -> None:
    path = ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)

    if not content.endswith("\n"):
        content += "\n"

    with path.open("w", encoding="utf-8", newline="\n") as file_obj:
        file_obj.write(content)


def require_v1(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def replace_once_v1(content: str, old: str, new: str, label: str) -> str:
    if old not in content:
        raise RuntimeError(f"ERRO: bloco nao encontrado para substituir: {label}")
    return content.replace(old, new, 1)


####################################################################################
# (2) CRIAR PARTIAL REUTILIZAVEL DO RODAPE PADRAO
####################################################################################

def write_footer_partial_v1() -> None:
    content = '''{% macro render_admin_table_footer_standard_v1(table_id="", page_size=5, aria_label="Entradas por página") %}
<div
  class="admin-table-footer-standard-v1 table-footer admin-status-table-footer-v1"
  data-admin-table-footer-standard-v1="1"
  {% if table_id %}data-admin-table-id="{{ table_id }}"{% endif %}
>
  <div class="admin-table-footer-page-size-v1">
    <select
      class="admin-table-footer-page-size-select-v1"
      aria-label="{{ aria_label }}"
      data-admin-table-footer-page-size-v1="1"
    >
      <option value="5" {% if page_size == 5 %}selected{% endif %}>5</option>
      <option value="10" {% if page_size == 10 %}selected{% endif %}>10</option>
      <option value="20" {% if page_size == 20 %}selected{% endif %}>20</option>
    </select>
    <span class="admin-table-footer-label-v1">
      <span>entradas</span>
      <span>por página</span>
    </span>
  </div>

  <div class="admin-table-footer-pagination-v1 pagination" data-admin-table-footer-pagination-v1="1">
    <button
      type="button"
      class="admin-table-footer-nav-btn-v1"
      aria-label="Página anterior"
      data-admin-table-footer-prev-v1="1"
      disabled
    >&#8249;</button>

    <span
      class="admin-table-footer-page-v1 active"
      aria-current="page"
      data-admin-table-footer-page-v1="1"
    >1</span>

    <button
      type="button"
      class="admin-table-footer-nav-btn-v1"
      aria-label="Próxima página"
      data-admin-table-footer-next-v1="1"
      disabled
    >&#8250;</button>
  </div>
</div>
{% endmacro %}
'''
    write_text_v1("templates/partials/admin_table_footer_standard_v1.html", content)


####################################################################################
# (3) CRIAR CSS REUTILIZAVEL DO RODAPE PADRAO
####################################################################################

def write_footer_css_v1() -> None:
    content = '''/* APPVERBO_ADMIN_TABLE_FOOTER_STANDARD_V1_START */

.admin-table-footer-standard-v1 {
  align-items: center;
  border-top: 1px solid #d8e0ec;
  display: grid;
  gap: 10px;
  grid-template-columns: minmax(0, 1fr) auto;
  justify-content: initial;
  margin-top: 8px;
  min-width: 100%;
  padding-top: 8px;
  width: 100%;
}

.admin-table-footer-page-size-v1 {
  align-items: center;
  display: inline-flex;
  gap: 6px;
  justify-self: start;
  min-width: 0;
}

.admin-table-footer-page-size-select-v1 {
  max-width: 76px;
  min-width: 64px;
  width: auto;
}

.admin-table-footer-label-v1 {
  align-items: flex-start;
  display: inline-flex;
  flex-direction: column;
  font-size: 11px;
  line-height: 1.15;
  white-space: nowrap;
}

.admin-table-footer-pagination-v1 {
  align-items: center;
  display: inline-flex;
  gap: 6px;
  justify-self: end;
  margin-left: auto;
}

.admin-table-footer-nav-btn-v1,
.admin-table-footer-page-v1 {
  align-items: center;
  border: 1px solid #d8e0ec;
  border-radius: 999px;
  display: inline-flex;
  font-size: 12px;
  height: 22px;
  justify-content: center;
  line-height: 1;
  min-width: 24px;
  padding: 0 8px;
}

.admin-table-footer-nav-btn-v1 {
  background: #ffffff;
  color: #4a5f7a;
  cursor: pointer;
}

.admin-table-footer-nav-btn-v1:disabled {
  cursor: default;
  opacity: 0.45;
}

.admin-table-footer-page-v1 {
  background: #1f67b8;
  border-color: #1f67b8;
  color: #ffffff;
  font-weight: 700;
}

@media (max-width: 640px) {
  .admin-table-footer-standard-v1 {
    grid-template-columns: 1fr;
  }

  .admin-table-footer-pagination-v1 {
    justify-self: start;
    margin-left: 0;
  }
}

/* APPVERBO_ADMIN_TABLE_FOOTER_STANDARD_V1_END */
'''
    write_text_v1("static/css/modules/admin_table_footer_standard_v1.css", content)


####################################################################################
# (4) CRIAR JAVASCRIPT REUTILIZAVEL DO RODAPE PADRAO
####################################################################################

def write_footer_js_v1() -> None:
    content = '''//###################################################################################
// APPVERBOBRAGA - ADMIN TABLE FOOTER STANDARD V1
//###################################################################################

(function () {
  "use strict";

  //###################################################################################
  // (1) FUNCOES BASE
  //###################################################################################

  function toSafeString_v1(value) {
    return String(value === null || value === undefined ? "" : value);
  }

  function toInteger_v1(value, fallback) {
    const parsed = parseInt(value, 10);
    return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
  }

  function clamp_v1(value, min, max) {
    return Math.min(Math.max(value, min), max);
  }

  function escapeAttribute_v1(value) {
    return toSafeString_v1(value)
      .replace(/&/g, "&amp;")
      .replace(/"/g, "&quot;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  //###################################################################################
  // (2) HTML REUTILIZAVEL PARA TABELAS GERADAS POR JAVASCRIPT
  //###################################################################################

  function buildFooterHtml_v1(config) {
    const safeConfig = config || {};
    const tableId = toSafeString_v1(safeConfig.tableId).trim();
    const pageSize = toInteger_v1(safeConfig.pageSize, 5);
    const ariaLabel = toSafeString_v1(safeConfig.ariaLabel || "Entradas por página");

    return [
      '<div class="admin-table-footer-standard-v1 table-footer admin-status-table-footer-v1" data-admin-table-footer-standard-v1="1"' + (tableId ? ' data-admin-table-id="' + escapeAttribute_v1(tableId) + '"' : "") + '>',
      '  <div class="admin-table-footer-page-size-v1">',
      '    <select class="admin-table-footer-page-size-select-v1" aria-label="' + escapeAttribute_v1(ariaLabel) + '" data-admin-table-footer-page-size-v1="1">',
      '      <option value="5"' + (pageSize === 5 ? " selected" : "") + '>5</option>',
      '      <option value="10"' + (pageSize === 10 ? " selected" : "") + '>10</option>',
      '      <option value="20"' + (pageSize === 20 ? " selected" : "") + '>20</option>',
      '    </select>',
      '    <span class="admin-table-footer-label-v1"><span>entradas</span><span>por página</span></span>',
      '  </div>',
      '  <div class="admin-table-footer-pagination-v1 pagination" data-admin-table-footer-pagination-v1="1">',
      '    <button type="button" class="admin-table-footer-nav-btn-v1" aria-label="Página anterior" data-admin-table-footer-prev-v1="1" disabled>&#8249;</button>',
      '    <span class="admin-table-footer-page-v1 active" aria-current="page" data-admin-table-footer-page-v1="1">1</span>',
      '    <button type="button" class="admin-table-footer-nav-btn-v1" aria-label="Próxima página" data-admin-table-footer-next-v1="1" disabled>&#8250;</button>',
      '  </div>',
      '</div>'
    ].join("");
  }

  //###################################################################################
  // (3) LOCALIZAR TABELA ASSOCIADA AO RODAPE
  //###################################################################################

  function findTableForFooter_v1(footerEl) {
    const tableId = toSafeString_v1(footerEl.dataset.adminTableId).trim();

    if (tableId) {
      const tableById = document.getElementById(tableId);

      if (tableById) {
        return tableById;
      }
    }

    const previousEl = footerEl.previousElementSibling;

    if (previousEl) {
      if (previousEl.matches && previousEl.matches("table")) {
        return previousEl;
      }

      const tableInsidePrevious = previousEl.querySelector ? previousEl.querySelector("table") : null;

      if (tableInsidePrevious) {
        return tableInsidePrevious;
      }
    }

    const cardEl = footerEl.closest(".card, section, .admin-subprocess-card-v1");

    if (!cardEl) {
      return null;
    }

    const tables = Array.from(cardEl.querySelectorAll("table"));

    for (let index = tables.length - 1; index >= 0; index -= 1) {
      const tableEl = tables[index];

      if (tableEl.compareDocumentPosition(footerEl) & Node.DOCUMENT_POSITION_FOLLOWING) {
        return tableEl;
      }
    }

    return tables.length ? tables[0] : null;
  }

  function getTableRows_v1(tableEl) {
    if (!tableEl) {
      return [];
    }

    const tbodyEl = tableEl.querySelector("tbody");

    if (!tbodyEl) {
      return [];
    }

    return Array.from(tbodyEl.querySelectorAll("tr"));
  }

  //###################################################################################
  // (4) RENDERIZAR PAGINACAO
  //###################################################################################

  function renderFooterState_v1(state) {
    const rows = getTableRows_v1(state.tableEl);
    const totalRows = rows.length;
    const totalPages = Math.max(1, Math.ceil(totalRows / state.pageSize));

    state.currentPage = clamp_v1(state.currentPage, 1, totalPages);

    const startIndex = (state.currentPage - 1) * state.pageSize;
    const endIndex = startIndex + state.pageSize;

    rows.forEach(function (rowEl, index) {
      rowEl.style.display = index >= startIndex && index < endIndex ? "" : "none";
    });

    state.pageEl.textContent = String(state.currentPage);
    state.prevEl.disabled = state.currentPage <= 1;
    state.nextEl.disabled = state.currentPage >= totalPages;
  }

  function initializeFooter_v1(footerEl) {
    if (!footerEl || footerEl.dataset.adminTableFooterInitializedV1 === "1") {
      return;
    }

    const tableEl = findTableForFooter_v1(footerEl);
    const pageSizeEl = footerEl.querySelector("[data-admin-table-footer-page-size-v1='1']");
    const prevEl = footerEl.querySelector("[data-admin-table-footer-prev-v1='1']");
    const nextEl = footerEl.querySelector("[data-admin-table-footer-next-v1='1']");
    const pageEl = footerEl.querySelector("[data-admin-table-footer-page-v1='1']");

    if (!tableEl || !pageSizeEl || !prevEl || !nextEl || !pageEl) {
      return;
    }

    const state = {
      tableEl: tableEl,
      pageSizeEl: pageSizeEl,
      prevEl: prevEl,
      nextEl: nextEl,
      pageEl: pageEl,
      currentPage: 1,
      pageSize: toInteger_v1(pageSizeEl.value, 5)
    };

    pageSizeEl.addEventListener("change", function () {
      state.pageSize = toInteger_v1(pageSizeEl.value, 5);
      state.currentPage = 1;
      renderFooterState_v1(state);
    });

    prevEl.addEventListener("click", function () {
      if (state.currentPage > 1) {
        state.currentPage -= 1;
        renderFooterState_v1(state);
      }
    });

    nextEl.addEventListener("click", function () {
      state.currentPage += 1;
      renderFooterState_v1(state);
    });

    footerEl.dataset.adminTableFooterInitializedV1 = "1";
    renderFooterState_v1(state);
  }

  function initializeFooters_v1(rootEl) {
    const scopeEl = rootEl || document;
    const footers = Array.from(scopeEl.querySelectorAll("[data-admin-table-footer-standard-v1='1']"));

    footers.forEach(initializeFooter_v1);
  }

  //###################################################################################
  // (5) EXPOR API E INICIALIZAR
  //###################################################################################

  window.AppVerboAdminTableFooterStandard_v1 = {
    buildFooterHtml_v1: buildFooterHtml_v1,
    initializeFooters_v1: initializeFooters_v1
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      initializeFooters_v1(document);
    });
  } else {
    initializeFooters_v1(document);
  }
})();
'''
    write_text_v1("static/js/modules/admin_table_footer_standard_v1.js", content)


####################################################################################
# (5) PATCH DO PARTIAL DE UTILIZADORES
####################################################################################

def patch_admin_user_table_partial_v1() -> None:
    path = "templates/partials/admin_user_table_v1.html"
    content = read_text_v1(path)

    import_line = '{% from "partials/admin_table_footer_standard_v1.html" import render_admin_table_footer_standard_v1 %}'

    if import_line not in content:
        content = import_line + "\n" + content

    footer_call = '{{ render_admin_table_footer_standard_v1(table_id=table_id, page_size=5, aria_label="Entradas por página") }}'

    if footer_call not in content:
        footer_pattern = re.compile(
            r'\n<div class="table-footer admin-status-table-footer-v1">\s*'
            r'<select[^>]*>[\s\S]*?</select>\s*'
            r'<span>entradas por página</span>\s*'
            r'<div class="pagination">[\s\S]*?</div>\s*'
            r'</div>\s*',
            flags=re.S,
        )

        content, replacements = footer_pattern.subn("\n" + footer_call + "\n", content, count=1)

        require_v1(
            replacements == 1,
            "ERRO: nao foi possivel substituir o rodape antigo em templates/partials/admin_user_table_v1.html.",
        )

    write_text_v1(path, content)


####################################################################################
# (6) PATCH DO MACRO GENERICO DE SUBPROCESSOS ADMINISTRATIVOS
####################################################################################

def patch_admin_subprocess_macro_v1() -> None:
    path = "templates/macros/admin_subprocess.html"
    content = read_text_v1(path)

    import_line = '{% from "partials/admin_table_footer_standard_v1.html" import render_admin_table_footer_standard_v1 %}'

    if import_line not in content:
        content = import_line + "\n" + content.lstrip("\n")

    old_table = '<table class="admin-subprocess-table-v1">'
    new_table = '<table id="admin-subprocess-{{ state.config.key }}-{{ status_value }}-table" class="admin-subprocess-table-v1" data-admin-table-standard-v1="1">'

    if old_table in content:
        content = content.replace(old_table, new_table, 1)
    elif 'class="admin-subprocess-table-v1"' in content and 'data-admin-table-standard-v1="1"' not in content:
        content = content.replace(
            'class="admin-subprocess-table-v1"',
            'class="admin-subprocess-table-v1" data-admin-table-standard-v1="1"',
            1,
        )

    footer_call = '{{ render_admin_table_footer_standard_v1(table_id="admin-subprocess-" ~ state.config.key ~ "-" ~ status_value ~ "-table", page_size=5, aria_label="Entradas por página (" ~ title ~ ")") }}'

    if footer_call not in content:
        old_static_footer_pattern = re.compile(
            r'\n\s*<div[^>]*class="[^"]*(?:table-limiter|table-footer|admin-status-table-footer-v1)[^"]*"[^>]*>[\s\S]*?</div>\s*</div>\s*(?=\n\s*{% else %})',
            flags=re.S,
        )

        content, replacements = old_static_footer_pattern.subn("\n      " + footer_call + "\n", content, count=1)

        if replacements == 0:
            marker = "        </table>\n      </div>\n    {% else %}"
            replacement = "        </table>\n      </div>\n      " + footer_call + "\n    {% else %}"

            content = replace_once_v1(
                content,
                marker,
                replacement,
                "inserir rodape padrao no macro render_admin_subprocess_table",
            )

    write_text_v1(path, content)


####################################################################################
# (7) PATCH DO TEMPLATE PRINCIPAL PARA CARREGAR CSS E JS
####################################################################################

def patch_new_user_template_v1() -> None:
    path = "templates/new_user.html"
    content = read_text_v1(path)

    css_href = "/static/css/modules/admin_table_footer_standard_v1.css"
    js_src = "/static/js/modules/admin_table_footer_standard_v1.js"

    css_tag = '<link rel="stylesheet" href="/static/css/modules/admin_table_footer_standard_v1.css?v=20260516-admin-table-footer-standard-v1">'
    js_tag = '<script src="/static/js/modules/admin_table_footer_standard_v1.js?v=20260516-admin-table-footer-standard-v1" defer></script>'

    if css_href not in content:
        admin_status_match = re.search(
            r'(<link rel="stylesheet" href="/static/css/modules/admin_status_tables_v1.css[^"]*">)',
            content,
        )

        if admin_status_match:
            content = content.replace(admin_status_match.group(1), admin_status_match.group(1) + "\n" + css_tag, 1)
        else:
            content = content.replace("{% block head_extra %}", "{% block head_extra %}\n" + css_tag, 1)

    if js_src not in content:
        head_match = re.search(r'({% block head_extra %}[\s\S]*?)(\n{% endblock %})', content)

        require_v1(
            head_match is not None,
            "ERRO: bloco head_extra nao encontrado em templates/new_user.html.",
        )

        content = content[:head_match.end(1)] + "\n" + js_tag + content[head_match.end(1):]

    write_text_v1(path, content)


####################################################################################
# (8) VALIDACOES DO CONTEUDO
####################################################################################

def validate_content_v1() -> None:
    partial_footer = read_text_v1("templates/partials/admin_table_footer_standard_v1.html")
    css = read_text_v1("static/css/modules/admin_table_footer_standard_v1.css")
    js = read_text_v1("static/js/modules/admin_table_footer_standard_v1.js")
    users_partial = read_text_v1("templates/partials/admin_user_table_v1.html")
    subprocess_macro = read_text_v1("templates/macros/admin_subprocess.html")
    template = read_text_v1("templates/new_user.html")

    checks = {
        "macro footer standard": "macro render_admin_table_footer_standard_v1" in partial_footer,
        "footer data attr": "data-admin-table-footer-standard-v1" in partial_footer,
        "css footer standard": "APPVERBO_ADMIN_TABLE_FOOTER_STANDARD_V1_START" in css,
        "js api global": "window.AppVerboAdminTableFooterStandard_v1" in js,
        "js initializer": "function initializeFooters_v1" in js,
        "users partial imports footer": "render_admin_table_footer_standard_v1" in users_partial,
        "users partial uses footer macro": "table_id=table_id" in users_partial,
        "subprocess macro imports footer": "render_admin_table_footer_standard_v1" in subprocess_macro,
        "subprocess table has id": 'id="admin-subprocess-{{ state.config.key }}-{{ status_value }}-table"' in subprocess_macro,
        "subprocess uses footer macro": 'table_id="admin-subprocess-" ~ state.config.key ~ "-" ~ status_value ~ "-table"' in subprocess_macro,
        "new_user loads css": "admin_table_footer_standard_v1.css" in template,
        "new_user loads js": "admin_table_footer_standard_v1.js" in template,
    }

    failed = [name for name, ok in checks.items() if not ok]

    if failed:
        raise RuntimeError("ERRO: validacoes falharam: " + ", ".join(failed))

    for relative_path in [
        "templates/partials/admin_table_footer_standard_v1.html",
        "templates/partials/admin_user_table_v1.html",
        "templates/macros/admin_subprocess.html",
        "templates/new_user.html",
        "static/css/modules/admin_table_footer_standard_v1.css",
        "static/js/modules/admin_table_footer_standard_v1.js",
    ]:
        text = read_text_v1(relative_path)

        if "Ã" in text or "Â" in text or "�" in text:
            raise RuntimeError(f"ERRO: possivel mojibake encontrado em {relative_path}")


####################################################################################
# (9) EXECUTAR PATCH
####################################################################################

def main_v1() -> None:
    write_footer_partial_v1()
    write_footer_css_v1()
    write_footer_js_v1()
    patch_admin_user_table_partial_v1()
    patch_admin_subprocess_macro_v1()
    patch_new_user_template_v1()
    validate_content_v1()

    print("OK: partial reutilizavel criado.")
    print("OK: CSS reutilizavel criado.")
    print("OK: JS reutilizavel criado.")
    print("OK: partial de utilizadores atualizado.")
    print("OK: macro generico de subprocessos atualizado.")
    print("OK: template principal atualizado.")
    print("OK: validacoes de conteudo concluidas.")


if __name__ == "__main__":
    main_v1()
