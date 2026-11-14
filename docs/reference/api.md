# API reference

Generated from the code. The code has no docstrings; the guides explain each part and this page lists every public class, method and argument. Import from the top level package: `from lalafo_sdk import Lalafo, AdForm, ValidationError`. The resource classes are reached through a client as `lf.auth`, `lf.catalog` and `lf.ads`.

## Clients

See [Quickstart](../getting-started/quickstart.md), [Signing in and sessions](../getting-started/sign-in.md) and [Async](../guides/async.md).

```{eval-rst}
.. autoclass:: lalafo_sdk.Lalafo
   :members: login, request, use_session, close

.. autoclass:: lalafo_sdk.AsyncLalafo
   :members: login, request, use_session, close
```

| Constructor argument | Meaning |
| --- | --- |
| `session` | A saved `Session`, a dict with a `token`, or `None` |
| `settings` | A ready `Settings` object |
| `config_file` | Path of a config file |
| `on_session` | A function called with every new `Session` |
| `http_client` | Your own `httpx.Client` or `httpx.AsyncClient` |
| any setting | Such as `timeout=30` |

Attributes: `session` (the current `Session` or `None`), `user_hash`, `settings`, `on_session`.

## `lf.auth`

```{eval-rst}
.. autoclass:: lalafo_sdk.resources.Auth
   :members: login, renew, logout, me
```

## `lf.catalog`

See [Categories, cities and params](../guides/catalog.md).

```{eval-rst}
.. autoclass:: lalafo_sdk.resources.Catalog
   :members: categories, category, real_estate, cities, filter_params, posting_params
```

## `lf.ads`

See [Posting ads](../guides/posting.md) and [Managing ads](../guides/managing.md).

```{eval-rst}
.. autoclass:: lalafo_sdk.resources.Ads
   :members: create, draft, upload_photo, remove_photos, save_draft, publish, edit, deactivate, activate, delete, get, details, list, all, limits, wait
```

## The form

```{eval-rst}
.. autoclass:: lalafo_sdk.AdForm
   :members: body
   :undoc-members: false

.. autoclass:: lalafo_sdk.AdParam
   :members:
   :undoc-members: false
```

## Helpers

See [Advanced use](../guides/advanced.md#helpers).

```{eval-rst}
.. autofunction:: lalafo_sdk.phone
.. autofunction:: lalafo_sdk.resolve_params
.. autofunction:: lalafo_sdk.jwt_claims
```

## Settings

See [Configuration](../getting-started/configuration.md).

```{eval-rst}
.. autofunction:: lalafo_sdk.load_settings

.. autoclass:: lalafo_sdk.Settings
   :members: path, url, resolved_user_agent, check_transport
   :undoc-members: false

.. autoclass:: lalafo_sdk.Endpoints
   :members:
   :undoc-members: false
```

## Messages

```{eval-rst}
.. autofunction:: lalafo_sdk.messages.use
.. autofunction:: lalafo_sdk.messages.reset
.. autofunction:: lalafo_sdk.messages.catalog
.. autofunction:: lalafo_sdk.messages.text
```

## Errors

See [Errors](../guides/errors.md).

```{eval-rst}
.. autoexception:: lalafo_sdk.LalafoError
.. autoexception:: lalafo_sdk.ConfigurationError
.. autoexception:: lalafo_sdk.InvalidRequestError
.. autoexception:: lalafo_sdk.SessionRequiredError
.. autoexception:: lalafo_sdk.WaitTimeoutError
.. autoexception:: lalafo_sdk.TransportError
.. autoexception:: lalafo_sdk.NotSentError
.. autoexception:: lalafo_sdk.BlockedError
.. autoexception:: lalafo_sdk.OutcomeUnknownError
.. autoexception:: lalafo_sdk.APIError
   :members: fields
.. autoexception:: lalafo_sdk.AuthenticationError
.. autoexception:: lalafo_sdk.ForbiddenError
.. autoexception:: lalafo_sdk.NotFoundError
.. autoexception:: lalafo_sdk.ConflictError
.. autoexception:: lalafo_sdk.RateLimitError
.. autoexception:: lalafo_sdk.ServerError
.. autoexception:: lalafo_sdk.BadRequestError
.. autoexception:: lalafo_sdk.ValidationError
.. autoexception:: lalafo_sdk.CaptchaRequiredError
```
