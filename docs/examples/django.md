# Django

Ads kept in a Django model, posted by a management command, with the lalafo session in the database so every process shares it and renewals are saved for all.

## Models

```python
from django.db import models


class LalafoSession(models.Model):
    data = models.JSONField()
    updated_at = models.DateTimeField(auto_now=True)


class Flat(models.Model):
    class State(models.TextChoices):
        DRAFT = "draft"
        POSTING = "posting"
        POSTED = "posted"
        UNKNOWN = "unknown"
        INVALID = "invalid"

    form = models.JSONField()
    photos = models.JSONField(default=list)
    state = models.CharField(max_length=10, choices=State.choices, default=State.DRAFT)
    lalafo_id = models.BigIntegerField(null=True, blank=True)
    lalafo_url = models.URLField(blank=True)
    problem = models.TextField(blank=True)
```

`form` holds an `AdForm` as a dict, `photos` file names under `MEDIA_ROOT`.

## The client

```python
from django.conf import settings

from lalafo_sdk import Lalafo, Session

from .models import LalafoSession


def save(session: Session) -> None:
    LalafoSession.objects.update_or_create(pk=1, defaults={"data": session.to_dict()})


def client() -> Lalafo:
    row = LalafoSession.objects.filter(pk=1).first()
    lf = Lalafo(row.data if row else None, on_session=save)
    if lf.session is None:
        lf.login(settings.LALAFO_LOGIN, settings.LALAFO_PASSWORD)
    return lf
```

## The command

```python
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from lalafo_sdk import InvalidRequestError, LalafoError, OutcomeUnknownError, ValidationError

from flats.lalafo import client
from flats.models import Flat


class Command(BaseCommand):
    help = "Post draft flats to lalafo.az"

    def handle(self, *args, **options):
        with client() as lf:
            for flat in Flat.objects.filter(state=Flat.State.DRAFT):
                flat.state = Flat.State.POSTING
                flat.save(update_fields=["state"])
                photos = [Path(settings.MEDIA_ROOT) / name for name in flat.photos]
                try:
                    ad = lf.ads.create(flat.form, photos)
                except (InvalidRequestError, ValidationError) as exc:
                    flat.state, flat.problem = Flat.State.INVALID, str(exc)
                except OutcomeUnknownError as exc:
                    flat.state, flat.problem = Flat.State.UNKNOWN, str(exc)
                except LalafoError as exc:
                    flat.state, flat.problem = Flat.State.DRAFT, str(exc)
                else:
                    flat.state, flat.lalafo_id, flat.lalafo_url = Flat.State.POSTED, ad.id, ad.url or ""
                    flat.problem = ""
                flat.save()
                self.stdout.write(f"{flat.pk}: {flat.state} {flat.lalafo_url or flat.problem}")
```

- `POSTING` is saved first, so a crash in the middle never leads to a second post on the next run.
- `UNKNOWN` rows need a look at the account; set them back to `DRAFT` or to `POSTED` by hand.
- The session row is updated by `save` whenever the SDK signs in or renews, from any process.

Run it from cron or a task queue: posting uploads photos and should not run inside a web request.
