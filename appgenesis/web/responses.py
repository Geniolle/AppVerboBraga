from __future__ import annotations

"""Convert shared outcome dataclasses (appgenesis.shared.results) into actual
Starlette/FastAPI responses, using the single Jinja2Templates instance from
appgenesis.web.templates.
"""

from fastapi import Request
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.responses import Response

from appgenesis.shared.results import JsonOutcome, Outcome, RedirectOutcome, TemplateOutcome
from appgenesis.web.templates import templates


def outcome_to_response(outcome: Outcome, request: Request | None = None) -> Response:
    """Convert a RedirectOutcome/TemplateOutcome/JsonOutcome into a Response.

    `request` is required for TemplateOutcome (Jinja2Templates needs it in the
    render context) and ignored otherwise.
    """

    if isinstance(outcome, RedirectOutcome):
        return RedirectResponse(url=outcome.url, status_code=outcome.status_code)

    if isinstance(outcome, JsonOutcome):
        return JSONResponse(content=outcome.payload, status_code=outcome.status_code)

    if isinstance(outcome, TemplateOutcome):
        if request is None:
            raise ValueError("request is required to render a TemplateOutcome")
        context = {"request": request, **outcome.context}
        return templates.TemplateResponse(
            outcome.template_name, context, status_code=outcome.status_code
        )

    raise TypeError(f"Unsupported outcome type: {type(outcome)!r}")


__all__ = ["outcome_to_response"]
