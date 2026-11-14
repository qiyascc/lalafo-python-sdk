# Testing your code

Run your code against a fake lalafo instead of the real one. httpx's `MockTransport` sends every request to a Python function you write; pass the resulting client as `http_client=`.

## A complete test

Your code:

```python
from lalafo_sdk import BAKU, Lalafo


def post_flat(lf: Lalafo, area: str, photo: bytes) -> int:
    form = {"category_id": 4800, "city_id": BAKU, "price": 80000, "description": "Flat",
            "params": [{"id": 70, "value": area}]}
    return lf.ads.create(form, [("flat.jpg", photo)]).id
```

The test:

```python
import httpx
import pytest

from lalafo_sdk import InvalidRequestError, Lalafo

PHOTO = b"\xff\xd8" + b"0" * 30_000
PARAMS = [{"id": 70, "name": "Sahə", "kind": "input", "is_required": True, "values": []}]


def handler(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    if path.endswith("/params/posting"):
        return httpx.Response(200, json=PARAMS)
    if path.endswith("/posting-ads/temp") and request.method == "POST":
        return httpx.Response(200, json={"id": 4242, "images": []})
    if path.endswith("/images/upload"):
        return httpx.Response(200, json={"id": 9001})
    if path.endswith("/posting-ads/temp/4242") and request.method == "PUT":
        return httpx.Response(200, json={"id": 4242})
    if path.endswith("/posting-ads/temp/4242/publish"):
        return httpx.Response(200, json={"id": 4242, "status_id": 1, "url": "/baku/ads/flat-id-4242"})
    return httpx.Response(404, json={"message": f"unexpected {request.method} {path}"})


def client() -> Lalafo:
    http = httpx.Client(transport=httpx.MockTransport(handler))
    return Lalafo({"token": "test", "user_id": "77"}, max_retries=0, http_client=http)


def test_post_flat():
    assert post_flat(client(), "42", PHOTO) == 4242


def test_small_photo_is_refused_before_sending():
    with pytest.raises(InvalidRequestError):
        post_flat(client(), "42", b"tiny")
```

Notes:

- A session can be a plain dict with a `token`. A token that is not a real JWT has no expiry, so it is never renewed in tests.
- Photos must be at least 20 KB even in tests; the check runs before any request.
- `max_retries=0` keeps failing tests fast.

## What lalafo answers look like

lalafo answers with plain JSON, not wrapped in an envelope. Errors are a list of `{"field": ..., "message": ...}` with status 422, which becomes `ValidationError` with `fields`. Lists of ads come as `{"items": [...], "_meta": {"currentPage": 1, "pageCount": 3, "totalCount": 45}}`.

## Failures

```python
from lalafo_sdk import OutcomeUnknownError


def test_publish_times_out():
    def slow(request):
        if request.url.path.endswith("/publish"):
            raise httpx.ReadTimeout("slow", request=request)
        return handler(request)

    lf = Lalafo({"token": "test"}, max_retries=0, http_client=httpx.Client(transport=httpx.MockTransport(slow)))
    with pytest.raises(OutcomeUnknownError):
        post_flat(lf, "42", PHOTO)
```

A Cloudflare check page is an HTML answer with the header `cf-mitigated: challenge`:

```python
httpx.Response(403, headers={"cf-mitigated": "challenge", "content-type": "text/html"}, text="<html></html>")
```

The SDK's own [tests/conftest.py](https://github.com/qiyascc/lalafo-python-sdk/blob/main/tests/conftest.py) builds real looking JWTs for testing the renewal; copy it if you need that.
