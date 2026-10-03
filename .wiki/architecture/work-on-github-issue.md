---
type: Module
title: Work on a GitHub issue
description: Takes a GitHub issue and produces a reviewed pull request, ready to merge. Why it guides a capable agent rather than banning, and the reason behind each of its rules.
tags: [architecture, github, process]
timestamp: 2026-10-03T12:12:18Z
sources: [skills/work-on-github-issue/**]
source_commit: be3fa4e2e9233de05344c0d974468f6cf6857f77
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

# Why each rule is there

- **A worktree, always.** Several agents may share one clone, and a branch
  switched or a file edited under another agent breaks its work with no error.
- **A reviewed plan before code.** A good implementation does not rescue a bad
  plan, and a design mistake is cheaper to see in a plan than in a diff. The
  reviewer is fresh because it has not absorbed the author's assumptions.
- **A big issue is planned by subagents.** Investigating a wide issue fills a
  context with code read on the way, and the same context then has to judge
  the plan and build it. Subagents return only their conclusions.
- **The user is asked only what is theirs**, so the user is not a bottleneck on
  choices the code settles.
- **The plan is left on the issue.** A session's reasoning dies with it, and a
  pull request is found only by someone who already knows to look for it; the
  issue is where the next person to work on or investigate that code starts.
- **A reviewer suited to the change.** A general reviewer misses what a
  specialist would catch, and a specialist on a typo is waste.
- **Approval, not perfection.** A reviewer always has another comment, so the
  loop ends on a judgement that the change is good enough to merge. The
  judgement is the agent's own reviewer's, not a maintainer's, who may take
  days: an agent told to wait for one waits, or polls, with nothing to do.
- **Step back when circling.** The same kind of finding in a new place is one
  design error paid for per site. A fresh subagent does not share the
  assumption the agent is stuck on, and a long context degrades judgement.

# How it bends the payload

It is not a pure [payload](/architecture/the-payload.md): its whole job is on
the network, through `gh`. It has no zip
([why](/architecture/the-zip-release.md#readmemds-link-is-the-list)).

# Not measured

Nothing here has an eval. The rules come from running issues to pull requests
by hand, and none has been tested on Sonnet or Haiku.
