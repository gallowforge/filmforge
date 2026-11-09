---
name: forge-story
description: "FilmForge story: turns a premise, song, poem or myth into a story bible, a timed screenplay and a shot list sized to a credit budget, written as YAML the tools validate, price and cut to music. Use this skill whenever the user has an idea to turn into a short film, painted film, music video or picture book; wants a premise, logline, story bible, beat sheet, screenplay, storyboard or shot list; asks how many shots or how long a film their credits buy; or wants an existing story tightened so it lands, even if they never say 'shot list'."
---

# FilmForge Story

Story comes first: nothing is painted, scored or bought until the film exists on paper, timed to the second and
priced to the credit. This skill writes three files: `story-bible.md`, `screenplay.md`, `shotlist.yaml`
(templates in `templates/`). The stage gate passes when the shot list validates and its plan fits the credits.

Paths: `scripts/`, `templates/` and `config/` below are folders inside this skill (the base directory shown when it loads), put there by `./install.sh`. Working from a clone of the repository, they are `tools/`, `templates/` and `config/` at its root.

## Step 1. Premise and thesis

- **Premise:** one sentence, who wants what and what it costs them.
- **Thesis:** one sentence the ending proves.

If either takes two sentences, the story is not found yet. Keep working here; everything downstream inherits it.

## Step 2. The heart: six engines

Great short animated films do the same few things. Fill every row; a film that cannot fill one is missing a part.

| Engine | Test |
| --- | --- |
| One relationship | Two characters the film is about. Everyone else serves them. |
| One flaw, with a price | The hero's flaw costs someone something real, on screen. |
| One choice that breaks your heart | The hero gives up what they wanted, by their own hand. |
| One twist | What the audience believed is not what is true, and the truth was planted. |
| One mirror | An image that lies early and tells the truth late. |
| One image, twice | One composition opens and closes the film, changed by everything between. |

Worked example (The Lantern Moth, the repository's text example, 36 s): one relationship, a lighthouse girl and the ember
moth, the first warm thing she has held all winter. One flaw with a price: she wants to keep the warmth, and while
she cups it the boat drifts toward the rocks. One choice: she opens her hands toward the dead lamp and lets the moth
go into it. One twist: the moth does not burn out; at dawn the lamp glass is covered in a hundred small ember moths.
One mirror: her reflection in the lamp lens, alone and lit by the moth, then lost in the beam's light. One image
twice: the dead lighthouse at night opens the film, the warm lighthouse at dawn closes it.

## Step 3. Setups and payoffs

A table where nothing appears only once. Each row: what is planted (shot), what it pays off (shot). If an image has
no payoff, cut it or give it one. Rows from The Lantern Moth: the dead lamp in the first frame / the same frame at
dawn, the lamp warm; the empty lantern she carries everywhere / it stays behind on the floor once the moth is gone;
one moth on her fingertip / a hundred moths on the glass; no warm gold anywhere / the beam blazes gold.

## Step 4. The colour script

One row per scene: time range, 3 to 5 colours, the feeling. Add the rules that carry meaning ("no warm gold before
the lamp is lit", "the only warm colour before the lamp is lit is the moth's orange", "no blue in the sky until
dawn"). Rules become `forbid` entries in the continuity ledger, measured on every painting.

## Step 5. The screenplay, timed

- Scenes with time ranges; shots with start, length, framing, and only what a camera can photograph, in the present
  tense. A beat that cannot be photographed is not in the film.
- Under each scene, what the music does (instruments, energy, a named hit, a written silence). The Lantern Moth's
  screenplay puts "a low drone, a soft kick on each bar. Cold and alone." under The Dark, and "the hit at 0:24,
  then warm full chords" under The Light. If the music already exists (a song, a piano piece), the story walks
  through its sections in order, one mood line under each, and the shots or pages turn with it.
- Words: say only what the pictures cannot (who is speaking, why they go, who dies, what the end means). Wordless
  is a strength: it plays to anyone anywhere. Narration is handwritten on screen or spoken; either way it is timed
  in film time later (forge-sound).

## Step 6. Size the film to the credits

```text
paint_credits = credits x 0.95 - sheets - plates - proofs - score
paintings     = floor(paint_credits / (price x 1.3))        # 1.3 = the repaint buffer
runtime       = paintings x average hold                     # painted holds: 4 to 6 s each
```

Worked example: 70 credits (66.5 spendable), two sheets and one plate (8.25, about 11.8 with buffers), a 64 s score
(9.28): about 45.4 left for paintings, so 12 paintings at 2.75 with the buffer: a 60-second film at 5 s a hold.
The Lantern Moth runs 6 shots in 36 s; `budget.py` plans it at 39.08 of 66.50 spendable, with 27.42 to spare after
what is already spent: room for 7 more paintings with retakes.

Rules while sizing:

- Hero frames first: name the 2 to 4 shots that must make people feel something. They are painted as proofs before
  everything else.
- Real motion only where nothing else works (flight, a transformation that is the climax). Elsewhere, key poses
  that snap (`poses: 2`) and life in post.
- Reuse a plate or a painting where the story allows (`kind: reuse`): the image-twice engine is free.

## Step 7. The shot list

Write `shotlist.yaml` (schema: references/shotlist-schema.md). Each shot: id, scene, dur, kind, framing, beat,
characters, refs (every character's sheet), cut_on, and where the music brief names a story hit, `pin`. Then:

```text
python3 scripts/shotlist.py validate shotlist.yaml
python3 scripts/budget.py shotlist.yaml --production production.yaml
```

Iterate until validate shows no errors and budget says FITS. Warnings to act on: painted holds under 1.5 s or over
10 s, narration faster than 2.4 words a second, a character in frame without their sheet attached.

## Output format

1. `story-bible.md`: premise, thesis, the six engines, world, characters (handle, look, want, movement), props and
   states, setups and payoffs, colour script, production rules.
2. `screenplay.md`: scenes with times, music notes, shots with start, length, framing, action, words.
3. `shotlist.yaml`: validates, fits.
4. A short report: runtime, shot count, credits planned versus available, the hero frames, the one risk.

## Gate checklist

- [ ] Premise and thesis are one sentence each
- [ ] All six engines filled; every setup paid off
- [ ] Colour script with its rules
- [ ] Every shot photographable; every beat under its music
- [ ] `shotlist.py validate`: no errors
- [ ] `budget.py`: FITS, reserve untouched
- [ ] Hero frames named

## Repair table

| Symptom | Fix |
| --- | --- |
| The ending does not land | The choice is missing or made for the hero; or the twist was not planted. Re-check engines 3 and 4 |
| It feels like a slideshow | Beats describe states, not actions; rewrite each beat as something changing in the frame |
| Over budget | Fewer, longer holds; reuse plates; key poses instead of video; then cut priority 3 shots |
| Narration warnings | Fewer words, or let the line run across the next cut (narration lives in film time) |
| Characters do not read as the same people | Not a story fault: forge-style-lock (sheets, anchors, scale locks) |

## References

- `references/story-engine.md`: the six engines in depth, with The Lantern Moth broken down
- `references/shotlist-schema.md`: every shot-list field, its values and which tool reads it
