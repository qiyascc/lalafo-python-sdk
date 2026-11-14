# Signing in and sessions

lalafo signs in with a phone number or an email and a password, and answers with a token pair: a short lived access token and a refresh token. The SDK keeps both in a {py:class}`~lalafo_sdk.Session`, sends the access token with every call, and renews it on its own before it runs out.

Categories, cities, filter params and public ad details work without a session. Everything about your own ads needs one.

## Sign in

```python
from lalafo_sdk import Lalafo

with Lalafo() as lf:
    session = lf.login("050 123 45 67", "password")
    print(session.user_id)
    print(lf.auth.me().username)
```

`lf.login(...)` is the same as `lf.auth.login(...)`. The first argument is a phone number or an email:

| Given | Sent as |
| --- | --- |
| `agent@example.az` | email |
| `050 123 45 67` | mobile `+994501234567` |
| `+994 50 123 45 67` | mobile `+994501234567` |
| `00994501234567` | mobile `+994501234567` |
| `501234567` | mobile `+994501234567` |

Local numbers get the country code from the `phone_code` setting (`994`). A number that cannot be a phone number raises `InvalidRequestError` before anything is sent, and so does a password shorter than 5 characters.

### When lalafo refuses

| Error | When |
| --- | --- |
| `ValidationError` | Wrong login or password. `exc.fields` maps the field to lalafo's message |
| `CaptchaRequiredError` | lalafo wants a captcha after several failed sign ins. The SDK never solves captchas: sign in once on the website in a browser, then try again later |
| `OutcomeUnknownError` | The sign in request timed out. It is not repeated |

## The session object

{py:class}`~lalafo_sdk.Session` holds four strings:

| Field | Meaning |
| --- | --- |
| `token` | The access token, a JWT sent as `Authorization: Bearer ...` |
| `refresh_token` | Used to get a new access token |
| `user_hash` | The browser id lalafo ties the session to; sent as the `user-hash` header |
| `user_id` | The account id |

and a few helpers:

| Member | Meaning |
| --- | --- |
| `to_dict()` | The four fields as a dict, ready for `json.dumps` |
| `Session.from_mapping(data)` | The reverse |
| `issued_at`, `expires_at` | Unix times read from the token, or `None` |
| `renew_due(share)` | `True` once `share` of the lifetime has passed |
| `expired()` | `True` once the token is past its end |

`repr(session)` shows the user id and the expiry, never the tokens.

## Keep the session

Pass a saved session as the first argument. A `Session` and a plain dict with a `token` both work:

```python
import json
from pathlib import Path

from lalafo_sdk import Lalafo, Session

FILE = Path("lalafo-session.json")


def save(session: Session) -> None:
    FILE.write_text(json.dumps(session.to_dict()))


saved = json.loads(FILE.read_text()) if FILE.exists() else None
with Lalafo(saved, on_session=save) as lf:
    if lf.session is None:
        lf.login("050 123 45 67", "password")
    print(lf.auth.me().username)
```

`on_session` is called with every new session: after `login` and after every renewal. Saving inside it means the file always holds the latest tokens, even when the SDK renewed them in the middle of a long job.

To swap the session of a client that already exists:

```python
lf.use_session(saved)
```

It returns the `Session` it loaded, or `None` when you pass `None`. A dict without a `token`, or any other type, raises `InvalidRequestError`.

:::{warning}
The tokens give full access to the account. Keep the session file out of version control and logs.
:::

## Automatic renewal

Every call that needs a session goes through a small guard:

1. If the access token has passed `renew_at` of its lifetime (75% by default), the SDK renews it first. If that renewal fails but the old token has not expired yet, the call goes ahead with the old one.
2. The call is sent.
3. If lalafo answers 401 and there is a refresh token, the SDK renews the session once and sends the call again. A 401 means the call was not processed, so repeating it is safe even for writes.

A renewal that lalafo refuses raises `AuthenticationError` with "The session expired and has no refresh token. Sign in again." Sign in and the new session goes to `on_session`.

You can also renew by hand:

```python
session = lf.auth.renew()
```

Lower `renew_at` to renew earlier, for example `Lalafo(saved, renew_at=0.5)`.

## Who am I

```python
user = lf.auth.me()
print(user.id, user.username, user.mobile, user.email)
```

{py:class}`~lalafo_sdk.User` has `id`, `username`, `mobile`, `email` and `raw`. It needs a session with a user id.

## Sign out

```python
lf.auth.logout()
```

Tells lalafo to end the session and sets `lf.session` to `None`.

## No session

A call that needs a session raises `SessionRequiredError` before anything is sent when the client has none.
