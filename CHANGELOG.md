# Changelog

## 0.1.0

- Sync `Lalafo` and async `AsyncLalafo`
- Sign in with a phone number or email and password; the session can be saved and loaded back
- The session renews itself at 75% of the token lifetime, or once after a 401, and `on_session` gets every new session
- Category tree with a real estate helper, cities, public filter params and posting params
- One call `ads.create` (draft, photos, save, publish) and every step on its own
- Edit, deactivate, activate, delete, my ad, public ad, my ads by status with paging, free ad limits, wait for moderation
- Params are checked against the category before anything is sent: unknown ids, unknown values, single value params and required params
- Reads retry with backoff, connection failures retry because nothing was sent, a Cloudflare check page is retried and then raises `BlockedError`
- Writes are never resent after a timeout, a cut connection or a 5xx; `OutcomeUnknownError` says to check the account first
- A sign in that lalafo answers with a captcha request raises `CaptchaRequiredError`
- The client sends the headers the lalafo website sends: no device fingerprint and no app identity
- goodconf settings, endpoint paths and messages are configurable
