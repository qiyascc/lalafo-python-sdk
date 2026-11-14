# Installation

This page goes from a machine with nothing on it to a working `import lalafo_sdk`. If you already have a virtual environment you like, skip to [Install the package](#install-the-package).

## Requirements

| What | Version |
| --- | --- |
| Python | 3.10, 3.11, 3.12 or 3.13 |
| [httpx](https://www.python-httpx.org/) | 0.24 or newer, below 1.0 |
| [goodconf](https://github.com/lincolnloop/goodconf) | 7.1 or newer |
| [pydantic](https://docs.pydantic.dev/) | 2.7 or newer |
| [PyYAML](https://pyyaml.org/) | 6 or newer |

pip installs the four libraries for you. Nothing else is needed: no compiler, no system packages, no browser.

Check your Python version first:

::::{tab-set}

:::{tab-item} Linux and macOS
```bash
python3 --version
```
:::

:::{tab-item} Windows CMD
```bat
py --version
```
:::

::::

If it prints `Python 3.9` or older, install a newer Python from [python.org](https://www.python.org/downloads/) or your system package manager. On Windows, tick **Add python.exe to PATH** in the installer.

## Create a virtual environment

A virtual environment keeps the SDK and its dependencies inside your project folder instead of the system Python. Do this once per project.

::::{tab-set}

:::{tab-item} Linux and macOS
```bash
mkdir my-project
cd my-project
python3 -m venv .venv
. .venv/bin/activate
```
:::

:::{tab-item} Windows CMD
```bat
mkdir my-project
cd my-project
py -m venv .venv
.venv\Scripts\activate.bat
```
:::

::::

After activation the prompt starts with `(.venv)`. Every `pip` and `python` command you run in that window now uses the environment. Open a new terminal later and you need to activate it again; run `deactivate` to leave it.

## Install the package

::::{tab-set}

:::{tab-item} pip
```bash
pip install lalafo-python-sdk
```
:::

:::{tab-item} uv
```bash
uv add lalafo-python-sdk
```
or, without a uv project:
```bash
uv pip install lalafo-python-sdk
```
:::

:::{tab-item} Poetry
```bash
poetry add lalafo-python-sdk
```
:::

:::{tab-item} requirements.txt
```text
lalafo-python-sdk>=0.1,<0.2
```
then
```bash
pip install -r requirements.txt
```
:::

::::

The distribution on PyPI is called `lalafo-python-sdk`. The package you import is `lalafo_sdk`:

```python
import lalafo_sdk
```

## Optional extras

Settings can be read from a config file (see [Configuration](configuration.md)). JSON works out of the box. The other formats need an extra:

| Extra | Install | When you need it |
| --- | --- | --- |
| `yaml` | `pip install "lalafo-python-sdk[yaml]"` | A `lalafo.yaml` or `lalafo.yml` config file |
| `toml` | `pip install "lalafo-python-sdk[toml]"` | A `lalafo.toml` config file on Python 3.10. Python 3.11 and newer read TOML without it |

On Windows CMD use double quotes around the name with brackets, as above. Single quotes do not work there.

## Check that it works

```bash
python -c "import lalafo_sdk; print(lalafo_sdk.__version__)"
```

It prints the installed version, for example `0.1.0`. If you see `ModuleNotFoundError`, the package went into a different Python than the one you are running: activate the virtual environment and install again.

## Before you sign in

The SDK needs no API key. To post you need a lalafo.az account with a password, signed in by phone number or email. Categories, cities, filter params and public ads work without an account. Next: [Signing in and sessions](sign-in.md).

## Upgrade

```bash
pip install --upgrade lalafo-python-sdk
```

Read the [changelog](../reference/changelog.md) before moving to a new minor version. While the version starts with `0.`, a minor release (0.1 to 0.2) may change behaviour, so pin the minor version in production with `lalafo-python-sdk>=0.1,<0.2`.

## Install from source

To try an unreleased change from the main branch:

```bash
pip install "git+https://github.com/qiyascc/lalafo-python-sdk"
```

To work on the SDK itself, see [Development](../project/development.md).

## Uninstall

```bash
pip uninstall lalafo-python-sdk
```

pip leaves the dependencies in place. Delete the `.venv` folder to remove everything at once.
