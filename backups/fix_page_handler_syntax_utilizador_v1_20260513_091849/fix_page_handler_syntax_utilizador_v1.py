from __future__ import annotations

from pathlib import Path
import py_compile
import re
import sys


ROOT = Path.cwd()
PAGE_HANDLER = ROOT / "appverbo" / "routes" / "profile" / "page_handler.py"


####################################################################################
# (1) HELPERS
####################################################################################

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def compile_file(path: Path) -> tuple[bool, str]:
    try:
        py_compile.compile(str(path), doraise=True)
        return True, ""
    except py_compile.PyCompileError as exc:
        return False, str(exc)


def print_context(lines: list[str], center_index: int, radius: int = 12) -> None:
    start = max(0, center_index - radius)
    end = min(len(lines), center_index + radius + 1)

    for index in range(start, end):
        print(f"{index + 1:5}: {lines[index]}")


def strip_trailing_whitespace(text: str) -> str:
    lines = text.splitlines()
    return "\n".join(line.rstrip() for line in lines) + "\n"


def paren_balance(text: str) -> int:
    balance = 0
    in_single = False
    in_double = False
    escaped = False

    for char in text:
        if escaped:
            escaped = False
            continue

        if char == "\\":
            escaped = True
            continue

        if char == "'" and not in_double:
            in_single = not in_single
            continue

        if char == '"' and not in_single:
            in_double = not in_double
            continue

        if in_single or in_double:
            continue

        if char in "([{":
            balance += 1
        elif char in ")]}":
            balance -= 1

    return balance


####################################################################################
# (2) CORRIGIR CHAMADA ABERTA ANTES DO IF DO UTILIZADOR
####################################################################################

def fix_open_call_before_utilizador_if(text: str) -> tuple[str, bool]:
    lines = text.splitlines()
    changed = False

    target_indexes = [
        index
        for index, line in enumerate(lines)
        if 'if resolved_admin_tab == "utilizador":' in line
    ]

    if not target_indexes:
        raise RuntimeError('ERRO: não foi encontrado "if resolved_admin_tab == \\"utilizador\\"".')

    for if_index in target_indexes:
        search_start = max(0, if_index - 100)
        call_start = None

        for index in range(if_index - 1, search_start - 1, -1):
            line = lines[index]

            if "montar_estado_pagina_utilizador_v1(" in line:
                call_start = index
                break

            if "admin_subprocess_state_utilizador_v1" in line and "=" in line:
                call_start = index
                break

        if call_start is None:
            continue

        slice_text = "\n".join(lines[call_start:if_index])
        balance = paren_balance(slice_text)

        if balance > 0:
            indent = re.match(r"^(\s*)", lines[call_start]).group(1)
            close_lines = [indent + ")" for _ in range(balance)]
            lines[if_index:if_index] = close_lines
            changed = True
            print(
                "Correção aplicada: chamada aberta fechada antes do bloco "
                f"resolved_admin_tab == utilizador. Linha base: {call_start + 1}"
            )
            break

    return "\n".join(lines) + "\n", changed


####################################################################################
# (3) GARANTIR IMPORT DA FUNÇÃO ISOLADA
####################################################################################

def ensure_utilizador_page_import(text: str) -> tuple[str, bool]:
    import_line = (
        "from appverbo.admin_subprocesses.utilizador.pagina "
        "import montar_estado_pagina_utilizador_v1"
    )

    if import_line in text:
        return text, False

    lines = text.splitlines()

    insert_index = 0
    for index, line in enumerate(lines):
        if line.startswith("from ") or line.startswith("import "):
            insert_index = index + 1

    lines.insert(insert_index, import_line)
    print("Import isolado do subprocesso Utilizador adicionado.")
    return "\n".join(lines) + "\n", True


####################################################################################
# (4) FALLBACK SE A SINTAXE CONTINUAR QUEBRADA
####################################################################################

def fallback_rewrite_utilizador_state_block(text: str) -> tuple[str, bool]:
    lines = text.splitlines()

    if_indexes = [
        index
        for index, line in enumerate(lines)
        if 'if resolved_admin_tab == "utilizador":' in line
    ]

    if not if_indexes:
        raise RuntimeError('ERRO: fallback não encontrou bloco "if resolved_admin_tab == utilizador".')

    if_index = if_indexes[0]
    base_indent = re.match(r"^(\s*)", lines[if_index]).group(1)

    start = None
    for index in range(if_index, max(-1, if_index - 80), -1):
        line = lines[index]
        if "admin_subprocess_state_utilizador_v1" in line:
            start = index
            break

    if start is None:
        start = if_index

    end = if_index + 1
    while end < len(lines):
        line = lines[end]

        if not line.strip():
            end += 1
            continue

        indent_len = len(line) - len(line.lstrip(" "))

        if indent_len <= len(base_indent) and end > if_index + 1:
            break

        end += 1

    new_block = [
        base_indent + "admin_subprocess_state_utilizador_v1 = None",
        base_indent + 'if resolved_admin_tab == "utilizador":',
        base_indent + "    admin_subprocess_state_utilizador_v1 = montar_estado_pagina_utilizador_v1(",
        base_indent + "        db=db,",
        base_indent + "        request=request,",
        base_indent + "    )",
    ]

    lines[start:end] = new_block

    print(
        "Fallback aplicado: bloco do estado do subprocesso Utilizador foi reescrito "
        f"das linhas {start + 1} até {end}."
    )

    return "\n".join(lines) + "\n", True


####################################################################################
# (5) EXECUÇÃO
####################################################################################

def main() -> None:
    original_text = read_text(PAGE_HANDLER)
    text = strip_trailing_whitespace(original_text)

    text, import_changed = ensure_utilizador_page_import(text)
    text, call_changed = fix_open_call_before_utilizador_if(text)

    write_text(PAGE_HANDLER, text)

    ok, error = compile_file(PAGE_HANDLER)

    if not ok:
        print("")
        print("Primeira correção não foi suficiente. Erro atual:")
        print(error)

        lines = read_text(PAGE_HANDLER).splitlines()
        if "line " in error:
            match = re.search(r"line (\d+)", error)
            if match:
                print("")
                print("Contexto do erro atual:")
                print_context(lines, int(match.group(1)) - 1)

        text, fallback_changed = fallback_rewrite_utilizador_state_block(read_text(PAGE_HANDLER))
        write_text(PAGE_HANDLER, text)

        ok, error = compile_file(PAGE_HANDLER)

        if not ok:
            print("")
            print("ERRO: page_handler.py continua sem compilar após fallback.")
            print(error)

            lines = read_text(PAGE_HANDLER).splitlines()
            match = re.search(r"line (\d+)", error)
            if match:
                print("")
                print("Contexto final do erro:")
                print_context(lines, int(match.group(1)) - 1)

            raise SystemExit(1)

    print("OK: page_handler.py compila com sucesso.")

    final_text = read_text(PAGE_HANDLER)

    if "montar_estado_pagina_utilizador_v1" not in final_text:
        raise RuntimeError("ERRO: função isolada montar_estado_pagina_utilizador_v1 não está referenciada.")

    if 'if resolved_admin_tab == "utilizador":' not in final_text:
        raise RuntimeError("ERRO: bloco do admin_tab utilizador não existe.")

    if final_text != original_text:
        print("OK: page_handler.py foi alterado.")
    else:
        print("OK: page_handler.py não precisou de alteração.")


if __name__ == "__main__":
    main()
