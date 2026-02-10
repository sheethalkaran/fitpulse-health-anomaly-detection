from utils.ui import load_premium_css
load_premium_css()

import streamlit as st

st.title("📄 Reports & Downloads")

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

st.markdown("### 📌 Final Dataset Preview")
st.dataframe(df.tail(30), use_container_width=True)

st.divider()

st.markdown("### ⬇️ Download Reports")

# ✅ Download full processed data (filtered)
st.download_button(
    "Download Full Processed Data (CSV)",
    df.to_csv(index=False),
    file_name=f"processed_fitness_data_{st.session_state.selected_user}.csv",
    mime="text/csv"
)

# ✅ Metric-wise anomaly reports (filtered)
if "Heart_Rate_anomaly" in df.columns:
    hr_anom = df[df["Heart_Rate_anomaly"].astype(int) == 1]
    st.download_button(
        "Download Heart Rate Anomalies (CSV)",
        hr_anom.to_csv(index=False),
        file_name=f"heart_rate_anomalies_{st.session_state.selected_user}.csv",
        mime="text/csv"
    )

if "Sleep_Duration_anomaly" in df.columns:
    sl_anom = df[df["Sleep_Duration_anomaly"].astype(int) == 1]
    st.download_button(
        "Download Sleep Anomalies (CSV)",
        sl_anom.to_csv(index=False),
        file_name=f"sleep_anomalies_{st.session_state.selected_user}.csv",
        mime="text/csv"
    )

if "Daily_Steps_anomaly" in df.columns:
    st_anom = df[df["Daily_Steps_anomaly"].astype(int) == 1]
    st.download_button(
        "Download Steps Anomalies (CSV)",
        st_anom.to_csv(index=False),
        file_name=f"steps_anomalies_{st.session_state.selected_user}.csv",
        mime="text/csv"
    )
