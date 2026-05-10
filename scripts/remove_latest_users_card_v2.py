# -*- coding: utf-8 -*-
from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path


TEMPLATE_PATH = Path("templates/new_user.html")


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFD", value)
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
    value = value.lower()
    value = re.sub(r"\s+", " ", value)
    return value


def find_target_index(content: str) -> int:
    direct_patterns = [
        r"Últimos\s+utilizadores\s+criados",
        r"Ultimos\s+utilizadores\s+criados",
        r"últimos\s+utilizadores\s+criados",
        r"ultimos\s+utilizadores\s+criados",
    ]

    for pattern in direct_patterns:
        match = re.search(pattern, content, flags=re.IGNORECASE)
        if match:
            return match.start()

    normalized = normalize_text(content)
    target = "ultimos utilizadores criados"
    normalized_index = normalized.find(target)

    if normalized_index < 0:
        return -1

    window_start = max(0, normalized_index - 800)
    window_end = min(len(content), normalized_index + 1600)
    window = content[window_start:window_end]

    for pattern in direct_patterns:
        match = re.search(pattern, window, flags=re.IGNORECASE)
        if match:
            return window_start + match.start()

    return normalized_index


def parse_open_tag_name(tag_text: str) -> str:
    match = re.match(r"<\s*([a-zA-Z0-9_-]+)", tag_text)
    if not match:
        return ""
    return match.group(1).lower()


def is_self_closing(tag_text: str) -> bool:
    clean = tag_text.strip()
    return clean.endswith("/>") or clean.lower().startswith("<!")

def token_stack_until(content: str, stop_index: int) -> list[tuple[str, int, int, str]]:
    token_pattern = re.compile(r"<\s*(/?)\s*(div|section|article)\b[^>]*>", flags=re.IGNORECASE)
    stack: list[tuple[str, int, int, str]] = []

    for match in token_pattern.finditer(content, 0, stop_index):
        is_close = bool(match.group(1))
        tag_name = match.group(2).lower()
        tag_text = match.group(0)

        if not is_close:
            if is_self_closing(tag_text):
                continue
            stack.append((tag_name, match.start(), match.end(), tag_text))
            continue

        for index in range(len(stack) - 1, -1, -1):
            if stack[index][0] == tag_name:
                del stack[index:]
                break

    return stack


def choose_ancestor(content: str, target_index: int) -> tuple[str, int, int, str] | None:
    stack = token_stack_until(content, target_index)

    for item in reversed(stack):
        tag_name, start, end, tag_text = item
        normalized_tag = normalize_text(tag_text)

        if "card" in normalized_tag:
            return item

    for item in reversed(stack):
        tag_name, start, end, tag_text = item

        if tag_name in {"div", "section", "article"}:
            return item

    return None


def find_matching_close(content: str, ancestor: tuple[str, int, int, str]) -> int:
    tag_name, start, _, _ = ancestor
    token_pattern = re.compile(rf"<\s*(/?)\s*{re.escape(tag_name)}\b[^>]*>", flags=re.IGNORECASE)
    depth = 0

    for match in token_pattern.finditer(content, start):
        is_close = bool(match.group(1))
        tag_text = match.group(0)

        if not is_close:
            if is_self_closing(tag_text):
                continue
            depth += 1
            continue

        depth -= 1

        if depth == 0:
            return match.end()

    return -1


def remove_latest_users_card(content: str) -> tuple[str, int]:
    target_index = find_target_index(content)

    if target_index < 0:
        return content, 0

    ancestor = choose_ancestor(content, target_index)

    if ancestor is None:
        raise RuntimeError("Nao foi possivel encontrar o container do card.")

    start = ancestor[1]
    end = find_matching_close(content, ancestor)

    if end < 0 or end <= start:
        raise RuntimeError("Nao foi possivel encontrar o fecho do container do card.")

    removed_block = content[start:end]

    if "Últimos utilizadores criados" not in removed_block and "Ultimos utilizadores criados" not in removed_block:
        if "ultimos utilizadores criados" not in normalize_text(removed_block):
            raise RuntimeError("Bloco selecionado nao contem o titulo esperado.")

    if len(removed_block) > 25000:
        raise RuntimeError(
            "Bloco selecionado parece grande demais. Remocao cancelada para evitar dano no template."
        )

    while start > 0 and content[start - 1] in " \t\r\n":
        start -= 1

    while end < len(content) and content[end:end + 1] in " \t\r\n":
        end += 1

    updated = content[:start] + "\n" + content[end:]

    return updated, 1


def main() -> int:
    if not TEMPLATE_PATH.exists():
        print(f"ERRO: ficheiro nao encontrado: {TEMPLATE_PATH}")
        return 2

    original = TEMPLATE_PATH.read_text(encoding="utf-8")
    updated, removed_count = remove_latest_users_card(original)

    if removed_count != 1:
        print("ERRO: nenhum card 'Ultimos utilizadores criados' foi removido.")
        return 3

    if normalize_text(updated).find("ultimos utilizadores criados") >= 0:
        print("ERRO: o titulo ainda existe apos a remocao.")
        return 4

    TEMPLATE_PATH.write_text(updated, encoding="utf-8", newline="")

    print("OK: card 'Ultimos utilizadores criados' removido com seguranca.")
    print("Blocos removidos:", removed_count)
    print("Ficheiro alterado:", TEMPLATE_PATH.as_posix())

    return 0


if __name__ == "__main__":
    sys.exit(main())
