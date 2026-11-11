from __future__ import annotations

from typing import Any, Mapping, Optional

from ._core import AsyncEngine, Op, SyncEngine
from .resources import Ads, Auth, Catalog


class _Namespaces:
    def _mount(self) -> None:
        self.auth = Auth(self)
        self.catalog = Catalog(self)
        self.ads = Ads(self)

    @staticmethod
    def _raw(method: str, path: str, body: Optional[Any], query: Optional[Mapping[str, Any]], safe: Optional[bool],
             auth: bool) -> Op:
        verb = method.upper()
        return Op(verb, path if path.startswith("/") else f"/{path}", body=body,
                  query=dict(query) if query is not None else None, safe=verb == "GET" if safe is None else safe,
                  auth=auth)


class Lalafo(SyncEngine, _Namespaces):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._mount()

    def login(self, login: str, password: str) -> Any:
        return self.auth.login(login, password)

    def request(self, method: str, path: str, body: Optional[Any] = None, *,
                query: Optional[Mapping[str, Any]] = None, safe: Optional[bool] = None, auth: bool = True) -> Any:
        return self._run(self._raw(method, path, body, query, safe, auth))


class AsyncLalafo(AsyncEngine, _Namespaces):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._mount()

    async def login(self, login: str, password: str) -> Any:
        return await self.auth.login(login, password)

    async def request(self, method: str, path: str, body: Optional[Any] = None, *,
                      query: Optional[Mapping[str, Any]] = None, safe: Optional[bool] = None,
                      auth: bool = True) -> Any:
        return await self._run(self._raw(method, path, body, query, safe, auth))
