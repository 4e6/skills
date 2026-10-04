---
type: Module
title: llm-wiki
description: Keeps a codebase's wiki as an OKF bundle. Why a Decision page sits behind a gate, why a page is retired on evidence and never on age, and why it is pinned by the content of its sources and not by a commit.
tags: [architecture, llm-wiki, retirement]
sources: [skills/llm-wiki/**]
sources_digest: eb60edbb8851cf37
---

# What it is for

A skill for the agent that writes the wiki and the agent that reads it: small
pages in the repository, checked against git by one script, `okf.py`. It is
used on whatever project the host has open, so [the payload](/architecture/the-payload.md)
says what it may reach. This page carries the reasoning that does not belong in
a stranger's context window ([editing a skill](/conventions/editing-a-skill.md)).

# A reason is not a Decision

**Why a gate and not a longer rule.** `Decision` was the page agents wrote
whenever the thing in front of them was a reason. The skill already had about
sixty lines saying when a `Decision` is not one, and the pages kept coming. Three
things drew them, none of them in those lines: the request said *record this
decision* and *add an ADR*, a directory was named `decisions/`, and the type
table opened with `Decision`. A rule read after the type was chosen is argued
away; what changed the outcome is what sits in front of the choice.

- **The trigger words are gone**, so a request to record *why* does not name a
  destination.
- **`decisions/` is not in the layout.** It appears when a page passes.
- **The type is picked cheapest-first**, from `Invariant` down to `Module`, and
  `Decision` is last. [This bundle's own pages](/architecture/index.md) show that
  order working: it has no `Decision`, and the argument for each rule sits in a
  *Why* section of the module that owns it.
- **The gate is four facts**: the fork was taken, two alternatives were weighed
  and each is named with what ruled it out, no single page owns it, and the user
  said yes. Asking the user is the one brake that does not depend on the agent
  judging its own page.
- **`lint` checks the shape.** `W019` fires below two rejected alternatives,
  `W020` when a Decision names no `sources`, `W021` when Decisions are more than a
  fifth of the concepts. It cannot tell a real alternative from a straw one; it
  stops the page that has none, which is the page that was a description.

A Decision whose sources change is not reported stale: it records an event, and
the code it shaped moving on does not falsify it. Only `S005`, its sources
matching nothing, says anything, and it says the page is a retirement candidate.

# Retired on evidence

Decisions had been kept for good, on the argument that a wrong choice's record
stops the next person trying it. That holds while the subject exists. Once the
code a decision shaped is gone there is nothing to re-litigate, and the page only
costs every reader who meets it. It is retired when its `sources` match nothing,
no live page links to it as governing, and any rejected alternative still worth a
warning has moved to a `Gotcha`, an `Invariant` or the page that replaced the
subject. That is the last step of folding the reasoning in, not a sweep.

- **Never on age.** A page does not become false by getting old; a three-year-old
  `Gotcha` that still bites is the wiki working. `prune` reads no date.
- **`prune` only lists.** `P001` sources match nothing, `P002` a superseded or
  answered page no live page links to, `P003` a page names a repo path no tracked
  file has. `P003` also catches examples, so it is a prompt to look.
- **The tombstone names a path and not a commit.** `git log --diff-filter=D --
  <path>` finds a deleted page. A hash written into the log would be one more
  reference a squash merge invalidates.

# The pin is content

A page is pinned by `sources_digest`, a digest of its sources' content, and not by a
commit: a commit is a name for history, and a squash merge, a rebase and a
shallow clone each rewrite or cut it off ([why, and what was tested](/conventions/a-change-and-its-wiki-are-one-commit.md#why-the-pin-is-content-not-a-commit)).
Three consequences are the skill's own:

- **`pin` takes pages by name.** Pinning says *I read these sources*, so there is no
  "all" form; `--migrate` converts only pages already current under the old pin.
- **A stale page still gets a diff to read.** A digest says that the sources
  changed and not how, so `stale` looks for the newest of the last 50 commits that
  touched them whose sources digest to the pin, and names it. After a squash there
  may be none, and the finding says only *changed*.
- **A Decision is not pinned.** It records an event; see above.

# What is not measured

None of this has been run against a fresh agent before and after. The rule that
prose is not cut on argument alone applies, and
[editing a skill](/conventions/editing-a-skill.md) names the method: subagent
hosts on a frozen set of "document this change" tasks, counting the Decision pages
each arm writes. The condensed `Decision or Module?` section keeps every rule it
had, once each, and was not tested to still hold with the gate in front.
`Gotcha`, `Data Model` and `Integration` stay separate types: nothing here shows
merging them helps, and a `Gotcha` is a page a user asks for by name.
