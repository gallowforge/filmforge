---
name: forge-style-lock
description: "FilmForge style lock: fixes one image model and setting, one look sentence (or two when the drawing itself carries the story), the palette and colour rules, the line, brush and lens language, the character-sheet specs with scale bars, and the prompt grammar every shot must follow, so every painting in a film or book matches. Use this skill whenever the user starts the visual side of a film, music video or picture book, wants consistent characters or one consistent look across many images, asks for a style bible, art direction, character sheets, turnarounds, a creature or material sheet, or says their images do not match each other."
---

# FilmForge Style Lock

A film made of separate generations only looks like one film if every image is made the same way: one model, one
setting, one look sentence pasted word for word, every character's sheet attached to every prompt, and a fixed
order for everything else. This skill writes `style-lock.yaml`, the character sheets and the character section of
`continuity.yaml`, then proves the lock with 2 to 4 proof frames before the paint stage may spend.

Paths: `scripts/`, `templates/` and `config/` below are folders inside this skill (the base directory shown when it loads), put there by `./install.sh`. Working from a clone of the repository, they are `tools/`, `templates/` and `config/` at its root.

## Step 1. One model, one setting

Choose once and never mix within a film. The default for painted films: GPT Image 2.5, high quality, 2K, 16:9
(2.75 credits a painting), upscaled to 4K in post. A picture book can use medium quality (about 1 credit) because
pages are seen smaller and still. Record it under `model:` with the price table's `model_id`.

If the look is undecided, paint the same proof frame in two or three candidate looks (cheap) and choose by eye at
100%. Do not lock on a thumbnail.

## Step 2. The look sentence

One sentence, opening every prompt word for word. It names the medium, the line, the colour, the texture and the
light, and it points at the references: "in exactly the style of the attached sheets". The Lantern Moth's lock (more
in references/looks.md):

> A frame from a hand-painted storybook film, in exactly the style of the attached sheets: soft gouache and
> watercolour on rough paper, confident brush-ink outlines, visible paper grain, deep night colours, light that
> comes only from lamps, embers and the sky.

A film or book may need two looks when its drawing carries the story: a living world in round, flowing lines and
full colour, and a frozen one in the same hand with every line ruled straight and a narrow grey palette, where
only the main characters keep their colours. Use a second look only when the change of drawing is part of the story;
it goes in `looks:` with its own name, and a shot picks it with `look:`.

## Step 3. The avoid tail

One line, closing every prompt word for word: what the model drifts into. The house tail:
`Avoid: 3D render, photorealism, text, watermark, extra fingers, distorted faces.` Add only what this look drifts
into (anime, plastic, CGI, a wrong medium). Negations that belong to one shot go in that shot's LOCKS slot.

## Step 4. Palette and colour rules

Name the swatches in `palette:` and the colour script per scene in `continuity.yaml` (`colour.script`). Turn every
colour rule of the story into a `forbid` rule with a prompt clause: the clause goes into every prompt the rule
covers, and `ledger.py palette` measures every painting against it. Example: The Lantern Moth allows no warm gold
before the lamp is lit (s05); every prompt before it carries "Absolutely no warm gold light anywhere in the frame.",
and `ledger.py palette` fails any painting in which that gold covers more than 2% of the frame.

## Step 5. Lens and composition language

For a painted film: paintings hold like film frames, so composition does the camera's work. Write the lens feel
(focal length, height), what never happens (no fisheye, no tilt), and the composition rules (subjects on thirds, a
quiet area for words when a shot has them).

## Step 6. Character sheets (templates/character-sheet.md)

One sheet per character, attached to every prompt that character appears in.

- Panels dead-on (front, back, face), flat shadowless light on a plain mid-grey field, so no lighting bakes in.
  Face and hand studies for stylised characters; expressions: neutral, the key emotion, its opposite.
- **A scale bar:** the character drawn beside every character or prop they share frames with, at true relative
  size. A companion drawn too small, frame after frame, is a repaint each time: scale must live on the sheet and in
  the ledger, never in hope.
- Non-human characters get a material sheet: what they are made of, a wrong-materials list ("embers, not fur, not
  glass"), how they move.
- Every shot prompt carries a relight clause: "relight to this scene; do not copy the sheet's flat light".

## Step 7. Handles, anchors, scale locks

For each character write into `continuity.yaml`: a **handle** (the visual name every prompt uses: "the girl in the
red knitted hood"), an **anchor** (the full look in one sentence, pasted word for word), a **scale** lock (a ratio
to something always nearby), and add the character's name to `names:`. Names never go into prompts: a model can
paint a name as text, and a name carries no visual information.

## Step 8. The prompt grammar (every painting, this order)

| # | Slot | What goes in |
| --- | --- | --- |
| 1 | LOOK | the look sentence, word for word |
| 2 | REFERENCES | what each attachment governs, in attach order; the relight clause |
| 3 | SHOT | framing, camera height, lens feel, who sits on which third |
| 4 | SUBJECT AND SCALE | each character's handle, anchor and scale lock; sizes as ratios; counts ("exactly one boat") |
| 5 | MOMENT | the one instant of the beat; emotion shown in face and body |
| 6 | SETTING | place, weather, time of day, what is in the background |
| 7 | LIGHT | direction, quality, temperature, and its source in the world |
| 8 | COLOUR | the scene's colour-script words |
| 9 | TEXT AREA | "keep the upper third quiet: pale sky for text" (only when words go there) |
| 10 | CONTINUITY | props and states, word for word from the ledger |
| 11 | LOCKS | forbidden-colour clauses, word for word; shot-specific negations |
| 12 | AVOID | the avoid tail, word for word |

`ledger.py prompts` checks slots 1, 4, 10, 11 and 12 mechanically before any credit is spent. Details and a full
example: references/prompt-grammar.md.

## Step 9. Prove the lock

Paint the sheets, the empty set plates, and 2 to 4 proof frames (the shots that must make people feel something).
Run forge-frame-qa on them at 100%. Repaint a sheet now rather than later: every painting inherits its faults. Then
`production.py signoff style --by <you> --note "<what you read>"`.

## Output format

1. `style-lock.yaml` (template): model, looks, default_look, avoid, grammar, references, lens, palette, max_chars.
2. One prompt per sheet and plate in `prompts/`, the sheets themselves in `art/sheets/`.
3. `continuity.yaml`: characters (handle, anchor, scale), names, colour script and forbid rules.
4. The proofs with their QA verdicts.

## Gate checklist

- [ ] One model and setting, recorded with its price-table id
- [ ] Look sentence(s) and avoid tail written; no names in either
- [ ] Every character: sheet with scale bar, handle, anchor, scale lock; name in `names:`
- [ ] Colour script and every colour rule as a `forbid` with a prompt clause
- [ ] Sheets, plates and proofs read at 100% and accepted
- [ ] Signed off

## Repair table

| Symptom | Fix |
| --- | --- |
| Paintings drift apart in style | The look sentence is not word for word in every prompt, or two models were mixed |
| Faces change between shots | The sheet was not attached, or the anchor was paraphrased; attach and paste |
| A character comes out the wrong size | No scale lock in the prompt, or no scale bar on the sheet |
| Names or words appear painted in the frame | A name or quoted text in the prompt; use handles; words are set in post |
| Flat, studio-lit scenes | The sheet's flat light was copied: add the relight clause |
| A forbidden colour creeps in | The clause is missing from LOCKS, or the rule's thresholds are too loose; measure with ledger.py palette |

## References

- `references/prompt-grammar.md`: each slot's rules with a full annotated prompt
- `references/looks.md`: worked looks and sheet prompts, and how to write a new one
