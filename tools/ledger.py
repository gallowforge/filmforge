#!/usr/bin/env python3
"""ledger.py: the continuity ledger. Who and what is in every shot, what colours it may use, and whether the
prompts and the paintings keep to it.

Commands
  check LEDGER --shotlist S                    declared continuity: characters, props and states shot by shot
  palette LEDGER --paintings DIR --shotlist S  measure every painting: palette against the scene's colour script,
                                               forbidden-colour rules, exposure jumps between neighbours [--write]
  prompts LEDGER --prompts DIR --style STYLE --shotlist S
                                               lint every prompt before a credit is spent: the style lock first,
                                               the avoid tail last, every handle, scale lock, prop and state anchor
                                               present, no character names, forbidden-colour clauses included
  show LEDGER --shotlist S                     the ledger as a table

Exit code 1 when anything drifts, so the director's gates can rely on it.
The ledger format is in templates/continuity.yaml.
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import forgekit as fk  # noqa: E402


def _ids(x):
    return list(x.keys()) if isinstance(x, dict) else list(x or [])


def _window(rule, order, sid):
    """Is shot `sid` inside a rule's window? from: first shot (inclusive), until: first shot NOT covered."""
    i = order.get(sid)
    if i is None:
        return False
    if rule.get("shots"):
        return sid in rule["shots"]
    lo = order.get(rule["from"], 0) if rule.get("from") else 0
    if rule.get("until"):
        hi = order.get(rule["until"], len(order))
        return lo <= i < hi
    if rule.get("through"):
        hi = order.get(rule["through"], len(order) - 1)
        return lo <= i <= hi
    return i >= lo


def _span(item, order, sid):
    """Props and states: present from `from` through `until` (inclusive)."""
    i = order.get(sid)
    if i is None:
        return False
    lo = order.get(item.get("from"), 0) if item.get("from") else 0
    hi = order.get(item.get("until"), len(order) - 1) if item.get("until") else len(order) - 1
    return lo <= i <= hi


def check(led, sl):
    E, W = [], []
    order = fk.shot_order(sl)
    shots = {s["id"]: s for s in fk.shots_of(sl)}
    lsh = led.get("shots") or {}
    chars = led.get("characters") or {}
    props = led.get("props") or {}
    states = {st["id"]: st for st in led.get("states") or [] if isinstance(st, dict) and st.get("id")}
    for sid in shots:
        if sid not in lsh:
            E.append(f"{sid}: no ledger entry")
    for sid in lsh:
        if sid not in shots:
            W.append(f"{sid}: in the ledger but not in the shot list")
    for pid, p in props.items():
        for k in ("from", "until"):
            if p.get(k) and p[k] not in order:
                E.append(f"prop {pid}: {k} '{p[k]}' is not a shot")
        if p.get("holder") and p["holder"] not in chars:
            E.append(f"prop {pid}: holder '{p['holder']}' is not a character")
    for st in states.values():
        if st.get("who") and st["who"] not in chars:
            E.append(f"state {st['id']}: '{st['who']}' is not a character")
    for sid in sorted(shots, key=lambda s: order[s]):
        e = lsh.get(sid) or {}
        here = set(e.get("characters") or [])
        planned = set(shots[sid].get("characters") or [])
        for c in here - set(chars):
            E.append(f"{sid}: character '{c}' is not in the ledger")
        if here != planned and sid in lsh:
            W.append(f"{sid}: ledger has {sorted(here)} but the shot list has {sorted(planned)}")
        listed = set(e.get("props") or [])
        for pid in listed - set(props):
            E.append(f"{sid}: prop '{pid}' is not in the ledger")
        for pid, p in props.items():
            inside = _span(p, order, sid)
            holder_here = (p.get("holder") in here) if p.get("holder") else True
            if inside and holder_here and pid not in listed and sid in lsh:
                E.append(f"{sid}: DRIFT, {pid} is missing ({p.get('holder') or 'it'} carries it from "
                         f"{p.get('from', 'the start')} to {p.get('until', 'the end')})")
            if pid in listed and not inside:
                E.append(f"{sid}: DRIFT, {pid} appears outside its span ({p.get('from', 'start')}..{p.get('until', 'end')})")
        sts = set(e.get("states") or [])
        for x in sts - set(states):
            E.append(f"{sid}: state '{x}' is not in the ledger")
        for st in states.values():
            inside = _span(st, order, sid)
            who_here = st.get("who") in here
            if inside and who_here and st["id"] not in sts and sid in lsh:
                E.append(f"{sid}: DRIFT, {st['who']} should have '{st['id']}' ({st.get('anchor', '')}) from {st.get('from', 'the start')}")
            if st["id"] in sts and not inside:
                E.append(f"{sid}: DRIFT, '{st['id']}' shows outside its span ({st.get('from', 'start')}..{st.get('until', 'end')})")
    return E, W


def forbidden_fraction(img, rule):
    import numpy as np
    a = np.asarray(img.convert("RGB"), np.float64).reshape(-1, 3)
    h, s, v = fk.rgb_to_hsv(a)
    lo, hi = rule["hue"]
    m = fk.hue_in(h, lo, hi) & (s >= float(rule.get("min_sat", 0.35))) & (v >= float(rule.get("min_val", 0.2)))
    return float(m.mean())


def measure(led, sl, folder, k=6):
    import numpy as np
    order = fk.shot_order(sl)
    shots = fk.shots_of(sl)
    col = led.get("colour") or {}
    script = col.get("script") or {}
    tol = float(col.get("tolerance", 28))
    jump = float(col.get("neighbour_jump", 22))
    stops = float(col.get("exposure_stops", 1.5))
    expected = set(col.get("expected_jumps") or [])     # time cuts and deliberate light changes
    rules = col.get("forbid") or []
    rows, E, W, measured = [], [], [], {}
    prev = None
    for s in shots:
        sid = s["id"]
        if s.get("kind") in ("code",):
            continue
        path = fk.find_painting(folder, sid if s.get("kind") != "reuse" else s.get("reuse_of"), s.get("painting"))
        if not path:
            W.append(f"{sid}: no painting found in {folder}")
            prev = None
            continue
        im = fk.load_rgb(path, 256)
        pal = fk.palette(im, k=k)
        px = np.asarray(im, np.float64).reshape(-1, 3)
        L = float(fk.srgb_to_lab(px)[:, 0].mean())
        lin = np.where(px / 255 <= 0.04045, px / 255 / 12.92, ((px / 255 + 0.055) / 1.055) ** 2.4)
        Y = float((lin @ np.array([0.2126, 0.7152, 0.0722])).mean()) + 1e-6
        dist = fk.palette_distance(pal, script.get(s.get("scene"))) if script.get(s.get("scene")) else None
        flags = []
        if dist is not None and dist > tol:
            flags.append(f"off colour script ({dist:.0f} > {tol:g})")
            E.append(f"{sid}: palette is {dist:.0f} delta E from scene {s.get('scene')}'s colour script (limit {tol:g})")
        for r in rules:
            if _window(r, order, sid):
                fr = forbidden_fraction(im, r)
                if fr > float(r.get("max_fraction", 0.02)):
                    flags.append(f"{r.get('id', 'forbid')} {fr * 100:.1f}%")
                    E.append(f"{sid}: {r.get('name', r.get('id'))}: {fr * 100:.1f}% of the frame "
                             f"(limit {float(r.get('max_fraction', 0.02)) * 100:.1f}%)")
        if prev and prev[0] == s.get("scene") and sid not in expected:
            dj = 0.5 * (fk.palette_distance(pal, [h for h, _, _ in prev[1]]) + fk.palette_distance(prev[1], [h for h, _, _ in pal]))
            ds = float(np.log2(Y / prev[2]))
            if dj > jump:
                flags.append(f"palette jump {dj:.0f}")
                W.append(f"{sid}: palette jumps {dj:.0f} delta E from the previous shot in the same scene")
            if abs(ds) > stops:
                flags.append(f"exposure {ds:+.1f} stops")
                W.append(f"{sid}: {abs(ds):.1f} stops {'brighter' if ds > 0 else 'darker'} than the previous shot in the "
                         f"same scene (fix in code with an exposure grade or the matched grade's levels, not a repaint)")
        prev = (s.get("scene"), pal, Y)
        measured[sid] = dict(file=os.path.basename(path), palette=[h for h, _, _ in pal],
                             weights=[round(f, 3) for _, f, _ in pal], lightness=round(L, 1),
                             script_distance=round(dist, 1) if dist is not None else None)
        rows.append([sid, s.get("scene", ""), os.path.basename(path), " ".join(h for h, _, _ in pal[:4]), f"{np.log2(Y):+.1f}",
                     f"{dist:.0f}" if dist is not None else "-", "; ".join(flags) or "ok"])
    return rows, E, W, measured


def _norm(t):
    t = t.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    t = t.replace("—", "-").replace("–", "-")
    return re.sub(r"\s+", " ", t).strip().lower()


def read_prompt(path):
    txt = open(path, encoding="utf-8").read()
    m = re.search(r"```[a-zA-Z]*\n(.*?)```", txt, re.S)
    return (m.group(1) if m else txt).strip()


def lint_prompts(led, sl, style, folder):
    E, W = [], []
    order = fk.shot_order(sl)
    chars = led.get("characters") or {}
    props = led.get("props") or {}
    states = {st["id"]: st for st in led.get("states") or [] if isinstance(st, dict) and st.get("id")}
    rules = (led.get("colour") or {}).get("forbid") or []
    looks = style.get("looks") or {}
    avoid = style.get("avoid", "")
    max_chars = int(style.get("max_chars", 4000))
    names = [n for n in led.get("names") or [] if n]
    lsh = led.get("shots") or {}
    checked = 0
    for s in fk.shots_of(sl):
        sid = s["id"]
        if s.get("kind") not in ("painting", "video", None):
            continue
        cand = [os.path.join(folder, sid + ext) for ext in (".md", ".txt")]
        path = next((p for p in cand if os.path.exists(p)), None)
        if not path:
            E.append(f"{sid}: no prompt file ({sid}.md) in {folder}")
            continue
        checked += 1
        raw = read_prompt(path)
        t = _norm(raw)
        look = s.get("look") or style.get("default_look") or (next(iter(looks)) if looks else None)
        lock = looks.get(look, "") if look else ""
        if lock and not t.startswith(_norm(lock)):
            E.append(f"{sid}: does not open with the '{look}' style lock, word for word")
        if avoid and not t.endswith(_norm(avoid)):
            E.append(f"{sid}: does not end with the avoid tail, word for word")
        here = (lsh.get(sid) or {}).get("characters") or s.get("characters") or []
        for c in here:
            ch = chars.get(c) or {}
            if ch.get("handle") and _norm(ch["handle"]) not in t:
                E.append(f"{sid}: {c}'s handle is missing (\"{ch['handle']}\")")
            if ch.get("scale") and _norm(ch["scale"]) not in t:
                E.append(f"{sid}: {c}'s scale lock is missing (\"{ch['scale']}\")")
        for pid in (lsh.get(sid) or {}).get("props") or []:
            p = props.get(pid) or {}
            if p.get("anchor") and _norm(p["anchor"]) not in t:
                E.append(f"{sid}: prop {pid}'s anchor is missing (\"{p['anchor']}\")")
        for x in (lsh.get(sid) or {}).get("states") or []:
            st = states.get(x) or {}
            if st.get("anchor") and _norm(st["anchor"]) not in t:
                E.append(f"{sid}: state {x}'s anchor is missing (\"{st['anchor']}\")")
        for r in rules:
            if r.get("prompt") and _window(r, order, sid) and _norm(r["prompt"]) not in t:
                E.append(f"{sid}: the '{r.get('id')}' clause is missing (\"{r['prompt']}\")")
        for n in names:
            if re.search(r"\b" + re.escape(n.lower()) + r"\b", t):
                E.append(f"{sid}: uses the name '{n}'; prompts use visual handles (names can be painted as text)")
        if len(raw) > max_chars:
            W.append(f"{sid}: {len(raw)} characters, over the {max_chars} limit set in the style lock")
    return E, W, checked


def show(led, sl):
    order = fk.shot_order(sl)
    lsh = led.get("shots") or {}
    rows = []
    for s in fk.shots_of(sl):
        e = lsh.get(s["id"]) or {}
        rows.append([s["id"], s.get("scene", ""), ", ".join(e.get("characters") or []) or "-",
                     ", ".join(e.get("props") or []) or "-", ", ".join(e.get("states") or []) or "-",
                     " ".join((e.get("palette") or [])[:3])])
    rules = (led.get("colour") or {}).get("forbid") or []
    out = fk.table(rows, ["shot", "scene", "characters", "props", "states", "measured palette"], "llllll")
    for r in rules:
        win = [sid for sid in order if _window(r, order, sid)]
        out += f"\nrule {r.get('id')}: {r.get('name', '')}  (applies to {', '.join(win) or 'no shots'})"
    return out


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0], epilog=__doc__.split("\n", 2)[2],
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("check", "palette", "prompts", "show"):
        q = sub.add_parser(name)
        q.add_argument("ledger")
        q.add_argument("--shotlist", required=True)
        if name == "palette":
            q.add_argument("--paintings", required=True, help="folder of paintings (named <shot id>_*.png)")
            q.add_argument("--write", action="store_true", help="store the measured palettes in the ledger")
            q.add_argument("--k", type=int, default=6, help="colours per palette (default 6)")
        if name == "prompts":
            q.add_argument("--prompts", required=True, help="folder with <shot id>.md prompt files")
            q.add_argument("--style", required=True, help="style-lock.yaml")
    a = p.parse_args(argv)
    led = fk.load_yaml(a.ledger)
    sl = fk.load_yaml(a.shotlist)
    if a.cmd == "show":
        print(show(led, sl))
        return 0
    if a.cmd == "check":
        E, W = check(led, sl)
        label = "continuity"
    elif a.cmd == "palette":
        rows, E, W, measured = measure(led, sl, a.paintings, a.k)
        print(fk.table(rows, ["shot", "scene", "file", "palette", "stops", "dE", "flags"], "llllrrl"))
        print()
        if a.write:
            for sid, m in measured.items():
                led.setdefault("shots", {}).setdefault(sid, {}).update(palette=m["palette"], lightness=m["lightness"])
            fk.dump_yaml(led, a.ledger)
            print(f"stored {len(measured)} palettes in {a.ledger}")
        label = "colour"
    else:
        E, W, n = lint_prompts(led, sl, fk.load_yaml(a.style), a.prompts)
        label = f"prompts ({n} checked)"
    for m in E:
        print(f"ERROR   {m}")
    for m in W:
        print(f"warning {m}")
    print(f"{label}: " + ("ok" if not E and not W else f"{len(E)} error(s), {len(W)} warning(s)"))
    return 1 if E else 0


if __name__ == "__main__":
    sys.exit(main())
