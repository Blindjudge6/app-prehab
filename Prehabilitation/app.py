from __future__ import annotations

import base64
import hmac
import os
import re
import sys
from pathlib import Path

import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from prehab_logic import (
    PROGRAM_LENGTH_WEEKS,
    QUESTIONS,
    STOP_CRITERIA,
    build_week_plan,
    compute_profile,
)

UI_READABILITY = {
    "base_font_px": 18,
    "line_height": 1.58,
    "max_content_width_px": 980,
}

APP_TITLE = "Priener Prä-Rehabilitationsprogramm RoMed Klinik Prien"
LOGO_CANDIDATES = [
    BASE_DIR / "assets/romed_prien_logo_transparent.png",
    BASE_DIR / "assets/romed_prien_logo_trim.png",
    BASE_DIR / "assets/romed_prien_logo.png",
    BASE_DIR / "assets/romed_prien_logo.jpg",
    BASE_DIR / "assets/romed_prien_logo.jpeg",
    BASE_DIR / "assets/romed_prien_logo.svg",
    BASE_DIR / "romed_prien_logo.png",
]

st.set_page_config(page_title=APP_TITLE, page_icon="", layout="wide")


def get_logo_path() -> Path | None:
    for logo_path in LOGO_CANDIDATES:
        if logo_path.exists():
            return logo_path
    return None


def get_logo_data_uri() -> str | None:
    logo_path = get_logo_path()
    if not logo_path:
        return None

    suffix = logo_path.suffix.lower()
    if suffix == ".svg":
        mime = "image/svg+xml"
    elif suffix in {".jpg", ".jpeg"}:
        mime = "image/jpeg"
    elif suffix == ".webp":
        mime = "image/webp"
    else:
        mime = "image/png"

    encoded = base64.b64encode(logo_path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def inject_styles() -> None:
    st.markdown(
        f"""
        <style>
        :root {{
            --bg: #f5f5f7;
            --card: #ffffff;
            --text-main: #1d1d1f;
            --text-subtle: #5f6368;
            --line: #dfe3e8;
            --accent: #0a84ff;
            --sidebar-bg: #eef2f6;
        }}
        .stApp {{
            background: radial-gradient(circle at top left, #ffffff 0%, var(--bg) 58%, #eceff3 100%);
            color: var(--text-main);
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", sans-serif;
            font-size: {UI_READABILITY['base_font_px']}px;
            line-height: {UI_READABILITY['line_height']};
        }}
        .stApp, .stApp p, .stApp label, .stApp span, .stApp div {{
            color: var(--text-main);
        }}
        .block-container {{
            max-width: {UI_READABILITY['max_content_width_px']}px;
            padding-top: 2rem;
            padding-bottom: 2.5rem;
        }}
        .brand-floating {{
            position: fixed;
            top: 68px;
            right: 24px;
            z-index: 1000;
            pointer-events: none;
        }}
        .brand-floating img {{
            width: min(27vw, 360px);
            height: auto;
            filter: contrast(1.06) saturate(1.04);
            image-rendering: -webkit-optimize-contrast;
        }}
        @media (max-width: 1100px) {{
            .brand-floating {{
                position: static;
                margin-bottom: 10px;
            }}
            .brand-floating img {{
                width: min(72vw, 380px);
            }}
        }}
        h1, h2, h3 {{
            letter-spacing: -0.02em;
            color: var(--text-main);
        }}
        [data-testid="stSidebar"] {{
            background: var(--sidebar-bg);
            border-right: 1px solid var(--line);
        }}
        [data-testid="stSidebar"] * {{
            color: var(--text-main) !important;
        }}
        .hero {{
            background: rgba(255, 255, 255, 0.92);
            border: 1px solid var(--line);
            border-radius: 22px;
            padding: 22px;
            margin-bottom: 16px;
            backdrop-filter: blur(8px);
        }}
        .hero p {{
            color: var(--text-subtle);
            margin: 0;
        }}
        .metric-card {{
            background: rgba(255, 255, 255, 0.92);
            border: 1px solid var(--line);
            border-radius: 16px;
            padding: 14px;
        }}
        .metric-label {{
            font-size: 0.86rem;
            color: var(--text-subtle);
            margin-bottom: 2px;
        }}
        .metric-value {{
            font-size: 1.2rem;
            font-weight: 620;
        }}
        .exercise-card {{
            background: rgba(255, 255, 255, 0.96);
            border: 1px solid var(--line);
            border-radius: 14px;
            padding: 14px;
            margin: 10px 0;
        }}
        .exercise-name {{
            font-weight: 620;
            margin-bottom: 6px;
        }}
        .dose-tag {{
            display: inline-block;
            border-radius: 999px;
            border: 1px solid rgba(10,132,255,0.28);
            color: #0759b3;
            background: rgba(10,132,255,0.08);
            padding: 2px 9px;
            font-size: 0.8rem;
            margin-bottom: 8px;
        }}
        .exercise-hint {{
            color: var(--text-subtle);
            margin-top: 8px;
        }}
        .section-note {{
            color: var(--text-subtle);
            margin-top: -4px;
            margin-bottom: 10px;
        }}
        [data-testid="stForm"] {{
            background: rgba(255, 255, 255, 0.98);
            border: 1px solid var(--line);
            border-radius: 16px;
            padding: 16px;
        }}
        [data-testid="stForm"] label,
        [data-testid="stForm"] p,
        [data-testid="stForm"] span,
        [data-testid="stForm"] div {{
            color: var(--text-main) !important;
        }}
        [data-testid="stRadio"] label p {{
            color: var(--text-main) !important;
            font-weight: 530;
        }}
        [data-testid="stRadio"] [role="radiogroup"] label {{
            background: #ffffff;
            border: 1px solid var(--line);
            border-radius: 12px;
            padding: 8px 10px;
            margin-bottom: 6px;
        }}
        [data-testid="stSlider"] {{
            padding-top: 8px;
            padding-bottom: 10px;
        }}
        [data-testid="stSlider"] label {{
            font-size: 1.08rem !important;
            font-weight: 560 !important;
        }}
        [data-testid="stSlider"] div[role="slider"] {{
            width: 1.3rem !important;
            height: 1.3rem !important;
            border: 2px solid #ffffff !important;
            box-shadow: 0 0 0 2px rgba(10, 132, 255, 0.2) !important;
        }}
        [data-testid="stSlider"] div[data-baseweb="slider"] > div > div {{
            height: 8px !important;
            border-radius: 999px !important;
        }}
        .stButton button,
        .stFormSubmitButton button {{
            border-radius: 999px;
            border: none;
            background: var(--accent);
            color: #ffffff;
            font-weight: 600;
        }}
        .stButton button:hover,
        .stFormSubmitButton button:hover {{
            background: #0074e0;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def init_state() -> None:
    if "assessment_done" not in st.session_state:
        st.session_state.assessment_done = False
    if "answers" not in st.session_state:
        st.session_state.answers = {}
    if "profile" not in st.session_state:
        st.session_state.profile = None
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False


def render_floating_logo() -> None:
    logo_uri = get_logo_data_uri()
    if logo_uri:
        st.markdown(
            f'<div class="brand-floating"><img src="{logo_uri}" alt="RoMed Klinik Prien Logo"></div>',
            unsafe_allow_html=True,
        )


def render_hero(title: str, subtitle: str) -> None:
    st.markdown(
        f'<div class="hero"><h1>{title}</h1><p>{subtitle}</p></div>',
        unsafe_allow_html=True,
    )


def render_branding(subtitle: str) -> None:
    render_hero(APP_TITLE, subtitle)


def require_password_access() -> bool:
    if st.session_state.authenticated:
        return True

    configured_password = ""
    try:
        configured_password = str(st.secrets.get("APP_PASSWORD", "")).strip()
    except Exception:
        configured_password = ""

    if not configured_password:
        configured_password = os.environ.get("APP_PASSWORD", "").strip()

    if not configured_password:
        local_secrets = BASE_DIR / ".streamlit" / "secrets.toml"
        if local_secrets.exists():
            try:
                for line in local_secrets.read_text(encoding="utf-8").splitlines():
                    stripped = line.strip()
                    if not stripped or stripped.startswith("#"):
                        continue
                    if stripped.startswith("APP_PASSWORD"):
                        _, raw_value = stripped.split("=", 1)
                        configured_password = raw_value.strip().strip('"').strip("'")
                        break
            except Exception:
                configured_password = ""
    if not configured_password or configured_password in {"CHANGE_ME", "SET_YOUR_PASSWORD_HERE"}:
        render_branding("Die Anwendung ist passwortgeschützt. Bitte hinterlegen Sie ein gültiges APP_PASSWORD in den Secrets.")
        st.error("Passwort nicht konfiguriert.")
        return False

    render_branding("Bitte geben Sie das Passwort ein, um die Anwendung zu öffnen.")
    with st.form("login_form"):
        entered_password = st.text_input("Passwort", type="password")
        submitted = st.form_submit_button("Anmelden")

    if submitted:
        if hmac.compare_digest(entered_password, configured_password):
            st.session_state.authenticated = True
            st.rerun()
        st.error("Das eingegebene Passwort ist nicht korrekt.")

    return False


def render_metric_card(label: str, value: str) -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def split_instruction_steps(text: str) -> list[str]:
    parts = re.split(r"[.;]", text)
    compact = []
    for part in parts:
        for chunk in part.split(","):
            cleaned = chunk.strip()
            if cleaned:
                compact.append(cleaned)

    if len(compact) >= 3:
        return compact[:3]
    if len(compact) == 2:
        return compact
    return [text.strip()]


def render_exercise_card(item: dict, fallback_dose: str = "") -> None:
    dose = item.get("plan_dose") or item.get("dose") or fallback_dose
    st.markdown(f'<div class="exercise-card"><div class="exercise-name">{item["name"]}</div>', unsafe_allow_html=True)
    if dose:
        st.markdown(f'<div class="dose-tag">Umfang: {dose}</div>', unsafe_allow_html=True)

    st.write("So führen Sie die Übung aus:")
    for idx, step in enumerate(split_instruction_steps(item["how"]), start=1):
        st.write(f"{idx}. {step}")

    st.write(f"**Therapeutisches Ziel:** {item['focus']}")
    st.markdown(f'<div class="exercise-hint"><strong>Sicherheitshinweis:</strong> {item["safety"]}</div></div>', unsafe_allow_html=True)


def render_questionnaire() -> None:
    render_branding(
        "Bitte beantworten Sie diesen kurzen Fragebogen vor jeder Trainingseinheit. Anschließend erhalten Sie Ihr tagesaktuelles Trainingsprogramm.",
    )

    with st.form("fragebogen"):
        answers = {}
        for question in QUESTIONS:
            answers[question["id"]] = st.radio(question["label"], question["options"], horizontal=False)
        submitted = st.form_submit_button("Programm erstellen")

    if submitted:
        st.session_state.answers = answers
        st.session_state.profile = compute_profile(answers)
        st.session_state.assessment_done = True
        st.rerun()


def render_profile(profile: dict) -> None:
    st.subheader("Ihr Belastungsprofil")
    c1, c2, c3 = st.columns(3)
    with c1:
        render_metric_card("Potenzialstufe", profile["level_label"])
    with c2:
        render_metric_card("Punktwert", f"{profile['score']}/14")
    with c3:
        render_metric_card("Belastungsstrategie", profile["intensity_hint"])

    st.markdown("<div class='section-note'>Therapeutische Schwerpunkte: " + ", ".join(profile["focus_areas"]) + "</div>", unsafe_allow_html=True)


def render_stop_check() -> bool:
    st.subheader("Tagescheck vor der Trainingseinheit")
    st.caption("Wenn ein Kriterium zutrifft, führen Sie heute bitte kein Training durch.")

    cols = st.columns(len(STOP_CRITERIA))
    selected = []
    for idx, criterion in enumerate(STOP_CRITERIA):
        selected.append(cols[idx].checkbox(criterion, value=False, key=f"stop_{idx}"))

    must_stop = any(selected)
    if must_stop:
        st.error("Training heute aussetzen. Bitte nehmen Sie medizinische Rücksprache auf.")
    else:
        st.success("Tagescheck unauffällig. Das Training kann durchgeführt werden.")
    return must_stop


def render_session(session: dict) -> None:
    st.markdown("#### Aufwärmphase")
    for item in session["warmup"]:
        render_exercise_card(item)

    st.markdown("#### Kraft und Funktion")
    for item in session["strength"]:
        render_exercise_card(item)

    st.markdown("#### Balance und Stabilität")
    for item in session["balance"]:
        render_exercise_card(item)

    st.markdown("#### Ausdauer")
    render_exercise_card(session["endurance"])

    st.markdown("#### Cool-down")
    for item in session["cooldown"]:
        render_exercise_card(item)


def render_week_plan(profile: dict) -> None:
    st.subheader("Ihr 8-Wochen-Trainingsplan")
    week = st.slider("Aktuelle Trainingswoche", min_value=1, max_value=PROGRAM_LENGTH_WEEKS, value=1)
    plan = build_week_plan(profile, week)

    m1, m2, m3 = st.columns(3)
    with m1:
        render_metric_card("Einheiten pro Woche", str(plan["sessions_per_week"]))
    with m2:
        render_metric_card("Sätze", str(plan["sets"]))
    with m3:
        render_metric_card("Wiederholungen", plan["reps_text"])

    st.caption(f"Ausdauerziel pro Einheit: {plan['endurance_minutes']} Minuten")

    tabs = st.tabs([session["title"] for session in plan["sessions"]])
    for idx, session in enumerate(plan["sessions"]):
        with tabs[idx]:
            render_session(session)


def main() -> None:
    inject_styles()
    init_state()
    render_floating_logo()

    if not require_password_access():
        return

    with st.sidebar:
        st.header("Navigation")
        if st.button("Abmelden", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()
        if st.session_state.assessment_done:
            if st.button("Tagesprofil neu erfassen", use_container_width=True):
                st.session_state.assessment_done = False
                st.session_state.answers = {}
                st.session_state.profile = None
                st.rerun()
        st.caption("Keine dauerhafte Datenspeicherung aktiv")

    if not st.session_state.assessment_done:
        render_questionnaire()
        return

    render_branding("Ihr individualisierter Trainingsplan zur funktionellen Vorbereitung auf die Operation.")
    profile = st.session_state.profile
    render_profile(profile)

    if not render_stop_check():
        render_week_plan(profile)


if __name__ == "__main__":
    main()
