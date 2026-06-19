from __future__ import annotations

import re
from pathlib import Path


ROOT = Path.cwd()


####################################################################################
# (1) FUNCOES BASE
####################################################################################

def read_text_v7(relative_path: str) -> str:
    path = ROOT / relative_path

    if not path.exists():
        raise FileNotFoundError(f"Ficheiro nao encontrado: {relative_path}")

    return path.read_text(encoding="utf-8")


def write_text_v7(relative_path: str, content: str) -> None:
    path = ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)

    if not content.endswith("\n"):
        content += "\n"

    path.write_text(content, encoding="utf-8", newline="\n")


def require_v7(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def replace_marker_block_v7(content: str, start_marker: str, end_marker: str, new_block: str) -> str:
    start_index = content.find(start_marker)
    end_index = content.find(end_marker)

    if start_index >= 0 and end_index >= start_index:
        end_index += len(end_marker)
        return content[:start_index].rstrip() + "\n\n" + new_block.strip() + "\n\n" + content[end_index:].lstrip()

    return content.rstrip() + "\n\n" + new_block.strip() + "\n"


def validate_no_mojibake_v7(relative_path: str) -> None:
    content = read_text_v7(relative_path)
    bad_tokens = ("Ã", "Â", "\ufffd")
    bad_lines = []

    for line_number, line in enumerate(content.splitlines(), start=1):
        if any(token in line for token in bad_tokens):
            bad_lines.append((line_number, line))

    if bad_lines:
        print(f"ERRO: possivel mojibake em {relative_path}")
        for line_number, line in bad_lines:
            print(f"Linha {line_number}: {line}")
        raise RuntimeError(f"Possivel mojibake em {relative_path}")


####################################################################################
# (2) CORRIGIR LOCAL CERTO: JS PRINCIPAL DO RODAPE PADRAO
####################################################################################

def patch_admin_table_footer_js_v7() -> None:
    relative_path = "static/js/modules/admin_table_footer_standard_v1.js"
    content = read_text_v7(relative_path)

    block = r'''// APPVERBO_ADMIN_MENU_FOOTER_FORCE_DEDUPE_V7_START

//###################################################################################
// APPVERBOBRAGA - CORRECAO DEFINITIVA DO RODAPE DUPLICADO DO MENU V7
//###################################################################################

(function () {
  "use strict";

  //###################################################################################
  // (1) FUNCOES BASE
  //###################################################################################

  function normalizarTextoMenuFooterForceDedupe_v7(value) {
    return String(value || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase()
      .trim();
  }

  function isMenuCardMenuFooterForceDedupe_v7(cardEl) {
    if (!cardEl) {
      return false;
    }

    const titleEl = cardEl.querySelector("h2, h3");
    const titleText = normalizarTextoMenuFooterForceDedupe_v7(titleEl ? titleEl.textContent : "");

    return titleText.indexOf("menus ativos") >= 0 || titleText.indexOf("menus inativos") >= 0;
  }

  function isAfterTableMenuFooterForceDedupe_v7(element, tableEl) {
    if (!element || !tableEl) {
      return false;
    }

    return Boolean(tableEl.compareDocumentPosition(element) & Node.DOCUMENT_POSITION_FOLLOWING);
  }

  function isFooterLikeMenuFooterForceDedupe_v7(element, tableEl) {
    if (!element || !tableEl) {
      return false;
    }

    if (!isAfterTableMenuFooterForceDedupe_v7(element, tableEl)) {
      return false;
    }

    if (!element.querySelector("select")) {
      return false;
    }

    const text = normalizarTextoMenuFooterForceDedupe_v7(element.textContent);

    return text.indexOf("entradas") >= 0 && text.indexOf("pagina") >= 0;
  }

  function getTopFooterRootMenuFooterForceDedupe_v7(element, cardEl, tableEl) {
    let currentEl = element;
    let parentEl = currentEl.parentElement;

    while (
      parentEl &&
      parentEl !== cardEl &&
      isFooterLikeMenuFooterForceDedupe_v7(parentEl, tableEl)
    ) {
      currentEl = parentEl;
      parentEl = currentEl.parentElement;
    }

    return currentEl;
  }

  function getFooterRootsMenuFooterForceDedupe_v7(cardEl) {
    if (!cardEl) {
      return [];
    }

    const tableEl = cardEl.querySelector("table");

    if (!tableEl) {
      return [];
    }

    const allElements = Array.from(cardEl.querySelectorAll("div, nav, footer"));
    const roots = [];

    allElements.forEach(function (element) {
      if (!isFooterLikeMenuFooterForceDedupe_v7(element, tableEl)) {
        return;
      }

      const rootEl = getTopFooterRootMenuFooterForceDedupe_v7(element, cardEl, tableEl);

      if (!rootEl) {
        return;
      }

      const alreadyInsideExistingRoot = roots.some(function (existingRoot) {
        return existingRoot === rootEl || existingRoot.contains(rootEl);
      });

      if (alreadyInsideExistingRoot) {
        return;
      }

      for (let index = roots.length - 1; index >= 0; index -= 1) {
        if (rootEl.contains(roots[index])) {
          roots.splice(index, 1);
        }
      }

      roots.push(rootEl);
    });

    roots.sort(function (leftEl, rightEl) {
      if (leftEl === rightEl) {
        return 0;
      }

      if (leftEl.compareDocumentPosition(rightEl) & Node.DOCUMENT_POSITION_FOLLOWING) {
        return -1;
      }

      return 1;
    });

    return roots;
  }

  function showFooterMenuFooterForceDedupe_v7(footerEl) {
    if (!footerEl) {
      return;
    }

    footerEl.removeAttribute("data-admin-menu-footer-force-hidden-v7");
    footerEl.classList.remove("admin-menu-footer-force-hidden-v7");

    if (footerEl.style) {
      footerEl.style.removeProperty("display");
      footerEl.style.removeProperty("height");
      footerEl.style.removeProperty("min-height");
      footerEl.style.removeProperty("margin");
      footerEl.style.removeProperty("padding");
      footerEl.style.removeProperty("border");
      footerEl.style.removeProperty("overflow");
    }
  }

  function hideFooterMenuFooterForceDedupe_v7(footerEl) {
    if (!footerEl) {
      return;
    }

    footerEl.setAttribute("data-admin-menu-footer-force-hidden-v7", "1");
    footerEl.setAttribute("aria-hidden", "true");
    footerEl.classList.add("admin-menu-footer-force-hidden-v7");

    if (footerEl.style) {
      footerEl.style.setProperty("display", "none", "important");
      footerEl.style.setProperty("height", "0", "important");
      footerEl.style.setProperty("min-height", "0", "important");
      footerEl.style.setProperty("margin", "0", "important");
      footerEl.style.setProperty("padding", "0", "important");
      footerEl.style.setProperty("border", "0", "important");
      footerEl.style.setProperty("overflow", "hidden", "important");
    }
  }

  //###################################################################################
  // (2) APLICAR DEDUPE SOMENTE NOS CARDS MENUS ATIVOS / MENUS INATIVOS
  //###################################################################################

  function aplicarMenuFooterForceDedupe_v7(rootEl) {
    const scopeEl = rootEl || document;
    const cards = Array.from(scopeEl.querySelectorAll(".card, section, .admin-subprocess-table-card-v1"));

    cards.forEach(function (cardEl) {
      if (!isMenuCardMenuFooterForceDedupe_v7(cardEl)) {
        return;
      }

      const footers = getFooterRootsMenuFooterForceDedupe_v7(cardEl);

      footers.forEach(function (footerEl, index) {
        if (index === 0) {
          showFooterMenuFooterForceDedupe_v7(footerEl);
          return;
        }

        hideFooterMenuFooterForceDedupe_v7(footerEl);
      });
    });
  }

  //###################################################################################
  // (3) REAPLICAR APOS TODOS OS SCRIPTS QUE POSSAM INJETAR RODAPE
  //###################################################################################

  function scheduleMenuFooterForceDedupe_v7() {
    [0, 50, 150, 300, 700, 1200, 2500, 5000].forEach(function (delayMs) {
      window.setTimeout(function () {
        aplicarMenuFooterForceDedupe_v7(document);
      }, delayMs);
    });
  }

  function startObserverMenuFooterForceDedupe_v7() {
    if (!document.body || window.AppVerboAdminMenuFooterForceDedupeObserverStarted_v7) {
      return;
    }

    const observer = new MutationObserver(function () {
      window.clearTimeout(window.AppVerboAdminMenuFooterForceDedupeTimer_v7);

      window.AppVerboAdminMenuFooterForceDedupeTimer_v7 = window.setTimeout(function () {
        aplicarMenuFooterForceDedupe_v7(document);
      }, 80);
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });

    window.AppVerboAdminMenuFooterForceDedupeObserverStarted_v7 = true;
  }

  window.AppVerboAdminMenuFooterForceDedupe_v7 = {
    aplicarMenuFooterForceDedupe_v7: aplicarMenuFooterForceDedupe_v7
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      scheduleMenuFooterForceDedupe_v7();
      startObserverMenuFooterForceDedupe_v7();
    });
  } else {
    scheduleMenuFooterForceDedupe_v7();
    startObserverMenuFooterForceDedupe_v7();
  }

  window.addEventListener("load", scheduleMenuFooterForceDedupe_v7);
})();

// APPVERBO_ADMIN_MENU_FOOTER_FORCE_DEDUPE_V7_END'''

    content = replace_marker_block_v7(
        content,
        "// APPVERBO_ADMIN_MENU_FOOTER_FORCE_DEDUPE_V7_START",
        "// APPVERBO_ADMIN_MENU_FOOTER_FORCE_DEDUPE_V7_END",
        block,
    )

    write_text_v7(relative_path, content)


####################################################################################
# (3) CSS DE SEGURANCA COM !IMPORTANT
####################################################################################

def patch_admin_table_footer_css_v7() -> None:
    relative_path = "static/css/modules/admin_table_footer_standard_v1.css"
    content = read_text_v7(relative_path)

    block = '''/* APPVERBO_ADMIN_MENU_FOOTER_FORCE_DEDUPE_V7_START */

.admin-menu-footer-force-hidden-v7,
[data-admin-menu-footer-force-hidden-v7="1"] {
  border: 0 !important;
  display: none !important;
  height: 0 !important;
  margin: 0 !important;
  min-height: 0 !important;
  overflow: hidden !important;
  padding: 0 !important;
}

/* APPVERBO_ADMIN_MENU_FOOTER_FORCE_DEDUPE_V7_END */'''

    content = replace_marker_block_v7(
        content,
        "/* APPVERBO_ADMIN_MENU_FOOTER_FORCE_DEDUPE_V7_START */",
        "/* APPVERBO_ADMIN_MENU_FOOTER_FORCE_DEDUPE_V7_END */",
        block,
    )

    write_text_v7(relative_path, content)


####################################################################################
# (4) ATUALIZAR TEMPLATE E REMOVER MODULO ANTIGO QUE NAO RESOLVEU
####################################################################################

def patch_new_user_template_v7() -> None:
    relative_path = "templates/new_user.html"
    content = read_text_v7(relative_path)

    css_tag = '<link rel="stylesheet" href="/static/css/modules/admin_table_footer_standard_v1.css?v=20260516-admin-footer-standard-v7-force-menu-dedupe">'
    js_tag = '<script src="/static/js/modules/admin_table_footer_standard_v1.js?v=20260516-admin-footer-standard-v7-force-menu-dedupe" defer></script>'

    content = re.sub(
        r'<link rel="stylesheet" href="/static/css/modules/admin_table_footer_standard_v1\.css\?v=[^"]*">',
        css_tag,
        content,
        count=1,
    )

    content = re.sub(
        r'<script src="/static/js/modules/admin_table_footer_standard_v1\.js\?v=[^"]*" defer></script>',
        js_tag,
        content,
        count=1,
    )

    content = re.sub(
        r'\n?\s*<link rel="stylesheet" href="/static/css/modules/admin_menu_footer_dedupe_v1\.css\?v=[^"]*">\s*',
        "\n",
        content,
    )

    content = re.sub(
        r'\n?\s*<script src="/static/js/modules/admin_menu_footer_dedupe_v1\.js\?v=[^"]*" defer></script>\s*',
        "\n",
        content,
    )

    require_v7(
        "admin-footer-standard-v7-force-menu-dedupe" in content,
        "ERRO: cache buster v7 nao aplicado.",
    )

    write_text_v7(relative_path, content)


####################################################################################
# (5) VALIDACOES
####################################################################################

def validate_content_v7() -> None:
    js = read_text_v7("static/js/modules/admin_table_footer_standard_v1.js")
    css = read_text_v7("static/css/modules/admin_table_footer_standard_v1.css")
    template = read_text_v7("templates/new_user.html")

    checks = {
        "JS contem bloco V7": "APPVERBO_ADMIN_MENU_FOOTER_FORCE_DEDUPE_V7_START" in js,
        "JS contem aplicador V7": "function aplicarMenuFooterForceDedupe_v7" in js,
        "JS usa display none important": 'setProperty("display", "none", "important")' in js,
        "JS identifica Menus ativos": "menus ativos" in js,
        "JS identifica Menus inativos": "menus inativos" in js,
        "CSS contem bloco V7": "APPVERBO_ADMIN_MENU_FOOTER_FORCE_DEDUPE_V7_START" in css,
        "Template carrega cache buster V7": "admin-footer-standard-v7-force-menu-dedupe" in template,
        "Template nao carrega modulo antigo": "admin_menu_footer_dedupe_v1" not in template,
    }

    failed = [label for label, ok in checks.items() if not ok]

    if failed:
        raise RuntimeError("Validacoes falharam: " + ", ".join(failed))

    validate_no_mojibake_v7("static/js/modules/admin_table_footer_standard_v1.js")
    validate_no_mojibake_v7("static/css/modules/admin_table_footer_standard_v1.css")
    validate_no_mojibake_v7("templates/new_user.html")


####################################################################################
# (6) EXECUTAR
####################################################################################

def main_v7() -> None:
    patch_admin_table_footer_js_v7()
    patch_admin_table_footer_css_v7()
    patch_new_user_template_v7()
    validate_content_v7()

    print("OK: local correto corrigido: static/js/modules/admin_table_footer_standard_v1.js")
    print("OK: dedupe V7 aplicado em Menus ativos e Menus inativos.")
    print("OK: ocultacao usa display none important para vencer CSS anterior.")
    print("OK: cache buster V7 aplicado no template.")


if __name__ == "__main__":
    main_v7()
