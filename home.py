import streamlit as st
import pandas as pd

from utils.ui import load_premium_css, render_header
from utils.runner import run_full_pipeline

st.set_page_config(page_title="Health Anomaly Detection", page_icon="🚀", layout="wide")

load_premium_css()
render_header()

# ---------------- SESSION STATE ----------------
if "df_final" not in st.session_state:
    st.session_state.df_final = None

if "module2_out" not in st.session_state:
    st.session_state.module2_out = None

if "selected_user" not in st.session_state:
    st.session_state.selected_user = "All Users"

# ---------------- SIDEBAR HEADER ----------------

st.sidebar.title("📤 Upload Data")
uploaded = st.sidebar.file_uploader("Upload Fitness Watch CSV", type=["csv"])

resample_rule = st.sidebar.selectbox(
    "Resample Frequency",
    ["30T", "1H", "6H", "1D"],
    index=1
)

st.sidebar.markdown("---")

# ---------------- RUN PIPELINE ----------------
if uploaded is not None:
    df_raw = pd.read_csv(uploaded)
    st.sidebar.success("✅ File uploaded")

    with st.spinner("Running pipeline (Module 1 → Module 2 → Module 3)..."):
        df_final, module2_out = run_full_pipeline(df_raw, resample_rule=resample_rule)

    st.session_state.df_final = df_final
    st.session_state.module2_out = module2_out
    st.sidebar.success("✅ Pipeline completed!")

if st.session_state.df_final is not None:
    df_all = st.session_state.df_final

    if "Person_ID" in df_all.columns:
        user_list = sorted(df_all["Person_ID"].dropna().unique().tolist())
        user_list = ["All Users"] + user_list

        st.session_state.selected_user = st.sidebar.selectbox(
            "👤 Filter by User (Person_ID)",
            user_list,
            index=user_list.index(st.session_state.selected_user)
            if st.session_state.selected_user in user_list else 0
        )
    else:
        st.sidebar.warning("⚠️ Person_ID column not found in data")
        st.session_state.selected_user = "All Users"

st.sidebar.markdown("---")
st.sidebar.caption(f"Showing: {st.session_state.selected_user}")

# ---------------- MAIN HOME PAGE ----------------
st.subheader("🏠 Home")
st.write(
    "Upload your dataset from the sidebar. Then open pages: "
    "**Dashboard, Heart Rate, Sleep, Steps, Model Insights, Reports**."
)

if st.session_state.df_final is None:
    st.info("👈 Upload a CSV file to begin analysis.")
else:
    df_preview = st.session_state.df_final.copy()

    #apply filter here too
    if st.session_state.selected_user != "All Users" and "Person_ID" in df_preview.columns:
        df_preview = df_preview[df_preview["Person_ID"] == st.session_state.selected_user]

    st.success(f"✅ Data ready for: {st.session_state.selected_user}")
    st.dataframe(df_preview.head(20), use_container_width=True)
