from pathlib import Path

HANDLERS = Path(__file__).resolve().parents[1] / "appgenesis" / "routes" / "auth" / "invite_handlers.py"


def test_invite_accept_post_errors_redirect_instead_of_render():
    source = HANDLERS.read_text(encoding="utf-8")

    # PRG: erros e alreadyActive do POST redirecionam para o GET; um refresh nao reenvia o formulario.
    post = source[source.index('@router.post("/users/invite/accept"') :]
    assert "_store_invite_accept_flash(" in post
    assert post.count("return render_invite_accept(") == 0
    assert '"password"' not in source.split("def _store_invite_accept_flash")[1].split("def _pop_invite_accept_flash")[0]
