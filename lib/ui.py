import streamlit as st

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', system-ui, sans-serif;
}

h1, h2, h3, h4 { font-weight: 600; letter-spacing: -0.01em; }
h1 { font-size: 2.0rem; }
h2 { font-size: 1.5rem; }

code, pre { font-family: 'JetBrains Mono', monospace; }

[data-testid="stSidebar"] { background-color: #14171C; }

div[data-testid="stContainer"][data-border="true"],
div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 12px;
    transition: border-color 120ms ease;
}

div[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: rgba(184, 134, 11, 0.5);
}

button[kind="primary"] {
    border-radius: 8px;
    font-weight: 500;
}

[data-testid="stMetric"] {
    background-color: #1A1D23;
    padding: 16px;
    border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.06);
}

.qmun-pill {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 500;
    background: rgba(184, 134, 11, 0.15);
    color: #E0B048;
    border: 1px solid rgba(184, 134, 11, 0.35);
}

.qmun-muted { color: #8A8F98; font-size: 0.9rem; }

.qmun-footer {
    margin-top: 60px;
    padding-top: 24px;
    border-top: 1px solid rgba(255,255,255,0.06);
    color: #5A6068;
    font-size: 0.8rem;
    text-align: center;
}
</style>
"""


def inject_global_css() -> None:
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


def page_header(title: str, subtitle: str | None = None) -> None:
    st.markdown(f"# {title}")
    if subtitle:
        st.markdown(f"<div class='qmun-muted'>{subtitle}</div>", unsafe_allow_html=True)
    st.markdown("<br/>", unsafe_allow_html=True)


def pill(text: str) -> str:
    return f"<span class='qmun-pill'>{text}</span>"


def brand_footer() -> None:
    st.markdown(
        "<div class='qmun-footer'>QMUN Hub · Queen's Model UN · "
        "Built for the team, by the team.</div>",
        unsafe_allow_html=True,
    )
