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

    path.write_text(content, encoding="utf-8", newline="\n")


def require_v1(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


####################################################################################
# (2) CRIAR CSS ESPECIFICO PARA OCULTAR A LINHA DUPLICADA DO MENU
####################################################################################

def write_css_v1() -> None:
    content = '''/* APPVERBO_ADMIN_MENU_FOOTER_DEDUPE_V1_START */

.admin-menu-footer-duplicate-hidden-v1,
[data-admin-menu-footer-duplicate-hidden-v1="1"] {
  display: none !important;
}

/* APPVERBO_ADMIN_MENU_FOOTER_DEDUPE_V1_END */
'''
    write_text_v1("static/css/modules/admin_menu_footer_dedupe_v1.css", content)


####################################################################################
# (3) CRIAR JS ESPECIFICO PARA MANTER APENAS O PRIMEIRO RODAPE DO MENU
####################################################################################

def write_js_v1() -> None:
    content = '''//###################################################################################
// APPVERBOBRAGA - ADMIN MENU FOOTER DEDUPE V1
//###################################################################################

(function () {
  "use strict";

  //###################################################################################
  // (1) FUNCOES BASE
  //###################################################################################

  function normalizarTextoMenuFooterDedupe_v1(value) {
    return String(value || "")
      .normalize("NFD")
      .replace(/[\\u0300-\\u036f]/g, "")
      .toLowerCase()
      .trim();
  }

  function isCardMenuFooterDedupe_v1(cardEl) {
    if (!cardEl) {
      return false;
    }

    const titleEl = cardEl.querySelector("h2, h3");
    const titleText = normalizarTextoMenuFooterDedupe_v1(titleEl ? titleEl.textContent : "");

    return titleText.indexOf("menus ativos") >= 0 || titleText.indexOf("menus inativos") >= 0;
  }

  function getFooterRootMenuFooterDedupe_v1(element) {
    if (!element) {
      return null;
    }

    return element.closest(
      "[data-admin-table-footer-standard-v1='1'], " +
      ".admin-table-footer-standard-v1, " +
      ".admin-status-table-footer-v1, " +
      ".table-limiter, " +
      "[id$='-limiter']"
    );
  }

  function getFooterCandidatesMenuFooterDedupe_v1(cardEl) {
    if (!cardEl) {
      return [];
    }

    const selector = [
      "[data-admin-table-footer-standard-v1='1']",
      ".admin-table-footer-standard-v1",
      ".admin-status-table-footer-v1",
      ".table-limiter",
      "[id$='-limiter']"
    ].join(",");

    const rawCandidates = Array.from(cardEl.querySelectorAll(selector));
    const uniqueCandidates = [];

    rawCandidates.forEach(function (candidateEl) {
      const footerRoot = getFooterRootMenuFooterDedupe_v1(candidateEl);

      if (!footerRoot || footerRoot !== candidateEl) {
        return;
      }

      if (uniqueCandidates.indexOf(footerRoot) < 0) {
        uniqueCandidates.push(footerRoot);
      }
    });

    uniqueCandidates.sort(function (leftEl, rightEl) {
      if (leftEl === rightEl) {
        return 0;
      }

      if (leftEl.compareDocumentPosition(rightEl) & Node.DOCUMENT_POSITION_FOLLOWING) {
        return -1;
      }

      return 1;
    });

    return uniqueCandidates;
  }

  function showFooterMenuFooterDedupe_v1(footerEl) {
    if (!footerEl) {
      return;
    }

    footerEl.classList.remove("admin-menu-footer-duplicate-hidden-v1");
    footerEl.removeAttribute("data-admin-menu-footer-duplicate-hidden-v1");

    if (footerEl.style.display === "none") {
      footerEl.style.display = "";
    }
  }

  function hideFooterMenuFooterDedupe_v1(footerEl) {
    if (!footerEl) {
      return;
    }

    footerEl.classList.add("admin-menu-footer-duplicate-hidden-v1");
    footerEl.setAttribute("data-admin-menu-footer-duplicate-hidden-v1", "1");
    footerEl.style.display = "none";
  }

  //###################################################################################
  // (2) CORRIGIR DUPLICACAO SOMENTE NOS CARDS DO SUBPROCESSO MENU
  //###################################################################################

  function aplicarDedupeMenuFooterDedupe_v1(rootEl) {
    const scopeEl = rootEl || document;
    const cards = Array.from(scopeEl.querySelectorAll(".card, section, .admin-subprocess-table-card-v1"));

    cards.forEach(function (cardEl) {
      if (!isCardMenuFooterDedupe_v1(cardEl)) {
        return;
      }

      const footers = getFooterCandidatesMenuFooterDedupe_v1(cardEl);

      if (footers.length <= 1) {
        if (footers.length === 1) {
          showFooterMenuFooterDedupe_v1(footers[0]);
        }

        return;
      }

      footers.forEach(function (footerEl, index) {
        if (index === 0) {
          showFooterMenuFooterDedupe_v1(footerEl);
          return;
        }

        hideFooterMenuFooterDedupe_v1(footerEl);
      });
    });
  }

  //###################################################################################
  // (3) EXECUTAR APOS OUTROS MODULOS E REAPLICAR SE HOUVER RENDER DINAMICO
  //###################################################################################

  function scheduleDedupeMenuFooterDedupe_v1() {
    window.setTimeout(function () {
      aplicarDedupeMenuFooterDedupe_v1(document);
    }, 50);

    window.setTimeout(function () {
      aplicarDedupeMenuFooterDedupe_v1(document);
    }, 250);

    window.setTimeout(function () {
      aplicarDedupeMenuFooterDedupe_v1(document);
    }, 750);
  }

  function startObserverMenuFooterDedupe_v1() {
    if (!document.body || window.AppVerboAdminMenuFooterDedupeObserverStarted_v1) {
      return;
    }

    const observer = new MutationObserver(function () {
      scheduleDedupeMenuFooterDedupe_v1();
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });

    window.AppVerboAdminMenuFooterDedupeObserverStarted_v1 = true;
  }

  window.AppVerboAdminMenuFooterDedupe_v1 = {
    aplicarDedupeMenuFooterDedupe_v1: aplicarDedupeMenuFooterDedupe_v1
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      scheduleDedupeMenuFooterDedupe_v1();
      startObserverMenuFooterDedupe_v1();
    });
  } else {
    scheduleDedupeMenuFooterDedupe_v1();
    startObserverMenuFooterDedupe_v1();
  }

  window.addEventListener("load", scheduleDedupeMenuFooterDedupe_v1);
})();
'''
    write_text_v1("static/js/modules/admin_menu_footer_dedupe_v1.js", content)


####################################################################################
# (4) ATUALIZAR TEMPLATE PRINCIPAL
####################################################################################

def patch_new_user_v1() -> None:
    relative_path = "templates/new_user.html"
    content = read_text_v1(relative_path)

    css_tag = '<link rel="stylesheet" href="/static/css/modules/admin_menu_footer_dedupe_v1.css?v=20260516-menu-footer-dedupe-v1">'
    js_tag = '<script src="/static/js/modules/admin_menu_footer_dedupe_v1.js?v=20260516-menu-footer-dedupe-v1" defer></script>'

    if "admin_menu_footer_dedupe_v1.css" not in content:
        if "admin_table_footer_standard_v1.css" in content:
            content = re.sub(
                r'(<link rel="stylesheet" href="/static/css/modules/admin_table_footer_standard_v1\.css\?v=[^"]*">)',
                r'\1\n' + css_tag,
                content,
                count=1,
            )
        else:
            content = content.replace("{% block head_extra %}", "{% block head_extra %}\n" + css_tag, 1)

    if "admin_menu_footer_dedupe_v1.js" not in content:
        if "admin_table_footer_standard_v1.js" in content:
            content = re.sub(
                r'(<script src="/static/js/modules/admin_table_footer_standard_v1\.js\?v=[^"]*" defer></script>)',
                r'\1\n' + js_tag,
                content,
                count=1,
            )
        else:
            content = content.replace("{% endblock %}", js_tag + "\n{% endblock %}", 1)

    write_text_v1(relative_path, content)


####################################################################################
# (5) VALIDAR CONTEUDO
####################################################################################

def validate_no_mojibake_v1(relative_path: str) -> None:
    content = read_text_v1(relative_path)
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


def validate_content_v1() -> None:
    css = read_text_v1("static/css/modules/admin_menu_footer_dedupe_v1.css")
    js = read_text_v1("static/js/modules/admin_menu_footer_dedupe_v1.js")
    template = read_text_v1("templates/new_user.html")

    checks = {
        "CSS contem classe de ocultacao": "admin-menu-footer-duplicate-hidden-v1" in css,
        "JS contem funcao principal": "function aplicarDedupeMenuFooterDedupe_v1" in js,
        "JS identifica Menus ativos": "menus ativos" in js,
        "JS identifica Menus inativos": "menus inativos" in js,
        "JS oculta somente duplicados": "hideFooterMenuFooterDedupe_v1" in js,
        "Template carrega CSS": "admin_menu_footer_dedupe_v1.css" in template,
        "Template carrega JS": "admin_menu_footer_dedupe_v1.js" in template,
    }

    failed = [label for label, ok in checks.items() if not ok]

    if failed:
        raise RuntimeError("Validacoes falharam: " + ", ".join(failed))

    validate_no_mojibake_v1("static/css/modules/admin_menu_footer_dedupe_v1.css")
    validate_no_mojibake_v1("static/js/modules/admin_menu_footer_dedupe_v1.js")
    validate_no_mojibake_v1("templates/new_user.html")


####################################################################################
# (6) EXECUTAR
####################################################################################

def main_v1() -> None:
    write_css_v1()
    write_js_v1()
    patch_new_user_v1()
    validate_content_v1()

    print("OK: modulo especifico criado para remover a linha duplicada do rodape do Menu.")
    print("OK: a primeira linha do rodape sera mantida.")
    print("OK: a segunda linha duplicada sera ocultada.")
    print("OK: template new_user.html atualizado com CSS e JS especificos.")


if __name__ == "__main__":
    main_v1()
