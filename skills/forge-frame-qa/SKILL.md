---
name: forge-frame-qa
description: "FilmForge frame QA: inspects every painting at full size against the character sheets and the continuity ledger, measures colour rules, palette and exposure with tools, scores it on a nine-criterion rubric and decides: accept, fix in post (naming the operation and its exact parameters), or repaint (with the root cause and the full corrected prompt). Use this skill whenever paintings, stills, keyframes, character sheets or book pages come back from an image model, when the user asks whether images are good, which ones need redoing, or wants a contact sheet, and always before spending credits on a repaint."
---

# FilmForge Frame QA

Nothing goes into the film on a thumbnail. Every painting is read at full size against its sheets, measured by the
tools, scored, and given one of three verdicts. The verdict always says what happens next and what it costs:
accept (free), fix in post (free, with the exact operation and numbers), or repaint (2.75 credits, with the
corrected prompt). In post means your editor, your compositor, or code you own.

Paths: `scripts/`, `templates/` and `config/` below are folders inside this skill (the base directory shown when it loads), put there by `./install.sh`. Working from a clone of the repository, they are `tools/`, `templates/` and `config/` at its root.

## The procedure

1. **Contact sheet** of the batch, to see it as a sequence (do neighbours cut together?):
   `python3 scripts/contact_sheet.py build art/film --shotlist shotlist.yaml --out out/contact_sheet.jpg`
2. **Full view** of each painting (read the image itself, not the sheet).
3. **100% crops** of what matters: faces, hands, the scale-critical subject, anything small.
   `python3 scripts/contact_sheet.py zoom art/film/s03_x.png --out-dir out/zoom --grid 2x2` or `--box x0,y0,x1,y1`.
   An image reader downsamples large images; crops show the real pixels.
4. **Measure** colour rules, palette and exposure:
   `python3 scripts/ledger.py palette continuity.yaml --paintings art/film --shotlist shotlist.yaml`
   It reports each painting's palette, its distance (delta E) from the scene's colour script, every forbidden-colour
   rule's share of the frame, and exposure jumps in stops between neighbours of one scene.
5. **Score** the rubric (below): nine criteria, 0 to 2.
6. **Decide** the verdict by the rules below.
7. **Write** the entry in `qa.yaml` (format below), then rebuild the contact sheet with `--qa qa.yaml` for badges.
8. **Report**: the verdict counts, each fix and repaint in one line, credits a repaint would cost.

## The rubric (templates/qa-rubric.md has the score anchors)

| Criterion | What you check |
| --- | --- |
| identity | faces and costume markers against the sheets |
| anatomy | hands, eyes, limbs on the focal subject |
| scale | every scale lock and every count (measure pixels in the crops) |
| style | the look lock: medium, line, colour, texture |
| colour | the colour script and forbidden rules (from ledger.py palette) and exposure against neighbours |
| continuity | every prop and state the ledger lists for this shot, and nothing outside its span |
| story | the beat reads in two seconds |
| composition | framing as listed, the eye lands on the subject, the text area quiet |
| clean | no painted text, watermark, smear or stray figure |

**Measuring scale:** in a crop, measure the subject and its reference in pixels and compare the ratio with the scale
lock. A moth whose lock asks for at least a palm, painted as a spark a fraction of the hand beside it, scores scale 0:
repaint.

## The verdict rules

- **accept**: no criterion at 0, total 15 of 18 or more, no measured violation.
- **fix**: every fault has a fix in post (table below) and nothing at 0 on identity, scale or story.
- **repaint**: identity, scale or story at 0; anatomy at 0 on the focal subject; style at 0; or three or more faults.

## Fix in post before credits

| Fault | Fix in post (`op` in qa.yaml) |
| --- | --- |
| one object in a wrong hue (a scarf that makes a side character read as the hero) | `recolour`: rotate one hue band inside one box to a new hue (box, band, new hue, saturation) |
| a forbidden colour leaking (gold before the lamp is lit, blue before the ending) | `recolour` the band to an allowed hue, or `blue` for blue: pull it toward silver, keeping 30% |
| one painting a stop or two too dark or bright on its own | matched levels, done for every painting; for a deliberate shift, `exposure` in stops of linear light |
| a stray figure in a clean area | `patch`: a shifted clean region, feathered over the stray |
| bad crop, tangent, wrong headroom | `crop`: the shot's `crop: [x0, y0, x1, y1]` in the painting's pixels (a motion field) |
| exposure or contrast off its neighbours | matched levels: each painting's 0.5 and 99.5 percentile luminance mapped to shared targets |
| soft detail | the 4K upscale: Lanczos with sharpening only on edges |
| a lifeless frame | motion in post (forge-motion), never a repaint |

A fix writes a new file beside the painting, `<id>_<slug>_g.<ext>`; the original is never touched. The checking
tools read the newest version of each shot by name, so they measure the `_g` copy. Each fix is re-measured and gets
`done: true` only when the measurement passes. Details and parameter meanings: references/code-fixes.md.

## Repaint: diagnose, then correct

Name the cause as a prompt slot or a reference: "scale lock missing from slot 4", "sheet attached in the wrong
order", "look paraphrased". Write the corrected prompt in full, check the budget, and hand it to forge-painter. If
the cause would hit other shots (a lock missing from the ledger), say so: it is a change to the method, not one repaint.

## qa.yaml entry format

The Lantern Moth's `qa.yaml` shows the format. Its notes are written as if the paintings existed; the example is
text only, so they show the decision, not a measurement you can repeat. Its s02 entry:

```yaml
  - shot: s02
    file: paintings/s02_last_match.jpg
    checked: [full frame, ledger palette]
    scores: {identity: 1, anatomy: 2, scale: 2, style: 2, colour: 0, continuity: 2, story: 2, composition: 2, clean: 2}
    total: 15
    max: 18
    measured: {no_gold_pct: 2.9, script_dE: 5}
    verdict: fix
    notes: >-
      A warm gold glow blooms from the match across the window and her hood (2.9% of the frame; the no-gold rule
      allows 2% before s05), and it turns the red hood orange. Lantern and its ember glow are present.
    fix:
      problem: gold glow from the match, hue 38 to 58, tinting the hood
      op: recolour
      params: {box: [560, 200, 1240, 820], hue_band: [38, 58], new_hue: 22, sat: 0.8}
      why_not_repaint: one hue band in one box; a recolour moves it to the moth's ember orange in minutes, for free
      verify: ledger.py palette shows no-gold under 2.0% on s02_last_match_g.jpg, and the hood reads red at 100%
      done: false
```

Once the recolour is saved as `s02_last_match_g.jpg`, `ledger.py palette` measures that copy; when it reads `ok`,
`done` becomes `true`. A repaint entry has `repaint: {cause, prompt_changes, credits, corrected_prompt}` instead of
`fix`.

## Worked findings

- **Scale (repaint):** a companion character drawn too small beside the hero, frame after frame. No fix in post can
  enlarge a painted subject convincingly, so each one is a repaint at its true size. The cause was upstream: no scale ratio
  on the sheets or in the prompts. Scale must live on the sheet (a scale bar) and in the ledger (a scale lock the
  lint enforces). The Lantern Moth's s03 shows the same fault: `ledger.py prompts` flags its missing scale lock
  before a credit is spent.
- **Colour (fix):** a colour the colour script forbids crept into a frame past its limit (The Lantern Moth's
  no-gold rule allows 2% of the frame before s05); a hue-band recolour inside a box, or a band pull toward silver
  for blue, fixed it in post.
- **Identity by colour (fix):** a side character's scarf matched the hero's colour, so he read as her; a hue-band
  recolour inside a box moved it.
- **Exposure (fix):** a painting well under its neighbour, past the ledger's 1.5-stop limit; matched levels or an
  exposure change in stops evens it, with no repaint.
- **Stray figure (fix):** an extra painted figure in a quiet frame is patched out from shifted clean regions.
- **A picture book's gate:** faces match the references; the right look and colour-script colours; the text area
  really calm; the page's motif present; it makes you feel the line of text it sits with. Fail one and the page is
  painted again.

## Never

- Accept from a thumbnail or a contact sheet alone.
- Repaint what post can fix, or "fix" in post what makes the story wrong.
- Pass a painting whose measured rule fails, even if it looks fine.

## Gate checklist (for the batch)

- [ ] Every painting read full size, with crops of faces, hands and scale-critical subjects
- [ ] `ledger.py palette` run; every error explained in a verdict
- [ ] Every painting has a qa.yaml entry with scores, verdict and the next action
- [ ] Contact sheet rebuilt with badges and looked at

## References

- `references/code-fixes.md`: each fix in post, its parameters, how to choose them, and how to verify
