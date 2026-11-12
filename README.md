# lalafo-python-sdk

[![PyPI](https://img.shields.io/pypi/v/lalafo-python-sdk?color=3775A9&logo=pypi&logoColor=white)](https://pypi.org/project/lalafo-python-sdk/)
[![Python](https://img.shields.io/badge/python-3.10%20to%203.13-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![lalafo](https://img.shields.io/badge/site-lalafo.az-E5156B)](https://lalafo.az)
[![Typed](https://img.shields.io/badge/typing-mypy-2A6DB2)](https://mypy-lang.org)
[![Async](https://img.shields.io/badge/sync%20%2B%20async-httpx-5A45FF)](https://www.python-httpx.org)
[![Ruff](https://img.shields.io/badge/lint-ruff-D7FF64?logo=ruff&logoColor=black)](https://docs.astral.sh/ruff)
[![License](https://img.shields.io/badge/license-MIT-green)](https://github.com/qiyascc/lalafo-python-sdk/blob/main/LICENSE)

Typed Python client for lalafo.az. Sign in, read categories and their params, post an ad with photos, edit, deactivate, activate and delete it, and list your own ads. Sync and async, with retry rules built so an ad is never posted twice.

```bash
pip install lalafo-python-sdk
```

The client talks to the same `https://lalafo.az/api/...` endpoints as the lalafo.az website, with the same headers (`device: pc`, `country-id`, `language`, a fresh `request-id`, `user-hash`). It sends no device fingerprint and no mobile app identity. lalafo has no public API and can change these endpoints; every path is a setting.

## Sign in

```python
from lalafo_sdk import Lalafo

with Lalafo() as lf:
    session = lf.login("050 123 45 67", "password")
    lf.auth.me().username
```

Sign in with a phone number (`050 123 45 67`, `+994501234567`) or an email. Keep the session instead of signing in every time:

```python
import json

def save(session):
    open("session.json", "w").write(json.dumps(session.to_dict()))

lf = Lalafo(json.load(open("session.json")), on_session=save)
```

The token is renewed with the refresh token once 75% of its lifetime has passed (`renew_at`), or once after a 401. `on_session` gets every new session, so store it there. A renewal that lalafo refuses raises `AuthenticationError`: sign in again.

## Post an ad

```python
from lalafo_sdk import BAKU

rooms = next(p for p in lf.catalog.filter_params(4800, BAKU) if p.id == 69)
form = {
    "category_id": 4800,
    "city_id": BAKU,
    "price": 80000,
    "currency": "AZN",
    "description": "Satılır 2 otaqlı köhnə tikili, təmirli, kupçalı.",
    "params": [
        {"id": 69, "value_id": rooms.find("2 otaqlı").id},
        {"id": 70, "value": "42"},
        {"id": 1239, "value_id": 28272},
        {"id": 1239, "value_id": 27535},
    ],
}
ad = lf.ads.create(form, ["kitchen.jpg", "room.jpg"])
ad.id, ad.status, ad.url
```

`create` does what the website does: it loads the posting params of the category and city, makes a draft (and clears photos left in a reused draft), uploads the photos, saves the draft and publishes it. lalafo writes the title itself, such as "Bakı, 2 otaqlı, Köhnə tikili, 42 kv. m". The ad goes to moderation (`AdStatus.MODERATION`); `lf.ads.wait(ad.id)` waits until moderation ends. An ad over the free limit comes back as `AdStatus.PAYMENT_WAITING` (`ad.awaiting_payment`): lalafo shows it only after payment on the website. The client never pays.

Params are checked before the draft is made: an unknown param, an unknown `value_id`, two values for a single value param or a missing required param raise `InvalidRequestError` and nothing is sent. Dropdowns take `value_id`, inputs take `value`, a multi select param repeats with each `value_id`. Leave `price` out for a negotiable price. Photos are bytes, paths or `(filename, bytes, content_type)`, from 1 to 20, each from 20 KB to 20 MB.

Each step is also there on its own: `ads.draft()`, `ads.upload_photo(draft_id, photo)`, `ads.save_draft(draft_id, form, image_ids)`, `ads.publish(draft_id)`.

## Manage ads

```python
lf.ads.edit(ad.id, {**form, "price": 75000}, ["new.jpg"])
lf.ads.edit(ad.id, form, ["only.jpg"], keep_photos=False)
lf.ads.deactivate(ad.id)
lf.ads.activate(ad.id)
lf.ads.delete(ad.id)

lf.ads.get(ad.id).rejected_reason
lf.ads.details(ad.id)
page = lf.ads.list("active", page=1, per_page=20)
everything = lf.ads.all("deactivated")
lf.ads.limits().raw
```

`list` takes `active`, `moderation`, `rejected`, `deactivated` or `payment_waiting`. An edit sends the ad back to moderation.

## Categories, cities and params

```python
estate = lf.catalog.real_estate()
for path, category in estate.walk():
    if category.postable:
        print(category.id, " / ".join(path))

lf.catalog.cities()
lf.catalog.filter_params(4800, BAKU)
lf.catalog.posting_params(4800, BAKU)
```

`filter_params` is public. `posting_params` needs a session and is the exact list the post form uses. Real estate ids on lalafo.az: apartments `4800` sale old building, `4793` sale new building, `2044` long term rent, `2045` daily rent; houses `2031` sale, `2033` rent; land `2038` sale, `2039` rent; country houses `5952`, `5953`; rooms `2050`, `2052`, `2053`; garages `5304`, `5305`; commercial rent `2065` to `2072`. Bakı is city `103261`.

## Safety

| Situation | What the client does |
| --- | --- |
| Connection refused, nothing sent | Retries, then `NotSentError` |
| Cloudflare check page | Retries, the request never reached lalafo, then `BlockedError` |
| Timeout, cut connection or 5xx on a write (sign in, draft, upload, save, publish, edit, deactivate, activate, delete) | No retry, `OutcomeUnknownError`: check the account before trying again |
| Same failure on a read | Retries with backoff, then `TransportError` or `ServerError` |
| 429 | Waits `Retry-After` and retries |
| 401 with a refresh token | Renews the session once and repeats the call, the call was not processed |
| Captcha asked after failed sign ins | `CaptchaRequiredError`, the client never solves captchas |
| Bad params, photos, phone or form | `InvalidRequestError` before anything is sent |
| `base_url` over plain http | `ConfigurationError`, except localhost or `allow_insecure_http` |

lalafo.az is sometimes slow and sometimes answers with a short Cloudflare check page. Reads ride over that with retries. A write that timed out may still have gone through, so it is never sent again on its own: look at `lf.ads.list()` first.

## Endpoints

| Namespace | Methods |
| --- | --- |
| `auth` | `login` `renew` `logout` `me` |
| `catalog` | `categories` `category` `real_estate` `cities` `filter_params` `posting_params` |
| `ads` | `create` `draft` `upload_photo` `remove_photos` `save_draft` `publish` `edit` `deactivate` `activate` `delete` `get` `details` `list` `all` `limits` `wait` |
| client | `login` `use_session` `request` |

`AsyncLalafo` has the same methods, awaited.

## Errors

`LalafoError` is the base. API answers raise `APIError` subclasses by status: `ValidationError` (400, 422, with `.fields`), `CaptchaRequiredError`, `AuthenticationError` (401), `ForbiddenError` (403), `NotFoundError` (404), `ConflictError` (409), `RateLimitError` (429), `ServerError` (5xx), `BadRequestError` for the rest. Each carries `status_code`, `message` and the raw `body`. `SessionRequiredError` means a call needs a signed in client.

## Config

Pass values in code, or set `LALAFO_BASE_URL`, `LALAFO_COUNTRY_ID`, `LALAFO_LANGUAGE`, `LALAFO_PHONE_CODE`, `LALAFO_TIMEOUT`, `LALAFO_MAX_RETRIES`, `LALAFO_RENEW_AT`, or put them in `lalafo.toml` ([example](https://github.com/qiyascc/lalafo-python-sdk/blob/main/examples/lalafo.toml)). Every path is a setting (`LALAFO_ENDPOINTS__LOGIN=...`). Messages live in `messages.yaml` and can be replaced with `messages.use(...)`.

The defaults are lalafo.az (country `13`, `az_AZ`, `+994`), the only site this client was built and tested against. lalafo runs the same platform in other countries; point `base_url`, `country_id`, `language` and `phone_code` at one of them at your own risk.

## Develop

```bash
pip install -e ".[dev]" && pytest && ruff check . && mypy src
```

## Links

- Source code: [github.com/qiyascc/lalafo-python-sdk](https://github.com/qiyascc/lalafo-python-sdk)
- PyPI: [pypi.org/project/lalafo-python-sdk](https://pypi.org/project/lalafo-python-sdk/)
- Project page: [theqiyas.cc/projects/lalafo-sdk](https://theqiyas.cc/projects/lalafo-sdk/)
- Author: [Qiyas Sadıqov](https://theqiyas.cc), more projects at [theqiyas.cc](https://theqiyas.cc)

## License

MIT
