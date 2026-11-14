# Real estate categories

Prints every postable real estate category on lalafo.az with the params of its post form, as a reference sheet for writing forms.

```python
import sys

from lalafo_sdk import BAKU, ParamKind


def main(city_id: int) -> None:
    from session_file import signed_in_client

    with signed_in_client() as lf:
        estate = lf.catalog.real_estate()
        for path, category in estate.walk():
            if not category.postable:
                continue
            print(f"\n{category.id}  {' / '.join(path)}")
            for param in lf.catalog.posting_params(category.id, city_id):
                flags = " ".join(f for f, on in (("required", param.required), ("multi", param.multi)) if on)
                print(f"    {param.id:>6}  {param.name}  [{param.kind}] {flags}")
                if param.kind == ParamKind.DROPDOWN:
                    shown = ", ".join(f"{v.id}={v.value}" for v in param.values[:10])
                    more = f" and {len(param.values) - 10} more" if len(param.values) > 10 else ""
                    print(f"            {shown}{more}")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else BAKU)
```

`posting_params` needs a session, so the script uses the [session file](session-file.md). For a quick look without signing in, use `lf.catalog.filter_params(category.id, city_id)` instead; it is the public filter list, close to but not always the same as the post form.

Known ids, for reference:

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
