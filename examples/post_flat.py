from __future__ import annotations

import json
import sys
from pathlib import Path

from lalafo_sdk import BAKU, Lalafo, Session

SESSION_FILE = Path("lalafo-session.json")


def save(session: Session) -> None:
    SESSION_FILE.write_text(json.dumps(session.to_dict()))


def main(login: str, password: str, *photos: str) -> None:
    saved = json.loads(SESSION_FILE.read_text()) if SESSION_FILE.exists() else None
    with Lalafo(saved, on_session=save) as lf:
        if lf.session is None:
            lf.login(login, password)
        rooms = next(p for p in lf.catalog.filter_params(4800, BAKU) if p.id == 69)
        ad = lf.ads.create(
            {
                "category_id": 4800,
                "city_id": BAKU,
                "price": 80000,
                "description": "Satılır 2 otaqlı köhnə tikili, təmirli, kupçalı.",
                "params": [{"id": 69, "value_id": rooms.find("2 otaqlı").id}, {"id": 70, "value": "42"}],
            },
            list(photos),
        )
        print(ad.id, ad.status.name, ad.url)


if __name__ == "__main__":
    main(*sys.argv[1:])
