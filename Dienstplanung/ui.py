from __future__ import annotations

import calendar
from collections import defaultdict
from datetime import date, timedelta

import pandas as pd
import streamlit as st

from models import DOCTORS
from planner import generate_plan


def _doctor_overview() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Arzt": d.name,
                "Tagdienst": d.can_day,
                "Visitendienst": d.can_visit,
                "Nacht/Wochenende": d.can_full_service,
                "FTE": d.fte,
                "Max Wochenenden/Monat": d.max_weekends_per_month if d.max_weekends_per_month is not None else "-",
            }
            for d in DOCTORS
        ]
    )


def _init_state() -> None:
    if "urlaub_entries" not in st.session_state:
        st.session_state.urlaub_entries = {}
    if "sperr_entries" not in st.session_state:
        st.session_state.sperr_entries = {}
    if "wunsch_entries" not in st.session_state:
        st.session_state.wunsch_entries = []


def _add_date_range_entries(
    target_key: str,
    start_day: date,
    end_day: date,
    doctors: list[str],
) -> None:
    if end_day < start_day:
        st.error("Enddatum darf nicht vor dem Startdatum liegen.")
        return
    if not doctors:
        st.error("Bitte mindestens einen Arzt auswaehlen.")
        return

    target: dict[str, list[str]] = st.session_state[target_key]
    day = start_day
    while day <= end_day:
        day_key = day.isoformat()
        existing = set(target.get(day_key, []))
        existing.update(doctors)
        target[day_key] = sorted(existing)
        day += timedelta(days=1)
    st.session_state[target_key] = target
    st.success("Eintrag gespeichert.")


def _entries_to_df(entries: dict[str, list[str]], title: str) -> pd.DataFrame:
    rows = []
    for day_key in sorted(entries.keys()):
        rows.append(
            {
                "Typ": title,
                "Datum": day_key,
                "Aerzte": ", ".join(entries[day_key]),
            }
        )
    return pd.DataFrame(rows)


def _structured_unavailable() -> tuple[dict[date, set[str]], pd.DataFrame]:
    unavailable: dict[date, set[str]] = defaultdict(set)
    urlaub: dict[str, list[str]] = st.session_state.urlaub_entries
    sperr: dict[str, list[str]] = st.session_state.sperr_entries

    for day_key, names in urlaub.items():
        unavailable[date.fromisoformat(day_key)].update(names)
    for day_key, names in sperr.items():
        unavailable[date.fromisoformat(day_key)].update(names)

    urlaub_df = _entries_to_df(urlaub, "Urlaub")
    sperr_df = _entries_to_df(sperr, "Sperrtag")
    overview = pd.concat([urlaub_df, sperr_df], ignore_index=True)
    return unavailable, overview


def _wish_conflicts(plan_df: pd.DataFrame) -> list[str]:
    wishes: list[dict[str, str]] = st.session_state.wunsch_entries
    if not wishes:
        return []

    by_date = {row["Datum"]: row for _, row in plan_df.iterrows()}
    conflicts: list[str] = []

    for wish in wishes:
        wish_day = wish["Datum"]
        wish_doc = wish["Arzt"]
        wish_type = wish["Wunsch"]
        row = by_date.get(wish_day)
        if not row:
            continue

        weekday_day_names = [n.strip() for n in str(row["Tagdienst"]).split(",") if n.strip()]
        is_day = wish_doc in weekday_day_names or row["Wochenend_Tagdienst"] == wish_doc
        is_night = row["Nachtdienst"] == wish_doc
        is_visit = row["Visitendienst"] == wish_doc
        date_label = f"{wish_day} ({wish_doc})"

        if wish_type == "Tagdienst gewuenscht" and not is_day:
            conflicts.append(f"{date_label}: Wunsch nicht erfuellt (kein Tagdienst).")
        if wish_type == "Nachtdienst gewuenscht" and not is_night:
            conflicts.append(f"{date_label}: Wunsch nicht erfuellt (kein Nachtdienst).")
        if wish_type == "Visitendienst gewuenscht" and not is_visit:
            conflicts.append(f"{date_label}: Wunsch nicht erfuellt (kein Visitendienst).")
        if wish_type == "Tagdienst nicht gewuenscht" and is_day:
            conflicts.append(f"{date_label}: Wunsch verletzt (Tagdienst zugeteilt).")
        if wish_type == "Nachtdienst nicht gewuenscht" and is_night:
            conflicts.append(f"{date_label}: Wunsch verletzt (Nachtdienst zugeteilt).")
        if wish_type == "Visitendienst nicht gewuenscht" and is_visit:
            conflicts.append(f"{date_label}: Wunsch verletzt (Visitendienst zugeteilt).")

    return conflicts


def _render_constraints_ui(year: int, month: int) -> None:
    doctor_names = [d.name for d in DOCTORS]
    tab_urlaub, tab_sperr, tab_wunsch = st.tabs(["Urlaub", "Sperrtage", "Wuensche"])

    with tab_urlaub:
        col1, col2 = st.columns(2)
        with col1:
            start = st.date_input("Urlaub von", key="urlaub_start")
        with col2:
            end = st.date_input("Urlaub bis", key="urlaub_end")
        doctors = st.multiselect("Aerzte", doctor_names, key="urlaub_doctors")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Urlaub speichern"):
                _add_date_range_entries("urlaub_entries", start, end, doctors)
        with c2:
            if st.button("Urlaub loeschen"):
                st.session_state.urlaub_entries = {}
        df = _entries_to_df(st.session_state.urlaub_entries, "Urlaub")
        if not df.empty:
            st.dataframe(df, use_container_width=True)

    with tab_sperr:
        col1, col2 = st.columns(2)
        with col1:
            start = st.date_input("Sperrtag von", key="sperr_start")
        with col2:
            end = st.date_input("Sperrtag bis", key="sperr_end")
        doctors = st.multiselect("Aerzte ", doctor_names, key="sperr_doctors")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Sperrtage speichern"):
                _add_date_range_entries("sperr_entries", start, end, doctors)
        with c2:
            if st.button("Sperrtage loeschen"):
                st.session_state.sperr_entries = {}
        df = _entries_to_df(st.session_state.sperr_entries, "Sperrtag")
        if not df.empty:
            st.dataframe(df, use_container_width=True)

    with tab_wunsch:
        _, last_day = calendar.monthrange(year, month)
        day_options = list(range(1, last_day + 1))
        wish_day_num = st.selectbox("Monatstag", day_options, key="wish_day_num")
        wish_day = date(year, month, wish_day_num)
        st.caption(f"Ausgewaehltes Datum: {wish_day.isoformat()}")
        wish_doc = st.selectbox("Arzt", doctor_names, key="wish_doc")
        wish_type = st.selectbox(
            "Wunsch",
            [
                "Tagdienst gewuenscht",
                "Nachtdienst gewuenscht",
                "Visitendienst gewuenscht",
                "Tagdienst nicht gewuenscht",
                "Nachtdienst nicht gewuenscht",
                "Visitendienst nicht gewuenscht",
            ],
            key="wish_type",
        )
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Wunsch speichern"):
                st.session_state.wunsch_entries.append(
                    {"Datum": wish_day.isoformat(), "Arzt": wish_doc, "Wunsch": wish_type}
                )
                st.success("Wunsch gespeichert.")
        with c2:
            if st.button("Wuensche loeschen"):
                st.session_state.wunsch_entries = []
        if st.session_state.wunsch_entries:
            st.dataframe(pd.DataFrame(st.session_state.wunsch_entries), use_container_width=True)


def render_app() -> None:
    st.set_page_config(page_title="Dienstplanung Chirurgie", layout="wide")
    _init_state()
    st.title("Dienstplanung Assistenzarzt Chirurgie")
    st.write("Automatische MVP-Planung fuer Tag-, Nacht-, Wochenend- und Visitendienste.")

    col1, col2, col3 = st.columns(3)
    with col1:
        year = int(
            st.number_input(
                "Jahr",
                min_value=2025,
                max_value=2035,
                value=date.today().year,
                step=1,
            )
        )
    with col2:
        month = int(
            st.number_input(
                "Monat",
                min_value=1,
                max_value=12,
                value=date.today().month,
                step=1,
            )
        )
    with col3:
        max_parallel_absent = int(
            st.number_input(
                "Max. gleichzeitig frei",
                min_value=0,
                max_value=len(DOCTORS),
                value=3,
                step=1,
            )
        )

    st.markdown("**Urlaub, Sperrtage und Wuensche**")
    _render_constraints_ui(year, month)

    if st.button("Plan generieren", type="primary"):
        unavailable, unavailable_df = _structured_unavailable()
        plan_df, stats_df, plan_warnings = generate_plan(
            year=year,
            month=month,
            absences=unavailable,
            max_parallel_absent=max_parallel_absent,
            friday_night_rest_days=3,
        )
        warnings = plan_warnings + _wish_conflicts(plan_df)

        if warnings:
            st.warning("Hinweise / Konflikte:")
            for warning in warnings:
                st.write(f"- {warning}")

        if not unavailable_df.empty:
            st.subheader("Harte Abwesenheiten (Urlaub + Sperrtage)")
            st.dataframe(unavailable_df, use_container_width=True)

        st.subheader("Monatsplan")
        st.dataframe(plan_df, use_container_width=True)

        st.subheader("Fairness-Statistik")
        st.dataframe(stats_df, use_container_width=True)

        csv_data = plan_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="CSV herunterladen",
            data=csv_data,
            file_name=f"dienstplan_{year}_{month:02d}.csv",
            mime="text/csv",
        )

    st.markdown("**Aerztestamm**")
    st.dataframe(_doctor_overview(), use_container_width=True)
