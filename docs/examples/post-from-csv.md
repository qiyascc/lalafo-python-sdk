# Post from CSV

An agency keeps its flats in a spreadsheet. Each row becomes one ad; the photos of a row are in a folder named after its `ref` column.

`flats.csv`:

```text
ref,category_id,price,rooms,area,description
yasamal-12,4800,80000,2 otaqlı,42,"Satılır 2 otaqlı köhnə tikili, təmirli."
nasimi-7,4793,145000,3 otaqlı,96,"Yeni tikili, 3 otaq, metroya yaxın."
```

```text
photos/
    yasamal-12/
        1.jpg
        2.jpg
    nasimi-7/
        1.jpg
```

The script:

```python
import csv
import json
import sys
from pathlib import Path

from lalafo_sdk import BAKU, InvalidRequestError, LalafoError, OutcomeUnknownError, ValidationError

ROOMS, AREA = 69, 70
DONE = Path("posted.json")


def build_form(lf, row):
    params = {p.id: p for p in lf.catalog.posting_params(int(row["category_id"]), BAKU)}
    rooms = params[ROOMS].find(row["rooms"])
    if rooms is None:
        raise InvalidRequestError(f"no rooms value {row['rooms']!r}")
    return {
        "category_id": int(row["category_id"]),
        "city_id": BAKU,
        "price": int(row["price"]),
        "description": row["description"],
        "params": [{"id": ROOMS, "value_id": rooms.id}, {"id": AREA, "value": row["area"]}],
    }


def main(path: str) -> None:
    from session_file import signed_in_client

    done = json.loads(DONE.read_text()) if DONE.exists() else {}
    with signed_in_client() as lf, open(path, encoding="utf-8") as source:
        for row in csv.DictReader(source):
            ref = row["ref"]
            if ref in done:
                continue
            photos = sorted(Path("photos", ref).glob("*.jpg"))
            try:
                ad = lf.ads.create(build_form(lf, row), photos)
            except (InvalidRequestError, ValidationError) as exc:
                print(f"{ref}: {exc}")
                continue
            except OutcomeUnknownError:
                done[ref] = {"state": "unknown"}
                print(f"{ref}: no answer, check the moderation tab")
            except LalafoError as exc:
                print(f"{ref}: will retry next run: {exc}")
                continue
            else:
                done[ref] = {"id": ad.id, "url": ad.url, "status": ad.status.name}
                print(f"{ref}: {ad.id} {ad.status.name} {ad.url}")
            DONE.write_text(json.dumps(done, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "flats.csv")
```

- `posted.json` records every row that was posted, or whose outcome is unknown, so a rerun skips them.
- Unknown outcomes are not retried automatically. Check the moderation tab and remove the entry from `posted.json` to post the row again.
- Rows with bad data are skipped with a message and tried again next run.
- The rooms label is looked up in the post form of the row's category, since new and old buildings may use different lists. The param ids `69` and `70` are the ones from the README example; check yours with the [real estate sheet](real-estate.md).
