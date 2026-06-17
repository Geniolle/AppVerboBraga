
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from appverbo.admin_subprocesses.models import AdminSubprocessConfig


class BaseAdminSubprocessRepository(ABC):
    config: AdminSubprocessConfig

    def __init__(self, config: AdminSubprocessConfig) -> None:
        self.config = config

    def get_field_options(
        self,
        session: Any,
        context: dict[str, Any] | None = None,
    ) -> dict[str, tuple[tuple[str, str], ...]]:
        return {}

    @abstractmethod
    def list_rows(self, session: Any, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def get_for_edit(
        self,
        session: Any,
        edit_key: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        raise NotImplementedError

    def create(
        self,
        session: Any,
        payload: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> bool:
        raise NotImplementedError

    def update(
        self,
        session: Any,
        edit_key: str,
        payload: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> bool:
        raise NotImplementedError

    def move(
        self,
        session: Any,
        edit_key: str,
        direction: str,
        context: dict[str, Any] | None = None,
    ) -> bool:
        raise NotImplementedError

    def delete(
        self,
        session: Any,
        edit_key: str,
        context: dict[str, Any] | None = None,
    ) -> bool:
        raise NotImplementedError
