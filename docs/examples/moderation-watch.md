# Moderation watch

Follows the ads waiting in moderation and sends a Telegram message for each one that gets rejected, with lalafo's reason. Run it every 10 minutes.

```python
import json
import os
from pathlib import Path

import httpx

from lalafo_sdk import AdStatus, NotFoundError

SEEN = Path("moderation-seen.json")
TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT = os.environ["TELEGRAM_CHAT_ID"]


def notify(text: str) -> None:
    httpx.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
               json={"chat_id": CHAT, "text": text}, timeout=15).raise_for_status()


def main() -> None:
    from session_file import signed_in_client

    watching = set(json.loads(SEEN.read_text())) if SEEN.exists() else set()
    with signed_in_client() as lf:
        for ad in lf.ads.all("moderation"):
            watching.add(ad.id)
        for ad_id in sorted(watching):
            try:
                ad = lf.ads.get(ad_id)
            except NotFoundError:
                watching.discard(ad_id)
                continue
            if not ad.status.final:
                continue
            watching.discard(ad_id)
            if ad.status in (AdStatus.REJECTED, AdStatus.BANNED):
                notify(f"lalafo rejected ad {ad.id}: {ad.title}\n{ad.rejected_reason or 'no reason given'}\n{ad.url or ''}")
    SEEN.write_text(json.dumps(sorted(watching)))


if __name__ == "__main__":
    main()
```

- Every ad in moderation is added to the watch list; finished or deleted ones leave it.
- `status.final` is `True` once moderation is over, whatever the outcome.
- httpx is installed with the SDK, so nothing else is needed.

For a single ad right after posting, `lf.ads.wait(ad.id)` does the same in one call; see [Posting ads](../guides/posting.md#after-posting).
