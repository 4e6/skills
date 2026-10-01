---
type: Open Question
title: Which countries should the intake offer as rows?
description: The place question offers four English-speaking countries and a typed row. Naming rows stopped hosts inventing regions, but an athlete in Lisbon found nothing near her on them.
tags: [intake, product]
timestamp: 2026-10-01T15:01:23Z
status: open
sources: [skills/training-week-meal-plan/SKILL.md]
source_commit: 3f5066241fd3cdce46a20049b3b77fe7007c40ff
---

# The question

[The intake](/architecture/the-intake.md) offers `United Kingdom`, `United
States`, `Canada`, `Australia` and a typed row for where the athlete lives. Rows
were named because hosts told to offer *broad regions* each invented their own,
and a region picks no dish and names no shop. The four are where an English plan
reads without a language gap, and UK against US is already a real difference in
what the shelf is called.

In the blind trial that measured the change, a Lisbon persona found *nothing
near me* on the four rows, while an invented *Europe* row had suited her.

# What is known

- The tools need at least two options, so the typed row cannot stand alone.
- Every athlete in the earlier runs typed a country anyway.
- The plan is written in English whatever the country: country picks dishes,
  shops and the units food is weighed in, never the language.
- **A country the rows do not name is cooked for.** Given Japan, Brazil, India
  or Poland, every eval run cooked that country's food and named its shops
  ([the evals](/architecture/the-evals.md#measurements)), with the country
  typed rather than picked. So the rows decide what is quick to pick, not what
  the plan can do.

# Open

Whether different rows — or rows chosen from what the host knows about the
athlete — serve better than the four.
