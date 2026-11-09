---
name: forge-motion
description: "FilmForge motion: plans each shot's life in post instead of credits (painted holds brought alive with drifting fog, ash, snow, rain, embers, glints, light sweeps, firelight flicker, heat shimmer, shake, lightning, glass cracks, transitions, golden threads, handwritten words and titles), writes every effect into the shot list's motion field in one exact vocabulary, applies frame-QA fixes in post and builds the preview the director signs off; decides when paid video is worth its credits. Use this skill whenever the user wants to animate stills or make paintings move, add particles, light or atmosphere, plan a motion or effects pass, build or change the edit, apply grade fixes, make a preview, or choose between AI video and motion in post."
---

# FilmForge Motion

Paintings hold like film frames; no zooms, no drift. Movement comes from inside the frame: particles, fog, flicker,
shimmer, light, all made in post for no credits. In post means your editor, your compositor, or code you own; the
tools' messages call it "in code". Paid video is kept for what post cannot do (real flight, a transformation that is
the film's climax). This skill fills each shot's `motion` field, applies the QA fixes and builds the preview the
director signs off.

Paths: `scripts/`, `templates/` and `config/` below are folders inside this skill (the base directory shown when it loads), put there by `./install.sh`. Working from a clone of the repository, they are `tools/`, `templates/` and `config/` at its root.

The `motion` field is the plan; the editor carries it out. Write it in the vocabulary below so the plan means one
thing to whoever builds the shot. Positions are pixels of the 3840x2160 master frame; scale them by `width / 3840`
for any other size, so a 1080p preview uses the same numbers.

## Step 1. Read the shot

For each shot: its beat, its scene's mood and colour script, its length after retime, the music under it (phrases,
hits in beatmap.json), what is already in the painting (fire, sea, sky, glass). Life must belong to the world of
the painting: embers rise from a fire that is painted there; snow falls where the sky is.

## Step 2. Choose its life (the vocabulary)

Every key `shotlist.py validate` knows. Times are seconds from the shot's start; positions are master-frame pixels;
colours are `[r, g, b]` from 0 to 1.

| Effect | Key | Value |
| --- | --- | --- |
| Transition in / out | `tin`, `tout` | `[fade, s]`, `[white, s]` or `[dissolve, s]` (dissolve: in only); a bare word means 0.8 s; default is a cut |
| Particles | `life` | a recipe, a layer, or a list of them (below) |
| Ash, flake and streak tint | `ashc` | `[r, g, b]`, default `[0.62, 0.55, 0.5]` |
| Ember tint | `emberc` | `[r, g, b]`, default `[1.0, 0.62, 0.22]` |
| Drifting fog band | `fog` + `fogc` | `[strength 0..1, y where it starts, y where it is full, drift speed]`; `[r, g, b]` |
| Firelight flicker | `flick` + `fire` | amplitude (0.1 to 0.2 for a lamp or a match); `[x, y, radius]` |
| Heat shimmer | `shim` | `[y full, y zero, 0, strength]` |
| Light sweep over the highlights | `sweep` | `[period s, band width px, intensity, 0]` |
| Camera shake | `shake` | `[start, length, amplitude px]`, dying away |
| Lightning | `bolts` | `[s, s, ...]`: hard white flashes |
| Glass crack | `crack` | `[start, length]` or `[start, length, x, y]` (from the point x, y; default 2620, 980) |
| Gold threads | `threads` | `[{pts: [[x, y], ...], t0, draw, w, col, wave, seed, motes, snap: [s, u], fade: [s, length]}]` |
| Handwritten words | `words` | `[{text, t0, x, y, size, write, t1, underline, halo}]` (x, y: top left of the line) |
| A word made of grains | `sand` | `{word, mat, t0, x, y, size, form, hold, blow, wind, n, seed, font}` (x, y: its centre) |
| Title | `title` | a string, or a `sand` mapping (defaults `mat: gold, t0: 0.4, x: 1920, y: 1000, size: 300`) |
| Reframe | `crop` | `[x0, y0, x1, y1]` in the painting's own pixels, applied before the upscale |
| A note for people | `note` | text |

Particles: recipes for tested mixes, `SNOW(n, wind)`, `EMB(n, alpha)` and `STARS(n)` called with numbers, `GLINT`,
`RAIN` and `GOLD` written bare; or one layer by name with its count and settings when no recipe fits: `ash` for ash,
dust and snow, `flakes` for large soft flakes near the lens, `sparkles` for glints and stars, `streaks` for rain,
`embers` rising from a source, `burst` thrown from a point at the shot's start, `moth` for an ember moth made of
particles. Every default and form: references/motion-vocabulary.md; starting points per mood:
references/effects-cookbook.md.

## Step 3. Let the music drive it

Bloom, ember flare, thread glow and the breathing of handwritten words follow the score's level and pulse, so a hit
flares the embers without a hand keyframe. Drive them from beatmap.json (`loudness`, `onsets`, `hits`) or an
audio-to-keyframes pass in your compositor. Put transitions and shakes on hits from beatmap.json (`shake` start =
the hit's time minus the shot's start).

## Step 4. Write the motion field

In `shotlist.yaml`, per shot. The Lantern Moth's lamp room by firelight, and its beam on the hit:

```yaml
    motion:
      life: EMB(60, 0.6)
      flick: 0.12
      fire: [2400, 1700, 900]
      ashc: [0.8, 0.84, 0.9]
```

```yaml
    motion:
      tin: [white, 0.4]
      sweep: [3.0, 520, 0.35, 0]
      life: GOLD
      shake: [0.0, 0.4, 10]
```

A shot that needs nothing gets `motion: none` (the gate wants every shot decided). Then
`python3 scripts/shotlist.py validate shotlist.yaml`: an unknown key comes back as a warning, so a typo is caught
before anyone builds the shot.

## Step 5. Apply the QA fixes

For every `fix` in qa.yaml, do its operation in post with its exact parameters (a recolour of one hue band in one
box, a blue pull, an exposure change in stops of linear light, a patch, or the shot's `crop`). Save the result beside
the original as `<id>_<slug>_g.<ext>` and never touch the original: the checking tools read the newest version of
each shot by name, so they measure the fixed copy. Re-measure with `ledger.py palette`, then set `done: true`. The
operations and how to choose their numbers: forge-frame-qa, references/code-fixes.md.

Then the finish every painting gets, in this order: matched levels (each painting's 0.5 and 99.5 percentile
luminance mapped to shared black and white targets, blended 60%), the upscale to the master's size (Lanczos, then a
sharpen only on edges), and one bloom, grain and vignette for the whole film.

## Step 6. Build the preview and look

In your editor or compositor, carry out the plan: every painting held for its retimed length, its `motion` built as
written, the narration set (forge-sound), the score or the mix under it. Export the 1080p preview to the path
`files.preview` names in production.yaml (`film/preview_1080p.mp4` by default). Then look at it four ways:

```text
ffmpeg -ss 24 -i film/preview_1080p.mp4 -frames:v 1 out/stills/s05.png        # a still at a story hit, named by shot
python3 scripts/contact_sheet.py build out/stills --shotlist shotlist.yaml --out out/preview_sheet.jpg
```

Stills at every story hit, one still per shot on the sheet (contact_sheet.py also flags a still whose aspect ratio
differs from the rest), a short loop of the moment that matters most, then the preview with sound. The master is
the same edit exported at 3840x2160 (forge-deliver).

Watch the preview with sound. Check the stills at every hit. Then the director signs off the motion stage.

## When to pay for video

Only when the motion is the story and post cannot fake it: real flight, a birth or transformation at the climax.
Cost it in budget.py (Kling 4.0: 16.25 credits per 5 s at 1080p, plus the keyframe painting); paint the keyframes
first and pass them through QA; draft cheaply where the model offers a draft and finalise one take. A paid clip is
cut into the edit like any other shot. Everything else is told in painted key poses that snap (`poses: 2`), the way
anime holds a pose.

## Output

- every shot's `motion` field (or `none`), passing `shotlist.py validate`
- the applied fixes (`_g` files, `done: true` in qa.yaml)
- `film/preview_1080p.mp4`, stills at the hits, a one-still-per-shot sheet

## Gate checklist

- [ ] Every painted shot has a motion plan or `motion: none`
- [ ] `shotlist.py validate`: no errors, and no unknown motion keys
- [ ] Every QA fix applied and re-measured
- [ ] The preview watched with sound; stills at every hit checked
- [ ] Signed off

## Repair table

| Symptom | Fix |
| --- | --- |
| It feels like a slideshow | Every hold needs one living layer tied to its world (particles, fog, flicker); vary them by scene |
| Effects look pasted on | Tint particles with `ashc` from the painting; emitters at painted sources; fog colour from the sky |
| Busy, noisy frames | Fewer particles (halve n), lower alpha; one effect family per scene |
| Shots from different generations do not cut together | Matched levels skipped or off for that painting: check its black and white points; one grade, grain and vignette for all |
| Effects ignore the music | Hits not used: place shakes, flares and transitions on beatmap hits; drive bloom and embers from the score |
| Text is hard to read | Move it to the painting's quiet area (`text_area`), size up, slow the write-on |
| validate warns about a motion key | A key outside the vocabulary: use the names in references/motion-vocabulary.md, or move the idea into `note` |

## References

- `references/motion-vocabulary.md`: every key, recipe and layer, their defaults, and the finish
- `references/effects-cookbook.md`: starting points per mood, in master-frame coordinates
