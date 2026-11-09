#!/usr/bin/env python3
"""budget.py: turn a shot list into a credit plan before a single credit is spent.

  shot list + price table -> every billable item, spend per stage, total with a retake buffer, the verdict against
  the credits you have, three tiers (full / painted holds only / must-haves only) and, when it does not fit,
  the cheapest changes that make it fit.

Examples
  budget.py shotlist.yaml --credits 70
  budget.py shotlist.yaml --production production.yaml          # credits and spend so far from the state file
  budget.py shotlist.yaml --credits 70 --retake 0 --json plan.json
  budget.py --prices                                             # print the price table

Exit code: 0 when the plan fits inside the credits minus the reserve, 2 when it does not, 1 on bad input.
"""
import argparse
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import forgekit as fk  # noqa: E402

STAGE_OF = {"sheet": "style", "plate": "style", "proof": "style", "music": "score", "painting": "paint",
            "video": "motion", "voice": "sound", "code": "motion", "reuse": "paint", "other": "paint"}
STAGES = ["style", "score", "paint", "motion", "sound"]


def unit_cost(prices, model, seconds=None):
    m = prices["models"].get(model)
    if m is None:
        raise KeyError(f"model '{model}' is not in the price table")
    per, cr = m.get("per", "image"), float(m.get("credits", 0))
    if per == "image":
        return cr
    if seconds is None:
        raise ValueError(f"model '{model}' is priced per {per}; the item needs seconds")
    if per == "second":
        return cr * float(seconds)
    if per == "clip":
        return cr * math.ceil(float(seconds) / float(m.get("seconds", 5)) - 1e-9)
    raise ValueError(f"unknown pricing unit '{per}' for {model}")


def line_items(sl, prices, retake=None):
    """Every billable thing in the shot list. retake: None = policy per kind, or one number for everything."""
    pol = prices.get("policy", {}).get("retake", {})
    dflt = prices.get("defaults", {})
    items = []

    def rate(kind):
        if retake is not None:
            return 0.0 if kind == "music" else float(retake)
        return float(pol.get(kind, 0.0))

    for a in sl.get("assets") or []:
        kind = a.get("kind", "other")
        model = a.get("model") or dflt.get(kind) or "code"
        secs = a.get("seconds")
        qty = int(a.get("count", 1)) * int(a.get("takes", 1))
        u = unit_cost(prices, model, secs)
        items.append(dict(id=a.get("id", "?"), kind=kind, model=model, qty=qty, unit=u, base=u * qty,
                          retake=rate(kind), stage=a.get("stage") or STAGE_OF.get(kind, "paint"),
                          priority=int(a.get("priority", 1)), seconds=secs, source="asset"))
    for s in fk.shots_of(sl):
        kind = s.get("kind", "painting")
        if kind in ("code", "reuse"):
            items.append(dict(id=s.get("id"), kind=kind, model="code", qty=1, unit=0.0, base=0.0, retake=0.0,
                              stage=STAGE_OF[kind], priority=int(s.get("priority", 1)), seconds=None, source="shot"))
            continue
        if kind == "video":
            # a video shot is its keyframe painting(s) plus the clip
            keys = int(s.get("keyframes", 1))
            pm = s.get("keyframe_model") or dflt.get("painting")
            pu = unit_cost(prices, pm)
            if keys:
                items.append(dict(id=f"{s.get('id')} keyframe", kind="painting", model=pm, qty=keys, unit=pu, base=pu * keys,
                                  retake=rate("painting"), stage="paint", priority=int(s.get("priority", 1)), seconds=None,
                                  source="shot"))
            model = s.get("model") or dflt.get("video")
            secs = float(s.get("video_seconds", s.get("dur", 5)))
            u = unit_cost(prices, model, secs)
            qty = int(s.get("takes", 1))
            items.append(dict(id=s.get("id"), kind="video", model=model, qty=qty, unit=u, base=u * qty, retake=rate("video"),
                              stage="motion", priority=int(s.get("priority", 1)), seconds=secs, source="shot",
                              poses_if_painted=int(s.get("poses", 2)), keyframes=keys))
            continue
        model = s.get("model") or dflt.get("painting")
        qty = int(s.get("poses", 1))
        u = unit_cost(prices, model)
        items.append(dict(id=s.get("id"), kind="painting", model=model, qty=qty, unit=u, base=u * qty,
                          retake=rate("painting"), stage="paint", priority=int(s.get("priority", 1)), seconds=None,
                          source="shot"))
    for it in items:
        it["with_retakes"] = it["base"] * (1.0 + it["retake"])
    return items


def totals(items):
    by = {st: [0.0, 0.0] for st in STAGES}
    for it in items:
        by.setdefault(it["stage"], [0.0, 0.0])
        by[it["stage"]][0] += it["base"]
        by[it["stage"]][1] += it["with_retakes"]
    return by, sum(i["base"] for i in items), sum(i["with_retakes"] for i in items)


def painted_holds(items, prices):
    """Every video shot becomes its painted key poses (the way the films tell motion when credits are short)."""
    out = []
    model = prices["defaults"]["painting"]
    u = unit_cost(prices, model)
    pr = float(prices.get("policy", {}).get("retake", {}).get("painting", 0.3))
    for it in items:
        if it["kind"] == "video":
            q = max(0, it.get("poses_if_painted", 2) - it.get("keyframes", 0))   # the keyframe already counts as one pose
            r = min(pr, it["retake"]) if it["retake"] else pr
            out.append(dict(it, kind="painting", model=model, qty=q, unit=u, base=u * q, retake=r,
                            with_retakes=u * q * (1 + r), stage="paint", converted=True))
        else:
            out.append(it)
    return out


def compute(sl, prices, credits=None, reserve_pct=None, retake=None, spent=0.0):
    items = line_items(sl, prices, retake)
    by, base, full = totals(items)
    reserve_pct = float(prices.get("policy", {}).get("reserve_pct", 5) if reserve_pct is None else reserve_pct)
    res = dict(items=items, by_stage=by, base=base, total=full, credits=credits, reserve_pct=reserve_pct, spent=spent)
    tiers = []
    holds = painted_holds(items, prices)
    must = [i for i in holds if i["priority"] <= 1]
    for name, its in (("full plan", items), ("painted holds only", holds), ("must-haves only", must)):
        tiers.append(dict(name=name, total=round(sum(i["with_retakes"] for i in its), 2), items=len(its)))
    res["tiers"] = tiers
    if credits is not None:
        spendable = float(credits) * (1 - reserve_pct / 100.0)
        res["spendable"] = spendable
        res["fits"] = full <= spendable + 1e-9
        res["margin"] = spendable - full
        for t in tiers:
            t["fits"] = t["total"] <= spendable + 1e-9
        u = unit_cost(prices, prices["defaults"]["painting"]) * (1 + float(prices.get("policy", {}).get("retake", {}).get("painting", 0.3)))
        res["room_paintings"] = int(max(0.0, res["margin"]) // u) if u > 0 else None
        if not res["fits"]:
            res["fit_plan"] = fit_plan(items, prices, spendable)
    return res


def fit_plan(items, prices, spendable):
    """Greedy: the cheapest changes, in the order a director would make them, until the plan fits."""
    steps = []
    cur = [dict(i) for i in items]

    def total():
        return sum(i["with_retakes"] for i in cur)

    # 1. video shots become painted key poses, lowest priority and most expensive first
    vids = sorted([i for i in cur if i["kind"] == "video"], key=lambda i: (-i["priority"], -i["with_retakes"]))
    for v in vids:
        if total() <= spendable:
            break
        conv = painted_holds([v], prices)[0]
        saved = v["with_retakes"] - conv["with_retakes"]
        cur[cur.index(v)] = conv
        poses = conv["qty"] + v.get("keyframes", 0)
        steps.append(dict(action=f"tell {v['id']} in {poses} painted key poses instead of video (motion in code)",
                          saved=round(saved, 2)))
    # 2. lower the retake buffer to the policy minimum
    if total() > spendable:
        mn = float(prices.get("policy", {}).get("min_retake", 0.15))
        before = total()
        for i in cur:
            if i["retake"] > mn:
                i["retake"] = mn
                i["with_retakes"] = i["base"] * (1 + mn)
        if before - total() > 1e-6:
            steps.append(dict(action=f"lower the retake buffer to {int(mn * 100)}% (fix more slips in code)",
                              saved=round(before - total(), 2)))
    # 3. drop optional shots, then optional assets (priority 3 before 2, most expensive first)
    for src in ("shot", "asset"):
        opt = sorted([i for i in cur if i["priority"] > 1 and i["source"] == src and i["with_retakes"] > 0],
                     key=lambda i: (-i["priority"], -i["with_retakes"]))
        for o in opt:
            if total() <= spendable:
                break
            cur.remove(o)
            steps.append(dict(action=f"drop optional {src} {o['id']} (priority {o['priority']})", saved=round(o["with_retakes"], 2)))
    left = total()
    return dict(steps=steps, total=round(left, 2), fits=left <= spendable + 1e-9,
                short_by=round(max(0.0, left - spendable), 2))


def report(sl, res, prices, prices_path):
    out = []
    title = sl.get("title", "untitled")
    shots = fk.shots_of(sl)
    dur = sum(float(s.get("dur", 0) or 0) for s in shots)
    out.append(f"{title}: {len(shots)} shots, {fk.fmt_time(dur)}  (prices: {os.path.basename(prices_path)})")
    out.append("")
    rows = []
    for it in res["items"]:
        live = prices["models"].get(it["model"], {}).get("live", True)
        unit = ("" if live else "~") + f"{it['unit']:.2f}"
        q = f"{it['qty']}" + (f" x {it['seconds']:g}s" if it.get("seconds") and it["kind"] in ("music", "video") else "")
        rows.append([it["id"], it["kind"], it["model"], q, unit, f"{it['base']:.2f}",
                     f"{int(round(it['retake'] * 100))}%", f"{it['with_retakes']:.2f}", it["stage"],
                     "" if it["priority"] <= 1 else f"p{it['priority']}"])
    out.append(fk.table(rows, ["item", "kind", "model", "qty", "unit", "base", "retake", "planned", "stage", ""],
                        "lllrrrrrll"))
    out.append("")
    srows = [[st, f"{v[0]:.2f}", f"{v[1]:.2f}"] for st, v in res["by_stage"].items() if v[1] > 0 or v[0] > 0]
    srows.append(["total", f"{res['base']:.2f}", f"{res['total']:.2f}"])
    out.append(fk.table(srows, ["stage", "base", "with retakes"], "lrr"))
    if any(not prices["models"].get(i["model"], {}).get("live", True) for i in res["items"]):
        out.append("~ = estimated price, not read from the live list: re-quote before spending")
    out.append("")
    out.append("tiers: " + "   ".join(f"{t['name']} {t['total']:.2f}" + (" (fits)" if t.get("fits") else
                                                                       " (over)" if "fits" in t else "")
                                    for t in res["tiers"]))
    if res.get("credits") is not None:
        c = float(res["credits"])
        out.append(f"credits {c:.2f}, reserve {res['reserve_pct']:g}% -> spendable {res['spendable']:.2f}"
                   + (f"; spent so far {res['spent']:.2f}, left {c - res['spent']:.2f}" if res.get("spent") else ""))
        if res["fits"]:
            out.append(f"FITS: {res['margin']:.2f} credits to spare"
                       + (f" (room for {res['room_paintings']} more painting{'s' if res['room_paintings'] != 1 else ''} with retakes)"
                          if res.get("room_paintings") else ""))
        else:
            out.append(f"WARNING: OVER BUDGET by {-res['margin']:.2f} credits. Do not spend until the plan fits.")
            fp = res["fit_plan"]
            if fp["steps"]:
                out.append("cheapest way to fit:")
                for k, s in enumerate(fp["steps"], 1):
                    out.append(f"  {k}. {s['action']}  (saves {s['saved']:.2f})")
            if fp["fits"]:
                out.append(f"  -> fits at {fp['total']:.2f}")
            else:
                out.append(f"  -> still short by {fp['short_by']:.2f}: needs more credits, or a shorter film")
    return "\n".join(out)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0], epilog=__doc__.split("\n", 2)[2],
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("shotlist", nargs="?", help="shot list YAML (shots plus assets)")
    p.add_argument("--prices", nargs="?", const="__show__", help="price table YAML (default config/prices.yaml); alone: print it")
    p.add_argument("--credits", type=float, help="credits available for this production")
    p.add_argument("--production", help="read credits_available and spend so far from production.yaml")
    p.add_argument("--reserve", type=float, help="reserve percent (default from the price table)")
    p.add_argument("--retake", type=float, help="one retake fraction for every image and video (e.g. 0 or 0.3)")
    p.add_argument("--json", help="write the plan as JSON")
    a = p.parse_args(argv)

    prices_path = a.prices if a.prices and a.prices != "__show__" else fk.default_prices()
    prices = fk.load_yaml(prices_path)
    if a.prices == "__show__" or not a.shotlist:
        rows = [[k, v.get("per"), (f"{v['credits']:g}" + (f" / {v['seconds']}s" if v.get("per") == "clip" else
                                                          " / s" if v.get("per") == "second" else "")),
                 "live" if v.get("live") else "estimate", v.get("use", "")] for k, v in prices["models"].items()]
        print(fk.table(rows, ["model", "per", "credits", "", "use"], "llrll"))
        return 0
    sl = fk.load_yaml(a.shotlist)
    credits, spent = a.credits, 0.0
    if a.production:
        pr = fk.load_yaml(a.production).get("budget", {})
        credits = float(pr.get("credits_available", 0)) if credits is None else credits
        spent = sum(float(x.get("credits", 0)) for x in (pr.get("spent") or []))
    try:
        res = compute(sl, prices, credits, a.reserve, a.retake, spent)
    except (KeyError, ValueError) as e:
        fk.die(str(e))
    print(report(sl, res, prices, prices_path))
    if a.json:
        with open(a.json, "w") as f:
            json.dump({k: v for k, v in res.items()}, f, indent=1, default=float)
        print(f"wrote {a.json}")
    if credits is not None and not res["fits"]:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
