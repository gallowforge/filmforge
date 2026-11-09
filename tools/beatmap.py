#!/usr/bin/env python3
"""beatmap.py: measure a film score, then place the cuts on it.

  audio -> tempo, beat grid, downbeats, onsets, hits, silences, loudness, phrase boundaries -> JSON + PNG
  plus a cut plan: N shots (or the shots of a shot list) with every cut placed on a phrase, downbeat or beat.

Examples
  beatmap.py score.mp3 --json beatmap.json --png beatmap.png
  beatmap.py score.mp3 --shotlist shotlist.yaml --json beatmap.json --png beatmap.png
  beatmap.py score.mp3 --shots 12 --start 0 --end 94
  beatmap.py take1.mp3 take2.mp3 --intent intent.yaml --out-dir takes/      # rank takes against the story's shape

Needs numpy and Pillow. WAV files are read directly; anything else is decoded with ffmpeg.
"""
import argparse
import json
import os
import subprocess
import sys
import wave

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import forgekit as fk  # noqa: E402

SR = 22050
NFFT = 2048
HOP = 256
FPS = SR / HOP                     # analysis frames per second (about 86)
VERSION = 1

# how much each kind of cut point is worth when the cut plan chooses between them
CUT_WEIGHT = {"phrase": 1.0, "silence": 0.9, "hit": 0.8, "downbeat": 0.6, "accent": 0.45, "beat": 0.3, "pin": 0.0}
PIN_TOL = 0.12                     # a pinned shot starts within 120 ms of its story moment


# ---- decoding ----------------------------------------------------------------------------------------------------------

def _resample(a, src, dst):
    if src == dst:
        return a
    if dst < src:
        k = int(np.ceil(src / dst))
        if k > 1:
            a = np.convolve(a, np.ones(k) / k, "same")
    n = int(round(len(a) * dst / src))
    return np.interp(np.arange(n) * (src / dst), np.arange(len(a)), a)


def read_wav(path, sr=SR):
    with wave.open(path) as w:
        ch, width, rate, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        raw = w.readframes(n)
    if width == 1:
        a = (np.frombuffer(raw, np.uint8).astype(np.float64) - 128.0) / 128.0
    elif width == 2:
        a = np.frombuffer(raw, "<i2") / 32768.0
    elif width == 3:
        b = np.frombuffer(raw, np.uint8).reshape(-1, 3).astype(np.int32)
        v = b[:, 0] | (b[:, 1] << 8) | (b[:, 2] << 16)
        a = np.where(v >= 1 << 23, v - (1 << 24), v) / float(1 << 23)
    elif width == 4:
        a = np.frombuffer(raw, "<i4") / 2147483648.0
    else:
        raise ValueError("unsupported WAV sample width")
    a = a.reshape(-1, ch).mean(1)
    return _resample(a.astype(np.float64), rate, sr)


def decode(path, sr=SR):
    if not os.path.exists(path):
        fk.die(f"audio file not found: {path}")
    if path.lower().endswith(".wav"):
        try:
            return read_wav(path, sr)
        except (wave.Error, EOFError, ValueError):
            pass                                    # float or extensible WAV: let ffmpeg read it
    try:
        out = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                             capture_output=True, check=True).stdout
    except FileNotFoundError:
        fk.die("ffmpeg is needed to read this file (or convert it to a PCM WAV first)")
    except subprocess.CalledProcessError as e:
        fk.die(f"ffmpeg could not read {path}: {e.stderr.decode(errors='replace').strip()[:300]}")
    return np.frombuffer(out, np.float32).astype(np.float64)


# ---- features ----------------------------------------------------------------------------------------------------------

def mel_bank(nb=40, fmin=30.0, fmax=8000.0):
    def hz2mel(f):
        return 2595.0 * np.log10(1.0 + f / 700.0)

    def mel2hz(m):
        return 700.0 * (10 ** (m / 2595.0) - 1.0)

    f = mel2hz(np.linspace(hz2mel(fmin), hz2mel(fmax), nb + 2))
    bins = np.fft.rfftfreq(NFFT, 1.0 / SR)
    fb = np.zeros((nb, len(bins)))
    for i in range(nb):
        lo, c, hi = f[i], f[i + 1], f[i + 2]
        fb[i] = np.clip(np.minimum((bins - lo) / (c - lo), (hi - bins) / (hi - c)), 0, None)
    return fb, f[1:-1]


def features(a):
    """Frame-level log-mel energies (dB), RMS (dB), spectral-flux onset strength (all bands and bass only)."""
    pad = NFFT // 2
    x = np.pad(a, (pad, pad))
    frames = np.lib.stride_tricks.sliding_window_view(x, NFFT)[::HOP]
    n = len(frames)
    fb, centres = mel_bank()
    win = np.hanning(NFFT)
    mel = np.empty((n, fb.shape[0]), np.float32)
    rms = np.empty(n, np.float64)
    for i in range(0, n, 2048):
        fr = frames[i:i + 2048]
        rms[i:i + 2048] = np.sqrt(np.mean(fr ** 2, 1) + 1e-12)
        mag = np.abs(np.fft.rfft(fr * win, axis=1))
        mel[i:i + 2048] = (mag ** 2) @ fb.T
    db = 10.0 * np.log10(mel + 1e-10)
    db = np.maximum(db, db.max() - 80.0)
    d = np.diff(db, axis=0, prepend=db[:1])
    up = np.maximum(d, 0.0)
    flux = up.mean(1)
    bass = up[:, centres < 200.0].mean(1) if np.any(centres < 200.0) else flux
    return dict(mel_db=db, rms_db=20.0 * np.log10(rms + 1e-9), flux=flux.astype(np.float64),
                bass=bass.astype(np.float64), n=n)


def smooth(x, w):
    w = max(1, int(w))
    if w <= 1:
        return x
    k = np.hanning(w + 2)[1:-1]
    return np.convolve(x, k / k.sum(), "same")


# ---- tempo and beats ---------------------------------------------------------------------------------------------------

def estimate_tempo(oenv, hint=90.0, lo=40.0, hi=220.0):
    """Autocorrelation of the onset envelope, scored with its multiples and a log-normal prior around the hint."""
    x = oenv - smooth(oenv, FPS * 1.0)
    x = np.maximum(x, 0)
    n = len(x)
    if n < FPS * 4 or not np.any(x):
        return None, 0.0, [], None
    f = np.fft.rfft(x, 2 * n)
    acf = np.fft.irfft(f * np.conj(f))[:n]
    acf = acf / (acf[0] + 1e-12)

    def acf_at(lag):
        if lag >= n - 1:
            return 0.0
        i = int(lag)
        fr = lag - i
        return acf[i] * (1 - fr) + acf[i + 1] * fr

    bpms = np.arange(lo, hi + 0.01, 0.25)
    raw = np.array([acf_at(60.0 * FPS / b) for b in bpms])
    comb = np.array([acf_at(60.0 * FPS / b) + 0.5 * acf_at(2 * 60.0 * FPS / b) + 0.25 * acf_at(4 * 60.0 * FPS / b)
                     for b in bpms])
    prior = np.exp(-0.5 * (np.log2(bpms / hint) / 1.0) ** 2)
    score = comb * prior
    k = int(np.argmax(score))
    # refine on the raw ACF peak near the winner
    lag0 = 60.0 * FPS / bpms[k]
    i0 = max(2, int(round(lag0)) - 3)
    i1 = min(n - 2, int(round(lag0)) + 3)
    j = i0 + int(np.argmax(acf[i0:i1 + 1]))
    y0, y1, y2 = acf[j - 1], acf[j], acf[j + 1]
    den = y0 - 2 * y1 + y2
    lag = j + (0.5 * (y0 - y2) / den if abs(den) > 1e-12 else 0.0)
    bpm = 60.0 * FPS / lag
    srt = np.sort(score)[::-1]
    conf = float((srt[0] - np.median(score)) / (srt[0] + 1e-12))
    # the best rival that is a different tempo (more than 4% away): if it scores within 5%, the pulse is ambiguous
    far = np.abs(np.log(bpms / bpms[k])) > np.log(1.04)
    rival = float(bpms[far][np.argmax(score[far])]) if far.any() else None
    ambiguous = bool(rival and score[far].max() >= 0.95 * score[k])
    alts = []
    for m in (0.5, 2.0, 2.0 / 3.0, 1.5):
        b = bpm * m
        if lo <= b <= hi:
            alts.append(round(float(b), 2))
    if rival and round(rival, 2) not in alts:
        alts.append(round(rival, 2))
    return float(bpm), max(0.0, min(1.0, conf)), alts, (round(rival, 2) if ambiguous else None)


def track_beats(oenv, bpm, tightness=100.0):
    """Dynamic-programming beat tracker (Ellis 2007): each beat is the best onset one period after the last."""
    period = 60.0 * FPS / bpm
    n = len(oenv)
    o = oenv / (oenv.std() + 1e-9)
    wx = np.arange(-int(period), int(period) + 1)
    local = np.convolve(o, np.exp(-0.5 * (wx * 32.0 / period) ** 2), "same")
    offs = np.arange(-int(round(2 * period)), -int(round(period / 2)) + 1)
    txwt = -tightness * np.log(-offs / period) ** 2
    cum = np.zeros(n)
    back = np.full(n, -1)
    thr = 0.01 * local.max()
    started = False
    for i in range(n):
        z = i + offs
        ok = z >= 0
        if not started and local[i] < thr:
            cum[i] = local[i]
            continue
        started = True
        if not ok.any():
            cum[i] = local[i]
            continue
        cand = cum[z[ok]] + txwt[ok]
        k = int(np.argmax(cand))
        cum[i] = local[i] + cand[k]
        back[i] = z[ok][k]
    # the last beat: the last strong local maximum of the cumulative score
    peaks = np.flatnonzero((cum[1:-1] > cum[:-2]) & (cum[1:-1] >= cum[2:])) + 1
    if len(peaks) == 0:
        return np.array([])
    med = np.median(cum[peaks])
    good = peaks[cum[peaks] >= 0.5 * med]
    i = int(good[-1]) if len(good) else int(peaks[-1])
    beats = []
    while i >= 0:
        beats.append(i)
        i = int(back[i])
    return np.array(beats[::-1])


def pick_onsets(oenv, delta=0.07, wait_s=0.05):
    o = oenv / (np.percentile(oenv, 99.5) + 1e-12)
    n = len(o)
    pm = int(0.03 * FPS) + 1
    pa = int(0.1 * FPS)
    out, last = [], -1e9
    for i in range(1, n - 1):
        lo, hi = max(0, i - pm), min(n, i + pm + 1)
        if o[i] < o[lo:hi].max() or o[i] < 0.08:
            continue
        if o[i] < o[max(0, i - pa):min(n, i + pa + 1)].mean() + delta:
            continue
        if i - last < wait_s * FPS:
            continue
        out.append((i / FPS, float(min(1.0, o[i]))))
        last = i
    return out


def refine_onsets(a, onsets, pre=0.05, post=0.05):
    """Move each onset to the true attack: the steepest 4 ms rise of a fine (1.5 ms) level envelope near it.
    The analysis window spreads energy about +-46 ms, so raw flux peaks land 10 to 40 ms early."""
    hop, win = 32, 64
    if len(a) < win * 4 or not onsets:
        return onsets
    hp = np.diff(a, prepend=a[:1])                 # high-pass: attacks are broadband, drones are not
    fr = np.lib.stride_tricks.sliding_window_view(hp, win)[::hop]
    env = 20.0 * np.log10(np.sqrt(np.mean(fr ** 2, 1)) + 1e-7)
    env = np.convolve(env, np.ones(3) / 3, "same")
    rise = np.r_[env[3:] - env[:-3], np.zeros(3)]
    out = []
    for t, st in onsets:
        k0 = max(0, int((t - pre) * SR / hop))
        k1 = min(len(rise) - 1, int((t + post) * SR / hop))
        if k1 <= k0:
            out.append((t, st))
            continue
        k = k0 + int(np.argmax(rise[k0:k1 + 1]))
        out.append(((k + 1.5) * hop / SR + win / 2 / SR, st))
    return out


def silences(rms_db, min_len=0.35, floor=-50.0, rel=35.0, always=1.0, context=2.0):
    """Spans where the level sits far below the piece's loud parts (or below an absolute floor).
    A span of `always` seconds or more is a silence. A shorter one is a silence only when the `context` seconds on
    each side are mostly sound: a held breath, not the gaps between the notes of a sparse texture."""
    loud = np.percentile(rms_db, 95)
    quiet = (rms_db < max(floor, loud - rel)) | (rms_db < -60)
    spans, i, n = [], 0, len(quiet)
    c = int(context * FPS)
    while i < n:
        if quiet[i]:
            j = i
            while j < n and quiet[j]:
                j += 1
            length = (j - i) / FPS
            if length >= always:
                spans.append((i / FPS, j / FPS))
            elif length >= min_len:
                sides = [quiet[max(0, i - c):i], quiet[j:min(n, j + c)]]
                sides = [x for x in sides if len(x) > FPS * 0.25]
                if sides and all(x.mean() < 0.3 for x in sides):
                    spans.append((i / FPS, j / FPS))
            i = j
        else:
            i += 1
    return spans


def in_silence(t, spans, margin=0.0):
    return any(a - margin <= t <= b + margin for a, b in spans)


# ---- structure ---------------------------------------------------------------------------------------------------------

def downbeat_phase(beat_frames, bass, oenv, meter):
    if len(beat_frames) < meter * 2:
        return 0, 0.0
    b = bass / (np.percentile(bass, 99) + 1e-12)
    o = oenv / (np.percentile(oenv, 99) + 1e-12)
    sc = []
    for ph in range(meter):
        idx = beat_frames[ph::meter]
        sc.append(np.mean(b[idx]) + 0.5 * np.mean(o[idx]))
    sc = np.array(sc)
    best = int(np.argmax(sc))
    srt = np.sort(sc)[::-1]
    conf = float((srt[0] - srt[1]) / (srt[0] + 1e-12)) if len(srt) > 1 else 0.0
    return best, conf


def novelty_boundaries(F, beat_times, meter, kernel_bars=2):
    """Foote novelty on a beat-synchronous self-similarity matrix. Returns (beat index, strength 0..1) peaks."""
    nb = len(F)
    if nb < meter * 4:
        return [], np.zeros(nb)
    X = F - F.mean(0)
    X = X / (X.std(0) + 1e-9)
    X = X / (np.linalg.norm(X, axis=1, keepdims=True) + 1e-9)
    S = X @ X.T
    L = max(2, kernel_bars * meter)
    g = np.exp(-0.5 * (np.linspace(-1.5, 1.5, 2 * L)) ** 2)
    G = np.outer(g, g)
    sign = np.ones((2 * L, 2 * L))
    sign[:L, L:] = -1
    sign[L:, :L] = -1
    K = G * sign
    Sp = np.pad(S, L, mode="edge")
    nov = np.zeros(nb)
    for i in range(nb):
        nov[i] = np.sum(Sp[i:i + 2 * L, i:i + 2 * L] * K)
    nov = np.maximum(nov, 0)
    # fade the edges, where the kernel sees padding
    ramp = np.clip(np.arange(nb) / L, 0, 1) * np.clip((nb - 1 - np.arange(nb)) / L, 0, 1)
    nov = nov * (0.3 + 0.7 * ramp)
    if nov.max() > 0:
        nov = nov / nov.max()
    thr = max(0.25, nov.mean() + 0.5 * nov.std())
    peaks = []
    for i in range(1, nb - 1):
        lo, hi = max(0, i - meter), min(nb, i + meter + 1)
        if nov[i] >= thr and nov[i] == nov[lo:hi].max():
            peaks.append((i, float(nov[i])))
    return peaks, nov


def analyse(path, meter=4, bpm_hint=90.0, title=None, bpm_force=None):
    a = decode(path)
    dur = len(a) / SR
    feat = features(a)
    oenv = feat["flux"]
    rms_db = feat["rms_db"]
    sil = silences(rms_db)
    bpm, conf, alts, rival = estimate_tempo(oenv, hint=bpm_hint)
    if bpm_force:
        bpm, conf, rival = float(bpm_force), 1.0, None
    beat_frames = track_beats(oenv, bpm) if bpm else np.array([], int)
    # drop beats that sit inside silence
    beat_frames = np.array([b for b in beat_frames if not in_silence(b / FPS, sil, margin=-0.05)], int)
    beats = beat_frames / FPS
    if len(beats) > 3:
        bpm_grid = 60.0 / np.median(np.diff(beats))
    else:
        bpm_grid = bpm or 0.0
    phase, dconf = downbeat_phase(beat_frames, feat["bass"], oenv, meter)
    downbeats = beats[phase::meter] if len(beats) else np.array([])
    raw_onsets = pick_onsets(oenv)
    onsets = refine_onsets(a, raw_onsets)
    # snap each beat to a refined onset within 40 ms; otherwise shift it by the typical refinement
    if len(beats) and onsets:
        shift = float(np.median([n[0] - r[0] for n, r in zip(onsets, raw_onsets)]))
        ot = np.array([o[0] for o in onsets])
        snapped = []
        for b in beats:
            j = int(np.argmin(np.abs(ot - (b + shift))))
            snapped.append(ot[j] if abs(ot[j] - (b + shift)) <= 0.04 else b + shift)
        beats = np.array(snapped)
        downbeats = beats[phase::meter]
    # the music re-enters on an attack: end each silence exactly there
    if onsets:
        ot = np.array([o[0] for o in onsets])
        fixed = []
        for s0, s1 in sil:
            near = ot[(ot >= s1 - 0.08) & (ot <= s1 + 0.12)]
            fixed.append((s0, float(near[0]) if len(near) else s1))
        sil = fixed

    # hits: strong onsets with a real jump in level just after them
    hits = []
    for t, s in onsets:
        i = int(t * FPS)
        before = rms_db[max(0, i - int(0.4 * FPS)):max(1, i - int(0.05 * FPS))]
        after = rms_db[i:i + int(0.25 * FPS)]
        if len(before) == 0 or len(after) == 0:
            continue
        rise = float(after.mean() - before.mean())
        after_silence = any(abs(t - b) < 0.12 for _, b in sil)
        if (s >= 0.55 and rise >= 3.0) or (after_silence and s >= 0.3) or s >= 0.9:
            hits.append((t, round(min(1.0, 0.6 * s + 0.4 * min(1.0, max(0.0, rise) / 12.0)) + (0.2 if after_silence else 0), 3)))
    dedup = []
    for t, s in sorted(hits):
        if t < 0.15:
            continue
        if dedup and t - dedup[-1][0] < 0.15:
            if s > dedup[-1][1]:
                dedup[-1] = (t, s)
            continue
        dedup.append((t, s))
    hits = [(t, min(1.0, s)) for t, s in dedup]
    keep = max(4, int(dur / 8))
    if len(hits) > keep:
        hits = sorted(sorted(hits, key=lambda h: -h[1])[:keep])

    # phrase boundaries: novelty on beat-synchronous features, plus silences
    bounds = []
    nov_curve = []
    if len(beat_frames) > meter * 4:
        edges = np.r_[beat_frames, min(feat["n"], beat_frames[-1] + int(np.median(np.diff(beat_frames))))]
        F = []
        for i in range(len(beat_frames)):
            s0, s1 = edges[i], max(edges[i] + 1, edges[i + 1])
            F.append(np.r_[feat["mel_db"][s0:s1].mean(0), 2.0 * rms_db[s0:s1].mean()])
        F = np.array(F)
        peaks, nov = novelty_boundaries(F, beats, meter)
        nov_curve = [[round(float(t), 3), round(float(v), 3)] for t, v in zip(beats, nov)]
        db_set = set(np.round(downbeats, 4)) if len(downbeats) else set()
        for i, s in peaks:
            t = beats[i]
            if len(downbeats):
                j = int(np.argmin(np.abs(downbeats - t)))
                if abs(downbeats[j] - t) <= 0.5 * 60.0 / max(bpm_grid, 1):     # only a near downbeat wins
                    t = downbeats[j]
            bounds.append({"t": float(t), "strength": s, "kind": "novelty", "on_downbeat": round(float(t), 4) in db_set})
    for s0, s1 in sil:
        if s0 > 0.5:
            bounds.append({"t": float(s0), "strength": 1.0, "kind": "silence-start", "on_downbeat": False})
        if s1 < dur - 0.5:
            bounds.append({"t": float(s1), "strength": 1.0, "kind": "silence-end", "on_downbeat": False})
    # silence edges always stay; a novelty peak within half a bar of one is the same event; novelty peaks
    # closer than one bar merge into the strongest
    bar = 60.0 / max(bpm_grid, 1e-6) * meter if bpm_grid else 2.0
    edges_ = [b for b in bounds if b["kind"] != "novelty"]
    merged = list(edges_)
    for b in sorted([b for b in bounds if b["kind"] == "novelty"], key=lambda b: (-b["strength"], b["t"])):
        if any(abs(b["t"] - e["t"]) < bar * 0.5 for e in edges_):
            continue
        if all(abs(b["t"] - m["t"]) >= bar * 0.9 for m in merged if m["kind"] == "novelty"):
            merged.append(b)
    bounds = sorted(merged, key=lambda b: b["t"])

    # phrases between the boundaries
    level = smooth(rms_db, FPS * 0.5)
    pts = [0.0] + [b["t"] for b in bounds] + [dur]
    phrases = []
    for k in range(len(pts) - 1):
        s0, s1 = pts[k], pts[k + 1]
        if s1 - s0 < 0.25:
            continue
        seg = level[int(s0 * FPS):max(int(s0 * FPS) + 1, int(s1 * FPS))]
        nbeats = int(np.sum((beats >= s0) & (beats < s1)))
        silent = in_silence((s0 + s1) / 2, sil)
        phrases.append({"index": len(phrases) + 1, "start": round(s0, 3), "end": round(s1, 3),
                        "beats": nbeats, "bars": round(nbeats / meter, 2), "level_db": round(float(seg.mean()), 1),
                        "silent": bool(silent)})

    hop = 0.5
    loud = [round(float(level[min(len(level) - 1, int(t * FPS))]), 1) for t in np.arange(0, dur, hop)]
    return dict(tool="beatmap", version=VERSION, file=os.path.basename(path), title=title or os.path.splitext(os.path.basename(path))[0],
                duration=round(dur, 3), sample_rate=SR, analysis_fps=round(FPS, 3),
                tempo=dict(bpm=round(float(bpm_grid), 2) if bpm_grid else None, acf_bpm=round(bpm, 2) if bpm else None,
                           confidence=round(conf, 3), alternatives=alts, ambiguous_with=rival, forced=bool(bpm_force),
                           meter=meter, downbeat_confidence=round(dconf, 3)),
                beats=[round(float(t), 3) for t in beats], downbeats=[round(float(t), 3) for t in downbeats],
                bars=len(downbeats), onsets=[[round(t, 3), round(s, 3)] for t, s in onsets],
                hits=[[round(t, 3), round(s, 3)] for t, s in hits], silences=[[round(a, 3), round(b, 3)] for a, b in sil],
                boundaries=[dict(b, t=round(b["t"], 3), strength=round(b["strength"], 3)) for b in bounds],
                phrases=phrases, novelty=nov_curve, loudness=dict(hop=hop, db=loud),
                _wave=a)


# ---- cut plan ----------------------------------------------------------------------------------------------------------

PRECISION = {"hit": 3, "accent": 3, "beat": 2, "downbeat": 2, "phrase": 1, "silence": 1, "pin": 0}


def candidates(an, start, end, pins=()):
    """Every place a cut may land. Points closer than 60 ms merge: the kind worth most wins, and the time comes
    from the most precise source (refined attacks, then the beat grid, then phrase and silence edges)."""
    c = {}

    def add(t, kind):
        if not (start + 1e-3 < t < end - 1e-3):
            return
        key = round(t / 0.06)
        for k2 in (key - 1, key, key + 1):
            if k2 in c and abs(c[k2][0] - t) < 0.06:
                t0, k0, p0 = c[k2]
                kind_ = kind if CUT_WEIGHT[kind] > CUT_WEIGHT[k0] else k0
                t_, p_ = (t, PRECISION[kind]) if PRECISION[kind] > p0 else (t0, p0)
                c[k2] = (t_, kind_, p_)
                return
        c[key] = (t, kind, PRECISION[kind])

    for b in an["boundaries"]:
        add(b["t"], "silence" if b["kind"].startswith("silence") else "phrase")
    for t, _ in an["hits"]:
        add(t, "hit")
    for t in an["downbeats"]:
        add(t, "downbeat")
    for t, st in an["onsets"]:
        if st >= 0.5:
            add(t, "accent")
    for pt in pins:                                     # a story moment with no music event near it still gets a point
        if pt is not None and not any(abs(v[0] - pt) <= PIN_TOL for v in c.values()):
            c[("pin", pt)] = (float(pt), "pin", 0)
    for t in an["beats"]:
        add(t, "beat")
    out = sorted(c.values())
    return np.array([t for t, _, _ in out]), [k for _, k, _ in out]


def plan_cuts(an, targets, ids=None, prefs=None, start=0.0, end=None, min_shot=1.5, max_shot=12.0, snap=0.08,
              scale=True, pins=None):
    """Choose N-1 cut points so every shot is close to its target length and every cut lands on the music.
    cost = sum(((dur - target) / target)^2) - snap * sum(weight of each cut point)
    pins[i] = score time where shot i must start (a story moment): a hard constraint, within PIN_TOL."""
    if end is None:
        end = an["duration"]
        if an["silences"] and an["silences"][-1][1] >= an["duration"] - 0.05:
            end = an["silences"][-1][0]                     # the music is over where the trailing silence begins
    end = min(end, an["duration"])
    span = end - start
    N = len(targets)
    if N == 0 or span <= 0:
        return None
    tg = np.array(targets, float)
    if scale and tg.sum() > 0:
        tg = tg * span / tg.sum()
    if N == 1:
        return dict(start=start, end=end, shots=[dict(id=(ids or ["s01"])[0], start=round(start, 3), end=round(end, 3),
                                                      dur=round(span, 3), target=round(float(tg[0]), 3), cut="end")])
    pins = list(pins or [None] * N)
    x, kinds = candidates(an, start, end, [p for p in pins[1:] if p is not None])
    w = np.array([CUT_WEIGHT[k] for k in kinds])
    prefs = prefs or [None] * N
    if scale and any(p is not None for p in pins):
        # scale targets piecewise between pins, so each stretch of shots fills its own span
        bounds = [(0, start)] + [(i, p) for i, p in enumerate(pins) if p is not None and i > 0] + [(N, end)]
        raw = np.array(targets, float)
        tg = raw.copy()
        for (i0, t0), (i1, t1) in zip(bounds, bounds[1:]):
            seg = raw[i0:i1]
            if seg.sum() > 0 and t1 > t0:
                tg[i0:i1] = seg * (t1 - t0) / seg.sum()
    M = len(x)
    if M < N - 1:
        return None
    INF = 1e18
    pts = np.r_[start, x]                      # index 0 = the start of the film
    cost = np.full((N, M + 1), INF)            # cost[i][j]: shots 0..i placed, shot i ends at candidate j (1..M)
    back = np.zeros((N, M + 1), int)
    tol_lo, tol_hi = min_shot - 1e-6, max_shot + 1e-6

    def bonus(i, j):  # the cut at the end of shot i lands on candidate j
        b = w[j - 1]
        pref = prefs[i]
        if pref and pref != "free":
            want = {"phrase": ("phrase", "silence"), "downbeat": ("downbeat", "phrase", "silence", "hit"),
                    "beat": ("beat", "downbeat", "phrase", "silence", "hit", "accent"), "hit": ("hit",), "silence": ("silence",)}.get(pref, ())
            b = b * 1.5 if kinds[j - 1] in want else b * 0.5
        return b

    js = np.arange(1, M + 1)

    def pinned_ok(i, j):          # the cut that ends shot i lands on candidate j
        p = pins[i + 1] if i + 1 < N else None
        return p is None or abs(pts[j] - p) <= PIN_TOL

    for j in js:
        d = pts[j] - start
        if tol_lo <= d <= tol_hi and pinned_ok(0, j):
            cost[0, j] = ((d - tg[0]) / tg[0]) ** 2 - snap * bonus(0, j)
    for i in range(1, N - 1):
        prev = cost[i - 1]
        for j in js:
            if not pinned_ok(i, j):
                continue
            d = pts[j] - pts[:j]                  # candidate starts 0..j-1
            ok = (d >= tol_lo) & (d <= tol_hi) & (prev[:j] < INF)
            if not ok.any():
                continue
            c = prev[:j] + ((d - tg[i]) / tg[i]) ** 2
            c[~ok] = INF
            k = int(np.argmin(c))
            cost[i, j] = c[k] - snap * bonus(i, j)
            back[i, j] = k
    # the last shot ends at `end`
    d = end - pts
    ok = (d >= tol_lo) & (d <= tol_hi) & (cost[N - 2] < INF)
    ok[0] = False
    if not ok.any():
        return None
    final = cost[N - 2] + ((d - tg[N - 1]) / tg[N - 1]) ** 2
    final[~ok] = INF
    j = int(np.argmin(final))
    total = float(final[j])
    chain = [j]
    for i in range(N - 2, 0, -1):
        j = back[i, j]
        chain.append(j)
    chain = chain[::-1]
    ends = [pts[j] for j in chain] + [end]
    cut_kinds = [kinds[j - 1] for j in chain] + ["end"]
    shots, t0 = [], start
    for i in range(N):
        shots.append(dict(id=(ids[i] if ids else f"s{i + 1:02d}"), start=round(t0, 3), end=round(ends[i], 3),
                          dur=round(ends[i] - t0, 3), target=round(float(tg[i]), 3), cut=cut_kinds[i]))
        t0 = ends[i]
    return dict(start=round(start, 3), end=round(end, 3), cost=round(total, 4), snap=snap, shots=shots)


# ---- intent (take selection) -------------------------------------------------------------------------------------------

def intent_match(an, intent):
    """Compare the measured level curve with the story's intended intensity curve, and requested hits with real ones."""
    pts = intent.get("points") or []
    out = {}
    if len(pts) >= 2:
        hop = an["loudness"]["hop"]
        db = np.array(an["loudness"]["db"], float)
        t = np.arange(len(db)) * hop
        lo, hi = np.percentile(db, 5), np.percentile(db, 95)
        lv = np.clip((db - lo) / max(1e-6, hi - lo), 0, 1)
        pt = np.array(pts, float)
        want = np.interp(t, pt[:, 0], pt[:, 1])
        m = (t >= pt[0, 0]) & (t <= pt[-1, 0])
        if m.sum() > 3 and np.std(lv[m]) > 1e-6 and np.std(want[m]) > 1e-6:
            r = float(np.corrcoef(lv[m], want[m])[0, 1])
        else:
            r = 0.0
        out["shape_r"] = round(r, 3)
        out["shape_mae"] = round(float(np.mean(np.abs(lv[m] - want[m]))), 3)
    req = intent.get("hits") or []
    if req:
        found = [h[0] for h in an["hits"]] + [o[0] for o in an["onsets"] if o[1] >= 0.5]
        rows = []
        for h in req:
            if found:
                k = int(np.argmin([abs(f - h) for f in found]))
                rows.append(dict(want=h, got=round(found[k], 3), off_ms=int(round((found[k] - h) * 1000))))
            else:
                rows.append(dict(want=h, got=None, off_ms=None))
        tol = float(intent.get("hit_tolerance_ms", 250))
        out["hits"] = rows
        out["hits_ok"] = sum(1 for r in rows if r["off_ms"] is not None and abs(r["off_ms"]) <= tol)
    want_len = intent.get("length")
    if want_len:
        out["length_off_s"] = round(an["duration"] - float(want_len), 2)
    # one number to rank takes: shape correlation, plus hits landed, minus length error
    score = out.get("shape_r", 0.0)
    if req:
        score += 0.5 * out["hits_ok"] / len(req)
    if want_len:
        score -= min(0.5, abs(out["length_off_s"]) / float(want_len))
    out["score"] = round(score, 3)
    return out


# ---- drawing -----------------------------------------------------------------------------------------------------------

def render_png(an, path, width=2400):
    from PIL import Image, ImageDraw
    T = fk.THEME
    S = 2                                         # draw at 2x, then downsample for clean anti-aliased lines
    W = width * S
    has_plan = bool(an.get("cut_plan"))
    H = (1040 if has_plan else 870) * S
    img = Image.new("RGB", (W, H), T["bg"])
    d = ImageDraw.Draw(img, "RGBA")
    pad = 56 * S
    d.rounded_rectangle((pad // 2, pad // 2, W - pad // 2, H - pad // 2), radius=30 * S, fill=T["card"], outline=(255, 255, 255, 22), width=S)
    # header
    f_title, f_sub, f_small, f_mono = fk.font(44 * S, "bold"), fk.font(22 * S), fk.font(17 * S), fk.font(16 * S, "mono")
    tx = pad + 24 * S
    d.text((tx, pad + 10 * S), an["title"], font=f_title, fill=T["text"])
    tempo = an["tempo"]
    bits = [f"{tempo['bpm']:.1f} BPM" if tempo["bpm"] else "no steady pulse", f"{tempo['meter']}/4",
            fk.fmt_time(an["duration"]), f"{len(an['beats'])} beats", f"{an['bars']} bars",
            f"{len(an['phrases'])} phrases", f"{len(an['hits'])} hits"]
    if an["silences"]:
        bits.append(f"{len(an['silences'])} silences")
    d.text((tx, pad + 70 * S), "   ·   ".join(bits), font=f_sub, fill=T["dim"])
    tag = "beatmap"
    d.text((W - pad - 24 * S - fk.text_w(d, tag, f_mono), pad + 22 * S), tag, font=f_mono, fill=T["accent"])

    x0, x1 = pad + 24 * S, W - pad - 24 * S
    dur = an["duration"]

    def X(t):
        return x0 + (x1 - x0) * (t / max(dur, 1e-9))

    # lanes
    y_ph0, y_ph1 = pad + 130 * S, pad + 160 * S          # phrase labels
    y_w0, y_w1 = pad + 168 * S, pad + 548 * S            # waveform
    y_b0, y_b1 = y_w1 + 10 * S, y_w1 + 46 * S            # beat ruler
    y_ol = y_b1 + 14 * S                                   # onset lane label
    y_o0, y_o1 = y_ol + 26 * S, y_ol + 92 * S            # onset strength
    y_t = y_o1 + 12 * S                                    # time axis
    y_cl = y_t + 52 * S                                    # cut plan label
    y_c0, y_c1 = y_cl + 28 * S, y_cl + 110 * S           # cut plan

    # phrase bands
    for k, ph in enumerate(an["phrases"]):
        a, b = X(ph["start"]), X(ph["end"])
        if not ph["silent"]:
            d.rectangle((a, y_w0, b, y_w1), fill=(255, 255, 255, 7 if k % 2 == 0 else 0))
        label = f"P{ph['index']}"
        if b - a > fk.text_w(d, label, f_small) + 14 * S:
            d.text((a + 8 * S, y_ph0), label, font=f_small, fill=T["accent2"] if not ph["silent"] else T["faint"])
    # silences
    for a, b in an["silences"]:
        xa, xb = X(a), X(b)
        d.rectangle((xa, y_w0, xb, y_w1), fill=(0, 0, 0, 90))
        for xx in range(int(xa) - (y_w1 - y_w0), int(xb), 14 * S):
            d.line((max(xa, xx), y_w1 - max(0, xa - xx), min(xb, xx + (y_w1 - y_w0)), y_w0 + max(0, xx + (y_w1 - y_w0) - xb)),
                   fill=(255, 255, 255, 14), width=S)
    # waveform (peak envelope) and RMS envelope
    wave_ = an["_wave"]
    cols = int(x1 - x0)
    mid = (y_w0 + y_w1) / 2
    amp = (y_w1 - y_w0) / 2 * 0.92
    if len(wave_):
        n = len(wave_)
        edges = np.linspace(0, n, cols + 1).astype(int)
        peak = np.array([np.abs(wave_[edges[i]:max(edges[i] + 1, edges[i + 1])]).max() for i in range(cols)])
        rms = np.array([np.sqrt(np.mean(wave_[edges[i]:max(edges[i] + 1, edges[i + 1])] ** 2)) for i in range(cols)])
        norm = max(1e-6, np.percentile(peak, 99.5))
        peak, rms = np.clip(peak / norm, 0, 1), np.clip(rms / norm, 0, 1)
        for i in range(0, cols, S):
            xx = x0 + i
            hp, hr = peak[i] * amp, rms[i] * amp
            d.line((xx, mid - hp, xx, mid + hp), fill=(110, 128, 150, 150), width=S)
            d.line((xx, mid - hr, xx, mid + hr), fill=(176, 194, 214, 230), width=S)
    # phrase boundaries
    for b in an["boundaries"]:
        xx = X(b["t"])
        col = (*T["accent"], 230) if b["kind"] == "novelty" else (*T["dim"], 200)
        d.line((xx, y_ph0, xx, y_w1), fill=col, width=2 * S)
    # hits
    for t, s in an["hits"]:
        xx = X(t)
        r = (5 + 5 * s) * S
        d.polygon([(xx, y_w0 + 6 * S), (xx + r, y_w0 + 6 * S + r), (xx, y_w0 + 6 * S + 2 * r), (xx - r, y_w0 + 6 * S + r)],
                  fill=(*T["red"], 235))
    # beat ruler
    d.line((x0, y_b0, x1, y_b0), fill=(255, 255, 255, 30), width=S)
    db_set = set(an["downbeats"])
    for t in an["beats"]:
        xx = X(t)
        if t in db_set:
            d.line((xx, y_b0, xx, y_b1), fill=(255, 255, 255, 150), width=S)
        else:
            d.line((xx, y_b0, xx, y_b0 + 12 * S), fill=(255, 255, 255, 60), width=S)
    step = 4 if len(an["downbeats"]) > 40 else 2 if len(an["downbeats"]) > 16 else 1
    for k, t in enumerate(an["downbeats"]):
        if k % step == 0:
            d.text((X(t) + 4 * S, y_b0 + 14 * S), str(k + 1), font=fk.font(13 * S, "mono"), fill=T["faint"])
    # onset strength curve
    if an["onsets"]:
        base = y_o1
        h = y_o1 - y_o0
        for t, s in an["onsets"]:
            xx = X(t)
            d.line((xx, base, xx, base - s * h), fill=(*T["teal"], 120 + int(110 * s)), width=S)
    d.text((x0, y_ol), "onset strength", font=f_small, fill=T["faint"])
    # time axis
    tick = 5 if dur <= 75 else 10 if dur <= 200 else 30
    t = 0
    while t <= dur + 1e-6:
        xx = X(t)
        d.line((xx, y_t, xx, y_t + 8 * S), fill=(255, 255, 255, 70), width=S)
        lab = fk.fmt_time(t, 0)
        lw = fk.text_w(d, lab, f_mono)
        lx_ = min(max(xx - lw / 2, x0), x1 - lw)
        d.text((lx_, y_t + 12 * S), lab, font=f_mono, fill=T["dim"])
        t += tick
    # cut plan
    if has_plan:
        plan = an["cut_plan"]
        f_id, f_d = fk.font(17 * S, "bold"), fk.font(14 * S, "mono")
        for k, sh in enumerate(plan["shots"]):
            a, b = X(sh["start"]), X(sh["end"])
            fill = (*T["accent"], 54) if k % 2 == 0 else (*T["accent"], 30)
            d.rounded_rectangle((a + S, y_c0, b - S, y_c1), radius=10 * S, fill=fill, outline=(*T["accent"], 120), width=S)
            if b - a > 30 * S:
                lab = fk.ellipsize(d, str(sh["id"]), f_id, b - a - 14 * S)
                d.text((a + 8 * S, y_c0 + 10 * S), lab, font=f_id, fill=T["text"])
            room = b - a - 14 * S
            for yy, txt, col in ((38, f"{sh['dur']:.2f}s", T["dim"]), (58, sh["cut"] if sh["cut"] != "end" else "", T["accent2"])):
                if txt and fk.text_w(d, txt, f_d) <= room:
                    d.text((a + 8 * S, y_c0 + yy * S), txt, font=f_d, fill=col)
            if sh["cut"] != "end":
                for yy in range(int(y_w0), int(y_o1), 12 * S):
                    d.line((b, yy, b, yy + 6 * S), fill=(255, 255, 255, 70), width=S)
        d.text((x0, y_cl), f"cut plan · {len(plan['shots'])} shots, every cut on the music", font=f_small, fill=T["faint"])
    # legend
    lx = x1
    ly = H - pad // 2 - 44 * S
    items = [("phrase boundary", T["accent"]), ("hit", T["red"]), ("onset", T["teal"]), ("downbeat", (220, 224, 230))]
    for lab, col in reversed(items):
        wlab = fk.text_w(d, lab, f_small)
        lx -= wlab
        d.text((lx, ly), lab, font=f_small, fill=T["dim"])
        lx -= 22 * S
        d.rounded_rectangle((lx, ly + 5 * S, lx + 14 * S, ly + 19 * S), radius=4 * S, fill=col)
        lx -= 30 * S
    img = img.resize((width, H // S), Image.LANCZOS)
    img.save(path, optimize=True)
    return path


# ---- report ------------------------------------------------------------------------------------------------------------

def summary(an):
    t = an["tempo"]
    lines = [f"{an['file']}: {fk.fmt_time(an['duration'])}, "
             + (f"{t['bpm']:.2f} BPM ({t['meter']}/4, confidence {t['confidence']:.2f}; also possible {t['alternatives']})"
                if t["bpm"] else "no steady pulse found"),
             f"  {len(an['beats'])} beats, {an['bars']} bars, {len(an['onsets'])} onsets, {len(an['hits'])} hits, "
             f"{len(an['silences'])} silences, {len(an['phrases'])} phrases"]
    if t.get("ambiguous_with"):
        lines.append(f"  note: the pulse is ambiguous between {t['bpm']:.2f} and {t['ambiguous_with']:.2f} BPM (a triplet or "
                     f"3-against-2 feel). Pass --bpm to pick the grid; cuts also land on accents and phrases either way.")
    if an["hits"]:
        lines.append("  hits:     " + ", ".join(f"{h[0]:.2f}s" for h in an["hits"]))
    if an["silences"]:
        lines.append("  silences: " + ", ".join(f"{a:.2f}-{b:.2f}s" for a, b in an["silences"]))
    rows = [[f"P{p['index']}", f"{p['start']:.2f}", f"{p['end']:.2f}", f"{p['end'] - p['start']:.2f}", p["bars"],
             f"{p['level_db']:.1f}", "silence" if p["silent"] else ""] for p in an["phrases"]]
    lines.append(fk.table(rows, ["phrase", "start", "end", "secs", "bars", "level dB", ""], "lrrrrrl"))
    plan = an.get("cut_plan")
    if plan:
        rows = [[s["id"], f"{s['start']:.2f}", f"{s['end']:.2f}", f"{s['dur']:.2f}", f"{s['target']:.2f}",
                 f"{s['dur'] - s['target']:+.2f}", s["cut"]] for s in plan["shots"]]
        lines.append("")
        lines.append(f"cut plan ({len(plan['shots'])} shots, {plan['start']:.2f}-{plan['end']:.2f}s):")
        lines.append(fk.table(rows, ["shot", "start", "end", "dur", "target", "delta", "cut on"], "lrrrrrl"))
    if an.get("intent"):
        it = an["intent"]
        lines.append("")
        lines.append(f"intent: shape r={it.get('shape_r')}  mean error={it.get('shape_mae')}  score={it['score']}")
        for h in it.get("hits", []):
            lines.append(f"  hit wanted at {h['want']:.2f}s -> nearest {h['got']}s ({h['off_ms']} ms)")
    return "\n".join(lines)


def strip(an):
    return {k: v for k, v in an.items() if not k.startswith("_")}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0], epilog=__doc__.split("\n", 2)[2],
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("audio", nargs="+", help="score file(s): wav, mp3, m4a, flac ...")
    p.add_argument("--json", help="write the analysis here (one input only)")
    p.add_argument("--png", help="write the picture here (one input only)")
    p.add_argument("--out-dir", help="write <name>.json and <name>.png for every input here")
    p.add_argument("--title", help="title on the picture (default: the file name)")
    p.add_argument("--meter", type=int, default=4, help="beats per bar (default 4)")
    p.add_argument("--bpm-hint", type=float, default=90.0, help="where to centre the tempo search (default 90, film-score tempi)")
    p.add_argument("--bpm", type=float, help="force the tempo (when the brief states it, or the pulse is ambiguous)")
    g = p.add_argument_group("cut plan")
    g.add_argument("--shots", type=int, help="suggest cut points for N equal-target shots")
    g.add_argument("--shotlist", help="suggest cut points for this shot list's shots (targets = their durations)")
    g.add_argument("--start", type=float, default=0.0, help="the film's first frame, in score seconds (default 0)")
    g.add_argument("--end", type=float, help="the film's last frame, in score seconds (default: where the music ends)")
    g.add_argument("--min-shot", type=float, default=1.5, help="shortest allowed shot in seconds (default 1.5)")
    g.add_argument("--max-shot", type=float, default=12.0, help="longest allowed shot in seconds (default 12)")
    g.add_argument("--snap", type=float, default=0.08, help="how strongly cuts prefer phrases over exact lengths (default 0.08)")
    g.add_argument("--no-scale", action="store_true", help="do not scale the shot list's durations to fill start..end")
    p.add_argument("--intent", help="YAML with points: [[t, level 0..1], ...], hits: [t, ...], length: s  (rank takes)")
    a = p.parse_args(argv)

    if len(a.audio) > 1 and (a.json or a.png):
        fk.die("with several inputs use --out-dir instead of --json/--png")
    targets = ids = prefs = pins = None
    if a.shotlist:
        sl = fk.load_yaml(a.shotlist)
        shots = fk.shots_of(sl)
        if not shots:
            fk.die(f"{a.shotlist} has no shots")
        targets = [float(s.get("dur", 0) or 0) for s in shots]
        ids = [str(s.get("id")) for s in shots]
        prefs = [s.get("cut_on") for s in shots]
        pins = [s.get("pin") for s in shots]
    elif a.shots:
        targets = [1.0] * a.shots
    intent = fk.load_yaml(a.intent) if a.intent else None

    results = []
    for path in a.audio:
        an = analyse(path, meter=a.meter, bpm_hint=a.bpm_hint, title=a.title if len(a.audio) == 1 else None, bpm_force=a.bpm)
        if targets:
            plan = plan_cuts(an, targets, ids, prefs, start=a.start, end=a.end, min_shot=a.min_shot, max_shot=a.max_shot,
                             snap=a.snap, scale=not a.no_scale, pins=pins)
            if plan is None:
                print(f"warning: no cut plan fits {len(targets)} shots between {a.min_shot}s and {a.max_shot}s in this span",
                      file=sys.stderr)
            an["cut_plan"] = plan
        if intent:
            an["intent"] = intent_match(an, intent)
        print(summary(an))
        print()
        js = a.json
        png = a.png
        if a.out_dir:
            os.makedirs(a.out_dir, exist_ok=True)
            stem = os.path.splitext(os.path.basename(path))[0]
            js, png = os.path.join(a.out_dir, stem + ".json"), os.path.join(a.out_dir, stem + ".png")
        if js:
            with open(js, "w") as f:
                json.dump(strip(an), f, indent=1)
            print(f"wrote {js}")
        if png:
            render_png(an, png)
            print(f"wrote {png}")
        results.append(an)
    if intent and len(results) > 1:
        print()
        print("takes ranked against the intent:")
        ranked = sorted(results, key=lambda r: -r["intent"]["score"])
        rows = [[k + 1, r["file"], r["intent"]["score"], r["intent"].get("shape_r", ""),
                 f"{r['intent'].get('hits_ok', '-')}/{len(intent.get('hits') or [])}", r["intent"].get("length_off_s", "")]
                for k, r in enumerate(ranked)]
        print(fk.table(rows, ["rank", "take", "score", "shape r", "hits", "length off s"], "rlrrrr"))
    return results


if __name__ == "__main__":
    main()
