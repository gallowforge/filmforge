# The Lantern Moth: music brief

One cue, instrumental, 40 seconds (36 s of picture plus a 4 s tail). Generated once the screenplay's timings are locked; measured with beatmap.py; then every cut moves onto it.

**Model:** a text-to-music model, instrumental only (`force_instrumental: true` where the model has it). Planned at 40 s x 0.145 = 5.8 credits, one take.

## The prompt

> Intimate cinematic score for a hand-painted storybook short. Solo piano and a soft music box over warm low strings, 120 BPM, 4/4, A minor turning to A major. No trailer percussion, no braams, no synths, no risers, no vocals, no choir.
> 0:00 to 0:12, the dark: a low string drone and one soft low pulse on every bar; cold and alone.
> 0:12 to 0:23, the choice: plucked piano notes enter on the eighths, a small tender theme; warmth held close, then a pull of longing.
> 0:23.5: everything stops, a held breath of complete silence.
> 0:24: one deep warm hit as a lighthouse lamp blazes, then full warm major chords on every bar, a pulse on every beat, release and wonder.
> 0:36 to 0:40: a long fading chord.

## Why it is shaped like this

- **Three phrases for three scenes**, each 12 s, so scene changes land on phrase boundaries.
- **The silence is written in**, because the story's turn (she opens her hands) needs the music to stop, and a silence is the easiest event to cut on.
- **One named hit** at 0:24 for the one moment the picture must land on (the beam).
- **Exclusions are explicit**: music models add trailer drums and risers unless told not to.

## The intent curve (for choosing between takes)

`intent.yaml` holds the shape the story wants (level 0 to 1 over time) and the one hit. With two takes, `beatmap.py take1 take2 --intent intent.yaml` ranks them by how well each matches.
