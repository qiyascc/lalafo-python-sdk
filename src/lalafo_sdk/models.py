from __future__ import annotations

import base64
import json
import time
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from typing import Any, Iterator, Mapping, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .enums import AdStatus, Currency, ParamKind


def _pick(body: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        value = body.get(key)
        if value is not None and value != "":
            return value
    return None


def _str(body: Mapping[str, Any], *keys: str) -> Optional[str]:
    value = _pick(body, *keys)
    return None if value is None else str(value)


def _int(body: Mapping[str, Any], *keys: str) -> Optional[int]:
    value = _pick(body, *keys)
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _float(body: Mapping[str, Any], *keys: str) -> Optional[float]:
    value = _pick(body, *keys)
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _bool(body: Mapping[str, Any], *keys: str) -> Optional[bool]:
    value = _pick(body, *keys)
    return value if isinstance(value, bool) else None


def _when(body: Mapping[str, Any], *keys: str) -> Optional[datetime]:
    value = _pick(body, *keys)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return datetime.fromtimestamp(value, tz=timezone.utc)


def _map(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, (list, tuple)) else []


def jwt_claims(token: str) -> dict[str, Any]:
    try:
        part = token.split(".")[1]
        claims = json.loads(base64.urlsafe_b64decode(part + "=" * (-len(part) % 4)))
    except (IndexError, ValueError):
        return {}
    return claims if isinstance(claims, dict) else {}


@dataclass(frozen=True)
class Session:
    token: str
    refresh_token: str = ""
    user_hash: str = ""
    user_id: str = ""

    def __repr__(self) -> str:
        return f"Session(user_id={self.user_id!r}, expires_at={self.expires_at!r})"

    @classmethod
    def from_login(cls, body: Mapping[str, Any], user_hash: str) -> Session:
        token = str(body.get("token") or "")
        uid = _str(body, "id") or str(jwt_claims(token).get("id") or "")
        return cls(token, str(body.get("refresh_token") or ""), str(body.get("user_hash") or user_hash), uid)

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> Session:
        token = str(data.get("token") or "")
        uid = str(data.get("user_id") or jwt_claims(token).get("id") or "")
        return cls(token, str(data.get("refresh_token") or ""), str(data.get("user_hash") or ""), uid)

    def to_dict(self) -> dict[str, str]:
        return {"token": self.token, "refresh_token": self.refresh_token, "user_hash": self.user_hash,
                "user_id": self.user_id}

    def renewed(self, body: Mapping[str, Any]) -> Session:
        return replace(self, token=str(body.get("token") or self.token),
                       refresh_token=str(body.get("refresh_token") or self.refresh_token))

    @property
    def issued_at(self) -> Optional[float]:
        value = jwt_claims(self.token).get("iat")
        return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None

    @property
    def expires_at(self) -> Optional[float]:
        claims = jwt_claims(self.token)
        value = claims.get("sensitive_exp", claims.get("exp"))
        return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None

    def renew_due(self, share: float, now: Optional[float] = None) -> bool:
        issued, expires = self.issued_at, self.expires_at
        if issued is None or expires is None or expires <= issued or not self.refresh_token:
            return False
        return (now if now is not None else time.time()) >= issued + (expires - issued) * share

    def expired(self, now: Optional[float] = None) -> bool:
        expires = self.expires_at
        return expires is not None and (now if now is not None else time.time()) >= expires


@dataclass(frozen=True)
class User:
    id: Optional[int]
    username: Optional[str]
    mobile: Optional[str]
    email: Optional[str]
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_api(cls, body: Mapping[str, Any]) -> User:
        return cls(_int(body, "id"), _str(body, "username", "name"), _str(body, "mobile", "phone"),
                   _str(body, "email"), dict(body))


@dataclass(frozen=True)
class Category:
    id: int
    name: str
    parent_id: Optional[int]
    url: Optional[str]
    postable: bool
    children: tuple[Category, ...] = ()
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_api(cls, body: Mapping[str, Any]) -> Category:
        kids = tuple(cls.from_api(c) for c in _list(body.get("children")) if isinstance(c, Mapping))
        return cls(_int(body, "id") or 0, _str(body, "name") or "", _int(body, "parent_id"), _str(body, "url"),
                   body.get("panel_type") == "params" and body.get("active", True) is not False, kids,
                   {k: v for k, v in body.items() if k != "children"})

    def walk(self, path: tuple[str, ...] = ()) -> Iterator[tuple[tuple[str, ...], Category]]:
        here = (*path, self.name)
        yield here, self
        for child in self.children:
            yield from child.walk(here)

    def find(self, category_id: int) -> Optional[Category]:
        return next((c for _, c in self.walk() if c.id == category_id), None)

    def leaves(self) -> tuple[Category, ...]:
        return tuple(c for _, c in self.walk() if c.postable)


@dataclass(frozen=True)
class City:
    id: int
    name: str
    alias: Optional[str]
    region: Optional[str]
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_api(cls, body: Mapping[str, Any]) -> City:
        return cls(_int(body, "id") or 0, _str(body, "name", "value") or "", _str(body, "alias"),
                   _str(_map(body.get("region")), "name"), dict(body))


@dataclass(frozen=True)
class ParamValue:
    id: int
    value: str

    @classmethod
    def from_api(cls, body: Mapping[str, Any]) -> ParamValue:
        return cls(_int(body, "id") or 0, _str(body, "value", "name") or "")


@dataclass(frozen=True)
class Param:
    id: int
    name: str
    kind: ParamKind
    required: bool
    multi: bool
    values: tuple[ParamValue, ...] = ()
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_api(cls, body: Mapping[str, Any]) -> Param:
        values = tuple(ParamValue.from_api(v) for v in _list(body.get("values")) if isinstance(v, Mapping))
        return cls(_int(body, "id") or 0, _str(body, "name") or "", ParamKind.parse(body.get("kind")),
                   bool(body.get("is_required")), bool(body.get("is_multi_select_posting")), values,
                   {k: v for k, v in body.items() if k != "values"})

    def value(self, value_id: int) -> Optional[ParamValue]:
        return next((v for v in self.values if v.id == value_id), None)

    def find(self, label: str) -> Optional[ParamValue]:
        wanted = label.strip().lower()
        return next((v for v in self.values if v.value.strip().lower() == wanted), None)


def params_from_api(body: Any) -> tuple[Param, ...]:
    items = body.get("items") if isinstance(body, Mapping) else body
    return tuple(Param.from_api(p) for p in _list(items) if isinstance(p, Mapping) and p.get("id") is not None)


@dataclass(frozen=True)
class Image:
    id: int
    thumbnail: Optional[str]
    original: Optional[str]
    main: bool = False

    @classmethod
    def from_api(cls, body: Mapping[str, Any]) -> Image:
        links = _map(body.get("links"))
        return cls(_int(body, "id") or 0, _str(body, "thumbnail_url") or _str(links, "thumbnail"),
                   _str(body, "original_url") or _str(links, "original"), bool(body.get("is_main")))


@dataclass(frozen=True)
class AdParamValue:
    id: int
    name: Optional[str]
    value: Optional[str]
    value_id: Optional[int]

    @classmethod
    def from_api(cls, body: Mapping[str, Any]) -> AdParamValue:
        return cls(_int(body, "id") or 0, _str(body, "name"), _str(body, "value"), _int(body, "value_id"))


@dataclass(frozen=True)
class Ad:
    id: int
    status: AdStatus
    title: Optional[str]
    description: Optional[str]
    price: Optional[float]
    currency: Optional[str]
    category_id: Optional[int]
    city_id: Optional[int]
    url: Optional[str]
    images: tuple[Image, ...] = ()
    params: tuple[AdParamValue, ...] = ()
    rejected_reason: Optional[str] = None
    mobile: Optional[str] = None
    username: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    campaign_types: tuple[str, ...] = ()
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_api(cls, body: Mapping[str, Any], base_url: str = "") -> Ad:
        path = _str(body, "url")
        url = path if path is None or path.startswith("http") else f"{base_url}{path}"
        return cls(
            _int(body, "id") or 0, AdStatus.parse(body.get("status_id")), _str(body, "title"),
            _str(body, "description"), _float(body, "price"), _str(body, "currency"), _int(body, "category_id"),
            _int(body, "city_id"), url,
            tuple(Image.from_api(i) for i in _list(body.get("images")) if isinstance(i, Mapping)),
            tuple(AdParamValue.from_api(p) for p in _list(body.get("params")) if isinstance(p, Mapping)),
            _str(body, "rejected_reason"), _str(body, "mobile"), _str(body, "username"),
            _when(body, "created_time"), _when(body, "updated_time"),
            tuple(str(t) for t in _list(body.get("available_campaign_types"))), dict(body),
        )

    @property
    def awaiting_payment(self) -> bool:
        return self.status is AdStatus.PAYMENT_WAITING

    @property
    def offers_promotion(self) -> bool:
        return "adViews" in self.campaign_types


@dataclass(frozen=True)
class AdPage:
    items: tuple[Ad, ...]
    page: int
    page_count: Optional[int]
    total: Optional[int]

    @property
    def has_more(self) -> bool:
        return self.page_count is not None and self.page < self.page_count

    @classmethod
    def from_api(cls, body: Mapping[str, Any], base_url: str = "", page: int = 1) -> AdPage:
        meta = _map(body.get("_meta"))
        items = tuple(Ad.from_api(a, base_url) for a in _list(body.get("items")) if isinstance(a, Mapping))
        return cls(items, _int(meta, "currentPage") or page, _int(meta, "pageCount"), _int(meta, "totalCount"))


@dataclass(frozen=True)
class Draft:
    id: int
    images: tuple[Image, ...]
    mobile: Optional[str]
    username: Optional[str]
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_api(cls, body: Mapping[str, Any]) -> Draft:
        return cls(_int(body, "id") or 0,
                   tuple(Image.from_api(i) for i in _list(body.get("images")) if isinstance(i, Mapping)),
                   _str(body, "mobile"), _str(body, "username"), dict(body))


@dataclass(frozen=True)
class Limits:
    raw: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_api(cls, body: Any) -> Limits:
        return cls(dict(body) if isinstance(body, Mapping) else {"items": _list(body)})


class AdParam(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: int
    value_id: Optional[int] = None
    value: Optional[str] = Field(default=None, max_length=200)

    @model_validator(mode="after")
    def _one(self) -> AdParam:
        if (self.value_id is None) == (self.value is None):
            raise ValueError(f"param {self.id}: give either value_id for a dropdown or value for an input")
        return self


class AdForm(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category_id: int
    city_id: int
    description: str = Field(min_length=1, max_length=6000)
    price: Optional[int] = Field(default=None, ge=1)
    currency: Currency = Currency.AZN
    is_negotiable: bool = False
    params: tuple[AdParam, ...] = ()
    username: Optional[str] = Field(default=None, max_length=100)
    mobile: Optional[str] = None
    email: Optional[str] = Field(default=None, max_length=100)
    hide_phone: bool = False
    is_hide_house_number: bool = False
    is_private_ad: bool = False

    def body(self, image_ids: list[int], params: list[dict[str, Any]]) -> dict[str, Any]:
        priced = self.price is not None
        out: dict[str, Any] = {
            "category_id": self.category_id,
            "city_id": self.city_id,
            "description": self.description.strip(),
            "price": self.price if priced else None,
            "currency": self.currency.value if priced else None,
            "is_negotiable": self.is_negotiable if priced else True,
            "image_order": image_ids,
            "params": params,
            "hide_phone": self.hide_phone,
            "hide_chat": None,
            "submit_request": None,
            "is_hide_house_number": self.is_hide_house_number,
            "is_private_ad": self.is_private_ad,
        }
        for key in ("username", "mobile", "email"):
            value = getattr(self, key)
            if value:
                out[key] = value.strip()
        return out
