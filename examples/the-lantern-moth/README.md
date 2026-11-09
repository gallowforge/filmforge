# The Lantern Moth (worked example)

A fictional 36-second painted film in six shots, written through every stage of the method up to the paint gate.
On a black winter coast, a lighthouse girl whose great lamp has died gives away the only warm thing she has, a moth
made of embers, to bring a lost boat home.

It is all text: the plan, the prompts and the decisions. That is the part of a film the technique controls, and the
part every tool checks.

## What is here

| File | Stage | What it is |
| --- | --- | --- |
| `production.yaml` | director | the state file: credits, spends, stage, gates passed, decisions |
| `story-bible.md`, `screenplay.md` | story | premise, the six engines, characters, colour script; the timed screenplay |
| `shotlist.yaml` | story, score, motion | six shots, retimed onto the score (`cut:` says what each cut landed on), each with its `motion` plan |
| `style-lock.yaml` | style | one model, one look, the avoid tail, the twelve-slot prompt grammar |
| `continuity.yaml` | paint | handles, anchors, the moth's scale lock, the lantern's span, the soot, the colour script, the no-gold rule |
| `score-brief.md`, `intent.yaml` | score | the music brief and the shape the story wants from it |
| `prompts/` | paint | one prompt per shot, in the grammar (s03 is missing its scale lock on purpose) |
| `qa.yaml` | frame QA | the decision format: accept, fix in post with the exact call, or repaint with the root cause and the corrected prompt |
| `archive-required.txt` | deliver | what the pre-production pack must hold before a credit is spent on paintings |

## Run the tools on it

```bash
T=../../tools
python3 $T/production.py status production.yaml                  # where the film stands, and the one next action
python3 $T/shotlist.py validate shotlist.yaml --ledger continuity.yaml
python3 $T/budget.py shotlist.yaml --production production.yaml  # 39.08 credits planned of 66.50 spendable
python3 $T/ledger.py prompts continuity.yaml --prompts prompts --style style-lock.yaml --shotlist shotlist.yaml
python3 $T/archive.py build . --require archive-required.txt     # hash the pack and prove it complete
```

The prompt lint stops the film at the paint gate, on the one prompt that lost a lock:

```text
ERROR   s03: moth's scale lock is missing ("its wingspan equals a child's open hand, never smaller than a palm and never larger than a face")
prompts (6 checked): 1 error(s), 0 warning(s)
```

## The next actions, in order (what the director would do)

1. Put QA's corrected prompt into `prompts/s03.md`; the lint passes.
2. Paint in batches of four, each judged at full size against the sheets before the next.
3. Apply the fixes in post that QA wrote for s02 and s04, re-measure with `ledger.py palette`, set `done: true`.
4. The paint gate passes; `production.py advance` moves the film to motion.
