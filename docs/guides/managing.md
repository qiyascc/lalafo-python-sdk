# Managing ads

Everything about the account's own ads is under `lf.ads` and needs a session.

## Read an ad

```python
from lalafo_sdk import AdStatus

ad = lf.ads.get(4242)
print(ad.title, ad.status.name, ad.price, ad.currency, ad.url)
if ad.status is AdStatus.REJECTED:
    print(ad.rejected_reason)
```

`get` reads one of your own ads, with everything lalafo shows the owner. `details` reads any public ad, without a session:

```python
public = lf.ads.details(4242)
```

Both return an {py:class}`~lalafo_sdk.Ad`:

| Field | Meaning |
| --- | --- |
| `id` | The ad id, an `int` |
| `status` | An `AdStatus`, see below |
| `title`, `description` | Texts |
| `price`, `currency` | The price as a `float` and its currency, or `None` |
| `category_id`, `city_id` | Where the ad is |
| `url` | The full address on lalafo.az |
| `images` | A tuple of `Image` with `id`, `thumbnail`, `original`, `main` |
| `params` | A tuple of `AdParamValue` with `id`, `name`, `value`, `value_id` |
| `rejected_reason` | Why moderation rejected it |
| `mobile`, `username` | The contact on the ad |
| `created_at`, `updated_at` | `datetime` in UTC |
| `campaign_types` | Paid promotion types lalafo offers for it |
| `raw` | The whole answer |

`ad.awaiting_payment` and `ad.offers_promotion` are shortcuts, see [Posting ads](posting.md#after-posting).

### Statuses

| `AdStatus` | Value | Meaning |
| --- | --- | --- |
| `MODERATION` | 1 | Being checked |
| `ACTIVE` | 2 | Live |
| `REJECTED` | 3 | Rejected, see `rejected_reason` |
| `BANNED` | 4 | Banned by lalafo |
| `DRAFT` | 7 | Not published |
| `DEACTIVATED` | 8 | Taken down by the owner |
| `PAYMENT_WAITING` | 11 | Waiting for payment on the website |
| `UNKNOWN` | 0 | A status this version does not know |

`status.final` is `False` for `MODERATION`, `DRAFT` and `UNKNOWN`, `True` for the rest.

## List your ads

```python
page = lf.ads.list("active", page=1, per_page=20)
for ad in page.items:
    print(ad.id, ad.title, ad.status.name)
print(page.page, page.page_count, page.total, page.has_more)
```

| Argument | Default | Meaning |
| --- | --- | --- |
| `status` | `None` | One of the tabs below, or `None` for all |
| `page` | `1` | Page number, from 1 |
| `per_page` | `20` | 1 to 100 |

| Tab | Statuses |
| --- | --- |
| `"active"` | `ACTIVE`, `PAYMENT_WAITING` |
| `"moderation"` | `MODERATION` |
| `"rejected"` | `REJECTED`, `BANNED` |
| `"deactivated"` | `DEACTIVATED` |
| `"payment_waiting"` | `PAYMENT_WAITING` |

The mapping is also importable as `TABS`. Another tab name raises `InvalidRequestError`.

{py:class}`~lalafo_sdk.AdPage` has `items`, `page`, `page_count`, `total` and `has_more`.

`all(status=None, max_pages=50)` reads every page, 100 ads at a time, and returns a tuple:

```python
deactivated = lf.ads.all("deactivated")
```

## Edit an ad

```python
ad = lf.ads.edit(4242, {**form, "price": 75000})
ad = lf.ads.edit(4242, form, ["new.jpg"])
ad = lf.ads.edit(4242, form, ["only.jpg"], keep_photos=False)
```

`edit(ad_id, form, images=None, *, keep_photos=True)` takes the full form, checked like a new one. What happens:

1. The current ad is read.
2. The posting params for that ad are loaded and the form is checked.
3. New photos, if any, are uploaded.
4. The ad is saved. With `keep_photos=True` the old photos stay and the new ones are added after them. With `keep_photos=False` and new photos, only the new photos remain. With `keep_photos=False` and no new photos, the old photos stay, so an ad is never left without any.
5. Photos that are no longer on the ad are removed from lalafo.

An edit sends the ad back to moderation. The photo limits are the same as for a new ad, except that `images` may be empty.

## Take an ad down and put it back

```python
lf.ads.deactivate(4242)
lf.ads.activate(4242)
```

A deactivated ad is hidden but kept, and can be activated again.

## Delete an ad

```python
lf.ads.delete(4242)
```

## Free limits

```python
limits = lf.ads.limits()
print(limits.raw)
```

How many free ads the account has left, as lalafo reports it. The structure of the answer is lalafo's own, so it is kept as is in `raw`.

## Ids

Ad ids are whole numbers. Text such as `"4242"` is accepted; anything else raises `InvalidRequestError`.

## Writes are not repeated

`edit`, `deactivate`, `activate` and `delete` are writes. A timeout, a cut connection or a 5xx raises `OutcomeUnknownError` and nothing is resent. Read the ad with `get` before trying again.
