from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


# ###################################################################################
# (1) CONTRATO PADRAO DE RETORNO DOS SUBPROCESSOS ADMINISTRATIVOS
# ###################################################################################

AdminOutcomeKind = Literal["redirect", "template", "json"]


@dataclass(frozen=True)
class AdminProcessOutcome:
    kind: AdminOutcomeKind
    redirect_url: str = ""
    status_code: int = 303
    template_name: str = ""
    template_context: dict[str, Any] | None = None
    json_payload: dict[str, Any] | None = None

    @classmethod
    def redirect(cls, url: str, status_code: int = 303) -> "AdminProcessOutcome":
        return cls(
            kind="redirect",
            redirect_url=str(url or ""),
            status_code=status_code,
        )

    @classmethod
    def template(
        cls,
        template_name: str,
        context: dict[str, Any],
        status_code: int = 200,
    ) -> "AdminProcessOutcome":
        return cls(
            kind="template",
            template_name=str(template_name or ""),
            template_context=dict(context or {}),
            status_code=status_code,
        )

    @classmethod
    def json(
        cls,
        payload: dict[str, Any],
        status_code: int = 200,
    ) -> "AdminProcessOutcome":
        return cls(
            kind="json",
            json_payload=dict(payload or {}),
            status_code=status_code,
        )