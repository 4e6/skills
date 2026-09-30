---
type: Module
title: Z-Image Turbo on macOS
description: One model on one kind of machine, and no fallback. The one skill here whose substance is a download, so its network use is fenced into a setup the user agrees to, pinned to what was tested, and drawing stays offline.
tags: [architecture, images, distribution]
timestamp: 2026-09-30T15:00:00Z
sources: [skills/z-image-turbo-macos/**]
source_commit: 60984927c08b2927285a9aca5f832877c13b332c
---

# What it is, and what it refuses to be

`z-image-turbo-macos` draws images from prompts with **Z-Image Turbo** — the
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
the model is 11 GB, far too big to ship in the folder, and mflux needs Python
3.10 or newer, which macOS does not provide. What the skill keeps instead:

- **The network is fenced into `setup`.** `check` reads the machine and the
  cache and downloads nothing, and prints the figure the host must put to the
  user before setup runs. `generate` switches the Hugging Face hub offline
  before mflux is imported, so a missing file is an exit 3 rather than an 11 GB
  download nobody agreed to.
- **What is downloaded is what was tested.** mflux is pinned to a version and
  the model to a revision. The revision's file sizes are written into the script,
  so the standard library can tell a complete download from a partial one
  without the environment and without asking the hub. That pin mattered at once:
  the repository's head moved while the skill was being written, adding only a
  model card.
- **It names what it installs, and nothing else.** The model, mflux and the
  cache locations appear because the skill cannot be described without them. The
  README links the model's page and mflux's repository; the payload's rule
  against naming anything outside the folder still holds for everything else.

The script itself stays on Python 3.9 until it needs the model: `check`,
`setup` and all of `generate`'s input checks run on the system `python3`, and
only then does it re-run itself under the environment's Python. Hosts type
`python3`; a skill that needs them to find `python3.14` first fails on the first
run of every host that doesn't.

# Why the pieces are shaped so

- **The environment lives outside the skill's folder**, in the user's cache.
  Installing or updating a skill replaces its folder, which would throw away a
  1.2 GB environment each time; and a folder symlinked from a checkout would put
  it inside the repository.
- **A seed follows its prompt**, not its place in the list. The predecessor used
  base seed plus index, so reordering a batch redrew every image. Now the same
  prompt redraws the same picture, and a different picture needs a new seed —
  which is why step 5 redraws one image alone rather than `--force` on the list.
- **An image is written aside and renamed.** `generate` skips any path that
  exists, so a half-written file left by an interrupt would pass as finished.
- **A MacBook on battery stops at 10%.** mflux registers its battery cut-off only
  in its own command line; the predecessor drove the Python API and documented a
  cut-off it never had. This script registers one.
- **mflux's progress bars are off.** One bar per step buried the one line per
  image that the host actually reads.

# How it meets the meal-plan skill

[Dish photos](/architecture/dish-photos.md) are drawn only where the host has a
tool that makes a picture from a description. On a Mac with this skill
installed, it has one. Neither skill names the other. The meal plan's photo —
square, 480 px, JPEG at about quality 80, at most 150 KB — is
`--size 1024x1024 --resize 480x480 --quality 80`, which came to 31 KB for a
bowl of porridge.

# Measured, 2026-09-30

On an M5 Pro with 48 GB: about 40 s per one-megapixel image at 9 steps, whether
square or 1344×768, and the model's load folded into the first image. Three
images in 128 s. An interrupt stopped the batch mid-image, kept the finished
one, left no partial file and exited 1, and the re-run redrew the same picture
byte for byte. `setup` built the environment in 25 s, with pip's cache warm and
the model already downloaded.

**Not measured:** a first `setup` that downloads the model, a 16 GB Mac, any M1
to M4 timing, sizes much above one megapixel, and the prompt guidance in step 3
beyond a handful of images.
