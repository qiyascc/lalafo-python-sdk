from __future__ import annotations

import base64
import json
import time
from typing import Any, Callable, Union

import httpx
import pytest

from lalafo_sdk import AsyncLalafo, Lalafo, Session

Reply = Union[httpx.Response, Exception, Callable[[httpx.Request], httpx.Response]]
PHOTO = b"\xff\xd8" + b"x" * 30000


def jwt(**claims: Any) -> str:
    enc = lambda d: base64.urlsafe_b64encode(json.dumps(d).encode()).decode().rstrip("=")
    return f"{enc({'alg': 'HS256'})}.{enc(claims)}.sig"


def fresh_token(user_id: int = 77) -> str:
    now = int(time.time())
    return jwt(id=user_id, iat=now, sensitive_exp=now + 86400)


def old_token(user_id: int = 77) -> str:
    now = int(time.time())
    return jwt(id=user_id, iat=now - 80000, sensitive_exp=now + 6400)


def session(token: str = "", refresh: str = "rf1") -> Session:
    return Session(token or fresh_token(), refresh, "uh-1", "77")


PARAMS = [
    {"id": 69, "name": "Otaqların sayı", "kind": "dropdown", "is_required": True, "is_multi_select_posting": False,
     "values": [{"id": 2774, "value": "2 otaqlı"}, {"id": 2775, "value": "3 otaqlı"}]},
    {"id": 70, "name": "Sahə (m2)", "kind": "input", "is_required": False},
    {"id": 1239, "name": "Mənzilin şəraiti", "kind": "dropdown", "is_required": False,
     "is_multi_select_posting": True, "values": [{"id": 28272, "value": "Kombi"}, {"id": 27535, "value": "Kredit"}]},
]

FORM = {"category_id": 4800, "city_id": 103261, "description": "Satılır 2 otaqlı köhnə tikili, təmirli.",
        "price": 80000, "params": [{"id": 69, "value_id": 2774}, {"id": 70, "value": "42"},
                                   {"id": 1239, "value_id": 28272}, {"id": 1239, "value_id": 27535}]}


def ad(ad_id: int = 4242, status: int = 1, **extra: Any) -> dict:
    return {"id": ad_id, "status_id": status, "title": "Bakı, 2 otaqlı, Köhnə tikili, 42 kv. m",
            "price": 80000, "currency": "AZN", "category_id": 4800, "city_id": 103261,
            "url": f"/baku/ads/baki-2-otaqli-id-{ad_id}", "created_time": 1793798674, "updated_time": 1793869042,
            "images": [{"id": 901, "is_main": True, "thumbnail_url": "https://img5.lalafo.com/t.jpg",
                        "original_url": "https://img5.lalafo.com/o.jpg"}],
            "params": [{"id": 69, "name": "Otaqların sayı", "value": "2 otaqlı", "value_id": 2774}],
            "available_campaign_types": [], **extra}


class Gateway:
    def __init__(self) -> None:
        self.requests: list[httpx.Request] = []
        self.replies: list[Reply] = []

    def reply(self, body: Any = None, status: int = 200, headers: Any = None) -> Gateway:
        content = b"" if body is None else (body if isinstance(body, bytes) else json.dumps(body).encode())
        self.replies.append(httpx.Response(status, content=content, headers=headers))
        return self

    def challenge(self) -> Gateway:
        self.replies.append(httpx.Response(403, content=b"<html>Just a moment</html>", headers={
            "server": "cloudflare", "content-type": "text/html", "cf-mitigated": "challenge"}))
        return self

    def fail(self, exc: Exception) -> Gateway:
        self.replies.append(exc)
        return self

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        reply = self.replies.pop(0) if self.replies else httpx.Response(200, json={})
        if isinstance(reply, Exception):
            raise reply
        if callable(reply):
            return reply(request)
        return reply

    def body(self, index: int = -1) -> Any:
        return json.loads(self.requests[index].content.decode())

    def header(self, name: str, index: int = -1) -> str:
        return str(self.requests[index].headers.get(name, ""))

    def has_header(self, name: str, index: int = -1) -> bool:
        return name in self.requests[index].headers

    @property
    def paths(self) -> list[str]:
        return [r.url.path for r in self.requests]

    @property
    def methods(self) -> list[str]:
        return [r.method for r in self.requests]

    def query(self, index: int = -1) -> list[tuple[str, str]]:
        return list(self.requests[index].url.params.multi_items())


@pytest.fixture
def gw() -> Gateway:
    return Gateway()


def _quiet(client: Any) -> Any:
    client._backoff = lambda attempt: 0.0
    client._sleep = (lambda seconds: None) if isinstance(client, Lalafo) else _no_wait
    return client


async def _no_wait(seconds: float) -> None:
    return None


@pytest.fixture
def saved() -> list[Session]:
    return []


@pytest.fixture
def lf(gw: Gateway, saved: list[Session]) -> Lalafo:
    client = Lalafo(max_retries=2, on_session=saved.append,
                    http_client=httpx.Client(transport=httpx.MockTransport(gw)))
    return _quiet(client)


@pytest.fixture
def signed(gw: Gateway, saved: list[Session]) -> Lalafo:
    client = Lalafo(session(), max_retries=2, on_session=saved.append,
                    http_client=httpx.Client(transport=httpx.MockTransport(gw)))
    return _quiet(client)


@pytest.fixture
def alf(gw: Gateway, saved: list[Session]) -> AsyncLalafo:
    client = AsyncLalafo(max_retries=2, on_session=saved.append,
                         http_client=httpx.AsyncClient(transport=httpx.MockTransport(gw)))
    return _quiet(client)
