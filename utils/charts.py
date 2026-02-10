import plotly.graph_objects as go

def line_with_anomalies(df, x, y, anom_col=None, baseline_col=None, title=None):
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df[x], y=df[y],
        mode="lines",
        name=y,
        line=dict(width=2)
    ))

    if baseline_col and baseline_col in df.columns:
        fig.add_trace(go.Scatter(
            x=df[x], y=df[baseline_col],
            mode="lines",
            name="Baseline",
            line=dict(width=2, dash="dash")
        ))

    if anom_col and anom_col in df.columns:
        anom = df[df[anom_col].astype(str).isin(["1", "True", "true", "TRUE"])] if df[anom_col].dtype != int else df[df[anom_col] == 1]
        if len(anom) > 0:
            fig.add_trace(go.Scatter(
                x=anom[x], y=anom[y],
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
