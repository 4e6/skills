---
type: Module
title: Z-Image Turbo on macOS
description: One model on one kind of machine, and no fallback. The one skill here whose substance is a download, so its network use is fenced into a setup the user agrees to, pinned to what was tested, and generating stays offline.
tags: [architecture, images, distribution]
timestamp: 2026-09-30T16:00:00Z
sources: [skills/z-image-turbo-macos/**]
source_commit: 60984927c08b2927285a9aca5f832877c13b332c
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

- **The network is fenced into `setup`.** `check` reads the machine and the
  cache and downloads nothing, and prints the figure the host must put to the
  user before setup runs. `generate` switches the Hugging Face hub offline, so a
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
  1.2 GB environment each time; and a folder symlinked from a checkout would put
  it inside the repository.
- **Setup deletes only what it made.** It rebuilds a broken environment, and the
  path can be moved with an environment variable, so a user naming a folder they
  own would have had it emptied. A marker file written at creation is the only
  licence to delete; any other non-empty folder is a refusal.
- **A seed follows the prompt and the file's name**, not the job's place in the
  list. The predecessor used base seed plus index, so reordering a batch redrew
  every image; a seed from the prompt alone made four jobs asking for four takes
  on one prompt come out identical. A job that would still repeat another is
  refused before anything is generated.
- **The drawing size follows the final shape.** Asked for a 1200×630 header, a
  host had to guess a drawing size; now `--resize` alone picks about one
  megapixel in its shape, so the crop throws little away.
- **The MLX buffer cache is capped at 1 GB.** Uncapped, MLX keeps freed buffers
  until memory runs short, and one image showed a 34 GB peak on a 48 GB Mac. The
  cap is mflux's own low-memory value.
- **Output is checked before the model loads.** A folder that cannot be written
  would otherwise cost a minute per image to discover. An image is written
  aside, flushed and renamed, because a file that exists is skipped as done.
- **A MacBook on battery stops at 10%.** mflux registers its battery cut-off only
  in its own command line; the predecessor drove the Python API and documented a
  cut-off it never had.
- **Exit 1 always means a re-run can help, and an unexpected error is 4.**
  Python reports any uncaught exception as 1, which the skill tells the host to
  retry; a fault in the script would have been retried forever. Retries are also
  capped at one in `SKILL.md`, since a battery stop or a Ctrl-C repeats.

# How it meets the meal-plan skill

[Dish photos](/architecture/dish-photos.md) are drawn only where the host has a
tool that makes a picture from a description. On a Mac with this skill
installed, it has one. Neither skill names the other. The meal plan's photo —
square, 480 px, JPEG at about quality 80, at most 150 KB — is
`--resize 480x480 --quality 80`, which came to 31 KB for a bowl of porridge.

# Measured, 2026-09-30

On an M5 Pro with 48 GB, at 9 steps:

| Size | Time | Peak memory footprint |
|---|---|---|
| 768×768 | 21 s | 26 GB uncapped |
| 1024×1024 | 38–40 s | 34 GB uncapped, 18 GB capped |
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

**Not measured:** a first `setup` that downloads the model, a Mac with less than
48 GB, any M1 to M4 timing, and Haiku or Opus as the host. No evaluation suite
exists, the same known gap as the [meal-plan skill](/conventions/editing-a-skill.md#where-the-skill-knowingly-differs-from-the-guidance).
