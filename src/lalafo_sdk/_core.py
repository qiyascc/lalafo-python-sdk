from __future__ import annotations

import asyncio
import random
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Generator, Mapping, Optional, TypeVar, Union

import httpx

from .config import Query, Settings, load_settings
from .errors import (
    APIError,
    AuthenticationError,
    BlockedError,
    CaptchaRequiredError,
    InvalidRequestError,
    NotSentError,
    OutcomeUnknownError,
    RateLimitError,
    SessionRequiredError,
    TransportError,
    for_status,
)
from .messages import text
from .models import Session

T = TypeVar("T")

NOT_SENT = (httpx.ConnectError, httpx.ConnectTimeout, httpx.PoolTimeout, httpx.UnsupportedProtocol)
RETRY_STATUSES = frozenset({429, 500, 502, 503, 504})
DEVICE = "pc"

SessionLike = Union[Session, Mapping[str, Any], None]
SessionHook = Callable[[Session], Any]


@dataclass
class Op:
    method: str
    endpoint: str
    parse: Callable[[Any], Any] = lambda body: body
    query: Optional[Query] = None
    body: Optional[Any] = None
    files: Optional[dict[str, Any]] = None
    data: Optional[dict[str, str]] = None
    path_params: Mapping[str, Any] = field(default_factory=dict)
    headers: Mapping[str, str] = field(default_factory=dict)
    safe: bool = False
    auth: bool = True


@dataclass(frozen=True)
class Raw:
    op: Op


@dataclass(frozen=True)
class Pause:
    seconds: float


Step = Any
Flow = Generator[Step, Any, T]


class Outcome:
    def __init__(self, value: Any = None, error: Optional[Exception] = None, wait: Optional[float] = None) -> None:
        self.value = value
        self.error = error
        self.wait = wait


def _number(value: Optional[str]) -> Optional[float]:
    try:
        return float(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def challenged(response: httpx.Response) -> bool:
    if response.headers.get("cf-mitigated", "").lower() == "challenge":
        return True
    if response.status_code in (403, 503) and "cloudflare" in response.headers.get("server", "").lower():
        return "text/html" in response.headers.get("content-type", "")
    return False


def error_message(body: Any) -> Optional[str]:
    if isinstance(body, list):
        parts = [f"{e.get('field')}: {e.get('message')}" if e.get("field") else str(e.get("message"))
                 for e in body if isinstance(e, Mapping)]
        return "; ".join(parts) or None
    if isinstance(body, Mapping):
        value = body.get("message") or body.get("error") or body.get("name")
        return str(value) if value else None
    return None


def asks_captcha(body: Any) -> bool:
    return isinstance(body, list) and any(isinstance(e, Mapping) and e.get("field") == "captcha" for e in body)


def coerce_session(value: SessionLike) -> Optional[Session]:
    if value is None or isinstance(value, Session):
        return value
    if isinstance(value, Mapping) and value.get("token"):
        return Session.from_mapping(value)
    raise InvalidRequestError(text("value.session"))


class Engine:
    def __init__(
        self,
        session: SessionLike = None,
        *,
        settings: Optional[Settings] = None,
        config_file: Optional[str] = None,
        on_session: Optional[SessionHook] = None,
        **overrides: Any,
    ) -> None:
        if settings is None:
            settings = load_settings(config_file, **overrides)
        elif overrides:
            changes = {k: v for k, v in overrides.items() if v is not None}
            settings = load_settings(None, **{**settings.model_dump(), **changes})
        self.settings = settings
        settings.check_transport()
        self.on_session = on_session
        self.session: Optional[Session] = coerce_session(session)
        self.user_hash = (self.session.user_hash if self.session else "") or str(uuid.uuid4())

    def __repr__(self) -> str:
        signed = self.session.user_id if self.session else None
        return f"{type(self).__name__}(base_url={self.settings.base_url!r}, user_id={signed!r})"

    def use_session(self, session: SessionLike) -> Optional[Session]:
        self.session = coerce_session(session)
        if self.session and self.session.user_hash:
            self.user_hash = self.session.user_hash
        return self.session

    def _store(self, session: Session) -> Session:
        self.session = session
        self.user_hash = session.user_hash or self.user_hash
        if self.on_session is not None:
            self.on_session(session)
        return session

    def _timeout(self) -> httpx.Timeout:
        return httpx.Timeout(self.settings.timeout, connect=self.settings.connect_timeout)

    def _headers(self, op: Op) -> dict[str, str]:
        token = self.session.token if self.session and op.auth else ""
        headers = {
            "Accept": "application/json",
            "User-Agent": self.settings.resolved_user_agent(),
            "device": DEVICE,
            "language": self.settings.language,
            "country-id": str(self.settings.country_id),
            "request-id": f"react-client-{uuid.uuid4()}",
            "user-hash": self.user_hash,
            "Authorization": f"Bearer {token}" if token else "",
        }
        headers.update(op.headers)
        return headers

    def _request_args(self, op: Op) -> dict[str, Any]:
        args: dict[str, Any] = {"headers": self._headers(op)}
        if op.files is not None:
            args["files"] = op.files
            args["data"] = op.data or {}
        elif op.body is not None:
            args["json"] = op.body
        return args

    def _url(self, op: Op) -> str:
        return self.settings.url(op.endpoint, op.query, **op.path_params)

    def _backoff(self, attempt: int) -> float:
        base = self.settings.backoff_base
        return min(self.settings.backoff_cap, base * (2**attempt)) + random.uniform(0, base / 2)

    def _on_exception(self, op: Op, exc: Exception, attempt: int) -> Outcome:
        path = self.settings.path(op.endpoint, **op.path_params)
        can_retry = attempt < self.settings.max_retries
        if isinstance(exc, NOT_SENT):
            if can_retry:
                return Outcome(wait=self._backoff(attempt))
            return Outcome(error=NotSentError(text("error.connect", error=exc), path=path))
        if op.safe:
            if can_retry:
                return Outcome(wait=self._backoff(attempt))
            return Outcome(error=TransportError(text("error.timeout", error=exc), path=path))
        return Outcome(error=OutcomeUnknownError(text("error.unknown_outcome", reason=type(exc).__name__), path=path))

    def _on_response(self, op: Op, response: httpx.Response, attempt: int) -> Outcome:
        path = self.settings.path(op.endpoint, **op.path_params)
        status = response.status_code
        can_retry = attempt < self.settings.max_retries
        if challenged(response):
            if can_retry:
                return Outcome(wait=self._backoff(attempt))
            return Outcome(error=BlockedError(text("error.blocked", attempts=attempt + 1), path=path))
        if status == 429 and can_retry:
            hint = _number(response.headers.get("retry-after"))
            return Outcome(wait=min(self.settings.backoff_cap, hint) if hint is not None else self._backoff(attempt))
        if status in RETRY_STATUSES and status != 429:
            if op.safe and can_retry:
                return Outcome(wait=self._backoff(attempt))
            if not op.safe:
                return Outcome(error=OutcomeUnknownError(text("error.unknown_outcome", reason=f"HTTP {status}"),
                                                         status_code=status, path=path))
        if not response.content:
            if status < 400:
                return Outcome(value=op.parse(None))
            return Outcome(error=for_status(status)(text("error.refused"), status_code=status, path=path))
        try:
            body = response.json()
        except ValueError:
            snippet = response.text[:200]
            if status < 400 and not op.safe:
                return Outcome(error=OutcomeUnknownError(text("error.body", body=snippet), status_code=status,
                                                         path=path))
            return Outcome(error=for_status(status)(text("error.body", body=snippet), status_code=status,
                                                    body=snippet, path=path))
        if status >= 400:
            if asks_captcha(body):
                return Outcome(error=CaptchaRequiredError(text("error.captcha"), status_code=status, body=body,
                                                          path=path))
            kind = for_status(status)
            error_args: dict[str, Any] = {"status_code": status, "body": body, "path": path}
            if kind is RateLimitError:
                error_args["retry_after"] = _number(response.headers.get("retry-after"))
            return Outcome(error=kind(error_message(body) or text("error.refused"), **error_args))
        return Outcome(value=op.parse(body))

    def _renew(self, soft: bool = False) -> Flow[Optional[Session]]:
        session = self.session
        if session is None or not session.refresh_token:
            if soft:
                return session
            raise AuthenticationError(text("error.no_refresh"), status_code=401)
        try:
            body = yield Raw(Op("POST", "renew", body={"refresh_token": session.refresh_token}))
        except AuthenticationError:
            raise AuthenticationError(text("error.no_refresh"), status_code=401) from None
        except (TransportError, APIError):
            if soft and not session.expired():
                return session
            raise
        if not isinstance(body, Mapping) or not body.get("token"):
            if soft and not session.expired():
                return session
            raise AuthenticationError(text("error.no_token"), status_code=401, body=body)
        return self._store(session.renewed(body))

    def _guard(self, op: Op) -> Flow[Any]:
        if op.auth:
            if self.session is None:
                raise SessionRequiredError(text("error.no_session"))
            if self.session.renew_due(self.settings.renew_at):
                yield from self._renew(soft=True)
        try:
            result = yield Raw(op)
        except AuthenticationError as error:
            if not op.auth or error.status_code != 401 or not (self.session and self.session.refresh_token):
                raise
            yield from self._renew()
            result = yield Raw(op)
        return result


class SyncEngine(Engine):
    def __init__(self, *args: Any, http_client: Optional[httpx.Client] = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._owns_http = http_client is None
        self._http = http_client or httpx.Client(timeout=self._timeout())

    def close(self) -> None:
        if self._owns_http:
            self._http.close()

    def __enter__(self: T) -> T:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    def _sleep(self, seconds: float) -> None:
        if seconds > 0:
            time.sleep(seconds)

    def _send(self, op: Op) -> Any:
        url = self._url(op)
        attempt = 0
        while True:
            try:
                response = self._http.request(op.method, url, **self._request_args(op))
            except httpx.HTTPError as exc:
                outcome = self._on_exception(op, exc, attempt)
            else:
                outcome = self._on_response(op, response, attempt)
            if outcome.wait is not None:
                self._sleep(outcome.wait)
                attempt += 1
                continue
            if outcome.error is not None:
                raise outcome.error
            return outcome.value

    def _run(self, op: Op) -> Any:
        return self._flow(self._guard(op))

    def _flow(self, flow: Flow[T]) -> T:
        reply: Any = None
        error: Optional[BaseException] = None
        while True:
            try:
                step = flow.throw(error) if error is not None else flow.send(reply)
            except StopIteration as done:
                result: T = done.value
                return result
            reply, error = None, None
            try:
                if isinstance(step, Pause):
                    self._sleep(step.seconds)
                elif isinstance(step, Raw):
                    reply = self._send(step.op)
                else:
                    reply = self._run(step)
            except Exception as exc:
                error = exc


class AsyncEngine(Engine):
    def __init__(self, *args: Any, http_client: Optional[httpx.AsyncClient] = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._owns_http = http_client is None
        self._http = http_client or httpx.AsyncClient(timeout=self._timeout())

    async def close(self) -> None:
        if self._owns_http:
            await self._http.aclose()

    async def __aenter__(self: T) -> T:
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.close()

    async def _sleep(self, seconds: float) -> None:
        if seconds > 0:
            await asyncio.sleep(seconds)

    async def _send(self, op: Op) -> Any:
        url = self._url(op)
        attempt = 0
        while True:
            try:
                response = await self._http.request(op.method, url, **self._request_args(op))
            except httpx.HTTPError as exc:
                outcome = self._on_exception(op, exc, attempt)
            else:
                outcome = self._on_response(op, response, attempt)
            if outcome.wait is not None:
                await self._sleep(outcome.wait)
                attempt += 1
                continue
            if outcome.error is not None:
                raise outcome.error
            return outcome.value

    async def _run(self, op: Op) -> Any:
        return await self._flow(self._guard(op))

    async def _flow(self, flow: Flow[T]) -> T:
        reply: Any = None
        error: Optional[BaseException] = None
        while True:
            try:
                step = flow.throw(error) if error is not None else flow.send(reply)
            except StopIteration as done:
                result: T = done.value
                return result
            reply, error = None, None
            try:
                if isinstance(step, Pause):
                    await self._sleep(step.seconds)
                elif isinstance(step, Raw):
                    reply = await self._send(step.op)
                else:
                    reply = await self._run(step)
            except Exception as exc:
                error = exc
