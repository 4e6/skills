---
type: Module
title: The handover, and what the athlete reads along the way
description: The progress checklist is the host's and never the athlete's. The athlete is handed the page — published, else attached, else opened and pointed at — and, with no page, a reply designed as one for a phone.
tags: [architecture, conversation]
timestamp: 2026-10-02T15:10:00Z
sources: [skills/training-week-meal-plan/SKILL.md, skills/training-week-meal-plan/references/when-there-is-no-page.md, skills/training-week-meal-plan/references/photos.md]
source_commit: e5ae3bf78ef71fa3efb195ca7b30307aea5865c5
---

# Progress is the host's, and the reply is the athlete's

`SKILL.md` carries a seven-step checklist, on the authoring guidance's advice. It
used to tell the host to copy it into the reply, and **every host tried did** —
`read references/fuelling.md`, `write plan.json`, `(skipped, no Python here)` in
a code block, first message and last. The athletes called it *a debug log*, and
on a phone it is a grey block that scrolls sideways. The guidance's reason for
the pattern is that it helps the model and the author track progress; the
person reading this reply is neither.

- **The checklist stays, and stays the host's.** Seven conditional steps with a
  repair loop are what the pattern is for; deleting it would trade a
  presentation fault for a correctness one. It appears nowhere the athlete reads
  — which on Claude Code includes a task list, drawn in their own terminal.
- **One plain line at most, when step 1 ends**, while the plan is written and
  checked. It **promises no check and no page**, because a host without Python
  makes neither and would have to take the promise back.
- **Silence is anchored to steps.** From the end of step 1 to step 7 the host
  says nothing but a question it cannot go on without — and one line before
  photos are drawn, since on a host that draws in the chat unexplained plates
  would otherwise appear.
- **The check's output is never pasted**, step 7 included. Step 7 says what the
  check found in the host's own words.

Two runs of the old text pasted the checklist and two of the new one did not. A
word-list check over the prose would catch a sentence pairing the checklist with
a place the athlete reads, but not every spelling of one; a host running the
skill is what shows the behaviour.

# The page is what they are handed

The JSON is scaffolding: it is named in every step that writes, checks or
repairs it, and in none of the handover. Two paths ask somebody to work out
which file is their week.

**Step 7 is an order, not a menu: publish, else attach, else open.** A link
reaches the athlete wherever they are: at the stove, in the shop, sent on to
whoever cooks with them. A file in the chat reaches them where the chat does. A
file on a disk reaches whoever sits at that machine. So step 7 hands over the
page step 6 wrote by the first of the three the host can do, each failure
falling back to the next in one plain line, and the page is:

- **never retyped.** The page is about 55 KB without photos, and a hand copy is not the page the
  renderer wrote; the shopping list comes last, which is the part a truncated
  copy loses;
- **private**, unless they ask to share it — it carries their weight and diet;
- **no opener and no path.** Without *name no path*, the smaller models handed
  the file over and recited its sandbox path beside it;
- **published as the renderer wrote it** — not redesigned, restyled or retyped
  to suit a publishing tool's rules for a page written by hand
  ([publishing a page with photos](#publishing-a-page-with-photos)).

**The trigger is what the host can do, not where it runs.** An earlier version
handed over only when the session was off the athlete's machine. Opus with a
file tool on the athlete's own machine attached the page instead of opening it,
which was first counted a regression and then judged the better outcome: a
published page is more useful than a local file even at the machine that made it.

**Until 1.7.0 the three were a menu**, publishing and attaching named as
examples — *an artifact or a file card is an example, never a requirement* —
with opening for where there was neither. That left the host to decide whether
it could publish, and on 2026-10-02 a real run decided it could not: Opus on
Claude Code, with a publishing tool, a six-photo page of 663 KB and an athlete
at the machine, opened the page locally. Asked why, it named two things. The
publishing tool asks for a file it did not write to be read whole first, and
`photos.md` said never to read the page back, it being mostly the photos' bytes —
about 200,000 tokens of base64, more than one read returns. And the tool's own
rules for a page (a dark theme, a design pass) did not fit a page the skill
forbids retyping. Wording alone would have left the first in place, so 1.7.0
changed what is published as well as the order.

**Where it can do neither, the page is opened** — `open`, `xdg-open` or
`start`, **tried once**, and where it will not run, the full path and the line
to run it themselves. Once, because the three ways it fails cannot be told
apart from inside the session: no shell, no opener installed, or a browser on a
machine nobody is sitting at. The claim is hedged — *I have opened it; if no
window came up, it is at …* — because **a command that exits cleanly is not a
window that appeared**. The three openers are one per platform, not the *too many
options* the guidance warns about: the machine is a basis for choosing.

**What is still unreached:** a sandbox with neither an opener nor a way to hand
over a file, where a path reaches nobody. Its fix would be to treat *no page they
can reach* as no page.

**Measured, 2026-09-29.** 69 simulated host runs, blind judges per pair. In a
sandbox that could hand over a file, the old text ran an opener and named an
unreachable path 3 times of 3 with Opus; the new text handed the file over clean
3 of 3, and blind judges preferred it in 6 of 6 pairs, then 5 of 5 after the
revision that dropped the location condition. The *name no path* revision fixed
Sonnet in the first pass and not in the second, and **the smaller models, Sonnet
and Haiku, still recite a path beside the handover about half the time**, on
either text. Given both, Opus in a sandbox chose the file card over the link
every time; the step then preferred neither, and from 1.7.0 prefers the link.
One real run on claude.ai, with code execution, published the page as an
artifact unprompted and named no path.

## Publishing a page with photos

`render.py … --photos photos.json --link-photos` writes a copy whose image
elements point at each photo's path from the list instead of carrying its bytes
— 48 KB for that six-photo week, against 663 KB — and prints one `link PATH`
line per photo. Step 7 publishes it, with each of those files beside it at the
same path, where the tool takes files beside a page. It is written beside
`photos.json`, and refuses to be written anywhere else, so the paths that
resolve on disk are the paths it is published with. It is the one page a host
may read back, and only because a publishing tool asks to. Where the tool takes
no files beside a page, the self-contained page is published whole — unless the
tool must read it first, when the review of #29 caught the first draft sending
the host straight back into the failure: there a copy without photos is
published, a link without them still beating a file with them. A file attached
is always the self-contained page, since an attachment is one file.

**A linked page is written in the list's folder, one name from the list**, so
`render.py` refuses to write over `photos.json` as it refuses to write over the
plan: both are read into memory first, and the write would report success.

**The page says it is light.** `<meta name="color-scheme" content="light">`, so
a viewer in a dark theme shows the paper as designed, and a host has no theme of
its own to impose ([the printable page](/architecture/the-printable-page.md)).

**Unmeasured.** [The evals](/architecture/the-evals.md) give a run no tool that
publishes, deliberately, since a run would publish to the author's account, so
the order is not yet measured; a stub that takes the page and its files and
publishes nothing would measure it. The evidence for 1.7.0 is the one real run
above.

# When there is no page

Two runs have no page: the renderer that would not start, and the one that ran
and exited 2. The rule is stated as *no page* and the file is checked before it
is pointed at. There the week goes into the reply itself — a path to a JSON file
is nothing anybody reads over a kitchen counter — and the reply is designed as a
page, **for a phone first**. The rules live in
`references/when-there-is-no-page.md`, because a host with Python never needs
them:

- **No code blocks and no tables** — both scroll sideways in a chat bubble.
- **A top of four lines at most**, what shows before the first scroll:
  `week_label` and `training_overview.total`, the biggest fuel day and why, the
  restriction, and what was assumed.
- **A day's snacks are one short line after its meals** — the guidance and the
  example.
- **Each day whole, with the recipe where the dish is first cooked** — one line
  of ingredients with quantities, then the steps; a one-sitting dish of four
  ingredients or fewer drops its steps, since the line is the method. A repeat
  or leftover is one line pointing back, and a repeat whose pot is not the
  origin's carries its own ingredient line.
- **The shopping list last, in one block**, so it is one screenshot.
- **Where the host can show a document beside the chat**, the week goes there
  and the reply carries the top and the closing lines. An example, never a
  requirement.
- **Nothing scales the pot, so the pot is what the recipe says.** A host that
  knows at step 3 it cannot run a command writes each origin's `yields` as the
  portions its sittings add up to. A host that only finds out at step 7 — no
  Python after all, or a page that would not render — leaves the plan as written.
  Either way each printed line is the written list at its factor, rounded once:
  the same amounts the page would print.
- **A batch line counts portions, not sittings** — *cook 4* over sittings of
  1¼, 1¾ and 1 visibly sums; **a repeat says it is cooked fresh**, or *again,
  same pot* reads as eggs kept from Monday to Friday.
- **No plan-wide fuelling block and no `week_load`**, which the page prints
  neither of, **and no count of tins**: that is the page's to compute from
  `pack`, so without a page a row is its name and its quantity, a tin's drained
  weight marked as one (`18 oz drained`), since no can's label says it.
- **The sentence about checking comes after the list**, with the disclaimer, so
  the caveat is met once.

**Measured, blind, 2026-09-24**, on simulated hosts with no code execution: trust went from
2 to 3 of 5 on every run, *would cook from it* from 2–3 to 4, and the judge
preferred it 3 of 3. **Length is the accepted cost** — the longest week ran to
about 2,000 words and was rated too long on all four runs, the complaint being
scrolling past seven days to reach the list.

Whether the reply is *checked* is said in one sentence that states a fact and
never an instruction ([a missing capability is announced](/architecture/the-validator.md#a-missing-capability-is-announced)).
