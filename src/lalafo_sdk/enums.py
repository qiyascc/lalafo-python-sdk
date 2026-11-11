from __future__ import annotations

from enum import Enum, IntEnum

REAL_ESTATE_ROOT = 2029
BAKU = 103261
AZERBAIJAN = 13


class AdStatus(IntEnum):
    MODERATION = 1
    ACTIVE = 2
    REJECTED = 3
    BANNED = 4
    DRAFT = 7
    DEACTIVATED = 8
    PAYMENT_WAITING = 11
    UNKNOWN = 0

    @classmethod
    def parse(cls, value: object) -> AdStatus:
        if not isinstance(value, (int, str)) or isinstance(value, bool):
            return cls.UNKNOWN
        try:
            return cls(int(value))
        except ValueError:
            return cls.UNKNOWN

    @property
    def final(self) -> bool:
        return self not in (AdStatus.MODERATION, AdStatus.DRAFT, AdStatus.UNKNOWN)


class Currency(str, Enum):
    AZN = "AZN"
    USD = "USD"

    def __str__(self) -> str:
        return self.value


class ParamKind(str, Enum):
    DROPDOWN = "dropdown"
    INPUT = "input"
    OTHER = "other"

    @classmethod
    def parse(cls, value: object) -> ParamKind:
        try:
            return cls(str(value))
        except ValueError:
            return cls.OTHER

    def __str__(self) -> str:
        return self.value


TABS: dict[str, tuple[AdStatus, ...]] = {
    "active": (AdStatus.ACTIVE, AdStatus.PAYMENT_WAITING),
    "moderation": (AdStatus.MODERATION,),
    "rejected": (AdStatus.REJECTED, AdStatus.BANNED),
    "deactivated": (AdStatus.DEACTIVATED,),
    "payment_waiting": (AdStatus.PAYMENT_WAITING,),
}
