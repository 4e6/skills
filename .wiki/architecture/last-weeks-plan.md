---
type: Module
title: Each week's files, and last week's dishes
description: A run writes plan-<first day>.json and .html, so weekly runs from one folder never overwrite each other. From those names last_week.py finds last week's plan and hands back its lunch and dinner names, and nothing else is kept.
tags: [architecture, files]
timestamp: 2026-09-30T14:00:00Z
sources: [skills/training-week-meal-plan/SKILL.md, skills/training-week-meal-plan/references/last-week.md, skills/training-week-meal-plan/scripts/last_week.py]
source_commit: 01265d60524785eee06f6acb56fc010adb69359b
---

# Each week's page is named for its first day

A run writes `plan-<date>.json` and `plan-<date>.html`, `<date>` being the plan's
first day as YYYY-MM-DD. With fixed names, an athlete running the skill weekly
from one folder — which is how a weekly tool gets used — silently replaced last
week's page, including one they might still be cooking from.

- **The format is stated**, not left to the example, or a host serving a
  European athlete writes `28-09-2026` and the names stop sorting by week.
- **Stated once, where the file is first written** (step 3). Every later step
  spells the placeholder, so the commands a host copies carry it.
- **The first day, not the day it is written**, so names sort by week and a redo
  lands on the same file. It is `days[0]`, even when that day is excluded — it is
  what `week_label` starts from.
- **Same first day, same file.** A redo replaces its own pair; a different week
  never touches it. Claude Code's Write tool refuses to overwrite a file the
  session has not read, so a redo reads the earlier same-week document first.
- **No date, or no year: plain `plan`.** A guessed date files the page under the
  wrong week and looks authoritative. *No year* is spelled out because an athlete
  who says *Thursday the 24th* has given nothing to build a filename from.

The scripts take paths and have no default names. `last_week.py` exits 0 when it
finds nothing, and 2 only for a malformed date, whose shape it checks by pattern
before parsing, because newer Pythons accept more date forms and the answer must
not depend on which one is installed.

# Last week's plan is read for its dishes, and nothing is kept

An athlete planning every week from one folder should not get last week's dinners
back. So at step 2, once the days are settled, `last_week.py` looks for last
week's plan and hands back its lunches and dinners, and no lunch or dinner this
week repeats one unless the athlete asked. This was chosen over *nothing kept
between runs* and over storing the intake beside the plan, which would be an
account in all but name.

**The script is the only reader, and the defence is how little it hands back.**
The folder is wherever the host runs, where anyone could have left a file with
the right name, and every free-text field in it would otherwise reach the host's
context. So the reference tells the host never to open the file, and the script
prints dish names only: one line each, sixty characters at most, fourteen at
most, with control characters, direction overrides and invisible tag characters
removed. That set is **listed rather than asked of `unicodedata`**, whose answer
moves with the Python installed, and a zero-width joiner stays because removing
it splits one emoji into two. A name that reads like an instruction is still a
name.

**Which files.** A name step 3 would write, directly in the folder, whose first
day falls in the calendar week before the new plan's. A plan always ends on a
Sunday, so that is one to seven days old and nothing else decides staleness.
**Last week may be two plans** — written Monday, re-planned from Thursday — so
the newest answers for the days it covers and each older one only for the days
before that. Reading only the newest dropped Monday to Wednesday's dinners. A
redo's own file, an earlier plan in the same week, the week before last and a
plain `plan` are never read.

**Skipped, never repaired.** A plan is passed over when `validate.py` could not validate it at all, when it is a symbolic link, when it is over a megabyte, and when
its day names do not say which dates they are — each one weekday, each later than
the one before, the first the weekday the file is named for. A plan with
**findings is still read**: plans ship with findings after two repairs, plans
written without Python were never checked, and a dish name is sound whatever the
quantities say.

**A day's dishes count for the date its name gives.** A day or meal marked
`excluded` was eaten elsewhere, and a slot's meal is the first listed — the one
the checks count. An earlier attempt borrowed the validator's day-order check to
decide which plans say no dates, and was wrong both ways: it skipped a plan with
a day left out, and passed `Friday,Saturday` because it compares names joined
with commas.

**No carry-over of leftovers.** Most weeks leave half a loaf, but the plan cannot
know whether the week was cooked as written, and a guessed fridge entry that
matches no row switches that food's comparison off — a guessed *rolled oats*
could take oats off the list unchecked. The athlete can see their
fridge; step 1 asks.

**Said once, in the reply, never as a file.** When the script found last week,
step 7 says the lunches and dinners were kept different, as one of the things
assumed — naming no file, script or date. Not in `training_overview.summary`,
which is about training. Without Python there is no read and nothing is said.
