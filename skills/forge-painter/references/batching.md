# Batches, names and versions

## Why four

Four paintings is enough to see a pattern (a face drifting, a colour creeping in) and few enough that one fix in
the prompts protects the rest of the film. Larger batches repeat the same mistake at full price.

## Worked batch plans

**The Lantern Moth (6 paintings, `production.yaml`).** Batch 1: s01 to s04 (11.0 credits); batch 2: s05 and s06
(5.5). Batch 1 is logged as painted before the prompt lint ran, a forced spend kept on purpose to show what the lint
prevents: s03's prompt had lost the moth's scale lock, and its QA notes send it for a repaint with the moth far too
small. Found in batch 1, the cause is fixed in the prompts before anything else is painted, and s03 alone is
repainted.

**The finish plan (13 paintings, `tests/fixtures/finish_plan.yaml`).**

1. Batch 1: s23, s25, s26, s27, the whole storm (one scene, one light, one weather: the paintings must cut together,
   so they are painted together).
2. Batch 2: s28, s29, s31, s34, the calm after it, the fire, the empty bell tower.
3. Batch 3: s39, s40, s41, s42, the turn and the way home.
4. Batch 4: s43 alone (the film's last image gets its own batch and its own attention).

Each batch is gated at 100% against the sheets before the next is painted: identity, every count, every scale lock,
the colour rules. Slips are fixed in post the same day.

## Naming

- `art/film/<id>_<slug>.png`: `s02_last_match.png`. The id first, so every tool finds it by prefix.
- Repaint: `_v2`, `_v3`. Fix in post: `_g` (a repaint's fix is `_v2_g`). The checking tools (ledger, contact sheet,
  archive) take the newest version in natural order, so they read the `_g` copy when one exists. To pick an older
  version, set `painting:` on the shot.
- Keep every version: a repaint is not always better, and the archive proves what was made.

## Logging

One `production.py spend` per batch, with the shot ids in the item: `--item "s01-s04 batch 1"`. A repaint is
its own line: `--item "s03 repaint (scale)"`.

## When a batch fails badly

If two of four fail QA for the same reason, stop. The cause is upstream (a sheet, the look, a ledger lock). Fix it
there, re-lint every remaining prompt, and only then continue.
