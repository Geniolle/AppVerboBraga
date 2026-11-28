from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_flicker_debug_assets_removed():
    assert not (ROOT / "static/js/modules/debug_flicker_v1.js").exists()
    assert not (ROOT / "static/js/modules/debug_flicker_cards_v1.js").exists()


def test_flicker_debug_not_referenced_in_code():
    for relative in (
        "templates/new_user.html",
        "appgenesis/routes/profile/page_handler.py",
    ):
        content = (ROOT / relative).read_text(encoding="utf-8")
        assert "debug_flicker" not in content, relative
