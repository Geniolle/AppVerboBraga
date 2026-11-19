import json
import re
from pathlib import Path

from appgenesis.core import templates

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = (ROOT / "templates/new_user.html").read_text(encoding="utf-8")
ISLAND = re.search(
    r'<script type="application/json" id="appgenesis-bootstrap">(.*?)</script>', TEMPLATE, re.S
)


def _context_for(expressions):
    context = {}
    for expression in expressions:
        parts = expression.split(".")
        node = context
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node.setdefault(parts[-1], "valor")
    return context


def test_bootstrap_is_a_json_data_island_without_inline_script():
    assert ISLAND is not None
    assert "window.__APPGENESIS_BOOTSTRAP__ = {" not in TEMPLATE
    assert "app_bootstrap_v1.js" in TEMPLATE
    assert (ROOT / "static/js/modules/app_bootstrap_v1.js").exists()


def test_bootstrap_island_renders_as_valid_json():
    island = ISLAND.group(1)
    expressions = re.findall(r"\{\{\s*([\w.]+)\|tojson\s*\}\}", island)
    assert expressions, "nenhuma expressao tojson encontrada"
    rendered = templates.env.from_string(island).render(_context_for(expressions))
    data = json.loads(rendered)
    assert "currentUserName" in data and "initialMenu" in data
