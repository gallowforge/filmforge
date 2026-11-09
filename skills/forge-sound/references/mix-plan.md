# The mix plan

## Format

Filled in for The Lantern Moth: times from its retimed shot list (s01 0:00, s02 0:06, s03 0:12, s04 0:18, s05
0:24, s06 0:30 to 0:36.17), the shape from its score brief and `intent.yaml`, layers from its screenplay. Levels
stay in words until the score is measured; then the score column takes beatmap.py's phrase levels in dB.

```text
# <Title>: mix plan

## Loudness script
| Section | Time | Score level | Carried by |
| --- | --- | --- | --- |
| The dark | 0:00 to 0:12 | quiet | drone and pulse; wind and sea, then the lamp room |
| The choice | 0:12 to 0:23.5 | warmer, rising | the theme; the moth's embers; the sea through the glass |
| The held breath | 0:23.5 to 0:24 | silence | nothing: every layer ducked out |
| The light | 0:24 to 0:36 | the loudest, then full | the hit and full chords; the sea; a thin dawn wind |

## Layers
| Layer | From | To | Level | Notes |
| --- | --- | --- | --- | --- |
| wind bed | 0:00 | 0:06 | low | over the headland |
| sea bed | 0:00 | 0:06 | low | below the cliff |
| room bed | 0:06 | 0:24 | low | inside the lamp room |
| crackle | 0:06 | 0:08 | short | the match catches, then dies |
| crackle | 0:08 | 0:18 | soft | the moth's embers |
| sea bed | 0:18 | 0:24 | lower | through the glass |
| duck | 0:23.5 | 0:24 | -40 dB | the held breath, silent on purpose |
| thump | 0:24 | | the hit | the lamp lights on the hit |
| chime | just after 0:24 | | soft | |
| whoosh | 0:24 | 0:26 | under the score | the beam crossing the sea |
| sea bed | 0:24 | 0:36.17 | low | |
| wind bed | 0:30 | 0:36.17 | lower | dawn: the wind has dropped |

## Narration
| Start | End | Line |
| --- | --- | --- |
| 0.5 | 5.4 | the lamp had gone out. |
| 30.5 | 35.567 | some lights are only kept by giving them away. |

## Targets
Master: the mix as mixed, peak set at the finish; posting and phone copies -14 LUFS, -1.5 dBTP (two-pass, linear).
```

## Keying effects to the shot table

Read every shot's start and end from the retimed shot list, and place each layer relative to a shot. In code you
own, the table is four lines:

```python
    T, t = {}, 0.0
    for s in sl["shots"]:
        T[s["id"]] = (t, t + float(s["dur"]))
        t += float(s["dur"])
```

then every layer is placed from it (the room bed from `T["s02"][0]` to `T["s04"][1]`). In a DAW, put a marker at
every cut point (`shotlist.py stats` prints where each scene starts; the durations give the rest) and snap each
layer to its shot's marker. Either way a re-cut moves the sound with it.

## Measuring

```text
ffmpeg -v info -i audio/full_mix.wav -af ebur128=peak=true -f null - 2>&1 | tail -12
```

The summary gives the three numbers that matter: integrated loudness (LUFS), loudness range (LU) and true peak.
Measure the finished film's own audio the same way (`-map 0:a` on the delivered file), since that is what people
hear.

## Normalising for posting (two-pass, linear)

Measure the mix with `loudnorm=I=-14:TP=-1.5:LRA=18:print_format=json`, then apply `loudnorm=I=-14:TP=-1.5:LRA=18`
with the measured values and `linear=true`, so the whole mix moves by one gain instead of being compressed (ffmpeg
falls back to dynamic mode only when one gain cannot meet the true-peak limit). A wide loudness range (LRA 18) keeps a
quiet, dynamic film from being flattened. The exact commands are in forge-deliver's references/deliverables.md.
