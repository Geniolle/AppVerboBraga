from pathlib import Path

STYLES = Path(__file__).resolve().parents[1] / "static" / "css" / "ui-standards.css"


def test_field_labels_are_centered_globally():
    source = STYLES.read_text(encoding="utf-8")

    # Regra global: o nome do campo fica alinhado a esquerda, sobre a largura do proprio campo.
    assert "APPGENESIS_FIELD_LABEL_CENTER_V1_START" in source
    assert ".field > label:not(:has(input, select, textarea))" in source
    assert "text-align: left;" in source
