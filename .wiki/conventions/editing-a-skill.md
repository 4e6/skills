---
type: Convention
title: Editing a skill
description: Re-read the two upstream guides before editing and never copy them here. The skill states the rule and this bundle carries the argument. Prose is not cut on argument alone, and a change to behaviour or to the page is judged by running it.
tags: [skills, authoring, review]
timestamp: 2026-09-30T21:38:47Z
sources: [skills/training-week-meal-plan/SKILL.md, skills/z-image-turbo-macos/SKILL.md]
source_commit: bae027044545122fadf81e46fed4acac4f6b0a62
---

# Read the guides, and point at them

Before editing any skill here, read both:

- the Agent Skills specification — <https://agentskills.io/specification>
- Anthropic's skill authoring guidance —
  <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices>

**Point at them; never copy either into this repository.** Both are revised
upstream without notice, and a copy is right the day it is written and silently
wrong afterwards. A paraphrase drifts even when its source does not: a summary of
a list once quietly lost several of its items.

`agentskills validate ./skills/<name>`, from the `skills-ref` package
(<https://github.com/agentskills/agentskills>), is the authoritative check
against the specification. CI runs it on every skill, on every pull request
([the zip release](/architecture/the-zip-release.md#what-ci-checks-and-on-what)).

# The skill states the rule; this bundle carries the argument

Every line of `SKILL.md` is loaded into a stranger's context window, so *concise
is key* and *assume Claude already knows* are rules about somebody else's
tokens. The skill keeps the instruction and the facts a model cannot work out from
where it stands; the reasons a maintainer needs live here. A first draft of the
handover step put both in the skill and ran to 48 lines for five instructions.

# This repository's own rules for a skill

On top of what the guides say, and not a restatement of them:

- a reference's Contents lists every `##` section it has;
- `README.md` is not linked from `SKILL.md`: it is for a human and a listing page,
  and linking it would spend the model's attention on the shop window;
- every script the documentation names exists, and every script that ships is
  named;
- `license`, a `LICENSE` file, `metadata.author` and `metadata.version` are set;
  `allowed-tools` and `disable-model-invocation` are absent
  ([the payload](/architecture/the-payload.md#frontmatter-the-host-reads));
- `compatibility` says whether the skill uses the network — and when it does, for
  what and how much — and names a runtime exactly when a script needs one;
- a skill that only works with one model or one kind of machine says so in its
  name, its `description`, its `compatibility` and its first paragraph
  ([why](/architecture/z-image-turbo-macos.md#what-it-is-and-what-it-refuses-to-be)).

Nothing in this repository checks any of it yet, though CI now has a place for
it ([which copy is the source](/questions/which-copy-is-the-source.md)).

# Where the skill knowingly differs from the guidance

- **The checklist never goes in the response.** The guidance has the agent copy
  it into its reply; here the reply is read by an athlete, not the author the
  pattern assumes ([the handover](/architecture/the-handover.md#progress-is-the-hosts-and-the-reply-is-the-athletes)).
- **The name is a noun phrase**, not the preferred gerund
  ([why](/architecture/the-payload.md#frontmatter-the-host-reads)). Renaming it
  breaks every install, since the folder name must match.
- **It is not tested systematically across models, and has no eval suite.** The
  simulated runs recorded here are mostly Opus, with some Sonnet and Haiku. That
  is a known gap, not a decision.

# Do not cut prose on argument alone

With no eval suite, nothing shows that removing a rule costs nothing. Where a
rule's value is unmeasured, leave it.

# How a change to behaviour is measured

The measurements in this bundle share a method, and it is the one to reuse:

- **Hosts are subagents** loading only their own copy of the skill, from outside
  any checkout, with the date given in the host's own form and no time of day.
- **Athletes are frozen personas**, answering through a responder that never sees
  the skill.
- **Two arms, before and after**, assigned blind; a scorer counts faults, and one
  pairwise judge per scenario compares the arms as X and Y.
- **Simulated hosts are not real ones.** Say which it was, and what the run did
  not cover — model sizes, real hosts, real tools.

# Judging a change to the page

Print the page from headless Chrome and check it, rather than eyeballing a
screenshot:

- **no recipe split** across a page or a column, checked per column off
  `pdftotext -bbox-layout`, with a positive control — the same page with recipes
  allowed to split — that must be caught;
- **the page count** against the page before, on the sample and on long plans;
- **the phone at a true 390 px**, laid out inside an iframe of that width —
  headless Chrome will not lay a window out narrower than 500 — and compared **at
  full height**: a one-screen screenshot once passed a change that altered the
  recipes below it;
- **the wide screen** too, on both sides of its two thresholds (about 790 px for
  the paper's measure, 1180 px for the rail): a tick box once wrapped the longest
  shopping rows only there, and the rail at 1100 px scrolled the page sideways;
- then **a reader**, blind where the change is a matter of taste — files named
  identically in both arms, with the key kept outside anything the reader can
  list, since a tool's file naming once revealed which arm a reader held.

Regenerate `examples/sample-plan.html` in the same commit
([the printable page](/architecture/the-printable-page.md#the-example-is-compared-byte-for-byte)).
