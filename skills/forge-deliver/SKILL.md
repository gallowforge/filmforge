---
name: forge-deliver
description: "FilmForge deliver: encodes and checks every deliverable of a finished film or book (4K master, 1080p for posting, phone copy, cover stills, print-book PDF, making-of, localised editions) with exact ffmpeg settings, verifies streams, loudness and picture-to-music sync on the finished files, then builds the production archive with a SHA-256 completeness proof that anyone can re-verify later, and proves backup copies byte for byte. Use this skill whenever the user wants to export, encode or render final versions, post a film, make a phone copy or covers, produce a print PDF or a translated edition, back up or archive a production, or prove that an archive or copy is complete."
---

# FilmForge Deliver

A film is finished when every version plays where it is meant to, measures right, and the whole production sits in
one folder with a proof that nothing is missing. This skill makes the deliverables from the deliverables matrix,
checks each one, and closes the production with `archive.py`.

Paths: `scripts/`, `templates/` and `config/` below are folders inside this skill (the base directory shown when it loads), put there by `./install.sh`. Working from a clone of the repository, they are `tools/`, `templates/` and `config/` at its root.

## Step 1. The deliverables matrix (templates/delivery-checklist.md)

Copy it into the production and strike what the film does not have. Every film deliverable comes from one master,
exported from your editor or compositor at 3840x2160 from the same shot list, paintings and mix as the preview, then
encoded with ffmpeg:

| Deliverable | Made from | Settings |
| --- | --- | --- |
| 4K master | the editor's 4K export | 3840x2160 at the shot list's fps; HEVC Main through VAAPI (`hevc_vaapi`) at constant QP 18, tagged BT.709, then remuxed with `-c copy -tag:v hvc1` so Apple players accept it; without VAAPI, H.264 (libx264, preset medium, CRF 18, yuv420p); AAC 320k; `+faststart` |
| 1080p for posting | the master | Lanczos to 1920x1080, libx264 preset slow, CRF 16, High profile, yuv420p; the mix normalised to -14 LUFS and -1.5 dBTP by a two-pass linear loudnorm; AAC 320k; `+faststart` |
| Phone copy | the posting copy | Lanczos to 1280x720 with light denoise (`hqdn3d=1.2:1.2:3:3`), libx264 at 900k (maxrate 1400k, buffer 2800k), AAC 128k; small enough to send in a chat |
| Covers | the master | 3 or 4 of the strongest frames at 4K, PNG, plus JPG for posting; readable at phone size |

The exact ffmpeg commands: references/deliverables.md. Put them in one script, so any change rebuilds every
deliverable.

Books and extras, when the film has them: a picture book as 4K and 1080p videos with the music, a print PDF, an
interactive web book that turns its pages with the music, localised editions (each language its own 4K, 1080p and
phone videos, every line re-set and checked by someone who reads it, never machine-set unreviewed), and the
making-of as a PDF plus a phone PDF. Details: references/deliverables.md.

## Step 2. Check every deliverable

Measure the files themselves, never the timeline:

- **Streams:** codec, size, pixel format, frame rate, codec tag (`hvc1` for the HEVC master), audio rate and
  channels, length, size and bitrate (`ffprobe`).
- **Loudness:** integrated, range and true peak (EBU R128, ffmpeg's `ebur128` filter). The master carries the mix
  as mixed; the posting and phone copies must read about -14 LUFS.
- **Sync at the story hits:** for each hit, the biggest picture change and the strongest sound onset within half a
  second, and how far apart they are in ms. Picture changes come from ffmpeg's scene score, onsets from
  `beatmap.py` run on the film's own audio. Target: one frame (42 ms at 24 fps) or less wherever a cut sits on the
  hit. A hit with no cut on it reports a gap; read it against the shot list.
- **Ends:** the first and last frames (black, or the title, on purpose).
- **Contact sheet** of the finished film, one frame every 2 s, looked at end to end.
- **Watched once** start to finish on the target screen with sound, before sign-off.

The commands for each: references/deliverables.md (Checks).

For PDFs: open in two readers, check every spread, fonts embedded, images at print resolution.

## Step 3. The archive and its proof

Everything that made the film goes in one production folder: production.yaml, the story files, prompts, every
painting and version, the sheets, the score and its measurement, the code, the mixes, the deliverables, the lessons.

```text
python3 scripts/archive.py build <film> --require deliverables.txt \
        --require-shotlist <film>/shotlist.yaml --paintings <film>/art/film \
        --exclude "code/.venv/=rebuilt from requirements.txt"
python3 scripts/archive.py verify <film>
```

`build` hashes every file into `<film>/MANIFEST.sha256` (plain `sha256sum -c` format, so the proof outlives the
tool) and writes `manifest.json`: file count, bytes, files by type, what was **left out on purpose and why** (caches,
virtual environments, any `4k/` upscale folder), the required deliverables and any missing, the shots without
paintings, and the digest of the manifest itself. It reports COMPLETE only when every required pattern matches and
every painted shot has its painting. `verify` re-hashes everything later and fails on any missing or changed file
(and on an edited manifest).

The same tool proves a smaller pack too. The Lantern Moth's `archive-required.txt` lists what its pre-production
pack must hold before a credit is spent on paintings, and `archive.py build` on the example folder with
`--require archive-required.txt` finds all ten patterns present and reports COMPLETE.

**Copies:** prove a backup or a move byte for byte: `python3 scripts/archive.py compare <film> <copy>`. It does in
one command what SHA-256 lists of every file at the source and in the copy, and a copy log, do by hand.

Write a short README in the archive: what each folder holds, what was left out on purpose, where the finished work is.

## Step 4. Close

`production.py signoff deliver --by <you> --note "<watched the master on the TV; checks pass>"`, then `advance` to
the retro (forge-director).

## Output

- `film/` with every deliverable, named `<Title>_4K.mp4`, `<Title>_1080p.mp4`, `<Title>_phone.mp4`, `covers/`
- the checks' numbers in the report (sizes, loudness, sync offsets at each hit)
- `MANIFEST.sha256`, `manifest.json`, the archive README

## Gate checklist

- [ ] Every deliverable in the matrix exists and passed its checks
- [ ] Sync at every story hit within one frame
- [ ] Watched on the target screen with sound
- [ ] `archive.py build`: COMPLETE; `archive.py verify`: OK
- [ ] Every copy proven with `archive.py compare`
- [ ] Signed off

## Repair table

| Symptom | Fix |
| --- | --- |
| Apple devices refuse the HEVC master | Missing `hvc1` tag: remux with `ffmpeg -i in.mp4 -c copy -tag:v hvc1 out.mp4` |
| The HEVC master will not decode | `hvc1` was written during the VAAPI encode: encode without the tag, then remux with `-c copy -tag:v hvc1` |
| The TV stutters over Wi-Fi | Bitrate too high (`ffprobe` prints it): encode the master again at a higher QP (a smaller file) |
| HEVC was wanted but there is no VAAPI encoder | `ffmpeg -h encoder=hevc_vaapi` and `ls /dev/dri` show what the machine has; otherwise deliver the H.264 master |
| Posting platform turns it down or clips it | Not normalised: post the two-pass copy (-14 LUFS, -1.5 dBTP, linear), not the master |
| Phone copy too big to send | Re-encode it from the posting copy at a lower `-b:v` (references/deliverables.md), or shorten; keep 720p |
| verify reports CHANGED | Someone edited a delivered file: restore it from a proven copy, or rebuild and re-sign |
| build reports INCOMPLETE | A required deliverable or a painting is missing: make it, or remove it from the list on purpose with a reason |

## References

- `references/deliverables.md`: the full ffmpeg commands, the checks, books, editions and covers
