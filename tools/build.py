"""Gera os SVGs do README do perfil (ASCII + glitch, organizado).

Uso (da raiz do repositório, com fonttools instalado e o ImageMagick no PATH):
    python tools/build.py tools/fonts tools/hand.png assets api
Cada SVG embute só os glifos que usa (subset WOFF em base64), porque o GitHub
mostra SVG como <img> e aí fonte externa não carrega.
"""
import base64
import io
import math
import subprocess
import sys
from pathlib import Path
from xml.sax.saxutils import escape

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

FONTS_DIR, HAND, OUT, API = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4])
OUT.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------ tokens
BG, PANEL, PANEL2 = '#0b0b0d', '#0f0f12', '#141418'
LINE, LINE2 = '#24242b', '#2f2f37'
TEXT, MUTED, DIM = '#c4c4cb', '#86868f', '#55555e'
INDIGO, PURPLE, MAGENTA, ORANGE, WHITE = '#2b1b8f', '#7b1fa2', '#d0268f', '#f4a259', '#ffffff'
LIGHT_TEXT = '#1b1b20'

FONTS = {
    'light': ('Outfit.ttf', 300),
    'regular': ('Outfit.ttf', 400),
    'mono': ('CaskaydiaMono-subset.ttf', None),
}
_font_cache: dict = {}
_used: dict = {}


def T(font: str, s: str) -> str:
    """Registra os caracteres usados por fonte e devolve o texto escapado."""
    _used.setdefault(font, set()).update(s)
    return escape(s)


def font_face(key: str) -> str:
    file, wght = FONTS[key]
    if (file, wght) not in _font_cache:
        f = TTFont(FONTS_DIR / file)
        if wght is not None and 'fvar' in f:
            f = instancer.instantiateVariableFont(f, {'wght': wght})
        _font_cache[(file, wght)] = f
    buf = io.BytesIO()
    f = _font_cache[(file, wght)]
    tmp = io.BytesIO()
    f.save(tmp)
    tmp.seek(0)
    sub = TTFont(tmp)
    opts = subset.Options()
    opts.flavor = 'woff'
    opts.layout_features = ['kern', 'liga', 'calt']
    opts.notdef_outline = True
    s = subset.Subsetter(opts)
    s.populate(text=''.join(sorted(_used[key])) + ' ')
    s.subset(sub)
    sub.flavor = 'woff'
    sub.save(buf)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"@font-face{{font-family:'{key}';src:url(data:font/woff;base64,{b64}) format('woff');}}"


def svg(w: int, h: int, body: str, extra_css: str = '', defs: str = '', label: str = '') -> str:
    faces = ''.join(font_face(k) for k in sorted(_used))
    css = (
        faces
        + ".light{font-family:'light'}.regular{font-family:'regular'}.mono{font-family:'mono'}"
        + extra_css
    )
    _used.clear()
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{escape(label)}">'
        f'<defs><style>{css}</style>{defs}</defs>{body}</svg>'
    )


def write(name: str, content: str) -> None:
    (OUT / name).write_text(content, encoding='utf-8')
    print(f'{name}: {len(content) / 1024:.0f} KB')


# ------------------------------------------------------------------ peças
def brush_gradient(gid: str, x1: float, x2: float, end: str = WHITE) -> str:
    return (
        f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="{x1}" y1="0" x2="{x2}" y2="0">'
        f'<stop offset="0" stop-color="{INDIGO}"/><stop offset=".3" stop-color="{PURPLE}"/>'
        f'<stop offset=".55" stop-color="{MAGENTA}"/><stop offset=".82" stop-color="{ORANGE}"/>'
        f'<stop offset="1" stop-color="{end}"/></linearGradient>'
    )


def brush(x: float, y: float, w: float, gid: str, width: float = 6) -> str:
    """Pincelada: um rabisco curto no começo e uma varrida longa que termina branca."""
    d = (
        f'M{x},{y + 3} c5,-7 11,6 17,0 s11,-6 17,0 '
        f'C{x + w * 0.3},{y - 1} {x + w * 0.62},{y + 7} {x + w},{y - 5}'
    )
    return (
        f'<path class="brush" d="{d}" pathLength="1" fill="none" stroke="url(#{gid})" '
        f'stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"/>'
    )


BRUSH_CSS = (
    '@media (prefers-reduced-motion:no-preference){'
    '.brush{stroke-dasharray:1;stroke-dashoffset:1;animation:draw 1.4s .3s cubic-bezier(.6,0,.2,1) forwards}'
    '@keyframes draw{to{stroke-dashoffset:0}}}'
)


_metrics: dict = {}


def text_width(s: str, size: float, font: str, ls: float = 0) -> float:
    """Largura do texto pelas métricas da fonte (avanço dos glifos, sem kerning)."""
    if font not in _metrics:
        file, wght = FONTS[font]
        f = TTFont(FONTS_DIR / file)
        if wght is not None and 'fvar' in f:
            f = instancer.instantiateVariableFont(f, {'wght': wght})
        _metrics[font] = (f.getBestCmap(), f['hmtx'].metrics, f['head'].unitsPerEm)
    cmap, hmtx, upm = _metrics[font]
    units = sum(hmtx[cmap[ord(c)]][0] for c in s if ord(c) in cmap)
    return units / upm * size + ls * len(s)


def wrap(s: str, size: float, max_w: float, font: str = 'regular') -> list[str]:
    lines, cur = [], ''
    for word in s.split():
        test = f'{cur} {word}'.strip()
        if text_width(test, size, font) > max_w and cur:
            lines.append(cur)
            cur = word
        else:
            cur = test
    if cur:
        lines.append(cur)
    return lines


def chips(x: float, y: float, labels: list[str], size: float = 10.5, gap: float = 6, h: float = 20) -> str:
    out = []
    for label in labels:
        w = text_width(label, size, 'mono') + 16
        out.append(
            f'<rect x="{x}" y="{y}" width="{w:.1f}" height="{h}" rx="{h / 2}" fill="none" stroke="{LINE2}"/>'
            f'<text class="mono" x="{x + w / 2:.1f}" y="{y + h / 2 + size * 0.36:.1f}" font-size="{size}" fill="{MUTED}" text-anchor="middle">{T("mono", label)}</text>'
        )
        x += w + gap
    return ''.join(out)


def arrow(x: float, y: float, size: float = 9, color: str = MUTED) -> str:
    """Seta ↗ desenhada (não depende de glifo da fonte)."""
    return (
        f'<path d="M{x},{y + size} L{x + size},{y} M{x + size * 0.3},{y} H{x + size} V{y + size * 0.7}" '
        f'fill="none" stroke="{color}" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>'
    )


# ------------------------------------------------------------------ hero
def ascii_hand(cols: int = 96) -> list[str]:
    """Mão do Figma convertida em ASCII: brilho do pixel vira densidade do caractere."""
    w, h = 300, 145
    rows = round(cols * h / w * 0.5)
    raw = subprocess.run(['magick', str(HAND), '-level', '6%,62%', '-resize', f'{cols}x{rows}!', '-depth', '8', 'gray:-'], capture_output=True, check=True).stdout
    ramp = ' .:-=+*#%@'
    lines = []
    for r in range(rows):
        line = ''
        for c in range(cols):
            v = max(0.0, (raw[r * cols + c] / 255 - 0.04) / 0.96) ** 0.8
            line += ramp[min(len(ramp) - 1, int(v * len(ramp)))]
        lines.append(line.rstrip())
    return lines


GLITCH_CSS = (
    '@media (prefers-reduced-motion:no-preference){'
    '.gA{animation:gA 7s steps(1) infinite}.gB{animation:gB 7s steps(1) infinite}'
    '@keyframes gA{0%,88%,100%{transform:translate(-1.5px,0)}89%{transform:translate(-6px,2px)}91%{transform:translate(4px,-1px)}93%{transform:translate(-1.5px,0)}}'
    '@keyframes gB{0%,88%,100%{transform:translate(1.5px,0)}89%{transform:translate(6px,-2px)}91%{transform:translate(-3px,1px)}93%{transform:translate(1.5px,0)}}'
    '.cursor{animation:blink 1.1s steps(1) infinite}@keyframes blink{50%{opacity:0}}}'
)


def glitch_text(x: float, y: float, text: str, size: float, font: str, color: str, ls: float = 0) -> str:
    """Texto com aberração cromática (cópias índigo e magenta deslocadas) que dá um tranco de vez em quando."""
    t = T(font, text)
    common = f'x="{x}" y="{y}" font-size="{size}" letter-spacing="{ls}"'
    return (
        f'<text {common} fill="{MAGENTA}" opacity=".55" class="{font} gA">{t}</text>'
        f'<text {common} fill="{INDIGO}" opacity=".7" class="{font} gB">{t}</text>'
        f'<text class="{font}" {common} fill="{color}">{t}</text>'
    )


def hero() -> str:
    W, H = 1000, 300
    b = [f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="16" fill="{BG}" stroke="{LINE}"/>']
    # mão em ASCII apontando pro nome
    lines = ascii_hand()
    fs, lh = 6.2, 7.4
    hx, hy = 548, 70
    spans = ''.join(f'<tspan x="{hx}" dy="{0 if k == 0 else lh}">{T("mono", ln)}</tspan>' for k, ln in enumerate(lines))
    b.append(f'<text class="mono" x="{hx}" y="{hy}" font-size="{fs}" fill="url(#handGrad)" xml:space="preserve">{spans}</text>')
    b.append(f'<rect x="{hx}" y="{hy - 10}" width="{W - hx}" height="{len(lines) * lh + 20}" fill="url(#handFade)"/>')
    # prompt
    prompt = 'valb@arch:~$ whoami'
    b.append(f'<text class="mono" x="44" y="56" font-size="12" fill="{DIM}">{T("mono", "valb")}<tspan fill="{MAGENTA}">{T("mono", "@")}</tspan>{T("mono", "arch:~$ whoami")}</text>')
    b.append(f'<rect class="cursor" x="{44 + text_width(prompt, 12, "mono") + 6:.1f}" y="46" width="7" height="13" fill="{ORANGE}"/>')
    # nome com glitch e pincelada
    name_w = text_width('Ivalber Souza', 64, 'light', -0.5)
    b.append(glitch_text(40, 132, 'Ivalber Souza', 64, 'light', TEXT, -0.5))
    b.append(brush(28, 156, name_w + 46, 'brushHero', 7))
    # papel e descrição
    b.append(f'<text class="regular" x="44" y="206" font-size="20" fill="{TEXT}">{T("regular", "Backend Developer")}</text>')
    parts = [('4+ years', ORANGE), (' building robust systems with ', MUTED), ('PHP', ORANGE), (', ', MUTED), ('DDD', ORANGE), (' and solid engineering practices.', MUTED)]
    spans = ''.join(f'<tspan fill="{c}">{T("regular", s)}</tspan>' for s, c in parts)
    b.append(f'<text class="regular" x="44" y="232" font-size="14" xml:space="preserve">{spans}</text>')
    now = [('now building ', DIM), ('kronofit', ORANGE), (', an ecosystem for personal trainers', DIM)]
    spans = ''.join(f'<tspan fill="{c}">{T("mono", s)}</tspan>' for s, c in now)
    b.append(f'<text class="mono" x="44" y="268" font-size="11" xml:space="preserve"><tspan fill="{MAGENTA}">{T("mono", "▸ ")}</tspan>{spans}</text>')
    defs = (
        f'<linearGradient id="handGrad" gradientUnits="userSpaceOnUse" x1="{hx}" y1="0" x2="{W}" y2="0"><stop offset="0" stop-color="{WHITE}"/><stop offset=".25" stop-color="{ORANGE}"/><stop offset=".55" stop-color="{MAGENTA}"/><stop offset="1" stop-color="{PURPLE}"/></linearGradient>'
        f'<linearGradient id="handFade" gradientUnits="userSpaceOnUse" x1="{W - 150}" y1="0" x2="{W - 4}" y2="0"><stop offset="0" stop-color="{BG}" stop-opacity="0"/><stop offset="1" stop-color="{BG}"/></linearGradient>'
        + brush_gradient('brushHero', 28, 28 + name_w + 46)
    )
    return svg(W, H, ''.join(b), BRUSH_CSS + GLITCH_CSS, defs, 'Ivalber Souza, Backend Developer. 4+ years building robust systems with PHP, DDD and solid engineering practices. Now building kronofit.')


# ------------------------------------------------------------------ títulos
def title(num: str, text: str, theme: str) -> str:
    W, H = 1000, 100
    color = TEXT if theme == 'dark' else LIGHT_TEXT
    size = 40
    x = 24
    prefix = f'{num} //'
    b = [f'<text class="mono" x="{x}" y="56" font-size="14" fill="{MAGENTA}">{T("mono", prefix)}</text>']
    tx = x + text_width(prefix, 14, 'mono') + 14
    tw = text_width(text, size, 'light', -0.3)
    b.append(f'<text class="light" x="{tx:.1f}" y="58" font-size="{size}" fill="{color}" letter-spacing="-.3">{T("light", text)}</text>')
    bw = tw + 30
    b.append(brush(tx - 10, 78, bw, 'brushT', 5))
    end = WHITE if theme == 'dark' else ORANGE
    return svg(W, H, ''.join(b), BRUSH_CSS, brush_gradient('brushT', tx - 10, tx - 10 + bw, end), text)


# ------------------------------------------------------------------ cards de projeto
def motif(kind: str, x: float, y: float, w: float, h: float) -> str:
    cx, cy = x + w / 2, y + h / 2
    out = []
    if kind == 'd20':
        R = min(w, h) * 0.42
        hexa = [(cx + R * math.cos(math.radians(-90 + 60 * k)), cy + R * math.sin(math.radians(-90 + 60 * k))) for k in range(6)]
        inner = [(cx + R * 0.52 * math.cos(math.radians(a)), cy + R * 0.52 * math.sin(math.radians(a))) for a in (-90, 30, 150)]
        pts = lambda ps: ' '.join(f'{px:.1f},{py:.1f}' for px, py in ps)
        out.append(f'<polygon points="{pts(hexa)}" fill="url(#fillSoft)" stroke="url(#grad)" stroke-width="1.6" stroke-linejoin="round"/>')
        out.append(f'<polygon points="{pts(inner)}" fill="none" stroke="url(#grad)" stroke-width="1.6" stroke-linejoin="round"/>')
        links = {0: (5, 0, 1), 1: (1, 2, 3), 2: (3, 4, 5)}
        for i, hs in links.items():
            for hidx in hs:
                out.append(f'<line x1="{inner[i][0]:.1f}" y1="{inner[i][1]:.1f}" x2="{hexa[hidx][0]:.1f}" y2="{hexa[hidx][1]:.1f}" stroke="url(#grad)" stroke-width="1.2" opacity=".85"/>')
        out.append(f'<text class="mono" x="{cx:.1f}" y="{cy + 7:.1f}" font-size="18" fill="{WHITE}" text-anchor="middle">{T("mono", "20")}</text>')
    elif kind == 'ports':
        for i, (port, dot) in enumerate([(':8080', ORANGE), (':3000', MAGENTA), (':5432', PURPLE)]):
            yy = y + 28 + i * 33
            out.append(f'<text class="mono" x="{x + 2}" y="{yy}" font-size="25" fill="url(#grad)" opacity="{1 - i * 0.22:.2f}">{T("mono", port)}</text>')
            out.append(f'<circle cx="{x + w - 10}" cy="{yy - 8}" r="3.5" fill="{dot}"/>')
    elif kind == 'phone':
        pw, ph = 76, h - 6
        px = cx - pw / 2
        out.append(f'<rect x="{px}" y="{y}" width="{pw}" height="{ph}" rx="12" fill="{PANEL2}" stroke="url(#grad)" stroke-width="1.6"/>')
        out.append(f'<rect x="{cx - 10}" y="{y + 6}" width="20" height="4" rx="2" fill="{LINE2}"/>')
        rows = [('> ', 30, MUTED), ('', 46, DIM), ('', 38, DIM), ('> ', 24, MAGENTA), ('', 50, DIM)]
        for i, (pfx, lw, c) in enumerate(rows):
            yy = y + 22 + i * 13
            if pfx:
                out.append(f'<text class="mono" x="{px + 9}" y="{yy + 3}" font-size="8" fill="{c}">{T("mono", pfx.strip())}</text>')
            out.append(f'<rect x="{px + (17 if pfx else 9)}" y="{yy - 2}" width="{lw}" height="4" rx="2" fill="{c}" opacity=".8"/>')
    elif kind == 'fps':
        R = min(w, h) * 0.36
        base = y + h - 8
        ridge = [(x, base), (x + w * 0.18, base - h * 0.35), (x + w * 0.32, base - h * 0.2), (x + w * 0.5, base - h * 0.62), (x + w * 0.68, base - h * 0.28), (x + w * 0.84, base - h * 0.45), (x + w, base)]
        pts = ' '.join(f'{a:.1f},{b2:.1f}' for a, b2 in ridge)
        out.append(f'<polyline points="{pts}" fill="url(#fillSoft)" stroke="url(#grad)" stroke-width="1.6" stroke-linejoin="round"/>')
        for i in range(1, len(ridge) - 1):
            out.append(f'<line x1="{ridge[i][0]:.1f}" y1="{ridge[i][1]:.1f}" x2="{ridge[i][0] + (w * 0.08 if i % 2 else -w * 0.08):.1f}" y2="{base}" stroke="url(#grad)" stroke-width="1" opacity=".55"/>')
        ccx, ccy = x + w * 0.5, y + h * 0.3
        out.append(f'<circle cx="{ccx}" cy="{ccy}" r="{R * 0.42:.1f}" fill="none" stroke="{WHITE}" stroke-width="1.4" opacity=".9"/>')
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            out.append(f'<line x1="{ccx + dx * R * 0.22:.1f}" y1="{ccy + dy * R * 0.22:.1f}" x2="{ccx + dx * R * 0.62:.1f}" y2="{ccy + dy * R * 0.62:.1f}" stroke="{WHITE}" stroke-width="1.4" opacity=".9"/>')
        out.append(f'<circle cx="{ccx}" cy="{ccy}" r="1.8" fill="{ORANGE}"/>')
        out.append(f'<text class="mono" x="{x + w - 4}" y="{y + 12}" font-size="11" fill="{DIM}" text-anchor="end">{T("mono", "1945")}</text>')
    elif kind == 'graph':
        nodes = [('Order::pay()', 0.5, 0.06), ('if approved', 0.5, 0.36), ('Invoice::issue()', 0.24, 0.7), ('Mailer::retry()', 0.78, 0.7)]
        pos = []
        for label, fx, fy in nodes:
            nw = text_width(label, 8.5, 'mono') + 12
            nx, ny = x + w * fx - nw / 2, y + h * fy
            pos.append((nx + nw / 2, ny, ny + 20))
            out.append(f'<rect x="{nx:.1f}" y="{ny:.1f}" width="{nw:.1f}" height="20" rx="5" fill="{PANEL2}" stroke="{LINE2}"/>')
            out.append(f'<text class="mono" x="{nx + nw / 2:.1f}" y="{ny + 13.5:.1f}" font-size="8.5" fill="{TEXT}" text-anchor="middle">{T("mono", label)}</text>')
        for a, bb, dashed in ((0, 1, False), (1, 2, False), (1, 3, True)):
            x1, _, y1 = pos[a]
            x2, y2, _ = pos[bb]
            out.append(f'<path d="M{x1:.1f},{y1:.1f} C{x1:.1f},{(y1 + y2) / 2:.1f} {x2:.1f},{(y1 + y2) / 2:.1f} {x2:.1f},{y2 - 2:.1f}" fill="none" stroke="url(#grad)" stroke-width="1.5" {"stroke-dasharray=\"4 3\"" if dashed else ""} marker-end="url(#arrowhead)"/>')
        out.append(f'<text class="mono" x="{pos[1][0] + 34:.1f}" y="{pos[1][2] + 18:.1f}" font-size="8.5" fill="{DIM}">{T("mono", "else")}</text>')
    elif kind == 'swap':
        boxes = [('barbell bench press', 0.0, 0.04), ('dumbbell press', 0.0, 0.46), ('push-up', 0.62, 0.86)]
        pos = []
        for label, fx, fy in boxes:
            nw = text_width(label, 9, 'mono') + 16
            nx, ny = x + w * fx, y + h * fy
            hot = label == 'dumbbell press'
            pos.append((nx, ny, nw))
            out.append(f'<rect x="{nx:.1f}" y="{ny:.1f}" width="{nw:.1f}" height="22" rx="5" fill="{PANEL2}" stroke="{"url(#grad)" if hot else LINE2}" stroke-width="{1.4 if hot else 1}"/>')
            out.append(f'<text class="mono" x="{nx + 8:.1f}" y="{ny + 14.5:.1f}" font-size="9" fill="{WHITE if hot else TEXT}">{T("mono", label)}</text>')
        (x0, y0, w0), (x1, y1, w1), (x2, y2, w2) = pos
        out.append(f'<path d="M{x0 + 24:.1f},{y0 + 22:.1f} V{y1 - 3:.1f}" stroke="url(#grad)" stroke-width="1.5" marker-end="url(#arrowhead)"/>')
        out.append(f'<text class="mono" x="{x0 + 32:.1f}" y="{(y0 + y1) / 2 + 14:.1f}" font-size="8.5" fill="{DIM}">{T("mono", "no barbell")}</text>')
        out.append(f'<path d="M{x1 + w1:.1f},{y1 + 11:.1f} H{x2 + w2 / 2:.1f} V{y2 - 3:.1f}" fill="none" stroke="url(#grad)" stroke-width="1.5" stroke-dasharray="4 3" marker-end="url(#arrowhead)"/>')
        out.append(f'<text class="mono" x="{x1 + w1 + 8:.1f}" y="{y1 + 4:.1f}" font-size="8.5" fill="{DIM}">{T("mono", "no bench")}</text>')
        out.append(f'<text class="mono" x="{x + w:.1f}" y="{y + 10:.1f}" font-size="8.5" fill="{DIM}" text-anchor="end">{T("mono", "gym-api")}</text>')
    elif kind == 'grid':
        rows, cell, gap = 7, 11, 3
        cols = int((w + gap) // (cell + gap))
        gx = cx - (cols * (cell + gap) - gap) / 2
        gy = cy - (rows * (cell + gap) - gap) / 2
        palette = [PANEL2, INDIGO, PURPLE, MAGENTA, ORANGE]
        seed = 11
        for c in range(cols):
            for r in range(rows):
                seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
                trend = c / cols
                v = (seed % 100) / 100 * 0.7 + trend * 0.45
                lvl = 0 if v < 0.35 else 1 if v < 0.55 else 2 if v < 0.72 else 3 if v < 0.9 else 4
                out.append(f'<rect x="{gx + c * (cell + gap):.1f}" y="{gy + r * (cell + gap):.1f}" width="{cell}" height="{cell}" rx="2.5" fill="{palette[lvl]}"/>')
    return ''.join(out)


def card(slug: str, w: int, name: str, desc: str, stack: list[str], kind: str, meta: str = '') -> str:
    H = 300
    b = [f'<rect x=".5" y=".5" width="{w - 1}" height="{H - 1}" rx="14" fill="{PANEL}" stroke="{LINE}"/>']
    b.append(f'<path d="M.5,30 H{w - .5}" stroke="{LINE}"/>')
    for i, c in enumerate((INDIGO, MAGENTA, ORANGE)):
        b.append(f'<circle cx="{18 + i * 14}" cy="15.5" r="4.2" fill="{c}"/>')
    b.append(f'<text class="mono" x="{w / 2}" y="19.5" font-size="10.5" fill="{DIM}" text-anchor="middle">{T("mono", "~/" + slug)}</text>')
    b.append(arrow(w - 26, 11, 8, DIM))
    if w >= 600:
        tx, tw = 26, w * 0.5
        mx, my, mw, mh = w * 0.58, 52, w * 0.36, 196
        name_y = 84
    elif w >= 450:
        tx, tw = 26, w * 0.44
        mx, my, mw, mh = w * 0.52, 58, w * 0.44, 170
        name_y = 84
    else:
        tx, tw = 24, w - 48
        mx, my, mw, mh = 24, 46, w - 48, 104
        name_y = 182
    b.append(motif(kind, mx, my, mw, mh))
    b.append(f'<text class="light" x="{tx}" y="{name_y}" font-size="26" fill="{TEXT}">{T("light", name)}</text>')
    lines = wrap(desc, 13, tw)
    for j, line in enumerate(lines[:4]):
        b.append(f'<text class="regular" x="{tx}" y="{name_y + 26 + j * 19}" font-size="13" fill="{MUTED}">{T("regular", line)}</text>')
    if meta:
        b.append(f'<text class="mono" x="{tx}" y="{H - 52}" font-size="10" fill="{DIM}">{T("mono", meta)}</text>')
    b.append(chips(tx, H - 38, stack))
    defs = (
        f'<linearGradient id="grad" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{PURPLE}"/><stop offset=".5" stop-color="{MAGENTA}"/><stop offset="1" stop-color="{ORANGE}"/></linearGradient>'
        f'<linearGradient id="fillSoft" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{MAGENTA}" stop-opacity=".16"/><stop offset="1" stop-color="{INDIGO}" stop-opacity="0"/></linearGradient>'
        f'<marker id="arrowhead" viewBox="0 0 8 8" refX="6" refY="4" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L8,4 L0,8z" fill="{ORANGE}"/></marker>'
    )
    return svg(w, H, ''.join(b), '', defs, f'{name}: {desc}')


# ------------------------------------------------------------------ botões e rodapé
def button(label: str, icon: str) -> str:
    size = 13
    w = int(text_width(label, size, 'mono') + 56)
    H = 40
    b = [f'<rect x=".5" y=".5" width="{w - 1}" height="{H - 1}" rx="20" fill="{PANEL}" stroke="{LINE2}"/>']
    b.append(f'<text class="mono" x="20" y="25" font-size="{size}" fill="{TEXT}">{T("mono", label)}</text>')
    ix = w - 30
    if icon == 'mail':
        b.append(f'<rect x="{ix}" y="14" width="14" height="11" rx="2" fill="none" stroke="url(#bg)" stroke-width="1.5"/><path d="M{ix + 1},15.5 l6,4.5 6,-4.5" fill="none" stroke="url(#bg)" stroke-width="1.5" stroke-linejoin="round"/>')
    else:
        b.append(f'<path d="M{ix + 2},{27} L{ix + 12},{15} M{ix + 5},15 H{ix + 12} V{22}" fill="none" stroke="url(#bg)" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>')
    defs = f'<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{MAGENTA}"/><stop offset="1" stop-color="{ORANGE}"/></linearGradient>'
    return svg(w, H, ''.join(b), '', defs, label)


def footer(theme: str) -> str:
    W, H = 1000, 60
    color = DIM if theme == 'dark' else '#8a8a93'
    line = 'valb@arch:~$ exit'
    x = (W - text_width(line, 12, 'mono')) / 2
    b = [f'<text class="mono" x="{x:.1f}" y="34" font-size="12" fill="{color}">{T("mono", "valb")}<tspan fill="{MAGENTA}">{T("mono", "@")}</tspan>{T("mono", "arch:~$ exit")}</text>']
    b.append(f'<rect class="cursor" x="{x + text_width(line, 12, "mono") + 6:.1f}" y="24" width="7" height="13" fill="{ORANGE}"/>')
    return svg(W, H, ''.join(b), GLITCH_CSS, '', 'valb@arch:~$ exit')


def font_module() -> str:
    """Cascadia cortada pros caracteres do painel neofetch, pra API na Vercel embutir no SVG."""
    chars = ''.join(chr(c) for c in range(0x20, 0x7F)) + 'áéíóúãõçâêôàÁÉÍÓÚÃÕÇ°·★●▸─│╭╮╰╯├┤█░▏'
    _used['mono'] = set(chars)
    face = font_face('mono')
    _used.clear()
    b64 = face.split('base64,', 1)[1].split(')', 1)[0]
    return f'// Gerado por tools/build.py: Caskaydia Mono (OFL) cortada pros caracteres do painel.\nexport const MONO_WOFF = "{b64}";\n'


# ------------------------------------------------------------------ saída
write('hero.svg', hero())
for theme in ('dark', 'light'):
    sfx = '' if theme == 'dark' else '-light'
    write(f'title-setup{sfx}.svg', title('01', 'Setup', theme))
    write(f'title-projects{sfx}.svg', title('02', 'Projects', theme))
    write(f'footer{sfx}.svg', footer(theme))
CARDS = [
    ('ato20', 650, 'ATO20', 'Free virtual tabletop for RPG campaigns over LAN, with VPN support, advanced camera control and a place for the game master to keep the story organized.', ['TypeScript', 'Rust', 'Tauri'], 'd20', '1.1k commits · 30 releases'),
    ('claude.remote', 340, 'claude.remote', 'Drive the Claude Code sessions running on my PC from my phone. A PWA over Tailscale, no cloud in between.', ['TypeScript', 'Fastify', 'PWA'], 'phone'),
    ('app.porto', 340, 'Porto', 'Start page for my machine: what is listening on each port, where it came from and who is connected.', ['TypeScript', 'Docker', 'systemd'], 'ports'),
    ('kronofit', 650, 'Kronofit', 'An ecosystem for personal trainers: student management, a workout API that swaps exercises by the equipment at hand, and an app to build training plans.', ['Laravel', 'Livewire', 'Fastify', 'Postgres'], 'swap', 'in progress · open-foco'),
    ('php.teller', 495, 'Teller', 'Maps the business rules documented in PHP docblocks into a navigable call graph, built from the real AST.', ['PHP', 'php-parser', 'AST'], 'graph'),
    ('app.commitable', 495, 'Commitable', 'Habit tracker with a GitHub-style contribution grid and a native Android home-screen widget.', ['React Native', 'Expo', 'Kotlin'], 'grid'),
]
for slug, w, name, desc, stack, kind, *meta in CARDS:
    write(f'card-{slug}.svg', card(slug, w, name, desc, stack, kind, meta[0] if meta else ''))
for slug, label, icon in [('contact', 'contact me', 'mail'), ('portfolio', 'portfolio', 'arrow'), ('blog', 'blog', 'arrow'), ('linkedin', 'linkedin', 'arrow'), ('instagram', 'instagram', 'arrow')]:
    write(f'btn-{slug}.svg', button(label, icon))
API.mkdir(parents=True, exist_ok=True)
(API / '_font.js').write_text(font_module(), encoding='utf-8')
print('api/_font.js:', round((API / '_font.js').stat().st_size / 1024), 'KB')
