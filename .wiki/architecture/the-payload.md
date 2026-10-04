---
type: Module
title: The skill is a payload
description: A skill folder is copied out whole and runs where this repository does not exist, on whatever the host provides. What each skill may reach — the network, packages, a newer Python — and why, skill by skill.
tags: [architecture, distribution]
sources:
  - resource: skills/training-week-meal-plan/**
  - resource: skills/z-image-turbo-macos/SKILL.md
  - resource: skills/z-image-turbo-macos/scripts/z_image_turbo.py
  - resource: skills/llm-wiki/SKILL.md
  - resource: skills/llm-wiki/scripts/**
  - resource: skills/work-on-github-issue/SKILL.md
  - resource: skills/research-plan-build-review/SKILL.md
sources_digest: 6d0b8d441737a60a
---

# The boundary

`skills/training-week-meal-plan/` is copied out whole — by `npx skills`, by a
symlink, by a zip uploaded to a web host
([the zip release](/architecture/the-zip-release.md)) — and runs in a stranger's session
([what this repository is](/overview.md)). Every
install path takes the folder alone, never the repository around it. Three
consequences look like restrictions and are the design.

## Nothing of its own reaches the network

Not for a font, not for a renderer, not for telemetry. That covers the markup —
no `@import`, `<link`, `<script`, remote `url()` or `src` — **and the verbs**:
no `curl`, `wget`, install command, fetch call or networking import. The second
half matters more, because what the skill ships is instructions an agent
executes, and prose reaches the network as easily as markup does.

The host may still publish the finished page with its own tool, kept private
([the handover](/architecture/the-handover.md)). That is the host's network, not
the payload's, and `compatibility` says so.

It follows that **the payload cannot measure anything**. There is no link on the
page and nothing to count arrivals with. Evidence about how the skill behaves
comes from running it, never from telemetry.

## Its scripts are Python 3.9, standard library only

Python 3 is on every macOS and Linux box and in the common sandboxes; almost
nothing else is. `compatibility` names that runtime **exactly when a script is
present**, because it is the field a client parses: a runtime claimed that the
host lacks can make it refuse a skill that is in fact pure instructions.

Python is **optional**. Without it the plan is still written, into the reply,
and the reply says it was not checked
([the handover](/architecture/the-handover.md#when-there-is-no-page)).

What each script may import is a per-script fact, not a shared list: in the 3.9
standard library, reaching neither the network nor any path it was not handed.
A shared list stops meaning anything once there are two scripts, because one
satisfies it on the other's behalf.

- `validate.py` reads the one file it is given.
- `render.py` imports `validate.py` beside it, so the rounding, the dish
  counting and the unit tables have one Python copy, not two. It also reads the photos it is
  handed — each a relative path inside its own folder, no `..`, not a link out —
  and admits `base64` and `hashlib` for them alone.

**`render.py` leaves no byte-code behind.** It switches the import cache off
before importing `validate.py`, because a cache write into the skill's own
folder on every run is a write its docstring says never happens.

## It names nothing outside itself

No file under the skill names anything it could be read as promoting, and no
repository, issue number, absolute path or module outside the folder. A reader
who has only the skill cannot follow any of those. **Nor does it name a host or
its tools.** A tool is described by what it does — *whichever one puts a
question to the user with options to pick from* — so the skill reads the same to
every agent. Until 1.1 it named Claude Code's `AskUserQuestion` as an example.

Two lessons stand behind the rule, and both argue for thinking before any
sentence goes back in that the host is told to pass on: a host restating a
paragraph to the athlete personalises it, and a feature list typed by hand goes
stale when a feature ships.

The scripts' and the stylesheet's comments state their behaviour and their own
reason. The comparison with anything else lives in this bundle, if anywhere.

# Frontmatter the host reads

- **`allowed-tools` is deliberately absent.** It is experimental and support
  varies, and narrowing what the host hands over would make the skill ask for a
  tool that is not there. So whether the agent can run anything, draw anything
  or publish anything is the host's decision, and every step has a path for the
  host that cannot ([a missing capability is announced](/architecture/the-validator.md#a-missing-capability-is-announced)).
- **`disable-model-invocation` is absent**, because the skill exists to be found.
- **The name is a noun phrase**, `training-week-meal-plan`, which the guidance
  allows beside its preferred gerund. It is chosen for the words somebody types
  into a search box.

# Vocabulary the payload must not use

A single word list cannot express the rules, so there are several:

| Rule | Applies to |
|---|---|
| **Machinery the skill does not have** — a computed load field, a calendar brief, *the coach* as a party the skill hears from (a coach's week the athlete pastes is fine), a choice of plan language, localisation fields | the files the host reads as instructions: `SKILL.md`, `references/`, `scripts/`, `examples/` |
| **Anything outside the folder** — a product it could be read as promoting, repositories, issue numbers, absolute paths, `webcal://` | everything under the folder, except what `z-image-turbo-macos` installs and where ([why](/architecture/z-image-turbo-macos.md#it-is-not-a-pure-payload-and-where-it-bends)) |

`calendar` is on neither: the fuelling rules have to be able to say there is no
calendar, and that clause is what stops the model looking for one. The page's
feature is called a *photo*, one word used everywhere; *photographs* is avoided.

# The authoring guides bind harder here

The specification is what a stranger's client parses, so getting it wrong is
visible outside this repository. How the skill is edited is
[a convention of its own](/conventions/editing-a-skill.md).

# The skills that cannot be pure payloads

`z-image-turbo-macos` is an 11 GB model and a runtime that needs Python 3.12 to 3.14, so
it cannot ship its substance or run on the standard library. It keeps the
boundary's purpose rather than its letter: the network only in a setup the user
agrees to, pinned to what was tested, and drawing offline
([Z-Image Turbo on macOS](/architecture/z-image-turbo-macos.md#it-is-not-a-pure-payload-and-where-it-bends)).
Everything above still holds for `training-week-meal-plan`, and for any skill
that can hold it.

`llm-wiki` bends less. Its one script parses YAML and gitignore patterns with
two packages from PyPI, installed once into a venv in its own `scripts/` folder:
the only network use, and the only write into the folder. The venv ignores
itself, because the folder may sit inside the repository the skill documents. It needs `git`,
to list the files it tracks and hash them, and to read history for the diff a stale
page is to be checked against. Its instructions name Claude Code's own paths
and files, as instructions about the host.

`work-on-github-issue` ships no script; its work is on the network, through
`gh`, and it names GitHub and `gh` because they are its subject ([work on a GitHub issue](/architecture/work-on-github-issue.md#how-it-bends-the-payload)).

`research-plan-build-review` is a pure payload: no script, no network of its
own, and it names no host and no host's tools ([the loop](/architecture/research-plan-build-review.md)).
`work-on-github-issue` names it, the only case of one skill naming another, and
carries a paragraph of the loop so it works without it.

Their scripts' own facts, in the same terms as the others:

- `okf.py` runs `git` in the repository it is pointed at and reads the bundle;
  it writes nothing but `index.md` files under `index --write`, a page's
  `sources_digest` line under `pin`, and a page's `sources` and `status` lines
  under `upgrade --write`.
- `z_image_turbo.py` runs `sysctl` and the Pythons it finds, to learn what the
  machine is. Under Python 3.9's standard library it reads the environment and
  the model cache and writes nothing but a lock file and, in `setup`, the
  environment. Only under the environment's Python, which it builds, does it
  import `huggingface_hub` (in `setup`, for the model; pip fetches the packages), `mlx`, `mflux` and
  `PIL`; it writes the images it is told to, and nothing else.
