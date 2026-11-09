# Deliverables, command by command

Every film deliverable comes from one source: the master your editor or compositor exports from the same shot list,
paintings and mix as the preview. Export it once at 3840x2160 and the shot list's fps, at the highest quality your
editor offers (`film/master_export.mov` below), then make every copy from it with ffmpeg. One script that runs these
commands in order rebuilds every deliverable after any change.

## 4K master

Encode with the GPU's HEVC encoder through VAAPI at constant QP 18, then remux with the `hvc1` tag so Apple players
accept it. Two steps, because writing `hvc1` during a VAAPI encode can produce a file that will not decode; the
remux with `-c copy` is clean.

```text
ffmpeg -vaapi_device /dev/dri/renderD128 -i film/master_export.mov -i audio/full_mix.wav -map 0:v -map 1:a \
  -vf "setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709,format=nv12,hwupload" \
  -c:v hevc_vaapi -profile:v main -rc_mode CQP -qp 18 -c:a aac -b:a 320k -shortest film/master_raw.mp4
ffmpeg -i film/master_raw.mp4 -c copy -tag:v hvc1 -movflags +faststart film/<Title>_4K.mp4
```

- `setparams` tags the frames BT.709 before the encode, so the colour tags reach the file.
- `/dev/dri/renderD128` is the first render node; `ls -l /dev/dri/by-path/` shows which card each node belongs to.
- No VAAPI encoder: H.264 instead, libx264 `-preset medium -crf 18 -pix_fmt yuv420p`, the same audio, `+faststart`.
- Audio: the mix as AAC 320k, cut to the picture's length (`-shortest`).
- Delete `master_raw.mp4` once the tagged file passes its checks.

## 1080p for posting

Loudness first, in two passes. Pass one measures the mix:

```text
ffmpeg -i audio/full_mix.wav -af loudnorm=I=-14:TP=-1.5:LRA=18:print_format=json -f null -
```

It prints `input_i`, `input_tp`, `input_lra`, `input_thresh` and `target_offset`. Pass two applies them with
`linear=true`, so the whole mix moves by one gain instead of being compressed, while the picture is scaled:

```text
ffmpeg -i film/<Title>_4K.mp4 -i audio/full_mix.wav -map 0:v -map 1:a \
  -vf "scale=1920:1080:flags=lanczos" -c:v libx264 -preset slow -crf 16 -profile:v high -pix_fmt yuv420p \
  -af "loudnorm=I=-14:TP=-1.5:LRA=18:measured_I=<input_i>:measured_TP=<input_tp>:measured_LRA=<input_lra>:measured_thresh=<input_thresh>:offset=<target_offset>:linear=true,aresample=48000" \
  -c:a aac -b:a 320k -shortest -movflags +faststart film/<Title>_1080p.mp4
```

- -14 LUFS integrated, -1.5 dBTP true peak. LRA 18 keeps a quiet, dynamic film from being flattened.
- ffmpeg falls back to dynamic mode only when one gain cannot meet the true-peak limit; measure the result to know.
- `aresample=48000` brings the audio back to 48 kHz after loudnorm.

## Phone copy

Made from the posting copy, so its loudness is already right:

```text
ffmpeg -i film/<Title>_1080p.mp4 -vf "scale=1280:720:flags=lanczos,hqdn3d=1.2:1.2:3:3" \
  -c:v libx264 -preset slow -b:v 900k -maxrate 1400k -bufsize 2800k -pix_fmt yuv420p \
  -c:a aac -b:a 128k -movflags +faststart film/<Title>_phone.mp4
```

If a phone copy is still too big for a chat app, run it again at a lower `-b:v`, keeping 720p.

## Checks

```text
ffprobe -v error -show_entries stream=codec_name,codec_tag_string,profile,width,height,pix_fmt,r_frame_rate,sample_rate,channels:format=duration,size,bit_rate -of compact=p=0 film/<Title>_4K.mp4
ffmpeg -i film/<Title>_1080p.mp4 -map 0:a -af ebur128=peak=true -f null -
ffmpeg -i film/<Title>_4K.mp4 -vf "fps=1/2,scale=640:-1,tile=6x4" out/final_sheet_%02d.jpg
```

Streams (codec, tag, profile, size, pixel format, frame rate, audio rate and channels), length, size and bitrate;
loudness (EBU R128: the summary at the end gives integrated, range and true peak); a contact sheet, one frame every
2 s. Look at the first and last frames on the sheet: black, or the title, on purpose.

### Sync at the story hits

Measured on the finished file, not the timeline: at each story hit, the biggest picture change against the strongest
sound onset nearby.

```text
ffmpeg -i film/<Title>_1080p.mp4 -an -vf "select='gte(scene,0)',metadata=print:key=lavfi.scene_score:file=out/scene.txt" -f null -
ffmpeg -i film/<Title>_1080p.mp4 -vn -ac 1 -ar 48000 out/finished_audio.wav
python3 scripts/beatmap.py out/finished_audio.wav --json out/finished_audio.json
```

`out/scene.txt` lists every frame's time and how much the picture changed (0 to 1); `onsets` in
`out/finished_audio.json` lists every attack, refined to the true attack. For each story hit, take the frame with the
highest scene score within half a second and the strongest onset within half a second, and write down how far apart
they are in ms. Target: one frame or less (42 ms at 24 fps) wherever a cut sits on the hit. A hit with no cut on it
shows a gap; read it against the shot list.

## Covers

Pick 3 or 4 frames that carry the film without context (the image-twice frame, the choice, the twist). Take them
from the 4K master as PNG, then JPG for posting. Check each at phone size: the subject must read.

```text
ffmpeg -ss 15 -i film/<Title>_4K.mp4 -frames:v 1 film/covers/<Title>_15s.png
ffmpeg -i film/covers/<Title>_15s.png -q:v 2 film/covers/<Title>_15s.jpg
```

(The Lantern Moth's would be the middle of s03, s05 and s06: the moth on her hand, the beam, the dawn.)

## Picture book

- Interactive: a page-turning web book (cream paper, page-turn animation, keyboard and swipe), the music under it,
  pages turning on the music's phrases or by hand; works on a phone.
- Video: the book as 4K and 1080p films, pages turning with the music.
- Print: a PDF at the printer's page size with bleed, images at 300 dpi, fonts embedded; every spread checked.

## Localised editions

One edition per language, made from the same paintings and timing: subtitles or re-set handwriting in a font that
supports the script, every line re-timed to its reading speed (a translated narration file in film time), and checked
by someone who reads the language. Deliver each as 4K, 1080p and phone.

## The making-of

A PDF (and a phone-size PDF): the story, the style lock and sheets, the score and its beatmap, the contact sheets,
before and after of the fixes in post, the numbers (credits planned and spent, paintings made, repainted, fixed in
post). The production's own files are its illustrations.
