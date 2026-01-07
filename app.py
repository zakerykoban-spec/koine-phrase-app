# app.py — Koine Flashcards (mobile-first, mastery, Greek parsing labels/values, no night mode)
# Deck schema: JSON list of objects like:
# {
#   "id":"0001",
#   "koine":"...",
#   "english":"...",
#   "tag":"...",
#   "audio":"assets/a.mp3",
#   "image":"assets/i.jpg",
#   "meta": { ... }   # can be English or Greek keys; app normalizes to Greek display
# }

import json
import random
from pathlib import Path

import streamlit as st

# -------------------------
# Paths
# -------------------------
APP_DIR = Path(__file__).parent
DECKS_DIR = APP_DIR / "decks"
FAV_FILE = APP_DIR / "favorites.json"

# -------------------------
# Page
# -------------------------
st.set_page_config(
    page_title="Διάλογοι Ἑλληνιστί",
    layout="wide",
    initial_sidebar_state="collapsed",  # iPhone-friendly
)
st.title("Διάλογοι Ἑλληνιστί")
st.caption("Mobile-first Koine flashcards • mastery session • favorites • πλήρης ἀνάλυσις (Greek labels)")

# -------------------------
# Styling (single day theme)
# -------------------------
st.markdown(
    """
    <style>
    .stApp { background-color: #fafafa; }

    .card {
        max-width: 980px;
        margin: 0 auto;
        padding: 14px 14px;
        background: rgba(255,255,255,0.98);
        border-radius: 18px;
        box-shadow: 0 10px 28px rgba(0,0,0,0.08);
        border: 1px solid rgba(0,0,0,0.06);
    }

    .greek {
        font-family: "Gentium Plus","Noto Serif",serif;
        font-weight: 650;
        text-align: center;
        margin-top: 10px;
        color: #1f1f1f;
        font-size: 76px;
        line-height: 1.15;
        word-wrap: break-word;
    }

    .eng {
        text-align: center;
        margin-top: 10px;
        color: #2b2b2b;
        opacity: 0.95;
        font-size: 44px;
        line-height: 1.25;
        word-wrap: break-word;
    }

    .parseWrap {
        margin-top: 14px;
        padding: 12px 14px;
        border-radius: 14px;
        background: rgba(245, 243, 238, 0.75);
        border: 1px solid rgba(0,0,0,0.06);
    }

    .parseTitle {
        font-size: 22px;
        font-weight: 650;
        color: #1f1f1f;
        margin-bottom: 8px;
        text-align: center;
    }

    table.parseTable {
        width: 100%;
        border-collapse: collapse;
        font-size: 18px;
        line-height: 1.3;
        color: #1f1f1f;
    }

    table.parseTable td {
        padding: 6px 8px;
        vertical-align: top;
        border-top: 1px solid rgba(0,0,0,0.06);
    }

    table.parseTable td.key {
        width: 34%;
        font-weight: 650;
        color: #333;
        white-space: nowrap;
    }

    table.parseTable td.val { color: #222; }

    .muted { text-align:center; opacity:0.7; font-size:14px; margin-top:8px; }

    @media (max-width: 640px) {
        .greek { font-size: 54px; }
        .eng { font-size: 28px; }
        .parseTitle { font-size: 20px; }
        table.parseTable { font-size: 16px; }

        div.stButton>button {
            padding: 0.85rem 0.85rem !important;
            font-size: 1.05rem !important;
            border-radius: 14px !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------
# Utilities
# -------------------------
def safe_load_json(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def safe_write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp.replace(path)

def deck_label_from_filename(fn: str) -> str:
    base = fn.replace(".json", "").replace("_", " ")
    return " ".join([w.capitalize() if not w.isdigit() else w for w in base.split()])

def load_deck_file(path: Path):
    raw = safe_load_json(path)
    if not isinstance(raw, list):
        raise ValueError(f"{path.name} must be a JSON list.")
    deck_name = path.stem
    out = []
    for i, p in enumerate(raw):
        if not isinstance(p, dict):
            continue
        p = dict(p)

        base_id = str(p.get("id") or f"{i+1:04d}").strip() or f"{i+1:04d}"
        p["id"] = f"{deck_name}:{base_id}"
        p["deck"] = deck_name

        p["koine"] = (p.get("koine") or "").strip()
        p["english"] = (p.get("english") or "").strip()
        p["tag"] = (p.get("tag") or "").strip() or None
        p["audio"] = (p.get("audio") or "").strip() or None
        p["image"] = (p.get("image") or "").strip() or None

        if "meta" in p and p["meta"] is not None and not isinstance(p["meta"], dict):
            p["meta"] = None

        if p["koine"] or p["english"]:
            out.append(p)
    return out

# -------------------------
# Greek parsing normalization (keys + values)
# -------------------------
KEY_MAP = {
    # lemma
    "lemma": "λέμμα",
    "lem": "λέμμα",
    "λῆμμα": "λέμμα",
    "λέμμα": "λέμμα",

    # part of speech
    "pos": "μέρος λόγου",
    "part_of_speech": "μέρος λόγου",
    "μέρος λόγου": "μέρος λόγου",

    # core morph
    "gender": "γένος",
    "γένος": "γένος",

    "case": "πτῶσις",
    "πτῶσις": "πτῶσις",

    "number": "ἀριθμός",
    "ἀριθμός": "ἀριθμός",

    "person": "πρόσωπον",
    "πρόσωπον": "πρόσωπον",

    "tense": "χρόνος",
    "χρόνος": "χρόνος",

    "aspect": "ἄσπεκτος",
    "ἄσπεκτος": "ἄσπεκτος",

    "mood": "ἔγκλισις",
    "ἔγκλισις": "ἔγκλισις",

    "voice": "φωνή",
    "φωνή": "φωνή",

    "degree": "βαθμός",
    "βαθμός": "βαθμός",

    "note": "σχόλιον",
    "σχόλιον": "σχόλιον",

    # optional extra fields you may add
    "dialect": "διάλεκτος",
    "διάλεκτος": "διάλεκτος",
}

VALUE_MAP = {
    "γένος": {
        "masculine": "ἀρσενικόν",
        "feminine": "θηλυκόν",
        "neuter": "οὐδέτερον",
        "m": "ἀρσενικόν",
        "f": "θηλυκόν",
        "n": "οὐδέτερον",
        "ἀρσενικόν": "ἀρσενικόν",
        "θηλυκόν": "θηλυκόν",
        "οὐδέτερον": "οὐδέτερον",
    },
    "ἀριθμός": {
        "singular": "ἑνικός",
        "plural": "πληθυντικός",
        "dual": "δυϊκός",
        "sg": "ἑνικός",
        "pl": "πληθυντικός",
        "ἑνικός": "ἑνικός",
        "πληθυντικός": "πληθυντικός",
        "δυϊκός": "δυϊκός",
    },
    "πτῶσις": {
        "nominative": "ὀνομαστική",
        "genitive": "γενική",
        "dative": "δοτική",
        "accusative": "αἰτιατική",
        "vocative": "κλητική",
        "nom": "ὀνομαστική",
        "gen": "γενική",
        "dat": "δοτική",
        "acc": "αἰτιατική",
        "voc": "κλητική",
        "ὀνομαστική": "ὀνομαστική",
        "γενική": "γενική",
        "δοτική": "δοτική",
        "αἰτιατική": "αἰτιατική",
        "κλητική": "κλητική",
    },
    "πρόσωπον": {
        "1": "πρῶτον",
        "2": "δεύτερον",
        "3": "τρίτον",
        "first": "πρῶτον",
        "second": "δεύτερον",
        "third": "τρίτον",
        "1st": "πρῶτον",
        "2nd": "δεύτερον",
        "3rd": "τρίτον",
        "πρῶτον": "πρῶτον",
        "δεύτερον": "δεύτερον",
        "τρίτον": "τρίτον",
    },
    "ἔγκλισις": {
        "indicative": "ὁριστική",
        "subjunctive": "ὑποτακτική",
        "optative": "εὐκτική",
        "imperative": "προστακτική",
        "infinitive": "ἀπαρέμφατον",
        "participle": "μετοχή",
        "ὁριστική": "ὁριστική",
        "ὑποτακτική": "ὑποτακτική",
        "εὐκτική": "εὐκτική",
        "προστακτική": "προστακτική",
        "ἀπαρέμφατον": "ἀπαρέμφατον",
        "μετοχή": "μετοχή",
    },
    "φωνή": {
        "active": "ἐνεργητική",
        "middle": "μέση",
        "passive": "παθητική",
        "act": "ἐνεργητική",
        "mid": "μέση",
        "pass": "παθητική",
        "ἐνεργητική": "ἐνεργητική",
        "μέση": "μέση",
        "παθητική": "παθητική",
    },
    "χρόνος": {
        "present": "ἐνεστώς",
        "imperfect": "παρατατικός",
        "aorist": "ἀόριστος",
        "perfect": "παρακείμενος",
        "pluperfect": "ὑπερσυντέλικος",
        "future": "μέλλων",
        "pres": "ἐνεστώς",
        "impf": "παρατατικός",
        "aor": "ἀόριστος",
        "perf": "παρακείμενος",
        "plup": "ὑπερσυντέλικος",
        "fut": "μέλλων",
        "ἐνεστώς": "ἐνεστώς",
        "παρατατικός": "παρατατικός",
        "ἀόριστος": "ἀόριστος",
        "παρακείμενος": "παρακείμενος",
        "ὑπερσυντέλικος": "ὑπερσυντέλικος",
        "μέλλων": "μέλλων",
    },
}

def _normalize_value(display_key: str, v):
    mapper = VALUE_MAP.get(display_key)
    if mapper is None:
        return v

    def norm_one(x):
        xs = str(x).strip()
        xl = xs.lower()
        return mapper.get(xl, mapper.get(xs, xs))

    if isinstance(v, (list, tuple)):
        return ", ".join(norm_one(x) for x in v)
    return norm_one(v)

def normalize_meta(meta: dict) -> dict:
    """Normalize meta keys to Greek display keys and normalize values where we have mappings."""
    if not meta or not isinstance(meta, dict):
        return {}

    out = {}
    for k, v in meta.items():
        if v is None:
            continue
        dk = KEY_MAP.get(str(k).strip(), str(k).strip())
        out[dk] = _normalize_value(dk, v)
    return out

# -------------------------
# Parsing renderer (complete; Greek-first ordering)
# -------------------------
def render_parse_meta(meta: dict) -> str:
    if not meta or not isinstance(meta, dict):
        return ""

    preferred = [
        "λέμμα",
        "μέρος λόγου",
        "γένος",
        "πτῶσις",
        "ἀριθμός",
        "πρόσωπον",
        "χρόνος",
        "ἄσπεκτος",
        "ἔγκλισις",
        "φωνή",
        "βαθμός",
        "διάλεκτος",
        "σχόλιον",
    ]

    rows = []
    used = set()

    def add_row(k):
        v = meta.get(k)
        if v is None or v == "":
            return
        used.add(k)
        rows.append((k, str(v)))

    for k in preferred:
        if k in meta:
            add_row(k)

    for k in sorted(meta.keys(), key=lambda x: str(x)):
        if k not in used:
            add_row(k)

    if not rows:
        return ""

    def esc(s: str) -> str:
        return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    html_rows = "\n".join(
        f"<tr><td class='key'>{esc(k)}</td><td class='val'>{esc(v)}</td></tr>"
        for k, v in rows
    )

    return f"""
    <div class='parseWrap'>
      <div class='parseTitle'>Ἡ ἀνάλυσις</div>
      <table class='parseTable'>
        {html_rows}
      </table>
    </div>
    """

# -------------------------
# Favorites
# -------------------------
def load_favs():
    if not FAV_FILE.exists():
        return set()
    try:
        data = safe_load_json(FAV_FILE)
        return set(map(str, data)) if isinstance(data, list) else set()
    except Exception:
        return set()

def save_favs(favs):
    safe_write_json(FAV_FILE, sorted(list(favs)))

def toggle_fav(pid: str):
    if pid in st.session_state.favs:
        st.session_state.favs.remove(pid)
    else:
        st.session_state.favs.add(pid)
    save_favs(st.session_state.favs)

# -------------------------
# Session state
# -------------------------
if "favs" not in st.session_state:
    st.session_state.favs = load_favs()

if "selected_id" not in st.session_state:
    st.session_state.selected_id = None
if "revealed" not in st.session_state:
    st.session_state.revealed = False

# settings (mobile accessible)
if "selected_decks" not in st.session_state:
    st.session_state.selected_decks = None
if "q" not in st.session_state:
    st.session_state.q = ""
if "flashcard_mode" not in st.session_state:
    st.session_state.flashcard_mode = True
if "auto_hide" not in st.session_state:
    st.session_state.auto_hide = True
if "show_media" not in st.session_state:
    st.session_state.show_media = True
if "show_parsing" not in st.session_state:
    st.session_state.show_parsing = True

# mastery
if "in_session" not in st.session_state:
    st.session_state.in_session = False
if "queue" not in st.session_state:
    st.session_state.queue = []
if "session_correct" not in st.session_state:
    st.session_state.session_correct = set()
if "session_incorrect" not in st.session_state:
    st.session_state.session_incorrect = set()
if "repeat_events" not in st.session_state:
    st.session_state.repeat_events = 0
if "session_total" not in st.session_state:
    st.session_state.session_total = 0
if "finished_summary" not in st.session_state:
    st.session_state.finished_summary = None
if "last_session_ids" not in st.session_state:
    st.session_state.last_session_ids = []

# -------------------------
# Discover decks
# -------------------------
if not DECKS_DIR.exists():
    st.error("Missing `decks/` folder. Put JSON deck files in `decks/` next to app.py.")
    st.stop()

deck_files = sorted([p for p in DECKS_DIR.glob("*.json") if p.is_file()])
if not deck_files:
    st.error("No deck files found in `decks/`.")
    st.stop()

deck_options = {deck_label_from_filename(p.name): p for p in deck_files}
deck_labels = list(deck_options.keys())

if st.session_state.selected_decks is None:
    st.session_state.selected_decks = [deck_labels[0]]

# -------------------------
# Mobile MAIN settings
# -------------------------
with st.expander("Decks & Settings", expanded=False):
    st.session_state.selected_decks = st.multiselect(
        "Decks",
        options=deck_labels,
        default=st.session_state.selected_decks,
    )
    st.session_state.q = st.text_input("Search (Greek or English)", value=st.session_state.q)

    st.session_state.flashcard_mode = st.toggle("Flashcard mode", value=st.session_state.flashcard_mode)
    st.session_state.auto_hide = st.toggle("Auto-hide on Next", value=st.session_state.auto_hide)

    repeat_after = st.slider("Repeat incorrect after N cards", 0, 8, 3)

    st.session_state.show_media = st.toggle("Show media", value=st.session_state.show_media)
    st.session_state.show_parsing = st.toggle("Show parsing on Reveal", value=st.session_state.show_parsing)

    st.caption(f"⭐ Favorites: {len(st.session_state.favs)}")

if not st.session_state.selected_decks:
    st.warning("Select at least one deck.")
    st.stop()

# -------------------------
# Load selected decks
# -------------------------
phrases = []
errors = []
for lbl in st.session_state.selected_decks:
    try:
        phrases.extend(load_deck_file(deck_options[lbl]))
    except Exception as e:
        errors.append(f"{lbl}: {e}")

if errors:
    st.error("Deck load errors:\n\n" + "\n".join(errors))
    st.stop()

def matches_search(p):
    if st.session_state.q.strip():
        needle = st.session_state.q.strip().lower()
        return needle in (p.get("koine", "").lower()) or needle in (p.get("english", "").lower())
    return True

filtered = [p for p in phrases if matches_search(p)]
if not filtered:
    st.info("No matches. Clear search.")
    st.stop()

filtered_ids = [p["id"] for p in filtered]
id_to_phrase = {p["id"]: p for p in filtered}

if st.session_state.selected_id not in id_to_phrase:
    st.session_state.selected_id = filtered_ids[0]

def browse_next():
    i = filtered_ids.index(st.session_state.selected_id)
    st.session_state.selected_id = filtered_ids[(i + 1) % len(filtered_ids)]
    if st.session_state.auto_hide:
        st.session_state.revealed = False

def browse_prev():
    i = filtered_ids.index(st.session_state.selected_id)
    st.session_state.selected_id = filtered_ids[(i - 1) % len(filtered_ids)]
    if st.session_state.auto_hide:
        st.session_state.revealed = False

# -------------------------
# Mastery helpers
# -------------------------
def end_session(store_summary=True):
    if store_summary:
        st.session_state.finished_summary = {
            "total": st.session_state.session_total,
            "correct": len(st.session_state.session_correct),
            "incorrect": len(st.session_state.session_incorrect),
            "repeat_events": st.session_state.repeat_events,
        }
    st.session_state.in_session = False
    st.session_state.queue = []
    st.session_state.revealed = False

def start_session(ids):
    ids = list(ids)
    if not ids:
        return
    st.session_state.queue = ids[:]
    random.shuffle(st.session_state.queue)
    st.session_state.in_session = True
    st.session_state.session_correct = set()
    st.session_state.session_incorrect = set()
    st.session_state.repeat_events = 0
    st.session_state.session_total = len(st.session_state.queue)
    st.session_state.finished_summary = None
    st.session_state.last_session_ids = ids[:]
    st.session_state.revealed = False
    st.session_state.selected_id = st.session_state.queue[0]

def reshuffle_session():
    if st.session_state.in_session and st.session_state.queue:
        random.shuffle(st.session_state.queue)
        st.session_state.selected_id = st.session_state.queue[0]
        st.session_state.revealed = False

def mark_correct(pid: str):
    st.session_state.session_correct.add(pid)
    st.session_state.session_incorrect.discard(pid)

    if st.session_state.in_session:
        st.session_state.queue = [x for x in st.session_state.queue if x != pid]
        st.session_state.revealed = False
        if st.session_state.queue:
            st.session_state.selected_id = st.session_state.queue[0]
        else:
            end_session(store_summary=True)
    else:
        browse_next()

def mark_incorrect(pid: str, repeat_after_n: int):
    st.session_state.session_incorrect.add(pid)
    st.session_state.session_correct.discard(pid)

    if st.session_state.in_session:
        st.session_state.repeat_events += 1
        qlist = [x for x in st.session_state.queue if x != pid]
        insert_at = min(repeat_after_n, len(qlist))
        qlist.insert(insert_at, pid)
        st.session_state.queue = qlist
        st.session_state.revealed = False
        st.session_state.selected_id = st.session_state.queue[0]
    else:
        browse_next()

# If in session, current card = queue head
if st.session_state.in_session and st.session_state.queue:
    if st.session_state.queue[0] not in id_to_phrase:
        end_session(store_summary=True)
    else:
        st.session_state.selected_id = st.session_state.queue[0]

# -------------------------
# Session controls (top)
# -------------------------
all_for_session = filtered_ids
favs_for_session = [pid for pid in all_for_session if pid in st.session_state.favs]

s1, s2, s3, s4 = st.columns(4)
with s1:
    if st.button("▶ Session (All)", use_container_width=True):
        start_session(all_for_session)
        st.rerun()
with s2:
    if st.button("⭐ Session (Favs)", use_container_width=True):
        if not favs_for_session:
            st.info("No favorites in the current search.")
        else:
            start_session(favs_for_session)
            st.rerun()
with s3:
    if st.button("🔀 Reshuffle", use_container_width=True):
        reshuffle_session()
        st.rerun()
with s4:
    if st.button("⏹ End", use_container_width=True):
        end_session(store_summary=True)
        st.rerun()

if st.session_state.in_session:
    total = max(1, st.session_state.session_total)
    done = total - len(st.session_state.queue)
    st.progress(done / total)
    st.caption(
        f"Remaining **{len(st.session_state.queue)}** • "
        f"Correct **{len(st.session_state.session_correct)}** • "
        f"Incorrect **{len(st.session_state.session_incorrect)}** • "
        f"Repeats **{st.session_state.repeat_events}**"
    )

if (not st.session_state.in_session) and st.session_state.finished_summary:
    s = st.session_state.finished_summary
    total = max(1, s["total"])
    accuracy = round(100 * (s["correct"] / total), 1)

    st.success("✅ Session complete")
    a, b, c, d = st.columns(4)
    a.metric("Total", s["total"])
    b.metric("Correct", s["correct"])
    c.metric("Incorrect", s["incorrect"])
    d.metric("Repeats", s["repeat_events"])
    st.caption(f"Accuracy: **{accuracy}%**")

    r1, r2 = st.columns(2)
    with r1:
        if st.button("🔁 Study missed only", use_container_width=True):
            missed = list(st.session_state.session_incorrect)
            if missed:
                start_session(missed)
                st.rerun()
            else:
                st.info("No missed items.")
    with r2:
        if st.button("▶ Restart full session", use_container_width=True):
            if st.session_state.last_session_ids:
                start_session(st.session_state.last_session_ids)
                st.rerun()

# -------------------------
# Card (mobile flow: Reveal under Greek; actions at bottom)
# -------------------------
selected = id_to_phrase[st.session_state.selected_id]

greek = (selected.get("koine") or "").strip()
eng = (selected.get("english") or "").strip()

raw_meta = selected.get("meta") if isinstance(selected.get("meta"), dict) else None
meta = normalize_meta(raw_meta) if raw_meta else None

audio_rel = (selected.get("audio") or "").strip()
image_rel = (selected.get("image") or "").strip()
audio_path = (APP_DIR / audio_rel) if audio_rel else None
image_path = (APP_DIR / image_rel) if image_rel else None

st.markdown("<div class='card'>", unsafe_allow_html=True)

if st.session_state.show_media:
    if image_path and image_path.exists():
        st.image(str(image_path), use_container_width=True)
    elif image_rel:
        st.markdown("<div class='muted'>Image path not found.</div>", unsafe_allow_html=True)

    if audio_path and audio_path.exists():
        st.audio(str(audio_path))
    elif audio_rel:
        st.markdown("<div class='muted'>Audio path not found.</div>", unsafe_allow_html=True)

# Greek
st.markdown(f"<div class='greek'>{greek or '—'}</div>", unsafe_allow_html=True)

# Reveal directly under Greek
if st.button("👁 Reveal / Hide", use_container_width=True):
    st.session_state.revealed = not st.session_state.revealed
    st.rerun()

show_answer = (not st.session_state.flashcard_mode) or st.session_state.revealed

if show_answer:
    if eng:
        st.markdown(f"<div class='eng'>{eng}</div>", unsafe_allow_html=True)
    if st.session_state.show_parsing and meta:
        st.markdown(render_parse_meta(meta), unsafe_allow_html=True)

# Action bar (all the “movement” buttons stay right under answer/parsing)
b1, b2, b3, b4, b5 = st.columns([0.18, 0.18, 0.22, 0.22, 0.20])

with b1:
    if st.button("⬅", use_container_width=True):
        if st.session_state.in_session:
            st.session_state.revealed = not st.session_state.revealed
        else:
            browse_prev()
        st.rerun()

with b2:
    if st.button("➡", use_container_width=True):
        if st.session_state.in_session and st.session_state.queue:
            pid = st.session_state.selected_id
            st.session_state.queue = [x for x in st.session_state.queue if x != pid] + [pid]
            if st.session_state.auto_hide:
                st.session_state.revealed = False
        else:
            browse_next()
        st.rerun()

with b3:
    if st.button("✅ Correct", use_container_width=True):
        mark_correct(st.session_state.selected_id)
        st.rerun()

with b4:
    if st.button("❌ Incorrect", use_container_width=True):
        mark_incorrect(st.session_state.selected_id, repeat_after_n=repeat_after)
        st.rerun()

with b5:
    is_fav = st.session_state.selected_id in st.session_state.favs
    if st.button("★" if is_fav else "☆", use_container_width=True):
        toggle_fav(st.session_state.selected_id)
        st.rerun()

st.markdown("</div>", unsafe_allow_html=True)

# -------------------------
# Jump list (optional)
# -------------------------
with st.expander("Jump list", expanded=False):
    labels = [f'{p["id"]} — {p.get("koine","")[:60]}' for p in filtered]
    label_to_id = {labels[i]: filtered[i]["id"] for i in range(len(filtered))}
    current_label = next((lab for lab in labels if label_to_id[lab] == st.session_state.selected_id), labels[0])
    idx = labels.index(current_label)

    choice = st.selectbox("Jump to phrase", labels, index=idx)
    chosen = label_to_id[choice]
    if chosen != st.session_state.selected_id:
        st.session_state.selected_id = chosen
        if st.session_state.auto_hide:
            st.session_state.revealed = False
        if st.session_state.in_session:
            end_session(store_summary=True)
        st.rerun()

st.caption(
    f'Deck: {selected.get("deck","—")} • '
    f'ID: {selected.get("id","")} • '
    f'Tag: {selected.get("tag") or "—"}'
)
