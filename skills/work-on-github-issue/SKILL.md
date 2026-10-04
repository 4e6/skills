---
name: work-on-github-issue
description: >-
  Takes a GitHub issue and produces a reviewed pull request, ready to merge,
  in any GitHub repository. Use when the user asks to work on, fix, implement,
  resolve or pick up a GitHub issue, or gives an issue number, reference or
  URL.
license: MIT
compatibility: >-
  Needs git, and the GitHub CLI (gh) authenticated with access to the
  repository.
metadata:
  author: 4e6
  version: "1.2.0"
---

# Work on a GitHub issue

The input is one issue: a number in the current repository, `owner/repo#123`,
or a URL. Without one, ask which issue. The work happens in a clone of the
issue's repository; for an issue elsewhere, find or make that clone first.

The end of the run is a pull request that solves the issue, with green checks
and your reviewer's approval, handed to the user. Merging is theirs to decide,
unless the ask already said to integrate, merge or ship it.

The loop this follows — research, plan, build, review, deliver — belongs to the
`research-plan-build-review` skill: its roles, its stop rules, and what to do
when you keep meeting the same problem. Follow it, with GitHub as the place the
work is read, recorded and delivered, and a reviewed pull request as the finish
line. Without that skill, the loop in brief: plan before code, and have the plan
read by a fresh reviewer who has not seen your reasoning; hand wide
investigation to subagents that return only conclusions; have the change
reviewed the same way before anyone else sees it; end on the reviewer's
approval, not on its running out of comments. A change to security,
concurrency, data migrations or performance deserves a reviewer briefed for it.
When the same problem keeps coming back, stop and fix it where it is decided;
when a fix keeps failing, hand the problem to a fresh subagent; when your context
is long, compact it and carry on from what is written down; when the plan no
longer fits, go back to it; when nothing works, ask the user. A plan says what changes and
where, why this approach and which were rejected, how you will know it works,
what is out of scope and what you could not settle. Where the host cannot start
a subagent, review in a separate pass that starts again from the issue and the
plan alone.

```
Progress:
- [ ] 1. Understand the issue
- [ ] 2. Set up a worktree
- [ ] 3. Plan, have the plan reviewed, and leave it on the issue
- [ ] 4. Implement and verify
- [ ] 5. Review the change, and open the pull request
- [ ] 6. Work the review until it is approved
- [ ] 7. Hand over
- [ ] 8. When the user says to merge: merge, and clean up
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

Start a new branch from the freshly fetched default branch of the issue's
repository.

To continue an existing branch, look for a worktree an earlier session left on
it first — git will not check a branch out in a second worktree, and the old
one is where to carry on. A pull request from a fork has its branch on the
fork, not on `origin`; check it out through the pull request.

Do everything in the worktree from then on, and leave the original checkout as
you found it. A fresh worktree has none of the ignored files the main checkout
has — installed dependencies, build output, local environment files — so set up
what the project needs before the first test run.

## 3. Plan, have the plan reviewed, and leave it on the issue

Research and plan as the loop says. For a bug, reproduce it first, ideally as a
failing test, and find the cause rather than the place it shows.

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

Review the change as the loop says, giving the reviewer the issue, the plan and
the diff, and asking it to report findings rather than edit files or post on
GitHub. This review is cheap; the project's CI and reviewers are not, so it
comes first.

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

**Seek approval, not perfection**, as the loop says: the loop ends when your
reviewer approves and the checks are green. Do not wait for a maintainer's
approval; that comes after the hand-over.

## 7. Hand over

The run ends with the pull request open, its checks green — or, where they
wait on a maintainer, passing locally — and its review answered. If the work turned up something the next person would want and the
code does not say — a dead end, a surprising cause, a follow-up — add it to the
issue.

Tell the user: the pull request's link, what changed, the decisions they should
know about, anything left open, and the worktree's path, which can be removed
once the pull request is merged or closed. Merge only when they say so. If the
ask already said "merge", "integrate" or "ship it", they have: do not stop to
wait, and go on to step 8 once the review is approved and the checks are green.

## 8. When the user says to merge: merge, and clean up

Merge the way the project merges. Then remove what the work left behind: the
worktree, its branch, locally and on the remote it was pushed to, and every
other worktree or branch made along the way, such as a subagent's or a branch
for an abandoned approach. Leave alone what this work did not make: other
agents share the clone.

After a squash or rebase merge, git sees the branch as unmerged and refuses a
plain delete. The merged pull request is the proof: once its last commit is the
branch's last commit, so nothing local was left unpushed, force the delete. Do
not remove a worktree with uncommitted changes until you have seen what they
are. Leave the worktree before removing it if the session is in it, and leave
the original checkout as you found it.
