import copy
import os

from PIL import Image

from helpers import EXAMPLE, paint_stand_ins, tmpdir

import forgekit as fk
import ledger as LG

LED = fk.load_yaml(os.path.join(EXAMPLE, "continuity.yaml"))
SL = fk.load_yaml(os.path.join(EXAMPLE, "shotlist.yaml"))
STYLE = fk.load_yaml(os.path.join(EXAMPLE, "style-lock.yaml"))


def test_example_continuity_is_consistent():
    E, W = LG.check(LED, SL)
    assert E == [] and W == [], (E, W)


def test_prop_missing_inside_its_span_is_drift():
    led = copy.deepcopy(LED)
    led["shots"]["s03"]["props"] = []
    E, _ = LG.check(led, SL)
    assert any("s03" in e and "lantern is missing" in e for e in E), E


def test_prop_outside_its_span_is_drift():
    led = copy.deepcopy(LED)
    led["shots"]["s05"]["props"] = ["lantern"]
    E, _ = LG.check(led, SL)
    assert any("s05" in e and "outside its span" in e for e in E), E


def test_state_must_follow_its_character():
    led = copy.deepcopy(LED)
    led["shots"]["s04"]["states"] = []
    E, _ = LG.check(led, SL)
    assert any("s04" in e and "soot" in e for e in E), E


def test_forbidden_colour_is_measured():
    rule = {"hue": [38, 58], "min_sat": 0.3, "min_val": 0.2}
    img = Image.new("RGB", (100, 100), (20, 26, 38))
    img.paste((242, 192, 64), (0, 0, 100, 10))                        # a 10% band of warm gold
    assert abs(LG.forbidden_fraction(img, rule) - 0.10) < 0.01
    img2 = Image.new("RGB", (100, 100), (20, 26, 38))
    img2.paste((232, 116, 59), (0, 0, 100, 30))                       # ember orange is allowed
    assert LG.forbidden_fraction(img2, rule) < 0.005


def test_measure_finds_a_gold_leak_and_an_exposure_jump():
    with tmpdir() as d:
        rows, E, W, measured = LG.measure(LED, SL, paint_stand_ins(os.path.join(d, "paintings")))
        assert any(e.startswith("s02") and "gold" in e for e in E), E       # the gold leak
        assert any(w.startswith("s04") and "stops darker" in w for w in W), W   # the exposure jump
        assert not any(w.startswith("s06") for w in W)                      # dawn is an expected jump
        assert set(measured) == {"s01", "s02", "s03", "s04", "s05", "s06"}


def test_prompt_lint_finds_exactly_the_missing_scale_lock():
    E, W, n = LG.lint_prompts(LED, SL, STYLE, os.path.join(EXAMPLE, "prompts"))
    assert n == 6
    assert len(E) == 1 and E[0].startswith("s03") and "scale lock" in E[0], E


def test_prompt_lint_catches_names_and_a_paraphrased_lock():
    with tmpdir() as d:
        src = open(os.path.join(EXAMPLE, "prompts", "s01.md")).read()
        bad = src.replace("A frame from a hand-painted storybook film", "A painting from a storybook film")
        bad = bad.replace("The lighthouse stands", "Nell watches as the lighthouse stands")
        for sid in ("s01",):
            open(os.path.join(d, sid + ".md"), "w").write(bad)
        sl = copy.deepcopy(SL)
        sl["shots"] = [s for s in sl["shots"] if s["id"] == "s01"]
        E, _, _ = LG.lint_prompts(LED, sl, STYLE, d)
        text = "\n".join(E)
        assert "style lock" in text and "'Nell'" in text, text
