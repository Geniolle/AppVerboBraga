from appgenesis.services.access_write_guard import menu_for_write_path


def test_personal_profile_write_maps_to_meu_perfil():
    assert menu_for_write_path("/users/profile/personal") == "meu_perfil"


def test_functions_and_auth_profile_writes_map_to_administrativo():
    assert menu_for_write_path("/users/functions/save") == "administrativo"
    assert menu_for_write_path("/users/profile/auth-profile-save") == "administrativo"


def test_settings_menu_writes_map_to_sessoes():
    assert menu_for_write_path("/settings/menu/sidebar-section-save") == "sessoes"


def test_process_data_is_validated_in_handler_not_by_path():
    assert menu_for_write_path("/users/profile/process-data") is None


def test_unrelated_paths_are_not_guarded():
    assert menu_for_write_path("/login") is None
    assert menu_for_write_path("/users/invite/accept") is None
