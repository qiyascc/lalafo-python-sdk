from __future__ import annotations

import httpx
import pytest

from lalafo_sdk import (
    BlockedError,
    ForbiddenError,
    NotFoundError,
    NotSentError,
    OutcomeUnknownError,
    RateLimitError,
    ServerError,
    TransportError,
)

from .conftest import FORM, PARAMS, PHOTO, ad, fresh_token


def test_publish_is_never_resent_after_a_timeout(gw, signed):
    gw.fail(httpx.ReadTimeout("slow"))
    with pytest.raises(OutcomeUnknownError) as info:
        signed.ads.publish(4242)
    assert len(gw.requests) == 1 and "Check the account" in info.value.message


@pytest.mark.parametrize("exc", [httpx.RemoteProtocolError("cut"), httpx.ReadError("reset"), httpx.WriteTimeout("w")])
def test_any_ambiguous_failure_on_a_write_is_unknown(gw, signed, exc):
    gw.fail(exc)
    with pytest.raises(OutcomeUnknownError):
        signed.ads.delete(4242)
    assert len(gw.requests) == 1


def test_login_is_not_resent_after_a_timeout(gw, lf):
    gw.fail(httpx.ReadTimeout("slow"))
    with pytest.raises(OutcomeUnknownError):
        lf.login("0501234567", "secret")
    assert len(gw.requests) == 1


def test_server_error_on_a_write_is_unknown_and_not_retried(gw, signed):
    gw.reply({"message": "boom"}, status=502)
    with pytest.raises(OutcomeUnknownError) as info:
        signed.ads.deactivate(4242)
    assert info.value.status_code == 502 and len(gw.requests) == 1


def test_a_create_that_fails_while_publishing_stops_there(gw, signed):
    gw.reply(PARAMS).reply({"id": 4242, "images": []}).reply({"id": 901}).reply({"id": 4242})
    gw.reply({"message": "boom"}, status=500)
    with pytest.raises(OutcomeUnknownError):
        signed.ads.create(FORM, [PHOTO])
    assert len(gw.requests) == 5


def test_garbage_success_body_on_a_write_is_unknown(gw, signed):
    gw.reply(b"<html>ok</html>")
    with pytest.raises(OutcomeUnknownError):
        signed.ads.publish(4242)


def test_connection_refused_is_retried_because_nothing_was_sent(gw, signed):
    gw.fail(httpx.ConnectError("refused")).reply(ad())
    assert signed.ads.publish(4242).id == 4242
    assert len(gw.requests) == 2


def test_connection_refused_every_time_is_not_sent(gw, signed):
    for _ in range(3):
        gw.fail(httpx.ConnectError("refused"))
    with pytest.raises(NotSentError):
        signed.ads.publish(4242)
    assert len(gw.requests) == 3


def test_reads_retry_timeouts_and_server_errors(gw, signed):
    gw.fail(httpx.ReadTimeout("slow")).reply({"message": "x"}, status=503).reply(ad())
    assert signed.ads.get(4242).id == 4242 and len(gw.requests) == 3


def test_reads_give_up_after_the_retries(gw, signed):
    for _ in range(3):
        gw.fail(httpx.ReadTimeout("slow"))
    with pytest.raises(TransportError):
        signed.ads.get(4242)


def test_a_cloudflare_check_page_is_retried_even_on_a_write(gw, signed):
    gw.challenge().reply(ad())
    assert signed.ads.publish(4242).id == 4242 and len(gw.requests) == 2


def test_a_cloudflare_check_page_every_time_is_blocked(gw, signed):
    for _ in range(3):
        gw.challenge()
    with pytest.raises(BlockedError) as info:
        signed.ads.list()
    assert "Nothing was processed" in info.value.message and len(gw.requests) == 3


def test_429_waits_and_retries(gw, signed):
    gw.reply({"message": "slow down"}, status=429, headers={"retry-after": "0"}).reply(ad())
    assert signed.ads.get(4242).id == 4242


def test_429_every_time_raises(gw, signed):
    for _ in range(3):
        gw.reply({"message": "slow down"}, status=429, headers={"retry-after": "1"})
    with pytest.raises(RateLimitError) as info:
        signed.ads.get(4242)
    assert info.value.retry_after == 1


@pytest.mark.parametrize("status,kind", [(403, ForbiddenError), (404, NotFoundError)])
def test_statuses_map_to_errors(gw, signed, status, kind):
    gw.reply({"message": "nope"}, status=status)
    with pytest.raises(kind) as info:
        signed.ads.get(4242)
    assert info.value.status_code == status and info.value.message == "nope"


def test_server_error_on_a_read_after_retries(gw, signed):
    for _ in range(3):
        gw.reply({"message": "down"}, status=500)
    with pytest.raises(ServerError):
        signed.ads.get(4242)


def test_no_device_fingerprint_and_no_app_identity(gw, signed):
    gw.reply(ad())
    signed.ads.publish(4242)
    headers = gw.requests[-1].headers
    assert "device-fingerprint" not in headers and headers["device"] == "pc"
    assert headers["authorization"] == f"Bearer {signed.session.token}" and fresh_token()
