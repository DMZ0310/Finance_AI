"""
Plotly chart components for the FinanceAI dashboard.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from app.utils.config import CATEGORY_COLORS

# ─── Shared theme ─────────────────────────────────────────────────────────────

_FONT      = "DM Sans, sans-serif"
_BG        = "rgba(0,0,0,0)"
_PAPER_BG  = "rgba(0,0,0,0)"
_GRID_CLR  = "rgba(255,255,255,0.08)"
_TEXT_CLR  = "#e2e8f0"
_ACCENT    = "#6366f1"


def _base_layout(**kwargs) -> dict:
    return dict(
        paper_bgcolor=_PAPER_BG,
        plot_bgcolor=_BG,
        font=dict(family=_FONT, color=_TEXT_CLR, size=12),
        margin=dict(l=20, r=20, t=40, b=20),
        showlegend=True,
        legend=dict(
            bgcolor="rgba(255,255,255,0.05)",
            bordercolor="rgba(255,255,255,0.1)",
            borderwidth=1,
            font=dict(size=11),
        ),
        **kwargs,
    )


# ─── Pie Chart ────────────────────────────────────────────────────────────────

def pie_chart(kpis: dict) -> go.Figure:
    """Donut chart of expense categories."""
    cat_totals = kpis.get("category_totals", {})
    if not cat_totals:
        return _empty_fig("No expense data")

    labels = list(cat_totals.keys())
    values = list(cat_totals.values())
    colours = [CATEGORY_COLORS.get(l, "#95a5a6") for l in labels]

    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.55,
        marker=dict(colors=colours, line=dict(color="rgba(0,0,0,0.3)", width=2)),
        textinfo="label+percent",
        textfont=dict(size=11),
        hovertemplate="<b>%{label}</b><br>$%{value:,.2f}<br>%{percent}<extra></extra>",
    ))
    fig.update_layout(
        **_base_layout(title=dict(text="Spending by Category", font=dict(size=15))),
        annotations=[dict(
            text=f"${sum(values):,.0f}<br><span style='font-size:11px'>Total</span>",
            x=0.5, y=0.5, font=dict(size=16, color=_TEXT_CLR),
            showarrow=False,
        )],
    )
    return fig


# ─── Monthly Line Chart ───────────────────────────────────────────────────────

def monthly_trend_chart(kpis: dict) -> go.Figure:
    """Line + area chart of monthly spending."""
    monthly = kpis.get("monthly_totals", {})
    if not monthly:
        return _empty_fig("No monthly data")

    months = sorted(monthly.keys())
    values = [monthly[m] for m in months]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=months, y=values,
        mode="lines+markers",
        name="Monthly Spend",
        line=dict(color=_ACCENT, width=3, shape="spline"),
        marker=dict(size=8, color=_ACCENT,
                    line=dict(color="white", width=2)),
        fill="tozeroy",
        fillcolor="rgba(99,102,241,0.15)",
        hovertemplate="<b>%{x}</b><br>$%{y:,.2f}<extra></extra>",
    ))

    # Average line
    avg = sum(values) / len(values)
    fig.add_hline(
        y=avg, line_dash="dash", line_color="rgba(255,165,0,0.6)",
        annotation_text=f"Avg ${avg:,.0f}",
        annotation_position="top right",
        annotation_font=dict(color="orange", size=11),
    )

    fig.update_layout(
        **_base_layout(title=dict(text="Monthly Spending Trend", font=dict(size=15))),
        xaxis=dict(showgrid=False, tickangle=-30),
        yaxis=dict(gridcolor=_GRID_CLR, tickprefix="$", tickformat=",.0f"),
    )
    return fig


# ─── Category Bar Chart ───────────────────────────────────────────────────────

def category_bar_chart(kpis: dict) -> go.Figure:
    """Horizontal bar chart sorted by spend amount."""
    cat_totals = kpis.get("category_totals", {})
    if not cat_totals:
        return _empty_fig("No category data")

    df = pd.DataFrame(
        sorted(cat_totals.items(), key=lambda x: x[1]),
        columns=["Category", "Amount"],
    )
    colours = [CATEGORY_COLORS.get(c, "#95a5a6") for c in df["Category"]]

    fig = go.Figure(go.Bar(
        x=df["Amount"], y=df["Category"],
        orientation="h",
        marker=dict(color=colours, line=dict(color="rgba(0,0,0,0.2)", width=1)),
        hovertemplate="<b>%{y}</b><br>$%{x:,.2f}<extra></extra>",
    ))
    fig.update_layout(
        **_base_layout(title=dict(text="Category Comparison", font=dict(size=15))),
        xaxis=dict(gridcolor=_GRID_CLR, tickprefix="$", tickformat=",.0f"),
        yaxis=dict(showgrid=False),
        bargap=0.3,
    )
    return fig


# ─── Weekly Heatmap ───────────────────────────────────────────────────────────

def weekly_heatmap(df: pd.DataFrame) -> go.Figure:
    """Spending heatmap by day-of-week and month."""
    expenses = df[df["is_expense"]].copy()
    if expenses.empty:
        return _empty_fig("No data")

    expenses["dow"]   = expenses["date"].dt.day_name()
    pivot = expenses.groupby(["month", "dow"])["amount"].sum().abs().unstack(fill_value=0)

    days_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    pivot = pivot.reindex(columns=[d for d in days_order if d in pivot.columns])

    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale="Purples",
        hovertemplate="<b>%{y} %{x}</b><br>$%{z:,.2f}<extra></extra>",
        showscale=True,
        colorbar=dict(
            tickprefix="$",
            tickformat=",.0f",
            bgcolor="rgba(0,0,0,0)",
            bordercolor="rgba(255,255,255,0.1)",
        ),
    ))
    fig.update_layout(
        **_base_layout(title=dict(text="Spending Heatmap (Month × Day)", font=dict(size=15))),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=False),
    )
    return fig


# ─── Cumulative Spending ──────────────────────────────────────────────────────

def cumulative_spending_chart(df: pd.DataFrame) -> go.Figure:
    """Cumulative expenses over time, coloured by month."""
    expenses = df[df["is_expense"]].copy().sort_values("date")
    if expenses.empty:
        return _empty_fig("No data")

    expenses["cumulative"] = expenses["amount"].abs().cumsum()
    months = expenses["month"].unique()
    palette = px.colors.qualitative.Vivid

    fig = go.Figure()
    for i, month in enumerate(months):
        mask = expenses["month"] == month
        subset = expenses[mask]
        fig.add_trace(go.Scatter(
            x=subset["date"], y=subset["cumulative"],
            mode="lines",
            name=str(month),
            line=dict(color=palette[i % len(palette)], width=2),
            hovertemplate="<b>%{x|%b %d}</b><br>Cumulative: $%{y:,.2f}<extra></extra>",
        ))

    fig.update_layout(
        **_base_layout(title=dict(text="Cumulative Spending Over Time", font=dict(size=15))),
        xaxis=dict(showgrid=False),
        yaxis=dict(gridcolor=_GRID_CLR, tickprefix="$", tickformat=",.0f"),
    )
    return fig


# ─── Income vs Expense ───────────────────────────────────────────────────────

def income_vs_expense_chart(df: pd.DataFrame) -> go.Figure:
    """Grouped bar showing income vs expenses by month."""
    monthly_income  = df[~df["is_expense"]].groupby("month")["amount"].sum()
    monthly_expense = df[df["is_expense"]].groupby("month")["amount"].sum().abs()
    months = sorted(set(monthly_income.index) | set(monthly_expense.index))

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=months, y=[monthly_income.get(m, 0) for m in months],
        name="Income", marker_color="#22c55e",
        hovertemplate="<b>%{x}</b><br>Income: $%{y:,.2f}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        x=months, y=[monthly_expense.get(m, 0) for m in months],
        name="Expenses", marker_color="#f43f5e",
        hovertemplate="<b>%{x}</b><br>Expenses: $%{y:,.2f}<extra></extra>",
    ))
    fig.update_layout(
        **_base_layout(title=dict(text="Income vs Expenses by Month", font=dict(size=15))),
        barmode="group",
        xaxis=dict(showgrid=False),
        yaxis=dict(gridcolor=_GRID_CLR, tickprefix="$", tickformat=",.0f"),
        bargap=0.2,
        bargroupgap=0.05,
    )
    return fig


# ─── Anomaly Scatter ─────────────────────────────────────────────────────────

def anomaly_scatter(df: pd.DataFrame, kpis: dict) -> go.Figure:
    """Scatter of all expenses, highlighting anomalies."""
    expenses  = df[df["is_expense"]].copy()
    anomalies = kpis.get("anomalies", pd.DataFrame())
    anom_idx  = set(anomalies.index) if not anomalies.empty else set()

    normal = expenses[~expenses.index.isin(anom_idx)]
    anom   = expenses[expenses.index.isin(anom_idx)]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=normal["date"], y=normal["amount"].abs(),
        mode="markers",
        name="Normal",
        marker=dict(color=_ACCENT, size=6, opacity=0.7),
        hovertemplate="<b>%{text}</b><br>$%{y:,.2f}<extra></extra>",
        text=normal["description"],
    ))
    if not anom.empty:
        fig.add_trace(go.Scatter(
            x=anom["date"], y=anom["amount"].abs(),
            mode="markers",
            name="⚠ Anomaly",
            marker=dict(color="#f59e0b", size=12, symbol="star",
                        line=dict(color="white", width=1)),
            hovertemplate="<b>%{text}</b><br>$%{y:,.2f}<extra></extra>",
            text=anom["description"],
        ))
    fig.update_layout(
        **_base_layout(title=dict(text="Transaction Anomaly Detection", font=dict(size=15))),
        xaxis=dict(showgrid=False),
        yaxis=dict(gridcolor=_GRID_CLR, tickprefix="$", tickformat=",.0f"),
    )
    return fig


# ─── Helper ──────────────────────────────────────────────────────────────────

def _empty_fig(message: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=message, x=0.5, y=0.5,
        xref="paper", yref="paper",
        showarrow=False,
        font=dict(size=14, color=_TEXT_CLR),
    )
    fig.update_layout(**_base_layout())
    return fig
