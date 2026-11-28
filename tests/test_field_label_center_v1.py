from pathlib import Path

STYLES = Path(__file__).resolve().parents[1] / "static" / "css" / "ui-standards.css"


def test_field_labels_are_above_field_left_aligned_globally():
    source = STYLES.read_text(encoding="utf-8")

    # Regra global: o nome do campo fica em cima do proprio campo, alinhado a esquerda.
    assert "APPGENESIS_FIELD_LABEL_TOP_LEFT_V3_START" in source
    assert ".field > label:not(:has(input, select, textarea))" in source
    assert "text-align: left;" in source
