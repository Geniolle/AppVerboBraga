from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_meu_perfil_runtime_receives_personal_card_target_by_injection_v1() -> None:
    runtime_text = _read("static/js/modules/process_subsequent_visibility_runtime_v1.js")
    assert "getMeuPerfilPersonalCardTarget" in runtime_text
    assert 'scope.querySelector("#perfil-pessoal-card' not in runtime_text
    assert 'root.querySelectorAll("#perfil-pessoal-card' not in runtime_text
    assert 'setActiveSubmenu("#perfil-pessoal-card"' not in runtime_text


def test_meu_perfil_navigation_state_uses_canonical_menu_key_v1() -> None:
    runtime_text = _read("static/js/modules/process_navigation_state_v1.js")
    assert 'startupMenu !== "perfil"' not in runtime_text
    assert "MEU_PERFIL_MENU_KEY" in runtime_text


def test_new_user_bootstrap_composes_meu_perfil_helpers_v1() -> None:
    new_user_text = _read("static/js/new_user.js")
    assert "getMeuPerfilPersonalCardTargetV1" in new_user_text
    assert 'document.getElementById("perfil-pessoal-card")' not in new_user_text
    assert 'setActiveSubmenu("#perfil-pessoal-card"' not in new_user_text

