import os
import json
import tempfile
import traceback
from io import StringIO
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from flask import Flask, request, jsonify, render_template, send_file

# Import preprocessing, model, anomaly detection from the existing modules
from module.module1_preprocessing import preprocess_data
from module.module2_features_model import run_modeling
from module.module3_anomaly_detection import detect_anomalies
from utils.charts import line_with_anomalies
import plotly.io as pio

app = Flask(__name__, template_folder='templates')

# In-memory storage for the active dataset and model output
ACTIVE_DF = None
ACTIVE_MODEL_OUT = None
ACTIVE_RAW_CSV = None  # To support downloading the full raw dataset later

# ---------------- HELPER FUNCTIONS ----------------

def parse_blood_pressure(bp_str):
    """
    Parses blood pressure string. Handles:
    - '120/80' -> (120, 80)
    - '40' (single number) -> (40, 24)
    - Fallback -> (120, 80)
    """
    try:
        parts = str(bp_str).replace(" ", "").split("/")
        if len(parts) == 2:
            return int(parts[0]), int(parts[1])
        elif len(parts) == 1 and parts[0].isdigit():
            systolic = int(parts[0])
            diastolic = int(round(systolic * 0.6))
            return systolic, diastolic
    except Exception:
        pass
    return 120, 80


def run_flask_pipeline(df_raw, resample_rule="1H"):
    """
    Executes the exact preprocessing, modeling, and anomaly detection steps
    sequentially, without using Streamlit decorators.
    """
    df0 = df_raw.copy()
    if "Person_ID" in df0.columns:
        df0["Person_ID"] = df0["Person_ID"].astype(str)
    
    anomaly_cols = [
        "Heart_Rate_anomaly",
        "Daily_Steps_anomaly",
        "Sleep_Duration_anomaly"
    ]
    
    # Check if this is already a pre-computed anomalies CSV
    if all(col in df0.columns for col in anomaly_cols):
        if "Timestamp" not in df0.columns and "timestamp" in df0.columns:
            df0 = df0.rename(columns={"timestamp": "Timestamp"})
        if "Timestamp" in df0.columns:
            df0["Timestamp"] = pd.to_datetime(df0["Timestamp"], errors="coerce")
            df0 = df0.dropna(subset=["Timestamp"]).sort_values("Timestamp")
        
        # Module 2 modeling (for clustering and forecasting insights)
        module2_out = run_modeling(df0)
        return df0, module2_out

    # Otherwise run full pipeline
    df_clean = preprocess_data(df0, resample_rule=resample_rule)

    if "Timestamp" in df_clean.columns:
        df_clean["Timestamp"] = pd.to_datetime(df_clean["Timestamp"], errors="coerce")
        df_clean = df_clean.dropna(subset=["Timestamp"])
        df_clean = df_clean.sort_values("Timestamp")
        df_clean = df_clean.drop_duplicates(subset=["Timestamp"], keep="last")

    module2_out = run_modeling(df_clean)
    df_final = detect_anomalies(df_clean)

    # Force Person_ID to string in final output as well
    if "Person_ID" in df_final.columns:
        df_final["Person_ID"] = df_final["Person_ID"].astype(str)

    return df_final, module2_out


def simulate_user_data(person_id, age, sleep_duration, daily_steps, stress_level, weight_category, bp, avg_hr):
    """
    Generates 5 days of hourly records (120 hours total) centered around user inputs
    with natural noise and deliberate anomalies.
    """
    systolic, diastolic = parse_blood_pressure(bp)
        
    end_time = pd.Timestamp.now().floor("h")
    start_time = end_time - pd.Timedelta(days=5)
    timestamps = pd.date_range(start=start_time, end=end_time, freq="h")[:120]
    
    rows = []
    np.random.seed(42)  # Seed for reproducible simulations
    
    for i, ts in enumerate(timestamps):
        day = (ts - start_time).days + 1  # 1 to 5
        hour = ts.hour
        
        # Sleep hour logic (10 PM to 6 AM)
        is_sleep = (hour >= 22) or (hour < 6)
        
        # Quality of sleep (5 to 9)
        quality_of_sleep = max(4, min(10, int(9 - stress_level / 2.0)))
        
        # Physical Activity level (1 to 100)
        pa_level = max(5, min(95, int(daily_steps / 100.0 - stress_level * 2)))
        
        # Hourly Steps distribution
        hourly_steps = 0
        if not is_sleep:
            peak_factor = 1.0
            if hour in [8, 9, 12, 13, 17, 18]:
                peak_factor = 2.0
            elif hour in [14, 15, 16]:
                peak_factor = 0.5
            
            base_hr_steps = daily_steps / 15.0
            hourly_steps = int(np.random.normal(base_hr_steps * peak_factor, base_hr_steps * 0.3))
            hourly_steps = max(0, hourly_steps)
            
            # Steps Anomaly on Day 4: very low steps all day
            if day == 4:
                hourly_steps = int(hourly_steps * 0.1)
                
        # Calculate daily steps accumulated so far
        # NOTE: rows stores '_ts' as actual pd.Timestamp for .date() comparison
        day_rows = [r for r in rows if r['_ts'].date() == ts.date()]
        daily_steps_so_far = sum(r['Hourly_Steps'] for r in day_rows) + hourly_steps
        
        # Heart Rate logic
        hr_noise = np.random.normal(0, 3)
        if is_sleep:
            hr = avg_hr - 8 + hr_noise
        else:
            activity_elev = (hourly_steps / 1500.0) * 15.0
            hr = avg_hr + activity_elev + hr_noise
            
        # Heart Rate Anomaly on Day 3 at 14:00 (spike!)
        if day == 3 and hour == 14:
            hr = 155.0
            
        # Sleep duration daily variance
        sleep_durations_by_day = {
            1: sleep_duration + 0.2,
            2: 4.5,  # Sleep Anomaly on Day 2: very low sleep
            3: sleep_duration - 0.5,
            4: sleep_duration + 0.1,
            5: sleep_duration
        }
        curr_sleep_dur = sleep_durations_by_day.get(day, sleep_duration)
        
        row = {
            "_ts": ts,  # Keep native Timestamp for in-loop comparisons
            "Timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
            "Person_ID": person_id,
            "Age": age,
            "Sleep_Duration": curr_sleep_dur,
            "Quality_of_Sleep": quality_of_sleep,
            "Physical_Activity_Level": pa_level,
            "Stress_Level": stress_level,
            "Weight_Category": weight_category,
            "Systolic_Blood_Pressure": systolic,
            "Diastolic_Blood_Pressure": diastolic,
            "Heart_Rate": round(max(40, hr), 1),
            "Daily_Steps": daily_steps_so_far,
            "Is_Sleep": "TRUE" if is_sleep else "FALSE",
            "Hourly_Steps": hourly_steps
        }
        rows.append(row)
        
    df_out = pd.DataFrame(rows)
    # Drop internal helper column used only for in-loop date comparisons
    if "_ts" in df_out.columns:
        df_out = df_out.drop(columns=["_ts"])
    return df_out


def generate_ai_suggestions(df_user):
    """
    Expert heuristic engine simulating clinical AI analysis on active user metrics.
    """
    if df_user.empty:
        return {}

    # Extract averages and details
    age = int(df_user["Age"].iloc[0]) if "Age" in df_user.columns else 30
    weight = df_user["Weight_Category"].iloc[0] if "Weight_Category" in df_user.columns else "Normal"
    systolic = int(df_user["Systolic_Blood_Pressure"].mean()) if "Systolic_Blood_Pressure" in df_user.columns else 120
    diastolic = int(df_user["Diastolic_Blood_Pressure"].mean()) if "Diastolic_Blood_Pressure" in df_user.columns else 80
    stress = float(df_user["Stress_Level"].mean()) if "Stress_Level" in df_user.columns else 5.0
    
    avg_hr = float(df_user["Heart_Rate"].mean()) if "Heart_Rate" in df_user.columns else 70.0
    avg_sleep = float(df_user["Sleep_Duration"].mean()) if "Sleep_Duration" in df_user.columns else 7.0
    
    # Calculate average daily steps (taking max step per day and averaging)
    if "Daily_Steps" in df_user.columns and "Timestamp" in df_user.columns:
        df_copy = df_user.copy()
        df_copy["Date"] = pd.to_datetime(df_copy["Timestamp"]).dt.date
        avg_steps = float(df_copy.groupby("Date")["Daily_Steps"].max().mean())
    else:
        avg_steps = 7000.0

    # Counts of detected anomalies
    hr_anoms = int(df_user["Heart_Rate_anomaly"].astype(int).sum()) if "Heart_Rate_anomaly" in df_user.columns else 0
    sleep_anoms = int(df_user["Sleep_Duration_anomaly"].astype(int).sum()) if "Sleep_Duration_anomaly" in df_user.columns else 0
    steps_anoms = int(df_user["Daily_Steps_anomaly"].astype(int).sum()) if "Daily_Steps_anomaly" in df_user.columns else 0
    total_anoms = hr_anoms + sleep_anoms + steps_anoms

    anomalies_found = []
    recommendations = []
    
    # Blood Pressure analysis
    bp_status = "Normal"
    bp_color = "green"
    if systolic >= 140 or diastolic >= 90:
        bp_status = "Hypertension Stage 2"
        bp_color = "red"
        recommendations.append({
            "metric": "Blood Pressure",
            "status": "Critical",
            "text": f"Your average BP is {systolic}/{diastolic} mmHg ({bp_status}). Consult a health professional to monitor cardiovascular strain.",
            "icon": "fa-heart-pulse"
        })
    elif systolic >= 130 or (diastolic >= 80 and diastolic <= 89):
        bp_status = "Hypertension Stage 1"
        bp_color = "orange"
        recommendations.append({
            "metric": "Blood Pressure",
            "status": "Warning",
            "text": f"Your average BP is {systolic}/{diastolic} mmHg ({bp_status}). Reduce sodium intake and engage in daily cardio.",
            "icon": "fa-heart-pulse"
        })
    elif systolic >= 120 and systolic <= 129:
        bp_status = "Elevated"
        bp_color = "yellow"
        recommendations.append({
            "metric": "Blood Pressure",
            "status": "Info",
            "text": f"Your BP is slightly Elevated ({systolic}/{diastolic} mmHg). Monitor stress levels and hydration.",
            "icon": "fa-heart-pulse"
        })
    else:
        recommendations.append({
            "metric": "Blood Pressure",
            "status": "Good",
            "text": f"Blood Pressure is optimal: {systolic}/{diastolic} mmHg.",
            "icon": "fa-heart-pulse"
        })

    # Anomaly notifications
    if hr_anoms > 0:
        anomalies_found.append(f"Detected {hr_anoms} unexplained Heart Rate anomaly spike(s) departing from your baseline trend.")
        recommendations.append({
            "metric": "Heart Rate",
            "status": "Critical",
            "text": "Cardiovascular spike detected. Avoid stimulants or sudden extreme workouts during these high stress periods.",
            "icon": "fa-gauge-high"
        })
    
    if sleep_anoms > 0:
        anomalies_found.append(f"Detected {sleep_anoms} sleep duration anomaly drop(s) below standard thresholds.")
        recommendations.append({
            "metric": "Sleep",
            "status": "Warning",
            "text": "Sleep duration experienced severe deficits. Establish a winding down routine (no screen time 1 hour before bed).",
            "icon": "fa-moon"
        })

    if steps_anoms > 0:
        anomalies_found.append(f"Detected {steps_anoms} steps anomaly event(s) signaling a significant drop in baseline movement.")
        recommendations.append({
            "metric": "Activity",
            "status": "Warning",
            "text": "Sedentary periods exceeded normal margins. Set hourly desktop reminders to stretch and walk for 5 minutes.",
            "icon": "fa-person-walking"
        })

    # General health metrics analysis
    if avg_steps < 5000:
        recommendations.append({
            "metric": "Steps Goal",
            "status": "Warning",
            "text": f"Averages steps ({int(avg_steps)}) are highly sedentary. Aim to reach at least 8,000 steps daily to promote overall longevity.",
            "icon": "fa-shoe-prints"
        })
    elif avg_steps >= 10000:
        recommendations.append({
            "metric": "Steps Goal",
            "status": "Good",
            "text": f"Excellent physical activity! You are hitting {int(avg_steps)} steps per day, meeting cardiorespiratory targets.",
            "icon": "fa-circle-check"
        })
        
    if avg_sleep < 6.0:
        recommendations.append({
            "metric": "Sleep Goal",
            "status": "Warning",
            "text": f"Your average sleep is {avg_sleep:.1f} hrs, below the healthy 7-8 hour window. Lack of sleep impairs cognitive recovery.",
            "icon": "fa-bed"
        })

    if stress > 6.5:
        recommendations.append({
            "metric": "Stress Management",
            "status": "Warning",
            "text": f"Average stress level is high ({stress:.1f}/10). Incorporate breathing intervals (4-7-8 method) during peak hours.",
            "icon": "fa-brain"
        })

    # Formulating the Health Score
    # Starting score is 100, reduced by anomalies and health deficits
    score = 100
    score -= total_anoms * 8
    if bp_status.startswith("Hypertension"):
        score -= 15
    elif bp_status == "Elevated":
        score -= 5
    if avg_steps < 5000:
        score -= 10
    if avg_sleep < 6.0:
        score -= 10
    if stress > 7.0:
        score -= 10
    score = max(10, min(100, score))

    if score >= 85:
        overall_status = "Excellent"
        status_color = "green"
    elif score >= 60:
        overall_status = "Concerned"
        status_color = "orange"
    else:
        overall_status = "Critical"
        status_color = "red"

    # AI Summary paragraph
    summary_sentences = [
        f"Diagnostic review for {df_user['Person_ID'].iloc[0]} (Age {age}, Weight Category: {weight}).",
        f"Your health profile generates an overall Health Score of {score}/100, placing you in the '{overall_status}' category."
    ]
    if total_anoms > 0:
        summary_sentences.append(f"The analysis identified {total_anoms} anomaly events. Our Prophet and DBSCAN clustering models marked outliers that deviate from your personal baseline.")
    else:
        summary_sentences.append("No statistical anomalies were flagged by the machine learning models. Your bio-metric trends remain consistent.")
        
    if bp_status.startswith("Hypertension"):
        summary_sentences.append(f"However, your blood pressure indicates elevated cardiovascular workloads ({bp_status}).")
    
    summary = " ".join(summary_sentences)

    clinical_note = (
        "This diagnostic evaluation represents a statistical analysis of fitness watch metrics "
        "and rule-based thresholds. It does not substitute professional clinical advice."
    )

    return {
        "score": score,
        "overall_status": overall_status,
        "status_color": status_color,
        "summary": summary,
        "anomalies_found": anomalies_found,
        "recommendations": recommendations,
        "clinical_note": clinical_note
    }

# ---------------- API ENDPOINTS ----------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/get_users", methods=["GET"])
def get_users():
    global ACTIVE_DF
    if ACTIVE_DF is None or ACTIVE_DF.empty:
        return jsonify({"users": []})
    
    if "Person_ID" in ACTIVE_DF.columns:
        users = sorted([str(u) for u in ACTIVE_DF["Person_ID"].dropna().unique()])
    else:
        users = ["All Users"]
    return jsonify({"users": users})


@app.route("/api/get_dashboard_data", methods=["GET"])
def get_dashboard():
    global ACTIVE_DF
    if ACTIVE_DF is None or ACTIVE_DF.empty:
        return jsonify({"error": "No active dataset. Upload a CSV or enter details."}), 400
    
    user_id = request.args.get("user", "All Users")
    df = ACTIVE_DF.copy()
    
    if user_id != "All Users" and "Person_ID" in df.columns:
        df = df[df["Person_ID"].astype(str) == str(user_id)]
        
    if df.empty:
        return jsonify({"error": f"No data found for user {user_id}"}), 400

    # Rename Timestamp if needed
    if "Timestamp" in df.columns and "timestamp" not in df.columns:
        df = df.rename(columns={"Timestamp": "timestamp"})

    # KPI stats
    avg_hr = round(df["Heart_Rate"].mean(), 1) if "Heart_Rate" in df.columns else 0.0
    avg_sleep = round(df["Sleep_Duration"].mean(), 1) if "Sleep_Duration" in df.columns else 0.0
    total_steps = int(df["Daily_Steps"].max()) if "Daily_Steps" in df.columns else 0 # max of cumulative or sum of hourly
    
    # Check if steps resetting is used
    if "Daily_Steps" in df.columns and "timestamp" in df.columns:
        # Sum of maximum daily steps if All Users, or max if single user
        df_c = df.copy()
        df_c["Date"] = pd.to_datetime(df_c["timestamp"]).dt.date
        if user_id == "All Users" and "Person_ID" in df_c.columns:
            total_steps = int(df_c.groupby(["Person_ID", "Date"])["Daily_Steps"].max().sum())
        else:
            total_steps = int(df_c.groupby("Date")["Daily_Steps"].max().sum())
    
    # Anomaly counts
    hr_anoms = int(df["Heart_Rate_anomaly"].astype(int).sum()) if "Heart_Rate_anomaly" in df.columns else 0
    sleep_anoms = int(df["Sleep_Duration_anomaly"].astype(int).sum()) if "Sleep_Duration_anomaly" in df.columns else 0
    steps_anoms = int(df["Daily_Steps_anomaly"].astype(int).sum()) if "Daily_Steps_anomaly" in df.columns else 0
    total_anoms = hr_anoms + sleep_anoms + steps_anoms

    # User details (from first row)
    row0 = df.iloc[0]
    user_details = {
        "person_id": str(row0.get("Person_ID", "N/A")),
        "age": int(row0.get("Age", 0)) if pd.notna(row0.get("Age")) else "N/A",
        "weight": str(row0.get("Weight_Category", "N/A")),
        "stress": str(row0.get("Stress_Level", "N/A")),
        "bp": f"{int(row0.get('Systolic_Blood_Pressure', 120))}/{int(row0.get('Diastolic_Blood_Pressure', 80))}" if pd.notna(row0.get("Systolic_Blood_Pressure")) else "N/A",
        "sleep_quality": str(row0.get("Quality_of_Sleep", "N/A"))
    }

    # Generate AI insights
    ai_insights = generate_ai_suggestions(df)

    # Anomaly table data
    cond = False
    if "Heart_Rate_anomaly" in df.columns:
        cond = cond | (df["Heart_Rate_anomaly"].astype(int) == 1)
    if "Daily_Steps_anomaly" in df.columns:
        cond = cond | (df["Daily_Steps_anomaly"].astype(int) == 1)
    if "Sleep_Duration_anomaly" in df.columns:
        cond = cond | (df["Sleep_Duration_anomaly"].astype(int) == 1)

    df_anom = df[cond].copy() if not isinstance(cond, bool) else pd.DataFrame()
    anomalies_list = []
    
    if not df_anom.empty:
        if "timestamp" in df_anom.columns:
            df_anom = df_anom.sort_values("timestamp", ascending=False)
        for _, row in df_anom.iterrows():
            types = []
            if "Heart_Rate_anomaly" in row and int(row["Heart_Rate_anomaly"]) == 1:
                types.append("Heart Rate")
            if "Daily_Steps_anomaly" in row and int(row["Daily_Steps_anomaly"]) == 1:
                types.append("Steps")
            if "Sleep_Duration_anomaly" in row and int(row["Sleep_Duration_anomaly"]) == 1:
                types.append("Sleep")
                
            anomalies_list.append({
                "timestamp": str(row.get("timestamp", "N/A")),
                "user": str(row.get("Person_ID", "N/A")),
                "type": ", ".join(types),
                "hr": row.get("Heart_Rate", "N/A"),
                "sleep": row.get("Sleep_Duration", "N/A"),
                "steps": row.get("Daily_Steps", "N/A")
            })

    # Return raw logs for the logs editor
    raw_logs = []
    df_sorted = df.copy()
    if "timestamp" in df_sorted.columns:
        df_sorted = df_sorted.sort_values("timestamp", ascending=False)
    for _, row in df_sorted.iterrows():
        # Format timestamp consistently as ISO format without microseconds
        ts = row.get("timestamp", "N/A")
        if pd.notna(ts) and ts != "N/A":
            try:
                ts = pd.to_datetime(ts).strftime("%Y-%m-%d %H:%M:%S")
            except:
                ts = str(ts)
        raw_logs.append({
            "timestamp": ts,
            "hr": row.get("Heart_Rate", "N/A"),
            "sleep": row.get("Sleep_Duration", "N/A"),
            "steps": row.get("Daily_Steps", "N/A"),
            "hourly_steps": row.get("Hourly_Steps", row.get("Daily_Steps", 0))
        })

    return jsonify({
        "kpis": {
            "avg_hr": avg_hr,
            "avg_sleep": avg_sleep,
            "total_steps": total_steps,
            "total_anoms": total_anoms,
            "hr_anoms": hr_anoms,
            "sleep_anoms": sleep_anoms,
            "steps_anoms": steps_anoms
        },
        "user_details": user_details,
        "ai_insights": ai_insights,
        "anomalies": anomalies_list,
        "raw_logs": raw_logs
    })


@app.route("/api/get_charts", methods=["GET"])
def get_charts():
    global ACTIVE_DF
    if ACTIVE_DF is None or ACTIVE_DF.empty:
        return jsonify({"error": "No active dataset"}), 400
    
    user_id = request.args.get("user", "All Users")
    df = ACTIVE_DF.copy()
    
    if user_id != "All Users" and "Person_ID" in df.columns:
        df = df[df["Person_ID"].astype(str) == str(user_id)]
        
    if df.empty:
        return jsonify({"error": f"No data found for user {user_id}"}), 400

    if "Timestamp" in df.columns and "timestamp" not in df.columns:
        df = df.rename(columns={"Timestamp": "timestamp"})

    # Check columns
    has_hr = "Heart_Rate" in df.columns
    has_sleep = "Sleep_Duration" in df.columns
    has_steps = "Daily_Steps" in df.columns

    hr_json, sleep_json, steps_json = "{}", "{}", "{}"

    if has_hr:
        fig_hr = line_with_anomalies(
            df=df, x="timestamp", y="Heart_Rate",
            anom_col="Heart_Rate_anomaly" if "Heart_Rate_anomaly" in df.columns else None,
            baseline_col="Heart_Rate_baseline" if "Heart_Rate_baseline" in df.columns else None,
            title="Heart Rate Trend vs Baseline + Anomalies"
        )
        # Add target line (normal HR zone 60-100)
        fig_hr.add_shape(type="line", x0=df["timestamp"].min(), x1=df["timestamp"].max(), y0=60, y1=60,
                         line=dict(color="rgba(0,0,255,0.4)", width=1, dash="dot"))
        fig_hr.add_shape(type="line", x0=df["timestamp"].min(), x1=df["timestamp"].max(), y0=100, y1=100,
                         line=dict(color="rgba(255,0,0,0.4)", width=1, dash="dot"))
        hr_json = pio.to_json(fig_hr)

    if has_sleep:
        fig_sleep = line_with_anomalies(
            df=df, x="timestamp", y="Sleep_Duration",
            anom_col="Sleep_Duration_anomaly" if "Sleep_Duration_anomaly" in df.columns else None,
            baseline_col="Sleep_Duration_baseline" if "Sleep_Duration_baseline" in df.columns else None,
            title="Sleep Duration Trend vs Baseline + Anomalies"
        )
        # Add 7-hour target line
        fig_sleep.add_shape(type="line", x0=df["timestamp"].min(), x1=df["timestamp"].max(), y0=7.0, y1=7.0,
                            line=dict(color="rgba(0,128,0,0.5)", width=2, dash="dash"))
        sleep_json = pio.to_json(fig_sleep)

    if has_steps:
        fig_steps = line_with_anomalies(
            df=df, x="timestamp", y="Daily_Steps",
            anom_col="Daily_Steps_anomaly" if "Daily_Steps_anomaly" in df.columns else None,
            baseline_col="Daily_Steps_baseline" if "Daily_Steps_baseline" in df.columns else None,
            title="Steps Accumulation Trend vs Baseline + Anomalies"
        )
        # Add 10k steps daily target line
        fig_steps.add_shape(type="line", x0=df["timestamp"].min(), x1=df["timestamp"].max(), y0=10000, y1=10000,
                            line=dict(color="rgba(255,165,0,0.6)", width=2, dash="dash"))
        steps_json = pio.to_json(fig_steps)

    return jsonify({
        "hr": json.loads(hr_json),
        "sleep": json.loads(sleep_json),
        "steps": json.loads(steps_json)
    })


@app.route("/api/get_model_insights", methods=["GET"])
def get_model_insights():
    global ACTIVE_DF, ACTIVE_MODEL_OUT
    if ACTIVE_MODEL_OUT is None or ACTIVE_DF is None or ACTIVE_DF.empty:
        return jsonify({"error": "No modeling run available"}), 400
    
    out = ACTIVE_MODEL_OUT

    # 1. TSFresh Top Features
    features_chart_json = "{}"
    features_df = out.get("features_df")
    if features_df is not None and not features_df.empty:
        required_patterns = [
            "__c3__lag_1", "__c3__lag_2", "__c3__lag_3",
            "__time_reversal_asymmetry_statistic__lag_2",
            "__time_reversal_asymmetry_statistic__lag_3"
        ]
        selected_features = [
            col for col in features_df.columns
            if any(pat in col for pat in required_patterns)
        ]
        if len(selected_features) > 0:
            var_series = features_df[selected_features].var().sort_values(ascending=False)
            chart_df = var_series.reset_index()
            chart_df.columns = ["feature", "variance"]
            
            fig_features = px.bar(
                chart_df, x="variance", y="feature", orientation="h",
                title="TSFresh Top Features by Variance"
            )
            fig_features.update_layout(template="plotly_white", height=350, margin=dict(l=10, r=10, t=40, b=10))
            features_chart_json = pio.to_json(fig_features)

    # 2. Prophet Forecasts
    prophet_charts = {}
    pf = out.get("prophet_forecasts")
    if pf:
        for metric, forecast_df in pf.items():
            # Convert pandas Series to plain Python lists so that
            # pio.to_json produces JSON arrays instead of binary-encoded
            # bdata dicts that Plotly.js may not decode correctly.
            x_vals = forecast_df["ds"].astype(str).tolist()
            y_hat = forecast_df["yhat"].tolist()
            y_upper = forecast_df["yhat_upper"].tolist()
            y_lower = forecast_df["yhat_lower"].tolist()

            fig_pf = go.Figure()
            fig_pf.add_trace(go.Scatter(x=x_vals, y=y_hat, mode="lines", name="Forecast (yhat)"))
            fig_pf.add_trace(go.Scatter(x=x_vals, y=y_upper, mode="lines", name="Upper Bound", line=dict(dash="dot"), opacity=0.6))
            fig_pf.add_trace(go.Scatter(x=x_vals, y=y_lower, mode="lines", name="Lower Bound", line=dict(dash="dot"), opacity=0.6))
            fig_pf.update_layout(
                template="plotly_white", height=400, title=f"Prophet forecast: {metric}",
                margin=dict(l=10, r=10, t=40, b=10), legend=dict(orientation="h", y=1.02, x=1, xanchor="right")
            )
            prophet_charts[metric] = json.loads(pio.to_json(fig_pf))

    # 3. DBSCAN PCA Clustering
    clustering_chart_json = "{}"
    clus = out.get("clustering_df")
    if clus is not None and not clus.empty:
        fig_db = px.scatter(
            clus, x="pca1", y="pca2", color=clus["cluster"].astype(str),
            title="DBSCAN Clustering Projection (PCA 2D)",
            labels={"color": "Cluster"}
        )
        fig_db.update_layout(template="plotly_white", height=400, margin=dict(l=10, r=10, t=40, b=10))
        clustering_chart_json = pio.to_json(fig_db)

    # Info summary
    features_count = features_df.shape[1] if features_df is not None else 0
    clusters_count = 0
    noise_points = 0
    clustering_skip_reason = out.get("clustering_skip_reason")
    if clus is not None and not clus.empty:
        clusters = clus["cluster"]
        clusters_count = len(set(clusters)) - (1 if -1 in set(clusters) else 0)
        noise_points = int((clusters == -1).sum())

    return jsonify({
        "features_count": features_count,
        "clusters_count": clusters_count,
        "noise_points": noise_points,
        "clustering_skip_reason": clustering_skip_reason,
        "features_chart": json.loads(features_chart_json),
        "prophet_charts": prophet_charts,
        "clustering_chart": json.loads(clustering_chart_json)
    })


@app.route("/api/upload_csv", methods=["POST"])
def upload_csv():
    global ACTIVE_DF, ACTIVE_MODEL_OUT, ACTIVE_RAW_CSV
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    try:
        df_raw = pd.read_csv(file)
        
        # Normalize Timestamp column to ISO format for consistency across all operations
        if "Timestamp" in df_raw.columns:
            df_raw["Timestamp"] = pd.to_datetime(df_raw["Timestamp"], errors="coerce").dt.strftime("%Y-%m-%d %H:%M:%S")
        
        # Save raw CSV representation as a string
        ACTIVE_RAW_CSV = df_raw.to_csv(index=False)
        
        # Run pipeline
        df_final, model_out = run_flask_pipeline(df_raw)
        
        ACTIVE_DF = df_final
        ACTIVE_MODEL_OUT = model_out
        
        return jsonify({
            "status": "success",
            "message": "File parsed and modeling pipeline run successfully!",
            "users_count": len(df_final["Person_ID"].unique()) if "Person_ID" in df_final.columns else 1,
            "raw_csv": ACTIVE_RAW_CSV
        })
    except Exception as e:
        return jsonify({"error": f"Failed to run pipeline: {str(e)}"}), 500


@app.route("/api/load_demo", methods=["POST"])
def load_demo():
    global ACTIVE_DF, ACTIVE_MODEL_OUT, ACTIVE_RAW_CSV
    try:
        demo_path = os.path.join("data", "sample_fitness_data.csv")
        if not os.path.exists(demo_path):
            return jsonify({"error": "Demo file sample_fitness_data.csv not found in data/"}), 404
        
        df_raw = pd.read_csv(demo_path)
        
        # Normalize Timestamp column to ISO format for consistency across all operations
        if "Timestamp" in df_raw.columns:
            df_raw["Timestamp"] = pd.to_datetime(df_raw["Timestamp"], errors="coerce").dt.strftime("%Y-%m-%d %H:%M:%S")
        
        ACTIVE_RAW_CSV = df_raw.to_csv(index=False)
        df_final, model_out = run_flask_pipeline(df_raw)
        
        ACTIVE_DF = df_final
        ACTIVE_MODEL_OUT = model_out
        
        return jsonify({
            "status": "success",
            "message": "Demo data loaded successfully!",
            "raw_csv": ACTIVE_RAW_CSV
        })
    except Exception as e:
        return jsonify({"error": f"Failed to load demo data: {str(e)}"}), 500


@app.route("/api/add_user_log", methods=["POST"])
def add_user_log():
    global ACTIVE_DF, ACTIVE_MODEL_OUT, ACTIVE_RAW_CSV
    data = request.json
    if not data:
        return jsonify({"error": "No form data received"}), 400
    
    try:
        name = data.get("name", "User_New")
        age = int(data.get("age", 30))
        weight = data.get("weight", "Normal")
        stress = int(data.get("stress", 5))
        bp = data.get("bp", "120/80")
        hr = int(data.get("hr", 72))
        sleep = float(data.get("sleep", 7.5))
        steps = int(data.get("steps", 8000))
        
        # Simulate 5-day dataset for this new user
        df_simulated = simulate_user_data(
            person_id=name, age=age, sleep_duration=sleep,
            daily_steps=steps, stress_level=stress,
            weight_category=weight, bp=bp, avg_hr=hr
        )
        
        # Append or create active dataset
        if ACTIVE_DF is not None and not ACTIVE_DF.empty:
            # We must load the raw data version, append the raw simulated data, and rerun the pipeline.
            # That way all indicators, baselines, and DBSCAN features are recalculated globally!
            df_raw_old = pd.read_csv(StringIO(ACTIVE_RAW_CSV))
            
            # Ensure matching column structures
            # Strip target columns like anomalies from simulated if present
            df_sim_raw = df_simulated[df_raw_old.columns.intersection(df_simulated.columns)].copy()
            df_raw_merged = pd.concat([df_raw_old, df_sim_raw], ignore_index=True)
        else:
            df_raw_merged = df_simulated
            
        ACTIVE_RAW_CSV = df_raw_merged.to_csv(index=False)
        df_final, model_out = run_flask_pipeline(df_raw_merged)
        
        ACTIVE_DF = df_final
        ACTIVE_MODEL_OUT = model_out
        
        return jsonify({
            "status": "success",
            "message": f"Successfully simulated 120 hourly logs and calculated models for {name}!",
            "user_id": name,
            "raw_csv": ACTIVE_RAW_CSV
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Failed to simulate user profile: {str(e)}"}), 500


@app.route("/api/add_hourly_log", methods=["POST"])
def add_hourly_log():
    global ACTIVE_DF, ACTIVE_MODEL_OUT, ACTIVE_RAW_CSV
    data = request.json
    if not data or ACTIVE_DF is None or ACTIVE_DF.empty:
        return jsonify({"error": "No active dataset to log into"}), 400
    
    try:
        user_id = str(data.get("user")).strip()
        timestamp = data.get("timestamp")  # YYYY-MM-DD HH:MM:SS
        hr = float(data.get("hr"))
        sleep = float(data.get("sleep"))
        hourly_steps = int(data.get("steps"))
        
        # Load raw active dataset
        df_raw = pd.read_csv(StringIO(ACTIVE_RAW_CSV))
        
        # Normalize Timestamp column to ISO format for consistency
        if "Timestamp" in df_raw.columns:
            df_raw["Timestamp"] = pd.to_datetime(df_raw["Timestamp"], errors="coerce").dt.strftime("%Y-%m-%d %H:%M:%S")
        
        # Get details from existing rows for this user (Age, Weight, BP, etc.)
        user_rows = df_raw[df_raw["Person_ID"].astype(str) == str(user_id)]
        if user_rows.empty:
            user_rows = df_raw  # fallback
            
        row0 = user_rows.iloc[0]
        
        # Parse the new log date
        log_date = pd.to_datetime(timestamp).date()
        log_date_str = str(log_date)  # YYYY-MM-DD format
        
        # Find all rows from the same date and user to calculate total daily steps
        df_raw["_date"] = pd.to_datetime(df_raw["Timestamp"], errors="coerce").dt.strftime("%Y-%m-%d")
        df_raw["_person_id_str"] = df_raw["Person_ID"].astype(str)
        
        same_day_rows = df_raw[(df_raw["_date"] == log_date_str) & (df_raw["_person_id_str"] == user_id)]
        current_daily_steps = same_day_rows["Hourly_Steps"].fillna(0).sum()
        daily_steps_accum = current_daily_steps + hourly_steps
        
        # Create new raw row with ISO format timestamp
        new_row = {
            "Timestamp": timestamp,
            "Person_ID": user_id,
            "Age": row0.get("Age"),
            "Sleep_Duration": sleep,
            "Quality_of_Sleep": row0.get("Quality_of_Sleep"),
            "Physical_Activity_Level": row0.get("Physical_Activity_Level"),
            "Stress_Level": row0.get("Stress_Level"),
            "Weight_Category": row0.get("Weight_Category"),
            "Systolic_Blood_Pressure": row0.get("Systolic_Blood_Pressure"),
            "Diastolic_Blood_Pressure": row0.get("Diastolic_Blood_Pressure"),
            "Heart_Rate": hr,
            "Daily_Steps": daily_steps_accum,
            "Is_Sleep": "TRUE" if (pd.to_datetime(timestamp).hour >= 22 or pd.to_datetime(timestamp).hour < 6) else "FALSE",
            "Hourly_Steps": hourly_steps
        }
        
        # Add the new row
        df_raw = pd.concat([df_raw, pd.DataFrame([new_row])], ignore_index=True)
        
        # Now update Daily_Steps for all rows from the same day (for the user) with the new total
        df_raw.loc[(df_raw["_date"] == log_date_str) & (df_raw["_person_id_str"] == user_id), "Daily_Steps"] = daily_steps_accum
        
        # Clean up temporary columns
        df_raw = df_raw.drop(columns=["_date", "_person_id_str"], errors="ignore")
        
        # Re-run full pipeline with all visualization, preprocessing, modeling
        ACTIVE_RAW_CSV = df_raw.to_csv(index=False)
        df_final, model_out = run_flask_pipeline(df_raw)
        
        ACTIVE_DF = df_final
        ACTIVE_MODEL_OUT = model_out
        
        return jsonify({
            "status": "success",
            "message": "Hourly log added and metrics re-analyzed!",
            "raw_csv": ACTIVE_RAW_CSV
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Failed to log hour: {str(e)}"}), 500


@app.route("/api/delete_log_row", methods=["POST"])
def delete_log_row():
    global ACTIVE_DF, ACTIVE_MODEL_OUT, ACTIVE_RAW_CSV
    data = request.json
    if not data or ACTIVE_DF is None or ACTIVE_DF.empty:
        return jsonify({"error": "No active dataset"}), 400
    
    try:
        user_id = str(data.get("user")).strip()
        timestamp_str = str(data.get("timestamp")).strip()
        
        df_raw = pd.read_csv(StringIO(ACTIVE_RAW_CSV))
        
        # Normalize column names: handle both "Timestamp" and "timestamp"
        ts_col = None
        if "Timestamp" in df_raw.columns:
            ts_col = "Timestamp"
        elif "timestamp" in df_raw.columns:
            ts_col = "timestamp"
        else:
            return jsonify({"error": "Timestamp column not found"}), 400
        
        # Convert incoming timestamp to datetime for robust comparison
        try:
            incoming_ts = pd.to_datetime(timestamp_str)
        except:
            return jsonify({"error": "Invalid timestamp format"}), 400
        
        # Ensure Person_ID is string for comparison
        df_raw["Person_ID"] = df_raw["Person_ID"].astype(str).str.strip()
        user_id = str(user_id).strip()
        
        # Create a normalized timestamp column for comparison (remove microseconds)
        df_raw["_ts_normalized"] = pd.to_datetime(df_raw[ts_col], errors="coerce").dt.floor("S")
        incoming_ts = incoming_ts.floor("S")
        
        # First try exact datetime match
        mask = (df_raw["Person_ID"] == user_id) & (df_raw["_ts_normalized"] == incoming_ts)
        
        if not mask.any():
            # Try minute-level matching (ignore seconds/microseconds)
            df_raw["_ts_minute"] = df_raw["_ts_normalized"].dt.floor("T")
            incoming_minute = incoming_ts.floor("T")
            mask = (df_raw["Person_ID"] == user_id) & (df_raw["_ts_minute"] == incoming_minute)
        
        if not mask.any():
            # Try day-level matching as last resort
            df_raw["_ts_day"] = df_raw["_ts_normalized"].dt.floor("D")
            incoming_day = incoming_ts.floor("D")
            mask = (df_raw["Person_ID"] == user_id) & (df_raw["_ts_day"] == incoming_day)
        
        if not mask.any():
            return jsonify({"error": "Row not found in raw dataset"}), 404
        
        # Get the date of the deleted row for Daily_Steps recalculation BEFORE dropping columns
        deleted_row_date = df_raw.loc[mask, ts_col].iloc[0]
        deleted_row_date_str = pd.to_datetime(deleted_row_date).strftime("%Y-%m-%d")
        
        # Clean up temporary columns used for matching
        df_raw = df_raw.drop(columns=["_ts_normalized", "_ts_minute", "_ts_day"], errors="ignore")
        
        # Apply the mask to delete the row - invert the mask to keep all rows EXCEPT the matched one
        df_raw = df_raw[~mask].reset_index(drop=True)
        
        if df_raw.empty:
            ACTIVE_DF = None
            ACTIVE_MODEL_OUT = None
            ACTIVE_RAW_CSV = None
            return jsonify({"status": "success", "message": "Dataset now empty", "raw_csv": None})
        
        # Recalculate Daily_Steps for all rows from the same day (user)
        # Add helper columns for filtering
        df_raw["_date"] = pd.to_datetime(df_raw[ts_col], errors="coerce").dt.strftime("%Y-%m-%d")
        df_raw["_person_id_str"] = df_raw["Person_ID"].astype(str)
        
        # Find all rows from the deleted row's date for this user
        same_day_mask = (df_raw["_date"] == deleted_row_date_str) & (df_raw["_person_id_str"] == user_id)
        same_day_rows = df_raw[same_day_mask]
        
        if len(same_day_rows) > 0:
            # Recalculate total daily steps for that day
            new_daily_total = same_day_rows["Hourly_Steps"].fillna(0).sum()
            df_raw.loc[same_day_mask, "Daily_Steps"] = new_daily_total
        
        # Clean up temporary columns
        df_raw = df_raw.drop(columns=["_date", "_person_id_str"], errors="ignore")
            
        # Re-run full pipeline with all visualization, preprocessing, modeling
        ACTIVE_RAW_CSV = df_raw.to_csv(index=False)
        df_final, model_out = run_flask_pipeline(df_raw)
        
        ACTIVE_DF = df_final
        ACTIVE_MODEL_OUT = model_out
        
        return jsonify({
            "status": "success",
            "message": "Row successfully removed. Re-running models...",
            "raw_csv": ACTIVE_RAW_CSV
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Failed to delete row: {str(e)}"}), 500


@app.route("/api/analyze_individual_metrics", methods=["POST"])
def analyze_individual_metrics():
    """Option B: Pure recommendation engine. Handles optional metrics. Does NOT modify ACTIVE_DF."""
    data = request.json
    if not data:
        return jsonify({"error": "No form data received"}), 400

    try:
        name = data.get("name", "User")
        age = int(data.get("age", 30)) if data.get("age") else 30
        weight = data.get("weight", "Normal")
        stress = int(data.get("stress", 5)) if data.get("stress") else 5
        
        # Optional metrics - only process if provided
        bp = data.get("bp")
        avg_hr = data.get("hr")
        avg_sleep = data.get("sleep")
        avg_steps = data.get("steps")

        recommendations = []
        score = 100
        metrics_provided = []
        
        # Blood Pressure analysis - ONLY if provided
        systolic, diastolic = None, None
        if bp:
            systolic, diastolic = parse_blood_pressure(bp)
            metrics_provided.append("BP")
            
            bp_status = "Normal"
            if systolic >= 140 or diastolic >= 90:
                bp_status = "Hypertension Stage 2"
                recommendations.append({"metric": "Blood Pressure", "status": "Critical",
                    "text": f"Your BP is {systolic}/{diastolic} mmHg ({bp_status}). Consult a health professional immediately.",
                    "icon": "fa-heart-pulse"})
                score -= 15
            elif systolic >= 130 or (diastolic >= 80 and diastolic <= 89):
                bp_status = "Hypertension Stage 1"
                recommendations.append({"metric": "Blood Pressure", "status": "Warning",
                    "text": f"Your BP is {systolic}/{diastolic} mmHg ({bp_status}). Reduce sodium intake and engage in daily cardio.",
                    "icon": "fa-heart-pulse"})
                score -= 10
            elif systolic >= 120 and systolic <= 129:
                bp_status = "Elevated"
                recommendations.append({"metric": "Blood Pressure", "status": "Info",
                    "text": f"Your BP is slightly Elevated ({systolic}/{diastolic} mmHg). Monitor stress and hydration.",
                    "icon": "fa-heart-pulse"})
                score -= 5
            else:
                recommendations.append({"metric": "Blood Pressure", "status": "Good",
                    "text": f"Blood Pressure is optimal: {systolic}/{diastolic} mmHg.",
                    "icon": "fa-heart-pulse"})

        # Heart Rate - ONLY if provided
        if avg_hr is not None:
            avg_hr = int(avg_hr)
            metrics_provided.append("HR")
            
            if avg_hr > 100:
                recommendations.append({"metric": "Heart Rate", "status": "Critical",
                    "text": f"Resting HR of {avg_hr} bpm is elevated (tachycardia range). Avoid stimulants. Consult a doctor if persistent.",
                    "icon": "fa-gauge-high"})
                score -= 10
            elif avg_hr < 50:
                recommendations.append({"metric": "Heart Rate", "status": "Warning",
                    "text": f"Resting HR of {avg_hr} bpm is below normal (bradycardia). If you are not an athlete, consider a check-up.",
                    "icon": "fa-gauge-high"})
                score -= 10
            else:
                recommendations.append({"metric": "Heart Rate", "status": "Good",
                    "text": f"Resting HR of {avg_hr} bpm is within normal range (60-100 bpm).",
                    "icon": "fa-gauge-high"})

        # Sleep - ONLY if provided
        if avg_sleep is not None:
            avg_sleep = float(avg_sleep)
            metrics_provided.append("Sleep")
            
            if avg_sleep < 6.0:
                recommendations.append({"metric": "Sleep", "status": "Warning",
                    "text": f"Average sleep of {avg_sleep:.1f} hrs is below the healthy 7-8 hour window. Lack of sleep impairs cognitive recovery.",
                    "icon": "fa-moon"})
                score -= 10
            elif avg_sleep > 9.0:
                recommendations.append({"metric": "Sleep", "status": "Warning",
                    "text": f"Average sleep of {avg_sleep:.1f} hrs is above optimal. Oversleeping may indicate underlying issues.",
                    "icon": "fa-moon"})
                score -= 10
            else:
                recommendations.append({"metric": "Sleep", "status": "Good",
                    "text": f"Sleep duration of {avg_sleep:.1f} hrs meets the recommended 7-9 hour target.",
                    "icon": "fa-moon"})

        # Steps - ONLY if provided
        if avg_steps is not None:
            avg_steps = int(avg_steps)
            metrics_provided.append("Steps")
            
            if avg_steps < 5000:
                recommendations.append({"metric": "Activity", "status": "Warning",
                    "text": f"Average steps ({avg_steps}) are sedentary. Aim for at least 8,000 steps daily.",
                    "icon": "fa-shoe-prints"})
                score -= 10
            elif avg_steps >= 10000:
                recommendations.append({"metric": "Activity", "status": "Good",
                    "text": f"Excellent! You hit {avg_steps} steps/day, meeting cardiovascular targets.",
                    "icon": "fa-circle-check"})
            else:
                recommendations.append({"metric": "Activity", "status": "Info",
                    "text": f"Steps ({avg_steps}) are moderate. Push towards 10,000 for optimal benefits.",
                    "icon": "fa-shoe-prints"})

        # Stress (always analyzed)
        if stress > 6:
            recommendations.append({"metric": "Stress", "status": "Warning",
                "text": f"Stress level is high ({stress}/10). Incorporate breathing exercises (4-7-8 method) during peak hours.",
                "icon": "fa-brain"})
            score -= 10
        elif stress <= 3:
            recommendations.append({"metric": "Stress", "status": "Good",
                "text": f"Stress level is low ({stress}/10). Excellent mental wellbeing.",
                "icon": "fa-brain"})

        # Age + Weight combo warnings
        if age > 50 and weight in ["Overweight", "Obese"]:
            recommendations.append({"metric": "Age & Weight", "status": "Warning",
                "text": f"At age {age} with weight category '{weight}', cardiovascular risk increases. Focus on balanced diet and regular cardio.",
                "icon": "fa-scale-balanced"})
            score -= 5

        score = max(10, min(100, score))

        if score >= 85: overall_status, status_color = "Excellent", "green"
        elif score >= 60: overall_status, status_color = "Concerned", "orange"
        else: overall_status, status_color = "Critical", "red"

        # Build summary with only provided metrics
        summary_parts = [f"Health evaluation for {name} (Age {age}, Weight: {weight}). Overall Health Score: {score}/100 — '{overall_status}'.", "Provided metrics:"]
        if bp:
            summary_parts.append(f"BP {systolic}/{diastolic} mmHg")
        if avg_hr is not None:
            summary_parts.append(f"HR {avg_hr} bpm")
        if avg_sleep is not None:
            summary_parts.append(f"Sleep {avg_sleep:.1f} hrs")
        if avg_steps is not None:
            summary_parts.append(f"Steps {avg_steps}")
        summary_parts.append(f"Stress {stress}/10")
        
        summary = ", ".join(summary_parts) + "."

        clinical_note = (
            "This evaluation is based on clinical reference ranges and rule-based thresholds. "
            "It does not substitute professional medical advice."
        )

        return jsonify({
            "score": score,
            "overall_status": overall_status,
            "status_color": status_color,
            "summary": summary,
            "recommendations": recommendations,
            "clinical_note": clinical_note
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500


@app.route("/api/reset", methods=["POST"])
def reset_dataset():
    global ACTIVE_DF, ACTIVE_MODEL_OUT, ACTIVE_RAW_CSV
    ACTIVE_DF = None
    ACTIVE_MODEL_OUT = None
    ACTIVE_RAW_CSV = None
    return jsonify({"status": "success", "message": "Dashboard reset."})


@app.route("/api/download_report", methods=["GET"])
def download_report():
    global ACTIVE_DF
    if ACTIVE_DF is None or ACTIVE_DF.empty:
        return "No active dataset", 400
        
    user_id = request.args.get("user", "All Users")
    report_type = request.args.get("type", "all")  # all, hr, sleep, steps
    
    df = ACTIVE_DF.copy()

    # Normalise timestamp column name to 'Timestamp'
    if "timestamp" in df.columns and "Timestamp" not in df.columns:
        df = df.rename(columns={"timestamp": "Timestamp"})

    if user_id != "All Users" and "Person_ID" in df.columns:
        df = df[df["Person_ID"].astype(str) == str(user_id)]
        
    if df.empty:
        return f"No data found for user {user_id}", 400

    # Filter rows and columns by report type
    if report_type == "hr":
        report_cols = [
            "Timestamp", "Person_ID", "Age", "Weight_Category",
            "Heart_Rate", "Heart_Rate_anomaly", "Heart_Rate_baseline", "Heart_Rate_residual",
            "Systolic_Blood_Pressure", "Diastolic_Blood_Pressure", "Stress_Level"
        ]
    elif report_type == "sleep":
        report_cols = [
            "Timestamp", "Person_ID", "Age", "Weight_Category",
            "Sleep_Duration", "Sleep_Duration_anomaly", "Sleep_Duration_baseline", "Sleep_Duration_residual",
            "Quality_of_Sleep", "Is_Sleep"
        ]
    elif report_type == "steps":
        report_cols = [
            "Timestamp", "Person_ID", "Age", "Weight_Category",
            "Daily_Steps", "Daily_Steps_anomaly", "Daily_Steps_baseline", "Daily_Steps_residual",
            "Hourly_Steps", "Physical_Activity_Level"
        ]
    else:
        # "all" — include everything
        report_cols = None

    if report_cols:
        # Keep only columns that exist in df
        output_cols = [c for c in report_cols if c in df.columns]
    else:
        # Select and order the most meaningful columns for the full report
        preferred_cols = [
            "Timestamp", "Person_ID", "Age", "Weight_Category",
            "Systolic_Blood_Pressure", "Diastolic_Blood_Pressure",
            "Stress_Level", "Quality_of_Sleep",
            "Heart_Rate", "Heart_Rate_anomaly",
            "Sleep_Duration", "Sleep_Duration_anomaly",
            "Daily_Steps", "Daily_Steps_anomaly",
            "Hourly_Steps", "Physical_Activity_Level", "Is_Sleep"
        ]
        output_cols = [c for c in preferred_cols if c in df.columns]
        remaining = [c for c in df.columns if c not in output_cols]
        output_cols += remaining
    df = df[output_cols]

    if df.empty:
        return f"No data found for report type '{report_type}' and user {user_id}", 404

    filename = f"fitpulse_report_{user_id}_{report_type}.xlsx"

    # Generate Excel file with openpyxl
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
    tmp.close()
    with pd.ExcelWriter(tmp.name, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=report_type.upper())

    return send_file(
        tmp.name,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=filename
    )

if __name__ == "__main__":
    # Standard Flask dev server for local Windows testing
    app.run(debug=True, port=5000)
