# app.py — Koine Flashcards (simple, mobile-friendly, parsing restored)
# Deck schema: JSON list of objects like:
# {
#   "id":"0001",
#   "koine":"...",
#   "english":"...",
#   "tag":"...",
#   "audio":"assets/a.mp3",
#   "image":"assets/i.jpg",
#   "meta": { "lemma":"...", "pos":"...", "χρόνος":"...", ... }
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
    initial_sidebar_state="collapsed",
)
st.title("Διάλογοι Ἑλληνιστί")
st.caption("Simple mobile-first Koine flashcards • favorites • parsing for usage decks")

# -------------------------
# Styling (mobile-first)
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
if "flashcard_mode" not in st.session_state:
    st.session_state.flashcard_mode = True
if "auto_hide" not in st.session_state:
    st.session_state.auto_hide = True
if "show_media" not in st.session_state:
    st.session_state.show_media = True
if "show_parsing" not in st.session_state:
    st.session_state.show_parsing = True

# -------------------------
# Load decks
# -------------------------
if not DECKS_DIR.exists():
    st.error("Missing `decks/` folder. Put JSON deck files in a `decks` folder next to app.py.")
    st.stop()

deck_files = sorted([p for p in DECKS_DIR.glob("*.json") if p.is_file()])
if not deck_files:
    st.error("No deck files found in `decks/`.")
    st.stop()

deck_options = {deck_label_from_filename(p.name): p for p in deck_files}
deck_labels = list(deck_options.keys())

with st.sidebar:
    st.header("Settings")
    selected_deck_labels = st.multiselect("Decks", options=deck_labels, default=[deck_labels[0]])
    q = st.text_input("Search", "")
    fav_only = st.checkbox("Favorites only", value=False)

    st.session_state.flashcard_mode = st.toggle("Flashcard mode", value=st.session_state.flashcard_mode)
    st.session_state.auto_hide = st.toggle("Auto-hide on Next", value=st.session_state.auto_hide)
    st.session_state.show_media = st.toggle("Show media", value=st.session_state.show_media)
    st.session_state.show_parsing = st.toggle("Show parsing on Reveal", value=st.session_state.show_parsing)

    st.write(f"⭐ Favorites: **{len(st.session_state.favs)}**")

if not selected_deck_labels:
    st.warning("Select at least one deck.")
    st.stop()

phrases = []
errors = []
for lbl in selected_deck_labels:
    try:
        phrases.extend(load_deck_file(deck_options[lbl]))
    except Exception as e:
        errors.append(f"{lbl}: {e}")

if errors:
    st.error("Deck load errors:\n\n" + "\n".join(errors))
    st.stop()

def match(p):
    if fav_only and p["id"] not in st.session_state.favs:
        return False
    if q.strip():
        needle = q.strip().lower()
        return needle in (p.get("koine", "").lower()) or needle in (p.get("english", "").lower())
    return True

filtered = [p for p in phrases if match(p)]
if not filtered:
    st.info("No matches. Clear search/filters.")
    st.stop()

id_to_phrase = {p["id"]: p for p in filtered}
filtered_ids = [p["id"] for p in filtered]

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

selected = id_to_phrase[st.session_state.selected_id]

# -------------------------
# Controls (mobile-friendly)
# -------------------------
c1, c2, c3, c4 = st.columns(4)
with c1:
    if st.button("⬅ Prev", use_container_width=True):
        browse_prev()
        st.rerun()
with c2:
    if st.button("👁 Reveal", use_container_width=True):
        st.session_state.revealed = not st.session_state.revealed
        st.rerun()
with c3:
    if st.button("Next ➡", use_container_width=True):
        browse_next()
        st.rerun()
with c4:
    is_fav = st.session_state.selected_id in st.session_state.favs
    if st.button("★" if is_fav else "☆", use_container_width=True):
        toggle_fav(st.session_state.selected_id)
        st.rerun()

# -------------------------
# Card
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
    if audio_path and audio_path.exists():
        st.audio(str(audio_path))

st.markdown(f"<div class='greek'>{greek or '—'}</div>", unsafe_allow_html=True)

show_answer = (not st.session_state.flashcard_mode) or st.session_state.revealed
if show_answer and eng:
    st.markdown(f"<div class='eng'>{eng}</div>", unsafe_allow_html=True)

# Parsing shown when answer is shown (or if flashcard mode off)
if show_answer and st.session_state.show_parsing and meta:
    st.markdown(render_parse_meta(meta), unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# Jump list (mobile-friendly, no sidebar required)
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
        st.rerun()

st.caption(f'Deck: {selected.get("deck","—")} • ID: {selected.get("id","")} • Tag: {selected.get("tag") or "—"}')
