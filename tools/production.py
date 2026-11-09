#!/usr/bin/env python3
"""production.py: the production state file (production.yaml), its stage gates, its credit ledger and the next action.

Commands
  status [PRODUCTION]                          where the film stands: stages, budget, the current gate, the next action
  gate [STAGE] [--production P]                run one stage's gate checks (default: the current stage)
  advance [PRODUCTION]                         pass the current gate and move to the next stage (refuses if it fails)
  spend CREDITS --item ID [--stage S] [--note T] [--force REASON] [--production P]
                                               log a spend; refused when an earlier gate is open or the reserve is hit
  signoff STAGE --by WHO --note TEXT [--production P]
                                               record a review (a look at the proof frames, the animatic, the master)

Stages, in order: brief, story, style, score, paint, motion, sound, deliver, retro.
No credit is spent in a stage until every earlier stage has passed its gate.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import forgekit as fk  # noqa: E402

STAGES = ["brief", "story", "style", "score", "paint", "motion", "sound", "deliver", "retro"]
SKILL = {"brief": "forge-director", "story": "forge-story", "style": "forge-style-lock", "score": "forge-score",
         "paint": "forge-painter + forge-frame-qa", "motion": "forge-motion", "sound": "forge-sound",
         "deliver": "forge-deliver", "retro": "forge-director"}
NEEDS_SIGNOFF = {"style", "motion", "deliver"}


class Prod:
    def __init__(self, path):
        self.path = path
        self.dir = os.path.dirname(os.path.abspath(path))
        self.d = fk.load_yaml(path)
        self.d.setdefault("stages", {})
        self.d.setdefault("budget", {}).setdefault("spent", [])

    def f(self, key):
        v = (self.d.get("files") or {}).get(key)
        return os.path.join(self.dir, v) if v else None

    def exists(self, key):
        p = self.f(key)
        return bool(p and os.path.exists(p))

    def save(self):
        fk.dump_yaml(self.d, self.path)

    @property
    def stage(self):
        return self.d.get("stage", "brief")

    def status_of(self, st):
        return (self.d["stages"].get(st) or {}).get("status", "open")

    def spent(self):
        return sum(float(x.get("credits", 0)) for x in self.d["budget"].get("spent") or [])


def _shotlist(p):
    return fk.load_yaml(p.f("shotlist")) if p.exists("shotlist") else None


def gate(p, st):
    """Returns a list of (ok, message, how to fix)."""
    R = []

    def c(ok, msg, fix=""):
        R.append((bool(ok), msg, fix))

    d = p.d
    sl = _shotlist(p)
    rel = lambda k: (d.get("files") or {}).get(k, f"<files.{k}>")  # noqa: E731
    if st == "brief":
        fm = d.get("format") or {}
        c(d.get("title"), "the film has a title", "set title: in production.yaml")
        c(fm.get("width") and fm.get("height") and fm.get("fps"), "format is set (width, height, fps)",
          "set format: {width: 3840, height: 2160, fps: 24}")
        c(float(d["budget"].get("credits_available", 0) or 0) > 0, "the credit ceiling is set",
          "set budget.credits_available to the credits this film may use")
        c(d["budget"].get("approved_by"), "the owner of the credits approved the ceiling",
          "the person who pays sets budget.approved_by (one question, once per film)")
        c(d.get("deliverables"), "deliverables are listed", "list deliverables: (master-4k, posting-1080p, phone, ...)")
    elif st == "story":
        for k in ("bible", "screenplay", "shotlist"):
            c(p.exists(k), f"{k} exists ({rel(k)})", f"forge-story: write {rel(k)} from templates/")
        if sl:
            import shotlist as SL
            E, W = SL.validate(sl)
            c(not E, f"shot list validates ({fk.plural(len(E), 'error')}, {fk.plural(len(W), 'warning')})",
              f"forge-story: python3 scripts/shotlist.py validate {rel('shotlist')}")
            import budget as B
            prices = fk.load_yaml(fk.default_prices())
            try:
                res = B.compute(sl, prices, float(d["budget"].get("credits_available", 0) or 0),
                                d["budget"].get("reserve_pct"))
                c(res["fits"], f"the plan fits the credits ({res['total']:.2f} planned of {res['spendable']:.2f} spendable)",
                  f"forge-story: python3 scripts/budget.py {rel('shotlist')} --production production.yaml, then cut to fit")
            except (KeyError, ValueError) as e:
                c(False, f"the plan can be priced ({e})", "fix the model names in the shot list or config/prices.yaml")
    elif st == "style":
        c(p.exists("style_lock"), f"style lock exists ({rel('style_lock')})", "forge-style-lock: write it from templates/style-lock.yaml")
        if p.exists("style_lock"):
            s = fk.load_yaml(p.f("style_lock"))
            c(s.get("looks") and s.get("avoid"), "style lock has its look(s) and its avoid tail",
              "forge-style-lock: fill looks: and avoid:")
        if sl:
            sheets = set()
            for a in sl.get("assets") or []:
                if a.get("kind") == "sheet":
                    ch = a.get("character")
                    sheets.update(ch if isinstance(ch, list) else [ch])
            chars = sl.get("characters") or []
            chars = list(chars.keys()) if isinstance(chars, dict) else chars
            miss = [x for x in chars if x not in sheets]
            c(not miss, "every character has a sheet" + (f" (missing: {', '.join(miss)})" if miss else ""),
              "forge-style-lock: add a sheet asset per character")
        c(p.exists("ledger"), f"continuity ledger exists ({rel('ledger')})", "forge-painter: write it from templates/continuity.yaml")
        if p.exists("ledger") and sl:
            import ledger as LG
            E, _ = LG.check(fk.load_yaml(p.f("ledger")), sl)
            c(not E, f"continuity ledger is consistent ({fk.plural(len(E), 'error')})",
              f"forge-painter: python3 scripts/ledger.py check {rel('ledger')} --shotlist {rel('shotlist')}")
        if sl and p.exists("qa"):
            proofs = [a["id"] for a in sl.get("assets") or [] if a.get("kind") in ("proof", "sheet")]
            q = {e.get("shot"): e for e in (fk.load_yaml(p.f("qa")).get("frames") or [])}
            bad = [x for x in proofs if (q.get(x) or {}).get("verdict") not in ("accept", "fix")]
            c(not bad, "sheets and proof frames passed QA" + (f" (not yet: {', '.join(bad)})" if bad else ""),
              "forge-frame-qa: inspect the sheets and proof frames")
        elif sl:
            c(False, "sheets and proof frames passed QA (no qa file yet)", "forge-frame-qa: inspect the sheets and proof frames")
    elif st == "score":
        c(p.exists("score_brief"), f"music brief exists ({rel('score_brief')})", "forge-score: write the brief")
        c(p.exists("score"), f"the score exists ({rel('score')})", "forge-score: generate the score from the brief")
        bm = None
        if p.exists("beatmap"):
            bm = json.load(open(p.f("beatmap")))
        c(bm is not None, f"the score is measured ({rel('beatmap')})",
          f"forge-score: python3 scripts/beatmap.py {rel('score')} --shotlist {rel('shotlist')} --json {rel('beatmap')} --png ...")
        if bm is not None:
            c(bm.get("cut_plan"), "the beatmap holds a cut plan", "forge-score: re-run beatmap.py with --shotlist")
        if sl:
            unc = [s["id"] for s in fk.shots_of(sl) if not s.get("cut")]
            c(not unc, "every shot is retimed to the music" + (f" ({len(unc)} not yet)" if unc else ""),
              f"forge-score: python3 scripts/shotlist.py retime {rel('shotlist')} --beatmap {rel('beatmap')} --in-place")
    elif st == "paint":
        if sl and p.exists("ledger") and p.exists("style_lock") and (d.get("files") or {}).get("prompts"):
            import ledger as LG
            E, _, n = LG.lint_prompts(fk.load_yaml(p.f("ledger")), sl, fk.load_yaml(p.f("style_lock")), p.f("prompts"))
            c(not E, f"every prompt passes the lint ({fk.plural(len(E), 'error')} in {fk.plural(n, 'prompt')})",
              f"forge-painter: python3 scripts/ledger.py prompts {rel('ledger')} --prompts {rel('prompts')} "
              f"--style {rel('style_lock')} --shotlist {rel('shotlist')}")
        if sl and p.f("paintings"):
            need = [s for s in fk.shots_of(sl) if s.get("kind", "painting") == "painting"]
            miss = [s["id"] for s in need if not (os.path.isdir(p.f("paintings")) and fk.find_painting(p.f("paintings"), s["id"], s.get("painting")))]
            c(not miss, f"every painting exists ({len(need) - len(miss)}/{len(need)})", "forge-painter: paint the rest in batches of four")
            q = {e.get("shot"): e for e in (fk.load_yaml(p.f("qa")).get("frames") or [])} if p.exists("qa") else {}
            unq = [s["id"] for s in need if s["id"] not in q]
            rep = [s["id"] for s in need if (q.get(s["id"]) or {}).get("verdict") == "repaint"]
            fix = [s["id"] for s in need if (q.get(s["id"]) or {}).get("verdict") == "fix" and not (q[s["id"]].get("fix") or {}).get("done")]
            c(not unq, "every painting has a QA verdict" + (f" (missing: {', '.join(unq)})" if unq else ""),
              "forge-frame-qa: inspect each painting at full size against the sheets")
            c(not rep, "no repaint is outstanding" + (f" ({', '.join(rep)})" if rep else ""),
              "forge-painter: repaint with the corrected prompt from qa.yaml, then QA again")
            c(not fix, "every code fix is applied" + (f" ({', '.join(fix)})" if fix else ""),
              "forge-motion: apply the fixes named in qa.yaml (module + parameters), then set fix.done: true")
            if p.exists("ledger") and os.path.isdir(p.f("paintings")):
                import ledger as LG
                _, E, _, _ = LG.measure(fk.load_yaml(p.f("ledger")), sl, p.f("paintings"))
                c(not E, f"colour checks pass ({fk.plural(len(E), 'error')})",
                  f"forge-frame-qa: python3 scripts/ledger.py palette {rel('ledger')} --paintings {rel('paintings')} --shotlist {rel('shotlist')}")
    elif st == "motion":
        if sl:
            nom = [s["id"] for s in fk.shots_of(sl) if s.get("kind", "painting") in ("painting", "reuse") and s.get("motion") is None]
            c(not nom, "every painted shot has a motion plan (or motion: none)" + (f" ({len(nom)} missing)" if nom else ""),
              "forge-motion: plan each shot's life in code")
        c(p.exists("preview"), f"a preview render exists ({rel('preview')})", "forge-motion: render a 1080p preview with the score")
    elif st == "sound":
        if sl:
            import shotlist as SL
            _, W = SL.validate(sl)
            nw = [w for w in W if "narration" in w]
            c(not nw, "narration fits its shots" + (f" ({len(nw)} too fast)" if nw else ""), "forge-sound: retime or trim the lines")
        c(p.exists("mix"), f"the mix exists ({rel('mix')})", "forge-sound: build the mix")
    elif st == "deliver":
        c(p.exists("deliverables"), f"deliverables folder exists ({rel('deliverables')})", "forge-deliver: encode the deliverables")
        arch = p.f("archive") or p.dir
        man = os.path.join(arch, "MANIFEST.sha256")
        c(os.path.exists(man), "the archive manifest exists", "forge-deliver: python3 scripts/archive.py build <folder> --require ...")
        if os.path.exists(man):
            import archive as AR
            r = AR.verify(arch)
            c(r["ok"] and r.get("complete", True) is not False,
              f"the archive verifies ({r['checked']} files, {len(r['missing'])} missing, {len(r['changed'])} changed)",
              "forge-deliver: fix the archive, then build and verify again")
    elif st == "retro":
        ok = p.exists("lessons") and os.path.getsize(p.f("lessons")) > 40
        c(ok, f"lessons are written ({rel('lessons')})", "forge-director: write what failed, what fixed it, what changes in the method")
    if st in NEEDS_SIGNOFF:
        so = (d["stages"].get(st) or {}).get("signoff")
        c(so and so.get("by"), f"signed off after a review" + (f" by {so['by']}" if so and so.get("by") else ""),
          f"look at the {'sheets and proof frames' if st == 'style' else 'preview with sound' if st == 'motion' else 'master'}"
          f", then: production.py signoff {st} --by <who> --note <what you checked>")
    return R


def next_action(p):
    for st in STAGES:
        if p.status_of(st) != "passed":
            res = gate(p, st)
            for ok, msg, fix in res:
                if not ok:
                    return st, f"[{st}] {msg}: NO.\n  do: {fix}\n  skill: {SKILL[st]}"
            return st, f"[{st}] the gate passes: run production.py advance"
    return None, "the production is finished and archived"


def cmd_status(p):
    d = p.d
    out = [f"{d.get('title', 'untitled')}  (stage: {p.stage})", ""]
    rows = []
    for st in STAGES:
        s = p.status_of(st)
        mark = {"passed": "passed", "open": "open"}.get(s, s)
        cur = "<- here" if st == p.stage else ""
        rows.append([st, mark, SKILL[st], cur])
    out.append(fk.table(rows, ["stage", "status", "skill", ""], "llll"))
    b = d["budget"]
    avail = float(b.get("credits_available", 0) or 0)
    res_pct = float(b.get("reserve_pct", 5))
    spent = p.spent()
    out.append("")
    line = f"credits: {avail:.2f} available, {spent:.2f} spent, {avail - spent:.2f} left (reserve {res_pct:g}% = {avail * res_pct / 100:.2f})"
    sl = _shotlist(p)
    if sl:
        try:
            import budget as B
            r = B.compute(sl, fk.load_yaml(fk.default_prices()), avail, res_pct)
            line += f"; plan {r['total']:.2f}" + (" (fits)" if r["fits"] else " (OVER BUDGET)")
        except (KeyError, ValueError):
            pass
    out.append(line)
    by = {}
    for x in b.get("spent") or []:
        by[x.get("stage", "?")] = by.get(x.get("stage", "?"), 0.0) + float(x.get("credits", 0))
    if by:
        out.append("spent by stage: " + ", ".join(f"{k} {v:.2f}" for k, v in by.items()))
    out.append("")
    st, act = next_action(p)
    if st:
        out.append(f"gate '{st}':")
        for ok, msg, _ in gate(p, st):
            out.append(f"  [{'x' if ok else ' '}] {msg}")
        out.append("")
    out.append("NEXT: " + act)
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0], epilog=__doc__.split("\n", 2)[2],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s1 = sub.add_parser("status")
    s1.add_argument("production", nargs="?", default="production.yaml")
    s2 = sub.add_parser("gate")
    s2.add_argument("stage", nargs="?")
    s2.add_argument("--production", default="production.yaml")
    s3 = sub.add_parser("advance")
    s3.add_argument("production", nargs="?", default="production.yaml")
    s4 = sub.add_parser("spend")
    s4.add_argument("credits", type=float)
    s4.add_argument("--item", required=True)
    s4.add_argument("--stage")
    s4.add_argument("--note", default="")
    s4.add_argument("--force", metavar="REASON", help="spend anyway; the reason is logged")
    s4.add_argument("--production", default="production.yaml")
    s5 = sub.add_parser("signoff")
    s5.add_argument("stage", choices=STAGES)
    s5.add_argument("--by", required=True)
    s5.add_argument("--note", required=True)
    s5.add_argument("--production", default="production.yaml")
    a = ap.parse_args(argv)
    p = Prod(a.production)
    if a.cmd == "status":
        print(cmd_status(p))
        return 0
    if a.cmd == "gate":
        st = a.stage or p.stage
        if st not in STAGES:
            fk.die(f"unknown stage '{st}' (one of {', '.join(STAGES)})")
        res = gate(p, st)
        for ok, msg, fix in res:
            print(f"[{'x' if ok else ' '}] {msg}" + ("" if ok else f"\n      do: {fix}"))
        ok = all(r[0] for r in res)
        print(f"gate '{st}': {'PASS' if ok else 'FAIL'}")
        return 0 if ok else 1
    if a.cmd == "advance":
        st = p.stage
        res = gate(p, st)
        if not all(r[0] for r in res):
            print(f"gate '{st}' fails; not advancing:")
            for ok, msg, fix in res:
                if not ok:
                    print(f"  [ ] {msg}\n      do: {fix}")
            return 1
        p.d["stages"].setdefault(st, {})["status"] = "passed"
        nxt = STAGES[STAGES.index(st) + 1] if st != STAGES[-1] else st
        p.d["stage"] = nxt
        p.save()
        print(f"gate '{st}' passed; now in '{nxt}'")
        return 0
    if a.cmd == "spend":
        st = a.stage or p.stage
        if st not in STAGES:
            fk.die(f"unknown stage '{st}'")
        b = p.d["budget"]
        avail = float(b.get("credits_available", 0) or 0)
        spendable = avail * (1 - float(b.get("reserve_pct", 5)) / 100.0)
        problems = [f"stage '{x}' has not passed its gate" for x in STAGES[:STAGES.index(st)] if p.status_of(x) != "passed"]
        if st == "paint":
            res = gate(p, "paint")
            if res and not res[0][0] and "lint" in res[0][1]:
                problems.append("the prompts do not pass the lint")
        if p.spent() + a.credits > spendable + 1e-9:
            problems.append(f"this spend reaches into the reserve ({p.spent() + a.credits:.2f} > {spendable:.2f})")
        if problems and not a.force:
            print("REFUSED: " + "; ".join(problems))
            print("  fix the gate first, or pass --force \"reason\" (the reason is logged)")
            return 1
        entry = dict(stage=st, item=a.item, credits=round(a.credits, 3))
        if a.note:
            entry["note"] = a.note
        if problems:
            entry["forced"] = a.force + " | " + "; ".join(problems)
        b.setdefault("spent", []).append(entry)
        p.save()
        print(f"logged {a.credits:.2f} credits for {a.item} in '{st}'; {avail - p.spent():.2f} left")
        return 0
    if a.cmd == "signoff":
        p.d["stages"].setdefault(a.stage, {})["signoff"] = dict(by=a.by, note=a.note)
        p.save()
        print(f"signed off '{a.stage}' by {a.by}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
