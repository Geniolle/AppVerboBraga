from __future__ import annotations

import re
from pathlib import Path


ROOT = Path.cwd()


####################################################################################
# (1) FUNCOES BASE
####################################################################################

def read_text_v2(relative_path: str) -> str:
    path = ROOT / relative_path
    if not path.exists():
        raise FileNotFoundError(f"Ficheiro nao encontrado: {relative_path}")
    return path.read_text(encoding="utf-8")


def write_text_v2(relative_path: str, content: str) -> None:
    path = ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)

    if not content.endswith("\n"):
        content += "\n"

    path.write_text(content, encoding="utf-8", newline="\n")


def require_v2(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def replace_first_v2(content: str, old: str, new: str, label: str) -> str:
    if old not in content:
        raise RuntimeError(f"ERRO: marcador nao encontrado: {label}")
    return content.replace(old, new, 1)


####################################################################################
# (2) GARANTIR PARTIAL REUTILIZAVEL DO RODAPE
####################################################################################

def write_footer_partial_v2() -> None:
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
    write_text_v2("templates/partials/admin_table_footer_standard_v1.html", content)


####################################################################################
# (3) GARANTIR CSS REUTILIZAVEL DO RODAPE
####################################################################################

def write_footer_css_v2() -> None:
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
    write_text_v2("static/css/modules/admin_table_footer_standard_v1.css", content)


####################################################################################
# (4) GARANTIR JS REUTILIZAVEL DO RODAPE
####################################################################################

def write_footer_js_v2() -> None:
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
    write_text_v2("static/js/modules/admin_table_footer_standard_v1.js", content)


####################################################################################
# (5) CORRIGIR PARTIAL DE UTILIZADORES PELO ELSE CORRETO
####################################################################################

def patch_admin_user_table_partial_v2() -> None:
    path = "templates/partials/admin_user_table_v1.html"
    content = read_text_v2(path)

    import_line = '{% from "partials/admin_table_footer_standard_v1.html" import render_admin_table_footer_standard_v1 %}'
    footer_call = '{{ render_admin_table_footer_standard_v1(table_id=table_id, page_size=5, aria_label="Entradas por página") }}'

    if import_line not in content:
        content = import_line + "\n" + content.lstrip("\n")

    empty_marker = '<p class="empty">{{ empty_message }}</p>'
    empty_index = content.find(empty_marker)

    require_v2(
        empty_index >= 0,
        "ERRO: marcador empty_message nao encontrado no partial de utilizadores.",
    )

    else_index = content.rfind("{% else %}", 0, empty_index)

    require_v2(
        else_index >= 0,
        "ERRO: {% else %} correto do bloco rows nao encontrado antes de empty_message.",
    )

    table_close_index = content.rfind("</table>", 0, else_index)

    require_v2(
        table_close_index >= 0,
        "ERRO: </table> nao encontrado antes do else correto do bloco rows.",
    )

    table_close_end = table_close_index + len("</table>")

    before = content[:table_close_end].rstrip()
    after = content[else_index:].lstrip()

    content = before + "\n" + footer_call + "\n" + after

    write_text_v2(path, content)


####################################################################################
# (6) CORRIGIR MACRO GENERICO DE SUBPROCESSOS
####################################################################################

def patch_admin_subprocess_macro_v2() -> None:
    path = "templates/macros/admin_subprocess.html"
    content = read_text_v2(path)

    import_line = '{% from "partials/admin_table_footer_standard_v1.html" import render_admin_table_footer_standard_v1 %}'
    footer_call = '{{ render_admin_table_footer_standard_v1(table_id="admin-subprocess-" ~ state.config.key ~ "-" ~ status_value ~ "-table", page_size=5, aria_label="Entradas por página (" ~ title ~ ")") }}'

    if import_line not in content:
        content = import_line + "\n" + content.lstrip("\n")

    if 'id="admin-subprocess-{{ state.config.key }}-{{ status_value }}-table"' not in content:
        content = replace_first_v2(
            content,
            '<table class="admin-subprocess-table-v1">',
            '<table id="admin-subprocess-{{ state.config.key }}-{{ status_value }}-table" class="admin-subprocess-table-v1" data-admin-table-standard-v1="1">',
            "tabela generica de subprocessos",
        )

    if footer_call not in content:
        empty_marker = '<p class="empty">Sem registos.</p>'
        empty_index = content.find(empty_marker)

        require_v2(
            empty_index >= 0,
            "ERRO: marcador Sem registos nao encontrado no macro de subprocessos.",
        )

        else_index = content.rfind("{% else %}", 0, empty_index)

        require_v2(
            else_index >= 0,
            "ERRO: else correto do bloco rows nao encontrado no macro de subprocessos.",
        )

        table_wrap_close_index = content.rfind("</div>", 0, else_index)
        table_close_index = content.rfind("</table>", 0, table_wrap_close_index)

        require_v2(
            table_close_index >= 0 and table_wrap_close_index >= 0 and table_close_index < table_wrap_close_index,
            "ERRO: estrutura table/wrap nao encontrada antes do else correto no macro de subprocessos.",
        )

        wrap_close_end = table_wrap_close_index + len("</div>")
        content = content[:wrap_close_end].rstrip() + "\n      " + footer_call + "\n" + content[else_index:]

    write_text_v2(path, content)


####################################################################################
# (7) CORRIGIR TEMPLATE PRINCIPAL
####################################################################################

def patch_new_user_template_v2() -> None:
    path = "templates/new_user.html"
    content = read_text_v2(path)

    css_href = "/static/css/modules/admin_table_footer_standard_v1.css"
    js_src = "/static/js/modules/admin_table_footer_standard_v1.js"

    css_tag = '<link rel="stylesheet" href="/static/css/modules/admin_table_footer_standard_v1.css?v=20260516-admin-table-footer-standard-v1">'
    js_tag = '<script src="/static/js/modules/admin_table_footer_standard_v1.js?v=20260516-admin-table-footer-standard-v1" defer></script>'

    if css_href not in content:
        admin_status_pattern = re.compile(
            r'(<link rel="stylesheet" href="/static/css/modules/admin_status_tables_v1.css[^"]*">)'
        )
        match = admin_status_pattern.search(content)

        if match:
            content = content.replace(match.group(1), match.group(1) + "\n" + css_tag, 1)
        else:
            content = content.replace("{% block head_extra %}", "{% block head_extra %}\n" + css_tag, 1)

    if js_src not in content:
        head_end_marker = "{% endblock %}"
        content = replace_first_v2(content, head_end_marker, js_tag + "\n" + head_end_marker, "fim do head_extra")

    write_text_v2(path, content)


####################################################################################
# (8) VALIDAR CONTEUDO
####################################################################################

def validate_content_v2() -> None:
    footer_partial = read_text_v2("templates/partials/admin_table_footer_standard_v1.html")
    footer_css = read_text_v2("static/css/modules/admin_table_footer_standard_v1.css")
    footer_js = read_text_v2("static/js/modules/admin_table_footer_standard_v1.js")
    users_partial = read_text_v2("templates/partials/admin_user_table_v1.html")
    subprocess_macro = read_text_v2("templates/macros/admin_subprocess.html")
    template = read_text_v2("templates/new_user.html")

    checks = {
        "macro reutilizavel": "macro render_admin_table_footer_standard_v1" in footer_partial,
        "data attr footer": "data-admin-table-footer-standard-v1" in footer_partial,
        "css marker": "APPVERBO_ADMIN_TABLE_FOOTER_STANDARD_V1_START" in footer_css,
        "js api": "window.AppVerboAdminTableFooterStandard_v1" in footer_js,
        "users import": 'from "partials/admin_table_footer_standard_v1.html" import render_admin_table_footer_standard_v1' in users_partial,
        "users footer call": "render_admin_table_footer_standard_v1(table_id=table_id" in users_partial,
        "users old hardcoded footer removed": users_partial.count("admin-status-table-footer-v1") <= 1,
        "subprocess import": 'from "partials/admin_table_footer_standard_v1.html" import render_admin_table_footer_standard_v1' in subprocess_macro,
        "subprocess table id": 'id="admin-subprocess-{{ state.config.key }}-{{ status_value }}-table"' in subprocess_macro,
        "subprocess footer call": 'table_id="admin-subprocess-" ~ state.config.key ~ "-" ~ status_value ~ "-table"' in subprocess_macro,
        "template css": "admin_table_footer_standard_v1.css" in template,
        "template js": "admin_table_footer_standard_v1.js" in template,
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
        text = read_text_v2(relative_path)

        if "Ã" in text or "Â" in text or "�" in text:
            raise RuntimeError(f"ERRO: possivel mojibake encontrado em {relative_path}")


####################################################################################
# (9) EXECUTAR
####################################################################################

def main_v2() -> None:
    write_footer_partial_v2()
    write_footer_css_v2()
    write_footer_js_v2()
    patch_admin_user_table_partial_v2()
    patch_admin_subprocess_macro_v2()
    patch_new_user_template_v2()
    validate_content_v2()

    print("OK: correcao v2 aplicada.")
    print("OK: partial reutilizavel do rodape criado/atualizado.")
    print("OK: CSS reutilizavel do rodape criado/atualizado.")
    print("OK: JS reutilizavel do rodape criado/atualizado.")
    print("OK: partial de utilizadores usa o macro reutilizavel.")
    print("OK: macro de subprocessos usa o macro reutilizavel.")
    print("OK: new_user.html carrega CSS e JS do rodape reutilizavel.")


if __name__ == "__main__":
    main_v2()
