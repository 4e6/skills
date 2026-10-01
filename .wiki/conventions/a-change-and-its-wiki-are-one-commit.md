---
type: Convention
title: A change and its wiki are one commit
description: A PR changes the code and every page it touches in one squashed commit, pinned to the commit it branched from. Nothing is pinned after a merge.
tags: [process, wiki]
timestamp: 2026-10-01T19:00:00Z
sources: [AGENTS.md, skills/llm-wiki/scripts/okf.py]
source_commit: 1bf51193ea564f2482ab29e115b0181d95867222
---

# The rule

A change lands as one commit with every wiki page it touches, PRs squashed on
merge. That covers a page whose text still holds, too: the review of it is
recorded in the same PR, by setting its `source_commit` to the commit the
branch started from (`git merge-base HEAD origin/main`). Nothing is pinned
after a merge.

# Why the pin moved into the PR

`okf.py stale` used to call a page stale whenever its sources changed after
its `source_commit`. A PR can only pin a commit that exists before it merges,
and a squash gives the change a new hash, so every merged PR left its pages
stale until a second commit to main pinned them to the merge. Every PR from #8
to #24 was followed by one, touching up to 20 pages, nearly all of them for the
pin alone.

`stale` now skips a commit that changed the page along with its sources,
since that commit is the page describing its own change. A commit that edits
the page for another reason covers only itself: a typo fixed later never
vouches for an earlier change that left the page alone. **Within a squashed
PR, though, any edit to the page counts as its review**, because the squash is
one commit. A typo fixed in the same PR as an unread change clears it, and
nothing flags the page after the merge, so the review is the one before it.

# What follows

- **A pin names a commit on main**, never one of a branch's own: a squash
  leaves those behind and `stale` reports `S006`.
- **The pages are reviewed before the PR merges.** Run `stale --base main` on
  the branch once the change is committed. It judges the branch as main will
  see it squashed, and lists the pages the change left alone; each is fixed or
  re-pinned to the merge base in the same PR.
- **A branch merged without squashing** is judged by its merge commit's diff
  against main, the same as a squash. This repository squashes.
