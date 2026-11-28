"""Etapa 5c: new_user.css dividido em static/css/new_user/; todos carregados uma vez, pela ordem numerada (cascata)."""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CSS_DIR = PROJECT_ROOT / "static" / "css" / "new_user"


def test_all_new_user_css_parts_loaded_once_in_numeric_order() -> None:
    template_text = (PROJECT_ROOT / "templates" / "new_user.html").read_text(encoding="utf-8")
    loaded = re.findall(r'href="/static/css/new_user/([\w.]+\.css)\?', template_text)
    on_disk = sorted(p.name for p in CSS_DIR.glob("*.css"))
    assert on_disk, "sem ficheiros em static/css/new_user/"
    assert loaded == on_disk
    assert not (PROJECT_ROOT / "static" / "css" / "new_user.css").exists()
    # A ordem relativa aos modulos tem de se manter: antes de process_shell_runtime_v1.css.
    assert template_text.index("/static/css/new_user/") < template_text.index("/static/css/modules/process_shell_runtime_v1.css")


def _brace_depths(css: str) -> tuple[int, int]:
    """(profundidade final, minima) das chavetas, ignorando comentarios e strings."""
    depth = lowest = 0
    i, in_comment, quote = 0, False, ""
    while i < len(css):
        two = css[i:i + 2]
        if in_comment:
            if two == "*/":
                in_comment, i = False, i + 1
        elif quote:
            if css[i] == "\\":
                i += 1
            elif css[i] == quote:
                quote = ""
        elif two == "/*":
            in_comment, i = True, i + 1
        elif css[i] in "\"'":
            quote = css[i]
        elif css[i] == "{":
            depth += 1
        elif css[i] == "}":
            depth -= 1
            lowest = min(lowest, depth)
        i += 1
    return depth, lowest


def test_new_user_css_parts_have_balanced_braces() -> None:
    # Uma "}" a mais faz o browser descartar a regra seguinte sem aviso.
    for path in sorted(CSS_DIR.glob("*.css")):
        assert _brace_depths(path.read_text(encoding="utf-8")) == (0, 0), path.name
    assert _brace_depths("a { b: 1; }\n}\n.c { d: 2; }") == (-1, -1)
