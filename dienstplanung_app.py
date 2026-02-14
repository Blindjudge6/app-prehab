from __future__ import annotations

import runpy
from pathlib import Path


base = Path(__file__).resolve().parent / "Dienstplanung"
candidate_new = base / "dienstplanung_app.py"
candidate_old = base / "app.py"
target = candidate_new if candidate_new.exists() else candidate_old
runpy.run_path(str(target), run_name="__main__")
