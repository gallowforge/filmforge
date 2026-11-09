---
name: forge-sound
description: "FilmForge sound: times narration (handwritten on-screen lines or a voice) in film time so it can cross cuts at a readable pace, plans the sound design (wind, fire, rain, glass, impacts, whooshes, and the silences) keyed to the shot table and builds it in post or in code you own, sets a loudness script per section, and mixes score, effects and narration to delivery loudness with measured proof. Use this skill whenever the user wants narration, voice-over, subtitles or on-screen words timed to a film, sound effects or ambience, a mix or mix plan, ducking, loudness targets for posting, or says the sound feels empty, too loud, too quiet or out of sync."
---

# FilmForge Sound

Sound is the half of the film nobody notices until it is wrong. Here it is planned like the picture: narration timed
to the second and measured against reading speed, sound design placed from the shot table so it can never drift
from the cut, a loudness script for the whole film, and a mix measured to its delivery targets. It is built in your
editor or DAW, or in code you own.

Paths: `scripts/`, `templates/` and `config/` below are folders inside this skill (the base directory shown when it loads), put there by `./install.sh`. Working from a clone of the repository, they are `tools/`, `templates/` and `config/` at its root.

## Step 1. Narration: what it says

Narration says only what the pictures cannot: who is speaking and why it matters, a name, a stake, what the ending
means. Never what is on screen. One voice, consistent. Handwritten lines are lowercase, set in post, never painted.
The Lantern Moth has two handwritten lines and no voice: "the lamp had gone out." opens it, and "some lights are
only kept by giving them away." closes it by saying what the ending means.

## Step 2. Narration: when it says it

Narration runs in film time, not shot time, so a line can flow across a cut the way a film's voice does.

- **Reading speed:** handwritten write-on lines at most 2.4 words a second (the shot list's `narration_wps`); a voice
  at most about 2.8. `shotlist.py stats` prints the film's rate (The Lantern Moth: 2 lines, 14 words, 0.39 words a
  second over the film).
- **Gaps:** at least 0.3 s between lines, more at a scene change.
- **Placement:** a line starts after the fade-in, never on top of a story hit (the hit belongs to the picture and
  the music), and sits in the painting's quiet area (`text_area`).
- **Length:** most lines 2.5 to 5 s on screen.

Narration is planned two ways:

1. **Each shot's `narration` line**, with a default timing: written on 0.5 s into the shot and held until 0.6 s
   before its end. Use it when every line belongs to one shot. `shotlist.py validate` checks its words per second.
2. **A narration file of `[start, end, text]` in film seconds**, when a line must cross a cut or start somewhere
   exact:

```yaml
# narration.yaml: film seconds, from the retimed shot list (shotlist.py stats prints the cut points)
- [0.5, 5.4, "the lamp had gone out."]
- [30.5, 35.567, "some lights are only kept by giving them away."]
```

Those two are the default timings of The Lantern Moth's `narration` lines (s06 runs 30.0 to 36.167 s). The first
starts inside s01's 1.5 s fade-in; to hold it until the picture is up, give it a later start in the file. Set the
lines in your editor low and centred like subtitles, on a soft dark band, written on left to right; a long line
breaks into two.

## Step 3. Sound design, keyed to the shot table

Every effect is placed relative to a shot, read from the retimed shot list, so it moves when the cut moves. Build it
in your DAW or editor from recorded or synthesised sounds, or in code you own from noise, filters and envelopes. The
palette a painted film needs is small:

| Sound | What it is |
| --- | --- |
| bed | a continuous bed: wind, sea, room, fire or rain, slowly breathing |
| whoosh | a band-passed sweep panned across the stereo field |
| thump | a low impact that dies away |
| crackle | embers or a match: short bright ticks |
| chime | a soft struck tone (a light coming on) |
| duck | everything already in the mix lowered under a span (a voice, a held breath); -8 dB for a voice |
| score | the music, laid in at the shot list's `score_offset` |
| finish | a soft limit, the tail faded, the peak set, written as 24-bit 48 kHz WAV |

The Lantern Moth's plan, from its shot list, screenplay and score brief: the score first, then the world: wind and
sea over the headland, the room inside the lamp, the match catching and dying, the moth's embers, the sea through
the glass. Its silence is designed too. The score holds its breath before the hit (0:23.5 to 0:24), so everything is
ducked to silence under it, and the lamp lights on the hit at the start of s05: a low thump, a soft chime just
after, then a whoosh as the beam crosses the sea.

Where the score drops out, the sound design comes up. A **silence beat** is designed, never left empty by accident:
when the music dies, only the world (wind, fire, falling ash) remains, or nothing at all.

## Step 4. The loudness script

Like the colour script: a target level per scene or music section, so the film has a shape. Start from the score's
own phrase levels (beatmap.py prints them as `level dB` in its phrase table) and write what carries each section.
The Lantern Moth's brief asks for a quiet dark, a warmer choice, complete silence at the held breath, then the
loudest moment on the hit and full chords to the end (its `intent.yaml` draws the same shape); the sound design keeps
the dark sparse, empties the held breath and lands the thump on the hit. Write it as a table: section, time, level,
what carries it (score, effects, voice). Format: references/mix-plan.md.

## Step 5. The mix

- Score as the bed; effects under it and up where it drops; a voice ducks the score while it speaks (-8 dB);
  handwritten narration needs no ducking.
- Finish with the peak set (-1.0 dB by default) and write 24-bit WAV to `audio/full_mix.wav`. Measure it:
  `ffmpeg -i audio/full_mix.wav -af ebur128=peak=true -f null -` prints integrated loudness, range and true peak.
- The master carries the mix as mixed. The posting and phone copies are normalised to -14 LUFS with a true peak of
  -1.5 dBTP, two-pass and linear (forge-deliver has the commands).
- The mix goes under the picture in the editor's export of the master, or is muxed in when the master is encoded
  (forge-deliver).

## Output

- narration: the shots' `narration` lines, or `narration.yaml` with film-time starts and ends
- the sound design, keyed to the retimed shot list (a DAW session, or code you own in `code/`)
- the loudness script table
- `audio/full_mix.wav` and its measured loudness

## Gate checklist

- [ ] Every line says something the picture cannot
- [ ] `shotlist.py validate`: no narration warnings; gaps of 0.3 s or more
- [ ] No line on a story hit; every line in a quiet area
- [ ] Sound design keyed to the shot table; silence beats designed
- [ ] Mix measured: integrated loudness, true peak; numbers in the report

## Repair table

| Symptom | Fix |
| --- | --- |
| Lines flash by | Over the reading speed: fewer words, or let the line run across the next cut with a narration file |
| Narration describes the picture | Cut the line, or replace it with the thing the picture cannot say |
| Effects drift from the picture after a re-cut | Effects were placed by absolute time; place each from its shot's start in the retimed shot list |
| The film feels flat | No loudness script: give the sections a shape, and design the silences |
| The held breath is not silent | Effects or beds run through it: `duck` the span to -40 dB, or end the beds before it |
| Posting platform turns it down or distorts it | Not normalised: post the two-pass copy forge-deliver makes (-14 LUFS, -1.5 dBTP) |

## References

- `references/mix-plan.md`: a full mix plan format and the delivery loudness commands
