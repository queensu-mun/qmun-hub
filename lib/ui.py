from __future__ import annotations

import streamlit as st

from lib.icons import qmun_logo, tricolor_bar

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Inter+Tight:wght@500;600;700;800&family=Fraunces:opsz,wght@9..144,400;9..144,500&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bg: #060E1A;
    --bg-deep: #03080F;
    --surface: #0E1A2C;
    --surface-2: #142337;
    --surface-3: #1B2F47;
    --border: #182942;
    --border-strong: #233754;
    --text: #F2F2F0;
    --text-muted: #8B9AAD;
    --text-faint: #56697F;
    --accent: #9D1939;
    --accent-hover: #BB1E45;
    --accent-soft: rgba(157, 25, 57, 0.14);
    --gold: #B89D5E;
    --blue: #4B7BBF;
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
        radial-gradient(ellipse 70% 40% at 25% 0%, rgba(157, 25, 57, 0.07), transparent 60%),
        radial-gradient(ellipse 60% 45% at 100% 30%, rgba(75, 123, 191, 0.05), transparent 60%),
        var(--bg) !important;
}

[data-testid="stAppViewContainer"] {
    background: transparent !important;
}

.block-container {
    padding-top: 1rem;
    padding-bottom: 4rem;
    max-width: 1200px;
}

/* Hide Streamlit default chrome AND sidebar */
#MainMenu, footer, header[data-testid="stHeader"] { visibility: hidden; height: 0; }
[data-testid="stDecoration"] { display: none; }
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] { display: none !important; }
[data-testid="stAppViewContainer"] section[data-testid="stSidebar"] + .main { margin-left: 0 !important; }

/* Headings */
h1, h2, h3, h4, h5 {
    font-family: 'Inter Tight', 'Inter', sans-serif;
    font-weight: 700;
    letter-spacing: -0.025em;
    color: var(--text);
}
h1 { font-size: 2.1rem; line-height: 1.1; margin-bottom: 0.4rem; font-weight: 700; }
h2 { font-size: 1.35rem; line-height: 1.25; margin-top: 2rem; font-weight: 600; }
h3 { font-size: 1.05rem; line-height: 1.3; margin-top: 1.25rem; font-weight: 600; letter-spacing: -0.01em; }

p, li {
    font-size: 0.95rem;
    line-height: 1.65;
    color: var(--text);
}

a { color: var(--text); text-decoration: none; border-bottom: 1px solid var(--border-strong); transition: border-color 120ms; }
a:hover { border-bottom-color: var(--accent); }

code, pre, .stCode { font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; }

blockquote {
    font-family: 'Fraunces', serif;
    font-size: 1.15rem;
    font-style: italic;
    color: var(--text);
    border-left: 2px solid var(--accent) !important;
    padding-left: 1.25rem !important;
    margin: 1.5rem 0 !important;
}

/* ---------------- TOP NAV ---------------- */
.qmun-brand-row {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 0.5rem 0;
}
.qmun-brand-text-block { line-height: 1.1; }
.qmun-brand-text {
    font-family: 'Inter Tight', sans-serif;
    font-weight: 700;
    letter-spacing: -0.015em;
    font-size: 1.05rem;
    color: var(--text);
    line-height: 1;
}
.qmun-brand-sub {
    font-size: 0.66rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.16em;
    margin-top: 4px;
    font-weight: 500;
}
.qmun-user-row {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 0.5rem 0;
    justify-content: flex-end;
}
.qmun-user-info { text-align: right; line-height: 1.1; }
.qmun-user-name { font-weight: 500; font-size: 0.88rem; color: var(--text); }
.qmun-user-role {
    font-size: 0.66rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.14em;
    margin-top: 3px;
    font-weight: 500;
}
.qmun-user-avatar {
    width: 34px; height: 34px;
    border-radius: 50%;
    background: linear-gradient(135deg, var(--accent), #4B7BBF);
    display: inline-flex; align-items: center; justify-content: center;
    color: white; font-weight: 600; font-size: 0.78rem;
    flex-shrink: 0;
}

/* Streamlit page links: compact single-row nav */
[data-testid="stPageLink-NavLink"] {
    background: transparent !important;
    border: none !important;
    border-radius: 5px !important;
    padding: 0.3rem 0.4rem !important;
    color: var(--text-muted) !important;
    font-weight: 500 !important;
    font-size: 0.82rem !important;
    text-decoration: none !important;
    transition: color 140ms ease, background 140ms ease;
    white-space: nowrap;
}
[data-testid="stPageLink-NavLink"]:hover {
    color: var(--text) !important;
    background: var(--surface) !important;
}

/* Sign-out: muted text button, not full-weight */
button[data-testid="stBaseButton-secondary"]:has(p) {
    background: transparent !important;
    border: 1px solid var(--border) !important;
    color: var(--text-faint) !important;
    font-size: 0.75rem !important;
    padding: 0.25rem 0.6rem !important;
    margin-top: 0.3rem;
}

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
}
.stButton > button:hover, .stDownloadButton > button:hover, .stFormSubmitButton > button:hover {
    border-color: var(--accent);
    background: var(--surface-2);
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

/* Cards: kept ONLY where genuinely useful, much subtler now */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(18, 32, 53, 0.5) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    padding: 1.25rem !important;
    transition: border-color 140ms ease;
}
div[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: var(--border-strong) !important;
}

/* Metrics */
[data-testid="stMetric"] {
    background: var(--surface);
    padding: 1rem 1.2rem;
    border-radius: 10px;
    border: 1px solid var(--border);
}
[data-testid="stMetricLabel"] {
    color: var(--text-muted) !important;
    font-size: 0.7rem !important;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-weight: 600;
}
[data-testid="stMetricValue"] {
    font-family: 'Inter Tight', sans-serif;
    font-weight: 700;
    color: var(--text) !important;
    font-size: 1.55rem !important;
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
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    margin-bottom: 0.75rem;
}

/* Caption / muted text */
.stCaption, [data-testid="stCaptionContainer"] {
    color: var(--text-muted) !important;
    font-size: 0.85rem !important;
}

/* ---------------- Utility classes ---------------- */
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
    font-size: 1rem;
    line-height: 1.55;
    max-width: 600px;
    margin-top: 0.5rem;
    margin-bottom: 1.5rem;
    font-weight: 400;
}

.subtle { color: var(--text-muted); font-size: 0.85rem; }

.hero-display {
    font-family: 'Inter Tight', sans-serif;
    font-weight: 700;
    font-size: 2.6rem;
    line-height: 1.05;
    letter-spacing: -0.03em;
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

/* Section heading + small subline pattern */
.section-head {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 1rem;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--border);
}
.section-head h3 { margin: 0; font-size: 0.95rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.12em; color: var(--text-muted); }
.section-head .section-aux { font-size: 0.78rem; color: var(--text-faint); }

/* Borderless feature row used on home */
.feature-row {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1.5rem;
    margin-bottom: 2rem;
}
.feature-tile {
    position: relative;
    padding: 1.5rem 0 1.25rem;
    border-top: 2px solid var(--border);
    transition: border-color 200ms ease, transform 200ms ease;
}
.feature-tile:hover {
    border-top-color: var(--accent);
}
.feature-tile-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    border-radius: 8px;
    background: var(--accent-soft);
    color: var(--accent);
    margin-bottom: 0.85rem;
}
.feature-tile-title {
    font-family: 'Inter Tight', sans-serif;
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 0.35rem;
    letter-spacing: -0.015em;
}
.feature-tile-blurb {
    color: var(--text-muted);
    font-size: 0.88rem;
    line-height: 1.55;
    margin-bottom: 0.85rem;
    min-height: 3rem;
}
.feature-tile-link {
    color: var(--accent);
    font-size: 0.85rem;
    font-weight: 600;
    border: none;
}
.feature-tile-link:hover { color: var(--accent-hover); border: none; }

/* This-week split-card */
.week-strip {
    display: flex;
    gap: 1.5rem;
    margin-bottom: 2.5rem;
}
.week-cell {
    flex: 1;
    padding: 1.25rem 1.5rem;
    background: linear-gradient(135deg, var(--surface), rgba(18, 32, 53, 0.4));
    border-left: 3px solid var(--accent);
    border-radius: 0 10px 10px 0;
    transition: all 200ms ease;
}
.week-cell:hover { transform: translateX(2px); }
.week-cell.gold { border-left-color: var(--gold); }
.week-cell-day {
    color: var(--text-muted);
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    margin-bottom: 0.5rem;
}
.week-cell-committee {
    font-family: 'Inter Tight', sans-serif;
    font-size: 1.2rem;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 0.25rem;
    letter-spacing: -0.015em;
}
.week-cell-topic {
    color: var(--text-muted);
    font-size: 0.92rem;
    line-height: 1.5;
}

/* Footer */
.qmun-footer {
    margin-top: 5rem;
    padding-top: 1.5rem;
    border-top: 1px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    color: var(--text-faint);
    font-size: 0.75rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}

/* Hero panel (placeholder when no hero.jpg) */
.hero-panel {
    position: relative;
    height: 240px;
    border-radius: 14px;
    background:
        radial-gradient(ellipse 70% 60% at 100% 0%, rgba(157, 25, 57, 0.18), transparent 70%),
        radial-gradient(ellipse 60% 60% at 0% 100%, rgba(75, 123, 191, 0.12), transparent 70%),
        linear-gradient(135deg, #0E1A2C, #07101D);
    border: 1px solid var(--border);
    overflow: hidden;
    padding: 1.75rem 1.75rem 0;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}
.hero-panel-mark {
    font-family: 'Inter Tight', sans-serif;
    font-size: 2.5rem;
    font-weight: 800;
    letter-spacing: -0.04em;
    line-height: 1;
    color: var(--text);
    opacity: 0.9;
}
.hero-panel-title {
    font-family: 'Inter Tight', sans-serif;
    font-size: 1.5rem;
    font-weight: 700;
    line-height: 1.05;
    letter-spacing: -0.02em;
    color: var(--text);
    margin-top: -3rem;
    text-align: right;
}
.hero-panel-meta {
    font-size: 0.7rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.18em;
    font-weight: 600;
    text-align: right;
    margin-bottom: 1rem;
}
.hero-panel-tricolor {
    display: flex;
    height: 4px;
    margin: 0 -1.75rem;
    margin-top: auto;
}
.hero-panel-tricolor > div { flex: 1; }

/* Announcement banner */
.qmun-announce {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 0.85rem 1.1rem;
    background: linear-gradient(90deg, var(--accent-soft), rgba(75, 123, 191, 0.06));
    border: 1px solid rgba(157, 25, 57, 0.3);
    border-radius: 8px;
    margin-bottom: 1.5rem;
    color: var(--text);
    font-size: 0.92rem;
}
.qmun-announce-dot {
    width: 7px; height: 7px; border-radius: 50%;
    background: var(--accent);
    flex-shrink: 0;
    box-shadow: 0 0 0 4px var(--accent-soft);
}
.qmun-announce-label {
    color: var(--accent);
    font-size: 0.65rem;
    text-transform: uppercase;
    letter-spacing: 0.16em;
    font-weight: 700;
    flex-shrink: 0;
    margin-right: 6px;
}

/* Hero photo treatment */
.hero-photo-wrap {
    position: relative;
    border-radius: 12px;
    overflow: hidden;
    height: 280px;
    background: var(--surface);
    border: 1px solid var(--border);
}
.hero-photo {
    width: 100%; height: 100%; object-fit: cover; display: block;
    filter: brightness(0.65) saturate(1.1);
}
.hero-photo-overlay {
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, rgba(6, 14, 26, 0.4) 0%, rgba(6, 14, 26, 0) 50%, rgba(6, 14, 26, 0.7) 100%);
    pointer-events: none;
}

/* Prep status card */
.prep-card {
    padding: 1.1rem 1.25rem;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    border-left: 3px solid var(--accent);
}
.prep-card.gold { border-left-color: var(--gold); }
.prep-card.blue { border-left-color: var(--blue); }
.prep-conf {
    color: var(--text-muted);
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    font-weight: 600;
    margin-bottom: 0.3rem;
}
.prep-role {
    font-family: 'Inter Tight', sans-serif;
    font-size: 1.05rem;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 0.25rem;
    letter-spacing: -0.01em;
}
.prep-when {
    color: var(--text-muted);
    font-size: 0.85rem;
    margin-bottom: 0.75rem;
}
.prep-checks { display: flex; gap: 1rem; font-size: 0.78rem; color: var(--text-muted); }
.prep-checks .done { color: var(--gold); }
.prep-checks .pending { color: var(--text-faint); }

.stat-line {
    display: flex;
    gap: 2.5rem;
    padding: 1rem 0 0;
    color: var(--text-muted);
    font-size: 0.85rem;
}
.stat-line .stat-num {
    color: var(--text);
    font-weight: 700;
    font-family: 'Inter Tight', sans-serif;
    font-size: 1.05rem;
    margin-right: 4px;
}

/* Horizontal radio styled as segmented control */
.stRadio[role="radiogroup"], div[data-testid="stRadio"] > div[role="radiogroup"] {
    display: inline-flex !important;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 3px;
    gap: 0 !important;
}
div[data-testid="stRadio"] label {
    padding: 0.4rem 1rem !important;
    border-radius: 6px !important;
    margin: 0 !important;
    cursor: pointer;
    font-size: 0.85rem !important;
    color: var(--text-muted) !important;
    transition: all 140ms ease;
    text-transform: none !important;
    letter-spacing: 0 !important;
    font-weight: 500 !important;
}
div[data-testid="stRadio"] label:hover { color: var(--text) !important; }
div[data-testid="stRadio"] label[data-baseweb="radio"] > div:first-child { display: none !important; }
div[data-testid="stRadio"] label:has(input:checked) {
    background: var(--accent-soft) !important;
    color: var(--accent) !important;
    font-weight: 600 !important;
}

/* Search result rows (Archive) */
.result-row {
    padding: 1rem 0 0.75rem;
    border-bottom: 1px solid var(--border);
}
.result-title {
    font-family: 'Inter Tight', sans-serif;
    font-weight: 700;
    font-size: 1.05rem;
    color: var(--text);
    letter-spacing: -0.01em;
    margin-bottom: 0.4rem;
}
.result-meta { margin-bottom: 0.5rem; }
.result-snippet {
    color: var(--text-muted);
    font-size: 0.9rem;
    line-height: 1.55;
    margin: 0.5rem 0 0;
    border-left: 2px solid var(--border-strong);
    padding-left: 0.85rem;
}

/* Doc list row (Archive default view) */
.doc-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.85rem 0;
    border-bottom: 1px solid var(--border);
    gap: 1rem;
}
.doc-row-title {
    font-family: 'Inter Tight', sans-serif;
    font-weight: 600;
    color: var(--text);
    font-size: 0.95rem;
    margin-bottom: 4px;
    letter-spacing: -0.01em;
}
.doc-row-meta { font-size: 0.78rem; }

/* Activity row (recent briefs / etc) */
.activity-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.85rem 0;
    border-bottom: 1px solid var(--border);
    transition: background 140ms ease;
    gap: 1rem;
}
.activity-row:hover { background: rgba(20, 35, 55, 0.4); }
.activity-row:last-child { border-bottom: 0; }
.activity-title {
    font-family: 'Inter Tight', sans-serif;
    font-weight: 600;
    color: var(--text);
    font-size: 0.95rem;
    margin-bottom: 3px;
    letter-spacing: -0.01em;
}
.activity-sep { color: var(--text-faint); margin: 0 4px; }
.activity-meta { color: var(--text-muted); font-size: 0.85rem; line-height: 1.4; }
.activity-tag {
    color: var(--text-muted);
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    font-weight: 600;
    padding: 3px 9px;
    border-radius: 5px;
    background: var(--surface);
    border: 1px solid var(--border);
    flex-shrink: 0;
}
</style>
"""


def inject_global_css() -> None:
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


def page_header(_eyebrow_unused: str, title: str, lede: str | None = None) -> None:
    """Eyebrow argument retained for backward compat but no longer rendered."""
    st.markdown(f"<h1>{title}</h1>", unsafe_allow_html=True)
    if lede:
        st.markdown(f"<div class='lede'>{lede}</div>", unsafe_allow_html=True)


def tag(text: str, *, accent: bool = False) -> str:
    cls = "tag tag-accent" if accent else "tag"
    return f"<span class='{cls}'>{text}</span>"


def top_nav(user) -> None:
    """Single-bar nav: brand | page links | user chip — all on one row."""
    initials = "".join(w[0].upper() for w in user.name.split()[:2]) if user.name else "?"
    first_name = user.name.split()[0] if user.name else user.name

    pages = [
        ("Home", "app.py"),
        ("Brief", "pages/2_Brief.py"),
        ("Archive", "pages/1_Archive.py"),
        ("Chatbot", "pages/3_Chatbot.py"),
        ("Training", "pages/4_Training.py"),
        ("Contribute", "pages/6_Alumni_Interview.py"),
    ]
    if user.is_exec:
        pages.append(("Director", "pages/5_Director.py"))

    # One row: brand(2) | links(1 each) | user(2)
    cols = st.columns([2] + [1] * len(pages) + [2])

    with cols[0]:
        st.markdown(
            f"<div class='qmun-brand-row' style='padding:0.3rem 0;'>"
            f"{qmun_logo(size=28)}"
            f"<div class='qmun-brand-text' style='font-size:0.9rem;'>Queen's MUN</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    for i, (label, path) in enumerate(pages):
        with cols[1 + i]:
            st.page_link(path, label=label)

    with cols[-1]:
        st.markdown(
            f"<div class='qmun-user-row' style='padding:0.2rem 0; gap:8px;'>"
            f"<div class='qmun-user-info'>"
            f"<div class='qmun-user-name' style='font-size:0.82rem;'>{first_name}</div>"
            f"<div class='qmun-user-role'>{user.role.title()}</div>"
            f"</div>"
            f"<div class='qmun-user-avatar' style='width:28px;height:28px;font-size:0.7rem;'>{initials}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
        if st.button("Sign out", key="nav_signout", use_container_width=True):
            from lib.auth import sign_out
            sign_out()
            st.rerun()

    # 1px tricolor line as bottom border of the nav bar
    st.markdown(tricolor_bar(height=1), unsafe_allow_html=True)
    st.markdown("<div style='height:1.25rem;'></div>", unsafe_allow_html=True)


def feature_tile(*, icon_svg: str, title: str, blurb: str, page_path: str, link_label: str = "Open") -> None:
    """Borderless feature tile: top accent line, icon chip, title, blurb, page link."""
    st.markdown(
        f"""
<div class='feature-tile'>
  <div class='feature-tile-icon'>{icon_svg}</div>
  <div class='feature-tile-title'>{title}</div>
  <div class='feature-tile-blurb'>{blurb}</div>
</div>
""",
        unsafe_allow_html=True,
    )
    st.page_link(page_path, label=f"{link_label} →")


def brand_footer() -> None:
    st.markdown(
        """
<div class='qmun-footer'>
  <div>Queen's Model UN · Team Workspace</div>
  <div>2026 / 2027</div>
</div>
""",
        unsafe_allow_html=True,
    )
