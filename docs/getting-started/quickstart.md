# Quickstart

This walk through posts a two room flat for sale in Baku. It assumes the SDK is installed ([Installation](installation.md)) and that you have a lalafo.az account with a password.

## 1. Sign in and keep the session

`post.py`:

```python
import json
from pathlib import Path

from lalafo_sdk import BAKU, Lalafo, Session

SESSION = Path("lalafo-session.json")


def save(session: Session) -> None:
    SESSION.write_text(json.dumps(session.to_dict()))


lf = Lalafo(json.loads(SESSION.read_text()) if SESSION.exists() else None, on_session=save)
if lf.session is None:
    lf.login("050 123 45 67", "password")
```

The first run signs in and `save` writes the session. Later runs load it, and the SDK renews it when needed, calling `save` each time. Keep `lalafo-session.json` out of version control.

## 2. Pick the category and the city

lalafo posts into a category and a city. For a flat for sale in an old building the category is `4800`, and Baku is `BAKU` (`103261`). The [real estate example](../examples/real-estate.md) lists the other real estate ids; [Categories, cities and params](../guides/catalog.md) shows how to find any category.

## 3. See which params the category wants

```python
params = lf.catalog.posting_params(4800, BAKU)
for param in params:
    values = ", ".join(f"{v.id}={v.value}" for v in param.values[:8])
    print(param.id, param.name, param.kind, "required" if param.required else "", "multi" if param.multi else "", values)
```

`posting_params` is the exact list the lalafo post form uses for that category and city. Each param is either a dropdown, which takes the id of one of its values, or an input, which takes text.

## 4. Fill in the form

```python
rooms = next(p for p in params if p.id == 69)

form = {
    "category_id": 4800,
    "city_id": BAKU,
    "price": 80000,
    "currency": "AZN",
    "description": "Satılır 2 otaqlı köhnə tikili, təmirli, kupçalı.",
    "params": [
        {"id": 69, "value_id": rooms.find("2 otaqlı").id},
        {"id": 70, "value": "42"},
    ],
}
```

- `category_id` and `city_id` from step 2.
- `price` is a whole number. Leave it out for a negotiable price.
- `currency` is `AZN` (the default) or `USD`.
- `description` is the text of the ad, up to 6000 characters. lalafo writes the title itself, such as "Bakı, 2 otaqlı, Köhnə tikili, 42 kv. m".
- `params` holds one entry per param: `value_id` for a dropdown, `value` for an input.

`rooms.find("2 otaqlı")` looks up a dropdown value by its label, ignoring case and surrounding spaces. It returns `None` when there is no such label, so check the labels printed in step 3.

## 5. Post it with photos

```python
ad = lf.ads.create(form, ["kitchen.jpg", "room.jpg"])
print(ad.id, ad.status.name, ad.url)
```

`create` loads the posting params again and checks the form against them, makes a draft, uploads the photos, saves the draft and publishes it. One to twenty photos, each between 20 KB and 20 MB.

The ad comes back in moderation (`AdStatus.MODERATION`). An ad over the account's free limit comes back as `AdStatus.PAYMENT_WAITING` instead; lalafo shows it only after payment on the website. The SDK never pays.

## 6. Wait for moderation

```python
final = lf.ads.wait(ad.id, timeout=900, interval=30)
print(final.status.name, final.rejected_reason)
```

`wait` reads the ad every `interval` seconds until moderation ends (any status other than moderation, draft or unknown) and returns it. After `timeout` seconds it raises `WaitTimeoutError`, which carries the last read in `exc.ad`.

## 7. Close the client

```python
lf.close()
```

or use `with Lalafo(...) as lf:` so it closes itself.

## The same with async

```python
import asyncio
import json
from pathlib import Path

from lalafo_sdk import AsyncLalafo


async def main() -> None:
    async with AsyncLalafo(json.loads(Path("lalafo-session.json").read_text())) as lf:
        page = await lf.ads.list("active")
        for ad in page.items:
            print(ad.id, ad.title, ad.price)


asyncio.run(main())
```

## Next steps

- [Posting ads](../guides/posting.md): every field of the form and every check.
- [Managing ads](../guides/managing.md): edit, deactivate, activate, delete, list.
- [Safety and retries](../guides/safety.md): what a timeout on a write means.
