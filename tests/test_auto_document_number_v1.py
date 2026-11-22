from appgenesis.routes.profile.profile_handlers import _apply_auto_document_number_v1


RULE = {"auto_document_number": {"prefix": "R", "date_field": "custom_data"}}


def test_numero_calculado_a_partir_da_data():
    values = {"custom_data": "2026-11-22", "custom_numero_documento": "digitado"}
    _apply_auto_document_number_v1(values, "custom_numero_documento", RULE)
    assert values["custom_numero_documento"] == "R261122"


def test_sem_data_remove_valor_calculado():
    values = {"custom_data": "", "custom_numero_documento": "R000000"}
    _apply_auto_document_number_v1(values, "custom_numero_documento", RULE)
    assert "custom_numero_documento" not in values


def test_campo_sem_regra_fica_igual():
    values = {"custom_data": "2026-11-22", "custom_outro": "x"}
    _apply_auto_document_number_v1(values, "custom_outro", {})
    assert values == {"custom_data": "2026-11-22", "custom_outro": "x"}


WEEKDAY_RULE = {"auto_document_number": {"prefix": "", "date_field": "custom_data", "format": "weekday"}}


def test_dia_da_semana_calculado_a_partir_da_data():
    values = {"custom_data": "2026-11-22", "custom_dia_da_semana": "digitado"}
    _apply_auto_document_number_v1(values, "custom_dia_da_semana", WEEKDAY_RULE)
    assert values["custom_dia_da_semana"] == "Domingo"


def test_dia_da_semana_sem_data_remove_valor():
    values = {"custom_data": "", "custom_dia_da_semana": "Domingo"}
    _apply_auto_document_number_v1(values, "custom_dia_da_semana", WEEKDAY_RULE)
    assert "custom_dia_da_semana" not in values
