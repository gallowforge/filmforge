---
name: forge-painter
description: "FilmForge painter: writes every shot's image prompt from the shot list, the character sheets and the style lock, on a fixed twelve-slot order with continuity anchors (handles, anchors, scale locks, props, states, forbidden-colour clauses); keeps the continuity ledger; lints every prompt before a credit is spent; paints in batches of four and hands each batch to frame QA. Use this skill whenever the user wants image prompts for a film's shots or a picture book's pages, storyboard frames, keyframes for video, a repaint of a frame, or asks to keep characters, props and colours consistent from shot to shot."
---

# FilmForge Painter

You turn the shot list into paintings that belong to one film. Every prompt is assembled from locked parts (the
style lock, the ledger, the shot list), never improvised, so the same character is described with the same words in
every shot. The lint proves it before money moves.

Paths: `scripts/`, `templates/` and `config/` below are folders inside this skill (the base directory shown when it loads), put there by `./install.sh`. Working from a clone of the repository, they are `tools/`, `templates/` and `config/` at its root.

## Inputs

`shotlist.yaml` (retimed), `style-lock.yaml`, `continuity.yaml`, the sheets and plates in `art/sheets/`.

## Step 1. The ledger, shot by shot

For every shot, write its entry in `continuity.yaml`: which characters are in frame, which props (with their
holders), which states (a wound, soot, a bandage on one hand). Props and states carry spans (`from`, `until`).

```text
python3 scripts/ledger.py check continuity.yaml --shotlist shotlist.yaml
```

It fails on drift: a prop missing inside its span while its holder is in frame, a prop or state outside its span,
an unknown id, a character list that disagrees with the shot list. Fix the ledger before writing a prompt.

## Step 2. Write each prompt (`prompts/<id>.md`)

Follow the style lock's grammar, slot by slot (forge-style-lock, references/prompt-grammar.md):

1. LOOK: the look for this shot (`look:` in the shot list, else the default), word for word.
2. REFERENCES: one clause per attached asset, from `style-lock.yaml references:`, in the order you attach them;
   the relight clause.
3. SHOT: the shot list's framing, camera height, lens feel, positions on thirds.
4. SUBJECT AND SCALE: per character, handle + anchor + scale lock from the ledger; counts.
5. MOMENT: the shot's beat as one instant.
6. SETTING: place, weather, time of day, the background.
7. LIGHT: direction, quality, temperature, and its source in the world.
8. COLOUR: the scene's colour-script words.
9. TEXT AREA, when the shot has `text_area` or narration over it.
10. CONTINUITY: the ledger's props and states for this shot, word for word.
11. LOCKS: every `forbid` clause covering this shot, word for word; shot-specific negations.
12. AVOID: the tail, word for word.

The file format, exactly:

````text
# s02: the last match

Model: gpt-image-2.5, high, 2K, 16:9. Attach: sheet_girl, sheet_moth.

```
<the prompt, slots 1 to 12 as paragraphs>
```
````

The first fenced block is the prompt; everything else is notes for people.

## Step 3. Lint before spending

```text
python3 scripts/ledger.py prompts continuity.yaml --prompts prompts --style style-lock.yaml --shotlist shotlist.yaml
```

It fails a prompt that does not open with the look, does not end with the avoid tail, misses a character's handle
or scale lock, a prop or state anchor, a forbidden-colour clause, or contains a character's name. `production.py
spend` refuses paint-stage spends while it fails. On The Lantern Moth's prompts it finds exactly one fault:

```text
ERROR   s03: moth's scale lock is missing ("its wingspan equals a child's open hand, never smaller than a palm and never larger than a face")
prompts (6 checked): 1 error(s), 0 warning(s)
```

## Step 4. Paint in batches of four

- **Order:** sheets and proofs (style stage), then hero frames, then the rest scene by scene. Reuse shots and code
  shots (made in post) cost nothing; paint them never.
- **Batch:** four prompts, each with its references attached in the order its REFERENCES slot names them. Log the
  spend first: `production.py spend 11.0 --item "s05-s08 batch 2"`.
- **Files:** `art/film/<id>_<slug>.png` (`s03_moth_on_finger.png` style: id first, then a slug). A repaint is
  `<id>_<slug>_v2.png`; a fix in post is `<id>_<slug>_g.png`. The checking tools take the newest version by name
  (natural order), so a `_g` copy is the one they measure. To use an older version, set `painting:` on the shot.
- **After each batch:** forge-frame-qa reads every painting at full size before the next batch is painted. A fault
  found in batch one is fixed in the prompts of batch two before it repeats.

## Step 5. Repaints

A repaint comes from forge-frame-qa with its cause and a corrected prompt. Put the corrected prompt in
`prompts/<id>.md`, lint, log the spend, paint `_v2`, and send it back to QA. If the cause was in the ledger or the
style lock (a lock missing for everyone), fix it there and re-lint every prompt.

## Special cases

- **Picture-book pages:** name the layout (spread 3:2, page 3:4, vignette 1:1 on a transparent background) and the
  text area in every prompt. All words are set in the book, never painted.
- **Video keyframes:** paint the first frame (and the last when the move must end somewhere exact) through this same
  grammar; the motion prompt is a separate step, run only after the keyframe passes QA.
- **Key poses** (`poses: 2`): one prompt per pose, identical except the MOMENT slot, so they snap cleanly.
- **Plates:** empty locations, no characters, reused across shots; they carry the setting so prompts stay short.

## Output

- `prompts/<id>.md` for every painted shot, all passing the lint.
- `continuity.yaml` with every shot's entry, passing `ledger.py check`.
- `art/film/` paintings, named by id, ready for QA.

## Checklist before each batch

- [ ] `ledger.py check` passes
- [ ] `ledger.py prompts` passes for this batch
- [ ] References attached in REFERENCES order; the right sheet versions
- [ ] Spend logged; batch of four or fewer
- [ ] The previous batch has its QA verdicts

## Repair table

| Lint or QA finding | Which slot to fix |
| --- | --- |
| does not open with the style lock | 1: paste the look, unedited |
| handle or scale lock missing | 4: paste from the ledger; add the ratio to something in frame |
| prop or state anchor missing | 10: paste from the ledger |
| forbidden-colour clause missing | 11: paste the rule's `prompt` |
| uses a name | 4 and anywhere else: replace with the handle |
| wrong size or wrong count in the painting | 4: scale lock and an exact count; then the sheet's scale bar |
| subject lit flat | 2: the relight clause; 7: a light with a source |
| text or letters painted | 9 and 12: the text area is for words set in post; "text" in the avoid tail |

## References

- `references/batching.md`: batch planning, naming, versions, and a worked batch plan
