# production.yaml, field by field

The one state file. Everything the director needs to know about a production is here or one path away from here.
`production.py` reads it; `production.py spend`, `signoff` and `advance` write it. Keep it hand-editable.

| Field | Type | Meaning |
| --- | --- | --- |
| `title` | text | The film's title |
| `logline` | text | One sentence: who wants what, and what it costs them (quote it if it contains a colon) |
| `format.width`, `.height`, `.fps` | numbers | The master's raster and frame rate (3840, 2160, 24) |
| `format.aspect` | text | "16:9" for film; a book uses its page ratios |
| `format.runtime_target` | seconds | What the story is sized to |
| `budget.credits_available` | number | The ceiling for this film |
| `budget.reserve_pct` | number | Never planned into (default 5) |
| `budget.approved_by` | text | Who approved the ceiling; the brief gate needs it |
| `budget.spent` | list | `{stage, item, credits, note?, forced?}` appended by `production.py spend` |
| `files.<key>` | path | Where each artefact lives, relative to production.yaml. Keys the gates use: bible, screenplay, shotlist, style_lock, ledger, score_brief, score, beatmap, prompts, paintings, qa, preview, mix, deliverables, archive, lessons |
| `deliverables` | list | Names from the delivery matrix (master-4k, posting-1080p, phone, covers, print-book, making-of, edition-<lang>) |
| `stage` | text | The current stage; `advance` moves it |
| `stages.<stage>.status` | text | `passed` once its gate passed |
| `stages.<stage>.signoff` | map | `{by, note}`: who looked at what |
| `decisions` | list | Locked decisions, one line each |

## Conventions

- A spend is logged when the generation is requested, at its listed price; failed and refunded generations are
  removed by hand with a note.
- A `forced` spend carries its reason and the problems it overrode. Review forced spends in the retro.
- If the state file and the folder disagree (a painting exists that qa.yaml does not know), the folder is the truth;
  fix the state file, then re-run the gate.
