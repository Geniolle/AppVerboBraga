"""Etapa 5: new_user.js dividido em static/js/new_user/; todos carregados uma vez, pela ordem numerada."""

from new_user_js_source import NEW_USER_JS_DIR, PROJECT_ROOT, new_user_js_parts


def test_all_new_user_parts_loaded_once_in_numeric_order() -> None:
    on_disk = sorted(p.name for p in NEW_USER_JS_DIR.glob("*.js"))
    assert on_disk, "sem ficheiros em static/js/new_user/"
    assert new_user_js_parts() == on_disk
    assert not (PROJECT_ROOT / "static" / "js" / "new_user.js").exists()
