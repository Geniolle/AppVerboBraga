from __future__ import annotations

from fastapi import Request
from sqlalchemy.orm import Session

from appgenesis.core import BASE_DIR
from appgenesis.domains.empresa.permissions import authorize_empresa_edit
from appgenesis.domains.empresa.schemas import EmpresaProfileFormInput
from appgenesis.models import Entity
from appgenesis.services.entities import (
    apply_entity_form_data_v1,
    clean_entity_form_data_v1,
    get_duplicate_entity_name_id_v1,
    save_entity_logo_upload,
    validate_entity_required_fields_v1,
)
from appgenesis.services.page import build_users_new_url
from appgenesis.services.session import get_current_user, get_session_entity_id
from appgenesis.shared.results import RedirectOutcome


def _empresa_error_redirect(msg: str) -> RedirectOutcome:
    url = build_users_new_url(menu="empresa", entity_error=msg) + "#empresa-card"
    return RedirectOutcome(url=url, status_code=303)


def execute_update_empresa_profile(
    session: Session, request: Request, form: EmpresaProfileFormInput
) -> RedirectOutcome:
    clean_entity_id = form.entity_id.strip()
    if not clean_entity_id.isdigit():
        return _empresa_error_redirect("Identificador de entidade inválido.")

    parsed_entity_id = int(clean_entity_id)

    entity_form_data, _ = clean_entity_form_data_v1(
        name=form.name,
        acronym=form.acronym,
        tax_id=form.tax_id,
        email=form.email,
        responsible_name=form.responsible_name,
        door_number=form.door_number,
        address=form.address,
        city=form.city,
        freguesia=form.freguesia,
        postal_code=form.postal_code,
        country=form.country,
        phone=form.phone,
        description=form.description,
    )

    current_user = get_current_user(request, session)
    if current_user is None:
        return RedirectOutcome(url="/login?error=Efetue login para continuar.", status_code=302)

    selected_entity_id = get_session_entity_id(request)
    resolved_entity_id, error_message = authorize_empresa_edit(
        session, current_user, selected_entity_id, parsed_entity_id
    )
    if error_message:
        return _empresa_error_redirect(error_message)

    entity = session.get(Entity, resolved_entity_id)
    if entity is None:
        return _empresa_error_redirect("Entidade não encontrada.")

    required_field_labels = validate_entity_required_fields_v1(entity_form_data)
    if required_field_labels:
        return _empresa_error_redirect(
            "Preencha os campos obrigatórios: " + ", ".join(required_field_labels) + "."
        )

    duplicate_id = get_duplicate_entity_name_id_v1(
        session,
        entity_form_data["name"],
        ignore_entity_id=resolved_entity_id,
    )
    if duplicate_id is not None:
        return _empresa_error_redirect("Já existe outra entidade com este nome.")

    current_logo_url = entity.logo_url or ""
    stored_logo_url, logo_error = save_entity_logo_upload(form.entity_logo_file)
    if logo_error:
        return _empresa_error_redirect(logo_error)

    delete_old_logo_after_commit = ""
    if stored_logo_url:
        entity.logo_url = stored_logo_url
        if current_logo_url.startswith("/static/entities/") and current_logo_url != stored_logo_url:
            delete_old_logo_after_commit = current_logo_url
    elif form.remove_logo == "1":
        entity.logo_url = None
        if current_logo_url.startswith("/static/entities/"):
            delete_old_logo_after_commit = current_logo_url

    # profile_scope e is_active NÃO são alterados pelo processo Empresa.
    apply_entity_form_data_v1(
        entity,
        entity_form_data,
        include_profile_scope=False,
        include_description=isinstance(form.description, str),
    )

    try:
        session.commit()
    except Exception:
        session.rollback()
        if stored_logo_url.startswith("/static/entities/"):
            (BASE_DIR / stored_logo_url.lstrip("/")).unlink(missing_ok=True)
        return _empresa_error_redirect("Não foi possível guardar as alterações. Tente novamente.")

    if delete_old_logo_after_commit:
        (BASE_DIR / delete_old_logo_after_commit.lstrip("/")).unlink(missing_ok=True)

    url = (
        build_users_new_url(menu="empresa", entity_success="Perfil da empresa atualizado com sucesso.")
        + "#empresa-card"
    )
    return RedirectOutcome(url=url, status_code=303)
