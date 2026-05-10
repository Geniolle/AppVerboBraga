# -*- coding: utf-8 -*-
"""
Remove do projeto o bloco/card "Ultimos utilizadores criados".
A remocao procura o titulo visivel com ou sem acentos e remove o container HTML
mais proximo para evitar deixar tabela/botoes soltos no layout.
"""

from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path


ROOT = Path(".").resolve()

TARGETS = {
    "ultimos utilizadores criados",
    "ultimos usuarios criados",
    "ultimos users criados",
    "latest users created",
    "latest created users",
}

SCAN_EXTENSIONS = {".html", ".jinja", ".jinja2", ".js", ".py"}

EXCLUDED_PARTS = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "backups",
}


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFD", value)
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
    value = value.lower()
    value = re.sub(r"\s+", " ", value)
    return value


def should_scan(path: Path) -> bool:
    if path.suffix.lower() not in SCAN_EXTENSIONS:
        return False

    parts = set(path.parts)
    if parts.intersection(EXCLUDED_PARTS):
        return False

    if path.as_posix().endswith("scripts/remove_latest_users_card_v1.py"):
        return False

    return True


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8", newline="")


def has_target(content: str) -> bool:
    normalized = normalize_text(content)
    return any(target in normalized for target in TARGETS)


def find_target_index(content: str) -> int:
    normalized = normalize_text(content)

    indexes = []
    for target in TARGETS:
        index = normalized.find(target)
        if index >= 0:
            indexes.append(index)

    if not indexes:
        return -1

    normalized_index = min(indexes)

    # Como a normalizacao remove acentos, o indice pode ficar ligeiramente diferente.
    # Ajusta procurando uma janela aproximada no texto original.
    original_window_start = max(0, normalized_index - 500)
    original_window_end = min(len(content), normalized_index + 1500)
    original_window = content[original_window_start:original_window_end]
    normalized_window = normalize_text(original_window)

    for target in TARGETS:
        window_index = normalized_window.find(target)
        if window_index >= 0:
            return original_window_start + window_index

    return normalized_index


def find_open_tag_before(content: str, index: int) -> tuple[int, str] | None:
    before = content[:index]

    candidates: list[tuple[int, str]] = []

    patterns = [
        (r"<div\b[^>]*class\s*=\s*['\"][^'\"]*\bcard\b[^'\"]*['\"][^>]*>", "div"),
        (r"<section\b[^>]*class\s*=\s*['\"][^'\"]*\bcard\b[^'\"]*['\"][^>]*>", "section"),
        (r"<article\b[^>]*class\s*=\s*['\"][^'\"]*\bcard\b[^'\"]*['\"][^>]*>", "article"),
        (r"<div\b[^>]*>", "div"),
        (r"<section\b[^>]*>", "section"),
        (r"<article\b[^>]*>", "article"),
    ]

    for pattern, tag_name in patterns:
        matches = list(re.finditer(pattern, before, flags=re.IGNORECASE))
        if matches:
            candidates.append((matches[-1].start(), tag_name))

    if not candidates:
        return None

    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0]


def find_matching_close(content: str, start: int, tag_name: str) -> int:
    tag_pattern = re.compile(rf"<(/?){tag_name}\b[^>]*>", flags=re.IGNORECASE)
    depth = 0

    for match in tag_pattern.finditer(content, start):
        is_close = bool(match.group(1))

        if not is_close:
            text = match.group(0)
            if text.rstrip().endswith("/>"):
                continue
            depth += 1
            continue

        depth -= 1

        if depth <= 0:
            return match.end()

    fallback = content.find(f"</{tag_name}>", start)
    if fallback >= 0:
        return fallback + len(f"</{tag_name}>")

    return -1


def remove_target_block(content: str) -> tuple[str, int]:
    removed_count = 0

    while has_target(content):
        target_index = find_target_index(content)

        if target_index < 0:
            break

        open_tag = find_open_tag_before(content, target_index)

        if open_tag is None:
            line_start = content.rfind("\n", 0, target_index)
            line_end = content.find("\n", target_index)
            if line_start < 0:
                line_start = 0
            if line_end < 0:
                line_end = len(content)
            content = content[:line_start] + content[line_end:]
            removed_count += 1
            continue

        start, tag_name = open_tag
        end = find_matching_close(content, start, tag_name)

        if end < 0 or end <= start:
            line_start = content.rfind("\n", 0, target_index)
            line_end = content.find("\n", target_index)
            if line_start < 0:
                line_start = 0
            if line_end < 0:
                line_end = len(content)
            content = content[:line_start] + content[line_end:]
            removed_count += 1
            continue

        while start > 0 and content[start - 1] in " \t\r\n":
            start -= 1

        while end < len(content) and content[end:end + 1] in " \t\r\n":
            end += 1

        content = content[:start] + "\n" + content[end:]
        removed_count += 1

    return content, removed_count


def main() -> int:
    modified_files: list[str] = []
    removed_total = 0

    files = [path for path in ROOT.rglob("*") if path.is_file() and should_scan(path)]

    for path in files:
        try:
            original = read_text(path)
        except UnicodeDecodeError:
            continue

        if not has_target(original):
            continue

        updated, removed_count = remove_target_block(original)

        if updated != original:
            write_text(path, updated)
            modified_files.append(path.as_posix())
            removed_total += removed_count

    if not modified_files:
        print("ERRO: nenhum bloco com 'Ultimos utilizadores criados' foi encontrado/removido.")
        return 2

    print("Blocos removidos:", removed_total)
    print("Ficheiros alterados:")
    for item in modified_files:
        print(" -", item)

    remaining = []
    for path in files:
        try:
            content = read_text(path)
        except UnicodeDecodeError:
            continue

        if has_target(content):
            remaining.append(path.as_posix())

    if remaining:
        print("ERRO: ainda existem referencias ao bloco removido:")
        for item in remaining:
            print(" -", item)
        return 3

    return 0


if __name__ == "__main__":
    sys.exit(main())
