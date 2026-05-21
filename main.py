"""
FinanceAI Assistant — Main Streamlit Application
Run with: streamlit run main.py
"""

import io
import logging
import os
import sys

import pandas as pd
import streamlit as st

# Ensure project root is on the path
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# ── Config must be first (sets up logging) ────────────────────────────────────
from app.utils.config import (
    APP_TITLE, APP_VERSION, ENABLE_AUTH, APP_PASSWORD,
    GEMINI_API_KEY, SAMPLE_DIR,
)
from app.utils.parser import parse_file, compute_kpis, build_summary_text
from app.utils import rag_engine
from app.utils.report_generator import generate_pdf_report
from app.components.charts import (
    pie_chart, monthly_trend_chart, category_bar_chart,
    weekly_heatmap, cumulative_spending_chart,
    income_vs_expense_chart, anomaly_scatter,
)
from app.components.ui_helpers import (
    render_css, render_header, kpi_card,
    section_header, info_banner, chat_bubble, render_empty_state,
)

logger = logging.getLogger(__name__)

# ─── Page Config ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

render_css()

# ─── Session State Init ──────────────────────────────────────────────────────

def _init_state():
    defaults = {
        "authenticated" : not ENABLE_AUTH,
        "df"            : None,
        "kpis"          : None,
        "indexed"       : False,
        "chat_history"  : [],
        "ai_insights"   : "",
        "page"          : "Dashboard",
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

_init_state()

# ─── Auth Gate ───────────────────────────────────────────────────────────────

def auth_wall():
    st.markdown("""
    <div style="display:flex; justify-content:center; align-items:center;
                min-height:80vh; flex-direction:column; gap:24px;">
        <div style="font-size:3rem">🔐</div>
        <h2 style="color:#818cf8; margin:0">FinanceAI Access</h2>
    </div>
    """, unsafe_allow_html=True)
    col = st.columns([1, 2, 1])[1]
    with col:
        pwd = st.text_input("Enter password", type="password", placeholder="Password…")
        if st.button("Unlock", use_container_width=True):
            if pwd == APP_PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Incorrect password.")

if not st.session_state.authenticated:
    auth_wall()
    st.stop()

# ─── Sidebar ─────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div style="padding: 16px 0 8px; text-align:center;">
        <div style="font-size:2rem">⚡</div>
        <div style="font-weight:700; font-size:1.1rem; color:#818cf8;">FinanceAI</div>
        <div style="font-size:0.72rem; color:#64748b;">v""" + APP_VERSION + """</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    page = st.radio(
        "Navigation",
        ["📊 Dashboard", "💬 AI Chatbot", "🔍 Analytics", "📈 Trends", "⚠️ Anomalies", "📥 Reports"],
        label_visibility="collapsed",
    )
    st.session_state.page = page

    st.markdown("---")
    st.markdown("**📁 Upload Statement**")
    uploaded = st.file_uploader(
        "Upload CSV or PDF",
        type=["csv", "pdf"],
        label_visibility="collapsed",
        help="Supported: CSV and PDF bank statements",
    )

    # Sample data shortcut
    st.markdown("**🎯 Quick Demo**")
    if st.button("Load Sample Data", use_container_width=True):
        sample_path = SAMPLE_DIR / "sample_transactions.csv"
        if sample_path.exists():
            with open(sample_path, "rb") as f:

                class _MockFile:
                    name = "sample_transactions.csv"
                    def read(self): return f.read()

            uploaded = _MockFile()
            st.success("Sample data loaded!")
        else:
            st.error("Sample file not found.")

    # Process upload
    if uploaded is not None:
        with st.spinner("Parsing transactions…"):
            try:
                df = parse_file(uploaded)
                kpis = compute_kpis(df)
                st.session_state.df    = df
                st.session_state.kpis  = kpis
                st.session_state.indexed = False  # reset index on new upload
                st.success(f"✓ {len(df)} transactions loaded")
            except Exception as e:
                st.error(f"Parse error: {e}")

    # RAG index button
    if st.session_state.df is not None and not st.session_state.indexed:
        if st.button("🔗 Index for AI Chat", use_container_width=True):
            if not GEMINI_API_KEY:
                st.warning("Set GEMINI_API_KEY in .env to enable AI features.")
            else:
                with st.spinner("Indexing transactions…"):
                    try:
                        summary = build_summary_text(st.session_state.df)
                        n = rag_engine.index_transactions(st.session_state.df, summary)
                        st.session_state.indexed = True
                        st.success(f"✓ {n} documents indexed")
                    except Exception as e:
                        st.error(f"Indexing error: {e}")

    if st.session_state.indexed:
        st.markdown('<div style="color:#22c55e; font-size:0.82rem">✓ AI Index Ready</div>',
                    unsafe_allow_html=True)

    # API key input (if not in env)
    if not GEMINI_API_KEY:
        st.markdown("---")
        st.markdown("**🔑 Gemini API Key**")
        key_input = st.text_input("API Key", type="password", placeholder="AIza…",
                                  label_visibility="collapsed")
        if key_input:
            os.environ["GEMINI_API_KEY"] = key_input
            from app.utils import config
            config.GEMINI_API_KEY = key_input
            rag_engine.GEMINI_API_KEY = key_input
            st.success("Key set for this session")

    st.markdown("---")
    if st.session_state.df is not None:
        df_s = st.session_state.df
        st.markdown(f"""
        <div style="font-size:0.78rem; color:#64748b; line-height:1.8">
            <div>📅 {df_s['date'].min().strftime('%b %Y')} – {df_s['date'].max().strftime('%b %Y')}</div>
            <div>🔢 {len(df_s)} transactions</div>
            <div>💸 ${st.session_state.kpis.get('total_expenses',0):,.2f} total spent</div>
        </div>
        """, unsafe_allow_html=True)

# ─── Main Content ────────────────────────────────────────────────────────────

render_header()

df   = st.session_state.df
kpis = st.session_state.kpis

# ═══════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ═══════════════════════════════════════════════════════════════════
if "Dashboard" in page:
    if df is None:
        render_empty_state("Upload a CSV or PDF bank statement, or click 'Load Sample Data'")
        st.stop()

    # ── KPI Row ──────────────────────────────────────────────────────────────
    section_header("Financial Overview", "Key metrics from your statement")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("Total Expenses",  f"${kpis['total_expenses']:,.2f}",  icon="💸", color="#f43f5e")
    with c2:
        kpi_card("Total Income",    f"${kpis['total_income']:,.2f}",    icon="💰", color="#22c55e")
    with c3:
        savings = kpis["net_savings"]
        color   = "#22c55e" if savings >= 0 else "#f43f5e"
        kpi_card("Net Savings",     f"${savings:,.2f}",                 icon="🏦", color=color)
    with c4:
        rate = kpis["savings_rate"]
        kpi_card("Savings Rate",    f"{rate:.1f}%",                     icon="📊",
                 color="#22c55e" if rate >= 20 else "#f59e0b")

    c5, c6, c7, c8 = st.columns(4)
    with c5:
        kpi_card("Transactions",    str(kpis["num_transactions"]),      icon="🔢", color="#818cf8")
    with c6:
        kpi_card("Top Category",    kpis["top_category"],               icon="🏆", color="#f59e0b")
    with c7:
        kpi_card("Avg Transaction", f"${kpis['avg_transaction']:,.2f}", icon="📉", color="#06b6d4")
    with c8:
        kpi_card("Largest Expense", f"${kpis['largest_expense']:,.2f}", icon="⚠️", color="#f43f5e")

    st.markdown("---")

    # ── Charts Row ───────────────────────────────────────────────────────────
    section_header("Spending Overview")
    col_l, col_r = st.columns([1, 1])
    with col_l:
        st.plotly_chart(pie_chart(kpis), use_container_width=True)
    with col_r:
        st.plotly_chart(income_vs_expense_chart(df), use_container_width=True)

    # ── Monthly Trend ─────────────────────────────────────────────────────────
    st.plotly_chart(monthly_trend_chart(kpis), use_container_width=True)

    # ── Recent Transactions ───────────────────────────────────────────────────
    section_header("Recent Transactions", "Latest 20 expenses")
    recent = (
        df[df["is_expense"]]
        .sort_values("date", ascending=False)
        .head(20)[["date", "description", "category", "amount"]]
        .copy()
    )
    recent["amount"]     = recent["amount"].abs().map("${:,.2f}".format)
    recent["date"]       = recent["date"].dt.strftime("%b %d, %Y")
    recent.columns       = ["Date", "Description", "Category", "Amount"]
    st.dataframe(recent, use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════
# PAGE: AI CHATBOT
# ═══════════════════════════════════════════════════════════════════
elif "Chatbot" in page:
    section_header("AI Financial Assistant", "Ask anything about your finances")

    if df is None:
        info_banner("Upload a bank statement first to enable data-aware responses.", "warning")

    if not GEMINI_API_KEY and not os.environ.get("GEMINI_API_KEY"):
        info_banner(
            "Gemini API key not configured. Add GEMINI_API_KEY to your .env file "
            "or enter it in the sidebar to enable AI responses.",
            "warning",
        )

    # Suggested questions
    if df is not None:
        st.markdown("**💡 Suggested Questions**")
        q_cols = st.columns(3)
        suggestions = [
            "Where did I spend the most money?",
            "How can I reduce my expenses?",
            "Summarize my monthly spending.",
            "What are my top 3 spending categories?",
            "Show me unusual transactions.",
            "What is my savings rate?",
        ]
        for i, q in enumerate(suggestions):
            with q_cols[i % 3]:
                if st.button(q, key=f"sug_{i}", use_container_width=True):
                    st.session_state.chat_history.append({"role": "user", "content": q})
                    with st.spinner("Thinking…"):
                        try:
                            answer = rag_engine.answer_question(
                                q,
                                kpis=st.session_state.kpis,
                                chat_history=st.session_state.chat_history[:-1],
                            )
                        except Exception as e:
                            answer = f"⚠️ Error: {e}"
                    st.session_state.chat_history.append({"role": "assistant", "content": answer})
                    st.rerun()

    st.markdown("---")

    # Chat history
    chat_container = st.container()
    with chat_container:
        if not st.session_state.chat_history:
            st.markdown("""
            <div style="text-align:center; padding:40px; color:#64748b">
                <div style="font-size:2.5rem; margin-bottom:12px">🤖</div>
                <div>Ask me anything about your finances!</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            for msg in st.session_state.chat_history:
                chat_bubble(msg["content"], msg["role"])

    # Input
    col_inp, col_btn = st.columns([5, 1])
    with col_inp:
        user_input = st.text_input(
            "Your question",
            placeholder="e.g. How much did I spend on food last month?",
            label_visibility="collapsed",
            key="chat_input",
        )
    with col_btn:
        send = st.button("Send ▶", use_container_width=True)

    if send and user_input.strip():
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.spinner("Analysing your finances…"):
            try:
                answer = rag_engine.answer_question(
                    user_input,
                    kpis=st.session_state.kpis,
                    chat_history=st.session_state.chat_history[:-1],
                )
            except Exception as e:
                answer = f"⚠️ Error generating response: {e}\n\nMake sure your Gemini API key is valid."
        st.session_state.chat_history.append({"role": "assistant", "content": answer})
        st.rerun()

    if st.button("🗑 Clear Chat", type="secondary"):
        st.session_state.chat_history = []
        st.rerun()

# ═══════════════════════════════════════════════════════════════════
# PAGE: ANALYTICS
# ═══════════════════════════════════════════════════════════════════
elif "Analytics" in page:
    section_header("Spending Analytics", "Deep dive into your expense patterns")

    if df is None:
        render_empty_state()
        st.stop()

    col_l, col_r = st.columns(2)
    with col_l:
        st.plotly_chart(category_bar_chart(kpis), use_container_width=True)
    with col_r:
        st.plotly_chart(pie_chart(kpis), use_container_width=True)

    st.plotly_chart(weekly_heatmap(df), use_container_width=True)

    # Category drill-down
    section_header("Category Drill-Down", "Click a category to see transactions")
    selected_cat = st.selectbox(
        "Select category",
        options=sorted(df[df["is_expense"]]["category"].unique()),
        label_visibility="visible",
    )
    if selected_cat:
        cat_df = (
            df[(df["category"] == selected_cat) & df["is_expense"]]
            .sort_values("date", ascending=False)
            [["date", "description", "amount"]]
            .copy()
        )
        cat_df["amount"] = cat_df["amount"].abs().map("${:,.2f}".format)
        cat_df["date"]   = cat_df["date"].dt.strftime("%b %d, %Y")
        cat_df.columns   = ["Date", "Description", "Amount"]
        total = df[(df["category"] == selected_cat) & df["is_expense"]]["amount"].abs().sum()
        info_banner(f"Total spent on <strong>{selected_cat}</strong>: <strong>${total:,.2f}</strong>", "info")
        st.dataframe(cat_df, use_container_width=True, hide_index=True)

    # AI Budget Recommendations
    st.markdown("---")
    section_header("AI Budgeting Recommendations")
    if st.button("✨ Generate AI Budget Tips", use_container_width=False):
        if not GEMINI_API_KEY and not os.environ.get("GEMINI_API_KEY"):
            st.warning("Configure Gemini API key to use this feature.")
        else:
            with st.spinner("Generating personalised advice…"):
                try:
                    tips = rag_engine.generate_budget_recommendations(kpis)
                    st.session_state.ai_insights = tips
                except Exception as e:
                    st.error(f"Error: {e}")

    if st.session_state.ai_insights:
        st.markdown(f"""
        <div style="background:rgba(99,102,241,0.08); border:1px solid rgba(99,102,241,0.3);
                    border-radius:12px; padding:20px; margin:12px 0;">
            <div style="color:#e2e8f0; font-size:0.92rem; line-height:1.7; white-space:pre-wrap;">
{st.session_state.ai_insights}
            </div>
        </div>
        """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# PAGE: TRENDS
# ═══════════════════════════════════════════════════════════════════
elif "Trends" in page:
    section_header("Spending Trends", "Visualise how your spending evolves over time")

    if df is None:
        render_empty_state()
        st.stop()

    st.plotly_chart(monthly_trend_chart(kpis), use_container_width=True)
    st.plotly_chart(cumulative_spending_chart(df),  use_container_width=True)
    st.plotly_chart(income_vs_expense_chart(df),    use_container_width=True)

    # Month-over-month comparison
    monthly = kpis.get("monthly_totals", {})
    if len(monthly) >= 2:
        section_header("Month-over-Month Change")
        months = sorted(monthly.keys())
        changes = []
        for i in range(1, len(months)):
            prev, curr = months[i - 1], months[i]
            delta_pct = (monthly[curr] - monthly[prev]) / monthly[prev] * 100
            changes.append({
                "Month"       : curr,
                "Spent"       : f"${monthly[curr]:,.2f}",
                "vs Prior Month": f"{'↑' if delta_pct > 0 else '↓'} {abs(delta_pct):.1f}%",
            })
        st.dataframe(pd.DataFrame(changes), use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════
# PAGE: ANOMALIES
# ═══════════════════════════════════════════════════════════════════
elif "Anomalies" in page:
    section_header("Transaction Anomaly Detection", "Unusual spending flagged by AI")

    if df is None:
        render_empty_state()
        st.stop()

    st.plotly_chart(anomaly_scatter(df, kpis), use_container_width=True)

    anomalies = kpis.get("anomalies", pd.DataFrame())
    if anomalies.empty:
        info_banner("No statistical anomalies detected in your transactions. 🎉", "success")
    else:
        info_banner(
            f"<strong>{len(anomalies)}</strong> transactions flagged as statistically unusual "
            f"(>2σ above your average transaction of ${kpis.get('avg_transaction', 0):.2f}).",
            "warning",
        )
        anom_display = anomalies[["date", "description", "category", "amount"]].copy()
        anom_display["amount"] = anom_display["amount"].abs().map("${:,.2f}".format)
        anom_display["date"]   = anom_display["date"].dt.strftime("%b %d, %Y")
        anom_display.columns   = ["Date", "Description", "Category", "Amount"]
        st.dataframe(anom_display, use_container_width=True, hide_index=True)

    # AI anomaly analysis
    st.markdown("---")
    if st.button("🤖 AI Anomaly Analysis", use_container_width=False):
        if not GEMINI_API_KEY and not os.environ.get("GEMINI_API_KEY"):
            st.warning("Configure Gemini API key to use this feature.")
        else:
            with st.spinner("Analysing unusual transactions…"):
                try:
                    analysis = rag_engine.detect_anomalies_ai(df, kpis)
                    st.markdown(f"""
                    <div style="background:rgba(245,158,11,0.08); border:1px solid rgba(245,158,11,0.3);
                                border-radius:12px; padding:20px; margin:12px 0;">
                        <div style="color:#e2e8f0; font-size:0.92rem; line-height:1.7; white-space:pre-wrap;">
{analysis}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Error: {e}")

# ═══════════════════════════════════════════════════════════════════
# PAGE: REPORTS
# ═══════════════════════════════════════════════════════════════════
elif "Reports" in page:
    section_header("Download Reports", "Export your financial summary")

    if df is None:
        render_empty_state()
        st.stop()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div style="background:var(--bg-card); border:1px solid var(--border);
                    border-radius:12px; padding:24px; text-align:center">
            <div style="font-size:2.5rem; margin-bottom:12px">📄</div>
            <div style="font-weight:600; margin-bottom:8px">PDF Report</div>
            <div style="font-size:0.85rem; color:#64748b; margin-bottom:16px">
                Full financial summary with charts, KPIs, and AI insights
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("📥 Generate PDF Report", use_container_width=True):
            with st.spinner("Building PDF…"):
                try:
                    pdf_bytes = generate_pdf_report(
                        df, kpis, st.session_state.ai_insights
                    )
                    st.download_button(
                        "⬇ Download PDF",
                        data=pdf_bytes,
                        file_name="financeai_report.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
                except Exception as e:
                    st.error(f"PDF error: {e}")

    with col2:
        st.markdown("""
        <div style="background:var(--bg-card); border:1px solid var(--border);
                    border-radius:12px; padding:24px; text-align:center">
            <div style="font-size:2.5rem; margin-bottom:12px">📊</div>
            <div style="font-weight:600; margin-bottom:8px">CSV Export</div>
            <div style="font-size:0.85rem; color:#64748b; margin-bottom:16px">
                Categorised and cleaned transactions as a CSV file
            </div>
        </div>
        """, unsafe_allow_html=True)

        export_df = df[["date", "description", "amount", "category", "month"]].copy()
        export_df["amount"] = export_df["amount"].abs()
        export_df["date"]   = export_df["date"].dt.strftime("%Y-%m-%d")
        csv_bytes = export_df.to_csv(index=False).encode("utf-8")

        st.download_button(
            "⬇ Download CSV",
            data=csv_bytes,
            file_name="financeai_transactions.csv",
            mime="text/csv",
            use_container_width=True,
        )

    # Full data preview
    st.markdown("---")
    section_header("Full Transaction Data")
    with st.expander("View all transactions", expanded=False):
        preview = df[["date", "description", "category", "amount", "month"]].copy()
        preview["amount"] = preview["amount"].abs().map("${:,.2f}".format)
        preview["date"]   = preview["date"].dt.strftime("%b %d, %Y")
        st.dataframe(preview, use_container_width=True, hide_index=True)

    # Summary stats
    section_header("Statistical Summary")
    expenses_only = df[df["is_expense"]]["amount"].abs()
    stats = pd.DataFrame({
        "Metric": ["Count", "Mean", "Median", "Std Dev", "Min", "Max", "25th %ile", "75th %ile"],
        "Value": [
            f"{len(expenses_only):,}",
            f"${expenses_only.mean():,.2f}",
            f"${expenses_only.median():,.2f}",
            f"${expenses_only.std():,.2f}",
            f"${expenses_only.min():,.2f}",
            f"${expenses_only.max():,.2f}",
            f"${expenses_only.quantile(0.25):,.2f}",
            f"${expenses_only.quantile(0.75):,.2f}",
        ],
    })
    st.dataframe(stats, use_container_width=True, hide_index=True)
