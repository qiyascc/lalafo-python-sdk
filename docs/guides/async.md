# Async

`AsyncLalafo` has the same namespaces, methods and results as `Lalafo`. Add `await`.

```python
import asyncio
import json
from pathlib import Path

from lalafo_sdk import AsyncLalafo, Session

FILE = Path("lalafo-session.json")


def save(session: Session) -> None:
    FILE.write_text(json.dumps(session.to_dict()))


async def main() -> None:
    async with AsyncLalafo(json.loads(FILE.read_text()), on_session=save) as lf:
        active, waiting = await asyncio.gather(lf.ads.all("active"), lf.ads.all("moderation"))
        print(len(active), "active,", len(waiting), "in moderation")


asyncio.run(main())
```

## Notes

- Use `async with` or `await lf.close()`. `http_client=` must be an `httpx.AsyncClient`.
- `on_session` is a plain function, called without `await`, also by the async client. Keep it quick: write a file or a row, nothing slow.
- `lf.session`, `lf.use_session(...)` and `lf.user_hash` are plain attributes and methods.
- Backoff waits use `asyncio.sleep`, so retries do not block the event loop. `ads.wait` sleeps the same way.
- One client holds one session. For several accounts, one client each. Do not sign in on a client while other calls on it are running.

## Parallel reads

```python
ads = await asyncio.gather(*(lf.ads.details(ad_id) for ad_id in ids))
```

lalafo is sometimes slow and shows Cloudflare check pages under load, so keep parallel requests low, with a semaphore for long lists:

```python
gate = asyncio.Semaphore(3)

async def details(ad_id):
    async with gate:
        return await lf.ads.details(ad_id)

ads = await asyncio.gather(*(details(ad_id) for ad_id in ids))
```

## Posting in parallel

lalafo can hand back a draft the account already has; that is why `create` clears old photos from the draft it gets. Two `create` calls running at the same time on one account could therefore end up working on the same draft. Post one ad at a time per account.
