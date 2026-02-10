from utils.ui import load_premium_css
load_premium_css()

import streamlit as st
import numpy as np
from utils.ui import kpi_card

st.title("🏠 Dashboard Overview")

# Header Row (Title Left + Button Right)
left, right = st.columns([7, 2])

with right:
    st.write("")  # spacing
    st.write("")
    if st.button("🚨 Detect Anomaly", use_container_width=True):
        st.session_state.show_anomaly_table = True

# default
if "show_anomaly_table" not in st.session_state:
    st.session_state.show_anomaly_table = False

#######
if st.session_state.get("df_final") is None:
    st.warning("Upload CSV from Home page first.")
    st.stop()

df_all = st.session_state.df_final.copy()

#Dashboard User Filter (All Users + Specific User)
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

    #store selection globally
    st.session_state.selected_user = selected_user
else:
    st.warning("⚠️ Person_ID column not found. Showing all data.")
    st.session_state.selected_user = "All Users"

#Apply filter
df = df_all.copy()
if st.session_state.selected_user != "All Users" and "Person_ID" in df.columns:
    df = df[df["Person_ID"] == st.session_state.selected_user]

if df.empty:
    st.warning("⚠️ No data available for selected user.")
    st.stop()

st.caption(f"✅ Currently showing data for: **{st.session_state.selected_user}**")

# Fix Timestamp column for display
if "Timestamp" in df.columns and "timestamp" not in df.columns:
    df = df.rename(columns={"Timestamp": "timestamp"})

#User Profile
st.markdown("### 🧾 User Summary")
row0 = df.iloc[0]

st.markdown(f"""
<div class="glass">
<b>Person ID:</b> {row0.get("Person_ID","N/A")} &nbsp; | &nbsp;
<b>Age:</b> {row0.get("Age","N/A")} &nbsp; | &nbsp;
<b>Weight Category:</b> {row0.get("Weight_Category","N/A")} <br><br>
<b>Stress Level:</b> {row0.get("Stress_Level","N/A")} &nbsp; | &nbsp;
<b>BP:</b> {row0.get("Systolic_Blood_Pressure","N/A")}/{row0.get("Diastolic_Blood_Pressure","N/A")} &nbsp; | &nbsp;
<b>Quality of Sleep:</b> {row0.get("Quality_of_Sleep","N/A")}
</div>
""", unsafe_allow_html=True)

st.divider()

#KPI Cards
c1, c2, c3, c4 = st.columns(4)

with c1:
    kpi_card("❤️ Avg Heart Rate", f"{df['Heart_Rate'].mean():.1f}" if "Heart_Rate" in df.columns else "N/A", "bpm")

with c2:
    kpi_card("🛌 Avg Sleep Duration", f"{df['Sleep_Duration'].mean():.1f}" if "Sleep_Duration" in df.columns else "N/A", "hours")

with c3:
    kpi_card("👟 Total Steps", f"{int(df['Daily_Steps'].sum())}" if "Daily_Steps" in df.columns else "N/A", "steps")

with c4:
    total_anom = 0
    if "Heart_Rate_anomaly" in df.columns:
        total_anom += df["Heart_Rate_anomaly"].astype(int).sum()
    if "Daily_Steps_anomaly" in df.columns:
        total_anom += df["Daily_Steps_anomaly"].astype(int).sum()
    if "Sleep_Duration_anomaly" in df.columns:
        total_anom += df["Sleep_Duration_anomaly"].astype(int).sum()

    kpi_card("🚨 Total Anomaly Flags", f"{int(total_anom)}", "across all metrics")

st.divider()

#Insights
st.subheader("🧠 Key Insights")

insights = []

if "Heart_Rate_anomaly" in df.columns:
    hr_count = int(df["Heart_Rate_anomaly"].astype(int).sum())
    insights.append(("❤️ Heart Rate", hr_count))

if "Sleep_Duration_anomaly" in df.columns:
    sl_count = int(df["Sleep_Duration_anomaly"].astype(int).sum())
    insights.append(("🛌 Sleep Duration", sl_count))

if "Daily_Steps_anomaly" in df.columns:
    st_count = int(df["Daily_Steps_anomaly"].astype(int).sum())
    insights.append(("👟 Steps", st_count))

if sum([x[1] for x in insights]) == 0:
    st.markdown("<div class='ok'>✅ No major anomalies detected for this selection.</div>", unsafe_allow_html=True)
else:
    for name, cnt in insights:
        if cnt > 0:
            st.markdown(f"<div class='insight'><b>{name}</b> has <b>{cnt}</b> anomaly events</div>", unsafe_allow_html=True)

####
#Anomaly Viewer Section
if st.session_state.show_anomaly_table:

    st.markdown("### 🚨 Anomaly Viewer (User-wise)")

    # Make sure timestamp column exists
    if "Timestamp" in df.columns and "timestamp" not in df.columns:
        df = df.rename(columns={"Timestamp": "timestamp"})

    needed_cols = [
        "Person_ID", "timestamp",
        "Heart_Rate", "Daily_Steps", "Sleep_Duration",
        "Heart_Rate_anomaly", "Daily_Steps_anomaly", "Sleep_Duration_anomaly"
    ]

    available_cols = [c for c in needed_cols if c in df.columns]

    # Filter only anomaly rows
    if "anomaly" in df.columns:
        df_anom = df[df["anomaly"].astype(int) == 1].copy()
    else:
        # fallback if "anomaly" column not present
        cond = False
        if "Heart_Rate_anomaly" in df.columns:
            cond = cond | (df["Heart_Rate_anomaly"].astype(int) == 1)
        if "Daily_Steps_anomaly" in df.columns:
            cond = cond | (df["Daily_Steps_anomaly"].astype(int) == 1)
        if "Sleep_Duration_anomaly" in df.columns:
            cond = cond | (df["Sleep_Duration_anomaly"].astype(int) == 1)

        df_anom = df[cond].copy()

    if df_anom.empty:
        st.success("✅ No anomalies detected for this selection.")
    else:
        # Add a clean readable column "Anomaly_Type"
        def anomaly_type(row):
            tags = []
            if "Heart_Rate_anomaly" in row and int(row["Heart_Rate_anomaly"]) == 1:
                tags.append("Heart Rate")
            if "Daily_Steps_anomaly" in row and int(row["Daily_Steps_anomaly"]) == 1:
                tags.append("Steps")
            if "Sleep_Duration_anomaly" in row and int(row["Sleep_Duration_anomaly"]) == 1:
                tags.append("Sleep")
            return ", ".join(tags)

        df_anom["Anomaly_Type"] = df_anom.apply(anomaly_type, axis=1)

        # Show top filters
        col1, col2 = st.columns(2)
        with col1:
            limit = st.selectbox("Show top anomalies", [10, 25, 50, 100], index=1)
        with col2:
            st.write("")
            if st.button("❌ Close Anomaly Viewer"):
                st.session_state.show_anomaly_table = False
                st.rerun()

        # Sort latest anomalies first
        if "timestamp" in df_anom.columns:
            df_anom = df_anom.sort_values("timestamp", ascending=False)

        # Final table view
        show_cols = ["Person_ID", "timestamp", "Anomaly_Type"]
        for c in ["Heart_Rate", "Daily_Steps", "Sleep_Duration"]:
            if c in df_anom.columns:
                show_cols.append(c)

        st.dataframe(
            df_anom[show_cols].head(limit),
            use_container_width=True
        )

        st.caption("✅ This list shows *which user + timestamp* has anomaly and in which metric.")


st.caption("Tip: Open Heart Rate / Sleep / Steps pages for detailed interactive graphs.")
