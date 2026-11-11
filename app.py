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
    st.write(f"Clinical cases: {len(data['case_mappings'])}")
    st.write(f"Lecture MCQs: {len(data['lecture_mcqs'])}")
    st.write(f"Quick recall questions: {len(data['quick_recall'])}")