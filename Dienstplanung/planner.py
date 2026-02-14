from __future__ import annotations

import calendar
from collections import defaultdict
from datetime import date, timedelta

import pandas as pd

from models import DOCTOR_BY_NAME, DOCTORS


def parse_absences(raw: str) -> tuple[dict[date, set[str]], list[str]]:
    absences: dict[date, set[str]] = defaultdict(set)
    warnings: list[str] = []
    lines = [line.strip() for line in raw.splitlines() if line.strip()]

    for idx, line in enumerate(lines, start=1):
        if ":" not in line:
            warnings.append(f"Zeile {idx}: ':' fehlt.")
            continue

        date_part, names_part = line.split(":", 1)
        try:
            day = date.fromisoformat(date_part.strip())
        except ValueError:
            warnings.append(f"Zeile {idx}: Ungueltiges Datum '{date_part.strip()}'.")
            continue

        names = {n.strip() for n in names_part.split(",") if n.strip()}
        unknown = sorted([name for name in names if name not in DOCTOR_BY_NAME])
        if unknown:
            warnings.append(f"Zeile {idx}: Unbekannte Namen: {', '.join(unknown)}.")

        absences[day].update({name for name in names if name in DOCTOR_BY_NAME})
    return absences, warnings


def month_dates(year: int, month: int) -> list[date]:
    _, last_day = calendar.monthrange(year, month)
    return [date(year, month, d) for d in range(1, last_day + 1)]


def _pick_fair(candidates: list[str], duty_count: dict[str, int], fte: dict[str, float]) -> str | None:
    if not candidates:
        return None
    return min(candidates, key=lambda name: (duty_count[name] / fte[name], duty_count[name], name))


def _pick_fair_weekend(
    candidates: list[str],
    weekend_count: dict[str, int],
    duty_count: dict[str, int],
    fte: dict[str, float],
) -> str | None:
    if not candidates:
        return None
    return min(
        candidates,
        key=lambda name: (
            weekend_count[name] / fte[name],
            duty_count[name] / fte[name],
            name,
        ),
    )


def generate_plan(
    year: int,
    month: int,
    absences: dict[date, set[str]],
    max_parallel_absent: int,
    friday_night_rest_days: int = 3,
) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    days = month_dates(year, month)
    fte = {d.name: d.fte for d in DOCTORS}
    duty_count: dict[str, int] = defaultdict(int)
    weekend_count: dict[str, int] = defaultdict(int)
    off_days: dict[date, set[str]] = defaultdict(set)
    assigned: dict[date, dict[str, list[str] | str]] = defaultdict(dict)
    warnings: list[str] = []

    for day in days:
        absent_count = len(absences.get(day, set()))
        if absent_count > max_parallel_absent:
            warnings.append(
                f"{day.isoformat()}: {absent_count} als abwesend eingetragen (Limit {max_parallel_absent})."
            )

    def is_unavailable(name: str, day: date) -> bool:
        return name in absences.get(day, set()) or name in off_days.get(day, set())

    def has_assignment(name: str, day: date) -> bool:
        for key, value in assigned.get(day, {}).items():
            if key == "day" and isinstance(value, list) and name in value:
                return True
            if key != "day" and value == name:
                return True
        return False

    def worked_previous_night(name: str, day: date) -> bool:
        return assigned.get(day - timedelta(days=1), {}).get("night") == name

    fridays = [d for d in days if d.weekday() == 4]
    for friday in fridays:
        saturday = friday + timedelta(days=1)
        sunday = friday + timedelta(days=2)
        if saturday.month != month or sunday.month != month:
            continue

        full_pool = [doctor.name for doctor in DOCTORS if doctor.can_full_service]
        visit_pool = [doctor.name for doctor in DOCTORS if doctor.can_visit]

        night_candidates: list[str] = []
        for name in full_pool:
            if any(is_unavailable(name, d) for d in (friday, saturday, sunday)):
                continue
            if any(has_assignment(name, d) for d in (friday, saturday, sunday)):
                continue
            if any(has_assignment(name, friday - timedelta(days=delta)) for delta in range(1, friday_night_rest_days + 1)):
                continue
            max_weekends = DOCTOR_BY_NAME[name].max_weekends_per_month
            if max_weekends is not None and weekend_count[name] >= max_weekends:
                continue
            night_candidates.append(name)

        weekend_night_doc = _pick_fair_weekend(night_candidates, weekend_count, duty_count, fte)
        if weekend_night_doc is None:
            warnings.append(f"{friday.isoformat()}: Kein Kandidat fuer Fr/Sa/So Nachtdienst.")
        else:
            assigned[friday]["night"] = weekend_night_doc
            assigned[saturday]["night"] = weekend_night_doc
            assigned[sunday]["night"] = weekend_night_doc
            duty_count[weekend_night_doc] += 3
            weekend_count[weekend_night_doc] += 1
            off_days[friday].add(weekend_night_doc)
            off_days[saturday + timedelta(days=1)].add(weekend_night_doc)
            off_days[sunday + timedelta(days=1)].add(weekend_night_doc)

        weekend_day_candidates: list[str] = []
        for name in full_pool:
            if name == weekend_night_doc:
                continue
            if any(is_unavailable(name, d) for d in (saturday, sunday)):
                continue
            if any(has_assignment(name, d) for d in (saturday, sunday)):
                continue
            max_weekends = DOCTOR_BY_NAME[name].max_weekends_per_month
            if max_weekends is not None and weekend_count[name] >= max_weekends:
                continue
            weekend_day_candidates.append(name)

        weekend_day_doc = _pick_fair_weekend(weekend_day_candidates, weekend_count, duty_count, fte)
        if weekend_day_doc is None:
            warnings.append(f"{friday.isoformat()}: Kein Kandidat fuer Sa/So Tagdienst.")
        else:
            assigned[saturday]["weekend_day"] = weekend_day_doc
            assigned[sunday]["weekend_day"] = weekend_day_doc
            duty_count[weekend_day_doc] += 2
            weekend_count[weekend_day_doc] += 1
            off_days[friday + timedelta(days=5)].add(weekend_day_doc)

        visit_candidates: list[str] = []
        for name in visit_pool:
            if name in (weekend_night_doc, weekend_day_doc):
                continue
            if any(is_unavailable(name, d) for d in (saturday, sunday)):
                continue
            if any(has_assignment(name, d) for d in (saturday, sunday)):
                continue
            visit_candidates.append(name)

        visit_doc = _pick_fair(visit_candidates, duty_count, fte)
        if visit_doc is None:
            warnings.append(f"{friday.isoformat()}: Kein Kandidat fuer Sa/So Visitendienst.")
        else:
            assigned[saturday]["visit"] = visit_doc
            assigned[sunday]["visit"] = visit_doc
            duty_count[visit_doc] += 2

        friday_late_candidates: list[str] = []
        for name in full_pool:
            if name == weekend_night_doc:
                continue
            if is_unavailable(name, friday) or has_assignment(name, friday):
                continue
            friday_late_candidates.append(name)

        friday_late_doc = _pick_fair(friday_late_candidates, duty_count, fte)
        if friday_late_doc is None:
            warnings.append(f"{friday.isoformat()}: Kein Kandidat fuer Freitag bis 19 Uhr.")
        else:
            assigned[friday]["friday_late"] = friday_late_doc
            duty_count[friday_late_doc] += 1

    for day in days:
        if day.weekday() >= 5 or day.weekday() == 4:
            continue
        if "night" in assigned[day]:
            continue
        candidates: list[str] = []
        for doctor in DOCTORS:
            if not doctor.can_full_service:
                continue
            name = doctor.name
            if is_unavailable(name, day) or has_assignment(name, day):
                continue
            candidates.append(name)
        night_doc = _pick_fair(candidates, duty_count, fte)
        if night_doc is None:
            warnings.append(f"{day.isoformat()}: Kein Kandidat fuer Nachtdienst.")
            continue
        assigned[day]["night"] = night_doc
        duty_count[night_doc] += 1
        off_days[day].add(night_doc)
        off_days[day + timedelta(days=1)].add(night_doc)

    for day in days:
        if day.weekday() >= 5:
            continue
        candidates: list[str] = []
        for doctor in DOCTORS:
            if not doctor.can_day:
                continue
            name = doctor.name
            if is_unavailable(name, day) or has_assignment(name, day) or worked_previous_night(name, day):
                continue
            candidates.append(name)
        assigned[day]["day"] = sorted(candidates)
        for name in candidates:
            duty_count[name] += 1

    weekday_map = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
    rows: list[dict[str, str]] = []
    for day in days:
        day_names = assigned.get(day, {}).get("day", [])
        if isinstance(day_names, str):
            day_names = [day_names]
        rows.append(
            {
                "Datum": day.isoformat(),
                "Wochentag": weekday_map[day.weekday()],
                "Tagdienst": ", ".join(day_names),
                "Freitag_bis_19": str(assigned.get(day, {}).get("friday_late", "")),
                "Nachtdienst": str(assigned.get(day, {}).get("night", "")),
                "Wochenend_Tagdienst": str(assigned.get(day, {}).get("weekend_day", "")),
                "Visitendienst": str(assigned.get(day, {}).get("visit", "")),
                "Abwesend": ", ".join(sorted(absences.get(day, set()))),
                "Geplant_frei": ", ".join(sorted(off_days.get(day, set()))),
            }
        )
    plan_df = pd.DataFrame(rows)

    stat_rows = [
        {
            "Arzt": doctor.name,
            "FTE": doctor.fte,
            "Dienste_gesamt": duty_count[doctor.name],
            "Dienste_pro_FTE": round(duty_count[doctor.name] / doctor.fte, 2),
            "Wochenenden": weekend_count[doctor.name],
        }
        for doctor in DOCTORS
    ]
    stats_df = pd.DataFrame(stat_rows).sort_values(by="Dienste_pro_FTE").reset_index(drop=True)
    return plan_df, stats_df, warnings
