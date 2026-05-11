# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path


PAGE_HANDLER = Path("appverbo/routes/profile/page_handler.py")


def read_text_no_bom(path: Path) -> str:
    content = path.read_text(encoding="utf-8-sig")
    return content.lstrip("\ufeff")


def write_text_no_bom(path: Path, content: str) -> None:
    content = content.lstrip("\ufeff").rstrip() + "\n"
    path.write_text(content, encoding="utf-8", newline="\n")


def remove_bad_clean_settings_blocks(content: str) -> str:
    patterns = [
        r'\n[ \t]*# APPVERBO_FIX_CLEAN_SETTINGS_EDIT_KEY_REFRESH_V1_START\n'
        r'[ \t]*clean_settings_edit_key_for_admin_refresh\s*=\s*str\(settings_edit_key or ""\)\.strip\(\)\n'
        r'[ \t]*# APPVERBO_FIX_CLEAN_SETTINGS_EDIT_KEY_REFRESH_V1_END\n',

        r'\n[ \t]*# APPVERBO_FIX_CLEAN_SETTINGS_EDIT_KEY_REFRESH_V2_START\n'
        r'[ \t]*clean_settings_edit_key_for_admin_refresh\s*=\s*str\(settings_edit_key or ""\)\.strip\(\)\n'
        r'[ \t]*# APPVERBO_FIX_CLEAN_SETTINGS_EDIT_KEY_REFRESH_V2_END\n',

        r'\n[ \t]*# APPVERBO_FIX_CLEAN_SETTINGS_EDIT_KEY_REFRESH_V3_START\n'
        r'[ \t]*clean_settings_edit_key_for_admin_refresh\s*=\s*str\(settings_edit_key or ""\)\.strip\(\)\n'
        r'[ \t]*# APPVERBO_FIX_CLEAN_SETTINGS_EDIT_KEY_REFRESH_V3_END\n',
    ]

    for pattern in patterns:
        content = re.sub(pattern, "\n", content)

    content = re.sub(
        r'(?m)^    clean_settings_edit_key_for_admin_refresh\s*=\s*str\(settings_edit_key or ""\)\.strip\(\)\n',
        "",
        content,
    )

    return content


def find_end_of_multiline_assignment(content: str, variable_name: str) -> int:
    pattern = re.compile(rf'(?m)^    {re.escape(variable_name)}\s*=')
    match = pattern.search(content)

    if not match:
        return -1

    line_start = match.start()
    position = line_start
    balance = 0

    while position < len(content):
        next_newline = content.find("\n", position)

        if next_newline < 0:
            next_newline = len(content)
            line = content[position:next_newline]
            line_end = next_newline
        else:
            line = content[position:next_newline + 1]
            line_end = next_newline + 1

        clean_line = line.split("#", 1)[0]
        balance += clean_line.count("(")
        balance -= clean_line.count(")")

        if line_end > match.end() and balance <= 0:
            return line_end

        if next_newline >= len(content):
            break

        position = line_end

    return -1


def ensure_clean_settings_edit_key_definition(content: str) -> str:
    usage_index = content.find("or bool(clean_settings_edit_key_for_admin_refresh)")

    if usage_index < 0:
        return content

    definition_index = content.find("clean_settings_edit_key_for_admin_refresh =")

    if 0 <= definition_index < usage_index:
        return content

    insert_position = find_end_of_multiline_assignment(
        content,
        "clean_settings_tab_for_admin_refresh",
    )

    if insert_position < 0 or insert_position > usage_index:
        raise RuntimeError(
            "Nao foi possivel localizar ponto seguro apos clean_settings_tab_for_admin_refresh."
        )

    definition = (
        "\n"
        "    # APPVERBO_FIX_CLEAN_SETTINGS_EDIT_KEY_REFRESH_V3_START\n"
        "    clean_settings_edit_key_for_admin_refresh = str(settings_edit_key or \"\").strip()\n"
        "    # APPVERBO_FIX_CLEAN_SETTINGS_EDIT_KEY_REFRESH_V3_END\n"
    )

    return content[:insert_position] + definition + content[insert_position:]


def ensure_menu_backend_context(content: str) -> str:
    if 'return "#settings-card", ""' not in content:
        raise RuntimeError("Target settings-card do Menu nao encontrado no backend.")

    if 'initial_menu_target = "#settings-card"' not in content:
        raise RuntimeError("Contexto initial_menu_target do Menu nao encontrado no backend.")

    if '"menu"' not in content:
        raise RuntimeError("admin_tab menu nao encontrado no backend.")

    return content


def validate_content(content: str) -> None:
    if content.startswith("\ufeff"):
        raise RuntimeError("BOM U+FEFF ainda existe no inicio do page_handler.py.")

    ast.parse(content)

    usage_index = content.find("or bool(clean_settings_edit_key_for_admin_refresh)")
    definition_index = content.find("clean_settings_edit_key_for_admin_refresh =")

    if usage_index >= 0:
        if definition_index < 0:
            raise RuntimeError("clean_settings_edit_key_for_admin_refresh nao foi definida.")

        if definition_index > usage_index:
            raise RuntimeError("clean_settings_edit_key_for_admin_refresh ficou depois do uso.")

    ensure_menu_backend_context(content)


def main() -> int:
    content = read_text_no_bom(PAGE_HANDLER)

    content = remove_bad_clean_settings_blocks(content)
    content = ensure_clean_settings_edit_key_definition(content)
    content = ensure_menu_backend_context(content)

    validate_content(content)

    write_text_no_bom(PAGE_HANDLER, content)

    print("OK: BOM removido, sintaxe corrigida e Menu preservado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
