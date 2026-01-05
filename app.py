# password gate enabled

import json
import random
from pathlib import Path

import streamlit as st

PASSWORD = st.secrets.get("APP_PASSWORD") if "APP_PASSWORD" in st.secrets else ""

if PASSWORD:
    entered = st.text_input("Password", type="password")
    if entered != PASSWORD:
        st.stop()

# -------------------------
# App config / files
# -------------------------
APP_DIR = Path(__file__).parent
DECKS_DIR = APP_DIR / "decks"
FAV_FILE = APP_DIR / "favorites.json"

# ---------- UI sizes ----------
GREEK_SIZE_PX = 80
ENGLISH_SIZE_PX = 50
PARSE_SIZE_PX = 28
CENTER_MAX_WIDTH_PX = 980  # wider now that list is in sidebar

st.set_page_config(page_title="Διάλογοι Ἑλληνιστί", layout="wide")
st.title("Διάλογοι Ἑλληνιστί")

# -------------------------
# Global styling (NO background)
# -------------------------
st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: #fafafa;
    }}

    section[data-testid="stSidebar"] {{
        background-color: rgba(245, 243, 238, 0.97);
    }}

    .centerWrap {{
        max-width: {CENTER_MAX_WIDTH_PX}px;
        margin: 0 auto;
        padding: 28px 36px;
        background: rgba(255, 255, 255, 0.98);
        border-radius: 20px;
        box-shadow: 0 10px 28px rgba(0,0,0,0.08);
    }}

    .greekBig {{
        font-family: "Gentium Plus", "Noto Serif", serif;
        font-size: {GREEK_SIZE_PX}px;
        line-height: 1.22;
        font-weight: 650;
        text-align: center;
        margin-top: 18px;
        color: #1f1f1f;
    }}

    .engText {{
        font-size: {ENGLISH_SIZE_PX}px;
        line-height: 1.45;
        text-align: center;
        margin-top: 14px;
        color: #2b2b2b;
        opacity: 0.95;
    }}

    .parseWrap {{
        margin-top: 16px;
        padding: 14px 16px;
        border-radius: 14px;
        background: rgba(245, 243, 238, 0.75);
        border: 1px solid rgba(0,0,0,0.06);
    }}

    .parseTitle {{
        font-size: {PARSE_SIZE_PX}px;
        font-weight: 650;
        color: #1f1f1f;
        margin-bottom: 8px;
        text-align: center;
    }}

    table.parseTable {{
        width: 100%;
        border-collapse: collapse;
        font-size: 20px;
        line-height: 1.3;
    }}

    table.parseTable td {{
        padding: 6px 8px;
        vertical-align: top;
        border-top: 1px solid rgba(0,0,0,0.06);
    }}

    table.parseTable td.key {{
        width: 32%;
        font-weight: 650;
        color: #333;
        white-space: nowrap;
    }}

    table.parseTable td.val {{
        color: #222;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

st.caption("Local decks + flashcards (mastery session • favorites • audio/images-ready).")


# -------------------------
# Utilities
# -------------------------
def deck_label_from_filename(fn: str) -> str:
    base = fn.replace(".json", "").replace("_", " ")
    return " ".join([w.capitalize() if not w.isdigit() else w for w in base.split()])


def safe_load_json(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_deck_file(path: Path):
    """
    Loads one deck JSON file (list of dicts).
    Adds:
      - namespaced id: "<deckname>:<id>"
      - deck: <deckname>
    Keeps any extra keys (e.g., `meta`) intact.
    """
    raw = safe_load_json(path)
    if not isinstance(raw, list):
        raise ValueError(f"{path.name} must be a JSON list of objects.")

    deck_name = path.stem
    out = []
    for i, p in enumerate(raw):
        if not isinstance(p, dict):
            continue
        p = dict(p)

        base_id = str(p.get("id") or f"{i+1:04d}").strip()
        if not base_id:
            base_id = f"{i+1:04d}"

        p["id"] = f"{deck_name}:{base_id}"
        p["deck"] = deck_name

        p["koine"] = (p.get("koine") or "").strip()
        p["english"] = (p.get("english") or "").strip()
        p["tag"] = (p.get("tag") or "").strip() or None
        p["audio"] = (p.get("audio") or "").strip() or None
        p["image"] = (p.get("image") or "").strip() or None

        # normalize meta (optional)
        if "meta" in p and p["meta"] is not None and not isinstance(p["meta"], dict):
            # if meta is malformed, drop it silently
            p["meta"] = None

        if p["koine"] or p["english"]:
            out.append(p)

    return out


def render_parse_meta(meta: dict) -> str:
    """
    Render parsing meta as an HTML table.
    Prefer a stable order; show remaining keys afterwards.
    """
    if not meta or not isinstance(meta, dict):
        return ""

    # Preferred key order (Koine labels + a few common fields)
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
        # optional extra keys you might add later:
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
        # stringify safely
        if isinstance(v, (list, tuple)):
            v = ", ".join(map(str, v))
        else:
            v = str(v)
        rows.append((k, v))

    for k in preferred:
        if k in meta:
            add_row(k)

    # Add any remaining keys (stable alphabetical)
    for k in sorted(meta.keys()):
        if k not in used:
            add_row(k)

    if not rows:
        return ""

    # HTML escape minimal (Streamlit will sanitize some, but keep simple)
    def esc(s: str) -> str:
        return (
            s.replace("&", "&amp;")
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
def load_favs():
    if not FAV_FILE.exists():
        return set()
    try:
        data = safe_load_json(FAV_FILE)
        return set(map(str, data)) if isinstance(data, list) else set()
    except Exception:
        return set()


def save_favs(favs):
    with open(FAV_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(list(favs)), f, ensure_ascii=False, indent=2)


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

# Mastery session
if "in_session" not in st.session_state:
    st.session_state.in_session = False
if "queue" not in st.session_state:
    st.session_state.queue = []
if "correct" not in st.session_state:
    st.session_state.correct = set()
if "incorrect" not in st.session_state:
    st.session_state.incorrect = set()
if "repeat_events" not in st.session_state:
    st.session_state.repeat_events = 0
if "session_total" not in st.session_state:
    st.session_state.session_total = 0
if "finished_summary" not in st.session_state:
    st.session_state.finished_summary = None

# Media toggles
if "audio_on" not in st.session_state:
    st.session_state.audio_on = True
if "show_media" not in st.session_state:
    st.session_state.show_media = True

# Parsing toggle
if "show_parsing" not in st.session_state:
    st.session_state.show_parsing = True


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
# Sidebar controls
# -------------------------
with st.sidebar:
    st.title("Koine Tools")

    with st.expander("Decks", expanded=True):
        selected_deck_labels = st.multiselect(
            "Load decks",
            options=deck_labels,
            default=[deck_labels[0]],
        )
        if not selected_deck_labels:
            st.warning("Select at least one deck.")
            st.stop()
        selected_deck_paths = [deck_options[lbl] for lbl in selected_deck_labels]
        st.caption("Tip: put decks in the `decks/` folder as JSON lists.")

    with st.expander("Settings", expanded=True):
        q = st.text_input("Search (Greek or English)", "")
        fav_only = st.checkbox("Favorites only", value=False)

        flashcard_mode = st.toggle("Flashcard mode", value=True)
        auto_hide_on_next = st.toggle("Auto-hide on Next", value=True)

        repeat_after = st.slider("Repeat incorrect after N cards", 0, 8, 3)
        st.session_state.show_media = st.toggle("Show media by default", value=st.session_state.show_media)

        # NEW: show parsing when revealed (usage decks)
        st.session_state.show_parsing = st.toggle("Show parsing on Reveal", value=st.session_state.show_parsing)

    # NOTE: Phrase List must come AFTER we compute filtered; we’ll inject it later

    with st.expander("Stats", expanded=False):
        st.write(f"Favorites: **{len(st.session_state.favs)}**")
        st.write(f"Correct (this session): **{len(st.session_state.correct)}**")
        st.write(f"Incorrect (this session): **{len(st.session_state.incorrect)}**")
        st.write(f"Queue remaining: **{len(st.session_state.queue)}**")
        if st.session_state.in_session:
            done = st.session_state.session_total - len(st.session_state.queue)
            st.write(f"Progress: **{done}/{st.session_state.session_total}**")

        if st.button("🧹 Reset session tracking", use_container_width=True):
            st.session_state.correct = set()
            st.session_state.incorrect = set()
            st.session_state.queue = []
            st.session_state.in_session = False
            st.session_state.revealed = False
            st.session_state.repeat_events = 0
            st.session_state.session_total = 0
            st.session_state.finished_summary = None
            st.rerun()


# -------------------------
# Load selected decks into phrases
# -------------------------
phrases = []
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
# Filter logic
# -------------------------
def match(p):
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

if st.session_state.selected_id not in id_to_phrase:
    st.session_state.selected_id = filtered_ids[0]

selected = id_to_phrase[st.session_state.selected_id]


# -------------------------
# Mastery session helpers
# -------------------------
def end_session(store_summary=True):
    if store_summary:
        st.session_state.finished_summary = {
            "total": st.session_state.session_total,
            "correct": len(st.session_state.correct),
            "incorrect": len(st.session_state.incorrect),
            "repeat_events": st.session_state.repeat_events,
        }
    st.session_state.in_session = False
    st.session_state.queue = []
    st.session_state.revealed = False


def start_mastery_session(ids):
    st.session_state.queue = list(ids)
    random.shuffle(st.session_state.queue)
    st.session_state.correct = set()
    st.session_state.incorrect = set()
    st.session_state.repeat_events = 0
    st.session_state.session_total = len(st.session_state.queue)
    st.session_state.finished_summary = None

    st.session_state.in_session = True
    st.session_state.revealed = False
    if st.session_state.queue:
        st.session_state.selected_id = st.session_state.queue[0]


def reshuffle_session_keep_stats():
    if not st.session_state.in_session or not st.session_state.queue:
        return
    random.shuffle(st.session_state.queue)
    st.session_state.selected_id = st.session_state.queue[0]
    st.session_state.revealed = False


def mark_correct(pid: str):
    st.session_state.correct.add(pid)
    st.session_state.incorrect.discard(pid)

    if st.session_state.in_session:
        st.session_state.queue = [x for x in st.session_state.queue if x != pid]
        st.session_state.revealed = False

        if st.session_state.queue:
            st.session_state.selected_id = st.session_state.queue[0]
        else:
            end_session(store_summary=True)
    else:
        browse_next_no_rerun()


def mark_incorrect(pid: str, repeat_after: int):
    st.session_state.incorrect.add(pid)
    st.session_state.correct.discard(pid)

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
        browse_next_no_rerun()


def browse_next_no_rerun():
    i = filtered_ids.index(st.session_state.selected_id)
    st.session_state.selected_id = filtered_ids[(i + 1) % len(filtered_ids)]
    if auto_hide_on_next:
        st.session_state.revealed = False


def browse_prev_no_rerun():
    i = filtered_ids.index(st.session_state.selected_id)
    st.session_state.selected_id = filtered_ids[(i - 1) % len(filtered_ids)]
    if auto_hide_on_next:
        st.session_state.revealed = False


# -------------------------
# Sidebar Phrase List (NOW that filtered exists)
# -------------------------
with st.sidebar:
    with st.expander("Phrase List", expanded=False):
        st.write(f"Showing **{len(filtered)}** results")

        def short(s, n=60):
            s = s or ""
            return s if len(s) <= n else s[:n] + "…"

        label_map = {
            f'{p["id"]} — [{p.get("deck","")}] {short(p.get("koine",""))}': p["id"]
            for p in filtered
        }
        labels = list(label_map.keys())

        current_label = next(
            (lab for lab, pid in label_map.items() if pid == st.session_state.selected_id),
            labels[0]
        )

        choice = st.selectbox("Jump to phrase", labels, index=labels.index(current_label))
        st.session_state.selected_id = label_map[choice]
        selected = id_to_phrase[st.session_state.selected_id]

    with st.expander("⭐ Favorites (quick jump)", expanded=False):
        favs_in_filtered = [pid for pid in filtered_ids if pid in st.session_state.favs]
        if not favs_in_filtered:
            st.caption("No favorites in this filtered set.")
        else:
            fav_choice = st.selectbox("Jump to favorite", favs_in_filtered)
            if st.button("Go"):
                st.session_state.selected_id = fav_choice
                st.session_state.revealed = False
                st.rerun()


# -------------------------
# Main area (full width)
# -------------------------
# ---- Session controls ----
top1, top2, top3, top4 = st.columns(4)
with top1:
    if st.button("▶ Start Session", use_container_width=True):
        start_mastery_session(filtered_ids)
        st.rerun()
with top2:
    if st.button("🔀 Reshuffle", use_container_width=True):
        reshuffle_session_keep_stats()
        st.rerun()
with top3:
    if st.button("⏹ End", use_container_width=True):
        end_session(store_summary=True)
        st.rerun()
with top4:
    is_fav = st.session_state.selected_id in st.session_state.favs
    if st.button("★" if is_fav else "☆", use_container_width=True):
        toggle_fav(st.session_state.selected_id)
        st.rerun()

# If in session, current card = queue head
if st.session_state.in_session and st.session_state.queue:
    st.session_state.selected_id = st.session_state.queue[0]
    selected = id_to_phrase.get(st.session_state.selected_id, selected)

# ---- Nav / grading row ----
nav1, nav2, nav3, nav4, nav5 = st.columns([0.18, 0.18, 0.18, 0.23, 0.23])

with nav1:
    if st.button("⬅", use_container_width=True):
        if st.session_state.in_session:
            st.session_state.revealed = not st.session_state.revealed
            st.rerun()
        else:
            browse_prev_no_rerun()
            st.rerun()

with nav2:
    if st.button("➡", use_container_width=True):
        if st.session_state.in_session:
            pid = st.session_state.selected_id
            st.session_state.queue = [x for x in st.session_state.queue if x != pid] + [pid]
            if auto_hide_on_next:
                st.session_state.revealed = False
            st.rerun()
        else:
            browse_next_no_rerun()
            st.rerun()

with nav3:
    if st.button("🎲", use_container_width=True):
        st.session_state.selected_id = random.choice(filtered_ids)
        if auto_hide_on_next:
            st.session_state.revealed = False
        st.rerun()

with nav4:
    if st.button("✅ Correct", use_container_width=True):
        mark_correct(st.session_state.selected_id)
        st.rerun()

with nav5:
    if st.button("❌ Incorrect", use_container_width=True):
        mark_incorrect(st.session_state.selected_id, repeat_after=repeat_after)
        st.rerun()

# ---- Session progress + conclusion ----
if st.session_state.in_session:
    total = max(1, st.session_state.session_total)
    done = total - len(st.session_state.queue)
    st.progress(done / total)
    st.caption(
        f"Remaining **{len(st.session_state.queue)}** • "
        f"Correct **{len(st.session_state.correct)}** • "
        f"Incorrect **{len(st.session_state.incorrect)}** • "
        f"Repeats **{st.session_state.repeat_events}**"
    )

if (not st.session_state.in_session) and st.session_state.finished_summary:
    s = st.session_state.finished_summary
    total = max(1, s["total"])
    accuracy = round(100 * (s["correct"] / total), 1)

    st.success("✅ Τέλος τοῦ δέλτου!  (Deck/session complete)")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total", s["total"])
    c2.metric("Correct", s["correct"])
    c3.metric("Incorrect", s["incorrect"])
    c4.metric("Repeats", s["repeat_events"])
    st.caption(f"Accuracy: **{accuracy}%**")

    colA, colB = st.columns(2)
    with colA:
        if st.button("🔁 Study missed only", use_container_width=True):
            missed = list(st.session_state.incorrect)
            if missed:
                start_mastery_session(missed)
                st.rerun()
            else:
                st.info("No incorrect items to review.")
    with colB:
        if st.button("▶ Restart full session", use_container_width=True):
            start_mastery_session(filtered_ids)
            st.rerun()

# ---- Center viewer ----
greek = (selected.get("koine") or "").strip()
eng = (selected.get("english") or "").strip()
meta = selected.get("meta") if isinstance(selected.get("meta"), dict) else None

audio_rel = (selected.get("audio") or "").strip()
image_rel = (selected.get("image") or "").strip()

audio_path = (APP_DIR / audio_rel) if audio_rel else None
image_path = (APP_DIR / image_rel) if image_rel else None

with st.container():
    st.markdown("<div class='centerWrap'>", unsafe_allow_html=True)

    if st.session_state.show_media and image_path and image_path.exists():
        st.image(str(image_path), use_container_width=True)
    else:
        st.info("No image yet (later: add `image: images/XXXX.jpg`).")

    if st.session_state.show_media and audio_path and audio_path.exists():
        a1, a2 = st.columns([0.35, 0.65])
        with a1:
            st.session_state.audio_on = st.toggle("Audio", value=st.session_state.audio_on)
        with a2:
            if st.session_state.audio_on:
                st.audio(str(audio_path))
    else:
        st.toggle("Audio", value=False, disabled=True)

    st.markdown(f"<div class='greekBig'>{greek or '—'}</div>", unsafe_allow_html=True)

    # Reveal / Hide + display
    show_answer_block = (not flashcard_mode) or st.session_state.revealed

    if flashcard_mode:
        r1, r2, r3 = st.columns([0.33, 0.34, 0.33])
        with r2:
            if st.button("👁 Reveal / Hide", use_container_width=True):
                st.session_state.revealed = not st.session_state.revealed
                st.rerun()

    if show_answer_block:
        if eng:
            st.markdown(f"<div class='engText'>{eng}</div>", unsafe_allow_html=True)

        # NEW: parsing (only when revealed / or non-flashcard) + toggle enabled
        if st.session_state.show_parsing and meta:
            st.markdown(render_parse_meta(meta), unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

st.caption(
    f"Deck: {selected.get('deck','—')} • "
    f"ID: {selected.get('id','')} • "
    f"Tag: {selected.get('tag','—') or '—'}"
)
