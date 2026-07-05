from __future__ import annotations


class DomainError(Exception):
    """Base class for errors raised by use cases/services across domains."""


class PermissionDeniedError(DomainError):
    """Raised when the acting user lacks permission for the requested operation."""


class ValidationError(DomainError):
    """Raised when input data fails domain validation rules."""


class NotFoundError(DomainError):
    """Raised when a requested domain entity does not exist or is not accessible."""


__all__ = [
    "DomainError",
    "PermissionDeniedError",
    "ValidationError",
    "NotFoundError",
]
