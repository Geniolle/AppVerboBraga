from __future__ import annotations

import re
from pathlib import Path


ROOT = Path.cwd()


####################################################################################
# (1) FUNCOES BASE
####################################################################################

def read_text_v3(relative_path: str) -> str:
    path = ROOT / relative_path

    if not path.exists():
        raise FileNotFoundError(f"Ficheiro nao encontrado: {relative_path}")

    return path.read_text(encoding="utf-8")


def write_text_v3(relative_path: str, content: str) -> None:
    path = ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)

    if not content.endswith("\n"):
        content += "\n"

    path.write_text(content, encoding="utf-8", newline="\n")


def require_v3(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def replace_marker_block_v3(content: str, start_marker: str, end_marker: str, new_block: str) -> str:
    start_index = content.find(start_marker)
    end_index = content.find(end_marker)

    if start_index >= 0 and end_index >= start_index:
        end_index += len(end_marker)
        return content[:start_index].rstrip() + "\n\n" + new_block.strip() + "\n\n" + content[end_index:].lstrip()

    return content.rstrip() + "\n\n" + new_block.strip() + "\n"


####################################################################################
# (2) ATUALIZAR CSS PARA ESCONDER APENAS O RODAPE DUPLICADO DO MENU
####################################################################################

def patch_css_v3() -> None:
    relative_path = "static/css/modules/admin_table_footer_standard_v1.css"
    content = read_text_v3(relative_path)

    block = """
/* APPVERBO_ADMIN_TABLE_FOOTER_MENU_DEDUPE_V3_START */

/*
  Correção específica do subprocesso Menu:
  quando o rodapé legado e o rodapé padrão aparecem no mesmo card,
  mantém o primeiro rodapé visível e oculta apenas a linha duplicada inferior.
*/

[data-admin-subprocess="menu"] [data-admin-table-footer-hidden-menu-duplicate-v3="1"],
#admin-menu-card [data-admin-table-footer-hidden-menu-duplicate-v3="1"],
[id*="menu"] [data-admin-table-footer-hidden-menu-duplicate-v3="1"] {
  display: none !important;
}

/* APPVERBO_ADMIN_TABLE_FOOTER_MENU_DEDUPE_V3_END */
"""

    content = replace_marker_block_v3(
        content,
        "/* APPVERBO_ADMIN_TABLE_FOOTER_MENU_DEDUPE_V3_START */",
        "/* APPVERBO_ADMIN_TABLE_FOOTER_MENU_DEDUPE_V3_END */",
        block,
    )

    write_text_v3(relative_path, content)


####################################################################################
# (3) ATUALIZAR JS PARA REMOVER SOMENTE A LINHA DUPLICADA INFERIOR DO MENU
####################################################################################

def patch_js_v3() -> None:
    relative_path = "static/js/modules/admin_table_footer_standard_v1.js"
    content = read_text_v3(relative_path)

    menu_dedupe_block = r'''
  //###################################################################################
  // (8.1) DEDUPE ESPECIFICO DO RODAPE DO SUBPROCESSO MENU
  //###################################################################################

  function isMenuFooterCard_v3(cardEl) {
    if (!cardEl) {
      return false;
    }

    if (cardEl.getAttribute("data-admin-subprocess") === "menu") {
      return true;
    }

    if (cardEl.id && cardEl.id.toLowerCase().indexOf("menu") >= 0) {
      return true;
    }

    const titleEl = cardEl.querySelector("h2, h3");
    const titleText = normalizeText_v2(titleEl ? titleEl.textContent : "");

    return titleText.indexOf("menus ativos") >= 0 || titleText.indexOf("menus inativos") >= 0;
  }

  function getMenuFooterCandidates_v3(cardEl) {
    if (!cardEl) {
      return [];
    }

    const selector = [
      "[data-admin-table-footer-standard-v1='1']",
      ".admin-table-footer-standard-v1",
      ".table-limiter",
      "[id$='-limiter']"
    ].join(",");

    const candidates = Array.from(cardEl.querySelectorAll(selector));
    const unique = [];

    candidates.forEach(function (element) {
      const ownFooter = element.closest(selector);

      if (ownFooter !== element) {
        return;
      }

      if (unique.indexOf(element) < 0) {
        unique.push(element);
      }
    });

    unique.sort(function (leftEl, rightEl) {
      if (leftEl === rightEl) {
        return 0;
      }

      return leftEl.compareDocumentPosition(rightEl) & Node.DOCUMENT_POSITION_FOLLOWING ? -1 : 1;
    });

    return unique;
  }

  function showMenuFooter_v3(footerEl) {
    if (!footerEl) {
      return;
    }

    footerEl.removeAttribute("data-admin-table-footer-hidden-menu-duplicate-v3");

    if (footerEl.getAttribute("data-admin-table-footer-hidden-duplicate-v2") === "1") {
      footerEl.removeAttribute("data-admin-table-footer-hidden-duplicate-v2");
    }

    if (footerEl.style && footerEl.style.display === "none") {
      footerEl.style.display = "";
    }
  }

  function hideMenuFooterDuplicate_v3(footerEl) {
    if (!footerEl) {
      return;
    }

    footerEl.setAttribute("data-admin-table-footer-hidden-menu-duplicate-v3", "1");
    footerEl.style.display = "none";
  }

  function hideDuplicateMenuFooters_v3(rootEl) {
    const scopeEl = rootEl || document;
    const cards = Array.from(scopeEl.querySelectorAll(".card, .admin-subprocess-table-card-v1, section"));

    cards.forEach(function (cardEl) {
      if (!isMenuFooterCard_v3(cardEl)) {
        return;
      }

      const footers = getMenuFooterCandidates_v3(cardEl);

      if (footers.length <= 1) {
        if (footers.length === 1) {
          showMenuFooter_v3(footers[0]);
        }

        return;
      }

      footers.forEach(function (footerEl, index) {
        if (index === 0) {
          showMenuFooter_v3(footerEl);
          return;
        }

        hideMenuFooterDuplicate_v3(footerEl);
      });
    });
  }
'''

    content = replace_marker_block_v3(
        content,
        "  //###################################################################################\n  // (8.1) DEDUPE ESPECIFICO DO RODAPE DO SUBPROCESSO MENU",
        "  //###################################################################################\n  // (8.1) DEDUPE ESPECIFICO DO RODAPE DO SUBPROCESSO MENU_END",
        menu_dedupe_block + "\n  //###################################################################################\n  // (8.1) DEDUPE ESPECIFICO DO RODAPE DO SUBPROCESSO MENU_END",
    )

    if "hideDuplicateMenuFooters_v3(scopeEl);" not in content:
        old = """    ensureStandardFootersForTables_v2(scopeEl);
    hideLegacyFootersWhenStandardExists_v2(scopeEl);
    hideDuplicateStandardFooters_v2(scopeEl);"""

        new = """    ensureStandardFootersForTables_v2(scopeEl);
    hideLegacyFootersWhenStandardExists_v2(scopeEl);
    hideDuplicateStandardFooters_v2(scopeEl);
    hideDuplicateMenuFooters_v3(scopeEl);"""

        require_v3(
            old in content,
            "ERRO: bloco initializeFooters_v2 esperado nao encontrado no JS.",
        )

        content = content.replace(old, new, 1)

    if "hideDuplicateMenuFooters_v3: hideDuplicateMenuFooters_v3" not in content:
        content = content.replace(
            "initializeFooters_v2: initializeFooters_v2",
            "initializeFooters_v2: initializeFooters_v2,\n    hideDuplicateMenuFooters_v3: hideDuplicateMenuFooters_v3",
            1,
        )

    write_text_v3(relative_path, content)


####################################################################################
# (4) ATUALIZAR CACHE BUSTER
####################################################################################

def patch_new_user_cache_v3() -> None:
    relative_path = "templates/new_user.html"
    content = read_text_v3(relative_path)

    css_tag = '<link rel="stylesheet" href="/static/css/modules/admin_table_footer_standard_v1.css?v=20260516-admin-footer-standard-v5-menu-dedupe">'
    js_tag = '<script src="/static/js/modules/admin_table_footer_standard_v1.js?v=20260516-admin-footer-standard-v5-menu-dedupe" defer></script>'

    if "admin_table_footer_standard_v1.css" in content:
        content = re.sub(
            r'<link rel="stylesheet" href="/static/css/modules/admin_table_footer_standard_v1\.css\?v=[^"]*">',
            css_tag,
            content,
            count=1,
        )
    else:
        content = content.replace("{% block head_extra %}", "{% block head_extra %}\n" + css_tag, 1)

    if "admin_table_footer_standard_v1.js" in content:
        content = re.sub(
            r'<script src="/static/js/modules/admin_table_footer_standard_v1\.js\?v=[^"]*" defer></script>',
            js_tag,
            content,
            count=1,
        )
    else:
        content = content.replace("{% endblock %}", js_tag + "\n{% endblock %}", 1)

    write_text_v3(relative_path, content)


####################################################################################
# (5) VALIDAR CONTEUDO
####################################################################################

def validate_no_mojibake_v3(relative_path: str) -> None:
    content = read_text_v3(relative_path)
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


def validate_content_v3() -> None:
    css = read_text_v3("static/css/modules/admin_table_footer_standard_v1.css")
    js = read_text_v3("static/js/modules/admin_table_footer_standard_v1.js")
    template = read_text_v3("templates/new_user.html")

    checks = {
        "CSS contem bloco especifico do Menu": "APPVERBO_ADMIN_TABLE_FOOTER_MENU_DEDUPE_V3_START" in css,
        "CSS contem atributo de duplicado do Menu": "data-admin-table-footer-hidden-menu-duplicate-v3" in css,
        "JS contem funcao hideDuplicateMenuFooters_v3": "function hideDuplicateMenuFooters_v3" in js,
        "JS chama hideDuplicateMenuFooters_v3": "hideDuplicateMenuFooters_v3(scopeEl);" in js,
        "JS identifica Menus ativos": "menus ativos" in js,
        "JS identifica Menus inativos": "menus inativos" in js,
        "new_user carrega cache buster v5": "admin-footer-standard-v5-menu-dedupe" in template,
    }

    failed = [label for label, ok in checks.items() if not ok]

    if failed:
        raise RuntimeError("Validacoes falharam: " + ", ".join(failed))

    for relative_path in [
        "static/css/modules/admin_table_footer_standard_v1.css",
        "static/js/modules/admin_table_footer_standard_v1.js",
        "templates/new_user.html",
    ]:
        validate_no_mojibake_v3(relative_path)


####################################################################################
# (6) EXECUTAR
####################################################################################

def main_v3() -> None:
    patch_css_v3()
    patch_js_v3()
    patch_new_user_cache_v3()
    validate_content_v3()

    print("OK: dedupe especifico do rodape do subprocesso Menu aplicado.")
    print("OK: a primeira linha do rodape do Menu sera mantida.")
    print("OK: a linha duplicada inferior do Menu sera ocultada.")
    print("OK: cache buster atualizado para v5.")


if __name__ == "__main__":
    main_v3()
