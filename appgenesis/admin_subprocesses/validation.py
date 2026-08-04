from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Literal

from .models import AdminSubprocessConfig
from .registry import list_admin_subprocess_configs
from .repositories.base import BaseAdminSubprocessRepository
from .service import build_admin_subprocess_config_for_entity_context_v1

AdminSubprocessIssueSeverity = Literal["error", "warning"]

_MIGRATION_STATUSES_EXPECTING_REPOSITORY = {"native", "native_next"}
_ENTITY_CONTEXT_VALIDATION_PROBE = {"selected_entity_number": "1000"}


@dataclass(frozen=True)
class AdminSubprocessValidationIssue:
    subprocess_key: str
    severity: AdminSubprocessIssueSeverity
    message: str


def resolve_admin_subprocess_repository_class(
    dotted_path: str,
) -> type[BaseAdminSubprocessRepository] | None:
    clean_path = str(dotted_path or "").strip()

    if not clean_path or "." not in clean_path:
        return None

    module_path, _, class_name = clean_path.rpartition(".")

    try:
        module = importlib.import_module(module_path)
        resolved = getattr(module, class_name)
    except (ImportError, AttributeError):
        return None

    if not isinstance(resolved, type) or not issubclass(resolved, BaseAdminSubprocessRepository):
        return None

    return resolved


def is_admin_subprocess_effectively_migrated(config: AdminSubprocessConfig) -> bool:
    return resolve_admin_subprocess_repository_class(config.repository_class) is not None


def validate_admin_subprocess_config(
    config: AdminSubprocessConfig,
) -> list[AdminSubprocessValidationIssue]:
    issues: list[AdminSubprocessValidationIssue] = []
    effective_config = build_admin_subprocess_config_for_entity_context_v1(
        config,
        _ENTITY_CONTEXT_VALIDATION_PROBE,
    )

    if config.repository_class:
        if resolve_admin_subprocess_repository_class(config.repository_class) is None:
            issues.append(
                AdminSubprocessValidationIssue(
                    subprocess_key=config.key,
                    severity="error",
                    message=(
                        f"repository_class '{config.repository_class}' não resolve para uma "
                        "subclasse de BaseAdminSubprocessRepository."
                    ),
                )
            )
    elif config.enabled and config.migration_status in _MIGRATION_STATUSES_EXPECTING_REPOSITORY:
        issues.append(
            AdminSubprocessValidationIssue(
                subprocess_key=config.key,
                severity="warning",
                message=(
                    f"subprocesso '{config.key}' está registado (enabled=True, "
                    f"migration_status='{config.migration_status}') mas não tem repository_class "
                    "— ainda é servido por handlers legados, não pelo motor administrativo "
                    "(registado != efetivamente migrado)."
                ),
            )
        )

    if effective_config.uses_entity_context:
        field_keys = [
            str(field.key or "").strip().lower()
            for field in effective_config.fields
            if str(field.key or "").strip()
        ]
        unique_field_keys = set(field_keys)
        status_field_key = str(effective_config.status_field or "").strip().lower()
        entity_field_key = "entity_number"

        if len(field_keys) != len(unique_field_keys):
            issues.append(
                AdminSubprocessValidationIssue(
                    subprocess_key=config.key,
                    severity="error",
                    message="Configuração entity-scoped contém chaves de campo duplicadas.",
                )
            )

        if status_field_key and status_field_key not in unique_field_keys:
            issues.append(
                AdminSubprocessValidationIssue(
                    subprocess_key=config.key,
                    severity="error",
                    message="Configuração entity-scoped não contém o campo Estado.",
                )
            )

        entity_field = next(
            (
                field
                for field in effective_config.fields
                if str(field.key or "").strip().lower() == entity_field_key
            ),
            None,
        )
        if entity_field is None:
            issues.append(
                AdminSubprocessValidationIssue(
                    subprocess_key=config.key,
                    severity="error",
                    message="Configuração entity-scoped não contém o campo Entidade.",
                )
            )
        elif str(entity_field.field_type or "").strip().lower() != "readonly":
            issues.append(
                AdminSubprocessValidationIssue(
                    subprocess_key=config.key,
                    severity="error",
                    message="Campo Entidade de subprocesso entity-scoped não é readonly.",
                )
            )

        if status_field_key in unique_field_keys and entity_field is not None:
            status_index = field_keys.index(status_field_key)
            entity_index = field_keys.index(entity_field_key)
            if entity_index != status_index + 1:
                issues.append(
                    AdminSubprocessValidationIssue(
                        subprocess_key=config.key,
                        severity="error",
                        message="Campos Estado e Entidade devem ficar adjacentes.",
                    )
                )

    return issues


def validate_admin_subprocess_registry() -> list[AdminSubprocessValidationIssue]:
    issues: list[AdminSubprocessValidationIssue] = []

    for config in list_admin_subprocess_configs():
        issues.extend(validate_admin_subprocess_config(config))

    return issues
