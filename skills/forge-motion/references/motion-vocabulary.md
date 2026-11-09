# The motion vocabulary

Each shot's `motion` field is a plan, written in `shotlist.yaml` and carried out in post: in your editor, your
compositor, or code you own. `shotlist.py validate` checks the keys (an unknown key is a warning) and leaves the
values to people, so write them in the forms below and anyone who carries out the plan reads them the same way.

## Conventions

- Times are seconds from the shot's start.
- Positions are pixels of the 3840x2160 master frame. For any other size, scale them by `width / 3840`, so a 1080p
  preview uses the same numbers.
- Colours are `[r, g, b]` from 0 to 1. Thread colours are 0 to 255.
- `seed` is any whole number. Two layers with the same seed scatter the same way, so give each layer its own.
- A shot that needs nothing is `motion: none`. The motion gate wants every painted shot decided.

## The keys

| Key | Value | What it means |
| --- | --- | --- |
| `tin`, `tout` | `[fade, s]`, `[white, s]` or `[dissolve, s]` | from or to black; a white flash; a dissolve over the previous shot's last frame (in only). A bare word means 0.8 s. No key: a cut |
| `life` | a recipe, a layer, or a list of them | particles (below) |
| `ashc` | `[r, g, b]`, default `[0.62, 0.55, 0.5]` | tint of ash, flakes and streaks |
| `emberc` | `[r, g, b]`, default `[1.0, 0.62, 0.22]` | tint of embers |
| `fog`, `fogc` | `[strength 0..1, y start, y full, drift speed]`; `[r, g, b]`, default `[0.5, 0.45, 0.4]` | a band of soft noise drifting sideways, appearing from `y start` and full by `y full`, mixed toward `fogc` |
| `flick`, `fire` | amplitude; `[x, y, radius]` | firelight: brightness wavers around the point, with noise at about 3.5 and 9 Hz under a Gaussian falloff. 0.1 to 0.2 is a lamp or a match |
| `shim` | `[y full, y zero, 0, strength]` | heat shimmer: the image ripples, strongest at `y full`, fading to nothing at `y zero` |
| `sweep` | `[period s, band width px, intensity, 0]` | a diagonal band of warm light crossing the frame every 1.4 periods, added only to the highlights (luminance over 0.35), so it reads as light catching paint |
| `shake` | `[start, length, amplitude px]` | a camera shake that dies away as the square of the time left |
| `bolts` | `[s, s, ...]` | lightning: hard white flashes that die in a few frames |
| `crack` | `[start, length]` or `[start, length, x, y]` | glass cracking: near-straight radial fractures joined by ring fractures, growing from the point (default 2620, 980) over `length` |
| `threads` | `[{pts, t0, draw, w, col, wave, seed, motes, snap, fade}]` | gold threads of light (below) |
| `words` | `[{text, t0, x, y, size, write, t1, underline, halo}]` | handwritten words written into the scene (below) |
| `sand` | `{word, mat, t0, x, y, size, form, hold, blow, wind, n, seed, font}` | a word made of grains (below) |
| `title` | a string, or a `sand` mapping | the title, formed from grains (below) |
| `crop` | `[x0, y0, x1, y1]` | a reframe in the painting's own pixels, applied before the upscale |
| `note` | text | a note for people |

## life: particles

A **recipe** is a shorthand for a tested mix:

| Recipe | Form | Holds |
| --- | --- | --- |
| `SNOW` | `SNOW(n)`, `SNOW(n, [wx, wy])` | `n` snowflakes plus 12 soft flakes near the lens drifting at three times the wind (wind default 30, 55 px/s) |
| `EMB` | `EMB(n)`, `EMB(n, alpha)` | `n` embers rising across the whole width from below the frame, and drifting ash |
| `STARS` | `STARS()`, `STARS(n)` | twinkling stars (default 90) and a little slow dust |
| `GLINT` | `GLINT` | 110 glints, rising dust, a few soft flakes |
| `RAIN` | `RAIN` | 260 streaks and wind-blown spray |
| `GOLD` | `GOLD` | 220 gold embers rising across the width and 50 sparkles |

A **layer** names one particle system with its count and settings, for when no recipe fits:

| Layer | Form (defaults) | Use |
| --- | --- | --- |
| `ash` | `ash(n, wind=(18, 70), size=(3, 7), alpha=0.8)` | ash, dust, snow; wind in px/s; nearer particles fall faster and look bigger |
| `flakes` | `flakes(n, wind=(260, 90), size=(26, 70), alpha=0.28)` | large soft discs near the lens |
| `sparkles` | `sparkles(n, alpha=1.0, size=(10, 26))` | glints and stars that twinkle in place |
| `streaks` | `streaks(n, speed=2600, size=(90, 220), alpha=0.35)` | rain |
| `embers` | `embers(n, src=(1920, 2300), spread=220, rise=150, life=3.2, alpha=1.0)` | embers rising from a source, swaying, flickering out |
| `burst` | `burst(n=170, at=(1920, 1050), speed=(900, 2600), kind=2, size=(16, 56), alpha=0.55)` | thrown from a point at the shot's start, slowing, drifting down; `kind` is flakes (2), embers (1) or glints (3) |
| `moth` | `moth(at=(1920, 1080), span=160, beat=1.0)` | an ember moth made of particles, wings beating, shedding sparks |

```yaml
life: SNOW(700)                                                  # a recipe
life: GOLD                                                       # a recipe written bare (GLINT, RAIN, GOLD)
life: "embers(40, src=(1920, 1300), spread=120, rise=60, life=2.5)"  # one layer
life: [STARS(120), "moth(at=(1740, 900), span=220)"]             # a list of either
```

Every layer runs on its shot's own clock, so a `burst` is always thrown at its shot's start. An event that must land
on a hit belongs to a shot that starts on the hit. Embers flare with the music's pulse.

## Graphics, in master-frame pixels

- **`threads`:** `pts` (the curve's points; a smooth spline runs through them), `t0` (0), `draw` seconds to draw on
  (1.5), `w` width (10), `col` (`[255, 196, 110]`), `wave` sway in px (18), `seed`, `motes` along it (60),
  `snap: [time, u]` breaks it at fraction `u` and throws sparks, `fade: [start, length]`.
- **`words`:** `text`, `t0`, `x`, `y` (top left of the line), `size` (110), `write` seconds to write on (grows with
  the line), `t1` when it has faded out (default 0.25 s before the shot ends), `underline` (a word in the line),
  `halo` (1.0). One calligraphic script face, gold over a soft warm shadow, breathing with the music.
- **`sand`** and **`title`:** `word`, `mat` (gold, ember, ash, dust, bone, ink, rain, glint, star), `t0`, `x`, `y`
  (its centre), `size` (420; a title 300), `form` seconds to gather (1.7), `hold` (1.6), `blow` (1.6), `wind`
  (`[-1.0, -0.35]`), `n` grains (12000), `seed`, `font`. Grains gather into the word, hold, then blow away from the
  right edge first. A `title` written as a plain string takes `mat: gold, t0: 0.4, x: 1920, y: 1000, size: 300`.
- **Narration** is not a motion key. It is each shot's `narration` line, written on 0.5 s into the shot and held until
  0.6 s before its end, or a narration file in film time when a line must cross a cut (forge-sound).

## Music-driven effects

Bloom, ember flare, the threads' glow and the breathing of handwritten words follow the score, so a hit flares the
embers without a hand keyframe. Drive them from the score's level and pulse: the level from `loudness` in
beatmap.json (every half second) or an audio-to-keyframes pass in your compositor, the pulse from its `onsets` and
`hits`. Put shakes, flashes and transitions on the hits in beatmap.json: a shake's start is the hit's time minus the
shot's start.

## The finish, one for the whole film

- **Matched levels** on every painting before anything else: each painting's 0.5 and 99.5 percentile luminance
  mapped to shared black and white targets, blended 60% so the painting keeps its character. Paintings from separate
  generations then cut together.
- **The upscale:** 2K paintings to the master's size with Lanczos, then a sharpen only where there are edges, so flat
  colour stays clean. A `crop` comes before it. Keep the upscaled copies in a `4k/` folder: `archive.py` leaves any
  `4k/` folder out on purpose and says so in manifest.json, since it is rebuilt from the 2K paintings.
- **One finishing pass** over every shot: bloom from the highlights, grain, vignette. One setting for the whole film.
