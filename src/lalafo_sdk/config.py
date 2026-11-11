from __future__ import annotations

from typing import Any, Optional, Sequence, Union
from urllib.parse import quote, urlencode, urlsplit

from goodconf import Field, GoodConf, GoodConfConfigDict
from pydantic import BaseModel, field_validator

from ._version import __version__
from .errors import ConfigurationError
from .messages import text

LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})

Query = Union[dict[str, Any], Sequence[tuple[str, Any]]]


class Endpoints(BaseModel):
    login: str = "/api/auth/login"
    renew: str = "/api/auth/renew-session"
    logout: str = "/api/auth/logout"
    user: str = "/api/user/v3/users/{user_id}"
    categories: str = "/api/proxy/catalog/v3/categories/tree"
    locations: str = "/api/proxy/location"
    filter_params: str = "/api/catalog/v3/params/filter"
    posting_params: str = "/api/catalog/v32/params/posting"
    draft: str = "/api/catalog/v32/posting-ads/temp"
    draft_save: str = "/api/catalog/v32/posting-ads/temp/{ad_id}"
    draft_publish: str = "/api/catalog/v32/posting-ads/temp/{ad_id}/publish"
    image_upload: str = "/api/upload/swoole-upload/v3/images/upload"
    image_remove: str = "/api/catalog/v3/images/remove-by-ids"
    my_ad: str = "/api/catalog/v3/feed/my-ad-details/{ad_id}"
    ad_edit: str = "/api/catalog/v32/posting-ads/{ad_id}"
    ad_activate: str = "/api/catalog/v32/posting-ads/{ad_id}/activate"
    ad_deactivate: str = "/api/catalog/v3/catalog/feed/{ad_id}/deactivate"
    ad_delete: str = "/api/catalog/v3/catalog/feed/{ad_id}"
    my_ads: str = "/api/search/v3/feed/my/all"
    ad_details: str = "/api/search/v3/feed/details/{ad_id}"
    limits: str = "/api/catalog/v3/feed/limits-info/{country_id}/{user_id}"


class Settings(GoodConf):
    model_config = GoodConfConfigDict(
        env_prefix="LALAFO_",
        file_env_var="LALAFO_CONFIG",
        default_files=["lalafo.toml", "lalafo.yaml", "lalafo.yml", "lalafo.json"],
        extra="ignore",
        env_nested_delimiter="__",
    )

    base_url: str = Field(default="https://lalafo.az", description=text("settings.base_url"))
    country_id: int = Field(default=13, ge=1, description=text("settings.country_id"))
    language: str = Field(default="az_AZ", min_length=2, max_length=10, description=text("settings.language"))
    phone_code: str = Field(default="994", pattern=r"^\d{1,4}$", description=text("settings.phone_code"))
    endpoints: Endpoints = Field(default_factory=Endpoints, description=text("settings.endpoints"))
    timeout: float = Field(default=30.0, gt=0, description=text("settings.timeout"))
    connect_timeout: float = Field(default=10.0, gt=0, description=text("settings.connect_timeout"))
    max_retries: int = Field(default=2, ge=0, le=10, description=text("settings.max_retries"))
    backoff_base: float = Field(default=0.8, ge=0, description=text("settings.backoff_base"))
    backoff_cap: float = Field(default=8.0, ge=0, description=text("settings.backoff_cap"))
    renew_at: float = Field(default=0.75, ge=0.1, le=1.0, description=text("settings.renew_at"))
    user_agent: str = Field(default="lalafo-python-sdk/{version}", description=text("settings.user_agent"))
    allow_insecure_http: bool = Field(default=False, description=text("settings.allow_insecure_http"))

    @field_validator("base_url")
    @classmethod
    def _base_url(cls, value: str) -> str:
        parts = urlsplit(value.strip())
        if parts.scheme not in ("http", "https") or not parts.hostname:
            raise ValueError(text("error.base_url", url=value))
        return value.strip().rstrip("/")

    def check_transport(self) -> None:
        parts = urlsplit(self.base_url)
        if parts.scheme == "https" or self.allow_insecure_http or parts.hostname in LOCAL_HOSTS:
            return
        raise ConfigurationError(text("error.insecure", url=self.base_url))

    def path(self, endpoint: str, **params: Any) -> str:
        template = endpoint if endpoint.startswith("/") else getattr(self.endpoints, endpoint)
        return str(template.format(**{k: quote(str(v), safe="") for k, v in params.items()}))

    def url(self, endpoint: str, query: Optional[Query] = None, **params: Any) -> str:
        address = self.base_url + self.path(endpoint, **params)
        pairs = list(query.items()) if isinstance(query, dict) else list(query or [])
        given = [(k, v) for k, v in pairs if v is not None and v != ""]
        return f"{address}?{urlencode(given, doseq=True)}" if given else address

    def resolved_user_agent(self) -> str:
        return self.user_agent.replace("{version}", __version__)


Settings.__doc__ = text("settings.description")


def load_settings(config_file: Optional[str] = None, **overrides: Any) -> Settings:
    given = {key: value for key, value in overrides.items() if value is not None}
    return Settings(load=True, config_file=config_file, **given)
