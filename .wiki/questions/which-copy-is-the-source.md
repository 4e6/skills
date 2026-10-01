---
type: Open Question
title: Which copy of a skill is the one to edit?
description: Two skills here have a second copy elsewhere. training-week-meal-plan's kept its tests and schema generator; llm-wiki's is where it was developed, though the author's assistant now loads this one. Until one side is the source, they drift.
tags: [process, distribution]
timestamp: 2026-10-01T12:19:17Z
status: open
sources: [skills/training-week-meal-plan/**, skills/llm-wiki/**]
source_commit: 6baaea7682972296b9ace115aa6a8e9adacec9c5
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

Nothing in this repository runs any of it. CI now runs here
([the zip release](/architecture/the-zip-release.md)), so tests that moved would
have somewhere to run.

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
- on 2026-10-01 it gained `dish-without-recipe` and `recipe-without-dish`,
  which the reference implementation does not emit either and which have no
  test here: a meal naming a dish no recipe at its sitting has, the case to add
  first wherever the tests end up;
- `plan-schema.json` gained a day's `snacks` and lost a meal's `extra`, by hand, so the schema is no longer what the generator would write
  and a byte comparison against it would fail;
- `fuelling.md` gained the daily targets and the snack rules, and moved food
  served with a dish every time into its recipe;
- `render.py`, `plan.css`, the example plan and its page, the no-page reply,
  `SKILL.md` and the README changed with them.

Copying the folder back unchanged would fail the old repository's checks in more
than one place; copying the other way would undo all of it.

# llm-wiki has the same question

`skills/llm-wiki/` was copied on 2026-09-30 from the author's own collection of
Claude Code skills, where it was developed. It came without tests to leave
behind, and it was changed on the way in, so nothing false went out with it:

- the frontmatter gained `license`, `compatibility` and `metadata`, and the
  folder a `LICENSE`;
- the scope note no longer says where the skill is kept or linked from, and the
  script's path is an example rather than one machine's;
- two references to skills that are not here were cut;
- two faults a review found were fixed here only: a setup that failed halfway
  was never retried, and its venv was not ignored; and `okf.py` let a leading
  `/` in `sources` match at any depth.

The same day, the author's assistant was pointed at this copy, so the other is
loaded by nothing and has none of the fixes. That leans toward this side being
the source, but the other copy still exists. A copy either way has to keep the
changes above. Until one side is the source, edit it in one place and carry the
change across.

# Until it is answered

Edit each skill in one place only, and say which in the commit.
