from pathlib import Path

LOGIN = Path(__file__).resolve().parents[1] / "templates" / "login.html"


def test_login_password_inputs_have_eye_toggle():
    source = LOGIN.read_text(encoding="utf-8")

    # Login, registo e admin: cada campo de palavra-passe tem o botao de olho (sem texto "Exibir").
    assert source.count('class="password-field"') == 4
    assert source.count("data-toggle-password=") == 4
    assert ">Exibir</button>" not in source
