import os

from helpers import FIXTURES, ROOT

import budget as B
import forgekit as fk

PRICES = fk.load_yaml(os.path.join(ROOT, "config", "prices.yaml"))


def test_reproduces_a_finish_plan_to_the_cent():
    # 13 paintings + two score cues: the plan's own total was 66.26 of 70.71 credits
    sl = fk.load_yaml(os.path.join(FIXTURES, "finish_plan.yaml"))
    res = B.compute(sl, PRICES, credits=70.71, reserve_pct=0, retake=0)
    assert abs(res["total"] - 66.26) < 0.02, res["total"]
    assert res["fits"] and abs(res["margin"] - 4.45) < 0.02
    assert abs(res["by_stage"]["paint"][1] - 35.75) < 1e-6


def test_default_buffer_warns_and_exit_code_is_2():
    path = os.path.join(FIXTURES, "finish_plan.yaml")
    res = B.compute(fk.load_yaml(path), PRICES, credits=70.71)
    assert not res["fits"]
    assert B.main([path, "--credits", "70.71"]) == 2
    assert B.main([path, "--credits", "70.71", "--retake", "0", "--reserve", "0"]) == 0


def _sl(shots, assets=()):
    return {"title": "t", "scenes": [{"id": "A"}], "assets": list(assets), "shots": shots}


def test_video_costs_keyframe_plus_whole_clips():
    sl = _sl([{"id": "v", "scene": "A", "dur": 7, "kind": "video", "beat": "x"}])
    items = B.line_items(sl, PRICES, retake=0)
    clip = next(i for i in items if i["kind"] == "video")
    key = next(i for i in items if i["kind"] == "painting")
    assert abs(clip["base"] - 2 * 16.25) < 1e-9          # 7 s on a 5 s model = two clips
    assert abs(key["base"] - 2.75) < 1e-9


def test_fit_plan_converts_video_first_and_tiers():
    sl = _sl([{"id": "s01", "scene": "A", "dur": 5, "kind": "painting", "beat": "a"},
              {"id": "s02", "scene": "A", "dur": 5, "kind": "video", "beat": "b", "priority": 2},
              {"id": "s03", "scene": "A", "dur": 5, "kind": "painting", "beat": "c", "priority": 3}],
             [{"id": "score", "kind": "music", "seconds": 20}])
    res = B.compute(sl, PRICES, credits=20)
    assert not res["fits"]
    steps = res["fit_plan"]["steps"]
    assert "s02" in steps[0]["action"] and "painted key poses" in steps[0]["action"]
    assert res["fit_plan"]["fits"]
    names = [t["name"] for t in res["tiers"]]
    assert names == ["full plan", "painted holds only", "must-haves only"]
    assert res["tiers"][1]["total"] < res["tiers"][0]["total"]


def test_example_fits_its_credits():
    from helpers import EXAMPLE
    sl = fk.load_yaml(os.path.join(EXAMPLE, "shotlist.yaml"))
    res = B.compute(sl, PRICES, credits=70)
    assert res["fits"] and res["room_paintings"] >= 1
