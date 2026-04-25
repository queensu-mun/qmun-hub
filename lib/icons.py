"""Inline SVG icons (Lucide-style, single-stroke). Returns HTML strings."""
from __future__ import annotations


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


# QMUN logo: tricolor monogram
def qmun_logo(*, size: int = 32) -> str:
    """Custom Queen's MUN monogram. A 'Q' with tricolor inset bars."""
    return f'''
<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 40 40" fill="none">
  <circle cx="20" cy="20" r="17" stroke="#F2F2F0" stroke-width="2.5"/>
  <line x1="27" y1="27" x2="34" y2="34" stroke="#F2F2F0" stroke-width="2.5" stroke-linecap="round"/>
  <rect x="13" y="13" width="14" height="2.2" fill="#9D1939"/>
  <rect x="13" y="18.4" width="14" height="2.2" fill="#B89D5E"/>
  <rect x="13" y="23.8" width="14" height="2.2" fill="#1B3A6B"/>
</svg>
'''


HERO_SVG = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 360" width="100%" height="100%" preserveAspectRatio="xMidYMid meet" style="display:block;"><defs><radialGradient id="bgGlow" cx="50%" cy="50%" r="60%"><stop offset="0%" stop-color="#9D1939" stop-opacity="0.15"/><stop offset="100%" stop-color="#0A0A0B" stop-opacity="0"/></radialGradient><linearGradient id="globeGrad" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#1F2028"/><stop offset="100%" stop-color="#13131A"/></linearGradient></defs><rect width="600" height="360" fill="url(#bgGlow)"/><g transform="translate(300 180)"><circle r="115" fill="url(#globeGrad)" stroke="#2A2B35" stroke-width="1.5"/><ellipse rx="115" ry="38" fill="none" stroke="#2A2B35" stroke-width="0.8"/><ellipse rx="115" ry="76" fill="none" stroke="#2A2B35" stroke-width="0.8"/><ellipse rx="115" ry="100" fill="none" stroke="#2A2B35" stroke-width="0.6" opacity="0.6"/><ellipse rx="38" ry="115" fill="none" stroke="#2A2B35" stroke-width="0.8"/><ellipse rx="76" ry="115" fill="none" stroke="#2A2B35" stroke-width="0.8"/><ellipse rx="100" ry="115" fill="none" stroke="#2A2B35" stroke-width="0.6" opacity="0.6"/><path d="M -90 -40 Q 0 -130 90 -40" fill="none" stroke="#9D1939" stroke-width="1.4" opacity="0.9"/><path d="M -100 30 Q 20 -90 100 -10" fill="none" stroke="#B89D5E" stroke-width="1.2" opacity="0.75"/><path d="M -70 60 Q 30 130 95 30" fill="none" stroke="#1B3A6B" stroke-width="1.4" opacity="0.9"/><circle cx="-90" cy="-40" r="4" fill="#9D1939"/><circle cx="90" cy="-40" r="4" fill="#9D1939"/><circle cx="-100" cy="30" r="3" fill="#B89D5E"/><circle cx="100" cy="-10" r="3" fill="#B89D5E"/><circle cx="-70" cy="60" r="4" fill="#1B3A6B"/><circle cx="95" cy="30" r="4" fill="#1B3A6B"/><circle r="2" fill="#F2F2F0" opacity="0.3"/></g><g opacity="0.55"><line x1="50" y1="80" x2="50" y2="50" stroke="#7C7C85" stroke-width="0.8"/><rect x="50" y="50" width="14" height="9" fill="#9D1939"/><line x1="540" y1="100" x2="540" y2="70" stroke="#7C7C85" stroke-width="0.8"/><rect x="540" y="70" width="14" height="9" fill="#1B3A6B"/><line x1="80" y1="290" x2="80" y2="260" stroke="#7C7C85" stroke-width="0.8"/><rect x="80" y="260" width="14" height="9" fill="#B89D5E"/></g></svg>'''


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
