from __future__ import annotations

import pytest

from lalafo_sdk import ConfigurationError, InvalidRequestError, Lalafo, load_settings, messages, phone


def test_env_settings(monkeypatch):
    monkeypatch.setenv("LALAFO_COUNTRY_ID", "12")
    monkeypatch.setenv("LALAFO_LANGUAGE", "ru_RU")
    monkeypatch.setenv("LALAFO_ENDPOINTS__LOGIN", "/api/v9/login")
    client = Lalafo()
    assert client.settings.country_id == 12 and client.settings.language == "ru_RU"
    assert client.settings.url("login") == "https://lalafo.az/api/v9/login"


def test_plain_http_is_refused_outside_localhost():
    with pytest.raises(ConfigurationError):
        Lalafo(base_url="http://lalafo.example")
    Lalafo(base_url="http://localhost:8000")
    Lalafo(base_url="http://lalafo.example", allow_insecure_http=True)


def test_settings_override_on_an_existing_settings_object():
    base = load_settings()
    client = Lalafo(settings=base, language="ru_RU")
    assert client.settings.language == "ru_RU" and base.language == "az_AZ"


@pytest.mark.parametrize("raw,expected", [
    ("050 123 45 67", "+994501234567"), ("+994 50 123 45 67", "+994501234567"), ("994501234567", "+994501234567"),
    ("501234567", "+994501234567"), ("00994501234567", "+994501234567"),
])
def test_phone_numbers(raw, expected):
    assert phone(raw, "994") == expected


@pytest.mark.parametrize("raw", ["12", "+99450123", "phone"])
def test_bad_phone_numbers(raw):
    with pytest.raises(InvalidRequestError):
        phone(raw, "994")


def test_messages_can_be_replaced():
    try:
        messages.use({"error": {"no_session": "Log in please"}})
        assert messages.text("error.no_session") == "Log in please"
        with pytest.raises(KeyError):
            messages.use({"error": {"made_up": "x"}})
    finally:
        messages.reset()
