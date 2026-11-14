# Posting ads

`lf.ads.create(form, photos)` posts an ad the way the lalafo website does. This page covers the form, the photos, every check and the individual steps.

## The form

The form is an {py:class}`~lalafo_sdk.AdForm` or a dict with the same keys:

| Key | Type | Default | Meaning |
| --- | --- | --- | --- |
| `category_id` | `int` | required | A postable category |
| `city_id` | `int` | required | A city, such as `BAKU` |
| `description` | `str` | required | 1 to 6000 characters |
| `price` | `int` | `None` | 1 or more. Leave it out for a negotiable price |
| `currency` | `"AZN"` or `"USD"` | `AZN` | Ignored without a price |
| `is_negotiable` | `bool` | `False` | Marks a price as negotiable. Always `True` without a price |
| `params` | list | `[]` | See [Filling in params](catalog.md#filling-in-params) |
| `username` | `str` | not sent | The contact name on the ad, up to 100 characters. Without it lalafo uses the account's |
| `mobile` | `str` | not sent | The contact phone, normalised to `+994...`. Without it lalafo uses the account's |
| `email` | `str` | not sent | Up to 100 characters |
| `hide_phone` | `bool` | `False` | Hide the phone number on the ad |
| `is_hide_house_number` | `bool` | `False` | Hide the house number of the address |
| `is_private_ad` | `bool` | `False` | The flag of the same name on the lalafo form |

Unknown keys are refused, so a typo fails loudly. lalafo writes the title itself from the category and the params.

## Photos

The second argument is a list of 1 to 20 photos. Each can be:

| Form | Example |
| --- | --- |
| A path | `"kitchen.jpg"` or `Path("kitchen.jpg")` |
| Bytes | `data`, sent as `photo1.jpg`, `photo2.jpg`, ... |
| `(filename, bytes)` | `("kitchen.jpg", data)` |
| `(filename, bytes, content_type)` | `("kitchen.png", data, "image/png")` |

Every photo must be between 20 KB and 20 MB. The order of the list is the order on the ad.

## What happens in `create`

1. The form and the photos are checked locally.
2. The posting params for the category and city are loaded, and the form's params are checked against them.
3. A draft is made. lalafo may hand back a draft left over from an earlier attempt; any photos still in it are removed.
4. The photos are uploaded into the draft, one by one.
5. The draft is saved with the form and the photo order.
6. The draft is published.

The result is an {py:class}`~lalafo_sdk.Ad`.

## Checks before sending

All of these raise `InvalidRequestError` before the draft is made:

- The form has every required key and no unknown ones, and each value has the right type and size.
- The phone number in `mobile`, when given, is a valid number.
- There are 1 to 20 photos, each 20 KB to 20 MB, of a supported form.
- Every param id exists for the category and city.
- Every `value_id` exists in its param.
- A single value param has one entry only.
- Every required param is present.
- Each param entry has exactly one of `value_id` and `value`.

Param problems are reported together in one message, separated by `;`.

```python
from lalafo_sdk import InvalidRequestError

try:
    lf.ads.create(form, ["kitchen.jpg"])
except InvalidRequestError as exc:
    print(exc)
```

prints something like `param 69 (Otaq sayı) is required; param 70 does not exist for this category and city`.

## After posting

| `ad.status` | Meaning |
| --- | --- |
| `AdStatus.MODERATION` | The usual case: lalafo is checking the ad |
| `AdStatus.PAYMENT_WAITING` | Over the account's free limit. `ad.awaiting_payment` is `True`. lalafo shows it after payment on the website; the SDK never pays |
| `AdStatus.ACTIVE` | Already live |

`ad.offers_promotion` is `True` when lalafo offers paid views for the ad (`"adViews"` in `ad.campaign_types`).

Wait for moderation to end:

```python
from lalafo_sdk import WaitTimeoutError

try:
    final = lf.ads.wait(ad.id, timeout=600, interval=15)
except WaitTimeoutError as exc:
    final = exc.ad
print(final.status.name, final.rejected_reason)
```

## The steps one by one

Each step of `create` is also available on its own, for flows that need control between them, such as uploading photos while the user is still typing:

```python
draft = lf.ads.draft()
if draft.images:
    lf.ads.remove_photos([image.id for image in draft.images])

images = [lf.ads.upload_photo(draft.id, path, index) for index, path in enumerate(paths, start=1)]
lf.ads.save_draft(draft.id, form, [image.id for image in images])
ad = lf.ads.publish(draft.id)
```

| Method | Returns | Notes |
| --- | --- | --- |
| `draft()` | `Draft` | `id`, `images`, `mobile`, `username`, `raw` |
| `upload_photo(ad_id, photo, index=1)` | `Image` | `index` only appears in error messages |
| `remove_photos(image_ids)` | lalafo's answer | |
| `save_draft(ad_id, form, image_ids, params=None)` | lalafo's answer | Checks the form against `params`, loading the posting params when you pass none |
| `publish(ad_id)` | `Ad` | |

`create` is the safer choice: it checks the form before it touches the draft.

## When lalafo refuses

| Error | When |
| --- | --- |
| `ValidationError` | lalafo rejected a field. `exc.fields` maps field names to messages |
| `ForbiddenError` | The account may not post here |
| `ConflictError` | lalafo answered 409 Conflict |
| `AuthenticationError` | The session is gone and cannot be renewed |

## Timeouts

Every step of `create` that changes something (draft, uploads, save, publish) is a write. A timeout, a cut connection or a 5xx during any of them raises `OutcomeUnknownError` and nothing is resent. The ad may exist as a draft or may even be published. Look at `lf.ads.list("moderation")` before trying again; see [Safety and retries](safety.md).
