# z-image-turbo-macos

An [Agent Skill](https://agentskills.io) that lets your assistant draw images on
your own Mac: one specific model, **Z-Image Turbo**, on one kind of machine, an
**Apple Silicon Mac**.

Describe a picture, or a batch of them, and the assistant writes the prompts,
draws them on the Mac's GPU and hands you the files — JPEG, PNG or WebP, at the
size you want. No API key, no account, no per-image cost, and nothing leaves the
Mac once it is set up.

## What it runs

- **The model:** Z-Image Turbo from Tongyi-MAI, 6B parameters, in the 8-bit MLX
  build [`mflux-community/z-image-turbo-mflux-q8`](https://huggingface.co/mflux-community/z-image-turbo-mflux-q8),
  pinned to one revision. It is good at photographic images and at short text
  inside a picture, in English or Chinese.
- **The runtime:** [mflux](https://github.com/filipstrand/mflux), a native MLX
  port of diffusion models, pinned to one version.

It supports nothing else. There is no other model to choose and no hosted
fallback; on a machine that cannot run it, it tells you so and stops.

## Requirements

- **A Mac with Apple Silicon** — M1 or later. Not an Intel Mac, not Linux, not
  Windows: MLX runs only on Apple's GPU.
- **16 GB of memory or more.** The model holds 12–14 GB while it draws; with
  less, the Mac swaps and each image takes many minutes.
- **About 13 GB of free disk.**
- **Python 3.10 or newer**, native to Apple Silicon — Homebrew's `python` is
  fine. macOS's own `python3` is 3.9 and too old for the model, though the skill's
  script runs on it and finds the newer one.

## Setup, once

The first time, the assistant checks the Mac and asks before it downloads
anything. Setup then fetches about 12 GB:

- mflux and its dependencies from PyPI, into its own environment at
  `~/.cache/z-image-turbo-macos/venv` — about 1.2 GB. Set `Z_IMAGE_TURBO_VENV` to
  put it elsewhere.
- the model from Hugging Face, into the Hugging Face cache (`~/.cache/huggingface`,
  or wherever `HF_HOME` points) — 11 GB. No Hugging Face account or token is
  needed.

That is the only time the skill uses the network. Drawing is offline.

## How fast

About 40 seconds for a one-megapixel image on an M5 Pro, measured; earlier and
base chips are slower. A batch loads the model once, so twenty images take about
twenty times as long as one.

## Removing it

Delete the skill's folder, `~/.cache/z-image-turbo-macos/`, and
`~/.cache/huggingface/hub/models--mflux-community--z-image-turbo-mflux-q8/`.

## Licence

The skill is MIT — see [LICENSE](LICENSE). Z-Image Turbo is released under
Apache-2.0, and mflux under MIT; neither is part of this folder, and setup
fetches them from their own publishers.
