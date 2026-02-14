from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Doctor:
    name: str
    can_day: bool
    can_visit: bool
    can_full_service: bool
    fte: float = 1.0
    max_weekends_per_month: int | None = None


DOCTORS: list[Doctor] = [
    Doctor("Bauregger", can_day=True, can_visit=True, can_full_service=False),
    Doctor("Devasurendra", can_day=True, can_visit=True, can_full_service=False),
    Doctor("Langen", can_day=True, can_visit=True, can_full_service=False),
    Doctor("Flanter", can_day=True, can_visit=True, can_full_service=False),
    Doctor("Gumbiller", can_day=True, can_visit=True, can_full_service=True),
    Doctor("Frey", can_day=True, can_visit=True, can_full_service=True),
    Doctor("Koch", can_day=True, can_visit=True, can_full_service=True, fte=0.5),
    Doctor("Mettin", can_day=True, can_visit=True, can_full_service=True, fte=0.5),
    Doctor("Umland", can_day=True, can_visit=True, can_full_service=True),
    Doctor("Zumbusch", can_day=True, can_visit=True, can_full_service=True),
    Doctor("Horner", can_day=True, can_visit=True, can_full_service=True),
    Doctor(
        "Fecher",
        can_day=True,
        can_visit=True,
        can_full_service=True,
        max_weekends_per_month=1,
    ),
]

DOCTOR_BY_NAME = {doctor.name: doctor for doctor in DOCTORS}
