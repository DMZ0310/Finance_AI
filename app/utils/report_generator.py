"""
PDF report generator for financial summaries.
Uses reportlab to produce a clean, downloadable report.
"""

import io
import logging
from datetime import datetime

import pandas as pd

logger = logging.getLogger(__name__)


def generate_pdf_report(df: pd.DataFrame, kpis: dict, ai_insights: str = "") -> bytes:
    """
    Generate a PDF financial summary report.

    Returns bytes of the PDF file.
    Falls back to a plain-text bytes report if reportlab is unavailable.
    """
    try:
        return _generate_with_reportlab(df, kpis, ai_insights)
    except ImportError:
        logger.warning("reportlab not installed; generating text report instead.")
        return _generate_text_report(df, kpis, ai_insights)


def _generate_with_reportlab(df: pd.DataFrame, kpis: dict, ai_insights: str) -> bytes:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    )

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()
    # Custom styles
    title_style = ParagraphStyle(
        "FinTitle",
        parent=styles["Heading1"],
        fontSize=22,
        textColor=colors.HexColor("#1a1a2e"),
        spaceAfter=4,
    )
    h2_style = ParagraphStyle(
        "FinH2",
        parent=styles["Heading2"],
        fontSize=14,
        textColor=colors.HexColor("#0f3460"),
        spaceBefore=16,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "FinBody",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
    )

    story = []

    # ── Header ─────────────────────────────────────────────────────────────────
    story.append(Paragraph("FinanceAI — Financial Summary Report", title_style))
    story.append(Paragraph(
        f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
        body_style,
    ))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#0f3460")))
    story.append(Spacer(1, 12))

    # ── KPI Summary ────────────────────────────────────────────────────────────
    story.append(Paragraph("Financial Overview", h2_style))
    kpi_data = [
        ["Metric", "Value"],
        ["Total Income",          f"${kpis.get('total_income', 0):,.2f}"],
        ["Total Expenses",        f"${kpis.get('total_expenses', 0):,.2f}"],
        ["Net Savings",           f"${kpis.get('net_savings', 0):,.2f}"],
        ["Savings Rate",          f"{kpis.get('savings_rate', 0):.1f}%"],
        ["# Transactions",        str(kpis.get('num_transactions', 0))],
        ["Avg Transaction",       f"${kpis.get('avg_transaction', 0):,.2f}"],
        ["Largest Expense",       f"${kpis.get('largest_expense', 0):,.2f}"],
        ["Top Category",          kpis.get('top_category', 'N/A')],
    ]
    kpi_table = Table(kpi_data, colWidths=[3 * inch, 2.5 * inch])
    kpi_table.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0),  colors.HexColor("#0f3460")),
        ("TEXTCOLOR",    (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",     (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8f9fa"), colors.white]),
        ("GRID",         (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")),
        ("LEFTPADDING",  (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING",   (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 12))

    # ── Category Breakdown ────────────────────────────────────────────────────
    story.append(Paragraph("Spending by Category", h2_style))
    cat_totals = kpis.get("category_totals", {})
    total_exp  = kpis.get("total_expenses", 1)
    cat_data   = [["Category", "Amount", "% of Total"]]
    for cat, amt in sorted(cat_totals.items(), key=lambda x: -x[1]):
        cat_data.append([cat, f"${amt:,.2f}", f"{amt / total_exp * 100:.1f}%"])
    cat_table = Table(cat_data, colWidths=[3 * inch, 1.5 * inch, 1.5 * inch])
    cat_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  colors.HexColor("#16213e")),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.HexColor("#f8f9fa"), colors.white]),
        ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(cat_table)
    story.append(Spacer(1, 12))

    # ── Monthly Trends ─────────────────────────────────────────────────────────
    story.append(Paragraph("Monthly Spending Trends", h2_style))
    monthly = kpis.get("monthly_totals", {})
    mo_data = [["Month", "Total Spent"]]
    for month, amt in sorted(monthly.items()):
        mo_data.append([month, f"${amt:,.2f}"])
    if len(mo_data) > 1:
        mo_table = Table(mo_data, colWidths=[3 * inch, 2 * inch])
        mo_table.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0),  colors.HexColor("#0f3460")),
            ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
            ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, -1), 10),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.HexColor("#f8f9fa"), colors.white]),
            ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")),
            ("LEFTPADDING",   (0, 0), (-1, -1), 8),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(mo_table)

    story.append(Spacer(1, 16))

    # ── AI Insights ────────────────────────────────────────────────────────────
    if ai_insights:
        story.append(Paragraph("AI-Generated Financial Insights", h2_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#dee2e6")))
        story.append(Spacer(1, 6))
        # Clean text for PDF
        clean_insights = ai_insights.replace("**", "").replace("##", "").replace("#", "")
        for line in clean_insights.split("\n"):
            if line.strip():
                story.append(Paragraph(line.strip(), body_style))
                story.append(Spacer(1, 4))

    # ── Transaction Log (first 30) ────────────────────────────────────────────
    story.append(Paragraph("Recent Transactions (up to 30)", h2_style))
    expenses = df[df["is_expense"]].head(30)
    tx_data  = [["Date", "Description", "Category", "Amount"]]
    for _, row in expenses.iterrows():
        tx_data.append([
            row["date"].strftime("%b %d, %Y"),
            row["description"][:35],
            row["category"],
            f"${abs(row['amount']):,.2f}",
        ])
    tx_table = Table(tx_data, colWidths=[1.2*inch, 2.8*inch, 1.5*inch, 1*inch])
    tx_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  colors.HexColor("#1a1a2e")),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.HexColor("#f8f9fa"), colors.white]),
        ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(tx_table)

    # Footer
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#dee2e6")))
    story.append(Paragraph(
        "Generated by FinanceAI Assistant • Confidential",
        ParagraphStyle("footer", parent=styles["Normal"], fontSize=8,
                       textColor=colors.grey, alignment=1),
    ))

    doc.build(story)
    return buf.getvalue()


def _generate_text_report(df: pd.DataFrame, kpis: dict, ai_insights: str) -> bytes:
    """Fallback plain-text report."""
    lines = [
        "=" * 60,
        "FinanceAI — Financial Summary Report",
        f"Generated: {datetime.now().strftime('%B %d, %Y')}",
        "=" * 60,
        "",
        "FINANCIAL OVERVIEW",
        "-" * 40,
        f"Total Income:    ${kpis.get('total_income', 0):,.2f}",
        f"Total Expenses:  ${kpis.get('total_expenses', 0):,.2f}",
        f"Net Savings:     ${kpis.get('net_savings', 0):,.2f}",
        f"Savings Rate:    {kpis.get('savings_rate', 0):.1f}%",
        "",
        "SPENDING BY CATEGORY",
        "-" * 40,
    ]
    for cat, amt in sorted(kpis.get("category_totals", {}).items(), key=lambda x: -x[1]):
        lines.append(f"  {cat:<25} ${amt:,.2f}")

    lines += ["", "AI INSIGHTS", "-" * 40, ai_insights or "Not generated.", ""]
    return "\n".join(lines).encode("utf-8")
