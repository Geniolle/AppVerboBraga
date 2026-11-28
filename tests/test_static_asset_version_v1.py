import re
from pathlib import Path

from appgenesis.web.templates import templates
from appgenesis.services.static_assets import ASSET_VERSION

ROOT = Path(__file__).resolve().parents[1]
HARDCODED_VERSION = re.compile(r"/static/[^\"'\s>]*\?v=(?!\{\{ asset_version \}\})")


def test_asset_version_is_non_empty():
    assert ASSET_VERSION.strip()


def test_jinja_global_exposes_asset_version():
    assert templates.env.globals["asset_version"] == ASSET_VERSION
    assert templates.env.from_string("{{ asset_version }}").render() == ASSET_VERSION


def test_templates_have_no_hardcoded_asset_versions():
    offenders = []
    for path in (ROOT / "templates").rglob("*.html"):
        for match in HARDCODED_VERSION.finditer(path.read_text(encoding="utf-8")):
            offenders.append(f"{path.relative_to(ROOT)}: {match.group(0)}")
    assert offenders == []
