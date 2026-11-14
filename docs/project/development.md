# Development

This page is for working on the SDK itself: running the tests, the linters and the type checker, building the docs and preparing a change.

## Get the code

```bash
git clone https://github.com/qiyascc/lalafo-python-sdk
cd lalafo-python-sdk
```

## Set up an environment

::::{tab-set}

:::{tab-item} Linux and macOS
```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
```
:::

:::{tab-item} Windows CMD
```bat
py -m venv .venv
.venv\Scripts\activate.bat
pip install -e ".[dev]"
```
:::

::::

The `dev` extra pulls in pytest, pytest-asyncio, ruff, mypy and the type stubs, plus the `toml` and `yaml` extras so the config file tests can run.

## Run the checks

The same three commands run in GitHub Actions on Python 3.10, 3.11, 3.12 and 3.13 for every push and pull request:

```bash
pytest -q
ruff check .
mypy src
```

The tests never reach lalafo.az. Every one of them runs against `httpx.MockTransport`, so they work offline and finish in a couple of seconds. The [testing guide](../guides/testing.md) shows the same technique for your own code.

## Project layout

| Path | What lives there |
| --- | --- |
| `src/lalafo_sdk/client.py` | `Lalafo` and `AsyncLalafo`, the two public clients |
| `src/lalafo_sdk/_core.py` | The request engine: retries, backoff, error mapping, the sync and async runners |
| `src/lalafo_sdk/resources.py` | The namespaces (`client.<namespace>.<method>`) and the checks done before a request is sent |
| `src/lalafo_sdk/models.py` | The typed objects returned by the API |
| `src/lalafo_sdk/config.py` | `Settings`, `Endpoints` and `load_settings` |
| `src/lalafo_sdk/errors.py` | The exception hierarchy |
| `src/lalafo_sdk/messages.yaml` | Every message the SDK produces |
| `tests/` | The test suite |
| `examples/` | Small runnable scripts and an example config file |
| `docs/` | This documentation |

## Build the documentation

The docs are written in Markdown (MyST) and built with Sphinx and the Furo theme. Read the Docs builds them on every push to `main`.

```bash
pip install -r docs/requirements.txt
pip install -e .
sphinx-build -W --keep-going -b html docs docs/_build/html
```

Open `docs/_build/html/index.html` in a browser. `-W` turns warnings into errors, the same way the Read the Docs build does, so a broken link or a missing page fails locally first.

## House rules

- No comments in the code. Names, types and tests carry the meaning; the README, the changelog and these docs carry the reasons.
- Every Python file starts with the signature block of the other files.
- No hardcoded user facing text. A new message goes into `messages.yaml` and is read with `text(...)`.
- A write must never be retried after an answer that leaves its outcome unknown. If a change touches the retry rules, add a test for the case where the request did reach the server.
- Keep the sync and async clients in step. Both are built from the same resource classes, so a new method usually needs no extra code for async, but it needs an async test.

## Sending a change

1. Open an issue first for anything larger than a fix, so the approach can be agreed on.
2. Make the change with tests.
3. Run `pytest`, `ruff check .` and `mypy src`.
4. Add a line to `CHANGELOG.md` under a new version heading.
5. Open a pull request against `main`.
