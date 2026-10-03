---
name: work-on-github-issue
description: >-
  Takes a GitHub issue and produces a reviewed pull request, ready to merge,
  with green checks, in any GitHub repository: reads the issue and its whole
  thread, works in a git worktree of its own so other agents can share the
  checkout, writes a plan, has it reviewed and leaves it on the issue before
  any code, implements and tests, opens the pull request and works the review
  until a reviewer approves, then hands it over. Use when the user asks to work
  on, fix, implement, resolve or pick up a GitHub issue, gives an issue number
  such as 123 or #123, an owner/repo#123 reference or an issue URL, or asks to
  turn an issue into a pull request.
license: MIT
compatibility: >-
  Needs git, and the GitHub CLI (gh) authenticated with access to the
  repository, run from a clone of it. Uses the network for GitHub, a handful
  of API calls per step to read the issue, push a branch, open a pull request
  and comment; the skill itself downloads nothing, but setting up the project
  and running its tests may fetch the project's own dependencies. Reviews are
  best done by subagents; where the host has none, the agent reviews in a
  separate, deliberate pass.
metadata:
  author: 4e6
  version: "1.0.0"
---

# Work on a GitHub issue

The input is one issue: a number in the current repository, `owner/repo#123`,
or a URL. Without one, ask which issue. The work happens in a clone of the
issue's repository; for an issue elsewhere, find or make that clone first.

The end of the run is a pull request that solves the issue, with green checks
and your reviewer's approval, handed to the user. Merging is theirs to decide.

Reviews below are done by a fresh subagent. Where the host cannot start one,
review in a separate pass that starts again from the issue and the plan alone.

```
Progress:
- [ ] 1. Understand the issue
- [ ] 2. Set up a worktree
- [ ] 3. Plan, have the plan reviewed, and leave it on the issue
- [ ] 4. Implement and verify
- [ ] 5. Review the change, and open the pull request
- [ ] 6. Work the review until it is approved
- [ ] 7. Hand over
```

## 1. Understand the issue

Read the **whole** thread, not just the description: later comments often
answer a question and change the scope in the same breath, and earlier work may
have left a plan or findings there. Follow the issues and pull requests it
links to.

Check whether the work has already started — a pull request for the issue, a
branch, an assignee. If it has, continue that work rather than starting over;
if it looks like someone else is actively on it, ask the user before touching
it. A closed issue is not worked: say so and stop.

Read the project's own rules before its code: `CONTRIBUTING.md`, the agent
instructions file (`AGENTS.md` or the host's equivalent), the pull request
template, the CI workflows. Where they differ from this skill, they win.

Then state the issue in your own words: what is wrong or missing, and what will
be true when it is done. If you cannot, the issue is underspecified — that is a
question for the user, not a guess to build on.

## 2. Set up a worktree

Always work in a git worktree of your own, even when the checkout looks idle.
Other agents may be working in the same clone, and a branch switched or a file
edited under them breaks their work silently. If the host can create a worktree
and move the session into it, use that.

Start a new branch from the freshly fetched default branch.

To continue an existing branch, look for a worktree an earlier session left on
it first — git will not check a branch out in a second worktree, and the old
one is where to carry on. A pull request from a fork has its branch on the
fork, not on `origin`; check it out through the pull request.

Do everything in the worktree from then on, and leave the original checkout as
you found it. A fresh worktree has none of the ignored files the main checkout
has — installed dependencies, build output, local environment files — so set up
what the project needs before the first test run.

## 3. Plan, have the plan reviewed, and leave it on the issue

A good implementation will not rescue a bad plan, and a design mistake is far
cheaper to spot in a plan than in a diff. So plan before writing code.

Read the code the change touches and its callers. For a bug, reproduce it first,
ideally as a failing test, and find the cause rather than the place it shows.

Write the plan down, briefly:

- what changes, and where;
- why this approach, and which alternatives you rejected;
- how you will know it works;
- what is out of scope;
- what you could not settle.

When the issue is big — several areas of the code, a long investigation, a
design with real alternatives — hand the planning to a planner subagent: give
it the issue, the project's rules and what you already know, and have it hand
back the plan. Areas that can be investigated apart can go to subagents of
their own, in parallel. Their reading stays in their context and only the
conclusions come back, which leaves yours for judging the plan and building
it. The plan is still yours: read it critically before it goes to review.

Then have it reviewed by a fresh subagent that has not seen your reasoning, nor
the planner's: give
it the issue and the plan, and ask for design flaws — a wrong cause, a missed
caller, a simpler approach, scope creep, a test that would not catch the bug.
Revise until the reviewer would approve it.

Some decisions belong to the user: scope the issue leaves open, behaviour
visible to the project's users, breaking changes, new dependencies. Ask about
those and wait for the answer. If nobody is in the session to answer, post the
questions as a comment on the issue and stop there. Decide everything else
yourself.

Post the final plan as a comment on the issue. The thread is where the next
person to work on or investigate this code will look, long after this session
and its reasoning are gone; the plan tells them what was found, what was chosen
and what was ruled out.

## 4. Implement and verify

Follow the plan. When the code shows the plan to be wrong, go back to step 3,
fix the plan rather than patching around it, and post what changed and why on
the issue.

Commit in steps that each make sense on their own, in the project's commit
style. Run what CI runs — tests, linters, type checks — and check the behaviour
the issue describes, not only the unit tests. Keep the diff to the issue:
unrelated problems you find are a note in the pull request or a new issue.

Push the branch early. Work that lives only in a local worktree is invisible to
everyone else, and is lost with the session. Without push access to the
repository, push to a fork. Give the fork's remote a name of its own: by
default `gh` renames the clone's `origin` to make room for the fork, and
remotes are shared by every worktree of the clone.

## 5. Review the change, and open the pull request

Read the diff yourself first, then choose a reviewer suited to the change. A
fresh subagent fits most changes: give it the issue, the plan and the diff, say
what to look hardest at, and ask it to report findings rather than edit files or
post on GitHub. A change to security, concurrency, data migrations or
performance deserves a reviewer briefed for that. This review is cheap; the
project's CI and reviewers are not, so it comes first.

Then open the pull request, filling in the project's template if it has one.
The body says what changed and why, the decisions made and the alternatives
rejected, how it was verified, and `Closes #<n>`.

## 6. Work the review until it is approved

Wait for the checks. They can take a minute to be reported after the pull
request opens, so none yet is not the same as none at all; a repository with no
CI has none to wait for. Checks that wait on a maintainer — a project may hold a
fork's workflow runs until one approves them — will not arrive on their own:
run the same commands locally and say at the hand-over that CI has not run.
Then answer every finding — from the checks, from your
reviewer, and from any human or bot review that has arrived — by fixing it or
by replying with a reason. Verify a finding before acting on it: reviewers are
wrong too. Have your reviewer read each round of fixes.

**Seek approval, not perfection.** The loop ends when your reviewer approves
and the checks are green — when the change is good enough to merge, not when
the reviewer runs out of things to say. Fix what is wrong: the issue not
solved, a bug, a broken test, a security hole. Take a cheap improvement.
Decline the rest with a reason, or note it as a follow-up. Do not wait for a
maintainer's approval; that comes after the hand-over.

## 7. Hand over

The run ends with the pull request open, its checks green — or, where they
wait on a maintainer, passing locally — and its review answered. If the work turned up something the next person would want and the
code does not say — a dead end, a surprising cause, a follow-up — add it to the
issue.

Tell the user: the pull request's link, what changed, the decisions they should
know about, anything left open, and the worktree's path, which can be removed
once the pull request is merged or closed. Merge only when they say so.

## When you keep returning to the same problem

Stop and step back. Ask why you keep making the same mistake.

- **The same kind of finding comes back in a different place**: it is one
  design error paid for site by site. Name the rule being broken, fix it where
  it is decided, and check the other sites against it.
- **A fix keeps failing**: hand the problem, stated crisply, to a fresh
  subagent. It does not share the assumption you are stuck on.
- **Your context is long**: it degrades your judgement. Compact it, then carry
  on from what is written down — the plan, the commits, the pull request.
- **The plan no longer fits**: go back to step 3.
- **None of that works**: ask the user, with what you tried and why it failed.
