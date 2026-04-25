from __future__ import annotations

import streamlit as st

from lib.icons import qmun_logo, tricolor_bar

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Inter+Tight:wght@500;600;700;800&family=Fraunces:opsz,wght@9..144,400;9..144,500&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bg: #0A0A0B;
    --bg-warm: #0D0C0E;
    --surface: #131318;
    --surface-2: #1A1A22;
    --surface-3: #22222C;
    --border: #1F2028;
    --border-strong: #2A2B35;
    --text: #F2F2F0;
    --text-muted: #8B8B94;
    --text-faint: #54545C;
    --accent: #9D1939;
    --accent-hover: #B81C44;
    --accent-soft: rgba(157, 25, 57, 0.12);
    --gold: #B89D5E;
    --blue: #1B3A6B;
}

/* Global */
html, body, [class*="css"], .stMarkdown, .stTextInput, .stSelectbox {
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
    font-feature-settings: "ss01", "cv11";
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

body {
    background:
        radial-gradient(ellipse 80% 50% at 50% 0%, rgba(157, 25, 57, 0.06), transparent 60%),
        radial-gradient(ellipse 60% 40% at 100% 100%, rgba(27, 58, 107, 0.05), transparent 60%),
        var(--bg) !important;
}

[data-testid="stAppViewContainer"] {
    background: transparent !important;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 4rem;
    max-width: 1200px;
}

/* Hide Streamlit chrome */
#MainMenu, footer, header[data-testid="stHeader"] { visibility: hidden; height: 0; }
[data-testid="stDecoration"] { display: none; }

/* Headings */
h1, h2, h3, h4, h5 {
    font-family: 'Inter Tight', 'Inter', sans-serif;
    font-weight: 700;
    letter-spacing: -0.025em;
    color: var(--text);
}
h1 { font-size: 2.75rem; line-height: 1.05; margin-bottom: 0.5rem; font-weight: 700; }
h2 { font-size: 1.75rem; line-height: 1.15; margin-top: 2.5rem; font-weight: 600; }
h3 { font-size: 1.2rem; line-height: 1.3; margin-top: 1.5rem; font-weight: 600; letter-spacing: -0.015em; }

p, li {
    font-size: 0.95rem;
    line-height: 1.65;
    color: var(--text);
}

a { color: var(--text); text-decoration: none; border-bottom: 1px solid var(--border-strong); transition: border-color 120ms; }
a:hover { border-bottom-color: var(--accent); }

/* Streamlit page links */
[data-testid="stPageLink-NavLink"] {
    background: transparent !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    padding: 0.5rem 0.85rem !important;
    color: var(--text) !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    transition: all 120ms ease;
    text-decoration: none !important;
}
[data-testid="stPageLink-NavLink"]:hover {
    border-color: var(--accent) !important;
    background: var(--accent-soft) !important;
}

code, pre, .stCode {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
}

blockquote {
    font-family: 'Fraunces', serif;
    font-size: 1.15rem;
    font-style: italic;
    color: var(--text);
    border-left: 2px solid var(--accent) !important;
    padding-left: 1.25rem !important;
    margin: 1.5rem 0 !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #08080A 0%, #0B0A0D 100%) !important;
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] .block-container { padding-top: 1.5rem; padding-bottom: 1.5rem; }
[data-testid="stSidebar"] [data-testid="stMarkdown"] p { font-size: 0.9rem; }

/* Buttons */
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
    border-radius: 8px;
    border: 1px solid var(--border-strong);
    background: var(--surface);
    color: var(--text);
    font-weight: 500;
    font-size: 0.875rem;
    padding: 0.5rem 1.1rem;
    transition: all 140ms ease;
    box-shadow: 0 1px 2px rgba(0,0,0,0.2);
}
.stButton > button:hover, .stDownloadButton > button:hover, .stFormSubmitButton > button:hover {
    border-color: var(--accent);
    background: var(--surface-2);
    transform: translateY(-1px);
    box-shadow: 0 3px 8px rgba(157, 25, 57, 0.15);
}
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {
    background: linear-gradient(180deg, var(--accent-hover), var(--accent));
    border-color: var(--accent);
    color: var(--text);
    font-weight: 600;
    box-shadow: 0 2px 6px rgba(157, 25, 57, 0.25);
}
.stButton > button[kind="primary"]:hover, .stFormSubmitButton > button[kind="primary"]:hover {
    background: linear-gradient(180deg, #C92652, var(--accent-hover));
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(157, 25, 57, 0.4);
}

/* Inputs */
.stTextInput input, .stTextArea textarea, .stNumberInput input, .stDateInput input,
.stSelectbox > div > div, [data-baseweb="input"] {
    background-color: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
    font-size: 0.95rem !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px var(--accent-soft) !important;
}
.stTextInput label, .stTextArea label, .stSelectbox label, .stRadio label, .stNumberInput label, .stDateInput label {
    color: var(--text-muted) !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

/* Cards */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: linear-gradient(180deg, var(--surface), var(--bg-warm)) !important;
    border: 1px solid var(--border) !important;
    border-radius: 14px !important;
    padding: 1.5rem !important;
    transition: all 200ms ease;
    position: relative;
    overflow: hidden;
}
div[data-testid="stVerticalBlockBorderWrapper"]::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(242, 242, 240, 0.08), transparent);
}
div[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: var(--border-strong) !important;
    transform: translateY(-1px);
    box-shadow: 0 8px 24px rgba(0,0,0,0.3);
}

/* Metrics */
[data-testid="stMetric"] {
    background: linear-gradient(180deg, var(--surface), var(--bg-warm));
    padding: 1.1rem 1.25rem;
    border-radius: 12px;
    border: 1px solid var(--border);
}
[data-testid="stMetricLabel"] {
    color: var(--text-muted) !important;
    font-size: 0.72rem !important;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-weight: 600;
}
[data-testid="stMetricValue"] {
    font-family: 'Inter Tight', sans-serif;
    font-weight: 700;
    color: var(--text) !important;
    font-size: 1.6rem !important;
}

/* Dividers */
hr, div[data-testid="stMarkdownContainer"] hr {
    border: 0;
    border-top: 1px solid var(--border);
    margin: 2.5rem 0;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    border-bottom: 1px solid var(--border);
    margin-bottom: 1.5rem;
}
.stTabs [data-baseweb="tab"] {
    color: var(--text-muted);
    font-weight: 500;
    font-size: 0.875rem;
    padding: 0.65rem 1.1rem;
    border-bottom: 2px solid transparent;
    transition: all 140ms ease;
}
.stTabs [data-baseweb="tab"]:hover { color: var(--text); }
.stTabs [aria-selected="true"] {
    color: var(--text) !important;
    border-bottom-color: var(--accent) !important;
    font-weight: 600;
}

/* Chat */
[data-testid="stChatMessage"] {
    background: linear-gradient(180deg, var(--surface), var(--bg-warm));
    border: 1px solid var(--border);
    border-radius: 12px;
    margin-bottom: 0.75rem;
}

/* Caption / muted text */
.stCaption, [data-testid="stCaptionContainer"] {
    color: var(--text-muted) !important;
    font-size: 0.85rem !important;
}

/* Custom utility classes */
.eyebrow {
    color: var(--accent);
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.16em;
    margin-bottom: 0.6rem;
    display: inline-flex;
    align-items: center;
    gap: 8px;
}
.eyebrow::before {
    content: '';
    display: inline-block;
    width: 16px;
    height: 1px;
    background: var(--accent);
}

.lede {
    color: var(--text-muted);
    font-size: 1.1rem;
    line-height: 1.55;
    max-width: 640px;
    margin-top: 0.75rem;
    margin-bottom: 2.5rem;
    font-weight: 400;
}

.subtle {
    color: var(--text-muted);
    font-size: 0.85rem;
}

.hero-display {
    font-family: 'Inter Tight', sans-serif;
    font-weight: 800;
    font-size: 3.5rem;
    line-height: 1;
    letter-spacing: -0.035em;
    color: var(--text);
    margin: 0;
}

.tag {
    display: inline-flex;
    align-items: center;
    padding: 3px 9px;
    border-radius: 6px;
    font-size: 0.7rem;
    font-weight: 500;
    background: var(--surface-2);
    color: var(--text-muted);
    border: 1px solid var(--border);
    margin-right: 4px;
    letter-spacing: 0.02em;
}
.tag-accent {
    background: var(--accent-soft);
    color: var(--accent);
    border-color: rgba(157, 25, 57, 0.3);
    font-weight: 600;
}

/* Branded card with icon */
.feature-card {
    display: flex;
    flex-direction: column;
    gap: 0;
    height: 100%;
}
.feature-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 38px;
    height: 38px;
    border-radius: 9px;
    background: var(--accent-soft);
    color: var(--accent);
    margin-bottom: 0.85rem;
}
.feature-title {
    font-family: 'Inter Tight', sans-serif;
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 0.35rem;
    letter-spacing: -0.015em;
}
.feature-blurb {
    color: var(--text-muted);
    font-size: 0.9rem;
    line-height: 1.5;
    margin-bottom: 1rem;
    flex: 1;
}

/* Brand mark in sidebar */
.brand-mark {
    display: flex;
    align-items: center;
    gap: 10px;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 1.5rem;
}
.brand-text {
    font-family: 'Inter Tight', sans-serif;
    font-weight: 700;
    letter-spacing: -0.015em;
    font-size: 1.05rem;
    color: var(--text);
    line-height: 1;
}
.brand-sub {
    font-size: 0.7rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin-top: 3px;
}

/* User chip in sidebar */
.user-chip {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 0.7rem 0.8rem;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    margin-bottom: 1rem;
}
.user-avatar {
    width: 30px; height: 30px;
    border-radius: 50%;
    background: linear-gradient(135deg, var(--accent), var(--blue));
    display: flex; align-items: center; justify-content: center;
    color: white; font-weight: 600; font-size: 0.78rem;
    flex-shrink: 0;
}
.user-name { font-weight: 500; font-size: 0.9rem; color: var(--text); line-height: 1.1; }
.user-role { font-size: 0.7rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.1em; margin-top: 2px; }

/* Footer */
.qmun-footer {
    margin-top: 5rem;
    padding-top: 1.5rem;
    border-top: 1px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
}
.qmun-footer-left {
    color: var(--text-faint);
    font-size: 0.78rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}

/* Stats line */
.stat-line {
    display: flex;
    gap: 2rem;
    padding: 0.5rem 0;
    color: var(--text-muted);
    font-size: 0.85rem;
}
.stat-line .stat-num {
    color: var(--text);
    font-weight: 600;
    font-family: 'Inter Tight', sans-serif;
}

/* This-week feature card */
.week-card-day {
    color: var(--accent);
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    margin-bottom: 0.5rem;
}
.week-card-committee {
    font-family: 'Inter Tight', sans-serif;
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 0.35rem;
    letter-spacing: -0.015em;
}
.week-card-topic {
    color: var(--text-muted);
    font-size: 0.9rem;
    line-height: 1.5;
    margin-bottom: 1rem;
}
</style>
"""


def inject_global_css() -> None:
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


def page_header(eyebrow: str, title: str, lede: str | None = None) -> None:
    st.markdown(tricolor_bar(height=2), unsafe_allow_html=True)
    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='eyebrow'>{eyebrow}</div>", unsafe_allow_html=True)
    st.markdown(f"<h1>{title}</h1>", unsafe_allow_html=True)
    if lede:
        st.markdown(f"<div class='lede'>{lede}</div>", unsafe_allow_html=True)


def tag(text: str, *, accent: bool = False) -> str:
    cls = "tag tag-accent" if accent else "tag"
    return f"<span class='{cls}'>{text}</span>"


def sidebar_brand() -> str:
    return f"""
<div class='brand-mark'>
  {qmun_logo(size=36)}
  <div>
    <div class='brand-text'>Queen's MUN</div>
    <div class='brand-sub'>Team workspace</div>
  </div>
</div>
"""


def user_chip(name: str, role: str) -> str:
    initials = "".join(w[0].upper() for w in name.split()[:2]) if name else "?"
    return f"""
<div class='user-chip'>
  <div class='user-avatar'>{initials}</div>
  <div>
    <div class='user-name'>{name}</div>
    <div class='user-role'>{role}</div>
  </div>
</div>
"""


def feature_card(*, icon_svg: str, title: str, blurb: str) -> None:
    """Render a feature card. Use inside a `with st.container(border=True)` block."""
    st.markdown(
        f"""
<div class='feature-card'>
  <div class='feature-icon'>{icon_svg}</div>
  <div class='feature-title'>{title}</div>
  <div class='feature-blurb'>{blurb}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def brand_footer() -> None:
    st.markdown(
        """
<div class='qmun-footer'>
  <div class='qmun-footer-left'>Queen's Model UN · Team Workspace</div>
  <div style='color: var(--text-faint); font-size: 0.78rem;'>2026 / 2027</div>
</div>
""",
        unsafe_allow_html=True,
    )
