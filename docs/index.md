# lalafo Python SDK

A typed Python client for [lalafo.az](https://lalafo.az). It signs in with a phone number or an email and a password, keeps the session alive on its own, reads categories, cities and the params of each category, posts an ad with photos in one call, and edits, deactivates, activates, deletes and lists the ads of the account. There is a sync client, `Lalafo`, and an async one, `AsyncLalafo`, with the same methods.

```python
from lalafo_sdk import BAKU, Lalafo

with Lalafo() as lf:
    lf.login("050 123 45 67", "password")
    rooms = next(p for p in lf.catalog.filter_params(4800, BAKU) if p.id == 69)
    ad = lf.ads.create(
        {
            "category_id": 4800,
            "city_id": BAKU,
            "price": 80000,
            "description": "Satılır 2 otaqlı köhnə tikili, təmirli, kupçalı.",
            "params": [{"id": 69, "value_id": rooms.find("2 otaqlı").id}, {"id": 70, "value": "42"}],
        },
        ["kitchen.jpg", "room.jpg"],
    )
    print(ad.id, ad.status, ad.url)
```

:::{important}
lalafo has no public API. The client talks to the same `https://lalafo.az/api/...` endpoints as the website, with the same headers the website sends (`device: pc`, `country-id`, `language`, a fresh `request-id`, `user-hash`). It sends no device fingerprint and no mobile app identity, and it never solves captchas. lalafo can change these endpoints at any time; every path is a setting.
:::

## Where to go next

::::{grid} 1 2 2 2
:gutter: 3

:::{grid-item-card} Installation
:link: getting-started/installation
:link-type: doc

Python versions, a virtual environment step by step, pip, uv and Poetry.
:::

:::{grid-item-card} Signing in and sessions
:link: getting-started/sign-in
:link-type: doc

Phone or email, saving the session, automatic renewal, `on_session`.
:::

:::{grid-item-card} Quickstart
:link: getting-started/quickstart
:link-type: doc

From a category id to a posted flat, step by step.
:::

:::{grid-item-card} Categories, cities and params
:link: guides/catalog
:link-type: doc

How lalafo describes an ad and how to fill in its params.
:::

:::{grid-item-card} Posting ads
:link: guides/posting
:link-type: doc

The form, photos, every check, and the draft steps one by one.
:::

:::{grid-item-card} Safety and retries
:link: guides/safety
:link-type: doc

Cloudflare check pages, slow answers and writes that are never repeated.
:::

:::{grid-item-card} Examples
:link: examples/index
:link-type: doc

A session file, real estate category ids, posting from CSV, moderation alerts, Django.
:::

:::{grid-item-card} API reference
:link: reference/api
:link-type: doc

Every class, method and field.
:::

::::

## What the SDK takes care of

- **Sessions that stay alive.** The token is renewed with the refresh token once 75% of its lifetime has passed, or once after a 401. Every new session goes to your `on_session` callback, so you can store it.
- **One call to post.** `ads.create` does what the website does: loads the posting params, makes a draft, clears old photos from a reused draft, uploads the photos, saves and publishes.
- **Checks before sending.** Unknown params, unknown values, two values for a single value param, missing required params, bad photos and bad phone numbers are refused before the draft is made.
- **Writes are never repeated.** A timeout or a 5xx on a write raises `OutcomeUnknownError` instead of sending it again.
- **Reads ride over hiccups.** lalafo.az is sometimes slow and sometimes answers with a short Cloudflare check page. Reads are retried with backoff.
- **Typed results** as frozen dataclasses, with the raw answer kept in `.raw`.

```{toctree}
:hidden:
:caption: Getting started

getting-started/installation
getting-started/sign-in
getting-started/quickstart
getting-started/configuration
```

```{toctree}
:hidden:
:caption: Guides

guides/catalog
guides/posting
guides/managing
guides/async
guides/errors
guides/safety
guides/messages
guides/advanced
guides/testing
```

```{toctree}
:hidden:
:caption: Examples

examples/index
examples/session-file
examples/real-estate
examples/post-from-csv
examples/moderation-watch
examples/django
```

```{toctree}
:hidden:
:caption: Reference

reference/api
reference/models
reference/changelog
reference/faq
```

```{toctree}
:hidden:
:caption: Project

project/development
project/about
```
