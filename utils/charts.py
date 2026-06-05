import plotly.graph_objects as go

def line_with_anomalies(df, x, y, anom_col=None, baseline_col=None, title=None):
    fig = go.Figure()

    # Convert pandas Series to plain Python lists so that
    # pio.to_json produces JSON arrays (not binary bdata dicts)
    # which Plotly.js can reliably decode on the frontend.
    x_list = df[x].astype(str).tolist()
    y_list = df[y].tolist()

    fig.add_trace(go.Scatter(
        x=x_list, y=y_list,
        mode="lines",
        name=y,
        line=dict(width=2)
    ))

    if baseline_col and baseline_col in df.columns:
        fig.add_trace(go.Scatter(
            x=x_list, y=df[baseline_col].tolist(),
            mode="lines",
            name="Baseline",
            line=dict(width=2, dash="dash")
        ))

    if anom_col and anom_col in df.columns:
        anom = df[df[anom_col].astype(str).isin(["1", "True", "true", "TRUE"])] if df[anom_col].dtype != int else df[df[anom_col] == 1]
        if len(anom) > 0:
            fig.add_trace(go.Scatter(
                x=anom[x].astype(str).tolist(), y=anom[y].tolist(),
                mode="markers",
                name="Anomaly",
                marker=dict(color="red", size=10),
                hovertemplate="<b>Anomaly</b><br>%{x}<br>Value=%{y}<extra></extra>"
            ))

    fig.update_layout(
        template="plotly_white",
        height=450,
        title=title,
        margin=dict(l=10, r=10, t=50, b=10),
        legend=dict(orientation="h", y=1.02, x=1, xanchor="right")
    )
    return fig

