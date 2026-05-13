from __future__ import annotations

from .configuracao import UTILIZADOR_CONFIG
from .urls import (
    montar_url_editar_utilizador_v1,
    montar_url_exibir_utilizador_v1,
    montar_url_fechar_utilizador_v1,
)

__all__ = (
    "UTILIZADOR_CONFIG",
    "montar_url_editar_utilizador_v1",
    "montar_url_exibir_utilizador_v1",
    "montar_url_fechar_utilizador_v1",
)
