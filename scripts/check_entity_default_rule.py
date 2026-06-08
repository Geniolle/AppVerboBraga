from pathlib import Path

ROOT = Path.cwd()

SCAN_DIRS = [
    "templates",
    "appverbo",
    "static/js",
]

TARGET_EXTENSIONS = {".html", ".py", ".js"}

IGNORE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    "dist",
    "build",
    "backups",
    "diagnostics",
    "migrations",
    "tests",
    "scripts",
}

IGNORE_FILES = {
    "query_pg.py",
    "scratch_debug_selenium.py",
    "scratch_fetch_rendered.py",
}

def should_ignore(path: Path) -> bool:
    if path.name in IGNORE_FILES:
        return True

    return any(part in IGNORE_DIRS for part in path.parts)

def has_estado(text: str) -> bool:
    lower = text.lower()
    return (
        'name="estado"' in lower
        or "name='estado'" in lower
        or "estado" in lower
    )

def has_numero_entidade(text: str) -> bool:
    lower = text.lower()
    return (
        "nº entidade" in lower
        or "n° entidade" in lower
        or "numero_entidade" in lower
        or "numeroentidade" in lower
        or "entity_default_rule" in lower
    )

files_to_review = []

for scan_dir in SCAN_DIRS:
    base = ROOT / scan_dir

    if not base.exists():
        continue

    for path in base.rglob("*"):
        if should_ignore(path):
            continue

        if not path.is_file():
            continue

        if path.suffix.lower() not in TARGET_EXTENSIONS:
            continue

        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        if has_estado(text) and not has_numero_entidade(text):
            files_to_review.append(path)

if not files_to_review:
    print("OK: nos ficheiros ativos, não encontrei Estado sem Nº Entidade.")
else:
    print("Ficheiros ativos que devem ser analisados:")
    for file in files_to_review:
        print(f"- {file.relative_to(ROOT)}")
