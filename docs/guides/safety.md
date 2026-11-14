# Safety and retries

lalafo.az is sometimes slow and sometimes answers with a short Cloudflare check page instead of the API. Reads can simply be tried again. Writes cannot: a draft or an ad that lalafo created but never confirmed must not be created twice. The SDK sorts every call into reads and writes and treats them differently.

## Reads and writes

| Kind | Calls | On a timeout, a cut connection or a 5xx |
| --- | --- | --- |
| Reads | `catalog.*`, `auth.me`, `auth.logout`, `ads.get`, `ads.details`, `ads.list`, `ads.all`, `ads.limits`, `ads.wait`, and the posting params read inside `create`, `edit` and `save_draft` | Retried with backoff, then `TransportError` or `ServerError` |
| Writes | `login`, `auth.renew`, `ads.create` and each of its steps (`draft`, `upload_photo`, `remove_photos`, `save_draft`, `publish`), `ads.edit`, `ads.deactivate`, `ads.activate`, `ads.delete` | Never retried. `OutcomeUnknownError` |

`lf.request(...)` treats `GET` as a read and every other method as a write, unless you pass `safe=`.

## Every situation

| Situation | What the client does |
| --- | --- |
| Connection refused, nothing sent | Retries, then `NotSentError` |
| Cloudflare check page | Retries, the request never reached lalafo, then `BlockedError` |
| Timeout, cut connection or 5xx on a write | No retry, `OutcomeUnknownError`: check the account before trying again |
| Same failure on a read | Retries with backoff, then `TransportError` or `ServerError` |
| A write answered with something that is not JSON | `OutcomeUnknownError` |
| 429 | Waits for `Retry-After` (at most `backoff_cap`) and retries, then `RateLimitError` |
| 401 with a refresh token | Renews the session once and repeats the call; the call was not processed |
| Token past `renew_at` of its lifetime | Renewed before the call |
| Captcha asked after failed sign ins | `CaptchaRequiredError`, the client never solves captchas |
| Bad params, photos, phone or form | `InvalidRequestError` before anything is sent |
| A call that needs a session, with none | `SessionRequiredError` before anything is sent |
| `base_url` over plain http | `ConfigurationError`, except localhost or `allow_insecure_http` |

A Cloudflare check page is retried even for writes, because the request was stopped before it reached lalafo.

## Backoff

The wait before retry number `n` (from 0) is `min(backoff_cap, backoff_base * 2 ** n)` plus a random part of up to `backoff_base / 2`. With the defaults (`max_retries=2`, `backoff_base=0.8`, `backoff_cap=8`) a read is tried three times, waiting about 0.8 and 1.6 seconds. When lalafo is slow, raise both:

```python
lf = Lalafo(saved, timeout=60, max_retries=4)
```

## When the outcome is unknown

| Call | How to check |
| --- | --- |
| `ads.create` | `lf.ads.list("moderation")` and `lf.ads.list("active")`; a half finished attempt may also have left a draft, which the next `create` reuses and clears |
| `ads.edit` | `lf.ads.get(ad_id)` and compare |
| `ads.deactivate`, `ads.activate` | `lf.ads.get(ad_id).status` |
| `ads.delete` | `lf.ads.get(ad_id)` raises `NotFoundError` when the delete went through |
| `login` | Sign in again; a second sign in does no harm |

```python
from lalafo_sdk import OutcomeUnknownError

try:
    ad = lf.ads.create(form, photos)
except OutcomeUnknownError:
    recent = lf.ads.list("moderation").items + lf.ads.list("active").items
    print("Check before posting again:", [(a.id, a.title) for a in recent[:10]])
    raise
```

## Headers

The client sends the headers the lalafo website sends: `device: pc`, `country-id`, `language`, a fresh `request-id` for every call and a `user-hash` tied to the session. It sends no device fingerprint and no mobile app identity, and identifies itself in the User-Agent.
