from __future__ import annotations

from pydantic import BaseModel, Field


class LoginFormSchema(BaseModel):
    email: str = Field(min_length=3, max_length=150)
    password: str = Field(min_length=1, max_length=255)
    entity_id: str = ""
    login_mode: str = "login"


class SignupFormSchema(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    country: str = Field(min_length=2, max_length=2)
    primary_phone: str = Field(min_length=1, max_length=30)
    email: str = Field(min_length=3, max_length=150)
    password: str = Field(min_length=8, max_length=255)
    confirm_password: str = Field(min_length=8, max_length=255)
    entity_id: str = ""
