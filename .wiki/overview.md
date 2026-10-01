---
type: Overview
title: What this repository is
description: Agent Skills that run in somebody else's session. training-week-meal-plan turns a described training week into meals, a shopping list and a printable page; z-image-turbo-macos draws images on a Mac; llm-wiki keeps a codebase's wiki.
tags: [overview]
timestamp: 2026-10-01T11:43:32Z
sources: [/README.md, skills/training-week-meal-plan/SKILL.md, skills/z-image-turbo-macos/SKILL.md, skills/llm-wiki/SKILL.md]
source_commit: e5ae3bf78ef71fa3efb195ca7b30307aea5865c5
---

# What it is

A collection of [Agent Skills](https://agentskills.io), one folder each under
`skills/`. A skill here is not a program this repository runs. It is a
**payload**: a folder somebody copies into their own assistant, where it runs on
their tokens and on whatever that host happens to provide
([the payload](/architecture/the-payload.md)).

There are three. `training-week-meal-plan`, below, is the one most of this bundle
is about. `z-image-turbo-macos` draws images from prompts with one model on one
kind of machine ([Z-Image Turbo on macOS](/architecture/z-image-turbo-macos.md)).
`llm-wiki` keeps a knowledge base like this one, and this bundle is kept with
it. Those two are not pure payloads
([where they bend](/architecture/the-payload.md#the-skills-that-cannot-be-pure-payloads)).

# What the meal-plan skill does

An endurance athlete describes their training week — pasted from a coach, or in
rough words — and gives their body weight. The skill turns that into:

- a plan from the first day they need through to Sunday, breakfast, lunch and dinner, with
  fuel lines on the sessions that need them;
- a line of snacks on each day the meals fall short of its carbohydrate or
  protein target — how much, and example food, never on the list;
- recipes with quantities, where every cooked portion is eaten by a named meal;
- a shopping list grouped by aisle, which buys what the week uses;
- where the host can run Python, a checked plan and a single printable HTML page.

The one claim it exists to make is **carbohydrate periodised to the week**: the
hardest days get the most carbohydrate, and the plan states which days those are
and is checked against that statement
([carb periodization](/domain/carb-periodization.md)).

# How it is built

Seven steps in `SKILL.md`, which the host follows:

| Step | What happens | Page |
|---|---|---|
| 1 | Ask for the week, the weight, three optional things and which days | [the intake](/architecture/the-intake.md) |
| 2 | Read the fuelling rules, and look for recent plans to vary the dishes | [carb periodization](/domain/carb-periodization.md), [recent weeks](/architecture/last-weeks-plan.md) |
| 3 | Write the plan as JSON against the published schema | [origin, repeat and leftover](/domain/origin-repeat-and-leftover.md) |
| 4–5 | Check it with `validate.py`, repair at most twice | [the validator](/architecture/the-validator.md) |
| 6 | Render the page with `render.py`, with photos where the host can draw | [the printable page](/architecture/the-printable-page.md), [dish photos](/architecture/dish-photos.md) |
| 7 | Hand the page over and report | [the handover](/architecture/the-handover.md) |

Two invariants carry most of the weight, stated in the rules and, where Python
runs, checked in code: [every cooked portion is eaten](/invariants/portion-conservation.md)
and [the list buys what the week uses](/invariants/the-list-buys-what-the-week-uses.md).
A third is a rule the whole skill is organised around:
[nothing about the athlete is invented](/invariants/nothing-about-the-athlete-is-invented.md).

Whether a host following the rules writes the right plan is measured on demand,
outside the skill, by [the evals](/architecture/the-evals.md): race weeks so far.

# Where it came from

The skill was developed inside a larger, private codebase and moved here on
2026-09-30. Its test suite, the generator for its plan schema and the reference
implementation its checks were ported from all stayed behind. Which copy is now
the one to edit is [not yet settled](/questions/which-copy-is-the-source.md).

The pages in this bundle keep the reasoning and the measurements behind the
skill's rules. They do not keep the mechanics of the old repository, which a
reader here cannot see.
