from __future__ import annotations

from pydantic import BaseModel, Field


class UserCreateSchema(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    primary_phone: str = Field(min_length=1, max_length=30)
    email: str = Field(min_length=3, max_length=150)
    profile_id: str = ""


class UserUpdateSchema(BaseModel):
    user_id: int
    full_name: str = Field(min_length=1, max_length=200)
    primary_phone: str = Field(min_length=1, max_length=30)
    email: str = Field(min_length=3, max_length=150)
    account_status: str = Field(default="active", max_length=20)
    profile_id: str = ""

