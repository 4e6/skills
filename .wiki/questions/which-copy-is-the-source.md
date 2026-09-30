---
type: Open Question
title: Which copy of the skill is the one to edit?
description: The skill moved here on 2026-09-30 and a copy stayed in the private codebase it was developed in, with its tests, its schema generator and the reference its checks were ported from. Until one side is the source, the two will drift.
tags: [process, distribution]
timestamp: 2026-09-30T14:00:00Z
status: open
sources: [skills/training-week-meal-plan/**]
source_commit: e71d6a4eac78ebe897dd9abea3f82f6815e160b5
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

On 2026-09-30 this repository changed the skill on its own: `validate.py` gained
`origin-without-ingredients`, a finding the reference implementation does not
emit, and the frontmatter `description` and `README.md` stopped promising seven
days. Copying the folder back unchanged would fail a parity suite that refuses a
code only one side emits.

# Until it is answered

Edit the skill in one place only, and say which in the commit.
