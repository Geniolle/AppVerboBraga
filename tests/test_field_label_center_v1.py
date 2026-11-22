from pathlib import Path

STYLES = Path(__file__).resolve().parents[1] / "static" / "css" / "ui-standards.css"


def test_field_labels_are_left_of_field_globally():
    source = STYLES.read_text(encoding="utf-8")

    # Regra global: o nome do campo fica a esquerda do proprio campo, na mesma linha, com 150px.
    assert "APPGENESIS_FIELD_LABEL_LEFT_V2_START" in source
    assert ".field:has(> label + input" in source
    assert "flex: 0 0 150px;" in source
    assert ".field > label:not(:has(input, select, textarea))" in source
    assert "text-align: left;" in source
