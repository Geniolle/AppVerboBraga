from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1] / "appgenesis"
FORBIDDEN = (
    "APPGENESIS_DEBUG_",
    "_debug_sessoes_flow_enabled_v1",
    "_log_sessoes_flow_v1",
    "_debug_sessoes_page_enabled_v1",
    "_log_sessoes_page_v1",
    "_debug_process_editor_flow_enabled_v1",
    "_log_process_editor_flow_v1",
)


def test_debug_logging_helpers_removed_from_routes():
    offenders = []
    for path in APP_DIR.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in FORBIDDEN:
            if token in text:
                offenders.append(f"{path.relative_to(APP_DIR.parent)}: {token}")
    assert offenders == []
