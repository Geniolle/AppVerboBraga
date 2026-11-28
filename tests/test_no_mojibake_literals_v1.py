import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# "Ã" ou "Â" seguido de caractere que nao e letra ASCII nem espaco (ex.: "Ã§", "Ã£", "Ãµ").
# Acentos legitimos em maiusculas (ÃO, ÇÃ) nao sao apanhados. "�" e o caractere de substituicao.
MOJIBAKE = re.compile(r"[ÃÂ](?![A-Za-z ])|�")
CODE_DIRS = ("appgenesis", "templates", "static/js", "static/css")
SUFFIXES = {".py", ".html", ".js", ".css"}


def test_no_mojibake_in_code_and_templates():
    offenders = []
    for directory in CODE_DIRS:
        for path in (ROOT / directory).rglob("*"):
            if path.suffix not in SUFFIXES or "__pycache__" in path.parts:
                continue
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                if MOJIBAKE.search(line):
                    offenders.append(f"{path.relative_to(ROOT)}:{number}")
    assert offenders == []
