# Configuration

`Lalafo()` works with no configuration at all. Settings can come from code, the environment or a config file, loaded with [goodconf](https://github.com/lincolnloop/goodconf).

## Where settings come from

1. **Arguments in code**, such as `Lalafo(timeout=10)`. Highest priority.
2. **Environment variables** starting with `LALAFO_`.
3. **A config file**, such as `lalafo.toml`.
4. **The defaults** below.

## In code

```python
from lalafo_sdk import Lalafo

lf = Lalafo(saved_session, timeout=45, max_retries=3, on_session=save)
```

The first positional argument is a saved session. `on_session` is a callback, not a setting. Every setting can be passed as a keyword.

Shared settings:

```python
from lalafo_sdk import Lalafo, load_settings

settings = load_settings("/etc/my-agency/lalafo.toml")
lf = Lalafo(saved_session, settings=settings)
```

## Environment variables

```bash
export LALAFO_TIMEOUT=45
export LALAFO_MAX_RETRIES=3
export LALAFO_LANGUAGE=ru_RU
```

Windows CMD:

```bat
set LALAFO_TIMEOUT=45
set LALAFO_LANGUAGE=ru_RU
```

Nested settings use a double underscore: `LALAFO_ENDPOINTS__LOGIN=/api/auth/login`.

## Config file

The client looks for `lalafo.toml`, `lalafo.yaml`, `lalafo.yml` or `lalafo.json` in the working directory, or the file named in `LALAFO_CONFIG` or `config_file=`.

::::{tab-set}

:::{tab-item} TOML
```toml
base_url = "https://lalafo.az"
country_id = 13
language = "az_AZ"
phone_code = "994"
timeout = 30
max_retries = 2
```
:::

:::{tab-item} YAML
```yaml
base_url: https://lalafo.az
country_id: 13
language: az_AZ
phone_code: "994"
timeout: 30
max_retries: 2
```
:::

:::{tab-item} JSON
```json
{
  "base_url": "https://lalafo.az",
  "country_id": 13,
  "language": "az_AZ",
  "phone_code": "994",
  "timeout": 30,
  "max_retries": 2
}
```
:::

::::

The repository has the same file: [examples/lalafo.toml](https://github.com/qiyascc/lalafo-python-sdk/blob/main/examples/lalafo.toml). YAML needs the `yaml` extra, TOML on Python 3.10 the `toml` extra.

## All settings

| Setting | Environment variable | Default | What it does |
| --- | --- | --- | --- |
| `base_url` | `LALAFO_BASE_URL` | `https://lalafo.az` | Site address. The API lives under it at `/api` |
| `country_id` | `LALAFO_COUNTRY_ID` | `13` | Country id sent as the `country-id` header. 13 is Azerbaijan |
| `language` | `LALAFO_LANGUAGE` | `az_AZ` | Sent as the `language` header, such as `az_AZ` or `ru_RU`. Changes the language of names and messages |
| `phone_code` | `LALAFO_PHONE_CODE` | `994` | Country calling code used to turn a local number into an international one |
| `endpoints` | `LALAFO_ENDPOINTS__<NAME>` | see below | Path of every API call, relative to `base_url` |
| `timeout` | `LALAFO_TIMEOUT` | `30` | Seconds to wait for an answer |
| `connect_timeout` | `LALAFO_CONNECT_TIMEOUT` | `10` | Seconds to wait for a connection |
| `max_retries` | `LALAFO_MAX_RETRIES` | `2` | Extra attempts for calls that are safe to repeat, 0 to 10 |
| `backoff_base` | `LALAFO_BACKOFF_BASE` | `0.8` | First wait between retries, in seconds |
| `backoff_cap` | `LALAFO_BACKOFF_CAP` | `8` | Longest wait between retries, in seconds |
| `renew_at` | `LALAFO_RENEW_AT` | `0.75` | Share of the token lifetime after which the session is renewed, 0.1 to 1 |
| `user_agent` | `LALAFO_USER_AGENT` | `lalafo-python-sdk/{version}` | User-Agent header. `{version}` becomes the SDK version |
| `allow_insecure_http` | `LALAFO_ALLOW_INSECURE_HTTP` | `false` | Allow a plain http `base_url` outside localhost, for a private test server only |

Values are checked when they load: `country_id=0`, `phone_code="+994"` or `renew_at=2` fail at once.

## Endpoints

Every path is a setting, so a change on lalafo's side can be followed without a new release. Paths with `{ad_id}`, `{user_id}` or `{country_id}` have those filled in for each call.

| Name | Default |
| --- | --- |
| `login` | `/api/auth/login` |
| `renew` | `/api/auth/renew-session` |
| `logout` | `/api/auth/logout` |
| `user` | `/api/user/v3/users/{user_id}` |
| `categories` | `/api/proxy/catalog/v3/categories/tree` |
| `locations` | `/api/proxy/location` |
| `filter_params` | `/api/catalog/v3/params/filter` |
| `posting_params` | `/api/catalog/v32/params/posting` |
| `draft` | `/api/catalog/v32/posting-ads/temp` |
| `draft_save` | `/api/catalog/v32/posting-ads/temp/{ad_id}` |
| `draft_publish` | `/api/catalog/v32/posting-ads/temp/{ad_id}/publish` |
| `image_upload` | `/api/upload/swoole-upload/v3/images/upload` |
| `image_remove` | `/api/catalog/v3/images/remove-by-ids` |
| `my_ad` | `/api/catalog/v3/feed/my-ad-details/{ad_id}` |
| `ad_edit` | `/api/catalog/v32/posting-ads/{ad_id}` |
| `ad_activate` | `/api/catalog/v32/posting-ads/{ad_id}/activate` |
| `ad_deactivate` | `/api/catalog/v3/catalog/feed/{ad_id}/deactivate` |
| `ad_delete` | `/api/catalog/v3/catalog/feed/{ad_id}` |
| `my_ads` | `/api/search/v3/feed/my/all` |
| `ad_details` | `/api/search/v3/feed/details/{ad_id}` |
| `limits` | `/api/catalog/v3/feed/limits-info/{country_id}/{user_id}` |

## Other countries

The defaults are lalafo.az, the only site this client was built and tested against. lalafo runs the same platform in other countries. Pointing `base_url`, `country_id`, `language` and `phone_code` at one of them may work, at your own risk.

## The User-Agent

The SDK sends `lalafo-python-sdk/<version>`. Put your product's name in front if you run one on top of it:

```python
lf = Lalafo(user_agent="my-agency/1.0 lalafo-python-sdk/{version}")
```

## Plain http

`base_url` must be https, because the session token travels with the requests. `localhost`, `127.0.0.1` and `::1` may use http. Anything else raises `ConfigurationError` unless `allow_insecure_http=True`.

## Your own httpx client

```python
import httpx

from lalafo_sdk import Lalafo

lf = Lalafo(saved_session, http_client=httpx.Client(proxy="http://proxy.internal:3128", timeout=30))
```

`proxy=` needs httpx 0.26 or newer; older versions call it `proxies=`. A client you pass in is not closed by `lf.close()`. Use `httpx.AsyncClient` with `AsyncLalafo`.
