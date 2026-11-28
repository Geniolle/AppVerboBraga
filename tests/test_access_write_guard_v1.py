from appgenesis.services.access_write_guard import write_rule_for_path


def test_personal_profile_write_requires_editar_on_meu_perfil():
    assert write_rule_for_path("/users/profile/personal") == ("meu_perfil", ("editar",))


def test_functions_save_accepts_criar_or_editar_on_administrativo():
    assert write_rule_for_path("/users/functions/save") == ("administrativo", ("criar", "editar"))


def test_delete_paths_require_eliminar():
    assert write_rule_for_path("/users/functions/delete") == ("administrativo", ("eliminar",))
    assert write_rule_for_path("/settings/menu/sidebar-section-delete") == ("sessoes", ("eliminar",))


def test_process_data_is_validated_in_handler_not_by_path():
    assert write_rule_for_path("/users/profile/process-data") is None


def test_unrelated_paths_are_not_guarded():
    assert write_rule_for_path("/login") is None
    assert write_rule_for_path("/users/invite/accept") is None
