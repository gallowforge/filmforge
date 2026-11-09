import copy
import os

from helpers import EXAMPLE, tmpdir

import forgekit as fk
import shotlist as SL

EX = fk.load_yaml(os.path.join(EXAMPLE, "shotlist.yaml"))


def test_example_validates_clean():
    E, W = SL.validate(EX, fk.load_yaml(os.path.join(EXAMPLE, "continuity.yaml")))
    assert E == [] and W == [], (E, W)


def test_errors_are_caught():
    sl = copy.deepcopy(EX)
    sl["shots"][1]["id"] = "s01"                  # duplicate id
    sl["shots"][2]["scene"] = "S9"                # unknown scene
    sl["shots"][3]["dur"] = -1                    # bad duration
    sl["shots"][4]["refs"] = ["nope"]             # unknown asset
    sl["shots"][5]["kind"] = "hologram"           # bad kind
    sl["shots"][0]["cut_on"] = "vibe"             # bad cut point
    E, _ = SL.validate(sl)
    text = "\n".join(E)
    for needle in ("used twice", "S9", "positive number", "'nope'", "hologram", "vibe"):
        assert needle in text, (needle, text)


def test_craft_warnings():
    sl = copy.deepcopy(EX)
    sl["shots"][0]["dur"] = 1.0                                         # too short to read
    sl["shots"][2]["narration"] = "one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen"
    sl["shots"][3]["refs"] = ["sheet_moth"]                             # the girl's sheet is missing
    _, W = SL.validate(sl)
    text = "\n".join(W)
    assert "shorter than the eye" in text
    assert "words in" in text
    assert "sheet_girl is not attached" in text


def test_retime_is_frame_exact():
    sl = copy.deepcopy(EX)
    plan = {"start": 0.0, "end": 36.15, "shots": [
        {"id": s["id"], "start": 0, "end": e, "dur": 0, "target": 6, "cut": "beat"}
        for s, e in zip(sl["shots"], [6.01, 11.98, 18.02, 24.0, 30.013, 36.15])]}
    out, changes = SL.retime(sl, {"cut_plan": plan})
    durs = [s["dur"] for s in out["shots"]]
    for d in durs:
        assert abs(d * 24 - round(d * 24)) < 1e-3                      # whole frames
    assert abs(sum(durs) - round(36.15 * 24) / 24) < 1e-3              # no drift


def test_stats_measure_cuts_on_the_music():
    bm = {"file": "x.wav", "duration": 37.0, "beats": [i * 0.5 for i in range(80)], "downbeats": [i * 2.0 for i in range(20)],
          "boundaries": [{"t": 12.0}, {"t": 24.0}], "hits": [[6.0, 1.0]], "onsets": []}
    text, res = SL.stats(EX, bm)
    assert res["on_music"] == res["cuts"] == 5
    assert "cuts on the music: 5/5" in text


def test_cli_validate_exit_codes():
    with tmpdir() as d:
        bad = os.path.join(d, "bad.yaml")
        fk.dump_yaml({"title": "x", "shots": [{"id": "a"}]}, bad)
        assert SL.main(["validate", bad]) == 1
        assert SL.main(["validate", os.path.join(EXAMPLE, "shotlist.yaml")]) == 0
