from __future__ import annotations

from fastapi import File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse

from appgenesis.db.session import SessionLocal
from appgenesis.domains.empresa.schemas import EmpresaProfileFormInput
from appgenesis.domains.empresa.use_cases import execute_update_empresa_profile
from appgenesis.web.responses import outcome_to_response

from appgenesis.routes.empresa.router import router


@router.post("/empresa/update", response_class=HTMLResponse)
def update_empresa_profile(
    request: Request,
    entity_id: str = Form(...),
    name: str = Form(...),
    acronym: str = Form(""),
    tax_id: str = Form(...),
    email: str = Form(...),
    responsible_name: str = Form(...),
    door_number: str = Form(...),
    address: str = Form(...),
    city: str = Form(...),
    freguesia: str = Form(...),
    postal_code: str = Form(...),
    country: str = Form(...),
    phone: str = Form(...),
    description: str | None = Form(default=None),
    remove_logo: str | None = Form(default=None),
    entity_logo_file: UploadFile | None = File(default=None),
) -> HTMLResponse:
    form = EmpresaProfileFormInput(
        entity_id=entity_id,
        name=name,
        acronym=acronym,
        tax_id=tax_id,
        email=email,
        responsible_name=responsible_name,
        door_number=door_number,
        address=address,
        city=city,
        freguesia=freguesia,
        postal_code=postal_code,
        country=country,
        phone=phone,
        description=description,
        remove_logo=remove_logo,
        entity_logo_file=entity_logo_file,
    )

    with SessionLocal() as session:
        outcome = execute_update_empresa_profile(session, request, form)

    return outcome_to_response(outcome, request)
