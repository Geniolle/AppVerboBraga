from __future__ import annotations

from dataclasses import dataclass

from fastapi import UploadFile


@dataclass(frozen=True)
class EmpresaProfileFormInput:
    entity_id: str
    name: str
    acronym: str
    tax_id: str
    email: str
    responsible_name: str
    door_number: str
    address: str
    city: str
    freguesia: str
    postal_code: str
    country: str
    phone: str
    description: str | None
    remove_logo: str | None
    entity_logo_file: UploadFile | None
