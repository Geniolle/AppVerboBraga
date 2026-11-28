from appgenesis.services.access_actions import actions_label, normalize_actions, serialize_actions


def test_saved_subset_is_not_expanded_to_all_actions():
    saved = serialize_actions(["exibir", "editar"])
    assert normalize_actions(saved) == ("exibir", "editar")


def test_single_editar_selection_stays_editar_only():
    assert normalize_actions(serialize_actions(["editar"])) == ("editar",)


def test_legacy_values_keep_previous_meaning():
    assert normalize_actions("exibir") == ("exibir",)
    assert normalize_actions("editar") == ("exibir", "editar", "criar", "eliminar")
    assert normalize_actions("todas") == ("exibir", "editar", "criar", "eliminar")


def test_label_lists_selected_actions():
    assert actions_label(serialize_actions(["criar", "exibir"])) == "Exibir, Criar"
