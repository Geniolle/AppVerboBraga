# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path


PAGE_HANDLER = Path("appverbo/routes/profile/page_handler.py")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: Path, content: str) -> None:
    path.write_text(content.rstrip() + "\n", encoding="utf-8", newline="\n")


def remove_bad_insertions(text: str) -> str:
    # Remove bloco inserido no meio do elif, que causou SyntaxError.
    text = re.sub(
        r'\n[ \t]*# APPVERBO_FIX_CLEAN_SETTINGS_EDIT_KEY_REFRESH_V1_START\n'
        r'[ \t]*clean_settings_edit_key_for_admin_refresh\s*=\s*str\(settings_edit_key or ""\)\.strip\(\)\n'
        r'[ \t]*# APPVERBO_FIX_CLEAN_SETTINGS_EDIT_KEY_REFRESH_V1_END\n',
        "\n",
        text,
    )

    text = re.sub(
        r'\n[ \t]*# APPVERBO_FIX_CLEAN_SETTINGS_EDIT_KEY_REFRESH_V2_START\n'
        r'[ \t]*clean_settings_edit_key_for_admin_refresh\s*=\s*str\(settings_edit_key or ""\)\.strip\(\)\n'
        r'[ \t]*# APPVERBO_FIX_CLEAN_SETTINGS_EDIT_KEY_REFRESH_V2_END\n',
        "\n",
        text,
    )

    # Remove qualquer atribuição solta anterior para reinserir num ponto seguro.
    text = re.sub(
        r'(?m)^    clean_settings_edit_key_for_admin_refresh\s*=\s*str\(settings_edit_key or ""\)\.strip\(\)\n',
        "",
        text,
    )

    return text


def find_assignment_insert_position(text: str, variable_name: str, usage_index: int) -> int:
    pattern = re.compile(rf'(?m)^    {re.escape(variable_name)}\s*=')
    match = pattern.search(text)

    if not match:
        return -1

    if match.start() > usage_index:
        return -1

    line_start = text.rfind("\n", 0, match.start()) + 1
    scan_text = text[line_start:usage_index]
    lines = scan_text.splitlines(keepends=True)

    balance = 0
    insert_offset = 0

    for line in lines:
        insert_offset += len(line)
        balance += line.count("(")
        balance -= line.count(")")

        if insert_offset > 0 and balance <= 0:
            return line_start + insert_offset

    return line_start + insert_offset


def ensure_definition_before_usage(text: str) -> str:
    usage = "clean_settings_edit_key_for_admin_refresh"

    usage_match = re.search(
        r'or bool\(clean_settings_edit_key_for_admin_refresh\)',
        text,
    )

    if not usage_match:
        return text

    usage_index = usage_match.start()

    existing_definition = text.find("clean_settings_edit_key_for_admin_refresh =")

    if 0 <= existing_definition < usage_index:
        return text

    insert_position = find_assignment_insert_position(
        text,
        "clean_settings_tab_for_admin_refresh",
        usage_index,
    )

    if insert_position < 0:
        # Fallback: inserir antes da linha do primeiro if/elif que usa clean_settings_tab_for_admin_refresh.
        line_start = text.rfind("\n", 0, usage_index) + 1

        while line_start > 0:
            previous_line_start = text.rfind("\n", 0, line_start - 1) + 1
            previous_line = text[previous_line_start:line_start]

            if previous_line.startswith("    if ") or previous_line.startswith("        if ") or previous_line.startswith("        elif "):
                line_start = previous_line_start
                break

            if previous_line_start == 0:
                break

            line_start = previous_line_start

        insert_position = line_start

    definition = (
        "\n"
        "    # APPVERBO_FIX_CLEAN_SETTINGS_EDIT_KEY_REFRESH_V2_START\n"
        "    clean_settings_edit_key_for_admin_refresh = str(settings_edit_key or \"\").strip()\n"
        "    # APPVERBO_FIX_CLEAN_SETTINGS_EDIT_KEY_REFRESH_V2_END\n"
    )

    return text[:insert_position] + definition + text[insert_position:]


def validate(text: str) -> None:
    ast.parse(text)

    definition_index = text.find("clean_settings_edit_key_for_admin_refresh =")
    usage_index = text.find("or bool(clean_settings_edit_key_for_admin_refresh)")

    if usage_index >= 0:
        if definition_index < 0:
            raise RuntimeError("clean_settings_edit_key_for_admin_refresh nao foi definida.")

        if definition_index > usage_index:
            raise RuntimeError("clean_settings_edit_key_for_admin_refresh ficou depois do uso.")

    if 'return "#settings-card", ""' not in text:
        raise RuntimeError("Target settings-card do Menu nao foi encontrado.")

    if 'initial_menu_target = "#settings-card"' not in text:
        raise RuntimeError("Contexto initial_menu_target do Menu nao foi encontrado.")


def main() -> int:
    text = read(PAGE_HANDLER)
    original = text

    text = remove_bad_insertions(text)
    text = ensure_definition_before_usage(text)
    validate(text)

    write(PAGE_HANDLER, text)

    if text != original:
        print("OK: sintaxe corrigida e variavel definida antes do uso.")
    else:
        print("OK: page_handler.py ja estava consistente.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
