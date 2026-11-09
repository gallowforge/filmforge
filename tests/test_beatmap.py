import json
import os

import numpy as np

from helpers import click_track, tmpdir

import beatmap as B


def _nearest_err(found, truth):
    found = np.array(found)
    return np.array([np.min(np.abs(found - t)) for t in truth])


def test_tempo_beats_and_downbeats():
    with tmpdir() as d:
        truth = click_track(os.path.join(d, "a.wav"), bpm=100, dur=30)
        an = B.analyse(os.path.join(d, "a.wav"))
        assert abs(an["tempo"]["bpm"] - 100) < 1.0, an["tempo"]
        err = _nearest_err(an["beats"], truth[2:-2])
        assert np.median(err) < 0.008, np.median(err)          # beats snap to the true attack
        bars = truth[::4]
        assert np.median(_nearest_err(an["downbeats"], bars[1:-1])) < 0.01   # beat one found


def test_onsets_refined_to_the_attack():
    with tmpdir() as d:
        truth = click_track(os.path.join(d, "a.wav"), bpm=120, dur=12)
        an = B.analyse(os.path.join(d, "a.wav"))
        err = _nearest_err([o[0] for o in an["onsets"]], truth)
        assert np.percentile(err, 90) < 0.006, err


def test_silence_and_phrase_boundaries():
    with tmpdir() as d:
        click_track(os.path.join(d, "a.wav"), bpm=120, dur=32, silence=(20.0, 21.0), change_at=12.0)
        an = B.analyse(os.path.join(d, "a.wav"))
        assert any(abs(a - 20.0) < 0.1 and abs(b - 21.0) < 0.06 for a, b in an["silences"]), an["silences"]
        ts = [b["t"] for b in an["boundaries"]]
        assert any(abs(t - 12.0) < 0.6 for t in ts), ts            # the chord entering is a phrase change
        assert any(abs(t - 21.0) < 0.03 for t in ts), ts           # the music re-entering, on its attack


def test_cut_plan_lands_on_beats_and_fills_the_span():
    with tmpdir() as d:
        truth = click_track(os.path.join(d, "a.wav"), bpm=120, dur=20)
        an = B.analyse(os.path.join(d, "a.wav"))
        plan = B.plan_cuts(an, [1.0] * 5, start=0.0, end=20.0)
        shots = plan["shots"]
        assert len(shots) == 5
        assert abs(shots[0]["start"]) < 1e-9 and abs(shots[-1]["end"] - 20.0) < 1e-6
        cuts = [s["end"] for s in shots[:-1]]
        assert np.max([np.min(np.abs(np.array(truth) - c)) for c in cuts]) < 0.01
        assert all(1.5 <= s["dur"] <= 12 for s in shots)


def test_pins_are_hard_constraints():
    with tmpdir() as d:
        click_track(os.path.join(d, "a.wav"), bpm=120, dur=24)
        an = B.analyse(os.path.join(d, "a.wav"))
        plan = B.plan_cuts(an, [4, 4, 4, 4, 4, 4], ids=list("abcdef"), start=0, end=24,
                           pins=[None, None, 9.0, None, None, None])
        c = next(s for s in plan["shots"] if s["id"] == "c")
        assert abs(c["start"] - 9.0) <= B.PIN_TOL


def test_default_end_is_where_the_music_stops():
    with tmpdir() as d:
        click_track(os.path.join(d, "a.wav"), bpm=120, dur=20, silence=(16.0, 20.0))
        an = B.analyse(os.path.join(d, "a.wav"))
        plan = B.plan_cuts(an, [1.0] * 4)
        assert 15.5 < plan["end"] < 16.0, plan["end"]                # after the last click (15.5 s), before 16
        assert plan["end"] == an["silences"][-1][0]


def test_intent_ranks_the_take_that_matches():
    with tmpdir() as d:
        click_track(os.path.join(d, "a.wav"), bpm=120, dur=24, change_at=12.0)     # gets louder at 12 s
        an = B.analyse(os.path.join(d, "a.wav"))
        rising = B.intent_match(an, {"points": [[0, 0.2], [11.9, 0.2], [12.1, 0.9], [24, 0.9]]})
        falling = B.intent_match(an, {"points": [[0, 0.9], [11.9, 0.9], [12.1, 0.2], [24, 0.2]]})
        assert rising["score"] > falling["score"]


def test_cli_writes_json_and_png():
    with tmpdir() as d:
        wav = os.path.join(d, "a.wav")
        click_track(wav, bpm=90, dur=16)
        js, png = os.path.join(d, "a.json"), os.path.join(d, "a.png")
        B.main([wav, "--shots", "4", "--json", js, "--png", png])
        data = json.load(open(js))
        for k in ("tempo", "beats", "downbeats", "onsets", "hits", "silences", "phrases", "boundaries", "cut_plan"):
            assert k in data
        assert len(data["cut_plan"]["shots"]) == 4
        from PIL import Image
        assert Image.open(png).size[0] == 2400
