from __future__ import annotations

import re
from pathlib import Path


####################################################################################
# (1) CONFIGURACAO
####################################################################################

PROJECT_ROOT = Path.cwd()
PROFILE_HANDLERS_PATH = PROJECT_ROOT / "appverbo" / "routes" / "profile" / "profile_handlers.py"


####################################################################################
# (2) FUNCOES AUXILIARES
####################################################################################

def read_text_v1(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text_v1(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def remove_marker_block_v1(content: str, marker_start: str, marker_end: str) -> str:
    pattern = re.compile(
        r"^[ \t]*#\s*" + re.escape(marker_start) + r".*?"
        + r"^[ \t]*#\s*" + re.escape(marker_end) + r"[^\r\n]*(?:\r?\n)?",
        flags=re.DOTALL | re.MULTILINE,
    )
    return pattern.sub("", content)


def remove_dangling_write_v1_calls(content: str) -> str:
    lines = content.splitlines(keepends=True)
    output: list[str] = []
    index = 0

    while index < len(lines):
        line = lines[index]

        if "_write_meu_perfil_save_debug_log_v1(" not in line:
            output.append(line)
            index += 1
            continue

        start_indent = len(line) - len(line.lstrip(" "))
        paren_balance = line.count("(") - line.count(")")
        index += 1

        while index < len(lines):
            current = lines[index]
            paren_balance += current.count("(") - current.count(")")

            current_stripped = current.strip()
            current_indent = len(current) - len(current.lstrip(" "))

            index += 1

            if paren_balance <= 0:
                break

            if (
                current_stripped.startswith(("except ", "finally:", "elif ", "else:"))
                and current_indent <= start_indent
            ):
                index -= 1
                break

        continue

    return "".join(output)


####################################################################################
# (3) APLICAR LIMPEZA
####################################################################################

def main() -> None:
    if not PROFILE_HANDLERS_PATH.exists():
        raise FileNotFoundError(f"Ficheiro nao encontrado: {PROFILE_HANDLERS_PATH}")

    content = read_text_v1(PROFILE_HANDLERS_PATH)

    marker_pairs = [
        ("APPVERBO_MEU_PERFIL_SAVE_LOGGER_V1_START", "APPVERBO_MEU_PERFIL_SAVE_LOGGER_V1_END"),
        ("APPVERBO_MEU_PERFIL_SAVE_LOGGER_FORM_RECEIVED_V1_START", "APPVERBO_MEU_PERFIL_SAVE_LOGGER_FORM_RECEIVED_V1_END"),
        ("APPVERBO_MEU_PERFIL_SAVE_LOGGER_QUANTITY_CONTEXT_V1_START", "APPVERBO_MEU_PERFIL_SAVE_LOGGER_QUANTITY_CONTEXT_V1_END"),
        ("APPVERBO_MEU_PERFIL_SAVE_LOGGER_BEFORE_UPDATE_V1_START", "APPVERBO_MEU_PERFIL_SAVE_LOGGER_BEFORE_UPDATE_V1_END"),
        ("APPVERBO_MEU_PERFIL_SAVE_LOGGER_AFTER_COMMIT_V1_START", "APPVERBO_MEU_PERFIL_SAVE_LOGGER_AFTER_COMMIT_V1_END"),
    ]

    for marker_start, marker_end in marker_pairs:
        content = remove_marker_block_v1(content, marker_start, marker_end)

    content = remove_dangling_write_v1_calls(content)

    forbidden = [
        "_write_meu_perfil_save_debug_log_v1",
        "APPVERBO_MEU_PERFIL_SAVE_LOGGER_V1",
        "APPVERBO_MEU_PERFIL_SAVE_LOGGER_FORM_RECEIVED_V1",
        "APPVERBO_MEU_PERFIL_SAVE_LOGGER_QUANTITY_CONTEXT_V1",
        "APPVERBO_MEU_PERFIL_SAVE_LOGGER_BEFORE_UPDATE_V1",
        "APPVERBO_MEU_PERFIL_SAVE_LOGGER_AFTER_COMMIT_V1",
    ]

    still_present = [item for item in forbidden if item in content]

    if still_present:
        raise RuntimeError("Ainda existem residuos do logger v1: " + ", ".join(still_present))

    write_text_v1(PROFILE_HANDLERS_PATH, content)

    print("OK: residuos do logger v1 removidos.")


if __name__ == "__main__":
    main()
