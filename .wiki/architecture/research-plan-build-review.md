---
type: Module
title: Research, plan, build, review
description: "One loop for any task, ending in what the task asked for: findings, a plan, a change or work run. Why the finish line is named first, why roles are jobs and not headcount, and why a fresh reviewer and an advisor are both kept."
tags: [architecture, process, agents]
sources:
  - resource: skills/research-plan-build-review/**
sources_digest: c14cefe69e33f1f5
---

# Why a skill of its own

The loop began inside [work on a GitHub issue](/architecture/work-on-github-issue.md),
which needs an issue and ends in a pull request. A task given in a prompt has
neither: it may be a question to answer, a choice to make, or work to run, and
the issue skill was the wrong frame for all three. So the loop is a skill that
asks nothing of the task but a finish line, and the issue skill is what that loop
becomes when the finish line is a reviewed pull request.

It is a pure [payload](/architecture/the-payload.md): no script, no network of
its own, and it names no host and no host's tools. Anything Claude Code-specific
— agent definitions with a model and tool list per role, an advisor setting —
would be an adapter beside it, not part of it
([what is not built](#rejected-alternatives)).

# Why each rule is there

- **The finish line is named first, and stages are cut to the ask.** The failure
  is not skipping a stage but adding one nobody asked for: a research question
  that comes back as a diff. Naming what the user gets, and which stages lead to
  it, is what stops that. A task of one step skips the loop, because a loop on a
  typo costs more than the typo.
- **Roles are jobs, not headcount.** Hosts differ in whether they can start a
  subagent. The fallback — the same agent, in a separate pass that starts again
  from the written artifact — is the one the issue skill already used, and it
  works because the artifact is all the next pass gets.
- **Every stage ends in something written down.** A subagent's context and a
  session's reasoning die with them; the next role, and the user, have only the
  artifact. It is written where the user will find it, because the skill keeps no
  state of its own, like the issue skill.
- **A researcher returns evidence and what it could not establish.** A research
  deliverable has no test to catch it being wrong, so the reviewer's only check is
  each claim against its evidence, and a claim with none is a finding.
- **The reviewer is fresh; the advisor is not, and both stay.** A fresh reviewer
  has not absorbed the author's assumptions, which is its whole value. A stronger
  model consulted mid-task has read the whole session and shares them, but sees
  the plan before it is built and the same failure coming back, which a reviewer
  of the finished artifact does not. Each covers what the other cannot, so the
  skill says neither replaces the other. It names the advisor by what it does, not
  by a host's setting.
- **Models by role, where the host allows.** Reading and editing are most of the
  tokens and need the least judgement; the plan and the final call need the most.
  This is guidance in one sentence, not a configuration, since the skill cannot
  set a model.
- **Approval, not perfection, with a cap of three rounds.** A reviewer always has
  another comment. The issue skill ends the loop on the reviewer's approval; a
  task with no pull request has no CI and no maintainer to end it either, so the
  cap is there to make it end. Three is a guess, not a measurement.
- **Merging, publishing, sending, deploying and deleting are the user's.** The
  issue skill held this for merging alone. In a loop that may run work, the
  list is longer, and the same reason holds: an agent cannot judge from where it
  stands what the user wants out of reach.
- **Work that cannot be undone says how to undo it, or how to check first.** A
  change can be reverted from git; a migration or a batch cannot, and a plan
  that does not say so is a plan nobody reviewed for it.

# Rejected alternatives

- **Fold the issue skill into this one**, with the pull request as a reference
  file. One thing to install, but the folder name must match the skill's name, so
  every existing install of `work-on-github-issue` would stop working.
- **Both skills self-contained.** Each installs alone, but the loop is then
  written twice and a rule changed in one is not changed in the other. The issue
  skill keeps a paragraph of the loop so that it still works alone; that
  paragraph is the cost of the delegation, and it must change when the loop does.
- **Agent definitions shipped here.** Subagent definitions live in
  `.claude/agents/` or a plugin, not in a skill folder, and only one host reads
  them. They are the second half of the design, and not built: a plugin beside
  the skills, with a `researcher`, a `worker` and a `reviewer`, would need its own
  place in the repository and its own release path
  ([the zip release](/architecture/the-zip-release.md)).
- **Agent teams or a workflow script for the loop.** The loop is sequential, and
  the one parallel part — researchers, and reviewers with different lenses — is
  what subagents do. A script that runs the loop belongs to a host that has one.

# Not measured

Nothing here has an eval. Three things are open: whether the `description`
triggers on the tasks it should and stays quiet on a one-step edit, which a
skill cannot guarantee for a user who wants the loop on every task, who is better
served by a line in their own instructions file; whether a task given the loop
beats the same task without it; and whether three rounds is the right cap.
