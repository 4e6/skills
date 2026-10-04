---
type: Module
title: Z-Image Turbo on macOS
description: One model on one kind of machine, and no fallback. The one skill here whose substance is a download, so its network use is fenced into a setup the user agrees to, pinned to what was tested, and generating stays offline.
tags: [architecture, images, distribution]
sources:
  - resource: skills/z-image-turbo-macos/**
sources_digest: 9f9a29248c96b873
---

# What it is, and what it refuses to be

`z-image-turbo-macos` generates images from prompts with **Z-Image Turbo** — the
8-bit MLX build `mflux-community/z-image-turbo-mflux-q8` — run by mflux on an
Apple Silicon Mac's GPU. It came out of a meal-plan skill in the private codebase
the [overview](/overview.md) mentions, where it was the first of four image
providers; the three hosted ones and the food-photo prompt stayed behind.

**The narrowness is the point, and the skill says so in its name, its
`description`, its `compatibility` and its first paragraph.** A host that knows
the skill cannot run on this machine stops and says why. One that half-knows
reaches for some other model or an online service, which is a different product
with different costs that the user did not ask for. So exit 3 means *cannot run
here*, and step 1 tells the host not to substitute anything.

# It is not a pure payload, and where it bends

[The payload](/architecture/the-payload.md) keeps a skill's own files off the
network and its scripts on Python 3.9's standard library. Neither can hold here:
the model is 11 GB, far too big to ship in the folder, and the packages need a
Python macOS does not provide. What the skill keeps instead:

- **The network is fenced into `setup`, and `setup` into `--yes`.** `check`
  reads the machine and the cache and downloads nothing, and prints the figure
  the host must put to the user. A bold rule in `SKILL.md` was not enough: a
  Haiku host ran setup without reporting that it asked. So without `--yes`
  setup downloads nothing and exits 2, and the flag is the host saying it asked. `generate` switches the Hugging Face hub offline, so a
  missing file is an exit 3 rather than an 11 GB download nobody agreed to.
- **What is installed is what was tested.** The model is pinned to a revision,
  and every package to the version in a working environment, not mflux alone:
  mflux leaves its dependencies loose, and a new `huggingface_hub` or
  `transformers` is exactly what changes how a model is found or a tokenizer
  loaded. The revision's file sizes are written into the script, so the standard
  library tells a complete download from a partial one without the environment
  and without asking the hub. The pin mattered at once: the repository's head
  moved while the skill was being written, adding only a model card.
- **The pins decide the Python, not the other way round.** The frozen set
  resolves from wheels alone on Python 3.12 to 3.14 and not on 3.10 or 3.11, so
  setup accepts exactly that range. MLX's wheels need macOS 14. Setup installs
  wheels only, so a missing one fails in seconds instead of a doomed source
  build — the failure the next Python release would otherwise bring.
- **It names what it installs, and Homebrew.** The model, mflux and the cache
  locations appear because the skill cannot be described without them. Homebrew
  appears too: its folder is where a native Python is usually found and a host's
  PATH often lacks it, and `brew install python` is the one-line answer to the
  commonest blocker. Nothing else outside the folder is named.

The script stays on Python 3.9 until it needs the model: `check`, `setup` and
all of `generate`'s input checks run on the system `python3`, and only then does
it re-run itself under the environment's Python. Hosts type `python3`; a skill
that needs them to find `python3.14` first fails on the first run of every host
that doesn't.

# Why the pieces are shaped so

- **The environment lives outside the skill's folder**, in the user's cache.
  Installing or updating a skill replaces its folder, which would throw away a
  1.4 GB environment each time; and a folder symlinked from a checkout would put
  it inside the repository.
- **Setup deletes only what it made.** It rebuilds a broken environment, and the
  path can be moved with an environment variable, so a user naming a folder they
  own would have had it emptied. A marker is the only licence to delete, and it
  is written before the environment is built, so an interrupted build is still
  setup's to redo; any other non-empty folder is a refusal. The marker also holds
  a hash of the pins — the pins alone, not the files' comments — so a skill
  update that changes them rebuilds the environment rather than calling the old
  one ready, and one that rewords a comment asks nobody to download again.
- **A seed follows the prompt and `out`**, not the job's place in the list. The
  predecessor used base seed plus index, so reordering a batch redrew every
  image; a seed from the prompt alone made four jobs asking for four takes on
  one prompt come out identical, and one from the file name alone made
  `a/hero.jpg` and `b/hero.jpg` collide. `out` relative to `--out-dir` keeps a
  jobs file's images the same from any folder; normalised and without its
  extension, `./fox.jpg`, `fox.jpg` and `fox.png` are one image, so a logo asked
  for in two formats is drawn alike twice. Every `made` line prints the seed, so
  any image can be made again under another name. Two names that would still
  draw one image are refused before anything is generated.
- **The drawing size follows the final size.** Asked for a 1200×630 header, a
  host had to guess a drawing size; asked for a 1200×1800 print, a one-megapixel
  drawing was enlarged 1.4 times. Now `--resize` alone sets the drawing to its
  shape and its area, so the crop throws little away and a print is drawn near
  its own size. Not larger than 1024×1536's area: 1536×1536 peaked at 24 GB,
  which would swap the 24 GB Mac the check calls enough. A note says when the
  final image is enlarged more than 1.5 times, below which it is hard to see.
- **Not smaller than 512×512's area, and a final size inside the bounds is drawn
  exactly.** The floor was once one megapixel, the size the model is trained
  around, so a 480 px dish photo was drawn at 1024×1024 and shrunk: a week of
  seven photos took 279 s. Drawn at 512×512 it took 9 s rather than 38, and
  side by side at 480 px the two were hard to tell apart — the smaller slightly
  softer in fine texture. A side that is a multiple of 16 needs no crop or
  scale, so `--resize 512x512` is the drawing itself. The cost falls on mid
  sizes too: a 1200×630 header is now drawn at 1200×624, not about a megapixel.
  With no `--resize`, the drawing is still 1024×1024.
- **The MLX buffer cache is capped at 1 GB.** Uncapped, MLX keeps freed buffers
  until memory runs short, and one image showed a 34 GB peak on a 48 GB Mac. The
  cap is mflux's own low-memory value.
- **Output is checked before the model loads.** A folder that cannot be written
  would otherwise cost a minute per image to discover. An image is written
  aside, flushed and renamed, because a file that exists is skipped as done.
- **A MacBook on battery stops at 10%.** mflux registers its battery cut-off only
  in its own command line; the predecessor drove the Python API and documented a
  cut-off it never had.
- **The host waits rather than polls.** A line appears only as an image
  finishes; the Haiku host read the output 84 times in one batch. `SKILL.md`
  now says to wait for the exit.
- **Exit 1 always means a re-run can help, and an unexpected error is 4.**
  Python reports any uncaught exception as 1, which the skill tells the host to
  retry; a fault in the script would have been retried forever. Retries are also
  capped at one in `SKILL.md`, since a battery stop or a Ctrl-C repeats.

# How it meets the meal-plan skill

[Dish photos](/architecture/dish-photos.md) are drawn only where the host has a
tool that makes a picture from a description. On a Mac with this skill
installed, it has one. Neither skill names the other. The meal plan's photo —
square, 640 px, JPEG at about quality 80, at most 400 KB — is
`--resize 640x640 --quality 80`, drawn at that size with nothing to crop, which
came to 55–68 KB for the sample week's eleven dishes. It was 512 px until the
page's tile grew to 80 mm.

# Measured, 2026-09-30

On an M5 Pro with 48 GB, at 9 steps:

| Size | Time | Peak memory footprint |
|---|---|---|
| 256×256 | 3 s | — |
| 512×512 | 9 s | — |
| 640×640 | 14–15 s | — |
| 768×768 | 21 s | 26 GB uncapped |
| 1024×1024 | 38–40 s | 34 GB uncapped, 18 GB capped |
| 1024×1536 | 63 s | 19 GB capped |
| 1536×1536 | 109–120 s | 39 GB uncapped, 24 GB capped |

Three images in about 130 s, the model's load folded into the first. An
interrupt or a SIGTERM stopped the batch mid-image, kept the finished ones, left
no partial file and exited 1; a re-run made only the missing ones. `setup` built
the environment in under a minute with pip's cache warm and the model already
downloaded.

**A host run.** Sonnet, given only the skill folder and a user asking for three
1200×630 blog headers, asked before setup, set up, generated the batch, saw one
image miss *steep*, and redrew that one with a new seed. It could not tell where
to run the script from or which drawing size to pick; both were fixed.

**A second host run.** Haiku, asked for four takes on a fox-head logo and one
with the words "Nordic Trails", square PNGs at 512 px: it set up from scratch,
put the prompts in a jobs file, got five different logos with the lettering
right, and handed them over. It did not report asking before setup, and read
the running batch's output 84 times; both are answered above.

**A third host run.** Opus, asked for a 1200×1800 watercolour for printing and
then for two more versions of it: it asked before setup with the check's own
figure, ran `setup --yes`, got two variants that differed, and redrew one whose
candle stood on the book's pages. It found the print enlarged 1.4 times, the
enlargement note printed twice, no redraw path for a prompt with an apostrophe,
and pip's output burying setup's; all four were fixed.

**Not measured:** a first `setup` that downloads the model, a Mac with less than
48 GB, any M1 to M4 timing, and a host run since the last round of fixes. No evaluation suite
exists, the same known gap as the [meal-plan skill](/conventions/editing-a-skill.md#where-the-skill-knowingly-differs-from-the-guidance).
