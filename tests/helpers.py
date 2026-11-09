"""Shared helpers for the tests: synthetic audio with known beats, temporary folders, tool imports."""
import os
import shutil
import sys
import tempfile
import wave
from contextlib import contextmanager

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TOOLS = os.path.join(ROOT, "tools")
EXAMPLE = os.path.join(ROOT, "examples", "the-lantern-moth")
FIXTURES = os.path.join(HERE, "fixtures")
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)


@contextmanager
def tmpdir():
    d = tempfile.mkdtemp(prefix="forge-test-")
    try:
        yield d
    finally:
        shutil.rmtree(d, ignore_errors=True)


def write_wav(path, x, sr=22050):
    x = np.clip(x / (np.abs(x).max() + 1e-9) * 0.9, -1, 1)
    with wave.open(path, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((x * 32767).astype("<i2").tobytes())
    return path


def click_track(path, bpm=100.0, dur=30.0, sr=22050, accent=4, silence=None, change_at=None, seed=0):
    """Clicks on every beat (beat one of each bar louder, with a low thump), optional silence span and a timbre
    change (a sustained chord enters) at change_at. Returns the true beat times."""
    rng = np.random.default_rng(seed)
    n = int(dur * sr)
    x = np.zeros(n)
    t = np.arange(n) / sr
    period = 60.0 / bpm
    beats = []
    k = 0
    while k * period < dur - 0.05:
        tb = k * period
        if not (silence and silence[0] <= tb < silence[1]):
            i = int(round(tb * sr))
            m = min(n - i, int(0.05 * sr))
            env = np.exp(-np.arange(m) / (0.004 * sr))
            amp = 1.0 if k % accent == 0 else 0.5
            x[i:i + m] += amp * rng.standard_normal(m) * env
            if k % accent == 0:
                mm = min(n - i, int(0.25 * sr))
                x[i:i + mm] += 0.8 * np.sin(2 * np.pi * 55 * np.arange(mm) / sr) * np.exp(-np.arange(mm) / (0.08 * sr))
            beats.append(tb)
        k += 1
    if change_at is not None:
        pad = sum(0.08 * np.sin(2 * np.pi * f * t) for f in (220.0, 277.2, 329.6))
        x += np.where(t >= change_at, pad, 0.0)
    if silence:
        x[(t >= silence[0]) & (t < silence[1])] = 0.0
    write_wav(path, x, sr)
    return beats


def copy_example(dst):
    """A writable copy of the worked example (without generated audio or outputs)."""
    target = os.path.join(dst, "film")
    shutil.copytree(EXAMPLE, target, ignore=shutil.ignore_patterns("out", "*.wav", "__pycache__", "MANIFEST.sha256",
                                                                   "manifest.json"))
    return target


def paint_stand_ins(folder, faults=True):
    """Six flat stand-in paintings for the example's shots (the repository holds no generated images). With faults:
    s02 carries a band of warm gold before the lamp is lit, and s04 sits well over two stops under s03."""
    from PIL import Image
    os.makedirs(folder, exist_ok=True)
    night, dawn = (20, 27, 38), (233, 160, 122)
    cols = {"s01": night, "s02": (26, 34, 48), "s03": (40, 48, 60), "s04": (40, 48, 60), "s05": (28, 34, 46), "s06": dawn}
    names = {"s01": "s01_dead_lighthouse", "s02": "s02_last_match", "s03": "s03_moth_on_finger",
             "s04": "s04_opens_her_hands", "s05": "s05_the_beam", "s06": "s06_dawn"}
    for sid, c in cols.items():
        im = Image.new("RGB", (640, 360), c)
        if faults and sid == "s02":
            im.paste((242, 192, 64), (0, 0, 640, 30))                   # about 8% warm gold
        if faults and sid == "s04":
            im = Image.new("RGB", (640, 360), (9, 11, 14))
        im.save(os.path.join(folder, names[sid] + ".png"))
    return folder
