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


def main() -> int:
    text = read(PAGE_HANDLER)
    original = text

    # Remove definicoes duplicadas antigas, se existirem.
    text = re.sub(
        r'\n\s*clean_settings_edit_key_for_admin_refresh\s*=\s*str\(settings_edit_key or ""\)\.strip\(\)\n',
        "\n",
        text,
    )
    text = re.sub(
        r'\n\s*clean_settings_edit_key_for_admin_refresh\s*=\s*str\(request\.query_params\.get\("settings_edit_key", ""\) or ""\)\.strip\(\)\n',
        "\n",
        text,
    )

    definition = (
        '    # APPVERBO_FIX_CLEAN_SETTINGS_EDIT_KEY_REFRESH_V1_START\n'
        '    clean_settings_edit_key_for_admin_refresh = str(settings_edit_key or "").strip()\n'
        '    # APPVERBO_FIX_CLEAN_SETTINGS_EDIT_KEY_REFRESH_V1_END\n'
    )

    # Preferir inserir dentro do bloco de inferencia de refresh das sessoes,
    # antes da primeira utilizacao em bool(clean_settings_edit_key_for_admin_refresh).
    usage = 'or bool(clean_settings_edit_key_for_admin_refresh)'

    usage_index = text.find(usage)

    if usage_index < 0:
        print("AVISO: uso de clean_settings_edit_key_for_admin_refresh nao encontrado. Nada a corrigir.")
        return 0

    if "APPVERBO_FIX_CLEAN_SETTINGS_EDIT_KEY_REFRESH_V1_START" not in text:
        # Inserir logo depois da definicao de clean_settings_tab_for_admin_refresh,
        # se existir.
        anchor_pattern = (
            r'    clean_settings_tab_for_admin_refresh = \(\n'
            r'        str\(settings_tab or ""\)\n'
            r'        \.strip\(\)\n'
            r'        \.lower\(\)\n'
            r'        \.replace\("_", "-"\)\n'
            r'    \)\n'
        )

        match = re.search(anchor_pattern, text)

        if match:
            text = text[:match.end()] + definition + text[match.end():]
        else:
            # Fallback seguro: inserir imediatamente antes da primeira utilizacao.
            line_start = text.rfind("\n", 0, usage_index)
            if line_start < 0:
                raise RuntimeError("Nao foi possivel encontrar linha antes do uso da variavel.")
            text = text[:line_start + 1] + definition + text[line_start + 1:]

    # Garantir que a definicao aparece antes do primeiro uso.
    definition_index = text.find("clean_settings_edit_key_for_admin_refresh =")
    usage_index = text.find(usage)

    if definition_index < 0:
        raise RuntimeError("Definicao de clean_settings_edit_key_for_admin_refresh nao foi criada.")

    if usage_index >= 0 and definition_index > usage_index:
        raise RuntimeError("Definicao ficou depois do uso. Correcao cancelada.")

    write(PAGE_HANDLER, text)

    if text != original:
        print("OK: clean_settings_edit_key_for_admin_refresh definido antes do uso.")
    else:
        print("OK: ficheiro ja estava consistente.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
