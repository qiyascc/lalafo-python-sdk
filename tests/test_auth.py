from __future__ import annotations

import httpx
import pytest

from lalafo_sdk import (
    AuthenticationError,
    CaptchaRequiredError,
    InvalidRequestError,
    Lalafo,
    Session,
    SessionRequiredError,
    ValidationError,
    __version__,
)

from .conftest import _quiet, fresh_token, old_token, session


def test_login_by_phone_stores_the_session_and_calls_the_hook(gw, lf, saved):
    token = fresh_token()
    gw.reply({"token": token, "refresh_token": "rf1", "user_hash": "uh-site", "id": 77})
    result = lf.login("050 123 45 67", "secret")
    assert gw.paths == ["/api/auth/login"] and gw.body() == {"mobile": "+994501234567", "password": "secret"}
    assert result == Session(token, "rf1", "uh-site", "77") and lf.session == result and saved == [result]
    assert lf.user_hash == "uh-site"


def test_login_sends_the_website_headers_and_nothing_else(gw, lf):
    gw.reply({"token": fresh_token(), "refresh_token": "rf1", "id": 77})
    lf.login("a@b.az", "secret")
    assert gw.body() == {"email": "a@b.az", "password": "secret"}
    assert gw.header("device") == "pc" and gw.header("country-id") == "13" and gw.header("language") == "az_AZ"
    assert gw.header("request-id").startswith("react-client-") and len(gw.header("user-hash")) == 36
    assert gw.header("x-cache-bypass") == "yes" and gw.header("authorization") == ""
    assert gw.header("user-agent") == f"lalafo-python-sdk/{__version__}"
    assert not gw.has_header("device-fingerprint")


def test_every_request_gets_a_new_request_id(gw, signed):
    gw.reply({"id": 77}).reply({"id": 77})
    signed.auth.me()
    signed.auth.me()
    assert gw.header("request-id", 0) != gw.header("request-id", 1)
    assert gw.header("authorization").startswith("Bearer ") and gw.header("user-hash") == "uh-1"


def test_wrong_password_is_a_validation_error_with_fields(gw, lf):
    gw.reply([{"field": "password", "message": "Incorrect password"}], status=422)
    with pytest.raises(ValidationError) as info:
        lf.login("+994501234567", "wrong-1")
    assert info.value.fields == {"password": "Incorrect password"} and lf.session is None


def test_captcha_demand_is_its_own_error(gw, lf):
    gw.reply([{"field": "captcha", "message": "Captcha required"}], status=422)
    with pytest.raises(CaptchaRequiredError) as info:
        lf.login("0501234567", "secret")
    assert "browser" in info.value.message


@pytest.mark.parametrize("login,password", [("", "secret"), ("0501234567", "1234"), ("12", "secret")])
def test_bad_login_input_is_refused_before_sending(gw, lf, login, password):
    with pytest.raises(InvalidRequestError):
        lf.login(login, password)
    assert gw.requests == []


def test_calls_that_need_a_session_say_so(gw, lf):
    with pytest.raises(SessionRequiredError):
        lf.ads.list()
    assert gw.requests == []


def test_session_renews_at_three_quarters_of_its_lifetime(gw, saved):
    client = _quiet(Lalafo(session(old_token()), on_session=saved.append,
                           http_client=httpx.Client(transport=httpx.MockTransport(gw))))
    new = fresh_token()
    gw.reply({"token": new}).reply({"id": 77, "username": "Qiyas"})
    user = client.auth.me()
    assert gw.paths == ["/api/auth/renew-session", "/api/user/v3/users/77"]
    assert gw.body(0) == {"refresh_token": "rf1"} and gw.header("authorization", 1) == f"Bearer {new}"
    assert saved[-1].token == new and saved[-1].refresh_token == "rf1" and user.username == "Qiyas"


def test_a_401_renews_once_and_repeats_the_call(gw, signed, saved):
    new = fresh_token()
    gw.reply({"message": "Unauthorized"}, status=401).reply({"token": new, "refresh_token": "rf2"})
    gw.reply({"items": [], "_meta": {"pageCount": 1, "totalCount": 0}})
    signed.ads.list()
    assert gw.paths == ["/api/search/v3/feed/my/all", "/api/auth/renew-session", "/api/search/v3/feed/my/all"]
    assert saved[-1].refresh_token == "rf2"


def test_a_refused_renewal_means_sign_in_again(gw, signed):
    gw.reply({"message": "Unauthorized"}, status=401).reply({"message": "expired"}, status=401)
    with pytest.raises(AuthenticationError) as info:
        signed.ads.list()
    assert "Sign in again" in info.value.message and len(gw.requests) == 2


def test_a_session_round_trips_through_a_dict(gw):
    s = session()
    again = Session.from_mapping(s.to_dict())
    assert again == s and "token" not in repr(s)
    client = Lalafo(s.to_dict())
    assert client.session == s and client.user_hash == "uh-1"


def test_logout_forgets_the_session(gw, signed):
    gw.reply({"success": True})
    signed.auth.logout()
    assert signed.session is None and gw.paths == ["/api/auth/logout"]
