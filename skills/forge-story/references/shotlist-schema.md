# shotlist.yaml schema

One file, read by every tool: `shotlist.py` (validate, stats, retime), `budget.py`, `beatmap.py --shotlist`,
`ledger.py`, `contact_sheet.py --shotlist`, `archive.py --require-shotlist`, `production.py`. It is also the edit
plan: whoever builds the film in post builds it from this file as written.

## Top level

| Field | Required | Meaning |
| --- | --- | --- |
| `title` | yes | Film title |
| `fps` | no (24) | Frame rate; retime rounds every cut to a frame; the edit runs at it |
| `runtime_target` | no | Seconds; validate warns when shots are 10% off |
| `narration_wps` | no (2.4) | Reading-speed limit for narration lines |
| `score_offset` | no (0) | Where the film's first frame sits in the score; set by retime; the edit lays the score in from there |
| `characters` | no | List of ids (their looks live in continuity.yaml) |
| `scenes` | yes | `{id, name, mood}` per scene |
| `assets` | no | Billable things that are not shots (below) |
| `shots` | yes | The film, in order |

## assets[]

| Field | Meaning |
| --- | --- |
| `id` | Unique; shots reference it in `refs` |
| `kind` | `sheet`, `plate`, `proof`, `music`, `video`, `voice`, `code`, `other` |
| `character` | For sheets: the character id (or a list for a lineup) |
| `model` | Overrides the price table's default for this kind |
| `seconds` | Music and voice length |
| `count`, `takes` | Multipliers (two takes of a cue: `takes: 2`) |
| `priority` | 1 must, 2 should, 3 nice to have |
| `stage` | Overrides which stage the spend belongs to |

## shots[]

| Field | Required | Values | Read by |
| --- | --- | --- | --- |
| `id` | yes | `s01`, `s07a` ... unique | all |
| `scene` | yes | a scene id | validate, stats, ledger palette |
| `dur` | yes | seconds > 0 | budget (video length), beatmap targets, retime, the edit |
| `kind` | yes | `painting`, `video`, `code`, `reuse` | budget, gates, the edit (`code`: no painting, a title, black or graphics made in post) |
| `beat` | yes | one line: what happens | validate, contact sheet labels |
| `framing` | no | extreme-wide, wide, medium-wide, medium, medium-close, close, extreme-close, insert, two-shot, over-shoulder, pov, aerial | painter |
| `characters` | no | ids | validate, ledger, screen time |
| `refs` | no | asset ids attached to the prompt | validate (every character's sheet), painter |
| `cut_on` | no | phrase, downbeat, beat, hit, silence, accent, free | beatmap's cut plan |
| `pin` | no | score seconds this shot must start on | beatmap's cut plan (hard constraint, 120 ms) |
| `cut` | set by retime | what the cut landed on | gate (score stage) |
| `narration` | no | a line | validate (words per second), forge-sound (default timing: written on 0.5 s in, held to 0.6 s before the end) |
| `text_area` | no | where words go | painter (keep it quiet) |
| `poses` | no | paintings in this shot (key poses) | budget |
| `keyframes` | no (1) | for video shots: paintings needed | budget |
| `video_seconds` | no | billed length if not `dur` | budget |
| `takes` | no | video takes | budget |
| `model` | no | price-table model for this shot | budget |
| `priority` | no (1) | 1, 2, 3 | budget's fit plan |
| `look` | no | a look name from the style lock | ledger prompts |
| `reuse_of` | for reuse | a shot id | validate, the edit (shows that shot's painting again) |
| `painting` | no | explicit file name | ledger palette, archive, gates (overrides the lookup by id, which takes the newest version) |
| `status` | no | planned, prompted, painted, accepted, fixed, repaint, rendered, cut | humans |
| `motion` | no | effect map or `none` (forge-motion) | the edit, which carries out the plan; validate (keys); gate (motion stage) |

The `motion` keys are a planning vocabulary: tin, tout, life, ashc, emberc, fog, fogc, flick, fire, shim, sweep,
shake, bolts, crack, threads, words, sand, title, crop, note. Their forms and defaults are in forge-motion's
references/motion-vocabulary.md.
