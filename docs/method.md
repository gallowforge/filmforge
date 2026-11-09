# The method

Seven stages, each with its rule. Only two of them spend credits (the paintings and the score); the rest is post, measurement and paper. Each rule below says what it is, why it saves credits, what enforces it, and how it shows in [The Lantern Moth](../examples/the-lantern-moth/), the repository's worked example in text. Every tool output quoted here is what the tools print when run on that folder.

## 1. Story first

**Rule.** The whole film exists on paper before a credit is spent: a story bible with the six engines, a timed screenplay, and a shot list priced against the credits.

**Why it saves credits.** A painting made for a story that later changes is a painting thrown away, and shots painted for different versions of the plot never cut together. Paper is free.

**Enforced by.** The story gate: the bible, screenplay and shot list exist, `shotlist.py validate` finds no errors, and `budget.py` says the plan fits inside the credits minus the reserve. `production.py spend` refuses any spend while an earlier gate is open. Skill: forge-story.

**On The Lantern Moth.** Six shots validate, and the plan fits with room to spare:

```text
ok: 6 shots, no problems

stage   base  with retakes
-----  -----  ------------
style   8.25         11.82
score   5.80          5.80
paint  16.50         21.45
total  30.55         39.08

credits 70.00, reserve 5% -> spendable 66.50; spent so far 33.30, left 36.70
FITS: 27.42 credits to spare (room for 7 more paintings with retakes)
```

## 2. One style lock

**Rule.** One image model and setting per film. One look sentence opens every prompt word for word and one avoid tail closes it. Every character has a sheet with a scale bar, attached to every prompt they appear in, and a handle, anchor and scale lock in the continuity ledger. Every prompt is linted before it is painted.

**Why it saves credits.** Every drift (a face that changes, a creature that shrinks, a colour that creeps in) is a repaint at full price. A lint is free and runs before the money moves.

**Enforced by.** The style gate: a look and an avoid tail, a sheet for every character, `ledger.py check` passing, sheets and proofs accepted at 100% and signed off. In the paint stage, `ledger.py prompts` checks the look, every handle, scale lock, prop, state and forbidden-colour clause, and the tail; `production.py spend` refuses paint-stage spends while it fails. Skills: forge-style-lock, forge-painter.

**On The Lantern Moth.** The ledger is consistent, and the lint catches the one prompt that lost its scale lock:

```text
continuity: ok

ERROR   s03: moth's scale lock is missing ("its wingspan equals a child's open hand, never smaller than a palm and never larger than a face")
prompts (6 checked): 1 error(s), 0 warning(s)
```

Painted from that prompt, the moth comes out a spark beside her hand instead of the size of her palm. The lint catches it before the credit is spent; frame QA would catch it after, as a repaint.

## 3. Music first

**Rule.** The score is generated and measured before the first cut. Every cut lands on something the music does (a phrase, a silence, a hit, a downbeat), and the story's hits are pinned to the music's.

**Why it saves credits.** The music sets the holds and the pacing before paintings are bought, so no painting is bought for a shot the music has no room for. A score split at a silence means one bad take costs one cue, not the film.

**Enforced by.** The score gate: the brief and the score exist, `beatmap.py` has measured it and made a cut plan, and every shot carries the `cut:` that `shotlist.py retime` writes. `shotlist.py stats` then shows every cut against the music. Skill: forge-score.

**On The Lantern Moth.** The score brief asks for one cue with a held breath before the hit at 24 s, where the lamp lights. After `shotlist.py retime`, every shot in `shotlist.yaml` carries what its cut landed on: a hit, a phrase, a downbeat, the silence, a downbeat, the end.

## 4. Motion in post

**Rule.** Paintings hold like film frames: no zooms, no drift. Everything that moves (fog, snow, embers, glints, light sweeps, firelight, shimmer, shake, lightning, cracks, threads, words, titles) is added in post, planned in each shot's `motion` field and carried out in your editor or compositor. Paid video only where the motion is the story and post cannot fake it.

**Why it saves credits.** A video clip costs 16.25 credits per 5 seconds at 1080p (`config/prices.yaml`), plus the keyframe painting under it, and looks like a different film beside the paintings. Post costs nothing, works at any size and changes in seconds.

**Enforced by.** The motion gate: every painted shot has a motion plan or `motion: none`, a preview exists, and it was watched with sound before sign-off. `shotlist.py validate` flags motion keys that are not in the vocabulary. When a plan is over, `budget.py`'s first suggestion turns video shots into painted key poses. Skill: forge-motion.

**On The Lantern Moth.** No shot is video. The beam's whole life is four lines in `shotlist.yaml`:

```yaml
    motion:
      tin: [white, 0.4]
      sweep: [3.0, 520, 0.35, 0]
      life: GOLD
      shake: [0.0, 0.4, 10]
```

## 5. Fix in post

**Rule.** Fix a slip in post before spending credits. Colour, a leak of a forbidden colour, an exposure jump, a crop: post. A wrong face, hand, pose, size or count: repaint, with the cause named and the full corrected prompt.

**Why it saves credits.** A repaint costs 2.75 credits and may not match its neighbours. A fix in post is free, exact, kept beside the original, and runs again in seconds.

**Enforced by.** Frame QA's verdict in `qa.yaml` for every painting (accept, fix with the exact call, or repaint), and the paint gate: no repaint outstanding, every fix applied, and `ledger.py palette` free of errors. Skill: forge-frame-qa.

**On The Lantern Moth.** `qa.yaml` shows the three decisions the method allows. s02 lets warm gold from the match leak into a scene that forbids it before the lamp is lit: fix in post, one hue band moved to the moth's ember orange inside one box, then re-measured with `ledger.py palette`. s04 sits two stops under its neighbour: fix in post, an exposure grade in stops of linear light. s03 lost the moth's scale lock, and post cannot draw a subject bigger: repaint, with the cause written down and the full corrected prompt beside it. Only that one costs a credit.

## 6. Deliver everything

**Rule.** One source, every version. The master, the posting copy, the phone copy and the covers all come from the same paintings, shot list and mix, and each one is measured: streams, loudness, sync at the story hits, the first and last frames.

**Why it saves credits.** A new version is an export, not a production. Nothing in delivery is generated.

**Enforced by.** The deliver gate: the deliverables exist, the archive verifies and was built COMPLETE, and the master was watched on its target screen before sign-off. Skill: forge-deliver, which carries the exact encode settings.

**The settings.** A 4K master in HEVC tagged `hvc1` for Apple players. A 1080p posting copy in H.264 High at CRF 16, its mix normalised to -14 LUFS and -1.5 dBTP by a two-pass linear loudnorm:

```bash
ffmpeg -i mix.wav -af loudnorm=I=-14:TP=-1.5:LRA=18:print_format=json -f null -          # pass 1: measure
ffmpeg -i master.mp4 -i mix.wav -map 0:v -map 1:a -vf scale=1920:1080:flags=lanczos \
  -c:v libx264 -preset slow -crf 16 -profile:v high -pix_fmt yuv420p \
  -af "loudnorm=I=-14:TP=-1.5:LRA=18:measured_I=...:measured_TP=...:measured_LRA=...:measured_thresh=...:offset=...:linear=true" \
  -c:a aac -b:a 320k -movflags +faststart film_1080p.mp4                                  # pass 2: apply
```

A 720p phone copy around 1 Mbps that sends in a chat app without recompression. Then sync is checked on the finished file at every story hit: the picture change against the sound's onset, within one frame (42 ms at 24 fps).

## 7. Archive with proof

**Rule.** Everything that made the film goes into one folder: the state file, the story, the prompts, every painting and version, the score and its measurement, the code, the mixes, the deliverables, the lessons. Every file is hashed, what was left out is written down with the reason, and every copy is proven byte for byte.

**Why it saves credits.** Months later, the prompt that made a frame or the call that fixed it is the thing you need. Without it, the frame is painted again.

**Enforced by.** `archive.py build` writes a `sha256sum`-compatible manifest and reports COMPLETE only when every required file is there and every painted shot has its painting; `archive.py verify` re-hashes it later; `archive.py compare` proves a copy. The deliver gate needs a verified, COMPLETE archive. Skill: forge-deliver.

**On The Lantern Moth.** The pre-production pack the paint stage needs, hashed and proved:

```text
17 files, 36.8 KB hashed into ./MANIFEST.sha256
  required deliverables: 10/10 present
manifest digest c3ffbd3c199747c7...  COMPLETE
OK: 17 files checked, 0 missing, 0 changed, 0 not in the manifest
```
