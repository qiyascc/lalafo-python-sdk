from __future__ import annotations

import pytest

from lalafo_sdk import AdForm, AdStatus, InvalidRequestError, WaitTimeoutError

from .conftest import FORM, PARAMS, PHOTO, ad


def _create_replies(gw, status=1, leftover=True):
    gw.reply(PARAMS)
    gw.reply({"id": 4242, "images": [{"id": 11}] if leftover else [], "mobile": "+994501234567"})
    if leftover:
        gw.reply({"success": True})
    gw.reply({"id": 901, "links": {"thumbnail": "t1", "original": "o1"}})
    gw.reply({"id": 902, "links": {"thumbnail": "t2", "original": "o2"}})
    gw.reply({"id": 4242})
    gw.reply(ad(status=status))


def test_create_runs_every_step_in_order(gw, signed):
    _create_replies(gw)
    result = signed.ads.create(FORM, [PHOTO, ("flat.png", PHOTO, "image/png")])
    assert gw.paths == [
        "/api/catalog/v32/params/posting",
        "/api/catalog/v32/posting-ads/temp",
        "/api/catalog/v3/images/remove-by-ids",
        "/api/upload/swoole-upload/v3/images/upload",
        "/api/upload/swoole-upload/v3/images/upload",
        "/api/catalog/v32/posting-ads/temp/4242",
        "/api/catalog/v32/posting-ads/temp/4242/publish",
    ]
    assert gw.methods == ["POST", "POST", "DELETE", "POST", "POST", "PUT", "POST"]
    assert gw.body(0) == {"category_id": 4800, "city_id": 103261}
    assert gw.query(2) == [("ids[]", "11")] and gw.query(6) == [("expand", "available_campaign_types")]
    upload = gw.requests[3]
    assert b'name="ad_id"' in upload.content and b"4242" in upload.content and b'name="image_file"' in upload.content
    assert upload.headers["x-cache-bypass"] == "yes"
    body = gw.body(5)
    assert body["title"] == "" and body["id"] == 4242 and body["image_order"] == [901, 902]
    assert body["price"] == 80000 and body["currency"] == "AZN" and body["is_negotiable"] is False
    assert body["params"] == [
        {"id": 69, "name": "Otaqların sayı", "value": "2 otaqlı", "value_id": 2774},
        {"id": 70, "name": "Sahə (m2)", "value": "42"},
        {"id": 1239, "name": "Mənzilin şəraiti", "value": "Kombi", "value_id": 28272},
        {"id": 1239, "name": "Mənzilin şəraiti", "value": "Kredit", "value_id": 27535},
    ]
    assert result.id == 4242 and result.status is AdStatus.MODERATION
    assert result.url == "https://lalafo.az/baku/ads/baki-2-otaqli-id-4242"


def test_no_price_means_negotiable(gw, signed):
    _create_replies(gw, leftover=False)
    signed.ads.create({**FORM, "price": None, "mobile": "055 123 45 67"}, [PHOTO, PHOTO])
    body = gw.body(4)
    assert body["price"] is None and body["currency"] is None and body["is_negotiable"] is True
    assert body["mobile"] == "+994551234567"


def test_over_the_free_limit_waits_for_payment(gw, signed):
    _create_replies(gw, status=11)
    result = signed.ads.create(FORM, [PHOTO, PHOTO])
    assert result.awaiting_payment


@pytest.mark.parametrize("params,error", [
    ([{"id": 70, "value": "42"}], "is required"),
    ([{"id": 69, "value_id": 1}], "has no value_id 1"),
    ([{"id": 69, "value_id": 2774}, {"id": 69, "value_id": 2775}], "takes one value"),
    ([{"id": 69, "value_id": 2774}, {"id": 5, "value": "x"}], "does not exist"),
])
def test_params_are_checked_before_a_draft_is_made(gw, signed, params, error):
    gw.reply(PARAMS)
    with pytest.raises(InvalidRequestError) as info:
        signed.ads.create({**FORM, "params": params}, [PHOTO])
    assert error in info.value.message and gw.paths == ["/api/catalog/v32/params/posting"]


@pytest.mark.parametrize("images", [[], [b"tiny"], [object()], [PHOTO] * 21])
def test_bad_photos_are_refused_before_sending(gw, signed, images):
    with pytest.raises(InvalidRequestError):
        signed.ads.create(FORM, images)
    assert gw.requests == []


def test_bad_form_is_refused_before_sending(gw, signed):
    with pytest.raises(InvalidRequestError):
        signed.ads.create({**FORM, "params": [{"id": 69}]}, [PHOTO])
    with pytest.raises(InvalidRequestError):
        signed.ads.create({**FORM, "mobile": "12"}, [PHOTO])
    assert gw.requests == []


def test_the_steps_work_on_their_own(gw, signed):
    gw.reply({"id": 55, "images": []}).reply({"id": 901, "links": {"thumbnail": "t"}})
    gw.reply({"id": 55}).reply(ad(55))
    draft = signed.ads.draft()
    image = signed.ads.upload_photo(draft.id, PHOTO)
    signed.ads.save_draft(draft.id, AdForm(**FORM), [image.id], params=[])
    assert signed.ads.publish(draft.id).id == 55
    assert gw.paths[-2:] == ["/api/catalog/v32/posting-ads/temp/55", "/api/catalog/v32/posting-ads/temp/55/publish"]


def test_edit_keeps_old_photos_and_adds_new_ones(gw, signed):
    gw.reply(ad(status=2, type=None)).reply(PARAMS).reply({"id": 950}).reply(ad(status=1))
    result = signed.ads.edit(4242, {**FORM, "price": 75000}, [PHOTO])
    assert gw.paths == ["/api/catalog/v3/feed/my-ad-details/4242", "/api/catalog/v32/params/posting",
                        "/api/upload/swoole-upload/v3/images/upload", "/api/catalog/v32/posting-ads/4242"]
    assert gw.body(1) == {"category_id": 4800, "city_id": 103261, "id": 4242, "type": None}
    assert gw.body(3)["image_order"] == [901, 950] and gw.body(3)["price"] == 75000 and "title" not in gw.body(3)
    assert result.status is AdStatus.MODERATION


def test_edit_can_replace_the_photos(gw, signed):
    gw.reply(ad(status=2)).reply(PARAMS).reply({"id": 950}).reply(ad()).reply({"success": True})
    signed.ads.edit(4242, FORM, [PHOTO], keep_photos=False)
    assert gw.body(3)["image_order"] == [950]
    assert gw.methods[-1] == "DELETE" and gw.query() == [("ids[]", "901")]


def test_manage_calls_use_the_website_paths(gw, signed):
    for _ in range(3):
        gw.reply(None)
    signed.ads.deactivate(4242)
    signed.ads.activate("4242")
    signed.ads.delete(4242)
    assert list(zip(gw.methods, gw.paths, strict=True)) == [
        ("PUT", "/api/catalog/v3/catalog/feed/4242/deactivate"),
        ("POST", "/api/catalog/v32/posting-ads/4242/activate"),
        ("DELETE", "/api/catalog/v3/catalog/feed/4242"),
    ]


def test_list_by_status_and_every_page(gw, signed):
    gw.reply({"items": [ad(1, 2)], "_meta": {"currentPage": 1, "pageCount": 2, "totalCount": 2}})
    page = signed.ads.list("active", per_page=1)
    assert gw.query() == [("expand", "url"), ("page", "1"), ("per-page", "1"), ("status_id[]", "2"),
                          ("status_id[]", "11")]
    assert page.has_more and page.total == 2 and page.items[0].status is AdStatus.ACTIVE
    gw.reply({"items": [ad(1, 8)], "_meta": {"currentPage": 1, "pageCount": 2}})
    gw.reply({"items": [ad(2, 8)], "_meta": {"currentPage": 2, "pageCount": 2}})
    every = signed.ads.all("deactivated")
    assert [a.id for a in every] == [1, 2] and ("status_id[]", "8") in gw.query()
    with pytest.raises(InvalidRequestError):
        signed.ads.list("sold")


def test_get_details_and_limits(gw, signed):
    gw.reply(ad(status=3, rejected_reason="Photo")).reply(ad(status=2)).reply({"free": 3})
    mine = signed.ads.get(4242)
    public = signed.ads.details(4242)
    limits = signed.ads.limits()
    assert mine.rejected_reason == "Photo" and gw.header("x-cache-bypass", 0) == "yes"
    assert gw.header("authorization", 1) == "" and gw.query(1) == [("expand", "url")]
    assert gw.paths[2] == "/api/catalog/v3/feed/limits-info/13/77" and limits.raw == {"free": 3}
    assert public.images[0].thumbnail == "https://img5.lalafo.com/t.jpg" and public.created_at is not None


def test_wait_returns_once_moderation_ends(gw, signed):
    gw.reply(ad(status=1)).reply(ad(status=2))
    assert signed.ads.wait(4242, timeout=60, interval=0).status is AdStatus.ACTIVE
    gw.reply(ad(status=1))
    with pytest.raises(WaitTimeoutError):
        signed.ads.wait(4242, timeout=0, interval=1)
