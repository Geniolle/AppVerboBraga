from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LoginFormInput:
    email: str
    password: str
    entity_id: str
    login_mode: str


@dataclass(frozen=True)
class SignupFormInput:
    full_name: str
    country: str
    primary_phone: str
    email: str
    password: str
    confirm_password: str
    entity_id: str
