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
