from __future__ import annotations

import logging
from typing import Optional

try:
    from apscheduler.schedulers.background import BackgroundScheduler
except ImportError as _apscheduler_import_error:
    raise ImportError(
        "apscheduler não está instalado. Execute: pip install apscheduler>=3.10,<4.0"
    ) from _apscheduler_import_error

from appverbo.config.settings import settings

logger = logging.getLogger(__name__)

_scheduler: Optional[BackgroundScheduler] = None


def _run_mt940_drive_import() -> None:
    """Scheduled job: import MT940 files from Google Drive every 4 hours."""
    service_account_json = settings.GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON
    if not service_account_json:
        logger.debug("MT940 scheduler: GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON not set, skipping.")
        return

    import json

    from sqlalchemy import select

    from appverbo.core import SessionLocal
    from appverbo.menu_settings import normalize_menu_process_additional_fields
    from appverbo.models.member import Member
    from appverbo.models.sidebar_menu_setting import SidebarMenuSetting
    from appverbo.services.mt940_import_service import import_mt940_from_drive

    menu_key = settings.MT940_IMPORT_MENU_KEY
    folder_id = settings.GOOGLE_DRIVE_MT940_FOLDER_ID
    backup_folder_name = settings.GOOGLE_DRIVE_MT940_BACKUP_FOLDER_NAME

    try:
        with SessionLocal() as session:
            # Find the owner entity and pick the first active member with a user account
            from appverbo.models.entity import Entity
            from appverbo.models.member import MemberEntity
            from appverbo.models.user import User

            owner_entity = session.scalar(
                select(Entity).where(Entity.profile_scope == "owner").limit(1)
            )
            if owner_entity is None:
                owner_entity = session.scalar(select(Entity).limit(1))
            if owner_entity is None:
                logger.warning("MT940 scheduler: no Entity found, skipping.")
                return

            row = session.scalar(
                select(SidebarMenuSetting).where(SidebarMenuSetting.menu_key == menu_key)
            )
            additional_fields: list[dict] = []
            if row and row.menu_config:
                try:
                    from appverbo.menu_config_scope import build_effective_menu_config_v1
                    cfg = json.loads(row.menu_config)
                    effective = build_effective_menu_config_v1(cfg, selected_entity_id=owner_entity.id)
                    additional_fields = normalize_menu_process_additional_fields(
                        effective.get("additional_fields")
                    )
                except Exception:
                    pass

            member = session.scalar(
                select(Member)
                .join(MemberEntity, MemberEntity.member_id == Member.id)
                .join(User, User.member_id == Member.id)
                .where(MemberEntity.entity_id == owner_entity.id)
                .where(MemberEntity.status == "active")
                .limit(1)
            )
            if member is None:
                logger.warning("MT940 scheduler: no Member found for entity %s, skipping.", owner_entity.id)
                return

            db_num = owner_entity.internal_number
            entity_internal_number: str | None = (
                str(db_num) if db_num is not None else str(owner_entity.id)
            )

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
            logger.info(
                "MT940 scheduler done — files=%d inserted=%d duplicates=%d errors=%d",
                result.ficheiros_processados,
                result.linhas_inseridas,
                result.duplicadas_ignoradas,
                len(result.errors),
            )
    except Exception:
        logger.exception("MT940 scheduler: unhandled error")


def start_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        return

    _scheduler = BackgroundScheduler(timezone="UTC")
    _scheduler.add_job(
        _run_mt940_drive_import,
        trigger="interval",
        hours=4,
        id="mt940_drive_import",
        replace_existing=True,
        misfire_grace_time=300,
    )
    _scheduler.start()
    logger.info("APScheduler started — MT940 Drive import every 4 hours.")


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("APScheduler stopped.")
