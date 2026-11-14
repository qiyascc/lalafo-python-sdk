# Models and enums

Everything the SDK returns is a frozen dataclass with plain Python types. Times are timezone aware `datetime` objects in UTC. Models built from lalafo answers keep the original in `.raw`, left out of `repr()` and equality.

| Model | Returned by | Guide |
| --- | --- | --- |
| `Session` | `login`, `auth.renew`, `use_session`, `on_session` | [Signing in](../getting-started/sign-in.md#the-session-object) |
| `User` | `auth.me` | [Signing in](../getting-started/sign-in.md#who-am-i) |
| `Category` | `catalog.categories`, `category`, `real_estate` | [Catalog](../guides/catalog.md) |
| `City` | `catalog.cities` | [Catalog](../guides/catalog.md#cities) |
| `Param`, `ParamValue` | `catalog.filter_params`, `posting_params` | [Catalog](../guides/catalog.md#params) |
| `Draft` | `ads.draft` | [Posting ads](../guides/posting.md#the-steps-one-by-one) |
| `Image` | `ads.upload_photo`, inside `Ad` and `Draft` | [Posting ads](../guides/posting.md) |
| `Ad`, `AdParamValue` | `ads.create`, `publish`, `edit`, `get`, `details`, `all`, `wait` | [Managing ads](../guides/managing.md#read-an-ad) |
| `AdPage` | `ads.list` | [Managing ads](../guides/managing.md#list-your-ads) |
| `Limits` | `ads.limits` | [Managing ads](../guides/managing.md#free-limits) |

```{eval-rst}
.. autoclass:: lalafo_sdk.Session
   :members: to_dict, from_mapping, issued_at, expires_at, renew_due, expired
   :undoc-members: false
.. autoclass:: lalafo_sdk.User
   :members:
   :undoc-members: false
.. autoclass:: lalafo_sdk.Category
   :members: walk, find, leaves
   :undoc-members: false
.. autoclass:: lalafo_sdk.City
   :members:
   :undoc-members: false
.. autoclass:: lalafo_sdk.Param
   :members: value, find
   :undoc-members: false
.. autoclass:: lalafo_sdk.ParamValue
   :members:
   :undoc-members: false
.. autoclass:: lalafo_sdk.Draft
   :members:
   :undoc-members: false
.. autoclass:: lalafo_sdk.Image
   :members:
   :undoc-members: false
.. autoclass:: lalafo_sdk.Ad
   :members: awaiting_payment, offers_promotion
   :undoc-members: false
.. autoclass:: lalafo_sdk.AdParamValue
   :members:
   :undoc-members: false
.. autoclass:: lalafo_sdk.AdPage
   :members: has_more
   :undoc-members: false
.. autoclass:: lalafo_sdk.Limits
   :members:
   :undoc-members: false
```

## Enums and constants

| Name | Values |
| --- | --- |
| `AdStatus` (an `IntEnum`) | `MODERATION` 1, `ACTIVE` 2, `REJECTED` 3, `BANNED` 4, `DRAFT` 7, `DEACTIVATED` 8, `PAYMENT_WAITING` 11, `UNKNOWN` 0. `final` is `False` for `MODERATION`, `DRAFT` and `UNKNOWN` |
| `Currency` | `AZN`, `USD` |
| `ParamKind` | `dropdown`, `input`, `other` |
| `BAKU` | `103261` |
| `AZERBAIJAN` | `13` |
| `REAL_ESTATE_ROOT` | `2029` |
| `TABS` | `active`, `moderation`, `rejected`, `deactivated`, `payment_waiting`, each with its statuses |

```{eval-rst}
.. autoclass:: lalafo_sdk.AdStatus
   :members: final, parse
   :undoc-members:
   :member-order: bysource
.. autoclass:: lalafo_sdk.Currency
   :members:
   :undoc-members:
   :member-order: bysource
.. autoclass:: lalafo_sdk.ParamKind
   :members: parse
   :undoc-members:
   :member-order: bysource
```
