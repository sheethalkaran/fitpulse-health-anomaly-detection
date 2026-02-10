from utils.ui import load_premium_css
load_premium_css()

import streamlit as st

st.title("🩺 Are You Healthy?")

st.markdown("Fill the form below to check your health status based on our dataset patterns.")

with st.form("health_form"):
    name = st.text_input("Your Name")
    age = st.number_input("Age", min_value=1, max_value=120)

    heart_rate = st.number_input("Heart Rate (bpm)", min_value=30, max_value=200)
    sleep = st.number_input("Sleep Duration (hours)", min_value=0.0, max_value=24.0)
    steps = st.number_input("Daily Steps", min_value=0)
    stress = st.slider("Stress Level (1–10)", 1, 10)

    submit = st.form_submit_button("Check My Health")

if submit:
    issues = []

    if heart_rate < 50 or heart_rate > 100:
        issues.append("Abnormal Heart Rate")

    if sleep < 6 or sleep > 9:
        issues.append("Poor Sleep Duration")

    if steps < 4000:
        issues.append("Low Physical Activity")

    if stress > 6:
        issues.append("High Stress Level")

    healthy = len(issues) < 2

    st.markdown("---")

    if healthy:
        st.success(f"✅ {name}, you are Healthy!")
    else:
        st.error(f"⚠️ {name}, your health indicators show concerns.")

    st.markdown("### 🧾 Summary")
    st.write(f"- **Age:** {age}")
    st.write(f"- **Heart Rate:** {heart_rate}")
    st.write(f"- **Sleep:** {sleep} hrs")
    st.write(f"- **Steps:** {steps}")
    st.write(f"- **Stress Level:** {stress}")

    if issues:
        st.markdown("### ⚠️ Detected Issues")
        for i in issues:
            st.write(f"- {i}")

        st.markdown("### 💡 Suggestions")
        if "Low Physical Activity" in issues:
            st.write("- Increase daily walking (6,000–10,000 steps)")
        if "Poor Sleep Duration" in issues:
            st.write("- Maintain consistent sleep schedule (7–8 hrs)")
        if "High Stress Level" in issues:
            st.write("- Try meditation, breathing exercises")
        if "Abnormal Heart Rate" in issues:
            st.write("- Monitor heart rate and avoid overexertion")
