from __future__ import annotations

import re
from pathlib import Path


ROOT = Path.cwd()


####################################################################################
# (1) FUNCOES BASE
####################################################################################

def read_text_v6(relative_path: str) -> str:
    path = ROOT / relative_path

    if not path.exists():
        raise FileNotFoundError(f"Ficheiro nao encontrado: {relative_path}")

    return path.read_text(encoding="utf-8")


def write_text_v6(relative_path: str, content: str) -> None:
    path = ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)

    if not content.endswith("\n"):
        content += "\n"

    path.write_text(content, encoding="utf-8", newline="\n")


def require_v6(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def validate_no_mojibake_v6(relative_path: str) -> None:
    content = read_text_v6(relative_path)
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
# (2) PATCH DO JS PRINCIPAL DO RODAPE PADRAO
####################################################################################

def patch_admin_table_footer_js_v6() -> None:
    relative_path = "static/js/modules/admin_table_footer_standard_v1.js"
    content = read_text_v6(relative_path)

    helper_block = r'''
  //###################################################################################
  // (6.1) PROTECAO DO SUBPROCESSO MENU CONTRA RODAPE DUPLICADO V6
  //###################################################################################

  function isMenuCardFooterStandard_v6(cardEl) {
    if (!cardEl) {
      return false;
    }

    const titleEl = cardEl.querySelector("h2, h3");
    const titleText = normalizeText_v2(titleEl ? titleEl.textContent : "");

    return titleText.indexOf("menus ativos") >= 0 || titleText.indexOf("menus inativos") >= 0;
  }

  function getFooterRootsFooterStandard_v6(cardEl) {
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

    const rawFooters = Array.from(cardEl.querySelectorAll(selector));
    const uniqueFooters = [];

    rawFooters.forEach(function (footerEl) {
      const rootFooter = footerEl.closest(selector);

      if (!rootFooter || rootFooter !== footerEl) {
        return;
      }

      if (uniqueFooters.indexOf(rootFooter) < 0) {
        uniqueFooters.push(rootFooter);
      }
    });

    uniqueFooters.sort(function (leftEl, rightEl) {
      if (leftEl === rightEl) {
        return 0;
      }

      if (leftEl.compareDocumentPosition(rightEl) & Node.DOCUMENT_POSITION_FOLLOWING) {
        return -1;
      }

      return 1;
    });

    return uniqueFooters;
  }

  function cardAlreadyHasMenuFooterFooterStandard_v6(cardEl) {
    return getFooterRootsFooterStandard_v6(cardEl).length > 0;
  }

  function showMenuFooterFooterStandard_v6(footerEl) {
    if (!footerEl) {
      return;
    }

    footerEl.removeAttribute("data-admin-menu-footer-hidden-source-v6");
    footerEl.classList.remove("admin-menu-footer-hidden-source-v6");

    if (footerEl.style && footerEl.style.display === "none") {
      footerEl.style.display = "";
    }
  }

  function hideMenuFooterFooterStandard_v6(footerEl) {
    if (!footerEl) {
      return;
    }

    footerEl.setAttribute("data-admin-menu-footer-hidden-source-v6", "1");
    footerEl.classList.add("admin-menu-footer-hidden-source-v6");
    footerEl.style.display = "none";
  }

  function hideExtraMenuFootersFooterStandard_v6(rootEl) {
    const scopeEl = rootEl || document;
    const cards = Array.from(scopeEl.querySelectorAll(".card, section, .admin-subprocess-table-card-v1"));

    cards.forEach(function (cardEl) {
      if (!isMenuCardFooterStandard_v6(cardEl)) {
        return;
      }

      const footers = getFooterRootsFooterStandard_v6(cardEl);

      footers.forEach(function (footerEl, index) {
        if (index === 0) {
          showMenuFooterFooterStandard_v6(footerEl);
          return;
        }

        hideMenuFooterFooterStandard_v6(footerEl);
      });
    });
  }
'''

    if "function isMenuCardFooterStandard_v6" not in content:
        marker = "  function insertFooterAfterTable_v2(tableEl) {"

        require_v6(
            marker in content,
            "ERRO: nao encontrei function insertFooterAfterTable_v2 no JS do rodape.",
        )

        content = content.replace(marker, helper_block + "\n" + marker, 1)

    old_guard = """  function insertFooterAfterTable_v2(tableEl) {
    const cardEl = getCardForElement_v2(tableEl);

    if (!cardEl || !isEligibleTable_v2(tableEl)) {
      return;
    }"""

    new_guard = """  function insertFooterAfterTable_v2(tableEl) {
    const cardEl = getCardForElement_v2(tableEl);

    if (!cardEl || !isEligibleTable_v2(tableEl)) {
      return;
    }

    if (isMenuCardFooterStandard_v6(cardEl) && cardAlreadyHasMenuFooterFooterStandard_v6(cardEl)) {
      return;
    }"""

    if "cardAlreadyHasMenuFooterFooterStandard_v6(cardEl)" not in content:
        require_v6(
            old_guard in content,
            "ERRO: bloco inicial de insertFooterAfterTable_v2 nao encontrado.",
        )

        content = content.replace(old_guard, new_guard, 1)

    if "hideExtraMenuFootersFooterStandard_v6(scopeEl);" not in content:
        inserted = False

        patterns = [
            "    hideDuplicateMenuFooters_v3(scopeEl);",
            "    hideDuplicateStandardFooters_v2(scopeEl);",
            "    hideLegacyFootersWhenStandardExists_v2(scopeEl);",
        ]

        for pattern in patterns:
            if pattern in content:
                content = content.replace(pattern, pattern + "\n    hideExtraMenuFootersFooterStandard_v6(scopeEl);", 1)
                inserted = True
                break

        require_v6(
            inserted,
            "ERRO: nao consegui inserir a chamada hideExtraMenuFootersFooterStandard_v6 no initializeFooters_v2.",
        )

    write_text_v6(relative_path, content)


####################################################################################
# (3) PATCH CSS DE SEGURANCA
####################################################################################

def patch_css_v6() -> None:
    relative_path = "static/css/modules/admin_table_footer_standard_v1.css"
    content = read_text_v6(relative_path)

    block = """
/* APPVERBO_ADMIN_TABLE_FOOTER_MENU_SOURCE_DEDUPE_V6_START */

.admin-menu-footer-hidden-source-v6,
[data-admin-menu-footer-hidden-source-v6="1"] {
  display: none !important;
}

/* APPVERBO_ADMIN_TABLE_FOOTER_MENU_SOURCE_DEDUPE_V6_END */
"""

    start_marker = "/* APPVERBO_ADMIN_TABLE_FOOTER_MENU_SOURCE_DEDUPE_V6_START */"
    end_marker = "/* APPVERBO_ADMIN_TABLE_FOOTER_MENU_SOURCE_DEDUPE_V6_END */"

    start_index = content.find(start_marker)
    end_index = content.find(end_marker)

    if start_index >= 0 and end_index >= start_index:
        end_index += len(end_marker)
        content = content[:start_index].rstrip() + "\n\n" + block.strip() + "\n\n" + content[end_index:].lstrip()
    else:
        content = content.rstrip() + "\n\n" + block.strip() + "\n"

    write_text_v6(relative_path, content)


####################################################################################
# (4) PATCH DO TEMPLATE PRINCIPAL
####################################################################################

def patch_new_user_v6() -> None:
    relative_path = "templates/new_user.html"
    content = read_text_v6(relative_path)

    css_tag = '<link rel="stylesheet" href="/static/css/modules/admin_table_footer_standard_v1.css?v=20260516-admin-footer-standard-v6-menu-source-dedupe">'
    js_tag = '<script src="/static/js/modules/admin_table_footer_standard_v1.js?v=20260516-admin-footer-standard-v6-menu-source-dedupe" defer></script>'

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

    require_v6(
        "admin-footer-standard-v6-menu-source-dedupe" in content,
        "ERRO: cache buster v6 nao foi aplicado no new_user.html.",
    )

    require_v6(
        "admin_menu_footer_dedupe_v1" not in content,
        "ERRO: referencias antigas admin_menu_footer_dedupe_v1 ainda existem no new_user.html.",
    )

    write_text_v6(relative_path, content)


####################################################################################
# (5) VALIDACOES
####################################################################################

def validate_content_v6() -> None:
    js = read_text_v6("static/js/modules/admin_table_footer_standard_v1.js")
    css = read_text_v6("static/css/modules/admin_table_footer_standard_v1.css")
    template = read_text_v6("templates/new_user.html")

    checks = {
        "JS contem isMenuCardFooterStandard_v6": "function isMenuCardFooterStandard_v6" in js,
        "JS contem guarda contra auto-injecao no Menu": "cardAlreadyHasMenuFooterFooterStandard_v6(cardEl)" in js,
        "JS contem limpeza de rodapes extras do Menu": "function hideExtraMenuFootersFooterStandard_v6" in js,
        "JS chama limpeza de rodapes extras do Menu": "hideExtraMenuFootersFooterStandard_v6(scopeEl);" in js,
        "CSS contem regra de ocultacao v6": "APPVERBO_ADMIN_TABLE_FOOTER_MENU_SOURCE_DEDUPE_V6_START" in css,
        "Template carrega cache buster v6": "admin-footer-standard-v6-menu-source-dedupe" in template,
        "Template remove modulo antigo ineficaz": "admin_menu_footer_dedupe_v1" not in template,
    }

    failed = [label for label, ok in checks.items() if not ok]

    if failed:
        raise RuntimeError("Validacoes falharam: " + ", ".join(failed))

    validate_no_mojibake_v6("static/js/modules/admin_table_footer_standard_v1.js")
    validate_no_mojibake_v6("static/css/modules/admin_table_footer_standard_v1.css")
    validate_no_mojibake_v6("templates/new_user.html")


####################################################################################
# (6) EXECUTAR
####################################################################################

def main_v6() -> None:
    patch_admin_table_footer_js_v6()
    patch_css_v6()
    patch_new_user_v6()
    validate_content_v6()

    print("OK: auto-injecao do rodape foi bloqueada no subprocesso Menu quando ja existe rodape.")
    print("OK: limpeza final mantem apenas o primeiro rodape nos cards Menus ativos/inativos.")
    print("OK: modulo antigo admin_menu_footer_dedupe_v1 removido do template.")
    print("OK: cache buster v6 aplicado.")


if __name__ == "__main__":
    main_v6()
