# Effects cookbook (starting points per mood)

Motion fields in master-frame (4K) coordinates, written as they go in a shot's `motion` (the forms are in
references/motion-vocabulary.md). These are starting points, not measurements: the first six rows are the plans in
The Lantern Moth's `shotlist.yaml`; the rest are untested starting values. Start from the closest mood, make a still
and a short loop in your editor or compositor, then tune to the painting.

## From The Lantern Moth

| Mood | Fields |
| --- | --- |
| Snow over a black sea at night (s01) | `tin: [fade, 1.5]`, `life: SNOW(700)`, `fog: [0.3, 1200, 2160, 0.04]`, `fogc: [0.45, 0.5, 0.55]`, `ashc: [0.8, 0.84, 0.9]` |
| A dying flame in a dark room (s02) | `life: EMB(60, 0.6)`, `flick: 0.12`, `fire: [2400, 1700, 900]`, `ashc: [0.8, 0.84, 0.9]` |
| A small warm light close to a face (s03) | `flick: 0.2`, `fire: [1920, 1300, 700]`, `life: "embers(40, src=(1920, 1300), spread=120, rise=60, life=2.5)"` |
| Snow beyond the glass, a choice made indoors (s04) | `life: SNOW(300, (80, 60))`, `flick: 0.1`, `fire: [1500, 1400, 800]` |
| Light blazes on the hit (s05) | `tin: [white, 0.4]`, `sweep: [3.0, 520, 0.35, 0]`, `life: GOLD`, `shake: [0.0, 0.4, 10]` |
| Dawn, the last image (s06) | `life: STARS(120)`, `fog: [0.2, 1400, 2160, 0.02]`, `tout: [fade, 2.0]` |

## Other moods (untested starting values)

| Mood | Fields |
| --- | --- |
| A quiet close-up in falling snow or ash | `life: SNOW(420, [20, 40])`, `ashc` pale, taken from the painting |
| Fire across the frame | `life: EMB(320)`, `flick: 0.09`, `fire: [1920, 1300, 2600]`, `shim: [2160, 300, 0, 0.8]`, `tin: [white, 0.8]` |
| Warm haze, moving into light | `life: EMB(140, 0.7)`, `fog: [0.35, 1000, 2160, 0.05]`, `fogc: [0.98, 0.7, 0.4]`, `tout: [white, 0.7]` |
| Falling or diving fast | `life: ["streaks(120)", "ash(300, wind=(0, -1500), size=(3, 7), alpha=0.6, seed=77)"]` |
| A reveal on a hit (feathers, sparks, shards) | `tin: [white, 0.3]`, `shake: [0.0, 0.55, 12]`, `life: ["burst(170, at=(1920, 1050))", "sparkles(60)"]` |
| Glass, mirrors, ice | `fog: [0.22, -200, 2160, 0.03]`, `fogc: [0.97, 0.93, 0.84]`, `sweep: [6.5, 260, 0.2, 0]`, `life: GLINT` |
| The glass breaks | the row above plus `crack: [3.2, 0.5, x, y]` from the point it is struck, `tout: [white, 0.5]` |
| Dust under a hot sky | `life: ["ash(500, wind=(90, 40), size=(3, 7), alpha=0.6)", "flakes(10, wind=(240, 80), alpha=0.2)"]`, `fog: [0.4, 900, 2160, 0.05]`, `fogc: [0.85, 0.62, 0.38]` |
| A heavy impact or a quake | `shake: [0.0, 0.9, 14]`, `life: "ash(900, wind=(40, 160), size=(4, 10), alpha=0.85)"`, `fog: [0.5, 1100, 2160, 0.12]` |
| Stillness after a loss | a strong `flick` (0.45) on a dying fire, low dark fog, slow ash, a few embers; `tin: [fade, 1.0]` out of black |
| A storm | `life: RAIN`, `bolts: [0.9, 1.05, 3.4]`, `shake: [0.9, 0.6, 8]` |
| Wonder | `tin: [white, 1.0]`, `life: STARS(120)`, warm low fog, a slow sweep `sweep: [9.0, 380, 0.12, 0]` |
| A thread between two characters | `threads: [{pts: [[900, 1300], [1900, 1000], [2900, 1250]], t0: 0.5, draw: 2.0}]`, with `snap: [4.0, 0.5]` if it breaks |
| A line written into the scene | `words: [{text: "...", t0: 1.0, x: 300, y: 260, size: 130}]`, in the painting's quiet area |
| A title that forms and blows away | `title: {word: "...", t0: 0.6, hold: 2.0, blow: 1.4}` on a `code` shot or over the last image |

## Rules of thumb

- One effect family per scene; change family when the scene changes. The audience reads the change as time passing.
- Embers rise from painted sources; fog colour comes from the sky in the painting; particle tint from its palette.
- Halve the particle count before adding a second system.
- Shakes under one second, on a hit. A white flash in, never a white flash out of a quiet shot.
- Long holds (7 s and up) need two layers moving at different speeds (slow fog, faster ash) or a slow sweep.
- `burst` and every layer run on the shot's own clock, so an event that must land on a hit belongs to a shot that
  starts on the hit.
