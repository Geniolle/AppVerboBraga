from __future__ import annotations

from pydantic import BaseModel, Field


class EntityCreateSchema(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    acronym: str = Field(default="", max_length=30)
    tax_id: str = Field(min_length=1, max_length=40)
    email: str = Field(min_length=1, max_length=150)
    responsible_name: str = Field(min_length=1, max_length=200)
    door_number: str = Field(min_length=1, max_length=30)
    address: str = Field(min_length=1, max_length=255)
    freguesia: str = Field(min_length=1, max_length=120)
    postal_code: str = Field(min_length=1, max_length=30)
    country: str = Field(min_length=1, max_length=120)
    phone: str = Field(min_length=1, max_length=30)
    entity_profile_scope: str = Field(default="legado", max_length=20)
    description: str = ""


class EntityUpdateSchema(EntityCreateSchema):
    entity_id: int
    entity_status: str = Field(default="active", max_length=20)
    remove_logo: str | None = None

