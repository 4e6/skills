---
name: z-image-turbo-macos
description: >-
  Generates images from text prompts on the user's own Apple Silicon Mac with
  one specific model, Z-Image Turbo (6B parameters, the 8-bit
  mflux-community/z-image-turbo-mflux-q8 build), run on the Mac's GPU through
  MLX and mflux. Makes one image or a batch, as JPEG, PNG or WebP at a chosen
  size, with no API key and no per-image cost, offline after a one-time setup of
  about 12 GB. Use when the user asks to generate, draw or render an image,
  photo, illustration or artwork locally or on their Mac, mentions Z-Image or
  mflux, or when another task needs images and the host has no image tool of
  its own. Works only on macOS 14 or later with an M-series chip, never on an
  Intel Mac, Linux or Windows.
license: MIT
compatibility: >-
  macOS 14 or later on Apple Silicon (M1 or later) only; 24 GB of memory or
  more runs it well. Runs one model, Z-Image Turbo
  (mflux-community/z-image-turbo-mflux-q8). Its script runs on Python 3.9 or
  newer; setup needs a native Python 3.12 to 3.14 for the model. Setup uses the
  network once: pinned packages from PyPI (about 1.4 GB installed) and the model
  from Hugging Face (11 GB). Generating is offline.
metadata:
  author: 4e6
  version: "1.0"
---

# Z-Image Turbo on an Apple Silicon Mac

This skill runs one model, **Z-Image Turbo**
(`mflux-community/z-image-turbo-mflux-q8`), on one kind of machine, an **Apple
Silicon Mac** on macOS 14 or later. It has no other model and no hosted
fallback: where it cannot run, it says so and stops.

Everything goes through one script. Run it with `python3`, by its full path,
from the folder the images are for — the user's working directory, never this
skill's folder, which is replaced when the skill is updated. `--out`,
`--out-dir` and `--jobs` are relative to where you run it. Below, `SKILL_DIR`
stands for this skill's directory. Any command's exit 4 is a fault in the
script: stop, and show the user its message. With no `python3` at all, or a
message about `xcode-select` in its place, tell the user the skill needs Apple's
command-line tools, and stop.

```
- [ ] 1  check the machine
- [ ] 2  set up, once, with the user's go-ahead
- [ ] 3  write the prompts
- [ ] 4  generate
- [ ] 5  look at every image, redraw the misses
```

## 1. Check the machine

```
python3 SKILL_DIR/scripts/z_image_turbo.py check
```

| Exit | Last line | Next |
|---|---|---|
| 0 | `ready` | step 3 |
| 1 | starts `setup needed:` | step 2 |
| 3 | `cannot run here: …` | stop |

On exit 3, tell the user in one sentence what the line marked `no` or `short`
says, and stop. Do not switch to another model or an online image service
unless the user asks for one. A `memory low` line is not a stop: say that images
will be much slower, and go on if they want to.

## 2. Set up, once

Setup is the only step that uses the network. **Tell the user the figure in
the check's last line — the most it can be is about 12 GB — and ask them before
running it.** `--yes` says they agreed; without it, setup downloads nothing and
exits 2.

```
python3 SKILL_DIR/scripts/z_image_turbo.py setup --yes
```

It installs pinned packages into its own environment (by default
`~/.cache/z-image-turbo-macos/venv`) and downloads the model into the Hugging
Face cache. Run it in the background where your host can. Exit 0 prints
`ready`. Exit 1: show the user the line that says why, and run it again once; a
second failure for the same reason, stop and report it. Exit 3 is the same as
in step 1.

## 3. Write the prompts

- **Write sentences, not keyword lists:** the subject, the setting, the
  composition and camera angle, the light, the medium or style.
- **There is no negative prompt and no guidance scale.** The model is steered by
  the prompt alone. Keep something out by describing what is there instead; *no
  text, no logos* at the end of a prompt does work.
- **Text in the image:** put the exact words in double quotes — a sign reading
  "OPEN DAILY". Short phrases render cleanly; paragraphs do not.
- Prompts may be in English or Chinese.

## 4. Generate

One image. Single-quote the prompt; a prompt with a quote mark or apostrophe
of either kind goes in a jobs file instead, even a jobs file of one, where the
shell cannot touch it:

```
python3 SKILL_DIR/scripts/z_image_turbo.py generate --prompt 'A lighthouse on a rocky coast at dusk, warm light in the lantern room, cinematic' --out lighthouse.jpg
```

Several: write a jobs file and run it once, since the model loads once per run.
Keep jobs files out of the user's folder; a temporary folder will do. `out` is
relative to `--out-dir`, and its extension — `.jpg`, `.jpeg`, `.png` or `.webp`
— chooses the format. An image already at a path counts as done, so use new
file names.

**Seeds.** A job without a `seed` gets one from its prompt and its `out` name,
and every `made` line prints it. So several jobs with one prompt and different
names give different images, and the same job gives the same image every time.
One name in two formats, `logo.png` and `logo.jpg`, is one image; the same image
under another name needs its seed passed on.

```json
[
  {"prompt": "Food photography, top-down view: porridge with blueberries and sliced banana in a rustic ceramic bowl, natural daylight, wooden table, no text", "out": "porridge.jpg"},
  {"prompt": "A hand-painted wooden sign reading \"OPEN DAILY\" hanging in a bakery door", "out": "sign.png", "seed": 7}
]
```

```
python3 SKILL_DIR/scripts/z_image_turbo.py generate --jobs jobs.json --out-dir images
```

| Option | Default | What it does |
|---|---|---|
| `--resize WxH` | none | the final size, such as `1200x630`, `1200x1800` or `512x512`: centre-crops to its shape and scales to it, where the drawing is not already that size |
| `--size WxH` | `--resize`'s shape and area, from 512×512's area to 1024×1536's; else `1024x1024` | the size the model draws at, which `--dry-run` shows. Leave it out |
| `--quality N` | `85` | JPEG and WebP quality |
| `--steps N` | `9` | what the model is tuned for; leave it |
| `--force` | off | redraws images that already exist |
| `--dry-run` | off | checks the jobs and lists what would be made |

**It takes about 40 seconds for each megapixel the model draws** — not the
final size: a 512×512 thumbnail is drawn at its own size and takes about 10
seconds, a 1024×1024 image 40, and a 1200×1800 print is drawn at 1024×1536 and
takes about a minute. Measured on an M5 Pro;
earlier and base chips are slower. Tell the user roughly how long a batch will take, and
run `generate` in the background where your host can: many hosts stop a command
at two minutes. A line appears only as each image finishes, so wait for the
command to exit rather than reading its output over and over.

Each image gets one line: `made PATH`, `have PATH` (already there, skipped),
`fail PATH: reason` (the batch went on), or `stop PATH: reason` (the batch
stopped: interrupted, a full disk, or a MacBook down to 10% battery).

| Exit | Meaning | Next |
|---|---|---|
| 0 | every job has its image | step 5 |
| 1 | some jobs have none | a battery stop: ask the user to plug in first. Otherwise run the same command once more; it makes only what is missing. The same failure twice: stop and report it |
| 2 | the command or the jobs file is wrong; nothing was made | fix what the message names |
| 3 | not set up, or the model would not load | step 1. If the check then says `ready`, stop and show the user the message |

## 5. Look at every image

View each image before handing it over, where you can see images. A miss is
anything that contradicts the prompt or could not be so: a wrong count of
things, garbled lettering, a mangled hand, a candle standing on a book's open
pages. Redraw a miss alone, with the same `--resize` as before, and either a
reworded prompt, which brings its own new seed, or the same prompt with a new
`--seed`:

```
python3 SKILL_DIR/scripts/z_image_turbo.py generate --prompt '…' --out images/porridge.jpg --seed 8 --force
```

A prompt with a quote mark or apostrophe goes in a jobs file of one, run with
`--force`; `--force` on the whole jobs file would redraw every image in it.
Redraw an image at most twice; then hand it over and say what is still wrong.

Give the user the full path of each image. Pass on, in your own words, anything
the command said that they need, such as a note that an image was enlarged;
quote none of its output.
