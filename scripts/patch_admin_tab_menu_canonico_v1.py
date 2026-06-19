from pathlib import Path

PAGE_HANDLER = Path("appverbo/routes/profile/page_handler.py")
TOP_MENU_JS = Path("static/js/modules/top_menu_active_v1.js")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8", newline="\n")


def patch_page_handler() -> None:
    text = read_text(PAGE_HANDLER)

    helper_marker = "APPVERBO_ADMIN_TAB_MENU_CANONICAL_V1_START"

    if helper_marker not in text:
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
            raise RuntimeError("Anchor não encontrado para inserir _normalize_admin_tab_menu_v1 em page_handler.py")

        text = text.replace(anchor, helper + anchor, 1)

    old_admin_tab_block = '''    resolved_admin_tab = admin_tab.strip().lower()
    if resolved_admin_tab not in {"utilizador", "entidade", "contas", "definicoes", "sessoes"}:
        resolved_admin_tab = "entidade"
    if resolved_admin_tab == "definicoes":
        resolved_admin_tab = "contas"
'''

    new_admin_tab_block = '''    resolved_admin_tab = _normalize_admin_tab_menu_v1(admin_tab)
'''

    if old_admin_tab_block in text:
        text = text.replace(old_admin_tab_block, new_admin_tab_block, 1)
    elif new_admin_tab_block not in text:
        raise RuntimeError("Bloco de normalização de admin_tab não encontrado em page_handler.py")

    old_target_block = '''        if resolved_admin_tab == "contas":
            return "#admin-account-status-card", ""
'''

    new_target_block = '''        if resolved_admin_tab in {"menu", "contas", "definicoes"}:
            return "#admin-account-status-card", ""
'''

    if old_target_block in text:
        text = text.replace(old_target_block, new_target_block, 1)
    elif new_target_block not in text:
        raise RuntimeError("Bloco de target do subprocesso Menu não encontrado em page_handler.py")

    write_text(PAGE_HANDLER, text)


def patch_top_menu_js() -> None:
    text = read_text(TOP_MENU_JS)

    old_menu_url = '      menu: "/users/new?menu=administrativo&admin_tab=contas",'
    new_menu_url = '      menu: "/users/new?menu=administrativo&admin_tab=menu",'

    if old_menu_url in text:
        text = text.replace(old_menu_url, new_menu_url, 1)
    elif new_menu_url not in text:
        raise RuntimeError("URL da aba Menu não encontrada em top_menu_active_v1.js")

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


def main() -> None:
    patch_page_handler()
    patch_top_menu_js()
    print("OK: patch admin_tab=menu canonico aplicado com compatibilidade para contas/definicoes.")


if __name__ == "__main__":
    main()
