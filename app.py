import json
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="MedBridge", page_icon="🩺", layout="wide")

DATA_FILE = Path(__file__).parent / "data" / "MedBridge_UpperLimb_Week1_Content.json"


@st.cache_data
def load_week1():
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)


def go(page_name):
    st.session_state.page = page_name


def pages_text(pages):
    return ", ".join(str(p) for p in pages)


# ---------- Clinical cases ----------
def show_cases(cases):
    names = [c["case"] for c in cases]
    name = st.selectbox("Select a case", names, key="case_select")
    case = next(c for c in cases if c["case"] == name)

    st.subheader(f"{case['case']} ({case['case_role']})")

    st.markdown("**Clinical Presentation (summary)**")
    st.write(case["clinical_pattern"])

    st.markdown("**Most relevant topic**")
    st.write(case["most_relevant_topic"])

    st.markdown("**Anatomy links**")
    for link in case["anatomy_links"]:
        st.markdown(
            f"- {link['topic']} ({link['source_file']}, p. {pages_text(link['pages'])})"
        )

    st.markdown("**Clinical correlation**")
    for item in case["clinical_correlation"]:
        st.markdown(f"- {item}")

    src = case["case_source"]
    st.caption(f"Case source: {src['file']}, p. {pages_text(src['pages'])}")


# ---------- Lecture MCQs ----------
def show_mcqs(mcqs):
    sections = ["All"] + list(dict.fromkeys(q["section"] for q in mcqs))
    section = st.selectbox("Section", sections, key="mcq_section")
    shown = [q for q in mcqs if section == "All" or q["section"] == section]
    st.write(f"{len(shown)} questions")

    for i, q in enumerate(shown, start=1):
        st.markdown(f"**{i}. {q['question']}**")
        options = [o.replace(" (Correct)", "") for o in q["options"]]
        choice = st.radio(
            "Choose one answer",
            options,
            index=None,
            key=q["id"],
            label_visibility="collapsed",
        )
        if choice is not None:
            if choice[0] == q["correct_answer"][0]:
                st.success("Correct ✅")
            else:
                st.error(f"Not correct. Correct answer: {q['correct_answer']}")
            st.write(f"Explanation: {q['explanation_from_source']}")
            st.caption(f"Source: {q['source']['file']}, p. {q['source']['page']}")
        st.divider()


# ---------- Quick recall ----------
def show_recall(items):
    categories = ["All"] + sorted({q["category"] for q in items})
    category = st.selectbox("Category", categories, key="recall_category")
    shown = [q for q in items if category == "All" or q["category"] == category]
    st.write(f"{len(shown)} questions. Tap a question to see the answer.")

    for q in shown:
        with st.expander(q["question"]):
            st.success(q["answer"])
            st.caption(
                f"Source: {q['source']['file']}, p. {pages_text(q['source']['pages'])}"
            )


# ---------- App ----------
if "page" not in st.session_state:
    st.session_state.page = "home"

if not DATA_FILE.exists():
    st.error("Data file not found: data/MedBridge_UpperLimb_Week1_Content.json")
    st.stop()

data = load_week1()
page = st.session_state.page

if page == "home":
    st.title("🩺 MedBridge")
    st.write("Connecting clinical cases with anatomy, clinical reasoning, and MCQs.")
    st.button("Upper Limb →", on_click=go, args=("module",))

elif page == "module":
    st.button("← Home", on_click=go, args=("home",))
    st.title("Upper Limb")
    st.write("Choose a week:")
    st.button("Week 1", on_click=go, args=("week1",))

elif page == "week1":
    st.button("← Upper Limb", on_click=go, args=("module",))
    st.title(f"Upper Limb: Week {data['week']}")

    tab_cases, tab_mcq, tab_recall = st.tabs(
        ["Clinical Cases", "Lecture MCQs", "Quick Recall"]
    )
    with tab_cases:
        show_cases(data["case_mappings"])
    with tab_mcq:
        show_mcqs(data["lecture_mcqs"])
    with tab_recall:
        show_recall(data["quick_recall"])