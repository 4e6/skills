---
type: Module
title: Work on a GitHub issue
description: Takes a GitHub issue and produces a reviewed pull request, ready to merge, in any repository. Guidance rather than bans — a worktree always, a reviewed plan before code, a reviewer fit for the change, approval over perfection.
tags: [architecture, github, process]
timestamp: 2026-10-03T11:56:11Z
sources: [skills/work-on-github-issue/**]
source_commit: be3fa4e2e9233de05344c0d974468f6cf6857f77
---

# What it is

`work-on-github-issue` takes one GitHub issue, named by the user, to a pull
request with green checks and a reviewer's approval, and hands it over. Merging
stays the user's. It works in any repository through `git` and `gh`, and defers
to the project's own rules — `CONTRIBUTING.md`, `AGENTS.md`, the pull request
template, what CI runs — wherever they differ.

# Guidance, not a fence

The skill assumes a capable agent and tells it how to work well, rather than
listing what it may not do. A list of bans has to foresee every spelling of
every act, grows with each incident, and spends a stranger's context on
situations that never arise; an agent that understands *why* a step exists
handles the case nobody wrote down. So the skill has one ban-shaped sentence —
merge only when the user says so — and gives its reason for the rest.

For the same reason it gives no commands for the agent to copy. The agent knows
`git` and `gh`, and a copied command is followed even where it does not fit. A
tool's behaviour is named only where an agent would otherwise get it wrong: a
branch started from a remote-tracking branch tracks it, git will not check a
branch out in two worktrees, `gh` renames the shared `origin` when it adds a
fork unless the remote is named, and checks are not reported the moment a pull
request opens.

It is also small: one `SKILL.md`, no scripts and no state machine. A run's
state is what GitHub and git already hold — the branch, the pull request, the
comments — so a session that dies leaves work another can pick up by looking,
and step 1 has the agent look before it starts.

# Why each rule is there

- **A worktree, always.** Several agents may share one clone. A branch switched
  or a file edited under another agent breaks its work with no error, so the
  skill never works in the shared checkout, even when it looks idle.
- **A reviewed plan before code.** A good implementation does not rescue a bad
  plan, and a design mistake is cheaper to see in ten lines of plan than in a
  diff. The reviewer is a fresh subagent because it has not absorbed the
  author's assumptions.
- **The user is asked only what is theirs.** Scope the issue leaves open,
  behaviour users see, breaking changes, new dependencies. Everything else the
  agent decides, so the user is not a bottleneck on choices the code settles.
  With nobody in the session, the questions go on the issue, where whoever
  answers and whichever session resumes can both read them.
- **The plan is left on the issue.** The final plan, any change to it, and
  what the work turned up that the code does not say. A session's reasoning
  dies with it, and a pull request is found only by someone who already knows
  to look for it; the issue is where the next person to work on or investigate
  that code starts.
- **A reviewer suited to the change.** A general reviewer misses what a
  security or migration reviewer would catch, and a specialist on a typo is
  waste. The skill's own local review runs before the project's, because it is
  the cheap one.
- **Approval, not perfection.** A reviewer always has another comment. The
  loop ends on a judgement that the change is good enough to merge, with the
  rest declined or noted, rather than when the reviewer falls silent. The
  judgement is the agent's own reviewer's, with the checks green, and not a
  maintainer's, who may take days: an agent told to wait for one waits, or
  polls, with nothing to do.
- **Step back when circling.** The same kind of finding in a new place is one
  design error paid for per site; the fix is the rule, not the next site. A
  fix that keeps failing goes to a fresh subagent, which does not share the
  assumption the agent is stuck on, and a long context is compacted because it
  degrades judgement.

# How it bends the payload

It is not a pure [payload](/architecture/the-payload.md): its whole job is on
the network, reading issues and writing branches, pull requests and comments
through `gh`, and `compatibility` says so. It ships nothing that reaches the
network on its own; every such act is a command the agent runs and the host
may ask about. It names `git`, `gh` and the files projects keep their rules
in, and describes a host's tools by what they do — *if the host can create a
worktree and move the session into it* — rather than by name.

It has no zip ([the zip release](/architecture/the-zip-release.md)), for the
same reason as `llm-wiki`: it needs a clone of the repository, which a web
app's chat does not have.

# Not measured

Nothing here has an eval. The rules come from running issues to pull requests
by hand, and none has been tested on Sonnet or Haiku.
