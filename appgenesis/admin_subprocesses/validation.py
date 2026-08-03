from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Literal

from .models import AdminSubprocessConfig
from .registry import list_admin_subprocess_configs
from .repositories.base import BaseAdminSubprocessRepository

AdminSubprocessIssueSeverity = Literal["error", "warning"]

_MIGRATION_STATUSES_EXPECTING_REPOSITORY = {"native", "native_next"}


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

    return issues


def validate_admin_subprocess_registry() -> list[AdminSubprocessValidationIssue]:
    issues: list[AdminSubprocessValidationIssue] = []

    for config in list_admin_subprocess_configs():
        issues.extend(validate_admin_subprocess_config(config))

    return issues
