from __future__ import annotations

import mimetypes
import re
import time
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional, Sequence, Union

from pydantic import ValidationError as PydanticValidationError

from ._core import Flow, Op, Pause
from .enums import REAL_ESTATE_ROOT, TABS, AdStatus
from .errors import InvalidRequestError, LalafoError, WaitTimeoutError
from .messages import text
from .models import (
    Ad,
    AdForm,
    AdPage,
    AdParam,
    Category,
    City,
    Draft,
    Image,
    Limits,
    Param,
    Session,
    User,
    params_from_api,
)

PHOTO_MIN = 20 * 1024
PHOTO_MAX = 20 * 1024 * 1024
PHOTO_COUNT = 20
PER_PAGE_MAX = 100
BYPASS = {"X-Cache-Bypass": "yes"}
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

PhotoLike = Union[bytes, str, Path, tuple[str, bytes], tuple[str, bytes, str]]
FormLike = Union[AdForm, Mapping[str, Any]]


def required(value: Any, name: str, limit: int = 255) -> str:
    result = str(value if value is not None else "").strip()
    if not result:
        raise InvalidRequestError(text("value.empty", field=name))
    if len(result) > limit:
        raise InvalidRequestError(text("value.too_long", field=name, limit=limit))
    return result


def whole(value: Any, name: str, low: int, high: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        raise InvalidRequestError(text("value.range", field=name, low=low, high=high, value=value))
    return value


def ad_id(value: Any) -> int:
    if isinstance(value, str) and value.strip().isdigit():
        value = int(value.strip())
    return whole(value, "ad_id", 1, 10**12)


def phone(value: Any, code: str) -> str:
    raw = str(value or "").strip()
    digits = "".join(ch for ch in raw if ch.isdigit())
    if raw.startswith("+"):
        full = digits
    elif digits.startswith("00"):
        full = digits[2:]
    elif digits.startswith(code) and len(digits) > len(code) + 6:
        full = digits
    elif digits.startswith("0"):
        full = code + digits[1:]
    else:
        full = code + digits
    if not 8 <= len(full) <= 15 or (full.startswith(code) and code == "994" and len(full) != 12):
        raise InvalidRequestError(text("value.phone", value=value))
    return "+" + full


def form(value: FormLike, code: str) -> AdForm:
    try:
        result = value if isinstance(value, AdForm) else AdForm.model_validate(dict(value))
    except PydanticValidationError as error:
        raise InvalidRequestError(str(error)) from None
    if result.mobile:
        result = result.model_copy(update={"mobile": phone(result.mobile, code)})
    return result


def photo(value: Any, index: int) -> tuple[str, bytes, str]:
    if isinstance(value, (str, Path)):
        path = Path(value)
        name, content = path.name, path.read_bytes()
        kind = mimetypes.guess_type(name)[0] or "image/jpeg"
    elif isinstance(value, (bytes, bytearray)):
        name, content, kind = f"photo{index}.jpg", bytes(value), "image/jpeg"
    elif isinstance(value, tuple) and len(value) in (2, 3) and isinstance(value[1], (bytes, bytearray)):
        name, content = str(value[0]), bytes(value[1])
        kind = str(value[2]) if len(value) == 3 else mimetypes.guess_type(name)[0] or "image/jpeg"
    else:
        raise InvalidRequestError(text("value.photo_type", index=index))
    if len(content) < PHOTO_MIN:
        raise InvalidRequestError(text("value.photo_small", index=index, size=len(content), limit=PHOTO_MIN))
    if len(content) > PHOTO_MAX:
        raise InvalidRequestError(text("value.photo_large", index=index, size=len(content), limit=PHOTO_MAX))
    return name, content, kind


def photos(values: Sequence[Any], allow_empty: bool = False) -> list[tuple[str, bytes, str]]:
    items = list(values)
    if (not items and not allow_empty) or len(items) > PHOTO_COUNT:
        raise InvalidRequestError(text("value.photo_count", limit=PHOTO_COUNT, count=len(items)))
    return [photo(item, i) for i, item in enumerate(items, start=1)]


def resolve_params(given: Iterable[AdParam], definitions: Sequence[Param]) -> list[dict[str, Any]]:
    defs = {d.id: d for d in definitions}
    out: list[dict[str, Any]] = []
    problems: list[str] = []
    counts: dict[int, int] = {}
    for p in given:
        counts[p.id] = counts.get(p.id, 0) + 1
        d = defs.get(p.id)
        if defs and d is None:
            problems.append(text("value.param_unknown", param_id=p.id))
            continue
        name = d.name if d else None
        if p.value_id is not None:
            choice = d.value(p.value_id) if d else None
            if d is not None and choice is None:
                problems.append(text("value.param_value", param_id=p.id, name=name, value_id=p.value_id))
                continue
            out.append({"id": p.id, "name": name, "value": choice.value if choice else None, "value_id": p.value_id})
        else:
            out.append({"id": p.id, "name": name, "value": p.value})
    for pid, n in counts.items():
        d = defs.get(pid)
        if n > 1 and d is not None and not d.multi:
            problems.append(text("value.param_single", param_id=pid, name=d.name))
    for d in definitions:
        if d.required and d.id not in counts:
            problems.append(text("value.param_required", param_id=d.id, name=d.name))
    if problems:
        raise InvalidRequestError("; ".join(problems))
    return out


class _Resource:
    def __init__(self, client: Any) -> None:
        self._client = client

    @property
    def _settings(self) -> Any:
        return self._client.settings

    @property
    def _base(self) -> str:
        return str(self._client.settings.base_url)

    def _ad(self) -> Any:
        base = self._base
        return lambda body: Ad.from_api(body if isinstance(body, Mapping) else {}, base)

    def _run(self, op: Op) -> Any:
        return self._client._run(op)

    def _flow(self, flow: Flow[Any]) -> Any:
        return self._client._flow(flow)

    def _user_id(self) -> str:
        session: Optional[Session] = self._client.session
        if session is None or not session.user_id:
            raise LalafoError(text("error.no_user"))
        return session.user_id


class Auth(_Resource):
    def login(self, login: str, password: str) -> Any:
        name = required(login, "login", 100)
        if not isinstance(password, str) or len(password) < 5:
            raise InvalidRequestError(text("value.password"))
        body = {"email": name, "password": password} if EMAIL.match(name) else \
            {"mobile": phone(name, self._settings.phone_code), "password": password}
        user_hash = self._client.user_hash
        return self._flow(self._login(body, user_hash))

    def _login(self, body: dict[str, Any], user_hash: str) -> Flow[Session]:
        reply = yield Op("POST", "login", body=body, headers=BYPASS, auth=False)
        if not isinstance(reply, Mapping) or not reply.get("token"):
            raise LalafoError(text("error.no_token"))
        session: Session = self._client._store(Session.from_login(reply, user_hash))
        return session

    def renew(self) -> Any:
        return self._flow(self._client._renew())

    def logout(self) -> Any:
        return self._flow(self._logout())

    def _logout(self) -> Flow[None]:
        yield Op("GET", "logout", safe=True)
        self._client.session = None
        return None

    def me(self) -> Any:
        return self._run(Op("GET", "user", User.from_api, path_params={"user_id": self._user_id()}, safe=True))


class Catalog(_Resource):
    def categories(self) -> Any:
        parse = lambda body: tuple(Category.from_api(c) for c in (body or []) if isinstance(c, Mapping))
        return self._run(Op("GET", "categories", parse, safe=True, auth=False))

    def category(self, category_id: int) -> Any:
        return self._flow(self._category(whole(category_id, "category_id", 1, 10**9)))

    def _category(self, wanted: int) -> Flow[Optional[Category]]:
        roots: tuple[Category, ...] = yield Op("GET", "categories", lambda body: tuple(
            Category.from_api(c) for c in (body or []) if isinstance(c, Mapping)), safe=True, auth=False)
        return next((found for root in roots if (found := root.find(wanted)) is not None), None)

    def real_estate(self) -> Any:
        return self.category(REAL_ESTATE_ROOT)

    def cities(self) -> Any:
        parse = lambda body: tuple(City.from_api(c) for c in (body or []) if isinstance(c, Mapping))
        return self._run(Op("GET", "locations", parse, safe=True, auth=False))

    def filter_params(self, category_id: int, city_id: Optional[int] = None) -> Any:
        query = {"category_id": whole(category_id, "category_id", 1, 10**9),
                 "city_id": whole(city_id, "city_id", 1, 10**9) if city_id is not None else None}
        return self._run(Op("GET", "filter_params", params_from_api, query=query, safe=True, auth=False))

    def posting_params(self, category_id: int, city_id: int, *, ad_id_: Optional[int] = None,
                       ad_type: Any = None) -> Any:
        return self._run(self._posting_op(category_id, city_id, ad_id_, ad_type))

    @staticmethod
    def _posting_op(category_id: int, city_id: int, ad: Optional[int] = None, ad_type: Any = None) -> Op:
        body: dict[str, Any] = {"category_id": whole(category_id, "category_id", 1, 10**9),
                                "city_id": whole(city_id, "city_id", 1, 10**9)}
        if ad is not None:
            body.update({"id": ad, "type": ad_type})
        return Op("POST", "posting_params", params_from_api, body=body, safe=True)


class Ads(_Resource):
    def draft(self) -> Any:
        return self._run(Op("POST", "draft", lambda body: Draft.from_api(body or {})))

    def upload_photo(self, ad_id_: Any, value: PhotoLike, index: int = 1) -> Any:
        return self._run(self._upload_op(ad_id(ad_id_), photo(value, index), index))

    def _upload_op(self, ad: int, item: tuple[str, bytes, str], index: int) -> Op:
        def parse(body: Any) -> Image:
            if not isinstance(body, Mapping) or body.get("id") is None:
                raise LalafoError(text("error.no_image", index=index))
            return Image.from_api(body)

        return Op("POST", "image_upload", parse, files={"image_file": item}, data={"ad_id": str(ad)}, headers=BYPASS)

    def remove_photos(self, image_ids: Sequence[int]) -> Any:
        return self._run(self._remove_op(list(image_ids)))

    @staticmethod
    def _remove_op(image_ids: list[int]) -> Op:
        query = [("ids[]", whole(i, "image_id", 1, 10**12)) for i in image_ids]
        return Op("DELETE", "image_remove", query=query)

    def save_draft(self, ad_id_: Any, data: FormLike, image_ids: Sequence[int],
                   params: Optional[Sequence[Param]] = None) -> Any:
        draft_id, ad_form = ad_id(ad_id_), form(data, self._settings.phone_code)
        return self._flow(self._save(draft_id, ad_form, list(image_ids), params))

    def _save(self, draft_id: int, ad_form: AdForm, image_ids: list[int],
              params: Optional[Sequence[Param]]) -> Flow[Any]:
        if params is None:
            params = yield Catalog._posting_op(ad_form.category_id, ad_form.city_id)
        body = {"id": draft_id, "title": "", **ad_form.body(image_ids, resolve_params(ad_form.params, params))}
        result = yield Op("PUT", "draft_save", body=body, path_params={"ad_id": draft_id})
        return result

    def publish(self, ad_id_: Any) -> Any:
        return self._run(self._publish_op(ad_id(ad_id_)))

    def _publish_op(self, draft_id: int) -> Op:
        return Op("POST", "draft_publish", self._ad(), query={"expand": "available_campaign_types"},
                  path_params={"ad_id": draft_id})

    def create(self, data: FormLike, images: Sequence[PhotoLike]) -> Any:
        ad_form = form(data, self._settings.phone_code)
        return self._flow(self._create(ad_form, photos(images)))

    def _create(self, ad_form: AdForm, items: list[tuple[str, bytes, str]]) -> Flow[Ad]:
        params: tuple[Param, ...] = yield Catalog._posting_op(ad_form.category_id, ad_form.city_id)
        resolved = resolve_params(ad_form.params, params)
        draft: Draft = yield Op("POST", "draft", lambda body: Draft.from_api(body or {}))
        if not draft.id:
            raise LalafoError(text("error.no_draft"))
        if draft.images:
            yield self._remove_op([i.id for i in draft.images])
        image_ids = []
        for index, item in enumerate(items, start=1):
            image: Image = yield self._upload_op(draft.id, item, index)
            image_ids.append(image.id)
        body = {"id": draft.id, "title": "", **ad_form.body(image_ids, resolved)}
        yield Op("PUT", "draft_save", body=body, path_params={"ad_id": draft.id})
        ad: Ad = yield self._publish_op(draft.id)
        return ad if ad.id else Ad.from_api({**ad.raw, "id": draft.id}, self._base)

    def get(self, ad_id_: Any) -> Any:
        return self._run(Op("GET", "my_ad", self._ad(), path_params={"ad_id": ad_id(ad_id_)}, headers=BYPASS,
                            safe=True))

    def details(self, ad_id_: Any) -> Any:
        return self._run(Op("GET", "ad_details", self._ad(), query={"expand": "url"},
                            path_params={"ad_id": ad_id(ad_id_)}, safe=True, auth=False))

    def edit(self, ad_id_: Any, data: FormLike, images: Optional[Sequence[PhotoLike]] = None, *,
             keep_photos: bool = True) -> Any:
        wanted, ad_form = ad_id(ad_id_), form(data, self._settings.phone_code)
        items = photos(images or [], allow_empty=True)
        return self._flow(self._edit(wanted, ad_form, items, keep_photos))

    def _edit(self, wanted: int, ad_form: AdForm, items: list[tuple[str, bytes, str]], keep: bool) -> Flow[Ad]:
        current: Ad = yield Op("GET", "my_ad", self._ad(), path_params={"ad_id": wanted}, headers=BYPASS, safe=True)
        ad_type = current.raw.get("type")
        params: tuple[Param, ...] = yield Catalog._posting_op(ad_form.category_id, ad_form.city_id, wanted, ad_type)
        resolved = resolve_params(ad_form.params, params)
        old = [i.id for i in current.images]
        new_ids = []
        for index, item in enumerate(items, start=1):
            image: Image = yield self._upload_op(wanted, item, index)
            new_ids.append(image.id)
        order = (old if keep or not new_ids else []) + new_ids
        body = {"id": wanted, "type": ad_type, **ad_form.body(order, resolved)}
        ad: Ad = yield Op("PUT", "ad_edit", self._ad(), body=body, path_params={"ad_id": wanted})
        dropped = [i for i in old if i not in order]
        if dropped:
            yield self._remove_op(dropped)
        return ad if ad.id else current

    def deactivate(self, ad_id_: Any) -> Any:
        return self._run(Op("PUT", "ad_deactivate", path_params={"ad_id": ad_id(ad_id_)}))

    def activate(self, ad_id_: Any) -> Any:
        return self._run(Op("POST", "ad_activate", path_params={"ad_id": ad_id(ad_id_)}))

    def delete(self, ad_id_: Any) -> Any:
        return self._run(Op("DELETE", "ad_delete", path_params={"ad_id": ad_id(ad_id_)}))

    def _list_op(self, status: Optional[str], page: int, per_page: int) -> Op:
        query: list[tuple[str, Any]] = [("expand", "url"), ("page", page), ("per-page", per_page)]
        if status is not None:
            if status not in TABS:
                raise InvalidRequestError(text("value.choice", field="status", choices=tuple(TABS), value=status))
            query += [("status_id[]", int(s)) for s in TABS[status]]
        base = self._base
        return Op("GET", "my_ads", lambda body: AdPage.from_api(body if isinstance(body, Mapping) else {}, base, page),
                  query=query, safe=True)

    def list(self, status: Optional[str] = None, page: int = 1, per_page: int = 20) -> Any:
        return self._run(self._list_op(status, whole(page, "page", 1, 10**6),
                                       whole(per_page, "per_page", 1, PER_PAGE_MAX)))

    def all(self, status: Optional[str] = None, max_pages: int = 50) -> Any:
        return self._flow(self._all(status, max(1, max_pages)))

    def _all(self, status: Optional[str], max_pages: int) -> Flow[tuple[Ad, ...]]:
        items: list[Ad] = []
        for page in range(1, max_pages + 1):
            batch: AdPage = yield self._list_op(status, page, PER_PAGE_MAX)
            items.extend(batch.items)
            if not batch.items or not batch.has_more:
                break
        return tuple(items)

    def limits(self) -> Any:
        return self._run(Op("GET", "limits", Limits.from_api, safe=True,
                            path_params={"country_id": self._settings.country_id, "user_id": self._user_id()}))

    def wait(self, ad_id_: Any, timeout: float = 600.0, interval: float = 15.0) -> Any:
        return self._flow(self._wait(ad_id(ad_id_), timeout, max(0.0, interval)))

    def _wait(self, wanted: int, timeout: float, interval: float) -> Flow[Ad]:
        deadline = time.monotonic() + timeout
        while True:
            ad: Ad = yield Op("GET", "my_ad", self._ad(), path_params={"ad_id": wanted}, headers=BYPASS, safe=True)
            if ad.status.final:
                return ad
            if time.monotonic() + interval > deadline:
                raise WaitTimeoutError(text("error.wait_timeout", ad_id=wanted, status=AdStatus(ad.status).name.lower(),
                                            seconds=timeout), ad=ad)
            yield Pause(interval)
