from __future__ import annotations

import json
import logging
from typing import Optional

from fastapi import APIRouter, File, Request, UploadFile, status
from fastapi.responses import JSONResponse
from sqlalchemy import select

from appverbo.config.settings import settings
from appverbo.core import SessionLocal
from appverbo.models.member import Member
from appverbo.models.sidebar_menu_setting import SidebarMenuSetting
from appverbo.models.user import User
from appverbo.services.session import get_current_user, get_session_entity_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/import/mt940", tags=["import-mt940"])

_ALLOWED_EXTENSIONS = {".txt", ".csv", ".xlsx"}


def _load_additional_fields(session, menu_key: str, entity_id: object = None) -> list[dict]:
    from appverbo.menu_config_scope import build_effective_menu_config_v1
    from appverbo.menu_settings import normalize_menu_process_additional_fields

    row = session.scalar(
        select(SidebarMenuSetting).where(SidebarMenuSetting.menu_key == menu_key)
    )
    if row is None or not row.menu_config:
        return []
    try:
        raw_config = json.loads(row.menu_config)
    except (json.JSONDecodeError, TypeError):
        return []
    effective = build_effective_menu_config_v1(raw_config, selected_entity_id=entity_id)
    return normalize_menu_process_additional_fields(effective.get("additional_fields"))


def _get_member(session, user_id: int) -> Optional[Member]:
    return session.scalar(
        select(Member).join(User, User.member_id == Member.id).where(User.id == user_id)
    )


def _unauthorized() -> JSONResponse:
    return JSONResponse(
        {"status": "error", "detail": "Não autenticado."},
        status_code=status.HTTP_401_UNAUTHORIZED,
    )


def _no_member() -> JSONResponse:
    return JSONResponse(
        {"status": "error", "detail": "Membro não encontrado."},
        status_code=status.HTTP_404_NOT_FOUND,
    )


# ─── POST /import/mt940/upload ────────────────────────────────────────────────


@router.post("/upload")
async def import_mt940_upload(
    request: Request,
    file: UploadFile = File(...),
) -> JSONResponse:
    """Manual file upload — accepts .txt MT940 files."""
    with SessionLocal() as session:
        current_user = get_current_user(request, session)
        if current_user is None:
            return _unauthorized()

        member = _get_member(session, current_user["id"])
        if member is None:
            return _no_member()

        filename = (file.filename or "").lower()
        if not any(filename.endswith(ext) for ext in _ALLOWED_EXTENSIONS):
            return JSONResponse(
                {
                    "status": "error",
                    "detail": f"Formato não suportado. Use: {', '.join(_ALLOWED_EXTENSIONS)}",
                },
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        raw_bytes = await file.read()
        content = ""
        for encoding in ("utf-8", "latin-1", "cp1252"):
            try:
                content = raw_bytes.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        if not content:
            content = raw_bytes.decode("utf-8", errors="replace")

        entity_id = get_session_entity_id(request)
        menu_key = settings.MT940_IMPORT_MENU_KEY
        additional_fields = _load_additional_fields(session, menu_key, entity_id=entity_id)

        entity_internal_number: Optional[str] = None
        if entity_id is not None:
            from appverbo.models.entity import Entity
            db_num = session.scalar(
                select(Entity.internal_number).where(Entity.id == entity_id)
            )
            entity_internal_number = str(db_num) if db_num is not None else str(entity_id)

        from appverbo.services.mt940_import_service import import_mt940_content

        result = import_mt940_content(
            session=session,
            member=member,
            content=content,
            menu_key=menu_key,
            additional_fields=additional_fields,
            entity_internal_number=entity_internal_number,
        )

    return JSONResponse({
        "status": result.status,
        "linhas_inseridas": result.linhas_inseridas,
        "duplicadas_ignoradas": result.duplicadas_ignoradas,
        "ficheiros_processados": result.ficheiros_processados,
        "errors": result.errors,
    })


# ─── POST /import/mt940/drive ─────────────────────────────────────────────────


@router.post("/drive")
async def import_mt940_from_drive_endpoint(request: Request) -> JSONResponse:
    """Trigger a manual Google Drive import."""
    with SessionLocal() as session:
        current_user = get_current_user(request, session)
        if current_user is None:
            return _unauthorized()

        member = _get_member(session, current_user["id"])
        if member is None:
            return _no_member()

        service_account_json = settings.GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON
        if not service_account_json:
            return JSONResponse(
                {"status": "error", "detail": "Google Drive não configurado (GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON ausente)."},
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        entity_id = get_session_entity_id(request)
        folder_id = settings.GOOGLE_DRIVE_MT940_FOLDER_ID
        backup_folder_name = settings.GOOGLE_DRIVE_MT940_BACKUP_FOLDER_NAME
        menu_key = settings.MT940_IMPORT_MENU_KEY
        additional_fields = _load_additional_fields(session, menu_key, entity_id=entity_id)

        entity_internal_number: Optional[str] = None
        if entity_id is not None:
            from appverbo.models.entity import Entity
            db_num = session.scalar(
                select(Entity.internal_number).where(Entity.id == entity_id)
            )
            entity_internal_number = str(db_num) if db_num is not None else str(entity_id)

        from appverbo.services.mt940_import_service import import_mt940_from_drive

        try:
            result = import_mt940_from_drive(
                session=session,
                member=member,
                service_account_json=service_account_json,
                folder_id=folder_id,
                backup_folder_name=backup_folder_name,
                menu_key=menu_key,
                additional_fields=additional_fields,
                entity_internal_number=entity_internal_number,
            )
        except Exception as exc:
            logger.exception("MT940 Drive import endpoint error")
            return JSONResponse(
                {"status": "error", "detail": str(exc)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    return JSONResponse({
        "status": result.status,
        "linhas_inseridas": result.linhas_inseridas,
        "duplicadas_ignoradas": result.duplicadas_ignoradas,
        "ficheiros_processados": result.ficheiros_processados,
        "errors": result.errors,
    })
