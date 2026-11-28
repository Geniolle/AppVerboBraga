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


V2_PREFIX = "v2:"


def _raw_items(raw: Any) -> Iterable[str]:
    if raw is None:
        return ()
    if isinstance(raw, str):
        return raw.split(",")
    return raw


def _strict_actions(raw: Any) -> tuple[str, ...]:
    # Formato novo: so as acoes marcadas (sem expansao de valores antigos).
    chosen: set[str] = set()
    for item in _raw_items(raw):
        clean = str(item or "").strip().lower()
        if clean.startswith(V2_PREFIX):
            clean = clean[len(V2_PREFIX):]
        for token in clean.split(","):
            token = token.strip()
            if token in ALL_ACTIONS:
                chosen.add(token)
    return tuple(action for action in ALL_ACTIONS if action in chosen)


def normalize_actions(raw: Any) -> tuple[str, ...]:
    """Acoes do perfil. Valor com prefixo v2: e o formato novo; sem prefixo e legado."""
    if isinstance(raw, str) and raw.strip().lower().startswith(V2_PREFIX):
        return _strict_actions(raw)
    if isinstance(raw, str) and raw.strip().lower() in _LEGACY_EXPANSION:
        return _LEGACY_EXPANSION[raw.strip().lower()]
    return _strict_actions(raw)


def serialize_actions(raw: Any) -> str:
    actions = _strict_actions(raw)
    return V2_PREFIX + ",".join(actions) if actions else ""


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
