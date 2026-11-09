# <Title>: delivery checklist

Stage 6 of the filmforge method (deliver everything), and the forge-deliver skill's matrix. Everything comes from
the same paintings, shot list and mix. Strike what this film does not have, and tick an item only after checking the
file itself.

## The deliverables matrix

| Deliverable | Spec | Check |
| --- | --- | --- |
| 4K master | 3840x2160, the shot list's fps, HEVC Main with the `hvc1` tag, AAC 320k, the mix as mixed | `ffprobe`: streams, tag, bitrate; plays on the TV over Wi-Fi without stutter |
| 1080p for posting | H.264 High, CRF 16, yuv420p, AAC 320k, `+faststart`, two-pass linear loudnorm to -14 LUFS / -1.5 dBTP | loudness measured (EBU R128); plays in a phone browser |
| Phone copy | 1280x720, H.264 at 900k (maxrate 1400k), AAC 128k, `+faststart` | sends in a chat app without recompression |
| Covers | 3 to 4 frames at full resolution, PNG and JPG, the film's strongest images, no text painted in | read at phone size |
| Print book (if any) | PDF, trim size fixed, bleed per printer, spreads as true double-width pages, the original full-size paintings, live type, fonts embedded | open in two PDF readers; every page checked at a 300 dpi crop |
| Making-of (if any) | PDF: the method, the cast, the world, the plates with their prompts, the gate, the ledger; plus a phone-size PDF | links and images |
| Localised editions (if any) | per language: subtitles or re-set handwriting, the same masters; paintings and timing unchanged | every line on screen long enough to read |

## Checks before calling it delivered

- [ ] Streams, codecs, codec tag, frame rate, resolution, audio rate and channels, duration as specified (`ffprobe`)
- [ ] Loudness measured (EBU R128): integrated, range, true peak under the limit
- [ ] Contact sheet of the finished film (one frame every 2 s) looked at in full
- [ ] Every story hit with a cut on it: picture within 1 frame (42 ms at 24 fps) of its music hit, offsets written in ms
- [ ] First and last frames are what they should be (black, title)
- [ ] Watched once start to finish on the target screen and once on a phone, with sound
- [ ] One command rebuilds every deliverable, so any change produces them all again

## Archive

- [ ] Everything that made the film in one folder (production.yaml, story, prompts, paintings, audio, code, deliverables)
- [ ] Left out on purpose, with the reason (caches, virtual environments, upscale caches)
- [ ] `archive.py build <folder> --require deliverables.txt --require-shotlist shotlist.yaml --paintings <dir>`: COMPLETE
- [ ] `archive.py verify <folder>`: OK
- [ ] Copies proven with `archive.py compare <folder> <copy>`
