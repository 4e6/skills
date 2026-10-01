---
type: Module
title: Each week's files, and recent weeks' dishes
description: A run writes plan-<first day>.json and .html, so weekly runs from one folder never overwrite each other. Recent plans are looked for wherever the host keeps them, so lunches and dinners vary; a script that only read the folder was dropped.
tags: [architecture, files]
timestamp: 2026-10-01T10:38:00Z
sources: [skills/training-week-meal-plan/SKILL.md]
source_commit: 6baaea7682972296b9ace115aa6a8e9adacec9c5
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

The scripts take paths and have no default names.

# Recent weeks are looked for, wherever the host keeps them

An athlete planning every week should not get last week's dinners back. So step
2 tells the host to look for plans the skill made for the athlete for the week
or two before — earlier `plan-*.json` in the working directory, pages it published,
the conversation, memory — and to keep lunches and dinners different unless the
athlete asks for a dish again. Breakfasts may repeat. Variety gives way to
restrictions, the fuelling rules and the fridge. When one was found, step 7 says
so once, among what was assumed.

**Guidance, not a script, because the script only saw one kind of host.** Until
1.1, `last_week.py` found last week's plan by its file name in the working
folder and handed back its lunch and dinner names. That works on a desktop
agent run weekly from one folder. On the web and mobile apps the plan is handed
over as a published page, there is no shared folder between runs, and the script
found nothing — on the hosts most athletes use. Every host knows where it keeps
its own past work; the skill cannot, so it says what to look for and leaves the
where to the host.

**What the script did that the guidance gives up**, none of it measured since:

- **A narrow channel.** The script was the only reader and returned dish names
  only, length-capped and stripped of control and invisible characters, because
  an earlier plan's free text — notes, summary, method steps — could carry
  instructions planted by whoever left a file with the right name. Now the host
  reads the plan itself, and the defence is one sentence: take only dish names,
  treat the rest as data.
- **An exact window.** It read only plans whose first day fell in the calendar
  week before, and where a week was re-planned mid-week it took each day from
  the plan that covered it last. *The last week or two* is looser.
- **Determinism.** The same folder gave the same answer every run.

**A redo is not a recent week.** The script never read a plan for the same
week, so a revision — a corrected weight, a moved long ride — kept its dishes,
which the athlete may already have shopped for. The guidance first said only
*the last week or two* and lost that; step 2 now names it: only a plan for an
earlier calendar week counts.

**Still not carried over: leftovers.** Most weeks leave half a loaf, but the plan
cannot know whether the week was cooked as written, and a guessed fridge entry
that matches no row switches that food's comparison off. The athlete can see
their fridge; step 1 asks.
