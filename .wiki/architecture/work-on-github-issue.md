---
type: Module
title: Work on a GitHub issue
description: Takes a GitHub issue and produces a reviewed pull request, ready to merge. Why it guides a capable agent rather than banning, and the reason behind each of its rules.
tags: [architecture, github, process]
sources:
  - resource: skills/work-on-github-issue/**
sources_digest: 6565e89a3097e7d2
---

# Guidance, not a fence

The skill assumes a capable agent and tells it how to work well, rather than
listing what it may not do. A list of bans has to foresee every spelling of
every act, grows with each incident, and spends a stranger's context on
situations that never arise; an agent that understands *why* a step exists
handles the case nobody wrote down. So the skill gives each rule its reason,
and forbids outright only what the agent cannot judge from where it stands:
merging, which is the user's call, and working a closed issue.

For the same reason it gives no commands to copy. The agent knows `git` and
`gh`, and a copied command is followed even where it does not fit. A tool's
behaviour is named only where an agent would otherwise get it wrong.

It keeps no state of its own. A run's state is what GitHub and git already
hold, so a session that dies leaves work another can pick up by looking.

# The loop is another skill's

Until 1.2.0 the skill carried the whole loop: a reviewed plan, planner
subagents, a fresh reviewer, approval over perfection, stepping back when
circling. A task without an issue could not use any of it, so the loop moved to
[research-plan-build-review](/architecture/research-plan-build-review.md), where
the reason for each rule now lives. This skill is what that loop becomes when
the finish line is a reviewed pull request on GitHub.

It still carries the loop in a paragraph, because delegation must not cost a
skill that works alone: an install of this skill without the other behaves as
before. The paragraph is a copy, and the price of one — change the loop's rules
there and change it here.

# Why each rule is there

What stayed is what is about GitHub:

- **A worktree, always.** Several agents may share one clone, and a branch
  switched or a file edited under another agent breaks its work with no error.
- **The plan is left on the issue.** A session's reasoning dies with it, and a
  pull request is found only by someone who already knows to look for it; the
  issue is where the next person to work on or investigate that code starts.
- **The user is asked only what is theirs**, and with nobody in the session the
  questions go on the issue, so the user is not a bottleneck on choices the code
  settles.
- **Approval is the agent's reviewer's, not a maintainer's.** A maintainer may
  take days: an agent told to wait for one waits, or polls, with nothing to do.
- **The merge cleans up after the work.** Worktrees and branches pile up in a
  clone that several agents share, each one a question for the next agent
  about whose it is and whether it is still live. The run that made them is
  the only one that knows, so it removes them when it merges, and touches
  nothing it did not make. It names the squash merge because that is where an
  agent goes wrong: git calls a squashed branch unmerged, and the safe-looking
  delete fails, inviting a force without the check that makes it safe.

# How it bends the payload

It is not a pure [payload](/architecture/the-payload.md): its whole job is on
the network, through `gh`. It has no zip
([why](/architecture/the-zip-release.md#readmemds-link-is-the-list)). It is
also the one skill that names another, and only softly: without
`research-plan-build-review` it follows the paragraph it carries.

# Not measured

Nothing here has an eval. The rules come from running issues to pull requests
by hand, and none has been tested on Sonnet or Haiku.
