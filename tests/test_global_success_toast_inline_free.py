from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_global_success_feedback_is_not_rendered_inline_anymore() -> None:
    template_paths = [
        "templates/new_user.html",
        "templates/login.html",
        "templates/password_reset_confirm.html",
        "templates/password_reset_request.html",
        "templates/user_invite_accept.html",
        "templates/macros/admin_subprocess.html",
    ]

    for relative_path in template_paths:
        text = _read_text(relative_path)
        assert "alert ok" not in text, relative_path
        assert "<div class=\"alert ok\"" not in text, relative_path


def test_global_toast_boot_is_loaded_from_base_template() -> None:
    base_text = _read_text("templates/base.html")
    assert "process_shell_runtime_v1.js" in base_text
    assert "appgenesis_feedback_toast_boot_v1.js" in base_text


def test_new_user_js_no_longer_bootstraps_feedback_toasts_inline() -> None:
    new_user_js = _read_text("static/js/new_user.js")
    assert "enhanceFeedbackToasts({ source: \"url\" })" not in new_user_js


def test_admin_subprocess_ajax_success_no_longer_inserts_inline_ok_alert() -> None:
    js_text = _read_text("static/js/modules/admin_subprocesses_v1.js")
    assert "_insertSessoesSaveAjaxFeedbackV1(createCard, \"alert ok\", safeMessage);" not in js_text
