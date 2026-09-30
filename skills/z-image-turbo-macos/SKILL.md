---
name: z-image-turbo-macos
description: >-
  Generates images from text prompts on the user's own Apple Silicon Mac with
  one specific model, Z-Image Turbo (6B parameters, the 8-bit
  mflux-community/z-image-turbo-mflux-q8 build), run on the Mac's GPU through
  MLX and mflux. Draws one picture or a batch, to JPEG, PNG or WebP at a chosen
  size, with no API key and no per-image cost, offline after a one-time setup of
  about 12 GB. Use when the user asks to generate, draw or render an image,
  photo, illustration or artwork locally or on their Mac, mentions Z-Image or
  mflux, or when another task needs pictures and the host has no image tool of
  its own. Works only on macOS with an M-series chip, never on an Intel Mac,
  Linux or Windows.
license: MIT
compatibility: >-
  macOS on Apple Silicon (M1 or later) only, with 16 GB of memory or more.
  Runs one model, Z-Image Turbo (mflux-community/z-image-turbo-mflux-q8). Its
  script runs on Python 3.9 or newer, and setup needs a native Python 3.10 or
  newer for the model. Setup uses the network once: mflux and its dependencies
  from PyPI (about 1.2 GB) and the model from Hugging Face (11 GB). Drawing is
  offline.
metadata:
  author: 4e6
  version: "1.0"
---

# Z-Image Turbo on an Apple Silicon Mac

This skill does one thing: it runs **Z-Image Turbo**, Tongyi-MAI's 6B
text-to-image model, in the 8-bit MLX build
`mflux-community/z-image-turbo-mflux-q8`, on the GPU of an **Apple Silicon
Mac**, through mflux. It supports no other model and no other machine — not an
Intel Mac, not Linux, not Windows — and it has no hosted fallback. Where it
cannot run, it says so and stops.

Every step is one script, run with whatever `python3` is on the path; it finds
the environment the model needs by itself. Paths below are relative to this
skill's directory.

```
- [ ] 1  check the machine
- [ ] 2  set up, once, with the user's go-ahead
- [ ] 3  write the prompts
- [ ] 4  generate
- [ ] 5  look at every image, redraw the misses
```

## 1. Check the machine

```
python3 scripts/z_image_turbo.py check
```

| Exit | Last line | Next |
|---|---|---|
| 0 | `ready` | step 3 |
| 1 | `setup needed: …` | step 2 |
| 3 | `cannot …` | stop |

On exit 3, tell the user in one sentence why this machine cannot run it, from
the line marked `no` or `short`, and stop. Do not switch to another model or an
online image service unless the user asks for one. A `memory low` line is not a
stop: say that drawing will be very slow, and go on if they want to.

## 2. Set up, once

Setup is the only step that uses the network, and it is large: the check's last
line says how much it will download, up to about 12 GB. **Tell the user that
figure and get their go-ahead before running it.**

```
python3 scripts/z_image_turbo.py setup
```

It installs mflux into its own environment, `~/.cache/z-image-turbo-macos/venv`,
and downloads the model into the Hugging Face cache. The model download takes
minutes on a fast connection and far longer on a slow one: run it in the
background where your host can. Exit 0 prints `ready`. Exit 1 means a step
failed: show the user the last lines it printed, and run it again when they
want, since the download resumes where it stopped. Exit 3 is the same as in step
1.

## 3. Write the prompts

Write each prompt as a concrete description in full sentences: the subject, what
it is doing, the setting, the composition and camera angle, the light, and the
medium or style — *food photography, top-down view*, *watercolour*, *flat vector
illustration*. Longer and more specific prompts follow better than lists of
keywords.

- **There is no negative prompt and no guidance scale.** The model is
  guidance-distilled, so it is steered by the prompt alone. Keep something out
  by saying what is there instead; *no text, no logos* at the end of a prompt
  does work.
- **Text in the picture:** put the exact words in double quotes — a hand-painted
  sign reading "OPEN DAILY". Short phrases render cleanly; paragraphs do not.
- Prompts may be in English or Chinese.

## 4. Generate

One image:

```
python3 scripts/z_image_turbo.py generate --prompt "A lighthouse on a rocky coast at dusk, warm light in the lantern room, long-exposure sea, cinematic" --out lighthouse.jpg
```

Several: write a jobs file and run it once, because the model loads once per
run. `out` is relative to `--out-dir`, and its extension — `.jpg`, `.jpeg`,
`.png` or `.webp` — chooses the format. `seed` is optional.

```json
[
  {"prompt": "Food photography, top-down view: porridge with blueberries and sliced banana in a rustic ceramic bowl, natural daylight, wooden table, no text", "out": "porridge.jpg"},
  {"prompt": "A hand-painted wooden sign reading \"OPEN DAILY\" hanging in a bakery door", "out": "sign.png", "seed": 7}
]
```

```
python3 scripts/z_image_turbo.py generate --jobs jobs.json --out-dir images
```

| Option | Default | What it does |
|---|---|---|
| `--size WxH` | `1024x1024` | the size the model draws at. Sides are multiples of 16, from 256 to 2048. The model is at its best near one megapixel: `1024x1024`, `1248x832` (3:2), `1344x768` (wide), `832x1248` (tall) |
| `--resize WxH` | none | centre-crops to that shape and scales to that size before saving, for a thumbnail or an exact size, such as `480x480` |
| `--quality N` | `85` | JPEG and WebP quality |
| `--steps N` | `9` | denoising steps. The model is tuned for 9; leave it |
| `--force` | off | redraws images that already exist |
| `--dry-run` | off | checks the jobs and lists what would be drawn |

**It takes time.** Each one-megapixel image takes about 40 seconds on an M5 Pro,
longer on earlier and base chips, and time grows with the pixel count. Before a
batch of more than three, tell the user roughly how long it will take, and run
it in the background where your host can.

Each image gets one line as it finishes:

- `made PATH` — drawn and saved.
- `have PATH` — already there, so skipped. A re-run never redraws a finished
  image without `--force`.
- `fail PATH: reason` — this one failed, and the batch went on.
- `stop PATH: reason` — the batch stopped, interrupted or on a MacBook down to
  10% battery. What was finished is kept.

| Exit | Meaning | Next |
|---|---|---|
| 0 | every job has its image | step 5 |
| 1 | some jobs have none | run the same command again; it draws only what is missing |
| 2 | the command or the jobs file is wrong, and nothing was drawn | fix what the message names |
| 3 | not set up, or the model would not load | step 1 |

## 5. Look at every image

View each image before handing it over, where you can see images. The seed
follows the prompt, so the same prompt redraws the same picture. For one that
misses the prompt — a wrong count of things, garbled lettering, a mangled hand —
reword the prompt or pick a new seed, and redraw that image alone, with the same
`--size` and `--resize` as before:

```
python3 scripts/z_image_turbo.py generate --prompt "…" --out images/sign.png --seed 8 --force
```

`--force` on a jobs file redraws every image in it. Redraw an image at most
twice; then hand it over and say what is still wrong.

Give the user the paths of the images, and nothing of the command's output.
