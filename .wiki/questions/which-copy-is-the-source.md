---
type: Open Question
title: Which copy of the skill is the one to edit?
description: The skill moved here on 2026-09-30 and a copy stayed in the private codebase it was developed in, with its tests, its schema generator and the reference its checks were ported from. Until one side is the source, the two will drift.
tags: [process, distribution]
timestamp: 2026-09-30T14:00:00Z
status: open
sources: [skills/training-week-meal-plan/**]
source_commit: 1fe8e50b9c494a943c7577be596b0680ea2425dc
---

# The question

`skills/training-week-meal-plan/` here is a copy of the folder as it stood in
the private codebase on 2026-09-30. That copy is still there, and three things
that hold this one together stayed with it:

- **the test suite** — the payload walk (no network, nothing outside itself, the
  vocabulary rules), the frontmatter and layout rules in
  [editing a skill](/conventions/editing-a-skill.md), the byte comparison of
  `examples/sample-plan.html`, and the scripts' tests run on Python 3.9 as well
  as a newer default;
- **the schema generator** — `references/plan-schema.json` is derived there from a
  larger plan schema, minus an omission list, so a hand edit here is overwritten
  the next time it is copied across;
- **the reference implementation** that `validate.py` is held to by a parity
  suite, with its divergences declared rather than accidental.

Nothing in this repository runs any of it.

# The options

- **The private codebase stays the source**, and this repository is published from
  it. The tests and the generator keep working; every change here is a copy, and
  a change made here first is lost.
- **This repository becomes the source.** The skill's own tests move here, in
  Python so they need nothing but the skill's runtime; the schema stops being
  derived and becomes this repository's own file; the other side stops shipping
  the folder.

# The copies have already diverged

On 2026-09-30 this repository changed the skill on its own, and every part of it
has moved:

- `validate.py` gained `origin-without-ingredients`, a finding the reference
  implementation does not emit, which a parity suite that refuses a code only one
  side emits would fail;
- `plan-schema.json` gained a day's `snacks` and lost a meal's `extra`, by hand, so the schema is no longer what the generator would write
  and a byte comparison against it would fail;
- `fuelling.md` gained the daily targets and the snack rules, and moved food
  served with a dish every time into its recipe;
- `render.py`, `plan.css`, the example plan and its page, the no-page reply,
  `SKILL.md` and the README changed with them.

Copying the folder back unchanged would fail the old repository's checks in more
than one place; copying the other way would undo all of it.

# Until it is answered

Edit the skill in one place only, and say which in the commit.
