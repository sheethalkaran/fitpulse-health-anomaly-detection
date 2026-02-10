from utils.ui import load_premium_css
load_premium_css()

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

st.title("📊 Model Insights")

#PIPELINE CHECK
if st.session_state.get("module2_out") is None:
    st.warning("Run pipeline from Home page first.")
    st.stop()

out = st.session_state.module2_out
df_all = st.session_state.get("df_final", None)

#USER FILTER
st.markdown("### 👤 Select User")

selected_user = st.session_state.get("selected_user", "All Users")

if df_all is not None and "Person_ID" in df_all.columns:
    user_list = sorted(df_all["Person_ID"].dropna().unique().tolist())
    user_list = ["All Users"] + user_list

    selected_user = st.selectbox(
        "Filter data by Person_ID",
        user_list,
        index=user_list.index(selected_user) if selected_user in user_list else 0
    )
    st.session_state.selected_user = selected_user
else:
    st.info("Person_ID filter not available (column not found).")

st.caption(f"✅ Currently selected: **{selected_user}**")
st.divider()

#KPI METRICS
features_count = out["features_df"].shape[1] if out.get("features_df") is not None else 0

clusters_count = 0
noise_points = 0
if out.get("clustering_df") is not None and len(out["clustering_df"]) > 0:
    clusters = out["clustering_df"]["cluster"]
    clusters_count = len(set(clusters)) - (1 if -1 in set(clusters) else 0)
    noise_points = int((clusters == -1).sum())

forecast_metrics = len(out["prophet_forecasts"]) if out.get("prophet_forecasts") else 0

c1, c2, c3 = st.columns(3)
c1.metric("🧠 TSFresh Features", features_count)
c2.metric("🧩 Clusters (DBSCAN)", clusters_count)
c3.metric("📈 Prophet Metrics", forecast_metrics)

st.divider()

#TABS
tab1, tab2, tab3 = st.tabs([
    "🧠 TSFresh (Top Features)",
    "📈 Prophet (Forecast Plot)",
    "🧩 Clustering (Scatter Plot)"
])

# TAB 1: TSFresh — RELEVANT FEATURES ONLY
with tab1:
    st.markdown("### 🧠 Selected TSFresh Features")

    features_df = out["features_df"].copy()

    required_patterns = [
        "__c3__lag_1",
        "__c3__lag_2",
        "__c3__lag_3",
        "__time_reversal_asymmetry_statistic__lag_2",
        "__time_reversal_asymmetry_statistic__lag_3"
    ]

    selected_features = [
        col for col in features_df.columns
        if any(pat in col for pat in required_patterns)
    ]

    if len(selected_features) == 0:
        st.error("Required TSFresh features not found. Check dataset.")
    else:
        var_series = features_df[selected_features].var().sort_values(ascending=False)
        chart_df = var_series.reset_index()
        chart_df.columns = ["feature", "variance"]

        fig = px.bar(
            chart_df,
            x="variance",
            y="feature",
            orientation="h",
            title="TSFresh Features (By Variance)"
        )

        fig.update_layout(template="plotly_white", height=420)
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("Show Selected Feature Values "):
            st.dataframe(
                features_df[selected_features].head(25),
                use_container_width=True
            )

# TAB 2: Prophet Forecast
with tab2:
    st.markdown("### 📈 Prophet Forecast Visualization")

    if not (isinstance(out, dict) and "prophet_forecasts" in out):
        st.warning("Prophet forecasts not found in module2_out.")
    else:
        pf = out["prophet_forecasts"]
        keys = list(pf.keys())

        if len(keys) == 0:
            st.info("No Prophet forecasts available (dataset too small / skipped).")
        else:
            metric = st.selectbox("Select Forecast Metric", keys)

            forecast_df = pf[metric].copy()

            #Visualization: yhat + bounds
            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=forecast_df["ds"],
                y=forecast_df["yhat"],
                mode="lines",
                name="Prediction (yhat)"
            ))

            fig.add_trace(go.Scatter(
                x=forecast_df["ds"],
                y=forecast_df["yhat_upper"],
                mode="lines",
                name="Upper Bound",
                line=dict(dash="dot"),
                opacity=0.6
            ))

            fig.add_trace(go.Scatter(
                x=forecast_df["ds"],
                y=forecast_df["yhat_lower"],
                mode="lines",
                name="Lower Bound",
                line=dict(dash="dot"),
                opacity=0.6
            ))

            fig.update_layout(
                template="plotly_white",
                height=520,
                title=f"Prophet Forecast for {metric}",
                margin=dict(l=10, r=10, t=50, b=10),
                legend=dict(orientation="h", y=1.02, x=1, xanchor="right")
            )

            st.plotly_chart(fig, use_container_width=True)

            with st.expander("Show Forecast Table"):
                st.dataframe(
                    forecast_df[["ds", "yhat", "yhat_lower", "yhat_upper"]].head(80),
                    use_container_width=True
                )

# TAB 3: DBSCAN Clustering
with tab3:
    st.markdown("### 🧩 DBSCAN Clustering Visualization")

    if not (isinstance(out, dict) and "clustering_df" in out):
        st.warning("Clustering output not found in module2_out.")
    else:
        clus = out["clustering_df"]

        if clus is None or len(clus) == 0:
            st.info("Clustering output empty (insufficient data/features).")
        else:
            fig = px.scatter(
                clus,
                x="pca1",
                y="pca2",
                color=clus["cluster"].astype(str),
                title="PCA Projection + DBSCAN Cluster Labels",
                labels={"color": "Cluster"}
            )
            fig.update_layout(template="plotly_white", height=520)
            st.plotly_chart(fig, use_container_width=True)

            st.caption(f"Noise points (cluster = -1): {noise_points}")

            with st.expander("Show Clustering Table"):
                st.dataframe(clus.head(50), use_container_width=True)
