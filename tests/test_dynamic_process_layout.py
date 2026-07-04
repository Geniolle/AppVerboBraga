from appverbo.dynamic_process_layout import resolve_dynamic_process_layout_config


####################################################################################
# (1) PROCESSO SEM CONFIGURACAO CONTINUA COM O COMPORTAMENTO PADRAO (SEM REGRESSAO)
####################################################################################

def test_resolve_dynamic_process_layout_config_default_has_no_history() -> None:
    config = resolve_dynamic_process_layout_config("extrato", "Extrato", {})

    assert config["layout"] == "single"
    assert config["uses_record_history"] is False
    assert config["singular_label"] == "registo"
    assert config["create_title"] == "Criar registo"


####################################################################################
# (2) PADROES LEGADOS (AUSENCIA/AUTORIZACAO/DEPARTAMENTO) CONTINUAM INALTERADOS
####################################################################################

def test_resolve_dynamic_process_layout_config_keeps_legacy_absence_pattern() -> None:
    config = resolve_dynamic_process_layout_config("ausencias", "Ausências", {})

    assert config["uses_record_history"] is True
    assert config["singular_label"] == "ausência"
    assert config["create_title"] == "Criar ausência"


def test_resolve_dynamic_process_layout_config_keeps_legacy_department_pattern() -> None:
    config = resolve_dynamic_process_layout_config("departamentos", "Departamentos", {})

    assert config["uses_record_history"] is True
    assert config["singular_label"] == "departamento"
    assert config["create_title"] == "Criar departamento"


####################################################################################
# (3) NOVO: process_record_uses_history GENERICO, SEM HARDCODE POR PROCESSO
####################################################################################

def test_resolve_dynamic_process_layout_config_generic_history_flag_uses_menu_label() -> None:
    config = resolve_dynamic_process_layout_config(
        "calendario",
        "Calendário",
        {"process_record_uses_history": True},
    )

    assert config["uses_record_history"] is True
    assert config["layout"] == "single"
    assert config["is_list_process"] is False
    assert config["singular_label"] == "Calendário"
    assert config["plural_label"] == "Calendários"
    assert config["create_title"] == "Criar Calendário"
    assert config["edit_title"] == "Editar Calendário"


def test_resolve_dynamic_process_layout_config_generic_history_flag_works_for_any_process() -> None:
    config = resolve_dynamic_process_layout_config(
        "extrato",
        "Extrato",
        {"process_record_uses_history": True},
    )

    assert config["uses_record_history"] is True
    assert config["singular_label"] == "Extrato"
    assert config["create_title"] == "Criar Extrato"


def test_resolve_dynamic_process_layout_config_calendario_uses_agenda_label() -> None:
    # Configuracao real do processo Calendario: registos sao "agendas", nao "calendarios".
    config = resolve_dynamic_process_layout_config(
        "calendario",
        "Calendário",
        {
            "process_record_uses_history": True,
            "process_record_singular_label": "Agenda",
            "process_record_plural_label": "Agendas",
        },
    )

    assert config["uses_record_history"] is True
    assert config["singular_label"] == "Agenda"
    assert config["plural_label"] == "Agendas"
    assert config["create_title"] == "Criar Agenda"
    assert config["edit_title"] == "Editar Agenda"
    assert config["empty_active_message"] == "Sem Agendas ativos."


def test_resolve_dynamic_process_layout_config_explicit_singular_label_wins_over_menu_label() -> None:
    config = resolve_dynamic_process_layout_config(
        "calendario",
        "Calendário",
        {
            "process_record_uses_history": True,
            "process_record_singular_label": "evento",
        },
    )

    assert config["singular_label"] == "evento"
    assert config["create_title"] == "Criar evento"


def test_resolve_dynamic_process_layout_config_without_history_flag_stays_generic_registo() -> None:
    config = resolve_dynamic_process_layout_config("calendario", "Calendário", {})

    assert config["uses_record_history"] is False
    assert config["singular_label"] == "registo"
    assert config["create_title"] == "Criar registo"
