from pathlib import Path
from urllib.parse import parse_qsl, urlsplit

from appgenesis.services.navigation_context import (
    POST_SAVE_MARKER_PARAM_V1,
    build_post_save_return_url_v1,
    build_return_url_v1,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]

####################################################################################
# (1) build_post_save_return_url_v1 tem de marcar appgenesis_after_save=1 sem quebrar
# a compatibilidade de build_return_url_v1 (menu/admin_tab/hash/success/extras).
####################################################################################


def test_build_post_save_return_url_marks_appgenesis_after_save() -> None:
    result = build_post_save_return_url_v1(
        return_menu="administrativo",
        return_admin_tab="entidade",
        default_menu="administrativo",
        default_admin_tab="entidade",
        default_hash="#recent-entities-card",
        entity_success="Entidade atualizada com sucesso.",
    )

    parsed = urlsplit(result)
    params = dict(parse_qsl(parsed.query, keep_blank_values=True))

    assert parsed.fragment == "recent-entities-card"
    assert params["menu"] == "administrativo"
    assert params["admin_tab"] == "entidade"
    assert params["entity_success"] == "Entidade atualizada com sucesso."
    assert params[POST_SAVE_MARKER_PARAM_V1] == "1"
    assert "entity_edit_id" not in params


def test_build_return_url_v1_stays_unmarked_for_error_paths() -> None:
    # build_return_url_v1 tem de continuar sem o marcador -- e' usado pelos
    # redirects de erro/validacao, que precisam manter o card/editor aberto.
    result = build_return_url_v1(
        default_menu="administrativo",
        default_admin_tab="entidade",
        default_hash="#edit-entity-card",
        entity_error="Falha de validacao.",
        entity_edit_id="42",
    )

    params = dict(parse_qsl(urlsplit(result).query, keep_blank_values=True))
    assert POST_SAVE_MARKER_PARAM_V1 not in params
    assert params["entity_edit_id"] == "42"


####################################################################################
# (2) Os redirects finais de sucesso (update/delete de entidade, update de
# utilizador) tem de usar build_post_save_return_url_v1 -- caso contrario
# return_after_save.js reabre o card/editor com o entity_edit_id/user_edit_id
# antigo do submit (bug relatado: Guardar fecha e reabre o card em edicao).
####################################################################################


def test_update_entity_success_redirect_uses_post_save_helper() -> None:
    handler_text = (
        PROJECT_ROOT / "appgenesis" / "routes" / "entities" / "update_handler.py"
    ).read_text(encoding="utf-8")

    success_index = handler_text.index('entity_success="Entidade atualizada com sucesso."')
    block_start = handler_text.rindex("return RedirectResponse(", 0, success_index)
    block = handler_text[block_start:success_index]

    assert "build_post_save_return_url_v1(" in block
    assert "entity_edit_id" not in block
    assert "#recent-entities-card" in block


def test_delete_entity_success_redirect_uses_post_save_helper() -> None:
    handler_text = (
        PROJECT_ROOT / "appgenesis" / "routes" / "entities" / "delete_handler.py"
    ).read_text(encoding="utf-8")

    success_index = handler_text.index('entity_success="Entidade excluida com sucesso."')
    block_start = handler_text.rindex("return RedirectResponse(", 0, success_index)
    block = handler_text[block_start:success_index]

    assert "build_post_save_return_url_v1(" in block
    assert "entity_edit_id" not in block


def test_update_user_success_redirect_uses_post_save_helper() -> None:
    handler_text = (
        PROJECT_ROOT / "appgenesis" / "routes" / "users" / "update_handler.py"
    ).read_text(encoding="utf-8")

    success_index = handler_text.index('success="Utilizador atualizado com sucesso."')
    block_start = handler_text.rindex("return RedirectResponse(", 0, success_index)
    block = handler_text[block_start:success_index]

    assert "build_post_save_return_url_v1(" in block
    assert "user_edit_id" not in block
