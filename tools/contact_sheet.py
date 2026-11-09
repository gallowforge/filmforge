#!/usr/bin/env python3
"""contact_sheet.py: every painting of a production on one labelled sheet, and 100% crops for close inspection.

Commands
  build FOLDER --out sheet.jpg [--shotlist S] [--qa qa.yaml] [--cols 6] [--title T]
        One cell per painting: shot id, beat, size, and the QA verdict badge when a qa.yaml is given.
        Paintings whose aspect ratio differs from the rest are flagged, so a wrong setting is caught on sight.
  zoom IMAGE --out-dir DIR [--grid 2x2] [--box x0,y0,x1,y1 ...]
        Native-resolution crops (no downscaling) so a reviewer sees faces, hands and small subjects at full size.

Examples
  contact_sheet.py build paintings/ --shotlist shotlist.yaml --qa qa.yaml --out out/contact_sheet.jpg
  contact_sheet.py zoom paintings/s03_moth.png --out-dir out/zoom --grid 2x2
  contact_sheet.py zoom paintings/s03_moth.png --out-dir out/zoom --box 900,300,1500,700
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import forgekit as fk  # noqa: E402

VERDICT_COL = {"accept": "green", "fix": "amber", "repaint": "red", "pending": "faint"}


def _match_shot(stem, shots):
    best = None
    for s in shots:
        sid = str(s.get("id"))
        pf = s.get("painting")
        if pf and os.path.splitext(os.path.basename(pf))[0] == stem:
            return s
        if stem == sid or stem.startswith(sid + "_") or stem.startswith(sid + "-") or stem.startswith(sid + " "):
            if best is None or len(sid) > len(str(best.get("id"))):
                best = s
    return best


def _qa_index(qa):
    out = {}
    for e in (qa or {}).get("frames", []) or []:
        if isinstance(e, dict) and e.get("shot"):
            out[str(e["shot"])] = e
            if e.get("file"):
                out[os.path.splitext(os.path.basename(e["file"]))[0]] = e
    return out


def _ratio(x):
    a, b = (float(v) for v in str(x).split(":"))
    return a / b


def build(folder, out, shotlist=None, qa=None, cols=None, thumb=480, title=None, pattern=None, limit=None, quality=86,
          aspects=None):
    from PIL import Image, ImageDraw
    T = fk.THEME
    paths = fk.list_images(folder, pattern)
    if limit:
        paths = paths[:limit]
    if not paths:
        fk.die(f"no images in {folder}")
    shots = fk.shots_of(fk.load_yaml(shotlist)) if shotlist else []
    qai = _qa_index(fk.load_yaml(qa)) if qa else {}
    infos = []
    for p in paths:
        with Image.open(p) as im:
            infos.append((p, im.size))
    ratios = sorted(w / h for _, (w, h) in infos)
    med = ratios[len(ratios) // 2]
    allowed = [_ratio(x) for x in aspects] if aspects else [med]

    def off(w, h):
        return min(abs((w / h) / r - 1) for r in allowed) > 0.02
    n = len(paths)
    cols = cols or (4 if n <= 8 else 6 if n <= 36 else 8)
    rows = (n + cols - 1) // cols
    S = 1
    gap, pad = 18, 56
    cell_w = thumb
    img_h = int(round(cell_w / med))
    label_h = 64
    cell_h = img_h + label_h
    head = 120
    W = pad * 2 + cols * cell_w + (cols - 1) * gap
    H = pad * 2 + head + rows * cell_h + (rows - 1) * gap + 36
    sheet = Image.new("RGB", (W, H), T["bg"])
    d = ImageDraw.Draw(sheet, "RGBA")
    d.rounded_rectangle((pad // 2, pad // 2, W - pad // 2, H - pad // 2), radius=28, fill=T["card"], outline=(255, 255, 255, 22))
    f_t, f_s, f_id, f_b, f_m, f_badge = fk.font(40, "bold"), fk.font(20), fk.font(19, "bold"), fk.font(15), fk.font(13, "mono"), fk.font(14, "bold")
    ttl = title or os.path.basename(os.path.abspath(folder))
    d.text((pad + 8, pad + 6), ttl, font=f_t, fill=T["text"])
    counts = {}
    for p, _ in infos:
        stem = os.path.splitext(os.path.basename(p))[0]
        sh = _match_shot(stem, shots) if shots else None
        e = qai.get(stem) or (qai.get(str(sh.get("id"))) if sh else None)
        v = (e or {}).get("verdict")
        if v:
            counts[v] = counts.get(v, 0) + 1
    sub = f"{n} paintings"
    if counts:
        sub += "   ·   " + "   ·   ".join(f"{v} {counts[v]}" for v in ("accept", "fix", "repaint", "pending") if v in counts)
    odd = sum(1 for _, (w, h) in infos if off(w, h))
    if odd:
        sub += f"   ·   {odd} off-aspect"
    d.text((pad + 8, pad + 60), sub, font=f_s, fill=T["dim"])
    tag = "contact sheet"
    d.text((W - pad - 8 - fk.text_w(d, tag, f_m), pad + 20), tag, font=f_m, fill=T["accent"])
    y0 = pad + head
    for k, (p, (w, h)) in enumerate(infos):
        r, c = divmod(k, cols)
        x = pad + c * (cell_w + gap)
        y = y0 + r * (cell_h + gap)
        d.rounded_rectangle((x, y, x + cell_w, y + cell_h), radius=14, fill=T["card2"])
        with Image.open(p) as im:
            im = im.convert("RGB")
            im.thumbnail((cell_w, img_h), Image.LANCZOS)
        ox, oy = x + (cell_w - im.size[0]) // 2, y + (img_h - im.size[1]) // 2
        mask = Image.new("L", im.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, im.size[0] - 1, im.size[1] - 1), radius=10, fill=255)
        sheet.paste(im, (ox, oy), mask)
        stem = os.path.splitext(os.path.basename(p))[0]
        sh = _match_shot(stem, shots) if shots else None
        e = qai.get(stem) or (qai.get(str(sh.get("id"))) if sh else None)
        sid = str(sh.get("id")) if sh else stem
        d.text((x + 12, y + img_h + 8), fk.ellipsize(d, sid, f_id, cell_w * 0.45), font=f_id, fill=T["text"])
        size_s = f"{w}x{h}"
        offa = off(w, h)
        d.text((x + cell_w - 12 - fk.text_w(d, size_s, f_m), y + img_h + 11), size_s, font=f_m,
               fill=T["red"] if offa else T["faint"])
        beat = (sh or {}).get("beat") or (stem if sh else "")
        if beat and beat != sid:
            d.text((x + 12, y + img_h + 36), fk.ellipsize(d, str(beat), f_b, cell_w - 24), font=f_b, fill=T["dim"])
        if e and e.get("verdict"):
            v = str(e["verdict"])
            col = T[VERDICT_COL.get(v, "faint")]
            score = e.get("total")
            mx = e.get("max")
            lab = v.upper() + (f"  {score}/{mx}" if score is not None and mx else f"  {score}" if score is not None else "")
            bw = fk.text_w(d, lab, f_badge) + 22
            bx, by = x + cell_w - bw - 10, y + 10
            d.rounded_rectangle((bx, by, bx + bw, by + 28), radius=14, fill=(*col, 235))
            d.text((bx + 11, by + 5), lab, font=f_badge, fill=(16, 18, 22))
        if offa:
            d.rounded_rectangle((x + 10, y + 10, x + 10 + fk.text_w(d, "ASPECT", f_badge) + 22, y + 38), radius=14,
                                fill=(*T["red"], 235))
            d.text((x + 21, y + 15), "ASPECT", font=f_badge, fill=(16, 18, 22))
    foot = "every painting at a glance: identity, scale, colour script and continuity are checked at full size with zoom"
    d.text((pad + 8, H - pad // 2 - 34), foot, font=f_b, fill=T["faint"])
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    if out.lower().endswith((".jpg", ".jpeg")):
        sheet.save(out, quality=quality, optimize=True, progressive=True)
    else:
        sheet.save(out, optimize=True)
    return out, dict(n=n, cols=cols, rows=rows, size=(W, H), verdicts=counts, off_aspect=odd)


def zoom(image, out_dir, grid=None, boxes=None, overlap=0.08):
    from PIL import Image
    os.makedirs(out_dir, exist_ok=True)
    im = Image.open(image).convert("RGB")
    W, H = im.size
    stem = os.path.splitext(os.path.basename(image))[0]
    crops = []
    if boxes:
        for k, b in enumerate(boxes):
            x0, y0, x1, y1 = [int(v) for v in b.split(",")]
            x0, y0, x1, y1 = max(0, x0), max(0, y0), min(W, x1), min(H, y1)
            if x1 <= x0 or y1 <= y0:
                fk.die(f"box {b} is outside the {W}x{H} image")
            crops.append((f"{stem}_box{k + 1}", (x0, y0, x1, y1)))
    else:
        gx, gy = (int(v) for v in (grid or "2x2").lower().split("x"))
        tw, th = W / gx, H / gy
        ox, oy = tw * overlap, th * overlap
        for j in range(gy):
            for i in range(gx):
                x0 = int(max(0, i * tw - ox))
                y0 = int(max(0, j * th - oy))
                x1 = int(min(W, (i + 1) * tw + ox))
                y1 = int(min(H, (j + 1) * th + oy))
                crops.append((f"{stem}_r{j + 1}c{i + 1}", (x0, y0, x1, y1)))
    out = []
    for name, box in crops:
        p = os.path.join(out_dir, name + ".png")
        im.crop(box).save(p)
        out.append((p, box))
    return out


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0], epilog=__doc__.split("\n", 2)[2],
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="labelled contact sheet of a folder of paintings")
    b.add_argument("folder")
    b.add_argument("--out", required=True, help="output .jpg or .png")
    b.add_argument("--shotlist", help="label cells with shot ids and beats")
    b.add_argument("--qa", help="qa.yaml from forge-frame-qa: adds verdict badges and scores")
    b.add_argument("--cols", type=int, help="columns (default: 4, 6 or 8 by count)")
    b.add_argument("--thumb", type=int, default=480, help="cell width in pixels (default 480)")
    b.add_argument("--title", help="sheet title (default: the folder name)")
    b.add_argument("--pattern", help="only files matching this glob, e.g. 's*.png'")
    b.add_argument("--limit", type=int, help="at most this many images")
    b.add_argument("--aspect", help="allowed aspect ratios, e.g. 16:9 or 3:4,3:2,1:1 for a book (default: the majority)")
    z = sub.add_parser("zoom", help="native-resolution crops of one painting")
    z.add_argument("image")
    z.add_argument("--out-dir", required=True)
    z.add_argument("--grid", help="tiles, e.g. 2x2 (default) or 3x2")
    z.add_argument("--box", action="append", help="x0,y0,x1,y1 in image pixels (repeatable)")
    a = p.parse_args(argv)
    if a.cmd == "build":
        out, info = build(a.folder, a.out, a.shotlist, a.qa, a.cols, a.thumb, a.title, a.pattern, a.limit,
                          aspects=a.aspect.split(",") if a.aspect else None)
        print(f"wrote {out}: {info['n']} paintings, {info['cols']}x{info['rows']} grid, {info['size'][0]}x{info['size'][1]} px"
              + (f", verdicts {info['verdicts']}" if info["verdicts"] else "")
              + (f", {info['off_aspect']} off-aspect" if info["off_aspect"] else ""))
        return 0
    if a.cmd == "zoom":
        for path, box in zoom(a.image, a.out_dir, a.grid, a.box):
            print(f"wrote {path}  (pixels {box[0]},{box[1]} to {box[2]},{box[3]}, 100%)")
        return 0


if __name__ == "__main__":
    sys.exit(main())
