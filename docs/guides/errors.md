# Errors

Every exception inherits from {py:class}`~lalafo_sdk.LalafoError`.

## The hierarchy

```text
LalafoError
├── ConfigurationError        settings that cannot work
├── InvalidRequestError       a bad argument, form, param or photo, found before sending (also a ValueError)
├── SessionRequiredError      the call needs a session and the client has none
├── WaitTimeoutError          ads.wait ran out of time (.ad holds the last read)
├── TransportError            no usable answer
│   ├── NotSentError          the connection failed, nothing was sent
│   ├── BlockedError          a Cloudflare check page after every retry
│   └── OutcomeUnknownError   a write may or may not have gone through
└── APIError                  lalafo answered with an error
    ├── AuthenticationError   401, or a session that cannot be renewed
    ├── ForbiddenError        403
    ├── NotFoundError         404
    ├── ConflictError         409
    ├── RateLimitError        429 after the retries
    ├── ServerError           5xx after the retries
    └── BadRequestError       other 4xx
        ├── ValidationError       400 or 422, with .fields
        └── CaptchaRequiredError  lalafo wants a captcha after failed sign ins
```

## Attributes

| Exception | Attributes |
| --- | --- |
| all | `message` |
| `TransportError` and below | `path`: the API path that was called |
| `OutcomeUnknownError` | `status_code` when there was an answer |
| `APIError` and below | `status_code`, `body`, `path`, and `fields` |
| `RateLimitError` | `retry_after` from the `Retry-After` header |
| `WaitTimeoutError` | `ad`: the last `Ad` read |

`fields` is a dict of field name to message, built from lalafo's error list. It is empty when lalafo did not say which field was wrong.

```python
from lalafo_sdk import ValidationError

try:
    lf.ads.edit(4242, form)
except ValidationError as exc:
    for field, message in exc.fields.items():
        print(field, message)
```

`str()` of an `APIError` starts with the status code in brackets.

## Which one to catch

| You want to | Catch |
| --- | --- |
| Show form errors | `InvalidRequestError`, `ValidationError` |
| Ask the user to sign in | `SessionRequiredError`, `AuthenticationError` |
| Tell the user to sign in on the website first | `CaptchaRequiredError` |
| Try again later | `BlockedError`, `RateLimitError`, `ServerError`, `NotSentError`, `TransportError` |
| Check the account before retrying | `OutcomeUnknownError` |

```python
from lalafo_sdk import (
    AuthenticationError,
    BlockedError,
    CaptchaRequiredError,
    InvalidRequestError,
    LalafoError,
    OutcomeUnknownError,
    SessionRequiredError,
    ValidationError,
)

try:
    ad = lf.ads.create(form, photos)
except InvalidRequestError as exc:
    show_form_error(str(exc))
except ValidationError as exc:
    show_field_errors(exc.fields)
except (SessionRequiredError, AuthenticationError):
    sign_in_again()
except OutcomeUnknownError:
    check_moderation_tab_first()
except BlockedError:
    retry_in_a_few_minutes()
except LalafoError as exc:
    log_and_retry_later(exc)
```

`CaptchaRequiredError` only comes from `login`.

## Messages

Every message comes from `messages.yaml` and can be replaced; see [Messages](messages.md).
