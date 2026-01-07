# app.py — Koine Flashcards (mobile-first, mastery + favorites sessions + review missed + night mode)
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
    initial_sidebar_state="collapsed",
)
st.title("Διάλογοι Ἑλληνιστί")
st.caption("Mobile-first Koine flashcards • mastery session • favorites • parsing • night mode")

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
# Parsing renderer
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
        return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

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

# viewer
if "selected_id" not in st.session_state:
    st.session_state.selected_id = None
if "revealed" not in st.session_state:
    st.session_state.revealed = False

# settings
if "selected_decks" not in st.session_state:
    st.session_state.selected_decks = None
if "q" not in st.session_state:
    st.session_state.q = ""
if "fav_only" not in st.session_state:
    st.session_state.fav_only = False
if "flashcard_mode" not in st.session_state:
    st.session_state.flashcard_mode = True
if "auto_hide" not in st.session_state:
    st.session_state.auto_hide = True
if "show_media" not in st.session_state:
    st.session_state.show_media = True
if "show_parsing" not in st.session_state:
    st.session_state.show_parsing = True
if "night_mode" not in st.session_state:
    st.session_state.night_mode = True  # default on for eye comfort

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
    st.session_state.last_session_ids = []  # for “restart full session”

# -------------------------
# Styling (Night / Day)
# -------------------------
if st.session_state.night_mode:
    BG = "#0b0f14"
    CARD = "rgba(18, 24, 32, 0.92)"
    TEXT = "#e7eaf0"
    SUBT = "rgba(231,234,240,0.70)"
    BORDER = "rgba(255,255,255,0.08)"
    PARSE_BG = "rgba(255,255,255,0.06)"
else:
    BG = "#fafafa"
    CARD = "rgba(255,255,255,0.98)"
    TEXT = "#1f1f1f"
    SUBT = "rgba(0,0,0,0.55)"
    BORDER = "rgba(0,0,0,0.06)"
    PARSE_BG = "rgba(245, 243, 238, 0.75)"

st.markdown(
    f"""
    <style>
    .stApp {{ background-color: {BG}; }}

    .card {{
        max-width: 980px;
        margin: 0 auto;
        padding: 14px 14px;
        background: {CARD};
        border-radius: 18px;
        box-shadow: 0 10px 28px rgba(0,0,0,0.22);
        border: 1px solid {BORDER};
    }}

    .greek {{
        font-family: "Gentium Plus","Noto Serif",serif;
        font-weight: 650;
        text-align: center;
        margin-top: 10px;
        color: {TEXT};
        font-size: 76px;
        line-height: 1.15;
        word-wrap: break-word;
    }}

    .eng {{
        text-align: center;
        margin-top: 10px;
        color: {TEXT};
        opacity: 0.92;
        font-size: 44px;
        line-height: 1.25;
        word-wrap: break-word;
    }}

    .parseWrap {{
        margin-top: 14px;
        padding: 12px 14px;
        border-radius: 14px;
        background: {PARSE_BG};
        border: 1px solid {BORDER};
    }}

    .parseTitle {{
        font-size: 22px;
        font-weight: 650;
        color: {TEXT};
        margin-bottom: 8px;
        text-align: center;
        opacity: 0.95;
    }}

    table.parseTable {{
        width: 100%;
        border-collapse: collapse;
        font-size: 18px;
        line-height: 1.3;
        color: {TEXT};
    }}

    table.parseTable td {{
        padding: 6px 8px;
        vertical-align: top;
        border-top: 1px solid {BORDER};
    }}

    table.parseTable td.key {{
        width: 34%;
        font-weight: 650;
        white-space: nowrap;
        opacity: 0.95;
    }}

    table.parseTable td.val {{
        opacity: 0.92;
    }}

    .muted {{
        text-align:center;
        color: {SUBT};
        font-size:14px;
        margin-top:8px;
    }}

    @media (max-width: 640px) {{
        .greek {{ font-size: 54px; }}
        .eng {{ font-size: 28px; }}
        .parseTitle {{ font-size: 20px; }}
        table.parseTable {{ font-size: 16px; }}

        div.stButton>button {{
            padding: 0.85rem 0.85rem !important;
            font-size: 1.05rem !important;
            border-radius: 14px !important;
        }}
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

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
    st.session_state.fav_only = st.checkbox("Favorites only (browse)", value=st.session_state.fav_only)

    st.session_state.flashcard_mode = st.toggle("Flashcard mode", value=st.session_state.flashcard_mode)
    st.session_state.auto_hide = st.toggle("Auto-hide on Next", value=st.session_state.auto_hide)

    repeat_after = st.slider("Repeat incorrect after N cards", 0, 8, 3)

    st.session_state.show_media = st.toggle("Show media", value=st.session_state.show_media)
    st.session_state.show_parsing = st.toggle("Show parsing on Reveal", value=st.session_state.show_parsing)

    st.session_state.night_mode = st.toggle("🌙 Night mode", value=st.session_state.night_mode)

    st.caption(f"⭐ Favorites: {len(st.session_state.favs)}")

# Optional sidebar (not required on iPhone)
with st.sidebar:
    st.header("Quick")
    st.write(f"Decks selected: **{len(st.session_state.selected_decks or [])}**")
    st.write(f"⭐ Favorites: **{len(st.session_state.favs)}**")
    if st.session_state.in_session:
        st.write(f"Session remaining: **{len(st.session_state.queue)}**")

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

def match(p):
    if st.session_state.q.strip():
        needle = st.session_state.q.strip().lower()
        if needle not in (p.get("koine", "").lower()) and needle not in (p.get("english", "").lower()):
            return False
    return True

# Browse-filtered (search only) list
search_filtered = [p for p in phrases if match(p)]
if not search_filtered:
    st.info("No matches. Clear search.")
    st.stop()

# “Browse favorites only” filter applies after search
if st.session_state.fav_only:
    filtered = [p for p in search_filtered if p["id"] in st.session_state.favs]
else:
    filtered = search_filtered

if not filtered:
    st.info("No matches (after favorites filter).")
    st.stop()

id_to_phrase = {p["id"]: p for p in filtered}
filtered_ids = [p["id"] for p in filtered]

# Ensure selected id is valid
if st.session_state.in_session and st.session_state.queue:
    if st.session_state.queue[0] not in {p["id"] for p in phrases}:
        # deck selection changed drastically; end session
        st.session_state.in_session = False
        st.session_state.queue = []
        st.session_state.revealed = False

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
# Mastery session helpers
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
    st.session_state.last_session_ids = ids[:]  # for restart
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
    st.session_state.selected_id = st.session_state.queue[0]

# -------------------------
# Session controls (top)
# -------------------------
# Build session candidate sets
all_for_session = [p["id"] for p in search_filtered]  # includes non-favs, search-filtered only
favs_for_session = [pid for pid in all_for_session if pid in st.session_state.favs]

t1, t2, t3, t4 = st.columns(4)
with t1:
    if st.button("▶ Session (All)", use_container_width=True):
        start_session(all_for_session)
        st.rerun()
with t2:
    if st.button("⭐ Session (Favs)", use_container_width=True):
        if not favs_for_session:
            st.info("No favorites in the current search filter.")
        else:
            start_session(favs_for_session)
            st.rerun()
with t3:
    if st.button("🔀 Reshuffle", use_container_width=True):
        reshuffle_session()
        st.rerun()
with t4:
    if st.button("⏹ End", use_container_width=True):
        end_session(store_summary=True)
        st.rerun()

# Session progress + completion tools
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
# Viewer controls (mobile-friendly)
# -------------------------
# Phrase selection from filtered browsing list (not necessarily session set)
if st.session_state.selected_id not in id_to_phrase:
    # If selected is outside filtered (can happen after filter changes), reset to first
    st.session_state.selected_id = filtered_ids[0]

selected = id_to_phrase[st.session_state.selected_id]

# Nav row + favorite star (for browsing)
nav1, nav2, nav3, nav4 = st.columns([0.26, 0.26, 0.26, 0.22])
with nav1:
    if st.button("⬅ Prev", use_container_width=True):
        if st.session_state.in_session:
            st.session_state.revealed = not st.session_state.revealed
        else:
            browse_prev()
        st.rerun()
with nav2:
    if st.button("👁 Reveal", use_container_width=True):
        st.session_state.revealed = not st.session_state.revealed
        st.rerun()
with nav3:
    if st.button("Next ➡", use_container_width=True):
        if st.session_state.in_session and st.session_state.queue:
            pid = st.session_state.selected_id
            st.session_state.queue = [x for x in st.session_state.queue if x != pid] + [pid]
            if st.session_state.auto_hide:
                st.session_state.revealed = False
        else:
            browse_next()
        st.rerun()
with nav4:
    is_fav = st.session_state.selected_id in st.session_state.favs
    if st.button("★" if is_fav else "☆", use_container_width=True):
        toggle_fav(st.session_state.selected_id)
        st.rerun()

# Grade row (works in session and in browse mode)
g1, g2 = st.columns(2)
with g1:
    if st.button("✅ Correct", use_container_width=True):
        mark_correct(st.session_state.selected_id)
        st.rerun()
with g2:
    if st.button("❌ Incorrect", use_container_width=True):
        mark_incorrect(st.session_state.selected_id, repeat_after_n=repeat_after)
        st.rerun()

# -------------------------
# Card render
# -------------------------
greek = (selected.get("koine") or "").strip()
eng = (selected.get("english") or "").strip()
meta = selected.get("meta") if isinstance(selected.get("meta"), dict) else None

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

st.markdown(f"<div class='greek'>{greek or '—'}</div>", unsafe_allow_html=True)

show_answer = (not st.session_state.flashcard_mode) or st.session_state.revealed
if show_answer and eng:
    st.markdown(f"<div class='eng'>{eng}</div>", unsafe_allow_html=True)

if show_answer and st.session_state.show_parsing and meta:
    st.markdown(render_parse_meta(meta), unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# -------------------------
# Jump list (mobile-friendly)
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
        # Jumping mid-session is confusing; end session cleanly
        if st.session_state.in_session:
            end_session(store_summary=True)
        st.rerun()

st.caption(
    f'Deck: {selected.get("deck","—")} • '
    f'ID: {selected.get("id","")} • '
    f'Tag: {selected.get("tag") or "—"}'
)
