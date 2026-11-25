"""Acoes de autorizacao de um perfil: exibir, editar, criar, eliminar (seleção múltipla).

Perfis antigos guardavam um nivel unico (todas / exibir / editar):
- 'exibir'  -> {exibir}
- 'editar'  -> todas as acoes (comportamento anterior: edicao completa)
- 'todas'   -> todas as acoes
"""

from __future__ import annotations

from typing import Any, Iterable

ACTION_EXIBIR = "exibir"
ACTION_EDITAR = "editar"
ACTION_CRIAR = "criar"
ACTION_ELIMINAR = "eliminar"
ALL_ACTIONS: tuple[str, ...] = (ACTION_EXIBIR, ACTION_EDITAR, ACTION_CRIAR, ACTION_ELIMINAR)
ACTION_LABELS: dict[str, str] = {
    ACTION_EXIBIR: "Exibir",
    ACTION_EDITAR: "Editar",
    ACTION_CRIAR: "Criar",
    ACTION_ELIMINAR: "Eliminar",
}
_LEGACY_EXPANSION: dict[str, tuple[str, ...]] = {
    "todas": ALL_ACTIONS,
    "editar": ALL_ACTIONS,
    "exibir": (ACTION_EXIBIR,),
}


def _raw_items(raw: Any) -> Iterable[str]:
    if raw is None:
        return ()
    if isinstance(raw, str):
        return raw.split(",")
    return raw


def normalize_actions(raw: Any) -> tuple[str, ...]:
    """Devolve as acoes validas, na ordem canonica, sem duplicados."""
    chosen: set[str] = set()
    for item in _raw_items(raw):
        clean = str(item or "").strip().lower()
        if not clean:
            continue
        if clean in _LEGACY_EXPANSION:
            chosen.update(_LEGACY_EXPANSION[clean])
        elif clean in ALL_ACTIONS:
            chosen.add(clean)
    return tuple(action for action in ALL_ACTIONS if action in chosen)


def serialize_actions(raw: Any) -> str:
    return ",".join(normalize_actions(raw))


def actions_label(raw: Any) -> str:
    return ", ".join(ACTION_LABELS[action] for action in normalize_actions(raw))


__all__ = [
    "ACTION_CRIAR",
    "ACTION_EDITAR",
    "ACTION_ELIMINAR",
    "ACTION_EXIBIR",
    "ALL_ACTIONS",
    "actions_label",
    "normalize_actions",
    "serialize_actions",
]
