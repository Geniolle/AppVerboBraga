from pathlib import Path
import re

PAGE_HANDLER = Path("appverbo/routes/profile/page_handler.py")
TOP_MENU_JS = Path("static/js/modules/top_menu_active_v1.js")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8", newline="\n")


def ensure_page_handler_helper(text: str) -> str:
    marker = "APPVERBO_ADMIN_TAB_MENU_CANONICAL_V1_START"

    if marker in text:
        return text

    anchor = "\n\n# APPVERBO_SESSOES_BACKEND_SPLIT_ENTIDADE_V22_START\n"

    helper = '''

# APPVERBO_ADMIN_TAB_MENU_CANONICAL_V1_START

def _normalize_admin_tab_menu_v1(raw_admin_tab: object) -> str:
    clean_admin_tab = str(raw_admin_tab or "").strip().lower()

    legacy_aliases = {
        "contas": "menu",
        "definicoes": "menu",
    }

    clean_admin_tab = legacy_aliases.get(clean_admin_tab, clean_admin_tab)

    if clean_admin_tab not in {"utilizador", "entidade", "menu", "sessoes"}:
        return "entidade"

    return clean_admin_tab

# APPVERBO_ADMIN_TAB_MENU_CANONICAL_V1_END
'''

    if anchor not in text:
        raise RuntimeError("Anchor não encontrado para inserir helper em page_handler.py")

    return text.replace(anchor, helper + anchor, 1)


def replace_admin_tab_normalization(text: str) -> str:
    replacement = '    resolved_admin_tab = _normalize_admin_tab_menu_v1(admin_tab)\n'

    if replacement in text:
        return text

    pattern = (
        r'    resolved_admin_tab = .*?\n'
        r'(?=    parsed_entity_edit_id:)'
    )

    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.DOTALL)

    if count != 1:
        raise RuntimeError(
            "Não foi possível substituir o bloco de normalização de admin_tab antes de parsed_entity_edit_id."
        )

    return updated


def replace_initial_menu_target(text: str) -> str:
    new_block = '''        if resolved_admin_tab in {"menu", "contas", "definicoes"}:
            return "#admin-account-status-card", ""
'''

    if new_block in text:
        return text

    old_block = '''        if resolved_admin_tab == "contas":
            return "#admin-account-status-card", ""
'''

    if old_block in text:
        return text.replace(old_block, new_block, 1)

    pattern = (
        r'        if resolved_admin_tab == "contas":\n'
        r'            return "#admin-account-status-card", ""\n'
    )

    updated, count = re.subn(pattern, new_block, text, count=1)

    if count != 1:
        raise RuntimeError("Não foi possível localizar target do subprocesso Menu em page_handler.py")

    return updated


def patch_page_handler() -> None:
    text = read_text(PAGE_HANDLER)
    text = ensure_page_handler_helper(text)
    text = replace_admin_tab_normalization(text)
    text = replace_initial_menu_target(text)
    write_text(PAGE_HANDLER, text)


def patch_top_menu_js() -> None:
    text = read_text(TOP_MENU_JS)

    text = text.replace(
        '      menu: "/users/new?menu=administrativo&admin_tab=contas",',
        '      menu: "/users/new?menu=administrativo&admin_tab=menu",',
        1,
    )

    old_expected_tab_block = '''    if (adminTab === "contas" || adminTab === "definicoes") {
      return "menu";
    }
'''

    new_expected_tab_block = '''    if (adminTab === "menu" || adminTab === "contas" || adminTab === "definicoes") {
      return "menu";
    }
'''

    if old_expected_tab_block in text:
        text = text.replace(old_expected_tab_block, new_expected_tab_block, 1)
    elif new_expected_tab_block not in text:
        raise RuntimeError("Bloco de compatibilidade adminTab Menu não encontrado em top_menu_active_v1.js")

    write_text(TOP_MENU_JS, text)


def validate_files() -> None:
    page_text = read_text(PAGE_HANDLER)
    js_text = read_text(TOP_MENU_JS)

    required_page_snippets = [
        'def _normalize_admin_tab_menu_v1(raw_admin_tab: object) -> str:',
        '"contas": "menu"',
        '"definicoes": "menu"',
        'if clean_admin_tab not in {"utilizador", "entidade", "menu", "sessoes"}:',
        'resolved_admin_tab = _normalize_admin_tab_menu_v1(admin_tab)',
        'if resolved_admin_tab in {"menu", "contas", "definicoes"}:',
    ]

    required_js_snippets = [
        'menu: "/users/new?menu=administrativo&admin_tab=menu",',
        'adminTab === "menu"',
        'adminTab === "contas"',
        'adminTab === "definicoes"',
    ]

    missing_page = [snippet for snippet in required_page_snippets if snippet not in page_text]
    missing_js = [snippet for snippet in required_js_snippets if snippet not in js_text]

    if missing_page:
        raise RuntimeError("Validação falhou em page_handler.py: " + " | ".join(missing_page))

    if missing_js:
        raise RuntimeError("Validação falhou em top_menu_active_v1.js: " + " | ".join(missing_js))


def main() -> None:
    patch_page_handler()
    patch_top_menu_js()
    validate_files()
    print("OK: patch admin_tab=menu canonico v2 aplicado e validado.")


if __name__ == "__main__":
    main()
