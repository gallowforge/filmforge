# Cutting to music

## Where a cut belongs, strongest first

1. **A phrase boundary**: the music changes section. Scene changes go here.
2. **A silence edge**: the music stops (a held breath) or re-enters. The story's turn goes here.
3. **A hit**: a strong attack with a jump in level. The moment the picture must land (a lamp blazes, a door gives).
4. **A downbeat**: beat one of a bar. Ordinary cuts inside a scene.
5. **An accent**: a strong attack off the grid (common in rubato or triplet passages).
6. **A beat**: when nothing stronger is near.

A cut a few frames before a hit reads as late; cut on it, or on the frame after. A cut inside a sustained note
reads as random.

## Holds

Painted holds read in 1.5 s at the shortest; most sit at 4 to 6 s; a held emotional frame can take 7 to 9 s if it
has life in it (fog, falling ash, a light sweep). Long phrases take longer holds, not more shots.

## The order of work when the film has two cues

1. Generate cue 1. Listen at the hits; retime the first half to it; cut the first half with the score in your
   editor and watch it. Nothing else is spent until this works.
2. Paint the rest in batches.
3. Cut the second half with provisional holds; generate cue 2 at that length; retime to it.
4. Cut the whole film.

## The picture follows the music too

Bloom, ember flare, the golden thread's glow and handwritten text's breathing follow the score's level and pulse,
so the picture swells and hits with the music without hand keyframes. In post, drive them from the score itself: an
audio-to-keyframes pass in your compositor, or a level envelope computed in code you own. beatmap.json's `loudness`
(every half second), `onsets` and `hits` give the same information for planning.

## The sync check on the finished file

The finished film is checked at every story hit: the biggest picture change near the hit against the strongest
sound onset near it, reported in milliseconds. Measure the delivered file, not the timeline: ffmpeg's scene score
gives the picture changes, and `beatmap.py` run on the film's own audio gives the onsets (the commands are in
forge-deliver's references/deliverables.md). Target: within one frame (42 ms at 24 fps) wherever a cut sits on the
hit. In The Lantern Moth the hit that matters most is 0:24, where the lamp lights after the held breath; every
other cut (6, 12, 18 and 30 s) is checked the same way.

Checked against every hit in the score's beatmap instead, hits inside shots where no cut was planned show a gap.
That is fine when the shot list says no cut belongs there, and a miss when one does.
