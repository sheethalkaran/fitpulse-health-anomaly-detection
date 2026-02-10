from utils.ui import load_premium_css
load_premium_css()

import streamlit as st
from utils.charts import line_with_anomalies

st.title("🛌 Sleep Duration Analysis")

if st.session_state.get("df_final") is None:
    st.warning("Upload CSV from Home page first.")
    st.stop()

df_all = st.session_state.df_final.copy()

# ✅ User Filter (Same as Dashboard)
st.markdown("### 👤 Select User")

if "Person_ID" in df_all.columns:
    user_list = sorted(df_all["Person_ID"].dropna().unique().tolist())
    user_list = ["All Users"] + user_list

    selected_user = st.selectbox(
        "Filter data by Person_ID",
        user_list,
        index=user_list.index(st.session_state.get("selected_user", "All Users"))
        if st.session_state.get("selected_user", "All Users") in user_list else 0
    )

    # store selection globally
    st.session_state.selected_user = selected_user
else:
    st.warning("⚠️ Person_ID column not found. Showing all data.")
    st.session_state.selected_user = "All Users"

# ✅ Apply filter
df = df_all.copy()
if st.session_state.selected_user != "All Users" and "Person_ID" in df.columns:
    df = df[df["Person_ID"] == st.session_state.selected_user]

if df.empty:
    st.warning("⚠️ No data found for selected user.")
    st.stop()

st.caption(f"✅ Currently showing data for: **{st.session_state.selected_user}**")

# ✅ Keep your original logic
if "Timestamp" in df.columns and "timestamp" not in df.columns:
    df = df.rename(columns={"Timestamp": "timestamp"})

if "timestamp" not in df.columns or "Sleep_Duration" not in df.columns:
    st.error("Required columns missing: timestamp / Sleep_Duration")
    st.stop()

fig = line_with_anomalies(
    df=df,
    x="timestamp",
    y="Sleep_Duration",
    anom_col="Sleep_Duration_anomaly",
    baseline_col="Sleep_Duration_baseline",
    title="Sleep Duration Trend vs Baseline + Anomalies"
)

st.plotly_chart(fig, use_container_width=True)

c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Avg Sleep", f"{df['Sleep_Duration'].mean():.1f}")
with c2:
    st.metric("Min Sleep", f"{df['Sleep_Duration'].min():.1f}")
with c3:
    st.metric("Sleep Anomalies", int(df["Sleep_Duration_anomaly"].astype(int).sum()))
