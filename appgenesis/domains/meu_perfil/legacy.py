from __future__ import annotations

from appgenesis.domains.meu_perfil.service import normalize_meu_perfil_menu_key_v1


def normalize_legacy_meu_perfil_menu_key_v1(raw_value):
    return normalize_meu_perfil_menu_key_v1(raw_value)

