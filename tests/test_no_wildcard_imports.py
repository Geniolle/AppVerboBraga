import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCAN_ROOTS = [REPO_ROOT / "appgenesis", REPO_ROOT / "web_app.py"]


def _iter_python_files():
    for root in SCAN_ROOTS:
        if root.is_file():
            yield root
        else:
            yield from root.rglob("*.py")


def _wildcard_imports(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and any(alias.name == "*" for alias in node.names):
            yield node.lineno


def test_no_wildcard_imports_in_appgenesis_package():
    offenders = {}
    for path in _iter_python_files():
        lines = list(_wildcard_imports(path))
        if lines:
            offenders[str(path.relative_to(REPO_ROOT))] = lines

    assert not offenders, (
        "Wildcard imports ('from X import *') are not allowed in appgenesis/ or "
        f"web_app.py — import explicit names instead. Found: {offenders}"
    )
