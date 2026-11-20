from pathlib import Path

TEMPLATE = Path(__file__).resolve().parents[1] / "templates" / "user_invite_accept.html"


def test_activate_account_passwords_share_a_row_with_eye_toggle():
    source = TEMPLATE.read_text(encoding="utf-8")

    # As duas palavras-passe ficam lado a lado (mesma linha) e o toggle usa icone de olho, nao o texto Exibir.
    assert 'class="password-pair"' in source
    assert ">Exibir</button>" not in source
    assert "<svg" in source
