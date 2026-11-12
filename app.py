import json
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="MedBridge", page_icon="🩺", layout="wide")

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
STYLE_FILE = BASE_DIR / "styles.css"

SECTION_KEYS = ("case_mappings", "lecture_mcqs", "quick_recall")
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


# ---------------------------------------------------------------
# Loading: styles and week files
# ---------------------------------------------------------------
def load_css():
    if STYLE_FILE.exists():
        css = STYLE_FILE.read_text(encoding="utf-8")
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def data_signature():
    """Changes whenever a JSON file is added, removed, or edited."""
    if not DATA_DIR.exists():
        return ()
    return tuple((p.name, p.stat().st_mtime) for p in sorted(DATA_DIR.glob("*.json")))


@st.cache_data
def load_all_weeks(signature):
    """Find every valid week file in data/. Returns (weeks, problems)."""
    weeks, problems, seen = [], [], set()
    for path in sorted(DATA_DIR.glob("*.json")):
        try:
            with open(path, encoding="utf-8") as f:
                week = json.load(f)
        except Exception as error:
            problems.append(f"{path.name}: cannot be read ({error})")
            continue
        if not isinstance(week, dict):
            problems.append(f"{path.name}: the file must contain a JSON object")
            continue
        if not isinstance(week.get("week"), int) or not week.get("region"):
            problems.append(f"{path.name}: needs a numeric 'week' and a 'region'")
            continue
        if not any(week.get(key) for key in SECTION_KEYS):
            problems.append(f"{path.name}: has no cases, MCQs or quick recall")
            continue
        key = f"{str(week['region']).replace(' ', '_')}_W{week['week']}"
        if key in seen:
            problems.append(f"{path.name}: duplicate of another {week['region']} Week {week['week']} file")
            continue
        seen.add(key)
        week["_key"] = key
        week["_file"] = path.name
        weeks.append(week)
    weeks.sort(key=lambda w: (w["region"], w["week"]))
    return weeks, problems


# ---------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------
def go(page, module=None, week_key=None):
    st.session_state.page = page
    st.session_state.module = module
    st.session_state.week_key = week_key


def source_text(src):
    """Build 'File name, p. 3, 4' from a dict with file and page/pages."""
    if not src:
        return ""
    pages = src.get("pages")
    if pages is None and src.get("page") is not None:
        pages = [src["page"]]
    file_name = src.get("file") or ""
    page_part = f"p. {', '.join(str(p) for p in pages)}" if pages else ""
    return ", ".join(part for part in (file_name, page_part) if part)


def clean_option(option):
    return option.replace(" (Correct)", "")


def is_correct(choice, question):
    return choice.strip()[:1].upper() == question["correct_answer"].strip()[:1].upper()


# ---------------------------------------------------------------
# Images
# ---------------------------------------------------------------
def resolve_image(file_name):
    """Return a safe path inside assets/, or None if it is missing or not allowed."""
    if not file_name or not ASSETS_DIR.exists():
        return None
    root = ASSETS_DIR.resolve()
    candidate = (root / file_name).resolve()
    if candidate.is_file() and candidate.suffix.lower() in IMAGE_EXTENSIONS and root in candidate.parents:
        return candidate
    # Fallback: look for the same file name anywhere inside assets/
    wanted = Path(file_name).name.lower()
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.name.lower() == wanted and path.suffix.lower() in IMAGE_EXTENSIONS:
            return path
    return None


def order_of(image):
    try:
        return float(image.get("order", 999))
    except (TypeError, ValueError):
        return 999


def images_for(week, pairs):
    """pairs: list of (related_type, related_id). Returns matching images in display order."""
    wanted = {(kind, str(ident)) for kind, ident in pairs}
    found = [
        im
        for im in week.get("images", [])
        if isinstance(im, dict) and (im.get("related_type"), str(im.get("related_id"))) in wanted
    ]
    return sorted(found, key=order_of)


def show_images(week, pairs):
    for im in images_for(week, pairs):
        path = resolve_image(im.get("file"))
        if path is None:
            st.caption(f"⚠️ Image not found: {im.get('file', '(no file name)')}")
            continue
        try:
            st.image(str(path), caption=im.get("caption"))
        except Exception:
            st.caption(f"⚠️ Image could not be opened: {im.get('file')}")
            continue
        if im.get("description"):
            st.caption(im["description"])
        src = source_text({"file": im.get("source_file"), "page": im.get("source_page")})
        if src:
            st.caption(f"Source: {src}")


# ---------------------------------------------------------------
# Section: Clinical Cases
# ---------------------------------------------------------------
def show_cases(week):
    wk = week["_key"]
    cases = week["case_mappings"]
    show_images(week, [("section", "cases")])

    names = [c.get("case", f"Case {i + 1}") for i, c in enumerate(cases)]
    name = st.selectbox("Select a case", names, key=f"{wk}:case_select")
    case = cases[names.index(name)]

    role = case.get("case_role")
    st.subheader(f"{name} ({role})" if role else name)

    if case.get("clinical_pattern"):
        st.markdown("**Clinical Presentation (summary)**")
        st.write(case["clinical_pattern"])
    if case.get("most_relevant_topic"):
        st.markdown("**Most relevant topic**")
        st.write(case["most_relevant_topic"])

    links = case.get("anatomy_links", [])
    pairs = [("case", name), ("topic", case.get("most_relevant_topic"))]
    pairs += [("topic", link.get("topic")) for link in links]
    show_images(week, [p for p in pairs if p[1]])

    if links:
        st.markdown("**Anatomy links**")
        for link in links:
            src = source_text({"file": link.get("source_file"), "pages": link.get("pages")})
            st.markdown(f"- {link.get('topic', '')}" + (f" ({src})" if src else ""))

    if case.get("clinical_correlation"):
        st.markdown("**Clinical correlation**")
        for item in case["clinical_correlation"]:
            st.markdown(f"- {item}")

    src = source_text(case.get("case_source"))
    if src:
        st.caption(f"Case source: {src}")


# ---------------------------------------------------------------
# Section: Lecture MCQs (progress is kept per week, in this session)
# ---------------------------------------------------------------
def quiz_key(wk, qid):
    run = st.session_state.get(f"{wk}:mcq_run", 0)
    return f"{wk}:mcq:{run}:{qid}"


def save_answer(wk, qid):
    answers = st.session_state.setdefault(f"{wk}:mcq_answers", {})
    answers[qid] = st.session_state.get(quiz_key(wk, qid))


def reset_quiz(wk):
    st.session_state[f"{wk}:mcq_answers"] = {}
    st.session_state[f"{wk}:mcq_run"] = st.session_state.get(f"{wk}:mcq_run", 0) + 1


def show_mcqs(week):
    wk = week["_key"]
    show_images(week, [("section", "mcqs")])
    indexed = [(q.get("id", f"mcq{i}"), q) for i, q in enumerate(week["lecture_mcqs"])]
    answers = st.session_state.setdefault(f"{wk}:mcq_answers", {})

    total = len(indexed)
    answered = sum(1 for qid, _ in indexed if answers.get(qid) is not None)
    correct = sum(1 for qid, q in indexed if answers.get(qid) is not None and is_correct(answers[qid], q))
    percent = round(100 * answered / total) if total else 0
    st.progress(answered / total if total else 0.0)
    st.write(f"Answered: {answered}/{total} ({percent}%)  |  Correct: {correct}")
    st.button("Retry / Reset quiz", on_click=reset_quiz, args=(wk,), key=f"{wk}:mcq_reset")

    sections = ["All"] + list(dict.fromkeys(q.get("section", "General") for _, q in indexed))
    section = st.selectbox("Section", sections, key=f"{wk}:mcq_section")
    shown = [(qid, q) for qid, q in indexed if section == "All" or q.get("section", "General") == section]
    st.write(f"{len(shown)} questions")

    for number, (qid, q) in enumerate(shown, start=1):
        st.markdown(f"**{number}. {q['question']}**")
        show_images(week, [("question", qid)])
        options = [clean_option(o) for o in q["options"]]
        saved = answers.get(qid)
        choice = st.radio(
            "Choose one answer",
            options,
            index=options.index(saved) if saved in options else None,
            key=quiz_key(wk, qid),
            on_change=save_answer,
            args=(wk, qid),
            label_visibility="collapsed",
        )
        if choice is not None:
            if is_correct(choice, q):
                st.success("Correct ✅")
            else:
                st.error(f"Not correct. Correct answer: {q['correct_answer']}")
            explanation = q.get("explanation_from_source") or q.get("explanation")
            if explanation:
                st.write(f"Explanation: {explanation}")
            src = source_text(q.get("source"))
            if src:
                st.caption(f"Source: {src}")
        st.divider()


# ---------------------------------------------------------------
# Section: Quick Recall
# ---------------------------------------------------------------
def show_recall(week):
    wk = week["_key"]
    show_images(week, [("section", "recall")])
    indexed = [(q.get("id", f"qr{i}"), q) for i, q in enumerate(week["quick_recall"])]

    categories = ["All"] + sorted({q.get("category", "General") for _, q in indexed})
    category = st.selectbox("Category", categories, key=f"{wk}:recall_category")
    shown = [(qid, q) for qid, q in indexed if category == "All" or q.get("category", "General") == category]
    st.write(f"{len(shown)} questions. Tap a question to reveal the answer.")

    for qid, q in shown:
        with st.expander(q["question"]):
            show_images(week, [("question", qid)])
            st.success(q["answer"])
            src = source_text(q.get("source"))
            if src:
                st.caption(f"Source: {src}")


SECTIONS = [
    ("Clinical Cases", "case_mappings", show_cases),
    ("Lecture MCQs", "lecture_mcqs", show_mcqs),
    ("Quick Recall", "quick_recall", show_recall),
]


# ---------------------------------------------------------------
# App: Home -> Module -> Week
# ---------------------------------------------------------------
load_css()

if "page" not in st.session_state:
    go("home")

weeks, problems = load_all_weeks(data_signature())

if not weeks:
    st.title("🩺 MedBridge")
    st.error("No valid week files found in the data/ folder.")
    for problem in problems:
        st.write(f"- {problem}")
    st.stop()

weeks_by_key = {w["_key"]: w for w in weeks}
modules = list(dict.fromkeys(w["region"] for w in weeks))

page = st.session_state.page
module = st.session_state.get("module")
week = weeks_by_key.get(st.session_state.get("week_key"))
if page == "module" and module not in modules:
    page = "home"
if page == "week" and week is None:
    page = "home"

if page == "home":
    st.title("🩺 MedBridge")
    st.write("Connecting clinical cases with anatomy, clinical reasoning, and MCQs.")
    for name in modules:
        st.button(f"{name} →", key=f"module:{name}", on_click=go, args=("module", name))

elif page == "module":
    st.button("← Home", key="back_home", on_click=go, args=("home",))
    st.title(module)
    st.write("Choose a week:")
    for w in [w for w in weeks if w["region"] == module]:
        st.button(f"Week {w['week']}", key=f"open:{w['_key']}", on_click=go, args=("week", module, w["_key"]))
    if problems:
        with st.expander("Content files that were skipped (for editors)"):
            for problem in problems:
                st.write(f"- {problem}")

else:
    st.button(f"← {week['region']}", key="back_module", on_click=go, args=("module", week["region"]))
    st.title(f"{week['region']}: Week {week['week']}")
    available = [(label, show) for label, key, show in SECTIONS if week.get(key)]
    for tab, (label, show) in zip(st.tabs([label for label, _ in available]), available):
        with tab:
            show(week)