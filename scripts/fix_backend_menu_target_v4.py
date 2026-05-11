# -*- coding: utf-8 -*-
from __future__ import annotations

import re
import sys
from pathlib import Path


PAGE_HANDLER = Path("appverbo/routes/profile/page_handler.py")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: Path, content: str) -> None:
    path.write_text(content.rstrip() + "\n", encoding="utf-8", newline="\n")


def ensure_menu_in_set(text: str, phrase: str) -> str:
    idx = text.find(phrase)

    if idx < 0:
        raise RuntimeError(f"Nao foi possivel localizar: {phrase}")

    open_idx = text.find("{", idx)
    close_idx = text.find("}", open_idx)

    if open_idx < 0 or close_idx < 0:
        raise RuntimeError(f"Nao foi possivel localizar set apos: {phrase}")

    body = text[open_idx + 1:close_idx]

    if '"menu"' in body or "'menu'" in body:
        return text

    body = body.rstrip() + ',\n        "menu",\n    '

    return text[:open_idx + 1] + body + text[close_idx:]


def remove_old_blocks(text: str) -> str:
    markers = [
        "APPVERBO_ADMIN_MENU_NATIVE_TARGET_RESOLVE_V1",
        "APPVERBO_ADMIN_MENU_NATIVE_TARGET_RESOLVE_V2",
        "APPVERBO_ADMIN_MENU_NATIVE_TARGET_RESOLVE_V3",
        "APPVERBO_ADMIN_MENU_NATIVE_TARGET_RESOLVE_V4",
        "APPVERBO_ADMIN_MENU_NATIVE_POST_CONTEXT_V1",
        "APPVERBO_ADMIN_MENU_NATIVE_POST_CONTEXT_V2",
        "APPVERBO_ADMIN_MENU_NATIVE_POST_CONTEXT_V3",
        "APPVERBO_ADMIN_MENU_NATIVE_POST_CONTEXT_V4",
    ]

    for marker in markers:
        text = re.sub(
            rf"(?s)\n?\s*# {marker}_START.*?# {marker}_END\n?",
            "\n",
            text,
        )

    return text


def force_target_block(text: str) -> str:
    match = re.search(
        r'(?s)(    if clean_menu_key == "administrativo":\n)(.*?)(    if clean_menu_key == "configuracao":)',
        text,
    )

    if not match:
        raise RuntimeError("Nao foi possivel localizar o bloco administrativo em _resolve_initial_menu_target.")

    header = match.group(1)
    body = match.group(2)
    next_block = match.group(3)

    target_block = (
        '        # APPVERBO_ADMIN_MENU_NATIVE_TARGET_RESOLVE_V4_START\n'
        '        if resolved_admin_tab == "menu":\n'
        '            return "#settings-card", ""\n'
        '        # APPVERBO_ADMIN_MENU_NATIVE_TARGET_RESOLVE_V4_END\n'
    )

    body = target_block + body.lstrip("\n")

    return text[:match.start()] + header + body + next_block + text[match.end():]


def force_context_block(text: str) -> str:
    context_block = (
        '\n    # APPVERBO_ADMIN_MENU_NATIVE_POST_CONTEXT_V4_START\n'
        '    if resolved_admin_tab == "menu":\n'
        '        initial_menu_target = "#settings-card"\n'
        '        initial_dynamic_process_section = ""\n'
        '        clean_dynamic_section_from_query = ""\n'
        '    # APPVERBO_ADMIN_MENU_NATIVE_POST_CONTEXT_V4_END\n\n'
    )

    markers = [
        "    # APPVERBO_ADMIN_SUBPROCESS_STATE_SESSOES_V2_START",
        "    context = {",
    ]

    for marker in markers:
        pos = text.find(marker)

        if pos >= 0:
            return text[:pos] + context_block + text[pos:]

    raise RuntimeError("Nao foi possivel localizar ponto seguro para inserir contexto do Menu.")


def main() -> int:
    text = read(PAGE_HANDLER)

    text = remove_old_blocks(text)

    text = ensure_menu_in_set(
        text,
        "if resolved_admin_tab not in",
    )

    text = ensure_menu_in_set(
        text,
        "if clean_settings_tab not in",
    )

    text = force_target_block(text)
    text = force_context_block(text)

    write(PAGE_HANDLER, text)

    print("OK: backend Menu corrigido para settings-card.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
