#!/usr/bin/env python3
"""shotlist.py: validate a shot list, measure it, and retime it to the score.

Commands
  validate SHOTLIST [--strict]                 schema and craft checks; errors exit 1 (warnings too with --strict)
  stats SHOTLIST [--beatmap beatmap.json]       duration, shots per scene, screen time, and how the cuts sit on the score
  retime SHOTLIST --beatmap beatmap.json        apply beatmap's cut plan: frame-exact durations, written to --out

The schema is in templates/shotlist.yaml and in the forge-story skill (references/shotlist-schema.md).
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import forgekit as fk  # noqa: E402

KINDS = {"painting", "video", "code", "reuse"}
FRAMINGS = {"extreme-wide", "wide", "medium-wide", "medium", "medium-close", "close", "extreme-close", "insert",
            "two-shot", "over-shoulder", "pov", "aerial"}
CUT_ON = {"phrase", "downbeat", "beat", "hit", "silence", "accent", "free"}
STATUS = {"planned", "prompted", "painted", "accepted", "fixed", "repaint", "rendered", "cut"}
ASSET_KINDS = {"sheet", "plate", "proof", "music", "video", "voice", "code", "other"}
MOTION_KEYS = {"tin", "tout", "fog", "fogc", "sweep", "flick", "fire", "shim", "shake", "crop", "ashc", "emberc", "life",
               "bolts", "crack", "threads", "words", "sand", "title", "note"}


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def validate(sl, ledger=None):
    """Returns (errors, warnings) as lists of strings."""
    E, W = [], []
    if not isinstance(sl, dict):
        return ["the file is not a YAML mapping"], []
    for k in ("title", "shots"):
        if k not in sl:
            E.append(f"missing top-level '{k}'")
    fps = sl.get("fps", 24)
    if not _num(fps) or fps <= 0:
        E.append("fps must be a positive number")
    scenes = sl.get("scenes") or []
    scene_ids = set()
    for sc in scenes:
        if not isinstance(sc, dict) or "id" not in sc:
            E.append(f"scene entry without an id: {sc!r}")
            continue
        if sc["id"] in scene_ids:
            E.append(f"scene id '{sc['id']}' is used twice")
        scene_ids.add(sc["id"])
    chars = sl.get("characters") or []
    char_ids = set(chars.keys()) if isinstance(chars, dict) else set(chars)
    assets = sl.get("assets") or []
    asset_ids, sheets = set(), {}
    for a in assets:
        if not isinstance(a, dict) or "id" not in a:
            E.append(f"asset entry without an id: {a!r}")
            continue
        if a["id"] in asset_ids:
            E.append(f"asset id '{a['id']}' is used twice")
        asset_ids.add(a["id"])
        k = a.get("kind")
        if k not in ASSET_KINDS:
            E.append(f"asset {a['id']}: kind '{k}' is not one of {sorted(ASSET_KINDS)}")
        if k == "sheet":
            if not a.get("character"):
                W.append(f"asset {a['id']}: a sheet should name its character (character: ...)")
            else:
                for c in (a["character"] if isinstance(a["character"], list) else [a["character"]]):
                    sheets[c] = a["id"]
                    if char_ids and c not in char_ids:
                        E.append(f"asset {a['id']}: character '{c}' is not declared")
        if k in ("music", "voice") and not _num(a.get("seconds")):
            E.append(f"asset {a['id']}: {k} needs seconds")
    shots = sl.get("shots") or []
    if not isinstance(shots, list) or not shots:
        E.append("shots must be a non-empty list")
        return E, W
    seen = set()
    wps_max = float(sl.get("narration_wps", 2.4))
    for i, s in enumerate(shots):
        where = f"shot #{i + 1}"
        if not isinstance(s, dict):
            E.append(f"{where} is not a mapping")
            continue
        sid = s.get("id")
        if not sid:
            E.append(f"{where} has no id")
        else:
            where = f"shot {sid}"
            if sid in seen:
                E.append(f"{where}: id used twice")
            seen.add(sid)
        if scene_ids and s.get("scene") not in scene_ids:
            E.append(f"{where}: scene '{s.get('scene')}' is not declared")
        elif not scene_ids and "scene" not in s:
            W.append(f"{where}: no scene")
        d = s.get("dur")
        if not _num(d) or d <= 0:
            E.append(f"{where}: dur must be a positive number of seconds")
            d = 0
        k = s.get("kind", "painting")
        if k not in KINDS:
            E.append(f"{where}: kind '{k}' is not one of {sorted(KINDS)}")
        if not str(s.get("beat", "")).strip():
            E.append(f"{where}: beat is empty (what happens, in one line)")
        for c in s.get("characters") or []:
            if char_ids and c not in char_ids:
                E.append(f"{where}: character '{c}' is not declared")
        for r in s.get("refs") or []:
            if r not in asset_ids:
                E.append(f"{where}: ref '{r}' is not an asset")
        if s.get("framing") and s["framing"] not in FRAMINGS:
            W.append(f"{where}: framing '{s['framing']}' is not a standard size ({', '.join(sorted(FRAMINGS))})")
        if s.get("cut_on") and s["cut_on"] not in CUT_ON:
            E.append(f"{where}: cut_on '{s['cut_on']}' is not one of {sorted(CUT_ON)}")
        if s.get("status") and s["status"] not in STATUS:
            E.append(f"{where}: status '{s['status']}' is not one of {sorted(STATUS)}")
        if "priority" in s and s["priority"] not in (1, 2, 3):
            E.append(f"{where}: priority must be 1 (must), 2 or 3 (nice to have)")
        if "pin" in s and (not _num(s["pin"]) or s["pin"] < 0):
            E.append(f"{where}: pin must be the score time (seconds) where this shot starts")
        if "poses" in s and (not isinstance(s["poses"], int) or s["poses"] < 1):
            E.append(f"{where}: poses must be a whole number of paintings, 1 or more")
        if k == "reuse":
            src = s.get("reuse_of")
            if not src:
                E.append(f"{where}: a reuse shot needs reuse_of: <shot id>")
            elif src not in {x.get('id') for x in shots if isinstance(x, dict)}:
                E.append(f"{where}: reuse_of '{src}' is not a shot")
        mot = s.get("motion")
        if mot is not None and mot != "none":
            if not isinstance(mot, dict):
                E.append(f"{where}: motion must be a mapping of effect: value (or 'none')")
            else:
                for mk in mot:
                    if mk not in MOTION_KEYS:
                        W.append(f"{where}: motion key '{mk}' is not a motion field ({', '.join(sorted(MOTION_KEYS))})")
        # craft checks
        if k == "painting" and d:
            if d < 1.5:
                W.append(f"{where}: a {d:g}s painted hold is shorter than the eye needs to read a painting (1.5s)")
            if d > 10:
                W.append(f"{where}: a {d:g}s painted hold is long; give it life in code (fog, particles, a sweep) or split it")
        if k == "video" and d and d > 10:
            W.append(f"{where}: {d:g}s of video is past most models' single-clip length; split it")
        for c in s.get("characters") or []:
            sh = sheets.get(c)
            if k in ("painting", "video") and sh and sh not in (s.get("refs") or []):
                W.append(f"{where}: {c} is in frame but their sheet {sh} is not attached (style lock: every sheet, every prompt)")
        nar = s.get("narration")
        if nar and d:
            words = len(re.findall(r"[\w']+", str(nar)))
            wps = words / d
            if wps > wps_max:
                W.append(f"{where}: narration is {words} words in {d:g}s ({wps:.1f}/s; keep it under {wps_max:g}/s "
                         f"or let it run across the cut)")
    # runtime against the target
    total = sum(float(s.get("dur", 0) or 0) for s in shots if isinstance(s, dict))
    tgt = sl.get("runtime_target")
    if _num(tgt) and tgt > 0 and abs(total - tgt) / tgt > 0.1:
        W.append(f"shots add up to {total:.1f}s but runtime_target is {tgt:g}s ({(total - tgt) / tgt * 100:+.0f}%)")
    if ledger:
        lshots = set((ledger.get("shots") or {}).keys())
        for sid in seen - lshots:
            W.append(f"shot {sid} has no entry in the continuity ledger")
    return E, W


def nearest(t, arr):
    if not arr:
        return None, None
    import bisect
    i = bisect.bisect_left(arr, t)
    best = None
    for j in (i - 1, i):
        if 0 <= j < len(arr):
            if best is None or abs(arr[j] - t) < abs(best - t):
                best = arr[j]
    return best, t - best


def stats(sl, bm=None, tol=0.06):
    shots = fk.shots_of(sl)
    total = sum(float(s.get("dur", 0) or 0) for s in shots)
    out = [f"{sl.get('title', 'untitled')}: {len(shots)} shots, {fk.fmt_time(total)} ({total:.2f}s)"]
    if shots:
        durs = [float(s.get("dur", 0) or 0) for s in shots]
        out.append(f"  average shot {total / len(shots):.2f}s, shortest {min(durs):.2f}s, longest {max(durs):.2f}s")
    kinds = {}
    for s in shots:
        kinds[s.get("kind", "painting")] = kinds.get(s.get("kind", "painting"), 0) + 1
    out.append("  kinds: " + ", ".join(f"{k} {v}" for k, v in kinds.items()))
    gens = sum(int(s.get("poses", 1)) for s in shots if s.get("kind", "painting") == "painting")
    out.append(f"  paintings to make: {gens} (plus {sum(1 for a in sl.get('assets') or [] if a.get('kind') in ('sheet', 'plate', 'proof'))} sheets, plates and proofs)")
    out.append("")
    names = {sc["id"]: sc.get("name", "") for sc in sl.get("scenes") or [] if isinstance(sc, dict)}
    rows, t = [], 0.0
    order = []
    per = {}
    for s in shots:
        sc = s.get("scene", "-")
        if sc not in per:
            per[sc] = [0, 0.0, t]
            order.append(sc)
        per[sc][0] += 1
        per[sc][1] += float(s.get("dur", 0) or 0)
        t += float(s.get("dur", 0) or 0)
    for sc in order:
        n, d, st = per[sc]
        rows.append([sc, names.get(sc, ""), fk.fmt_time(st), n, f"{d:.2f}", f"{d / n:.2f}"])
    out.append(fk.table(rows, ["scene", "name", "starts", "shots", "secs", "avg"], "lllrrr"))
    screen = {}
    for s in shots:
        for c in s.get("characters") or []:
            screen[c] = screen.get(c, 0.0) + float(s.get("dur", 0) or 0)
    if screen:
        out.append("")
        out.append("screen time: " + ", ".join(f"{c} {v:.1f}s ({v / total * 100:.0f}%)" for c, v in
                                               sorted(screen.items(), key=lambda kv: -kv[1])))
    nar = [(s.get("id"), s.get("narration")) for s in shots if s.get("narration")]
    if nar:
        words = sum(len(re.findall(r"[\w']+", str(n))) for _, n in nar)
        out.append(f"narration: {len(nar)} lines, {words} words, {words / total:.2f} words/s over the film")
    res = dict(total=total, shots=len(shots))
    if bm:
        cuts = fk.cut_times(sl)[:-1]
        beats, downs = bm.get("beats", []), bm.get("downbeats", [])
        phr = sorted(b["t"] for b in bm.get("boundaries", []))
        hits = sorted(h[0] for h in bm.get("hits", []))
        acc = sorted(o[0] for o in bm.get("onsets", []) if o[1] >= 0.5)
        start = float((bm.get("cut_plan") or {}).get("start", 0.0)) if bm.get("cut_plan") else float(sl.get("score_offset", 0.0))
        tally = {"phrase": 0, "hit": 0, "downbeat": 0, "beat": 0, "accent": 0, "off-grid": 0}
        rows = []
        for sid, ct in zip([s.get("id") for s in shots], cuts):
            mt = ct + start
            kind, off = "off-grid", None
            for name, arr in (("phrase", phr), ("hit", hits), ("downbeat", downs), ("beat", beats), ("accent", acc)):
                n_, o_ = nearest(mt, arr)
                if n_ is not None and abs(o_) <= tol:
                    kind, off = name, o_
                    break
            if kind == "off-grid":
                n_, o_ = nearest(mt, sorted(beats + phr + hits))
                off = o_
            tally[kind] += 1
            rows.append([sid, f"{ct:.3f}", kind, f"{off * 1000:+.0f} ms" if off is not None else "-"])
        dur_m = float(bm.get("duration", 0))
        cov = min(total, max(0.0, dur_m - start)) / total * 100 if total else 0
        out.append("")
        out.append(f"score: {bm.get('file')} {fk.fmt_time(dur_m)}, film starts at {start:.2f}s of the score; "
                   f"the score covers {cov:.0f}% of the film")
        on = len(cuts) - tally["off-grid"]
        out.append(f"cuts on the music: {on}/{len(cuts)} within {int(tol * 1000)} ms  ("
                   + ", ".join(f"{k} {v}" for k, v in tally.items() if v) + ")")
        out.append(fk.table(rows, ["cut after", "at", "lands on", "offset"], "lrlr"))
        res.update(cuts=len(cuts), on_music=on, coverage=cov, tally=tally)
    return "\n".join(out), res


def retime(sl, bm, fps=None):
    plan = bm.get("cut_plan")
    if not plan:
        fk.die("the beatmap JSON has no cut_plan: run beatmap.py with --shotlist first")
    shots = fk.shots_of(sl)
    ps = plan["shots"]
    if [str(s.get("id")) for s in shots] != [str(p["id"]) for p in ps]:
        fk.die("the cut plan's shots do not match this shot list (ids or order differ): re-run beatmap.py --shotlist")
    fps = fps or sl.get("fps", 24)
    changes = []
    # frame-exact: round every cut point (not every duration) so no drift accumulates
    t0 = round(plan["start"] * fps)
    for s, p in zip(shots, ps):
        t1 = round(p["end"] * fps)
        new = (t1 - t0) / fps
        old = float(s.get("dur", 0) or 0)
        s["dur"] = round(new, 4)
        s["cut"] = p["cut"]
        changes.append((s.get("id"), old, new, p["cut"]))
        t0 = t1
    sl["score_offset"] = plan["start"]
    return sl, changes


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0], epilog=__doc__.split("\n", 2)[2],
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate", help="schema and craft checks")
    v.add_argument("shotlist")
    v.add_argument("--ledger", help="continuity ledger, to check every shot has an entry")
    v.add_argument("--strict", action="store_true", help="warnings fail too")
    st = sub.add_parser("stats", help="durations, scenes, screen time, cuts on the score")
    st.add_argument("shotlist")
    st.add_argument("--beatmap", help="beatmap JSON, to measure how the cuts sit on the music")
    st.add_argument("--tolerance", type=float, default=0.06, help="seconds a cut may sit off a music event (default 0.06)")
    st.add_argument("--json", help="write the numbers as JSON")
    r = sub.add_parser("retime", help="apply the beatmap cut plan to the shot durations")
    r.add_argument("shotlist")
    r.add_argument("--beatmap", required=True)
    r.add_argument("--out", help="output YAML (default: <name>.retimed.yaml)")
    r.add_argument("--in-place", action="store_true", help="overwrite the shot list (comments are lost)")
    a = p.parse_args(argv)

    sl = fk.load_yaml(a.shotlist)
    if a.cmd == "validate":
        E, W = validate(sl, fk.load_yaml(a.ledger) if a.ledger else None)
        for m in E:
            print(f"ERROR   {m}")
        for m in W:
            print(f"warning {m}")
        n = len(fk.shots_of(sl))
        if not E and not W:
            print(f"ok: {n} shots, no problems")
        else:
            print(f"{len(E)} error(s), {len(W)} warning(s) in {n} shots")
        return 1 if E or (a.strict and W) else 0
    if a.cmd == "stats":
        bm = json.load(open(a.beatmap)) if a.beatmap else None
        text, res = stats(sl, bm, a.tolerance)
        print(text)
        if a.json:
            json.dump(res, open(a.json, "w"), indent=1)
        return 0
    if a.cmd == "retime":
        bm = json.load(open(a.beatmap))
        sl, ch = retime(sl, bm)
        rows = [[sid, f"{o:.3f}", f"{n:.3f}", f"{n - o:+.3f}", cut] for sid, o, n, cut in ch]
        print(fk.table(rows, ["shot", "was", "now", "change", "cut on"], "lrrrl"))
        out = a.shotlist if a.in_place else (a.out or re.sub(r"\.ya?ml$", "", a.shotlist) + ".retimed.yaml")
        fk.dump_yaml(sl, out)
        print(f"wrote {out}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
