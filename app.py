# app.py — Koine Flashcards (mobile-first, Streamlit Cloud-safe)
# Schema: each deck file is a JSON list of objects with keys like:
# { "id": "0001", "koine": "...", "english": "...", "tag": "...", "audio": "assets/a.mp3", "image":"assets/i.jpg", "meta": {...} }

import json
import os
import random
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


import streamlit as st


# -------------------------
# Config / Paths
# -------------------------
APP_DIR = Path(__file__).parent
DECKS_DIR = APP_DIR / "decks"
FAV_FILE = APP_DIR / "favorites.json"
STATS_FILE = APP_DIR / "stats.json"


# -------------------------
# Password Gate (SAFE)
# -------------------------
# Streamlit Cloud: set APP_PASSWORD in App -> Settings -> Secrets
# Local: either secrets.toml OR environment variable APP_PASSWORD
def get_app_password() -> str:
    try:
        pw = st.secrets.get("APP_PASSWORD", "")
    except Exception:
        pw = ""
    if not pw:
        pw = os.getenv("APP_PASSWORD", "")
    return (pw or "").strip()


def password_gate():
    pw = get_app_password()
    if not pw:
        return  # dev / open mode

    # keep gate state stable across reruns
    if "auth_ok" not in st.session_state:
        st.session_state.auth_ok = False

    if st.session_state.auth_ok:
        return

    st.markdown("### 🔒 Password")
    entered = st.text_input("Enter password", type="password")
    if entered and entered == pw:
        st.session_state.auth_ok = True
        st.rerun()
    st.stop()


password_gate()


# -------------------------
# Page config
# -------------------------
st.set_page_config(
    page_title="Διάλογοι Ἑλληνιστί",
    layout="wide",
    initial_sidebar_state="collapsed",  # better for iPhone
)


# -------------------------
# Styling (mobile-first)
# -------------------------
GREEK_SIZE_PX_DESKTOP = 80
ENGLISH_SIZE_PX_DESKTOP = 46
PARSE_TITLE_PX_DESKTOP = 24

GREEK_SIZE_PX_MOBILE = 54
ENGLISH_SIZE_PX_MOBILE = 28
PARSE_TITLE_PX_MOBILE = 20

CENTER_MAX_WIDTH_PX = 980

st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: #fafafa;
    }}

    section[data-testid="stSidebar"] {{
        background-color: rgba(245, 243, 238, 0.97);
    }}

    /* Center card */
    .centerWrap {{
        max-width: {CENTER_MAX_WIDTH_PX}px;
        margin: 0 auto;
        padding: 18px 18px;
        background: rgba(255, 255, 255, 0.98);
        border-radius: 20px;
        box-shadow: 0 10px 28px rgba(0,0,0,0.08);
    }}

    .subtle {{
        text-align:center;
        opacity: 0.75;
        margin-top: 8px;
        margin-bottom: 0px;
        font-size: 14px;
    }}

    .greekBig {{
        font-family: "Gentium Plus", "Noto Serif", serif;
        font-size: {GREEK_SIZE_PX_DESKTOP}px;
        line-height: 1.18;
        font-weight: 650;
        text-align: center;
        margin-top: 14px;
        color: #1f1f1f;
        word-wrap: break-word;
    }}

    .engText {{
        font-size: {ENGLISH_SIZE_PX_DESKTOP}px;
        line-height: 1.35;
        text-align: center;
        margin-top: 12px;
        color: #2b2b2b;
        opacity: 0.95;
        word-wrap: break-word;
    }}

    .parseWrap {{
        margin-top: 14px;
        padding: 12px 14px;
        border-radius: 14px;
        background: rgba(245, 243, 238, 0.75);
        border: 1px solid rgba(0,0,0,0.06);
    }}

    .parseTitle {{
        font-size: {PARSE_TITLE_PX_DESKTOP}px;
        font-weight: 650;
        color: #1f1f1f;
        margin-bottom: 8px;
        text-align: center;
    }}

    table.parseTable {{
        width: 100%;
        border-collapse: collapse;
        font-size: 18px;
        line-height: 1.3;
    }}

    table.parseTable td {{
        padding: 6px 8px;
        vertical-align: top;
        border-top: 1px solid rgba(0,0,0,0.06);
    }}

    table.parseTable td.key {{
        width: 34%;
        font-weight: 650;
        color: #333;
        white-space: nowrap;
    }}

    table.parseTable td.val {{
        color: #222;
    }}

    /* Mobile tweaks */
    @media (max-width: 640px) {{
        .centerWrap {{
            padding: 14px 14px;
            border-radius: 18px;
        }}
        .greekBig {{
            font-size: {GREEK_SIZE_PX_MOBILE}px;
            margin-top: 10px;
        }}
        .engText {{
            font-size: {ENGLISH_SIZE_PX_MOBILE}px;
        }}
        .parseTitle {{
            font-size: {PARSE_TITLE_PX_MOBILE}px;
        }}
        table.parseTable {{
            font-size: 16px;
        }}
        /* Make Streamlit buttons bigger on mobile */
        div.stButton>button {{
            padding: 0.85rem 0.85rem !important;
            font-size: 1.05rem !important;
            border-radius: 14px !important;
        }}
        div[data-testid="stVerticalBlock"] > div:has(> div.stButton) {{
            margin-top: 4px;
            margin-bottom: 4px;
        }}
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Διάλογοι Ἑλληνιστί")
st.caption("Mobile-first Koine flashcards • mastery session • favorites • media-ready")


# -------------------------
# JSON helpers
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


# -------------------------
# Deck loading
# -------------------------
def deck_label_from_filename(fn: str) -> str:
    base = fn.replace(".json", "").replace("_", " ")
    return " ".join([w.capitalize() if not w.isdigit() else w for w in base.split()])


def load_deck_file(path: Path) -> List[dict]:
    raw = safe_load_json(path)
    if not isinstance(raw, list):
        raise ValueError(f"{path.name} must be a JSON list of objects.")

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
# Parsing meta renderer
# -------------------------
def render_parse_meta(meta: dict) -> str:
    if not meta or not isinstance(meta, dict):
        return ""

    preferred = [
        "lemma",
        "pos",
        "γένος",
        "πτῶσις",
        "ἀριθμός",
        "πρόσωπον",
        "χρόνος",
        "ἔγκλισις",
        "φωνή",
        "βαθμός",
        "ambiguous",
        "note",
    ]

    rows = []
    used = set()

    def add_row(k):
        v = meta.get(k)
        if v is None:
            return
        used.add(k)
        if isinstance(v, (list, tuple)):
            v = ", ".join(map(str, v))
        else:
            v = str(v)
        rows.append((k, v))

    for k in preferred:
        if k in meta:
            add_row(k)
    for k in sorted(meta.keys()):
        if k not in used:
            add_row(k)

    if not rows:
        return ""

    def esc(s: str) -> str:
        return (
            str(s)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    html_rows = "\n".join(
        f"<tr><td class='key'>{esc(k)}</td><td class='val'>{esc(v)}</td></tr>"
        for k, v in rows
    )

    return f"""
    <div class='parseWrap'>
      <div class='parseTitle'>Parsing (ἡ ἀνάλυσις)</div>
      <table class='parseTable'>
        {html_rows}
      </table>
    </div>
    """


# -------------------------
# Favorites (persistent)
# -------------------------
def load_favs() -> Set[str]:
    if not FAV_FILE.exists():
        return set()
    try:
        data = safe_load_json(FAV_FILE)
        return set(map(str, data)) if isinstance(data, list) else set()
    except Exception:
        return set()


def save_favs(favs: Set[str]):
    safe_write_json(FAV_FILE, sorted(list(favs)))


def toggle_fav(pid: str):
    if pid in st.session_state.favs:
        st.session_state.favs.remove(pid)
    else:
        st.session_state.favs.add(pid)
    save_favs(st.session_state.favs)


# -------------------------
# Lifetime stats (persistent)
# -------------------------
# stats.json shape:
# { "by_id": { "<phrase_id>": {"correct": 12, "incorrect": 3} } }
def load_stats() -> Dict:
    if not STATS_FILE.exists():
        return {"by_id": {}}
    try:
        data = safe_load_json(STATS_FILE)
        if not isinstance(data, dict):
            return {"by_id": {}}
        data.setdefault("by_id", {})
        return data
    except Exception:
        return {"by_id": {}}


def save_stats(stats: Dict):
    safe_write_json(STATS_FILE, stats)


def bump_stat(pid: str, key: str):
    stats = st.session_state.stats
    by_id = stats.setdefault("by_id", {})
    rec = by_id.setdefault(pid, {"correct": 0, "incorrect": 0})
    rec[key] = int(rec.get(key, 0)) + 1
    save_stats(stats)


# -------------------------
# Session state init
# -------------------------
def ss_init():
    if "favs" not in st.session_state:
        st.session_state.favs = load_favs()
    if "stats" not in st.session_state:
        st.session_state.stats = load_stats()

    if "selected_id" not in st.session_state:
        st.session_state.selected_id = None
    if "revealed" not in st.session_state:
        st.session_state.revealed = False

    # mastery session
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

    # UI toggles
    if "show_media" not in st.session_state:
        st.session_state.show_media = True
    if "audio_on" not in st.session_state:
        st.session_state.audio_on = True
    if "show_parsing" not in st.session_state:
        st.session_state.show_parsing = True

    if "flashcard_mode" not in st.session_state:
        st.session_state.flashcard_mode = True
    if "auto_hide_on_next" not in st.session_state:
        st.session_state.auto_hide_on_next = True


ss_init()


# -------------------------
# Discover decks
# -------------------------
if not DECKS_DIR.exists():
    st.error("Missing `decks/` folder. Create it inside your app folder and add one or more *.json deck files.")
    st.stop()

deck_files = sorted([p for p in DECKS_DIR.glob("*.json") if p.is_file()])
if not deck_files:
    st.error("No deck files found. Add at least one JSON deck file in `decks/`.")
    st.stop()

deck_options = {deck_label_from_filename(p.name): p for p in deck_files}
deck_labels = list(deck_options.keys())


# -------------------------
# Sidebar (nice on desktop; not required on iPhone)
# -------------------------
with st.sidebar:
    st.header("Koine Tools")

    selected_deck_labels = st.multiselect(
        "Load decks",
        options=deck_labels,
        default=[deck_labels[0]],
    )
    if not selected_deck_labels:
        st.warning("Select at least one deck.")
        st.stop()

    st.divider()
    st.subheader("Settings")
    q = st.text_input("Search (Greek or English)", "")
    fav_only = st.checkbox("Favorites only", value=False)

    st.session_state.flashcard_mode = st.toggle("Flashcard mode", value=st.session_state.flashcard_mode)
    st.session_state.auto_hide_on_next = st.toggle("Auto-hide on Next", value=st.session_state.auto_hide_on_next)

    repeat_after = st.slider("Repeat incorrect after N cards", 0, 8, 3)
    st.session_state.show_media = st.toggle("Show media", value=st.session_state.show_media)
    st.session_state.show_parsing = st.toggle("Show parsing on Reveal", value=st.session_state.show_parsing)

    st.divider()
    st.subheader("Quick stats")
    st.write(f"Favorites: **{len(st.session_state.favs)}**")
    st.write(f"Correct (session): **{len(st.session_state.session_correct)}**")
    st.write(f"Incorrect (session): **{len(st.session_state.session_incorrect)}**")
    st.write(f"Queue remaining: **{len(st.session_state.queue)}**")

    if st.button("🧹 Reset session", use_container_width=True):
        st.session_state.in_session = False
        st.session_state.queue = []
        st.session_state.session_correct = set()
        st.session_state.session_incorrect = set()
        st.session_state.repeat_events = 0
        st.session_state.session_total = 0
        st.session_state.revealed = False
        st.session_state.finished_summary = None
        st.rerun()


selected_deck_paths = [deck_options[lbl] for lbl in selected_deck_labels]


# -------------------------
# Load decks
# -------------------------
phrases: List[dict] = []
load_errors = []
for path in selected_deck_paths:
    try:
        phrases.extend(load_deck_file(path))
    except Exception as e:
        load_errors.append(f"{path.name}: {e}")

if load_errors:
    st.error("Some decks failed to load:\n\n" + "\n".join(load_errors))
    st.stop()

if not phrases:
    st.error("Loaded decks contain no usable entries (need koine or english text).")
    st.stop()


# -------------------------
# Filter
# -------------------------
def match(p: dict) -> bool:
    if fav_only and p["id"] not in st.session_state.favs:
        return False
    if q.strip():
        needle = q.strip().lower()
        return (needle in (p.get("koine") or "").lower()) or (needle in (p.get("english") or "").lower())
    return True


filtered = [p for p in phrases if match(p)]
if not filtered:
    st.info("No matches. Clear search/filters.")
    st.stop()

id_to_phrase = {p["id"]: p for p in filtered}
filtered_ids = [p["id"] for p in filtered]


def ensure_selected_valid():
    if st.session_state.in_session and st.session_state.queue:
        pid = st.session_state.queue[0]
        if pid in id_to_phrase:
            st.session_state.selected_id = pid
            return

    if st.session_state.selected_id in id_to_phrase:
        return

    st.session_state.selected_id = filtered_ids[0]


ensure_selected_valid()
selected = id_to_phrase[st.session_state.selected_id]


# -------------------------
# Mastery session
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


def start_mastery_session(ids: List[str]):
    st.session_state.queue = list(ids)
    random.shuffle(st.session_state.queue)

    st.session_state.session_correct = set()
    st.session_state.session_incorrect = set()
    st.session_state.repeat_events = 0
    st.session_state.session_total = len(st.session_state.queue)
    st.session_state.finished_summary = None

    st.session_state.in_session = True
    st.session_state.revealed = False

    if st.session_state.queue:
        st.session_state.selected_id = st.session_state.queue[0]


def reshuffle_session():
    if st.session_state.in_session and st.session_state.queue:
        random.shuffle(st.session_state.queue)
        st.session_state.selected_id = st.session_state.queue[0]
        st.session_state.revealed = False


def browse_next():
    i = filtered_ids.index(st.session_state.selected_id)
    st.session_state.selected_id = filtered_ids[(i + 1) % len(filtered_ids)]
    if st.session_state.auto_hide_on_next:
        st.session_state.revealed = False


def browse_prev():
    i = filtered_ids.index(st.session_state.selected_id)
    st.session_state.selected_id = filtered_ids[(i - 1) % len(filtered_ids)]
    if st.session_state.auto_hide_on_next:
        st.session_state.revealed = False


def mark_correct(pid: str):
    st.session_state.session_correct.add(pid)
    st.session_state.session_incorrect.discard(pid)
    bump_stat(pid, "correct")

    if st.session_state.in_session:
        st.session_state.queue = [x for x in st.session_state.queue if x != pid]
        st.session_state.revealed = False
        if st.session_state.queue:
            st.session_state.selected_id = st.session_state.queue[0]
        else:
            end_session(store_summary=True)
    else:
        browse_next()


def mark_incorrect(pid: str, repeat_after: int):
    st.session_state.session_incorrect.add(pid)
    st.session_state.session_correct.discard(pid)
    bump_stat(pid, "incorrect")

    if st.session_state.in_session:
        st.session_state.repeat_events += 1
        qlist = [x for x in st.session_state.queue if x != pid]
        insert_at = min(repeat_after, len(qlist))
        qlist.insert(insert_at, pid)
        st.session_state.queue = qlist
        st.session_state.revealed = False
        if st.session_state.queue:
            st.session_state.selected_id = st.session_state.queue[0]
    else:
        browse_next()


# -------------------------
# MOBILE-FRIENDLY top controls (always visible)
# -------------------------
top = st.container()
with top:
    c1, c2, c3, c4 = st.columns([0.25, 0.25, 0.25, 0.25])
    with c1:
        if st.button("▶ Session", use_container_width=True):
            start_mastery_session(filtered_ids)
            st.rerun()
    with c2:
        if st.button("🔀 Shuffle", use_container_width=True):
            reshuffle_session()
            st.rerun()
    with c3:
        if st.button("⏹ End", use_container_width=True):
            end_session(store_summary=True)
            st.rerun()
    with c4:
        is_fav = st.session_state.selected_id in st.session_state.favs
        if st.button("★" if is_fav else "☆", use_container_width=True):
            toggle_fav(st.session_state.selected_id)
            st.rerun()


# Session progress / summary
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

    st.success("✅ Τέλος τοῦ δέλτου!  (Deck/session complete)")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total", s["total"])
    m2.metric("Correct", s["correct"])
    m3.metric("Incorrect", s["incorrect"])
    m4.metric("Repeats", s["repeat_events"])
    st.caption(f"Accuracy: **{accuracy}%**")

    a, b = st.columns(2)
    with a:
        if st.button("🔁 Study missed only", use_container_width=True):
            missed = list(st.session_state.session_incorrect)
            if missed:
                start_mastery_session(missed)
                st.rerun()
            else:
                st.info("No incorrect items to review.")
    with b:
        if st.button("▶ Restart full session", use_container_width=True):
            start_mastery_session(filtered_ids)
            st.rerun()


# -------------------------
# Viewer card (mobile-first)
# -------------------------
selected = id_to_phrase[st.session_state.selected_id]

greek = (selected.get("koine") or "").strip()
eng = (selected.get("english") or "").strip()
meta = selected.get("meta") if isinstance(selected.get("meta"), dict) else None

audio_rel = (selected.get("audio") or "").strip()
image_rel = (selected.get("image") or "").strip()

audio_path = (APP_DIR / audio_rel) if audio_rel else None
image_path = (APP_DIR / image_rel) if image_rel else None

st.markdown("<div class='centerWrap'>", unsafe_allow_html=True)

# media
if st.session_state.show_media:
    if image_path and image_path.exists():
        st.image(str(image_path), use_container_width=True)
    elif image_rel:
        st.markdown("<p class='subtle'>Image path not found.</p>", unsafe_allow_html=True)

    if audio_path and audio_path.exists():
        a1, a2 = st.columns([0.35, 0.65])
        with a1:
            st.session_state.audio_on = st.toggle("Audio", value=st.session_state.audio_on)
        with a2:
            if st.session_state.audio_on:
                st.audio(str(audio_path))
    elif audio_rel:
        st.markdown("<p class='subtle'>Audio path not found.</p>", unsafe_allow_html=True)

# greek always
st.markdown(f"<div class='greekBig'>{greek or '—'}</div>", unsafe_allow_html=True)

show_answer_block = (not st.session_state.flashcard_mode) or st.session_state.revealed
if show_answer_block:
    if eng:
        st.markdown(f"<div class='engText'>{eng}</div>", unsafe_allow_html=True)
    if st.session_state.show_parsing and meta:
        st.markdown(render_parse_meta(meta), unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)


# -------------------------
# Mobile-friendly action row
# -------------------------
# On iPhone these are the main controls.
b1, b2, b3 = st.columns([0.34, 0.32, 0.34])
with b1:
    if st.button("⬅ Prev", use_container_width=True):
        if st.session_state.in_session:
            # In session, Prev toggles reveal to avoid confusing queue moves
            st.session_state.revealed = not st.session_state.revealed
        else:
            browse_prev()
        st.rerun()
with b2:
    if st.button("👁 Reveal / Hide", use_container_width=True):
        st.session_state.revealed = not st.session_state.revealed
        st.rerun()
with b3:
    if st.button("Next ➡", use_container_width=True):
        if st.session_state.in_session and st.session_state.queue:
            pid = st.session_state.selected_id
            # rotate card to end of queue
            st.session_state.queue = [x for x in st.session_state.queue if x != pid] + [pid]
            if st.session_state.auto_hide_on_next:
                st.session_state.revealed = False
        else:
            browse_next()
        st.rerun()

g1, g2 = st.columns(2)
with g1:
    if st.button("✅ Correct", use_container_width=True):
        mark_correct(st.session_state.selected_id)
        st.rerun()
with g2:
    if st.button("❌ Incorrect", use_container_width=True):
        mark_incorrect(st.session_state.selected_id, repeat_after=repeat_after)
        st.rerun()


# -------------------------
# Optional: quick jump (mobile-friendly, no sidebar required)
# -------------------------
with st.expander("Jump / Filtered list", expanded=False):
    st.write(f"Showing **{len(filtered)}** results")

    def short(s: str, n=60) -> str:
        s = s or ""
        return s if len(s) <= n else s[:n] + "…"

    labels = [
        f'{p["id"]} — [{p.get("deck","")}] {short(p.get("koine",""))}'
        for p in filtered
    ]
    label_to_id = {labels[i]: filtered[i]["id"] for i in range(len(filtered))}

    current_label = next((lab for lab in labels if label_to_id[lab] == st.session_state.selected_id), labels[0])
    idx = labels.index(current_label)

    choice = st.selectbox("Jump to phrase", labels, index=idx)
    chosen_id = label_to_id[choice]
    if chosen_id != st.session_state.selected_id:
        st.session_state.selected_id = chosen_id
        if st.session_state.auto_hide_on_next:
            st.session_state.revealed = False
        st.rerun()


# Footer
st.caption(
    f"Deck: {selected.get('deck','—')} • "
    f"ID: {selected.get('id','')} • "
    f"Tag: {selected.get('tag','—') or '—'}"
)
