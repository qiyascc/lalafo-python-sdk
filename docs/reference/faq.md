# FAQ and troubleshooting

## Is this an official lalafo API?

No. lalafo has no public API. The SDK uses the same endpoints and headers as the lalafo.az website, as one signed in account, and names itself in the User-Agent. lalafo can change the endpoints; every path is a setting.

## `CaptchaRequiredError` when signing in

lalafo asks for a captcha after several failed sign ins. The SDK never solves captchas. Sign in once on lalafo.az in a browser, wait a while, then try again with the right password.

## `BlockedError: lalafo answered with a Cloudflare check page`

lalafo showed its Cloudflare check page on every attempt. Nothing was processed. Wait a few minutes and try again, and send fewer requests at once. Raising `max_retries` gives more attempts.

## Calls are slow or time out

lalafo.az is sometimes slow. Raise `timeout` (for example to 60) and `max_retries`. Reads are retried; writes that time out raise `OutcomeUnknownError`.

## `OutcomeUnknownError` on `create`

The ad may have been created, or a draft may be left over. Look at `lf.ads.list("moderation")` and `lf.ads.list("active")` before posting again. A leftover draft is picked up and cleared by the next `create`.

## `InvalidRequestError: param … is required`

The post form of that category and city needs that param. Print `lf.catalog.posting_params(category_id, city_id)` and add it.

## `param … has no value_id …`

The value id does not belong to that param. Look it up with `param.find("label")` or print `param.values`.

## `param … takes one value`

Only multi select params may repeat. Remove the extra entries.

## `photo … is … bytes, lalafo needs at least 20480`

lalafo refuses photos under 20 KB and over 20 MB. Use a larger photo or compress a huge one.

## `AuthenticationError: The session expired and has no refresh token`

The saved session cannot be renewed. Sign in again; `on_session` will store the new one.

## My ad is in `PAYMENT_WAITING`

The account is over its free limit in that category. lalafo shows the ad after payment on the website. The SDK does not pay.

## Does it work for lalafo in other countries?

It was built and tested for lalafo.az only. `base_url`, `country_id`, `language` and `phone_code` can point elsewhere, at your own risk.

## How do I get names in Russian?

Set `language="ru_RU"` (or `LALAFO_LANGUAGE=ru_RU`). Labels in params then come in Russian, so `param.find(...)` needs Russian labels.
