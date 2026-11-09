# The stages, one by one

Each stage: what goes in, the work, what comes out, and the gate `production.py gate <stage>` checks. A stage may
loop (paint and frame QA loop until every painting has a final verdict). Credits move only inside the stages that
list a spend, and only after every earlier gate has passed.

## brief

- **In:** an idea, a song, a poem, a myth; the credit ceiling.
- **Work:** create the folder from templates; fill production.yaml; write the logline.
- **Out:** production.yaml.
- **Gate:** title; format (width, height, fps); `budget.credits_available` > 0; `budget.approved_by`; deliverables.

## story (forge-story)

- **In:** the brief.
- **Work:** premise and thesis; the six engines; setups and payoffs; colour script; screenplay with timings; shot
  list sized to the credits; `shotlist.py validate`; `budget.py` until it fits.
- **Out:** story-bible.md, screenplay.md, shotlist.yaml.
- **Gate:** the three files exist; the shot list validates with no errors; the plan fits the credits minus reserve.
- **Spend:** none.

## style (forge-style-lock, then forge-frame-qa on the results)

- **In:** the bible (characters, world, colour script).
- **Work:** choose one model and setting; write the look and the avoid tail; write the character sheets' prompts
  and paint them; paint the empty set plates; paint 2 to 4 proof frames (the shots that must make people feel
  something); fill continuity.yaml (handles, anchors, scale locks, props, states, colour rules).
- **Out:** style-lock.yaml, art/sheets/, continuity.yaml, the proofs.
- **Gate:** style lock has looks and avoid; every character in the shot list has a sheet asset; `ledger.py check`
  passes; every sheet and proof in qa.yaml is accept or fix; signed off after reading them at 100%.
- **Spend:** sheets, plates, proofs.

## score (forge-score)

- **In:** the screenplay's timings and story hits.
- **Work:** the music brief and intent curve; generate (one cue, or two split at a silence); measure with
  beatmap.py; rank takes; plan cuts with `--shotlist` (cut_on and pin per shot); `shotlist.py retime`;
  `shotlist.py stats --beatmap` to show every cut on the music.
- **Out:** score-brief.md, intent.yaml, the audio, audio/beatmap.json and .png, the retimed shot list.
- **Gate:** brief exists; score exists; beatmap exists with a cut plan; every shot carries `cut:` (retimed).
- **Spend:** the score.

## paint (forge-painter and forge-frame-qa, in a loop)

- **In:** retimed shot list, style lock, ledger, sheets.
- **Work:** prompts per shot (`prompts/<id>.md`); `ledger.py prompts` lint; paint in batches of four; contact sheet;
  QA each painting (full view, 100% crops, `ledger.py palette`); verdicts in qa.yaml; fixes in post applied by
  forge-motion; repaints with the corrected prompt, QA again.
- **Out:** art/film/, prompts/, qa.yaml, out/contact_sheet.jpg.
- **Gate:** every prompt lints; every painting exists; every painting has a verdict; no repaint outstanding; every
  fix is `done: true`; `ledger.py palette` has no errors.
- **Spend:** paintings and repaints.

## motion (forge-motion)

- **In:** accepted paintings, the cut plan, qa.yaml fixes.
- **Work:** each shot's life planned in the `motion` field, which the editor carries out in post; `shotlist.py
  validate`; apply the QA fixes in post (saved as `_g` copies); build the 1080p preview with the score in your editor
  or compositor; stills at the story hits and a one-still-per-shot sheet (`contact_sheet.py build`).
- **Out:** the motion fields, the `_g` fixes, film/preview_1080p.mp4.
- **Gate:** every painted shot has a motion plan (or `motion: none`); the preview exists; signed off after watching
  it with sound.
- **Spend:** video clips, only if the plan has them.

## sound (forge-sound)

- **In:** the retimed shot list, the score, the narration lines.
- **Work:** narration timing in film time; sound design keyed to the shot table, built in a DAW or code you own;
  the loudness script; mix.
- **Out:** narration list, audio/full_mix.wav.
- **Gate:** no narration line reads too fast for its shot; the mix exists.

## deliver (forge-deliver)

- **In:** the shot list, the paintings and the mix.
- **Work:** export the 4K master from the editor and encode it (HEVC tagged `hvc1`); the 1080p copy with a two-pass
  linear loudnorm to -14 LUFS and the phone copy (ffmpeg); covers; book or making-of if planned; checks on the
  finished files (streams, loudness, sync at the story hits, contact sheet); the archive and its proof.
- **Out:** film/, MANIFEST.sha256, manifest.json.
- **Gate:** deliverables folder exists; the manifest exists; `archive.py verify` OK and the build recorded COMPLETE;
  signed off after watching the master on its target screen.

## retro (forge-director)

- **Work:** lessons.md, and each lesson's change made in the method (rule, rubric line, clause, price, gate).
- **Gate:** lessons.md written (non-empty).
