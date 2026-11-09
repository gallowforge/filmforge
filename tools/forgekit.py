"""forgekit: shared helpers for the filmforge tools.

Only numpy, Pillow and PyYAML are needed. Every tool imports this module from its own folder, so the
tools work the same from the repository (tools/) and from an installed skill (scripts/).
"""
import os
import re
import sys

import numpy as np
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)          # repo root, or the installed skill folder


# ---- files -------------------------------------------------------------------------------------------------------------

def die(msg, code=1):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def load_yaml(path):
    if not os.path.exists(path):
        die(f"file not found: {path}")
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if data is not None else {}


def dump_yaml(obj, path):
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(obj, f, sort_keys=False, allow_unicode=True, width=110)


def default_prices():
    """config/prices.yaml next to the tools folder, or $FORGE_PRICES."""
    env = os.environ.get("FORGE_PRICES")
    if env:
        return env
    return os.path.join(ROOT, "config", "prices.yaml")


def natural_key(s):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", str(s))]


IMAGE_EXT = (".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff")


def list_images(folder, pattern=None):
    """Image files in a folder, sorted; an empty list when the folder does not exist yet (nothing painted)."""
    import fnmatch
    out = []
    if not folder or not os.path.isdir(folder):
        return out
    for name in os.listdir(folder):
        if name.startswith("."):
            continue
        if not name.lower().endswith(IMAGE_EXT):
            continue
        if pattern and not fnmatch.fnmatch(name, pattern):
            continue
        out.append(os.path.join(folder, name))
    return sorted(out, key=lambda p: natural_key(os.path.basename(p)))


def find_painting(folder, shot_id, explicit=None):
    """The file that holds a shot's painting. An explicit `painting:` wins; otherwise the newest version whose
    name starts with the shot id (s04_x.png < s04_x_v2.png, natural order)."""
    if explicit:
        p = explicit if os.path.isabs(explicit) else os.path.join(folder, explicit)
        return p if os.path.exists(p) else None
    hits = []
    for p in list_images(folder):
        stem = os.path.splitext(os.path.basename(p))[0]
        if stem == shot_id or re.match(re.escape(shot_id) + r"[_\-. ]", stem):
            hits.append(p)
    return hits[-1] if hits else None


# ---- shot lists --------------------------------------------------------------------------------------------------------

def shots_of(shotlist):
    return shotlist.get("shots") or []


def shot_order(shotlist):
    return {s["id"]: i for i, s in enumerate(shots_of(shotlist)) if isinstance(s, dict) and "id" in s}


def cut_times(shotlist):
    """Cumulative end time of every shot (the cut points), honouring an optional `gap` field."""
    t, out = 0.0, []
    for s in shots_of(shotlist):
        t += float(s.get("gap", 0) or 0)
        t += float(s.get("dur", 0) or 0)
        out.append(t)
    return out


def plural(n, word, many=None):
    return f"{n} {word if n == 1 else (many or word + 's')}"


def fmt_time(s, decimals=1):
    s = max(0.0, float(s))
    m = int(s // 60)
    rest = s - m * 60
    if decimals:
        return f"{m}:{rest:0{3 + decimals}.{decimals}f}"
    return f"{m}:{int(round(rest)):02d}"


def table(rows, header=None, align=None):
    """Plain aligned text table. align: string of 'l'/'r' per column."""
    rows = [[str(c) for c in r] for r in rows]
    if header:
        rows = [list(map(str, header))] + rows
    if not rows:
        return ""
    n = max(len(r) for r in rows)
    rows = [r + [""] * (n - len(r)) for r in rows]
    w = [max(len(r[i]) for r in rows) for i in range(n)]
    align = (align or "l" * n).ljust(n, "l")
    lines = []
    for k, r in enumerate(rows):
        cells = [c.rjust(w[i]) if align[i] == "r" else c.ljust(w[i]) for i, c in enumerate(r)]
        lines.append("  ".join(cells).rstrip())
        if header and k == 0:
            lines.append("  ".join("-" * x for x in w))
    return "\n".join(lines)


# ---- colour ------------------------------------------------------------------------------------------------------------

def hex_to_rgb(h):
    h = h.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    return "#%02x%02x%02x" % tuple(int(round(max(0, min(255, c)))) for c in rgb)


def srgb_to_lab(rgb):
    """rgb: (..., 3) floats 0..255 -> CIE Lab (D65)."""
    c = np.asarray(rgb, np.float64) / 255.0
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    m = np.array([[0.4124564, 0.3575761, 0.1804375],
                  [0.2126729, 0.7151522, 0.0721750],
                  [0.0193339, 0.1191920, 0.9503041]])
    xyz = c @ m.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > (6 / 29) ** 3, np.cbrt(xyz), xyz / (3 * (6 / 29) ** 2) + 4 / 29)
    L = 116 * f[..., 1] - 16
    a = 500 * (f[..., 0] - f[..., 1])
    b = 200 * (f[..., 1] - f[..., 2])
    return np.stack([L, a, b], -1)


def rgb_to_hsv(rgb):
    """rgb: (..., 3) floats 0..255 -> hue degrees 0..360, saturation 0..1, value 0..1."""
    a = np.asarray(rgb, np.float64) / 255.0
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx, mn = a.max(-1), a.min(-1)
    d = mx - mn + 1e-12
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60.0
    s = np.where(mx > 0, (mx - mn) / (mx + 1e-12), 0.0)
    return h % 360, s, mx


def hue_in(h, lo, hi):
    """Hue band test that wraps past 360 (red is 345..15)."""
    lo, hi = lo % 360, hi % 360
    return (h >= lo) & (h <= hi) if lo <= hi else (h >= lo) | (h <= hi)


def load_rgb(path, max_side=None):
    from PIL import Image
    im = Image.open(path)
    im.draft("RGB", (max_side, max_side)) if max_side and im.format == "JPEG" else None
    im = im.convert("RGB")
    if max_side and max(im.size) > max_side:
        im.thumbnail((max_side, max_side), Image.LANCZOS)
    return im


def palette(path_or_img, k=6, seed=0, side=160):
    """Dominant colours by k-means in Lab. Returns [(hex, fraction, lab)] sorted by fraction."""
    from PIL import Image
    im = path_or_img if isinstance(path_or_img, Image.Image) else load_rgb(path_or_img, side)
    if max(im.size) > side:
        im = im.copy()
        im.thumbnail((side, side), Image.LANCZOS)
    px = np.asarray(im.convert("RGB"), np.float64).reshape(-1, 3)
    lab = srgb_to_lab(px)
    rng = np.random.default_rng(seed)
    # k-means++ seeding
    cent = [lab[rng.integers(len(lab))]]
    for _ in range(1, k):
        d = np.min(((lab[:, None, :] - np.array(cent)[None]) ** 2).sum(-1), 1)
        cent.append(lab[rng.choice(len(lab), p=d / d.sum())] if d.sum() > 0 else lab[rng.integers(len(lab))])
    cent = np.array(cent)
    for _ in range(25):
        lbl = np.argmin(((lab[:, None, :] - cent[None]) ** 2).sum(-1), 1)
        new = np.array([lab[lbl == j].mean(0) if np.any(lbl == j) else cent[j] for j in range(k)])
        if np.allclose(new, cent, atol=1e-3):
            break
        cent = new
    lbl = np.argmin(((lab[:, None, :] - cent[None]) ** 2).sum(-1), 1)
    out = []
    for j in range(k):
        m = lbl == j
        if not np.any(m):
            continue
        out.append((rgb_to_hex(px[m].mean(0)), float(m.mean()), cent[j]))
    return sorted(out, key=lambda x: -x[1])


def palette_distance(measured, target_hex):
    """Weighted mean of each measured colour's distance (CIE76 delta E) to its nearest target colour."""
    if not measured or not target_hex:
        return None
    tl = srgb_to_lab(np.array([hex_to_rgb(h) for h in target_hex], np.float64))
    tot = 0.0
    for hx, frac, lab in measured:
        lab = srgb_to_lab(np.array(hex_to_rgb(hx), np.float64)) if lab is None else lab
        tot += frac * float(np.min(np.linalg.norm(tl - lab, axis=1)))
    return tot / max(1e-9, sum(f for _, f, _ in measured))


# ---- drawing -----------------------------------------------------------------------------------------------------------

THEME = dict(
    bg=(11, 13, 16), card=(18, 21, 26), card2=(24, 28, 34), line=(255, 255, 255, 22), text=(232, 236, 241),
    dim=(146, 156, 168), faint=(88, 97, 109), accent=(242, 166, 90), accent2=(255, 214, 153),
    teal=(79, 209, 197), red=(255, 107, 107), green=(94, 214, 140), amber=(245, 190, 80), blue=(120, 160, 210),
)

_FONT_CACHE = {}
_SANS = ["Inter-Regular.ttf", "Inter.ttf", "DejaVuSans.ttf", "LiberationSans-Regular.ttf", "Arial.ttf",
         "Helvetica.ttc", "NotoSans-Regular.ttf"]
_SANS_BOLD = ["Inter-SemiBold.ttf", "Inter-Bold.ttf", "DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf",
              "Arial Bold.ttf", "NotoSans-Bold.ttf"]
_MONO = ["JetBrainsMono-Regular.ttf", "JetBrainsMonoNerdFont-Regular.ttf", "DejaVuSansMono.ttf",
         "LiberationMono-Regular.ttf", "Menlo.ttc"]
_FONT_DIRS = ["/usr/share/fonts", "/usr/local/share/fonts", os.path.expanduser("~/.local/share/fonts"),
              os.path.expanduser("~/Library/Fonts"), "/Library/Fonts", "/System/Library/Fonts",
              "/System/Library/Fonts/Supplemental", "C:/Windows/Fonts"]


def _find_font(names):
    for d in _FONT_DIRS:
        if not os.path.isdir(d):
            continue
        for dirpath, _, files in os.walk(d):
            low = {f.lower(): f for f in files}
            for n in names:
                if n.lower() in low:
                    return os.path.join(dirpath, low[n.lower()])
    return None


def font(size, kind="sans"):
    """kind: sans | bold | mono. Falls back to Pillow's built-in font when no TTF is installed."""
    from PIL import ImageFont
    key = (kind, size)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    names = {"sans": _SANS, "bold": _SANS_BOLD, "mono": _MONO}[kind]
    env = os.environ.get({"sans": "FORGE_FONT", "bold": "FORGE_FONT_BOLD", "mono": "FORGE_FONT_MONO"}[kind])
    path = env if env and os.path.exists(env) else _find_font(names)
    try:
        f = ImageFont.truetype(path, size) if path else ImageFont.load_default(size)
    except Exception:
        f = ImageFont.load_default()
    _FONT_CACHE[key] = f
    return f


def text_w(draw, s, f):
    b = draw.textbbox((0, 0), s, font=f)
    return b[2] - b[0]


def ellipsize(draw, s, f, max_w):
    if text_w(draw, s, f) <= max_w:
        return s
    while s and text_w(draw, s + "…", f) > max_w:
        s = s[:-1]
    return s.rstrip() + "…"
