<h1 align="center">filmforge</h1>

<p align="center"><b>The technique for making painted films with AI image and video models, written down.</b><br>
How to write the story, lock one look, prompt every shot, judge every painting and spend every credit once.</p>

<p align="center">
  <a href="#the-technique-on-one-page"><b>The technique</b></a>
  &nbsp;·&nbsp;
  <a href="#the-prompt"><b>The prompt</b></a>
  &nbsp;·&nbsp;
  <a href="#the-nine-skills">The nine skills</a>
  &nbsp;·&nbsp;
  <a href="docs/method.md">The method in full</a>
  &nbsp;·&nbsp;
  <a href="#quickstart">Quickstart</a>
</p>

<p align="center">
  <a href="https://github.com/gallowforge/filmforge/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/gallowforge/filmforge/actions/workflows/ci.yml/badge.svg" /></a>
  <img alt="9 Claude Code skills" src="https://img.shields.io/badge/Claude_Code-9_skills-e9bb66?labelColor=0d0b0a" />
  <img alt="7 tools" src="https://img.shields.io/badge/tools-7-e9bb66?labelColor=0d0b0a" />
  <img alt="40 tests" src="https://img.shields.io/badge/tests-40_passing-e9bb66?labelColor=0d0b0a" />
  <img alt="MIT licence" src="https://img.shields.io/badge/licence-MIT-c8bba7?labelColor=0d0b0a" />
</p>

<br />

Image and video models can paint almost anything. A film made with them still fails in the same few places. The characters drift off model between shots. The look changes from one generation to the next. A clip costs a day's credits and still doesn't cut. The music arrives last and fights the edit. And the slip is found after the money is gone.

**filmforge is the technique that prevents those failures, written as nine Claude Code skills.** The story comes first and is priced before anything is generated. One look is locked and pasted word for word into every prompt. Every prompt follows the same twelve slots, carries its continuity anchors and is linted before it costs a credit. Paintings are made in batches of four and judged at full size. A slip is fixed in post before anything is repainted, and a repaint gets its root cause and its corrected prompt first. Seven small tools check the work at each stage gate. The repository holds the method, not the pictures: no generated images, no films, no renders.

## The technique on one page

1. **Story before credits.** A premise becomes a story bible, a timed screenplay and a shot list built on six engines: one relationship, a flaw with a price, a choice that breaks your heart, a twist, a mirror, and one image used twice. Nothing is generated until the story works on paper.
2. **Price the whole film first.** Every sheet, plate, painting, cue and clip is priced against the credit ceiling, with a retake buffer per stage and a reserve that is never spent. If it doesn't fit, cut nice-to-haves, never the story's spine.
3. **One model, one setting, one look.** The model choice belongs to the director, and it is made once per film. A single look sentence goes into every prompt unchanged, with the palette, the colour rules and the forbidden colours.
4. **Sheets before shots.** Every character gets a sheet with a scale bar, and every recurring place a plate. Each is made at the cheapest setting and proven in three real scenes before any shot is painted.
5. **Handles, never names.** Prompts describe people by a fixed handle and anchor ("the girl in the red knitted hood"). A model paints names as text, and named identities get refused.
6. **Twelve slots, every time.** Look, references, shot, subject and scale, moment, setting, light, colour, text area, continuity, locks, avoid. The order never changes, so a missing slot shows.
7. **Lint before you paint.** Every prompt is checked against the style lock and the continuity ledger: the look sentence word for word, every character's anchor and scale lock, every prop and state, the forbidden-colour clause, the avoid tail, and the length.
8. **Batches of four, judged at full size.** Each batch is read at 100% against the sheets before the next is painted. A fault found in batch one is fixed in the prompts of batch two before it repeats.
9. **Fix in post before you repaint.** Colour, exposure, levels and framing are grades, not paintings. A repaint is for what post can't fix (scale, anatomy, identity). It is spent only once its root cause and its full corrected prompt are written down.
10. **When a result gets worse, take away.** Remove the last addition instead of adding more text. Describe what you want positively. Mention every attached reference in the prompt, and keep grain and grading off references.
11. **Music first, then cut on it.** The score is briefed and measured before the edit: tempo, phrases, hits, silences. Every cut is planned onto it, with the story's hits pinned.
12. **Paintings hold; life comes in post.** A painting is held like a film frame and given life in post (fog, particles, light, handwritten words, effects that move with the music). Paid video is kept for the moments where motion is the story.
13. **Deliver everything, and prove it.** Master, posting copy at -14 LUFS, phone copy, stills and print, each checked for streams, loudness and sync. Then an archive with a SHA-256 manifest that anyone can re-verify.

The method in full, stage by stage with the rules and the gates, is in [docs/method.md](docs/method.md).

## The prompt

Every shot's prompt is written in the same twelve slots, from the shot list, the character sheets and the style lock. This is the first shot of the worked example, [`examples/the-lantern-moth`](examples/the-lantern-moth):

```text
A frame from a hand-painted storybook film, in exactly the style of the attached sheets: soft gouache and
watercolour on rough paper, confident brush-ink outlines, visible paper grain, deep night colours, light that comes
only from lamps, embers and the sky.                                                                  <- LOOK, word for word

References: the attached plate governs the headland, the lighthouse and the sea, nothing else.          <- REFERENCES

An extreme wide shot from the sea at eye height, framed like a 35 mm lens. The lighthouse stands on a
black rock headland on the right third of the frame, its great lamp dead and dark behind cold glass.     <- SHOT, SUBJECT
Far out on the left third, very small against the swell, a fishing boat with one red sail pitches
between grey waves. Snow crosses the frame on a hard wind.                                              <- MOMENT, SETTING

Night. The only light is a faint cold glow low on the horizon behind the clouds, from the left; no lamp
is lit anywhere. Colours: night slate, ink blue-grey and sea grey; the red sail is the only colour.      <- LIGHT, COLOUR

Keep the upper-left sky quiet: soft cloud and snow only, room for a handwritten line.                   <- TEXT AREA

Absolutely no warm gold light anywhere in the frame.                                                    <- LOCKS

Avoid: 3D render, CGI, photorealism, anime, plastic, text, letters, signatures, watermark, extra
fingers, distorted faces.                                                                               <- AVOID
```

The lint reads all six of the example's prompts and catches the one that lost a lock:

```text
$ ledger.py prompts continuity.yaml --prompts prompts --style style-lock.yaml --shotlist shotlist.yaml
ERROR   s03: moth's scale lock is missing ("its wingspan equals a child's open hand, never smaller than a palm and never larger than a face")
prompts (6 checked): 1 error(s), 0 warning(s)
```

That one missing clause is the difference between a moth the size of a palm and a speck nobody can see. It is cheap to catch here and costs a repaint later.

## The nine skills

The director runs the production through stage gates and hands each stage to its skill.

| Skill | What it does |
| --- | --- |
| [forge-director](skills/forge-director/SKILL.md) | Runs the production through its stage gates, keeps the state file and the credit ledger, prices the plan, and always names the one next action |
| [forge-story](skills/forge-story/SKILL.md) | Premise to story bible, timed screenplay and a shot list sized to the credits |
| [forge-style-lock](skills/forge-style-lock/SKILL.md) | One model and setting, one look, the palette and colour rules, character sheets with scale bars, the prompt grammar |
| [forge-score](skills/forge-score/SKILL.md) | The music brief, then the score measured, ranked against the story's shape and cut on |
| [forge-painter](skills/forge-painter/SKILL.md) | Every shot's prompt in the twelve slots with continuity anchors, linted, painted in batches of four |
| [forge-frame-qa](skills/forge-frame-qa/SKILL.md) | Every painting at full size: scored on nine criteria, then accept, fix in post, or repaint with the root cause and the corrected prompt |
| [forge-motion](skills/forge-motion/SKILL.md) | Each shot's life planned in post instead of credits, and when paid video is worth it |
| [forge-sound](skills/forge-sound/SKILL.md) | Narration timed in film time, sound design keyed to the shots, a mix to delivery loudness |
| [forge-deliver](skills/forge-deliver/SKILL.md) | Every deliverable with exact encode settings, checked, then the archive with its proof |

Seven tools enforce the gates. `production.py` keeps the state and names the next action. `budget.py` prices the plan. `shotlist.py` validates and retimes the shot list. `beatmap.py` measures the score and plans the cuts. `ledger.py` checks continuity, lints prompts and measures colour. `contact_sheet.py` builds the QA sheet and the 100% crops. `archive.py` hashes and verifies. They check, price and measure; they generate nothing.

## The worked example

[*The Lantern Moth*](examples/the-lantern-moth) is a 36-second film in six shots, written through every stage up to the paint gate. A lighthouse girl gives away the only warm thing she has, a moth made of embers, so the dead lamp can bring a lost boat home. It holds the story bible, the screenplay, the shot list, the style lock, the continuity ledger, the score brief, all six prompts (one missing its scale lock on purpose) and the frame-QA decisions. The tools run on it:

```text
$ budget.py shotlist.yaml --production production.yaml
...
credits 70.00, reserve 5% -> spendable 66.50; spent so far 33.30, left 36.70
FITS: 27.42 credits to spare (room for 7 more paintings with retakes)
```

## Why it is different

| | The usual way | filmforge |
| --- | --- | --- |
| Cost | Known when the credits run out | Priced per shot before the first spend, with retake buffers and a fit plan |
| Consistency | Hoped for, prompt by prompt | One locked look, sheets with scale, a continuity ledger, every prompt linted |
| The music | Added last, fought in the edit | Briefed and measured first; every cut planned on it |
| A slip | Regenerate and hope | Judged at full size, fixed in post; repainted only with a root cause and a corrected prompt |
| Motion | Paid video per shot | Painted holds given life in post; video only where motion is the story |
| Done | When it looks done | Streams, loudness and sync measured; the archive hashed and verified |

## Quickstart

```bash
git clone https://github.com/gallowforge/filmforge.git && cd filmforge
python3 -m pip install -r requirements.txt     # numpy, Pillow, PyYAML (ffmpeg only for mp3 and m4a input)
./install.sh                                   # the nine skills into ~/.claude/skills, each with its tools
```

Then, in Claude Code:

```text
use forge-director to start a production
```

The director asks for the credit ceiling, makes the production folder from [`templates/`](templates/) and starts the story. `./install.sh --uninstall` removes only the folders it made.

## Quality

| Check | What it covers |
| --- | --- |
| 40 tests (pytest, and a plain runner that needs no pytest) | Every tool: the state file and gates, pricing, the shot list, the beat map, the ledger and prompt lint, the contact sheet, the archive |
| CI: docs | Every relative link and anchor, no machine paths or private addresses, markdownlint, external links |
| CI: tools | Every tool answers `--help`, the tests, the installer into a throwaway home folder and out again |

## Repository layout

```text
skills/      the nine forge-* skills (SKILL.md and references): the technique
tools/       production, budget, shotlist, beatmap, ledger, contact_sheet, archive (+ forgekit, shared)
templates/   the files a production starts from
config/      prices.yaml, the credit price table
examples/    the-lantern-moth, the worked example in text
docs/        method.md, the method stage by stage
tests/       40 tests
```

## FAQ

<details>
<summary><b>Does it need Higgsfield?</b></summary>

No. It was built on Higgsfield, but any image or video model that takes reference images works. The price table lists models and costs, and you can add your own.
</details>

<details>
<summary><b>Why are there no pictures here?</b></summary>

Because the product is the technique. The skills, the prompts and the gates are what make the pictures good, so they are what this repository keeps.
</details>

<details>
<summary><b>Why paintings held on screen instead of generated video?</b></summary>

Cost and consistency. A five-second clip costs more than five paintings, often needs rerolls, and rarely matches the shot beside it. A painting held like a film frame, given life in post, costs one image and cuts cleanly. Video is kept for the moments where motion is the story.
</details>

<details>
<summary><b>Does it work without Claude Code?</b></summary>

The tools are plain Python command lines and run anywhere. The skills are the method written for Claude Code, and [docs/method.md](docs/method.md) is the same method for people.
</details>

## Contributing

Issues and pull requests are welcome. Run `python3 -m pytest -q tests` and `python3 scripts/check_docs.py` before you open one. A change to the method belongs in its skill and in [docs/method.md](docs/method.md) together.

## Licence

MIT, see [LICENSE](LICENSE).
