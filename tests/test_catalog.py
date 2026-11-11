from __future__ import annotations

from lalafo_sdk import BAKU, REAL_ESTATE_ROOT, ParamKind

TREE = [
    {"id": 1317, "parent_id": 1, "name": "Elektronika", "panel_type": "category", "children": []},
    {"id": 2029, "parent_id": 1, "name": "Daşınmaz əmlak", "panel_type": "category", "children": [
        {"id": 2040, "parent_id": 2029, "name": "Mənzillər", "panel_type": "category", "children": [
            {"id": 4800, "parent_id": 2040, "name": "Köhnə tikili", "panel_type": "params", "active": True,
             "children": []},
            {"id": 4793, "parent_id": 2040, "name": "Yeni tikili", "panel_type": "params", "children": []},
        ]},
        {"id": 9999, "parent_id": 2029, "name": "Old", "panel_type": "params", "active": False, "children": []},
    ]},
]


def test_categories_and_the_real_estate_branch(gw, lf):
    gw.reply(TREE).reply(TREE)
    roots = lf.catalog.categories()
    assert [r.id for r in roots] == [1317, 2029] and gw.header("authorization") == ""
    estate = lf.catalog.real_estate()
    assert estate.id == REAL_ESTATE_ROOT and [c.id for c in estate.leaves()] == [4800, 4793]
    paths = {c.id: " / ".join(p) for p, c in estate.walk()}
    assert paths[4800] == "Daşınmaz əmlak / Mənzillər / Köhnə tikili"


def test_cities(gw, lf):
    gw.reply([{"id": BAKU, "name": "Bakı", "alias": "baku", "region": {"id": 224, "name": "Bakı"}}])
    city = lf.catalog.cities()[0]
    assert (city.id, city.name, city.alias, city.region) == (BAKU, "Bakı", "baku", "Bakı")


def test_filter_params_skip_location_and_price_blocks(gw, lf):
    gw.reply([{"name": "Yerləşmə", "kind": "location"}, {"name": "Qiymət", "kind": "price"},
              {"id": 69, "name": "Otaqların sayı", "kind": "dropdown", "is_required": True,
               "is_multi_select_posting": False, "values": [{"id": 2774, "value": "2 otaqlı"}]},
              {"id": 70, "name": "Sahə (m2)", "kind": "input", "type": "integer"}])
    params = lf.catalog.filter_params(4800, BAKU)
    assert gw.query() == [("category_id", "4800"), ("city_id", str(BAKU))]
    rooms, area = params
    assert rooms.required and rooms.kind is ParamKind.DROPDOWN and rooms.find(" 2 Otaqlı ").id == 2774
    assert area.kind is ParamKind.INPUT and not area.values


def test_posting_params_need_a_session_and_post(gw, signed):
    gw.reply({"items": [{"id": 69, "name": "Rooms", "kind": "dropdown", "values": []}]})
    params = signed.catalog.posting_params(4800, BAKU)
    assert gw.methods == ["POST"] and gw.body() == {"category_id": 4800, "city_id": BAKU} and params[0].id == 69
