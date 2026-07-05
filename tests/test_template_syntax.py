from pathlib import Path

from jinja2 import Environment

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_new_user_sidebar_partial_has_valid_jinja_syntax():
    template_path = REPO_ROOT / "templates" / "partials" / "new_user_sidebar.html"
    content = template_path.read_text(encoding="utf-8")

    Environment().parse(content)
