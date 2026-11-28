"""Fonte de new_user.js para testes: os ficheiros de static/js/new_user/ pela ordem do template."""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
NEW_USER_JS_DIR = PROJECT_ROOT / "static" / "js" / "new_user"


def new_user_js_parts() -> list[str]:
    template_text = (PROJECT_ROOT / "templates" / "new_user.html").read_text(encoding="utf-8")
    return re.findall(r'src="/static/js/new_user/([\w.]+\.js)\?', template_text)


def read_new_user_js() -> str:
    return "".join((NEW_USER_JS_DIR / name).read_text(encoding="utf-8") for name in new_user_js_parts())
