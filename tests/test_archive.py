import json
import os
import shutil
import subprocess

from helpers import tmpdir

import archive as AR


def _folder(d):
    f = os.path.join(d, "film")
    os.makedirs(os.path.join(f, "art", "film", "4k"))
    os.makedirs(os.path.join(f, "film"))
    os.makedirs(os.path.join(f, "__pycache__"))
    for p, txt in (("screenplay.md", "words"), ("art/film/s01_a.png", "png1"), ("art/film/s02_b.png", "png2"),
                   ("art/film/4k/s01_a.png", "cache"), ("film/Film_4K.mp4", "video"), ("__pycache__/x.pyc", "b")):
        with open(os.path.join(f, p), "w") as fh:
            fh.write(txt)
    with open(os.path.join(f, "shotlist.yaml"), "w") as fh:
        fh.write("title: t\nscenes: [{id: A}]\nshots:\n"
                 "  - {id: s01, scene: A, dur: 4, kind: painting, beat: a}\n"
                 "  - {id: s02, scene: A, dur: 4, kind: painting, beat: b}\n")
    with open(os.path.join(d, "req.txt"), "w") as fh:
        fh.write("# required\nscreenplay.md\nfilm/*_4K.mp4\n")
    return f


def test_build_then_verify_ok_and_left_out_recorded():
    with tmpdir() as d:
        f = _folder(d)
        m = AR.build(f, os.path.join(d, "req.txt"), os.path.join(f, "shotlist.yaml"), os.path.join(f, "art", "film"))
        assert m["complete"] and m["files"] == 5
        pats = {lo["pattern"]: lo for lo in m["left_out"]}
        assert "*/4k/" in pats and "__pycache__/" in pats             # caches left out, with reasons
        assert AR.verify(f)["ok"]


def test_verify_catches_changed_missing_and_edited_manifest():
    with tmpdir() as d:
        f = _folder(d)
        AR.build(f)
        open(os.path.join(f, "screenplay.md"), "w").write("edited")
        os.remove(os.path.join(f, "art", "film", "s02_b.png"))
        r = AR.verify(f)
        assert not r["ok"] and r["changed"] == ["screenplay.md"] and r["missing"] == ["art/film/s02_b.png"]
        AR.build(f)
        with open(os.path.join(f, AR.MANIFEST), "a") as fh:
            fh.write("0" * 64 + "  sneaky.txt\n")
        assert AR.verify(f)["tampered_manifest"]


def test_incomplete_when_required_or_painting_missing():
    with tmpdir() as d:
        f = _folder(d)
        os.remove(os.path.join(f, "film", "Film_4K.mp4"))
        os.remove(os.path.join(f, "art", "film", "s02_b.png"))
        m = AR.build(f, os.path.join(d, "req.txt"), os.path.join(f, "shotlist.yaml"), os.path.join(f, "art", "film"))
        assert not m["complete"]
        assert m["required_missing"] == ["film/*_4K.mp4"] and m["shots_missing"] == ["s02"]


def test_manifest_is_plain_sha256sum_format():
    if not shutil.which("sha256sum"):
        return
    with tmpdir() as d:
        f = _folder(d)
        AR.build(f)
        r = subprocess.run(["sha256sum", "-c", "--quiet", AR.MANIFEST], cwd=f, capture_output=True, text=True)
        assert r.returncode == 0, r.stdout + r.stderr
        meta = json.load(open(os.path.join(f, AR.META)))
        assert meta["files"] == 5


def test_compare_proves_a_copy():
    with tmpdir() as d:
        f = _folder(d)
        c = os.path.join(d, "copy")
        shutil.copytree(f, c)
        assert AR.compare(f, c)["ok"]
        open(os.path.join(c, "screenplay.md"), "w").write("drift")
        r = AR.compare(f, c)
        assert not r["ok"] and r["differ"] == ["screenplay.md"]
