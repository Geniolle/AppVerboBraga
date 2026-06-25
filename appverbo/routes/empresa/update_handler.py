from __future__ import annotations

from fastapi import APIRouter, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from appverbo.core import *  # noqa: F403,F401
from appverbo.services import *  # noqa: F403,F401
from appverbo.models import Entity

from appverbo.routes.empresa.router import router


def _empresa_error_redirect(msg: str) -> RedirectResponse:
    url = build_users_new_url(menu="empresa", entity_error=msg) + "#empresa-card"
    return RedirectResponse(url=url, status_code=status.HTTP_303_SEE_OTHER)


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
    clean_entity_id = entity_id.strip()
    if not clean_entity_id.isdigit():
        return _empresa_error_redirect("Identificador de entidade inválido.")

    parsed_entity_id = int(clean_entity_id)

    entity_form_data, _ = clean_entity_form_data_v1(
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
    )

    with SessionLocal() as session:
        current_user = get_current_user(request, session)
        if current_user is None:
            return RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=status.HTTP_302_FOUND,
            )

        current_user_is_admin = is_admin_user(
            session, current_user["id"], current_user["login_email"]
        )
        if not current_user_is_admin:
            return _empresa_error_redirect("Apenas administradores podem editar o perfil da empresa.")

        selected_entity_id = get_session_entity_id(request)
        entity_permissions = get_user_entity_permissions(
            session,
            current_user["id"],
            current_user["login_email"],
            selected_entity_id,
        )

        # Escopo operacional: apenas entidades com vínculo ativo do utilizador.
        # O entity_id enviado pelo form DEVE corresponder à entidade ativa da sessão.
        resolved_entity_id = entity_permissions.get("selected_entity_id")
        allowed_data_ids = entity_permissions.get("allowed_data_entity_ids") or set()

        if resolved_entity_id is None:
            return _empresa_error_redirect("Sem entidade ativa. Contacte o administrador.")

        if parsed_entity_id != resolved_entity_id:
            return _empresa_error_redirect("Entidade não corresponde à entidade ativa da sessão.")

        if resolved_entity_id not in allowed_data_ids:
            return _empresa_error_redirect("Sem permissão operacional para editar o perfil desta entidade.")

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
        stored_logo_url, logo_error = save_entity_logo_upload(entity_logo_file)
        if logo_error:
            return _empresa_error_redirect(logo_error)

        delete_old_logo_after_commit = ""
        if stored_logo_url:
            entity.logo_url = stored_logo_url
            if current_logo_url.startswith("/static/entities/") and current_logo_url != stored_logo_url:
                delete_old_logo_after_commit = current_logo_url
        elif remove_logo == "1":
            entity.logo_url = None
            if current_logo_url.startswith("/static/entities/"):
                delete_old_logo_after_commit = current_logo_url

        # profile_scope e is_active NÃO são alterados pelo processo Empresa.
        apply_entity_form_data_v1(
            entity,
            entity_form_data,
            include_profile_scope=False,
            include_description=isinstance(description, str),
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

    url = build_users_new_url(menu="empresa", entity_success="Perfil da empresa atualizado com sucesso.") + "#empresa-card"
    return RedirectResponse(url=url, status_code=status.HTTP_303_SEE_OTHER)
