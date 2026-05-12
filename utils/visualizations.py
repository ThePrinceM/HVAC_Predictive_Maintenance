"""
HVAC Fault Detection — Visualization Helpers
==============================================
Plotly charts with dark industrial HVAC theme matching dashboard.jpeg.
Fonts: Barlow (values) + DM Sans (labels).
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List

# ─── Theme Constants (TASKS.md Section 1.1) ─────────────────────────────────────

COLORS = {
    "bg_primary":    "#0b0f1a",
    "bg_card":       "#0f1623",
    "bg_surface":    "#131d2e",
    "border":        "#1c2e47",
    "text_primary":  "#dce8f5",
    "text_secondary":"#6b8299",
    "accent_blue":   "#3b9eff",
    "accent_green":  "#22d46b",
    "accent_orange": "#f5a623",
    "accent_red":    "#e84040",
    "accent_yellow": "#f5d020",
    "accent_purple": "#9b72f5",
    "accent_cyan":   "#00c8e0",
}

FAULT_COLORS = {
    "Normal":               COLORS["accent_green"],
    "Filter_Clog":          COLORS["accent_orange"],
    "Fan_Fault":            COLORS["accent_red"],
    "Refrigerant_Leak":     COLORS["accent_cyan"],
    "Electrical_Issue":     COLORS["accent_yellow"],
    "Compressor_Fault":     COLORS["accent_purple"],
    "Control_Sensor_Fault": COLORS["accent_blue"],
}

CHART_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans, sans-serif", color=COLORS["text_primary"], size=12),
    margin=dict(l=40, r=20, t=40, b=40),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=COLORS["border"], borderwidth=1, font=dict(size=11)),
)

def _apply_theme(fig: go.Figure) -> go.Figure:
    fig.update_layout(**CHART_LAYOUT)
    fig.update_xaxes(gridcolor=COLORS["border"], zerolinecolor=COLORS["border"], linecolor=COLORS["border"], tickfont=dict(color=COLORS["text_secondary"]))
    fig.update_yaxes(gridcolor=COLORS["border"], zerolinecolor=COLORS["border"], linecolor=COLORS["border"], tickfont=dict(color=COLORS["text_secondary"]))
    return fig


# ─── KPI Sparkline ──────────────────────────────────────────────────────────────

def plot_sparkline(values: list, color: str = "#3b9eff", height: int = 60) -> go.Figure:
    """Tiny area sparkline for KPI cards. No axes, no margins."""
    fig = go.Figure(go.Scatter(
        y=values, mode="lines", fill="tozeroy",
        line=dict(color=color, width=1.5),
        fillcolor=color.replace(")", ",0.15)").replace("rgb", "rgba") if "rgb" in color else f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.15)",
    ))
    fig.update_layout(
        height=height, margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return fig


# ─── Risk Gauge ─────────────────────────────────────────────────────────────────

def plot_risk_gauge(risk_pct: int, risk_label: str, risk_color: str) -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=risk_pct,
        number={"suffix": "%", "font": {"size": 52, "color": risk_color, "family": "Barlow"}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "#6b8299", "tickfont": {"color": "#6b8299"}},
            "bar": {"color": risk_color, "thickness": 0.25},
            "bgcolor": "rgba(0,0,0,0)",
            "bordercolor": "#1c2e47",
            "steps": [
                {"range": [0, 40],  "color": "rgba(34,212,107,0.15)"},
                {"range": [40, 70], "color": "rgba(245,166,35,0.15)"},
                {"range": [70, 100],"color": "rgba(232,64,64,0.15)"},
            ],
            "threshold": {
                "line": {"color": risk_color, "width": 3},
                "thickness": 0.85,
                "value": risk_pct
            }
        },
        domain={"x": [0, 1], "y": [0, 1]}
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=260,
        margin=dict(l=20, r=20, t=30, b=10),
        uirevision="risk_gauge",
        font=dict(family="Barlow", color="#dce8f5")
    )
    fig.add_annotation(
        text=f'<b>{risk_label}</b>',
        x=0.5, y=0.1, xref="paper", yref="paper",
        showarrow=False,
        font=dict(size=16, color=risk_color, family="Barlow"),
        bgcolor=f"rgba({','.join(str(int(risk_color.lstrip('#')[i:i+2],16)) for i in (0,2,4))},0.15)",
        bordercolor=risk_color,
        borderwidth=1,
        borderpad=6
    )
    return fig


# ─── Live Parameter Trends ─────────────────────────────────────────────────────

def plot_live_trends(buffer_df: pd.DataFrame) -> go.Figure:
    """Multi-line chart from simulator buffer."""
    if buffer_df.empty:
        fig = go.Figure()
        fig.update_layout(height=280)
        return _apply_theme(fig)

    lines = [
        ("supply_temp_C", "Supply Air Temp (\u00b0C)", COLORS["accent_cyan"]),
        ("return_temp_C", "Return Air Temp (\u00b0C)", COLORS["accent_green"]),
        ("compressor_current_A", "Compressor Current (A)", COLORS["accent_red"]),
        ("airflow_rate", "Airflow (m\u00b3/s)", COLORS["accent_orange"]),
    ]
    x_labels = buffer_df["timestamp_str"].tolist() if "timestamp_str" in buffer_df.columns else list(range(len(buffer_df)))

    fig = go.Figure()
    for col, label, color in lines:
        if col in buffer_df.columns:
            fig.add_trace(go.Scatter(x=x_labels, y=buffer_df[col], mode="lines", name=label, line=dict(color=color, width=1.5)))

    fig.update_layout(
        title=dict(text="PARAMETER TRENDS (Last 24 Hours)", font=dict(size=14, family="Barlow")),
        height=280, hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=10)),
    )
    return _apply_theme(fig)


# ─── Full Sensor Trends (3 subplots) ───────────────────────────────────────────

def plot_full_sensor_trends(buffer_df: pd.DataFrame) -> go.Figure:
    """3-row subplot for Live Monitor: temps, pressures, electrical."""
    if buffer_df.empty:
        fig = go.Figure()
        fig.update_layout(height=600)
        return _apply_theme(fig)

    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                        subplot_titles=["Temperatures (\u00b0C)", "Pressures (PSI)", "Electrical & Mechanical"])
    x = buffer_df["timestamp_str"].tolist() if "timestamp_str" in buffer_df.columns else list(range(len(buffer_df)))

    temps = [("supply_temp_C", COLORS["accent_cyan"]), ("return_temp_C", COLORS["accent_green"]), ("outdoor_temp_C", COLORS["accent_yellow"])]
    pressures = [("suction_pressure_psi", COLORS["accent_blue"]), ("discharge_pressure_psi", COLORS["accent_orange"]), ("refrigerant_pressure_psi", COLORS["accent_purple"])]
    elec = [("compressor_current_A", COLORS["accent_red"]), ("fan_speed_RPM", COLORS["accent_cyan"]), ("vibration_mm_s", COLORS["accent_yellow"]), ("airflow_rate", COLORS["accent_green"])]

    for col, color in temps:
        if col in buffer_df.columns:
            fig.add_trace(go.Scatter(x=x, y=buffer_df[col], mode="lines", name=col, line=dict(color=color, width=1.2)), row=1, col=1)
    for col, color in pressures:
        if col in buffer_df.columns:
            fig.add_trace(go.Scatter(x=x, y=buffer_df[col], mode="lines", name=col, line=dict(color=color, width=1.2)), row=2, col=1)
    for col, color in elec:
        if col in buffer_df.columns:
            fig.add_trace(go.Scatter(x=x, y=buffer_df[col], mode="lines", name=col, line=dict(color=color, width=1.2)), row=3, col=1)

    fig.update_layout(height=650, showlegend=True, legend=dict(orientation="h", font=dict(size=9)))
    return _apply_theme(fig)


# ─── Correlation Heatmap ───────────────────────────────────────────────────────

FEATURE_COLUMNS = [
    "return_temp_C", "supply_temp_C", "outdoor_temp_C", "suction_pressure_psi",
    "discharge_pressure_psi", "compressor_current_A", "fan_speed_RPM",
    "vibration_mm_s", "unit_age", "refrigerant_pressure_psi", "filter_health",
    "airflow_rate", "damper_position_%",
]

def plot_correlation_heatmap(df: pd.DataFrame) -> go.Figure:
    """Correlation matrix of sensor features."""
    cols = [c for c in FEATURE_COLUMNS if c in df.columns]
    corr = df[cols].corr()
    fig = go.Figure(go.Heatmap(
        z=corr.values, x=cols, y=cols,
        colorscale=[[0, COLORS["accent_blue"]], [0.5, COLORS["bg_card"]], [1, COLORS["accent_red"]]],
        text=np.round(corr.values, 2), texttemplate="%{text}", textfont=dict(size=9),
        zmin=-1, zmax=1,
    ))
    fig.update_layout(title=dict(text="Feature Correlation Matrix", font=dict(size=14, family="Barlow")), height=500, xaxis=dict(tickangle=-45))
    return _apply_theme(fig)


# ─── Confusion Matrix ──────────────────────────────────────────────────────────

def plot_confusion_matrix(cm: list, labels: List[str]) -> go.Figure:
    cm_arr = np.array(cm)
    cm_norm = cm_arr.astype(float) / cm_arr.sum(axis=1, keepdims=True)
    text_vals = [[str(v) for v in row] for row in cm_arr]
    fig = go.Figure(go.Heatmap(
        z=cm_norm, x=labels, y=labels, text=text_vals, texttemplate="%{text}",
        textfont=dict(size=12, color="white"),
        colorscale=[[0, COLORS["bg_card"]], [0.3, "#0d3b66"], [0.6, "#1a6b8a"], [0.8, "#00b4d8"], [1, COLORS["accent_cyan"]]],
        showscale=True, colorbar=dict(title="Norm", tickfont=dict(color=COLORS["text_secondary"])),
    ))
    fig.update_layout(title=dict(text="Confusion Matrix", font=dict(size=16)), xaxis_title="Predicted", yaxis_title="Actual", height=500, xaxis=dict(tickangle=-45))
    return _apply_theme(fig)


# ─── Accuracy Comparison ───────────────────────────────────────────────────────

def plot_accuracy_comparison(train_acc: float, val_acc: float, test_acc: float) -> go.Figure:
    cats = ["Train", "Validation", "Test"]
    vals = [train_acc * 100, val_acc * 100, test_acc * 100]
    colors = [COLORS["accent_green"], COLORS["accent_cyan"], COLORS["accent_orange"]]
    fig = go.Figure(go.Bar(x=cats, y=vals, marker=dict(color=colors), text=[f"{v:.2f}%" for v in vals], textposition="outside", textfont=dict(color="white", size=14, family="Barlow")))
    fig.update_layout(title=dict(text="Accuracy Comparison", font=dict(size=16)), yaxis_title="Accuracy (%)", yaxis=dict(range=[0, 105]), height=350)
    return _apply_theme(fig)


# ─── Feature Importance ────────────────────────────────────────────────────────

def plot_feature_importance(importances: Dict[str, float], top_n: int = 13) -> go.Figure:
    sorted_feats = sorted(importances.items(), key=lambda x: x[1], reverse=True)[:top_n]
    names = [f[0] for f in sorted_feats][::-1]
    values = [f[1] for f in sorted_feats][::-1]
    n = len(names)
    colors = [f"rgba({int(59+i*30/n)}, {int(158+i*20/n)}, {int(255-i*50/n)}, 0.85)" for i in range(n)]
    fig = go.Figure(go.Bar(x=values, y=names, orientation="h", marker=dict(color=colors), text=[f"{v:.4f}" for v in values], textposition="auto", textfont=dict(color="white", size=11)))
    fig.update_layout(title=dict(text=f"Top {top_n} Feature Importances", font=dict(size=16, family="Barlow")), xaxis_title="Importance", height=max(350, top_n * 32))
    return _apply_theme(fig)


# ─── SHAP Summary ──────────────────────────────────────────────────────────────

def plot_shap_summary(shap_values, feature_names: List[str]) -> go.Figure:
    if hasattr(shap_values, "values"):
        vals = shap_values.values
    else:
        vals = np.array(shap_values)
    if vals.ndim == 3:
        mean_abs = np.mean(np.abs(vals), axis=(0, 2))
    else:
        mean_abs = np.mean(np.abs(vals), axis=0)
    sorted_idx = np.argsort(mean_abs)
    sorted_names = [feature_names[i] for i in sorted_idx]
    sorted_vals = mean_abs[sorted_idx]
    n = len(sorted_names)
    colors = [f"rgba({int(255-i*200/n)}, {int(50+i*100/n)}, {int(100+i*100/n)}, 0.9)" for i in range(n)]
    fig = go.Figure(go.Bar(x=sorted_vals, y=sorted_names, orientation="h", marker=dict(color=colors), text=[f"{v:.4f}" for v in sorted_vals], textposition="auto", textfont=dict(color="white", size=11)))
    fig.update_layout(title=dict(text="SHAP Feature Impact (Mean |SHAP|)", font=dict(size=16, family="Barlow")), xaxis_title="Mean |SHAP value|", height=max(400, n * 30))
    return _apply_theme(fig)


# ─── Probability Chart ─────────────────────────────────────────────────────────

def plot_probability_chart(probabilities: Dict[str, float]) -> go.Figure:
    sorted_probs = sorted(probabilities.items(), key=lambda x: x[1], reverse=True)
    classes = [p[0] for p in sorted_probs]
    probs = [p[1] for p in sorted_probs]
    colors = [FAULT_COLORS.get(c, COLORS["accent_cyan"]) for c in classes]
    fig = go.Figure(go.Bar(x=classes, y=[p*100 for p in probs], marker=dict(color=colors), text=[f"{p*100:.1f}%" for p in probs], textposition="outside", textfont=dict(color="white", size=12)))
    fig.update_layout(title=dict(text="Prediction Confidence by Class", font=dict(size=16)), yaxis_title="Probability (%)", yaxis=dict(range=[0, 110]), height=400, xaxis=dict(tickangle=-30))
    return _apply_theme(fig)


# ─── Metrics History ────────────────────────────────────────────────────────────

def plot_metrics_history(history_df: pd.DataFrame) -> go.Figure:
    if history_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No training runs yet", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font=dict(size=18, color=COLORS["text_secondary"]))
        fig.update_layout(height=400)
        return _apply_theme(fig)
    fig = go.Figure()
    for col, name, color, dash in [("train_accuracy", "Train", COLORS["accent_green"], "solid"), ("val_accuracy", "Validation", COLORS["accent_cyan"], "dash"), ("test_accuracy", "Test", COLORS["accent_orange"], "dot")]:
        fig.add_trace(go.Scatter(x=list(range(1, len(history_df)+1)), y=history_df[col]*100, mode="lines+markers", name=name, line=dict(color=color, width=2.5, dash=dash), marker=dict(size=8, color=color)))
    fig.update_layout(title=dict(text="Accuracy Trend Across Training Runs", font=dict(size=16, family="Barlow")), xaxis_title="Training Run", yaxis_title="Accuracy (%)", yaxis=dict(range=[0, 105]), height=400, hovermode="x unified")
    return _apply_theme(fig)
