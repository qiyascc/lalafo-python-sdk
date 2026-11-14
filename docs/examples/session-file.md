# A session file

Sign in once, keep the session in a JSON file, and let the SDK keep it fresh.

```python
import json
import os
from pathlib import Path

from lalafo_sdk import AuthenticationError, Lalafo, Session

FILE = Path(os.environ.get("LALAFO_SESSION_FILE", "lalafo-session.json"))


def save(session: Session) -> None:
    FILE.write_text(json.dumps(session.to_dict()))
    FILE.chmod(0o600)


def signed_in_client() -> Lalafo:
    saved = json.loads(FILE.read_text()) if FILE.exists() else None
    lf = Lalafo(saved, on_session=save)
    if lf.session is not None:
        try:
            lf.auth.me()
            return lf
        except AuthenticationError:
            pass
    lf.login(os.environ["LALAFO_LOGIN"], os.environ["LALAFO_PASSWORD"])
    return lf


if __name__ == "__main__":
    with signed_in_client() as lf:
        user = lf.auth.me()
        print(user.id, user.username, lf.session)
```

- `save` runs after every sign in and every renewal, so the file is always current.
- `lf.auth.me()` checks the session and renews it on the way if it is due.
- `LALAFO_LOGIN` is a phone number or an email.
- `chmod(0o600)` keeps the file private on Linux and macOS.

Use it from other scripts:

```python
from session_file import signed_in_client

with signed_in_client() as lf:
    print(len(lf.ads.all("active")))
```
