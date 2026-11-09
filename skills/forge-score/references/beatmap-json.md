# beatmap.json

Written by `beatmap.py --json`. Times are seconds from the start of the audio file, rounded to the millisecond.

| Field | Meaning |
| --- | --- |
| `tool`, `version` | "beatmap", 1 |
| `file`, `title` | Audio file name and the title used on the picture |
| `duration` | Length in seconds |
| `sample_rate`, `analysis_fps` | Analysis rate (22050 Hz) and frames per second of the analysis (about 86) |
| `tempo.bpm` | Tempo of the beat grid (median beat interval) |
| `tempo.acf_bpm` | The autocorrelation estimate before tracking |
| `tempo.confidence` | 0 to 1: how far the winner stands above the field |
| `tempo.alternatives` | Half, double, 2/3, 3/2 and the best rival tempo |
| `tempo.ambiguous_with` | The rival when it scores within 5% (a triplet or 3-against-2 feel); otherwise null |
| `tempo.forced` | True when `--bpm` set it |
| `tempo.meter`, `tempo.downbeat_confidence` | Beats per bar; how clearly beat one stood out |
| `beats` | Every beat time, snapped to the refined attack within 40 ms |
| `downbeats`, `bars` | Every bar's first beat; the count |
| `onsets` | `[time, strength 0..1]` for every attack, refined to the true attack (about 1.5 ms) |
| `hits` | `[time, strength]`: strong attacks with a real jump in level, or attacks right after a silence |
| `silences` | `[start, end]`: spans far below the piece's loud parts; ends snap to the attack that ends them |
| `boundaries` | `{t, strength, kind, on_downbeat}`: phrase boundaries; kind is novelty, silence-start or silence-end |
| `phrases` | `{index, start, end, beats, bars, level_db, silent}` between boundaries |
| `novelty` | `[beat time, novelty 0..1]`: the structure-change curve the boundaries come from |
| `loudness` | `{hop: 0.5, db: [...]}`: smoothed level every half second |
| `cut_plan` | With `--shots` or `--shotlist`: `{start, end, cost, snap, shots: [{id, start, end, dur, target, cut}]}` |
| `intent` | With `--intent`: `{shape_r, shape_mae, hits: [{want, got, off_ms}], hits_ok, length_off_s, score}` |

## How it is measured

- Mono, 22050 Hz; 2048-sample frames every 256 samples; 40 mel bands from 30 Hz to 8 kHz.
- Onset strength: positive spectral flux of the log-mel energies. Bass flux (bands under 200 Hz) helps find beat one.
- Tempo: autocorrelation of the onset envelope, scored with its multiples and a log-normal prior centred on 90 BPM
  (film-score tempi; `--bpm-hint` moves it), refined by parabolic interpolation.
- Beats: dynamic programming (each beat is the best onset about one period after the last; Ellis 2007).
- Phrases: Foote novelty on a beat-synchronous self-similarity matrix (two-bar checkerboard kernel), peaks snapped to
  a downbeat within half a beat, plus silence edges.
- Onset refinement: the steepest rise of a 1.5 ms level envelope of the high-passed signal within 50 ms.
- Cut plan: dynamic programming over candidate cut points; cost = sum of squared relative length errors minus
  `snap` x the weight of each cut's music event; pins are hard constraints.
