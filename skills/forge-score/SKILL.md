---
name: forge-score
description: "FilmForge score: writes the music brief from the screenplay (one palette, timestamped sections, named hits, written silences, explicit exclusions, cue splits at silences), then measures the generated score with beatmap.py (tempo, beat grid, downbeats, onsets, hits, phrases, silences, loudness), ranks takes against the story's intent curve, plans every cut onto the music with story hits pinned, and retimes the shot list frame-exactly. Use this skill whenever the user wants music for a film, a score or song prompt for ElevenLabs, Suno or Udio, to cut a film or slideshow to music, find the beats, phrases or drops in a track, sync cuts or effects to a song, choose between music takes, or says the edit feels off the music."
---

# FilmForge Score

Music comes first. The score is generated before the edit and measured beat by beat, and every cut is placed on
something the music does. The picture follows the music in a second way too: bloom, embers and text breathing are
driven in post by its measured level. This skill writes `score-brief.md` and `intent.yaml`, generates the score, measures
it, and hands back a retimed shot list whose cuts land within a frame of the music.

Paths: `scripts/`, `templates/` and `config/` below are folders inside this skill (the base directory shown when it loads), put there by `./install.sh`. Working from a clone of the repository, they are `tools/`, `templates/` and `config/` at its root.

## Step 1. The brief (templates/score-brief.md)

- **One palette sentence** shared by every cue: the lead instrument and its single theme, the key, the supporting
  instruments, the tempo if it matters, and the exclusions. Music models add trailer drums, braams, synth risers
  and choirs unless told not to: always write "No trailer percussion, no braams, no synths, no risers, no vocals".
- **Timestamped sections** taken from the screenplay's scene times: what the music does in each, in feelings and
  instrumentation ("0:12 to 0:23, the choice: plucked piano notes enter on the eighths, a small tender theme;
  warmth held close, then a pull of longing").
- **Named hits**: the story moments the picture must land on, with their times ("0:24: one deep warm hit as a
  lighthouse lamp blazes").
- **Written silences**: a silence is the strongest cut point there is, and the place to split cues.
- **Cue split:** when the film has a natural silence (a death, a time cut), split the score there into two cues:
  if one take comes out wrong, only that cue is redone, and the silence hides the seam.
- **Length:** the picture plus a tail of 2 to 4 seconds for the last chord.

Worked example (The Lantern Moth, one cue, 40 s, instrumental), from its `score-brief.md`: a palette sentence
(intimate cinematic score for a hand-painted storybook short; solo piano and a soft music box over warm low strings,
120 BPM, 4/4, A minor turning to A major; no trailer percussion, no braams, no synths, no risers, no vocals, no
choir); then the dark (0:00 to 0:12, a low string drone and one soft low pulse on every bar; cold and alone); the
choice (0:12 to 0:23, plucked notes and a small tender theme); a written silence at 0:23.5, "a held breath of
complete silence"; the hit at 0:24, "one deep warm hit as a lighthouse lamp blazes, then full warm major chords";
and a fading chord from 0:36 to 0:40. Three phrases for three scenes, one silence for the story's turn, one named
hit for the one moment the picture must land on. A longer film with a natural silence in the middle (a death, a
time cut) splits there into two cues, each with its own brief.

Write `intent.yaml` from the same sections: `points` (time, intended level 0 to 1), `hits` (the named hit times),
`length`.

## Step 2. Generate

Price it first (`budget.py`: 0.145 credits a second; The Lantern Moth's 40 s cue is 5.80). One take per cue by
default; two when the cue carries the film's climax and the credits allow (`takes: 2` on the asset). Log each with
`production.py spend`.

## Step 3. Measure

```text
python3 scripts/beatmap.py audio/score.mp3 --json audio/beatmap.json --png audio/beatmap.png --title "<Title>, cue 1"
```

Read the summary: tempo and confidence, beats, bars, hits, silences, the phrase table. Look at the PNG: waveform with
phrase bands, boundaries, hits, the beat ruler with bar numbers, onset strength, and (with a shot list) the cut plan.

- **Ambiguous pulse:** a triplet or 3-against-2 feel can score two tempi almost equally. beatmap says so and names
  both. Pass `--bpm` with the one the music is felt in (or the one the brief asked for). Cuts land on accents and
  phrases either way.
- **Precision:** onsets are refined in the time domain to the true attack (about 1.5 ms), beats snap to them, and a
  silence ends exactly on the attack that ends it.

Check the measurement against the brief. For The Lantern Moth that means: three phrases with boundaries near 0:12
and 0:24, a silence from about 0:23.5 to 0:24, the named hit at 0:24, and the tail's silence from about 0:36. A
take that misses the hit or fills the silence fails the brief, however good it sounds.

## Step 4. Choose the take

```text
python3 scripts/beatmap.py take1.mp3 take2.mp3 --intent intent.yaml --out-dir out/takes
```

Each take gets a shape correlation (measured level against the intended curve), its named hits found within the
tolerance, and its length error; the ranking prints at the end. Listen to the top take at the hits before choosing.

## Step 5. Plan the cuts and retime

In the shot list, give each shot a `cut_on` (phrase, downbeat, beat, hit, silence, accent, free), and `pin: <seconds>`
on each shot that must start on a named hit. Then:

```text
python3 scripts/beatmap.py audio/score.mp3 --shotlist shotlist.yaml --json audio/beatmap.json --png audio/beatmap.png
python3 scripts/shotlist.py retime shotlist.yaml --beatmap audio/beatmap.json --in-place
python3 scripts/shotlist.py stats shotlist.yaml --beatmap audio/beatmap.json
```

The planner chooses one cut point per shot change so each hold stays near its intended length and each cut lands on
the strongest music event nearby (phrase > silence > hit > downbeat > accent > beat), pins held within 120 ms, holds
between `--min-shot` and `--max-shot`. `--start` and `--end` set the film's span in the score (the end defaults to
where trailing silence begins). Retime rounds every cut point (not every duration) to a frame, so nothing drifts.
`stats` must show every cut on the music within 60 ms.

The Lantern Moth's shot list shows what a retime writes. Its six provisional 6 s holds carry `cut:` fields: s01
ends on a hit, s02 on a phrase, s03 on a downbeat, s04 on the held breath (`silence`), s05 on a downbeat, and s06
runs to where the tail's silence begins (6.1667 s, rounded to a frame, so the film is 36.17 s). On a longer film
what remains is taste in how long each hold breathes: review the plan, move a cut to a neighbouring phrase where the
story wants it, and re-run stats.

## Output format

- `score-brief.md` and `intent.yaml`
- `audio/beatmap.json` (schema: references/beatmap-json.md) and `audio/beatmap.png`
- the retimed `shotlist.yaml` (each shot's `cut:` says what it landed on)
- a report: tempo, phrases, the hits, cuts on the music N of N, the take chosen and why

## Gate checklist

- [ ] Brief has palette, sections, hits, silences, exclusions, cue split, length
- [ ] Score measured; the PNG looked at
- [ ] Ambiguous tempo resolved with `--bpm` (or confirmed irrelevant)
- [ ] Story hits pinned; every shot retimed; `stats` shows every cut on the music
- [ ] Spend logged

## Repair table

| Symptom | Fix |
| --- | --- |
| Cuts feel a beat late or early | The grid is at the wrong tempo level: `--bpm` with the felt tempo, re-plan |
| No cut plan fits | Holds too long or short for the span: widen `--min-shot`/`--max-shot`, or adjust the shot list |
| A story moment misses its music | Add `pin:` on the shot; if no music event is near, the brief's hit time was wrong: regenerate or move the moment |
| Music swallows the narration | The brief needs space: fewer instruments under narrated passages; forge-sound ducks the rest |
| Two takes both wrong at one section | Split the cue there next time; regenerate only that cue |
| The music has trailer drums or a choir | The exclusions are missing from the palette sentence |

## References

- `references/beatmap-json.md`: every field of the analysis JSON
- `references/cutting-to-music.md`: cutting rules, music-driven picture, and the sync check on the finished file
