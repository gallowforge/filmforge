# <Title>: music brief

<N> cue(s), instrumental, <length> s. Written from the screenplay's timings; generated; measured with beatmap.py;
then every cut moves onto it.

**Model:** <music model>, instrumental only. Planned at <seconds> x <credits per second> = <credits>, <takes> take(s).
**Cue split:** <where the film has a natural silence; one bad cue never costs the other>.

## Shared palette (opens every cue's prompt)

> <Intimate cinematic score for ...: lead instrument carries one theme in <key>, with <instruments>. <tempo>.
> No trailer percussion, no braams, no synths, no risers, no vocals, no choir.>

## Cue 1 (<length> s)

> <palette sentence>
> 0:00 to 0:00, <scene>: <instrumentation, energy, feeling>.
> 0:00: <a named hit: what happens in the picture>.
> 0:00: <a written silence>.
> ...

## Story hits (become `pin:` on the shots that start on them)

| Time | Picture | Shot |
| --- | --- | --- |
| 0:00 | <what lands> | sNN |

## Intent curve (intent.yaml, for choosing between takes)

points: [[0, 0.2], ...], hits: [..], length: <s>
