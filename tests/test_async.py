from __future__ import annotations

import httpx
import pytest

from lalafo_sdk import AdStatus, OutcomeUnknownError

from .conftest import FORM, PARAMS, PHOTO, ad, fresh_token


async def test_async_login_and_create(gw, alf, saved):
    gw.reply({"token": fresh_token(), "refresh_token": "rf1", "id": 77})
    gw.reply(PARAMS).reply({"id": 4242, "images": []}).reply({"id": 901}).reply({"id": 4242}).reply(ad())
    await alf.login("050 123 45 67", "secret")
    result = await alf.ads.create(FORM, [PHOTO])
    assert result.status is AdStatus.MODERATION and saved[0].user_id == "77"
    assert gw.header("authorization").startswith("Bearer ")


async def test_async_write_timeout_is_unknown(gw, alf):
    gw.reply({"token": fresh_token(), "refresh_token": "rf1", "id": 77}).fail(httpx.ReadTimeout("slow"))
    await alf.login("a@b.az", "secret")
    with pytest.raises(OutcomeUnknownError):
        await alf.ads.delete(4242)
    assert len(gw.requests) == 2


async def test_async_context_manager_closes():
    from lalafo_sdk import AsyncLalafo

    async with AsyncLalafo() as client:
        assert client.session is None
