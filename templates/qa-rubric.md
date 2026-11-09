# Frame QA rubric (forge-qa-rubric-1)

Every painting is read at full size against the sheets (contact_sheet.py zoom gives 100% crops), and measured
(ledger.py palette). Nine criteria, each 0, 1 or 2. Maximum 18.

| # | Criterion | 2 | 1 | 0 |
| --- | --- | --- | --- | --- |
| 1 | identity | faces and costume markers match the sheets | one marker off (a colour, a detail) | wrong face, wrong costume, or two characters merged |
| 2 | anatomy | hands, eyes, limbs clean | one small slip off the focal point | extra fingers, broken limbs or eyes on the focal subject |
| 3 | scale | every scale lock and count holds | slightly off, still reads | a subject at the wrong size or a wrong count (a companion drawn tiny, two where the ledger says one) |
| 4 | style | the look lock exactly | drifting (texture, line weight) | another medium (3D, photo, anime) |
| 5 | colour | colour script and forbidden rules hold (measured) | near the limits, or an exposure jump | a forbidden colour over its limit, or the wrong scene's palette |
| 6 | continuity | every prop and state in the ledger present and right | one minor slip | a prop or state missing, or present outside its span |
| 7 | story | the beat reads in two seconds | reads after a look | does not read, or tells the wrong beat |
| 8 | composition | framing as listed, text area quiet, eye lands on the subject | a tangent or crowded edge | cropped subject, text area busy |
| 9 | clean | no text, watermarks, smears, stray figures | a small blemish | painted text, a watermark, a stray figure on the subject |

## Verdict

- **accept**: no 0, total 15 or more, no measured violation.
- **fix**: every fault has a code fix in the table below (forge-frame-qa/references/code-fixes.md), and no 0 on
  identity, scale or story. Write the module, the call and the parameters; set `done: true` once applied and re-measured.
- **repaint**: a 0 on identity, scale or story; or anatomy 0 on the focal subject; or style 0; or three or more faults.
  Write the cause (which prompt slot or reference failed) and the full corrected prompt.

## Fixes in post before credits

Every fix writes a new file beside the painting (`<id>_<slug>_g.png`) and never touches the original.

| Fault | Fix in post |
| --- | --- |
| one object in the wrong hue | recolour one hue band inside a box to a new hue |
| a forbidden colour leaking | recolour it to an allowed hue, or pull stray blue toward silver |
| a painting off by a deliberate exposure | an exposure grade in stops of linear light, with a soft shoulder |
| a stray figure in a clean area | a patch from a shifted clean region, as a short script that keeps the original |
| bad crop, tangent, wrong headroom | the shot's `crop` in `motion` (the painting's pixels) |
| exposure or contrast off its neighbours | a matched grade: each painting's blacks and highlights mapped to shared targets |
| soft detail | the 4K upscale with edge-only sharpening |
| lifeless frame | motion in post (fog, particles, a light sweep), not a repaint |
