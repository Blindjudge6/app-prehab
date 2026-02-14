from __future__ import annotations

PROGRAM_LENGTH_WEEKS = 8
STOP_CRITERIA = ["Fieber", "Schwindel", "Dyspnoe", "AP", "Schmerz > 6/10"]

QUESTIONS = [
    {
        "id": "pain_rest",
        "label": "1) Wie stark sind Ihre Hüftschmerzen in Ruhe?",
        "options": ["0-2", "3-4", "5-6", "7-10"],
        "scores": {"0-2": 2, "3-4": 1, "5-6": 0, "7-10": 0},
    },
    {
        "id": "pain_load",
        "label": "2) Wie stark sind Ihre Schmerzen bei Belastung?",
        "options": ["0-3", "4-5", "6", "7-10"],
        "scores": {"0-3": 2, "4-5": 1, "6": 0, "7-10": 0},
    },
    {
        "id": "walking",
        "label": "3) Wie lange können Sie aktuell am Stück gehen?",
        "options": ["> 30 min", "15-30 min", "5-15 min", "< 5 min"],
        "scores": {"> 30 min": 2, "15-30 min": 1, "5-15 min": 0, "< 5 min": 0},
    },
    {
        "id": "sit_to_stand",
        "label": "4) Wie oft schaffen Sie Aufstehen vom Stuhl in 30 Sekunden?",
        "options": ["> 10", "6-10", "3-5", "0-2"],
        "scores": {"> 10": 2, "6-10": 1, "3-5": 0, "0-2": 0},
    },
    {
        "id": "balance",
        "label": "5) Einbeinstand mit Festhalten: wie lange möglich?",
        "options": ["> 10 sek", "5-10 sek", "1-4 sek", "nicht möglich"],
        "scores": {"> 10 sek": 2, "5-10 sek": 1, "1-4 sek": 0, "nicht möglich": 0},
    },
    {
        "id": "endurance",
        "label": "6) Wie belastbar fühlen Sie sich im Alltag?",
        "options": ["gut", "mittel", "eher niedrig", "sehr niedrig"],
        "scores": {"gut": 2, "mittel": 1, "eher niedrig": 0, "sehr niedrig": 0},
    },
    {
        "id": "fear",
        "label": "7) Wie sicher fühlen Sie sich bei Bewegung?",
        "options": ["sehr sicher", "eher sicher", "eher unsicher", "sehr unsicher"],
        "scores": {"sehr sicher": 2, "eher sicher": 1, "eher unsicher": 0, "sehr unsicher": 0},
    },
]


def compute_profile(answers: dict) -> dict:
    score = sum(q["scores"][answers[q["id"]]] for q in QUESTIONS)

    level = "mittel"
    if score <= 5 or answers["pain_load"] in {"6", "7-10"}:
        level = "niedrig"
    elif score >= 10 and answers["pain_rest"] in {"0-2", "3-4"}:
        level = "hoch"

    focus = []
    if answers["pain_load"] in {"6", "7-10"}:
        focus.append("Schmerzregulation")
    if answers["walking"] in {"5-15 min", "< 5 min"}:
        focus.append("Gehstrecke und Mobilität")
    if answers["sit_to_stand"] in {"3-5", "0-2"}:
        focus.append("Kraftentwicklung")
    if answers["balance"] in {"1-4 sek", "nicht möglich"}:
        focus.append("Balance und Sturzprophylaxe")
    if answers["endurance"] in {"eher niedrig", "sehr niedrig"}:
        focus.append("Kardiorespiratorische Belastbarkeit")
    if answers["fear"] in {"eher unsicher", "sehr unsicher"}:
        focus.append("Bewegungssicherheit")

    if not focus:
        focus = ["Funktionserhalt und Progression"]

    intensity_hint = {
        "niedrig": "sanfter Belastungsaufbau",
        "mittel": "moderates Trainingsniveau",
        "hoch": "aktive Belastungssteigerung",
    }[level]

    return {
        "score": score,
        "level": level,
        "level_label": level.capitalize(),
        "focus_areas": focus,
        "intensity_hint": intensity_hint,
    }


def get_progression(level: str, week: int) -> dict:
    base = {
        "niedrig": {"sets": 2, "reps": "6-8", "endurance": 10},
        "mittel": {"sets": 2, "reps": "8-10", "endurance": 15},
        "hoch": {"sets": 3, "reps": "10-12", "endurance": 20},
    }[level]

    if week >= 3:
        base["sets"] += 1 if level != "niedrig" else 0
        base["endurance"] += 5
    if week >= 5:
        base["reps"] = {"niedrig": "8-10", "mittel": "10-12", "hoch": "12-14"}[level]
        base["endurance"] += 5
    if week >= 7:
        base["endurance"] += 5

    return base


EXERCISE_LIBRARY = {
    "niedrig": {
        "warmup": [
            {
                "name": "Langsames Gehen",
                "how": "Gehen Sie auf ebenem Untergrund in ruhigem, gleichmäßigem Tempo.",
                "focus": "Kreislaufaktivierung und Gelenkvorbereitung",
                "safety": "Bei Unsicherheit nutzen Sie eine stabile Abstützung.",
                "dose": "2-3 Minuten",
            },
            {
                "name": "Beckenkippen im Stand",
                "how": "Stellen Sie sich hüftbreit hin und kippen Sie das Becken langsam vor und zurück.",
                "focus": "Lumbopelvine Mobilität",
                "safety": "Ohne Schwung bewegen und ruhig weiteratmen.",
                "dose": "8-10 Wiederholungen",
            },
            {
                "name": "Kleines Hüftkreisen",
                "how": "Halten Sie sich leicht fest und führen Sie kleine, kontrollierte Beckenkreise aus.",
                "focus": "Gelenkmobilisation der Hüfte",
                "safety": "Bewegen Sie nur im schmerzarmen Bereich.",
                "dose": "5 Kreise je Richtung",
            },
        ],
        "strength": [
            {
                "name": "Sitz-auf-Stand mit Armhilfe",
                "how": "Setzen Sie sich auf einen stabilen Stuhl, stehen Sie kontrolliert auf und setzen Sie sich langsam wieder ab.",
                "focus": "Kraft von Oberschenkel und Gesäß",
                "safety": "Knie zeigen nach vorne, Last gleichmäßig verteilen.",
            },
            {
                "name": "Kurzes Bridging",
                "how": "In Rückenlage die Füße aufstellen, das Becken leicht anheben und kontrolliert absenken.",
                "focus": "Aktivierung der dorsalen Kette",
                "safety": "Kein Hohlkreuz erzwingen.",
            },
            {
                "name": "Seitliches Beinheben im Stand",
                "how": "Mit einer Hand abstützen, ein Bein langsam seitlich anheben und wieder senken.",
                "focus": "Kräftigung der Hüftabduktoren",
                "safety": "Den Oberkörper aufrecht halten.",
            },
        ],
        "balance": [
            {
                "name": "Gewichtsverlagerung rechts-links",
                "how": "Stehen Sie hüftbreit und verlagern Sie das Gewicht langsam von einer Seite zur anderen.",
                "focus": "Posturale Kontrolle im Stand",
                "safety": "Üben Sie in Wand- oder Stuhlnähe.",
                "dose": "30-45 Sekunden pro Satz",
            },
            {
                "name": "Tandemstand mit Halt",
                "how": "Ein Fuß vor den anderen, Position mit leichter Abstützung halten.",
                "focus": "Stabilisierung in enger Standbasis",
                "safety": "Blick nach vorne und ruhig atmen.",
                "dose": "20-30 Sekunden pro Seite",
            },
        ],
        "endurance": {
            "name": "Gehen in moderatem Tempo",
            "how": "Gehen Sie so, dass Sprechen weiterhin möglich bleibt.",
            "focus": "Alltagsausdauer",
            "safety": "Bei deutlicher Schmerzsteigerung sofort Tempo reduzieren.",
        },
        "cooldown": [
            {
                "name": "Ruhige Atmung",
                "how": "Atmen Sie langsam durch die Nase ein und verlängert durch den Mund aus.",
                "focus": "Vegetative Beruhigung",
                "safety": "Aufrecht sitzen oder stehen.",
                "dose": "2 Minuten",
            },
            {
                "name": "Sanfte Hüftbeuger-Dehnung",
                "how": "Im halben Ausfallschritt das Becken vorsichtig nach vorne schieben, bis vorn an der Hüfte ein Zug spürbar ist.",
                "focus": "Verbesserung der Hüftextension",
                "safety": "Nicht in den Schmerz hineindehnen.",
                "dose": "20-30 Sekunden pro Seite",
            },
        ],
    },
    "mittel": {
        "warmup": [
            {
                "name": "Zügiges Gehen",
                "how": "Gehen Sie in gleichmäßig flottem Rhythmus.",
                "focus": "Kardiovaskuläre Aktivierung",
                "safety": "Achten Sie auf sichere Schrittführung.",
                "dose": "5 Minuten",
            },
            {
                "name": "Beckenkippen im Stand",
                "how": "Kippen Sie das Becken kontrolliert vor und zurück, ohne den Oberkörper zu verdrehen.",
                "focus": "Mobilisation der LWS-Hüft-Region",
                "safety": "Bewegung klein und präzise halten.",
                "dose": "10 Wiederholungen",
            },
            {
                "name": "Dynamische Ausfallschritt-Vorbereitung",
                "how": "Setzen Sie einen kleinen Schritt nach vorne, übernehmen Sie kurz Last und gehen Sie zurück.",
                "focus": "Vorbereitung für funktionelle Kraftübungen",
                "safety": "Nur so tief bewegen, wie es schmerzarm möglich ist.",
                "dose": "8 je Seite",
            },
        ],
        "strength": [
            {
                "name": "Sitz-auf-Stand ohne Armhilfe",
                "how": "Stehen Sie vom Stuhl auf und setzen Sie sich langsam ohne Handunterstützung wieder ab.",
                "focus": "Funktionelle Kraft und Kontrolle",
                "safety": "Knie stabil über den Füßen führen.",
            },
            {
                "name": "Bridging",
                "how": "In Rückenlage das Becken bis zur Linie Schulter-Hüfte-Knie anheben, kurz halten und absenken.",
                "focus": "Kräftigung der Hüftextensoren",
                "safety": "Nacken entspannt lassen.",
            },
            {
                "name": "Mini-Kniebeuge am Stuhl",
                "how": "Mit leichter Handführung an der Lehne in die Knie gehen und wieder strecken.",
                "focus": "Beinachsenkontrolle",
                "safety": "Fersen am Boden halten.",
            },
        ],
        "balance": [
            {
                "name": "Einbeinstand mit Fingerkontakt",
                "how": "Heben Sie ein Bein an und stabilisieren Sie sich mit einem Finger an Tisch oder Wand.",
                "focus": "Einbeinige Standstabilität",
                "safety": "Becken waagerecht halten.",
                "dose": "20-30 Sekunden pro Seite",
            },
            {
                "name": "Tandemgang",
                "how": "Gehen Sie Ferse vor Spitze in einer Linie, langsam und kontrolliert.",
                "focus": "Koordination und Gleichgewicht",
                "safety": "Üben Sie in Flurnähe mit möglichem Wandkontakt.",
                "dose": "10-20 Schritte",
            },
        ],
        "endurance": {
            "name": "Zügiges Gehen",
            "how": "Wählen Sie ein Tempo, bei dem Sie noch sprechen können, aber leicht außer Atem sind.",
            "focus": "Präoperative Ausdauerverbesserung",
            "safety": "Bei Erschöpfung kurz verlangsamen.",
        },
        "cooldown": [
            {
                "name": "Ruhige Atmung",
                "how": "Atmung verlängern und den Puls schrittweise senken.",
                "focus": "Regeneration",
                "safety": "Nicht pressen.",
                "dose": "2 Minuten",
            },
            {
                "name": "Dehnung Gesäß und vorderer Oberschenkel",
                "how": "Dehnen Sie beide Muskelgruppen nacheinander in ruhiger Position.",
                "focus": "Spannungsreduktion",
                "safety": "Nur bis zu moderatem Dehngefühl gehen.",
                "dose": "20-30 Sekunden pro Seite",
            },
        ],
    },
    "hoch": {
        "warmup": [
            {
                "name": "Zügiges Gehen",
                "how": "Gehen Sie rhythmisch und lassen Sie die Arme locker mitschwingen.",
                "focus": "Ganzkörperaktivierung",
                "safety": "Gleichmäßig atmen.",
                "dose": "5-7 Minuten",
            },
            {
                "name": "Dynamische Hüftmobilisation",
                "how": "Bein vor und zurück pendeln, mit kleiner Amplitude und guter Kontrolle.",
                "focus": "Erweiterung des Bewegungsumfangs",
                "safety": "Bei Bedarf an stabiler Fläche festhalten.",
                "dose": "8-10 je Seite",
            },
            {
                "name": "Schrittmuster vorwärts-rückwärts",
                "how": "Setzen Sie mehrere kontrollierte Schritte vor und zurück.",
                "focus": "Koordination und Reaktionsfähigkeit",
                "safety": "Keine abrupten Richtungswechsel.",
                "dose": "60-90 Sekunden",
            },
        ],
        "strength": [
            {
                "name": "Sitz-auf-Stand mit langsamer Absenkphase",
                "how": "Normal aufstehen, beim Hinsetzen drei Sekunden kontrolliert absenken.",
                "focus": "Exzentrische Muskelkontrolle",
                "safety": "Rumpf stabil halten.",
            },
            {
                "name": "Kurzer Ausfallschritt",
                "how": "Kleinen Schritt nach vorne setzen, beide Knie leicht beugen und kontrolliert zurückgehen.",
                "focus": "Funktionelle Hüft- und Beinkraft",
                "safety": "Vorderes Knie über dem Fuß halten.",
            },
            {
                "name": "Step-up auf niedrige Stufe",
                "how": "Mit einem Fuß aufsteigen, hochdrücken und kontrolliert wieder absteigen.",
                "focus": "Treppenfunktion und Kraft",
                "safety": "Geländer oder Wand in Reichweite.",
            },
        ],
        "balance": [
            {
                "name": "Einbeinstand frei",
                "how": "Heben Sie ein Bein an, stabilisieren Sie frei und wechseln Sie die Seite.",
                "focus": "Fortgeschrittene Standkontrolle",
                "safety": "Zu Beginn nahe einer stabilen Abstützung üben.",
                "dose": "20-40 Sekunden pro Seite",
            },
            {
                "name": "Seitwärtsschritte mit Stop",
                "how": "Gehen Sie seitlich zwei bis drei Schritte, stoppen Sie kurz und wechseln Sie die Richtung.",
                "focus": "Laterale Stabilität",
                "safety": "Rutschfesten, ebenen Untergrund nutzen.",
                "dose": "45-60 Sekunden",
            },
        ],
        "endurance": {
            "name": "Intervall-Gehen",
            "how": "Gehen Sie zwei Minuten zügig und anschließend eine Minute locker, dann wiederholen.",
            "focus": "Kardiorespiratorische Leistungsfähigkeit",
            "safety": "Bei Beschwerden die Intensität unmittelbar reduzieren.",
        },
        "cooldown": [
            {
                "name": "Ruhige Atmung",
                "how": "Atmen Sie tief und kontrolliert, bis sich der Puls beruhigt.",
                "focus": "Physiologische Erholung",
                "safety": "Nicht flach atmen.",
                "dose": "2 Minuten",
            },
            {
                "name": "Waden- und Hüftbeuger-Dehnung",
                "how": "Dehnen Sie beide Seiten nacheinander in ruhiger Haltung.",
                "focus": "Beweglichkeitserhalt",
                "safety": "Keine ruckartigen Bewegungen.",
                "dose": "20-30 Sekunden pro Seite",
            },
        ],
    },
}


def get_exercises(level: str) -> dict:
    return EXERCISE_LIBRARY[level]


def _attach_dose(items: list[dict], dose_text: str) -> list[dict]:
    result = []
    for item in items:
        updated = dict(item)
        updated["plan_dose"] = dose_text
        result.append(updated)
    return result


def iter_patient_texts() -> list[str]:
    texts = []
    for question in QUESTIONS:
        texts.append(question["label"])
    for level_data in EXERCISE_LIBRARY.values():
        for section_name in ["warmup", "strength", "balance", "cooldown"]:
            for exercise in level_data[section_name]:
                texts.extend([exercise["name"], exercise["how"], exercise["focus"], exercise["safety"]])
        endurance = level_data["endurance"]
        texts.extend([endurance["name"], endurance["how"], endurance["focus"], endurance["safety"]])
    return texts


def build_week_plan(profile: dict, week: int) -> dict:
    level = profile["level"]
    progression = get_progression(level, week)
    ex = get_exercises(level)

    sessions = []
    for tag in ["Einheit A", "Einheit B", "Einheit C"]:
        sessions.append(
            {
                "title": f"{tag} (Woche {week})",
                "warmup": ex["warmup"],
                "strength": _attach_dose(ex["strength"], f"{progression['sets']} Sätze x {progression['reps']}"),
                "balance": _attach_dose(ex["balance"], f"{progression['sets']} Sätze"),
                "endurance": {
                    "name": ex["endurance"]["name"],
                    "how": ex["endurance"]["how"],
                    "focus": ex["endurance"]["focus"],
                    "safety": ex["endurance"]["safety"],
                    "plan_dose": f"{progression['endurance']} Minuten",
                },
                "cooldown": ex["cooldown"],
            }
        )

    return {
        "sessions_per_week": 3,
        "sets": progression["sets"],
        "reps_text": progression["reps"],
        "endurance_minutes": progression["endurance"],
        "sessions": sessions,
    }
