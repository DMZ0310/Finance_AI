"""
Reusable Streamlit UI components: KPI cards, metric rows, styled containers.
"""

import streamlit as st


def kpi_card(label: str, value: str, delta: str = "", icon: str = "💰", color: str = "#6366f1"):
    """Render a styled KPI card with an icon, value, and optional delta."""
    delta_html = ""
    if delta:
        delta_color = "#22c55e" if "+" in delta or "↑" in delta else "#f43f5e"
        delta_html = f'<div class="kpi-delta" style="color:{delta_color}">{delta}</div>'

    st.markdown(f"""
    <div class="kpi-card" style="border-left: 4px solid {color}">
        <div class="kpi-icon">{icon}</div>
        <div class="kpi-content">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            {delta_html}
        </div>
    </div>
    """, unsafe_allow_html=True)


def section_header(title: str, subtitle: str = ""):
    """Render a styled section heading."""
    sub_html = f'<p class="section-subtitle">{subtitle}</p>' if subtitle else ""
    st.markdown(f"""
    <div class="section-header">
        <h2 class="section-title">{title}</h2>
        {sub_html}
    </div>
    """, unsafe_allow_html=True)


def info_banner(message: str, kind: str = "info"):
    """kind: 'info' | 'success' | 'warning' | 'error'"""
    icons  = {"info": "ℹ️", "success": "✅", "warning": "⚠️", "error": "❌"}
    colors = {
        "info"   : ("rgba(99,102,241,0.15)", "#818cf8"),
        "success": ("rgba(34,197,94,0.15)",  "#4ade80"),
        "warning": ("rgba(245,158,11,0.15)", "#fbbf24"),
        "error"  : ("rgba(244,63,94,0.15)",  "#fb7185"),
    }
    bg, border = colors.get(kind, colors["info"])
    icon = icons.get(kind, "ℹ️")
    st.markdown(f"""
    <div style="background:{bg}; border:1px solid {border}; border-radius:10px;
                padding:12px 16px; margin:8px 0; display:flex; gap:10px; align-items:flex-start;">
        <span style="font-size:18px">{icon}</span>
        <span style="color:#e2e8f0; font-size:14px; line-height:1.5">{message}</span>
    </div>
    """, unsafe_allow_html=True)


def chat_bubble(message: str, role: str):
    """Render a styled chat bubble for user or assistant."""
    if role == "user":
        st.markdown(f"""
        <div class="chat-bubble user-bubble">
            <div class="chat-avatar">👤</div>
            <div class="chat-text">{message}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Format markdown-like text
        formatted = (
            message
            .replace("**", "<strong>", 1)
        )
        # Simple bold formatting
        import re
        formatted = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", message)
        formatted = formatted.replace("\n", "<br>")
        st.markdown(f"""
        <div class="chat-bubble ai-bubble">
            <div class="chat-avatar">🤖</div>
            <div class="chat-text">{formatted}</div>
        </div>
        """, unsafe_allow_html=True)


def render_css():
    """Inject the main application CSS."""
    st.markdown("""
    <style>
    /* ── Google Font Import ── */
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

    /* ── Root Variables ── */
    :root {
        --bg-primary:    #0a0a1a;
        --bg-secondary:  #111128;
        --bg-card:       #16162a;
        --bg-card-hover: #1e1e38;
        --border:        rgba(255,255,255,0.08);
        --border-active: rgba(99,102,241,0.4);
        --accent:        #6366f1;
        --accent-light:  #818cf8;
        --text-primary:  #f1f5f9;
        --text-secondary:#94a3b8;
        --text-muted:    #64748b;
        --success:       #22c55e;
        --danger:        #f43f5e;
        --warning:       #f59e0b;
        --radius:        12px;
        --shadow:        0 4px 24px rgba(0,0,0,0.3);
    }

    /* ── Global Reset ── */
    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif !important;
        background-color: var(--bg-primary) !important;
        color: var(--text-primary) !important;
    }

    .stApp { background-color: var(--bg-primary) !important; }

    /* ── Header ── */
    .main-header {
        background: linear-gradient(135deg, #1a1a3e 0%, #0f0f24 50%, #1a1a3e 100%);
        border-bottom: 1px solid var(--border);
        padding: 24px 32px 20px;
        margin: -1rem -1rem 2rem -1rem;
        position: relative;
        overflow: hidden;
    }
    .main-header::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -10%;
        width: 40%;
        height: 200%;
        background: radial-gradient(ellipse, rgba(99,102,241,0.15), transparent 70%);
        pointer-events: none;
    }
    .main-header h1 {
        font-size: 2rem !important;
        font-weight: 700 !important;
        background: linear-gradient(135deg, #818cf8, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0 !important;
        padding: 0 !important;
    }
    .main-header p {
        color: var(--text-secondary) !important;
        font-size: 0.9rem !important;
        margin: 4px 0 0 !important;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background-color: var(--bg-secondary) !important;
        border-right: 1px solid var(--border) !important;
    }
    [data-testid="stSidebar"] .stRadio label {
        color: var(--text-secondary) !important;
        font-size: 0.9rem !important;
        padding: 6px 0;
    }
    [data-testid="stSidebar"] .stRadio label:hover {
        color: var(--text-primary) !important;
    }

    /* ── KPI Cards ── */
    .kpi-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 18px 20px;
        display: flex;
        gap: 14px;
        align-items: flex-start;
        transition: transform 0.2s, box-shadow 0.2s;
        margin-bottom: 8px;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow);
        background: var(--bg-card-hover);
    }
    .kpi-icon { font-size: 1.8rem; line-height: 1; }
    .kpi-label {
        color: var(--text-muted);
        font-size: 0.78rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 4px;
    }
    .kpi-value {
        color: var(--text-primary);
        font-size: 1.5rem;
        font-weight: 700;
        font-family: 'DM Mono', monospace;
        line-height: 1.1;
    }
    .kpi-delta { font-size: 0.82rem; font-weight: 500; margin-top: 3px; }

    /* ── Section Headers ── */
    .section-header { margin: 28px 0 16px; }
    .section-title {
        font-size: 1.25rem !important;
        font-weight: 600 !important;
        color: var(--text-primary) !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    .section-subtitle {
        color: var(--text-muted) !important;
        font-size: 0.85rem !important;
        margin: 4px 0 0 !important;
    }

    /* ── Chat ── */
    .chat-bubble {
        display: flex;
        gap: 12px;
        margin: 12px 0;
        align-items: flex-start;
    }
    .chat-avatar {
        font-size: 1.4rem;
        min-width: 36px;
        text-align: center;
    }
    .chat-text {
        padding: 12px 16px;
        border-radius: 12px;
        font-size: 0.92rem;
        line-height: 1.6;
        max-width: 80%;
    }
    .user-bubble { flex-direction: row-reverse; }
    .user-bubble .chat-text {
        background: linear-gradient(135deg, #4f46e5, #7c3aed);
        color: white;
        border-radius: 12px 2px 12px 12px;
    }
    .ai-bubble .chat-text {
        background: var(--bg-card);
        border: 1px solid var(--border);
        color: var(--text-primary);
        border-radius: 2px 12px 12px 12px;
    }

    /* ── Buttons ── */
    .stButton > button {
        background: linear-gradient(135deg, #6366f1, #7c3aed) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-family: 'DM Sans', sans-serif !important;
        font-weight: 500 !important;
        padding: 10px 24px !important;
        transition: all 0.2s !important;
    }
    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 16px rgba(99,102,241,0.4) !important;
    }

    /* ── Inputs ── */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        color: var(--text-primary) !important;
        font-family: 'DM Sans', sans-serif !important;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--border-active) !important;
        box-shadow: 0 0 0 3px rgba(99,102,241,0.15) !important;
    }

    /* ── File Uploader ── */
    [data-testid="stFileUploader"] {
        background: var(--bg-card) !important;
        border: 2px dashed var(--border) !important;
        border-radius: var(--radius) !important;
        padding: 16px !important;
        transition: border-color 0.2s !important;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: var(--accent) !important;
    }

    /* ── DataFrames / Tables ── */
    .stDataFrame {
        background: var(--bg-card) !important;
        border-radius: var(--radius) !important;
        border: 1px solid var(--border) !important;
    }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {
        background: var(--bg-card) !important;
        border-radius: 10px 10px 0 0 !important;
        gap: 4px !important;
        padding: 4px !important;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        color: var(--text-secondary) !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #6366f1, #7c3aed) !important;
        color: white !important;
    }

    /* ── Expander ── */
    .streamlit-expanderHeader {
        background: var(--bg-card) !important;
        border-radius: var(--radius) !important;
        color: var(--text-primary) !important;
        font-weight: 500 !important;
    }

    /* ── Divider ── */
    hr {
        border-color: var(--border) !important;
        margin: 20px 0 !important;
    }

    /* ── Plotly charts in dark mode ── */
    .js-plotly-plot .plotly {
        background: transparent !important;
    }

    /* ── Spinner ── */
    .stSpinner > div { border-top-color: var(--accent) !important; }

    /* ── Hide Streamlit branding ── */
    #MainMenu { visibility: hidden; }
    footer     { visibility: hidden; }
    header     { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)


def render_header():
    """Render the main app header."""
    st.markdown("""
    <div class="main-header">
        <h1>⚡ FinanceAI Assistant</h1>
        <p>AI-powered personal finance analysis & budgeting</p>
    </div>
    """, unsafe_allow_html=True)


def render_empty_state(message: str = "Upload a bank statement to get started"):
    """Display an empty state placeholder."""
    st.markdown(f"""
    <div style="text-align:center; padding:60px 20px; color:var(--text-muted);">
        <div style="font-size:3rem; margin-bottom:16px;">📊</div>
        <div style="font-size:1.1rem; font-weight:500; margin-bottom:8px; color:var(--text-secondary);">
            No Data Yet
        </div>
        <div style="font-size:0.9rem;">{message}</div>
    </div>
    """, unsafe_allow_html=True)
