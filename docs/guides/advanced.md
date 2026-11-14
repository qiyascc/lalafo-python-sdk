# Advanced use

## Any API call

`lf.request` sends any call under `base_url` with the same headers, session handling, renewal and error handling as the built in methods:

```python
data = lf.request("GET", "/api/catalog/v3/feed/limits-info/13/77")
```

| Argument | Default | Meaning |
| --- | --- | --- |
| `method` | | `GET`, `POST`, `PUT`, `DELETE`, ... |
| `path` | | A path under `base_url`. A missing leading `/` is added |
| `body` | `None` | Sent as JSON |
| `query` | `None` | A dict of query parameters. `None` and empty values are left out |
| `safe` | `GET` only | Whether the call may be retried. Pass `True` for a `POST` that only reads |
| `auth` | `True` | Send the session. With `True` and no session, `SessionRequiredError` |

It returns the parsed JSON answer, or `None` for an empty one.

## Helpers

| Name | What it does |
| --- | --- |
| `phone(value, code)` | Normalises a phone number to `+<code>...`, as the login and the form do |
| `resolve_params(params, definitions)` | Checks form params against posting params and returns the list that would be sent |
| `jwt_claims(token)` | The claims inside a JWT, or `{}` |

```python
from lalafo_sdk import AdParam, phone, resolve_params

phone("050 123 45 67", "994")
resolve_params([AdParam(id=70, value="42")], lf.catalog.posting_params(4800, 103261))
```

`resolve_params` raises `InvalidRequestError` with every problem joined by `;`, the same check `create` runs.

## Constants

| Name | Value |
| --- | --- |
| `BAKU` | `103261` |
| `AZERBAIJAN` | `13`, the country id |
| `REAL_ESTATE_ROOT` | `2029`, the real estate branch of the category tree |
| `TABS` | The tab names of `ads.list` and the statuses in each |

## The user hash

lalafo ties a session to a `user-hash`, the browser id the website sends. The client takes it from the saved session, or makes a new random one. It is part of `Session.to_dict()`, so a saved session keeps its hash. `lf.user_hash` shows the current one.

## The client object

`repr(lf)` shows the address and the user id, never a token: `Lalafo(base_url='https://lalafo.az', user_id='77')`. `lf.settings` is the loaded {py:class}`~lalafo_sdk.Settings`; create a new client to change it.

## Your own httpx client

```python
import logging

import httpx

from lalafo_sdk import Lalafo

log = logging.getLogger("lalafo")


def show(response: httpx.Response) -> None:
    log.info("%s %s -> %s", response.request.method, response.request.url.path, response.status_code)


lf = Lalafo(saved, http_client=httpx.Client(timeout=30, event_hooks={"response": [show]}))
```

Never log request headers: the `Authorization` header holds the access token.

## Threads

A sync client can be shared between threads for reads. A renewal replaces the session for every thread, which is fine. Do not call `login` on a client other threads are using.
