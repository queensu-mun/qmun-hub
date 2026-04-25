"""Inline SVG icons (Lucide-style, single-stroke). Returns HTML strings."""
from __future__ import annotations

import base64


def _svg(path: str, *, size: int = 20, stroke_width: float = 1.5, color: str = "currentColor") -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="{stroke_width}" '
        f'stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-0.15em;display:inline-block;">'
        f'{path}</svg>'
    )


def brief(size: int = 20) -> str:
    return _svg(
        '<path d="M14 3v4a1 1 0 0 0 1 1h4"/>'
        '<path d="M17 21H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h7l5 5v11a2 2 0 0 1-2 2z"/>'
        '<path d="M9 9h1"/><path d="M9 13h6"/><path d="M9 17h6"/>',
        size=size,
    )


def archive(size: int = 20) -> str:
    return _svg(
        '<rect x="3" y="3" width="18" height="4" rx="1"/>'
        '<path d="M5 7v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7"/>'
        '<path d="M10 12h4"/>',
        size=size,
    )


def chat(size: int = 20) -> str:
    return _svg(
        '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
        size=size,
    )


def book(size: int = 20) -> str:
    return _svg(
        '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>'
        '<path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>',
        size=size,
    )


def target(size: int = 20) -> str:
    return _svg(
        '<circle cx="12" cy="12" r="10"/>'
        '<circle cx="12" cy="12" r="6"/>'
        '<circle cx="12" cy="12" r="2"/>',
        size=size,
    )


def mic(size: int = 20) -> str:
    return _svg(
        '<rect x="9" y="2" width="6" height="12" rx="3"/>'
        '<path d="M5 10v2a7 7 0 0 0 14 0v-2"/>'
        '<line x1="12" y1="19" x2="12" y2="22"/>',
        size=size,
    )


def arrow_right(size: int = 16) -> str:
    return _svg(
        '<line x1="5" y1="12" x2="19" y2="12"/>'
        '<polyline points="12 5 19 12 12 19"/>',
        size=size,
    )


def globe(size: int = 20) -> str:
    return _svg(
        '<circle cx="12" cy="12" r="10"/>'
        '<line x1="2" y1="12" x2="22" y2="12"/>'
        '<path d="M12 2a15 15 0 0 1 4 10 15 15 0 0 1-4 10 15 15 0 0 1-4-10 15 15 0 0 1 4-10z"/>',
        size=size,
    )


def calendar(size: int = 20) -> str:
    return _svg(
        '<rect x="3" y="4" width="18" height="18" rx="2"/>'
        '<line x1="16" y1="2" x2="16" y2="6"/>'
        '<line x1="8" y1="2" x2="8" y2="6"/>'
        '<line x1="3" y1="10" x2="21" y2="10"/>',
        size=size,
    )


def users(size: int = 20) -> str:
    return _svg(
        '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>'
        '<circle cx="9" cy="7" r="4"/>'
        '<path d="M23 21v-2a4 4 0 0 0-3-3.87"/>'
        '<path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
        size=size,
    )


# Refined wordmark logo: bold monogram "Q·M" with red dot and stacked tricolor underline
_QMUN_LOGO_SVG = '''<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 40 40" fill="none"><rect x="3" y="3" width="34" height="34" rx="7" fill="#0F1B2E" stroke="#243854" stroke-width="1"/><text x="20" y="23" font-family="Inter Tight, sans-serif" font-weight="800" font-size="14" fill="#F2F2F0" text-anchor="middle" letter-spacing="-0.5">QM</text><rect x="9" y="29" width="7" height="2" fill="#9D1939"/><rect x="16.5" y="29" width="7" height="2" fill="#B89D5E"/><rect x="24" y="29" width="7" height="2" fill="#4B7BBF"/></svg>'''


def qmun_logo(*, size: int = 32) -> str:
    """Returns the QM logo as a base64 data-uri <img> tag (safe in any markdown context)."""
    b64 = base64.b64encode(_QMUN_LOGO_SVG.encode()).decode()
    return (
        f'<img src="data:image/svg+xml;base64,{b64}" width="{size}" height="{size}" '
        f'style="display:inline-block;vertical-align:middle;border:none;" alt="Queen\'s MUN"/>'
    )


# Editorial hero: stylized assembly seating arc with chamber backdrop. Diplomatic, not scientific.
HERO_SVG = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 380" width="100%" height="100%" preserveAspectRatio="xMidYMid meet" style="display:block;"><defs><linearGradient id="bgFade" x1="0%" y1="0%" x2="0%" y2="100%"><stop offset="0%" stop-color="#0F1C32" stop-opacity="0.6"/><stop offset="100%" stop-color="#060E1A" stop-opacity="0"/></linearGradient><linearGradient id="podiumGrad" x1="0%" y1="0%" x2="0%" y2="100%"><stop offset="0%" stop-color="#243854"/><stop offset="100%" stop-color="#15243B"/></linearGradient></defs><rect width="600" height="380" fill="url(#bgFade)"/><g transform="translate(300 230)"><path d="M -240 0 A 240 240 0 0 1 240 0" fill="none" stroke="#243854" stroke-width="1.2"/><path d="M -195 0 A 195 195 0 0 1 195 0" fill="none" stroke="#1F314B" stroke-width="1"/><path d="M -150 0 A 150 150 0 0 1 150 0" fill="none" stroke="#1A2A40" stroke-width="0.9"/><path d="M -105 0 A 105 105 0 0 1 105 0" fill="none" stroke="#162335" stroke-width="0.8"/><g fill="#3A5377"><circle cx="-220" cy="-22" r="3.5"/><circle cx="-180" cy="-50" r="3.5"/><circle cx="-130" cy="-72" r="3.5"/><circle cx="-75" cy="-86" r="3.5"/><circle cx="-15" cy="-92" r="3.5"/><circle cx="45" cy="-89" r="3.5"/><circle cx="105" cy="-78" r="3.5"/><circle cx="155" cy="-58" r="3.5"/><circle cx="200" cy="-30" r="3.5"/></g><g fill="#3A5377"><circle cx="-180" cy="-12" r="3"/><circle cx="-145" cy="-38" r="3"/><circle cx="-100" cy="-58" r="3"/><circle cx="-50" cy="-70" r="3"/><circle cx="0" cy="-74" r="3"/><circle cx="50" cy="-72" r="3"/><circle cx="100" cy="-62" r="3"/><circle cx="145" cy="-44" r="3"/><circle cx="180" cy="-18" r="3"/></g><g><circle cx="-95" cy="-20" r="4" fill="#9D1939"/><circle cx="-30" cy="-30" r="4" fill="#B89D5E"/><circle cx="40" cy="-28" r="4" fill="#4B7BBF"/></g><rect x="-50" y="0" width="100" height="22" rx="3" fill="url(#podiumGrad)" stroke="#2D4467" stroke-width="0.8"/><rect x="-3" y="-16" width="6" height="16" fill="#7C8FA8"/><rect x="-7" y="-22" width="14" height="8" fill="#9D1939"/></g><g opacity="0.4"><line x1="80" y1="80" x2="80" y2="40" stroke="#5A6A7E" stroke-width="0.7"/><rect x="80" y="40" width="16" height="11" fill="#9D1939"/><line x1="520" y1="100" x2="520" y2="60" stroke="#5A6A7E" stroke-width="0.7"/><rect x="520" y="60" width="16" height="11" fill="#4B7BBF"/><line x1="40" y1="200" x2="40" y2="160" stroke="#5A6A7E" stroke-width="0.7"/><rect x="40" y="160" width="16" height="11" fill="#B89D5E"/></g></svg>'''


def hero_illustration() -> str:
    """Hero SVG wrapped in a self-contained HTML doc for st.components.v1.html iframe."""
    return f'''<!DOCTYPE html><html><head><style>html,body{{margin:0;padding:0;background:transparent;overflow:hidden;}}</style></head><body>{HERO_SVG}</body></html>'''


def tricolor_bar(*, height: int = 3) -> str:
    """Thin tricolor bar (red, gold, blue) for visual accent."""
    return f'''
<div style="display:flex; height:{height}px; border-radius:2px; overflow:hidden; margin: 0;">
  <div style="flex:1; background:#9D1939;"></div>
  <div style="flex:1; background:#B89D5E;"></div>
  <div style="flex:1; background:#1B3A6B;"></div>
</div>
'''
