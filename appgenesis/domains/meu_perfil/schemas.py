from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AddressProfileFormInput:
    address: str
    city: str
    freguesia: str
    postal_code: str


@dataclass(frozen=True)
class TrainingProfileFormInput:
    training_discipulado_verbo_vida: str | None
    training_ebvv: str | None
    training_rhema: str | None
    training_escola_ministerial: str | None
    training_escola_missoes: str | None
    training_outros_enabled: str | None
    training_outros: str
