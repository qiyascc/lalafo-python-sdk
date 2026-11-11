from __future__ import annotations

from collections.abc import Mapping
from importlib import resources
from pathlib import Path
from typing import Any, Union

import yaml

PathLike = Union[str, Path]

_PACKAGE_FILE = "messages.yaml"
_catalog: dict[str, str] = {}


def _flatten(node: Mapping[str, Any], prefix: str = "") -> dict[str, str]:
    flat: dict[str, str] = {}
    for key, value in node.items():
        path = f"{prefix}{key}"
        if isinstance(value, Mapping):
            flat.update(_flatten(value, f"{path}."))
        else:
            flat[path] = str(value)
    return flat


def _parse(raw: str) -> dict[str, str]:
    data = yaml.safe_load(raw) or {}
    if not isinstance(data, Mapping):
        raise ValueError("messages file must contain a mapping")
    return _flatten(data)


def _read_packaged() -> dict[str, str]:
    raw = resources.files(__package__).joinpath(_PACKAGE_FILE).read_text(encoding="utf-8")
    return _parse(raw)


def catalog() -> Mapping[str, str]:
    if not _catalog:
        _catalog.update(_read_packaged())
    return _catalog


def use(source: PathLike | Mapping[str, Any]) -> None:
    overrides = _flatten(source) if isinstance(source, Mapping) else _parse(Path(source).read_text(encoding="utf-8"))
    unknown = set(overrides) - set(_read_packaged())
    if unknown:
        raise KeyError(", ".join(sorted(unknown)))
    catalog()
    _catalog.update(overrides)


def reset() -> None:
    _catalog.clear()


def text(key: str, **params: Any) -> str:
    template = catalog()[key]
    return template.format(**params) if params else template
