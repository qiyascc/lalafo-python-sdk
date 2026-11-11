from __future__ import annotations

from typing import Any, Mapping, Optional


class LalafoError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ConfigurationError(LalafoError):
    pass


class InvalidRequestError(LalafoError, ValueError):
    pass


class SessionRequiredError(LalafoError):
    pass


class TransportError(LalafoError):
    def __init__(self, message: str, *, path: str = "") -> None:
        super().__init__(message)
        self.path = path


class NotSentError(TransportError):
    pass


class BlockedError(TransportError):
    pass


class OutcomeUnknownError(TransportError):
    def __init__(self, message: str, *, status_code: Optional[int] = None, **kwargs: Any) -> None:
        super().__init__(message, **kwargs)
        self.status_code = status_code


class APIError(LalafoError):
    def __init__(self, message: str, *, status_code: int, body: Any = None, path: str = "") -> None:
        super().__init__(message)
        self.status_code = status_code
        self.body = body
        self.path = path

    def __str__(self) -> str:
        return f"[{self.status_code}] {self.message}"

    @property
    def fields(self) -> dict[str, str]:
        items = self.body if isinstance(self.body, list) else []
        return {str(e.get("field")): str(e.get("message")) for e in items if isinstance(e, Mapping) and e.get("field")}


class BadRequestError(APIError):
    pass


class ValidationError(BadRequestError):
    pass


class CaptchaRequiredError(BadRequestError):
    pass


class AuthenticationError(APIError):
    pass


class ForbiddenError(APIError):
    pass


class NotFoundError(APIError):
    pass


class ConflictError(APIError):
    pass


class RateLimitError(APIError):
    def __init__(self, message: str, *, retry_after: Optional[float] = None, **kwargs: Any) -> None:
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class ServerError(APIError):
    pass


class WaitTimeoutError(LalafoError):
    def __init__(self, message: str, *, ad: Any = None) -> None:
        super().__init__(message)
        self.ad = ad


def for_status(status: int) -> type[APIError]:
    if status == 401:
        return AuthenticationError
    if status == 403:
        return ForbiddenError
    if status == 404:
        return NotFoundError
    if status == 409:
        return ConflictError
    if status in (400, 422):
        return ValidationError
    if status == 429:
        return RateLimitError
    if status >= 500:
        return ServerError
    if status >= 400:
        return BadRequestError
    return APIError
