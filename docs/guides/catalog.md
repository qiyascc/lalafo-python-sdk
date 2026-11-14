# Categories, cities and params

An ad on lalafo sits in a category and a city, and carries **params**: the details the category asks for, such as the number of rooms or the area of a flat. This page shows how to find all three.

## The category tree

```python
for root in lf.catalog.categories():
    for path, category in root.walk():
        if category.postable:
            print(category.id, " / ".join(path))
```

`categories()` returns the top level categories as a tuple of {py:class}`~lalafo_sdk.Category`. It is public and needs no session.

| `Category` field or method | Meaning |
| --- | --- |
| `id` | The category id |
| `name` | The name in the `language` setting |
| `parent_id` | The id of the parent category |
| `url` | The category path on lalafo |
| `postable` | `True` for an active category with a params form. Ads go into postable categories |
| `children` | The sub categories |
| `walk()` | Yields `(path, category)` for the category and everything under it; `path` is the tuple of names from the root |
| `find(category_id)` | The category with that id inside this one, or `None` |
| `leaves()` | Every postable category inside this one |

`catalog.category(category_id)` reads the whole tree and returns the category with that id, or `None`.

### Real estate

`catalog.real_estate()` is `catalog.category(REAL_ESTATE_ROOT)`, the real estate branch (`2029`):

```python
estate = lf.catalog.real_estate()
for category in estate.leaves():
    print(category.id, category.name)
```

Known real estate ids on lalafo.az:

| Id | Category |
| --- | --- |
| 4800 | Apartments for sale, old building |
| 4793 | Apartments for sale, new building |
| 2044 | Apartments, long term rent |
| 2045 | Apartments, daily rent |
| 2031 | Houses for sale |
| 2033 | Houses for rent |
| 2038 | Land for sale |
| 2039 | Land for rent |
| 5952, 5953 | Country houses |
| 2050, 2052, 2053 | Rooms |
| 5304, 5305 | Garages |
| 2065 to 2072 | Commercial property for rent |

## Cities

```python
for city in lf.catalog.cities():
    print(city.id, city.name, city.region)
```

Each {py:class}`~lalafo_sdk.City` has `id`, `name`, `alias`, `region` and `raw`. Baku is available as the constant `BAKU` (`103261`).

## Params

Params come in two lists.

`catalog.filter_params(category_id, city_id=None)` is the public list lalafo uses for search filters. It needs no session.

`catalog.posting_params(category_id, city_id)` is the exact list the post form uses for that category and city. It needs a session, and it is what `ads.create` checks against.

```python
for param in lf.catalog.posting_params(4800, BAKU):
    print(param.id, param.name, param.kind, param.required, param.multi)
    for value in param.values:
        print("    ", value.id, value.value)
```

A {py:class}`~lalafo_sdk.Param`:

| Field or method | Meaning |
| --- | --- |
| `id` | The param id |
| `name` | The label on the form |
| `kind` | `ParamKind.DROPDOWN`, `ParamKind.INPUT` or `ParamKind.OTHER` |
| `required` | The form needs it |
| `multi` | More than one value may be chosen |
| `values` | For dropdowns, the choices as `ParamValue(id, value)` |
| `value(value_id)` | The `ParamValue` with that id, or `None` |
| `find(label)` | The `ParamValue` with that label, ignoring case and surrounding spaces, or `None` |

## Filling in params

The `params` list of a form has one entry per value:

| Kind | Entry |
| --- | --- |
| Dropdown | `{"id": 69, "value_id": 1234}` |
| Input | `{"id": 70, "value": "42"}` |
| Multi select | One entry per chosen value: `{"id": 1239, "value_id": 28272}, {"id": 1239, "value_id": 27535}` |

Each entry has exactly one of `value_id` and `value`; giving both or neither is an error. Input values are text, up to 200 characters.

Looking values up by label keeps the code readable:

```python
params = lf.catalog.posting_params(4800, BAKU)
by_id = {p.id: p for p in params}

form_params = [
    {"id": 69, "value_id": by_id[69].find("2 otaqlı").id},
    {"id": 70, "value": "42"},
]
```

The labels come in the `language` setting (`az_AZ` by default). Print them once to see the exact spelling.

## Cache

The tree and the params change rarely. Load them once per run, or keep them in a file, rather than for every ad. `ads.create` loads the posting params itself every time, so its checks always use lalafo's current form.
