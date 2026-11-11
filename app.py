import json
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="MedBridge", page_icon="🩺", layout="wide")

DATA_FILE = Path(__file__).parent / "data" / "MedBridge_UpperLimb_Week1_Content.json"


@st.cache_data
def load_week1():
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)


st.title("🩺 MedBridge")
st.subheader("Module 1: Upper Limb")
st.write("Connecting clinical cases with anatomy, clinical reasoning, and MCQs.")

if not DATA_FILE.exists():
    st.error("Data file not found: data/MedBridge_UpperLimb_Week1_Content.json")
    st.stop()

data = load_week1()

st.write(f"Week: {data['week']}")
st.write(f"Clinical cases: {len(data['case_mappings'])}")
st.write(f"Lecture MCQs: {len(data['lecture_mcqs'])}")
st.write(f"Quick recall questions: {len(data['quick_recall'])}") 