import os

from PIL import Image

from helpers import tmpdir

import contact_sheet as CS
import forgekit as fk


def _make(d, n=5):
    os.makedirs(os.path.join(d, "art"))
    for i in range(1, n + 1):
        size = (640, 360) if i != 3 else (360, 640)                  # one painting in the wrong aspect
        Image.new("RGB", size, (20 * i, 40, 60)).save(os.path.join(d, "art", f"s0{i}_shot.png"))
    sl = {"title": "t", "scenes": [{"id": "A"}],
          "shots": [{"id": f"s0{i}", "scene": "A", "dur": 4, "kind": "painting", "beat": f"beat {i}"} for i in range(1, n + 1)]}
    qa = {"frames": [{"shot": "s01", "verdict": "accept", "total": 17, "max": 18},
                     {"shot": "s02", "verdict": "fix", "total": 14, "max": 18},
                     {"shot": "s04", "verdict": "repaint", "total": 10, "max": 18}]}
    fk.dump_yaml(sl, os.path.join(d, "sl.yaml"))
    fk.dump_yaml(qa, os.path.join(d, "qa.yaml"))


def test_build_labels_verdicts_and_flags_aspect():
    with tmpdir() as d:
        _make(d)
        out, info = CS.build(os.path.join(d, "art"), os.path.join(d, "sheet.jpg"), os.path.join(d, "sl.yaml"),
                             os.path.join(d, "qa.yaml"), cols=3, thumb=200)
        assert os.path.exists(out)
        assert info["n"] == 5 and info["off_aspect"] == 1
        assert info["verdicts"] == {"accept": 1, "fix": 1, "repaint": 1}
        assert Image.open(out).size == info["size"]


def test_allowed_aspects_for_books():
    with tmpdir() as d:
        _make(d)
        _, info = CS.build(os.path.join(d, "art"), os.path.join(d, "s.png"), aspects=["16:9", "9:16"], thumb=160)
        assert info["off_aspect"] == 0


def test_zoom_crops_are_native_resolution():
    with tmpdir() as d:
        p = os.path.join(d, "big.png")
        Image.new("RGB", (2688, 1520), (10, 10, 10)).save(p)
        tiles = CS.zoom(p, os.path.join(d, "z"), grid="2x2")
        assert len(tiles) == 4
        w, h = Image.open(tiles[0][0]).size
        assert 1344 <= w <= 1460 and 760 <= h <= 830                  # half the frame plus overlap, unscaled
        box = CS.zoom(p, os.path.join(d, "z"), boxes=["100,200,500,450"])
        assert Image.open(box[0][0]).size == (400, 250)
