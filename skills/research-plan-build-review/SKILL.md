---
name: research-plan-build-review
description: >-
  Carries a task through research, plan, build and review, using fresh
  subagents and reviewers, and delivers whatever the task asked for: findings,
  a plan, a change, or work run. Use for any task bigger than a quick answer or
  a one-step edit — investigating a problem, choosing between approaches,
  fixing a bug, building a feature, migrating, auditing — whether or not an
  issue or ticket exists.
license: MIT
compatibility: >-
  Works in any assistant. Best where it can start subagents; without them each
  role is a separate pass by the same agent. Uses no network of its own.
metadata:
  author: 4e6
  version: "1.0.0"
---

# Research, plan, build, review

A task of any size goes through the same loop. What differs is where it stops
and what is handed over. A small task gets the loop at small scale, and a task
that is one step skips it, roles and all: just do it.

```
Progress:
- [ ] 1. Name the finish line
- [ ] 2. Research
- [ ] 3. Plan, and have the plan reviewed
- [ ] 4. Build and verify
- [ ] 5. Have the result reviewed
- [ ] 6. Deliver
```

## 1. Name the finish line

Say in one sentence what will be true when the task is done, and what the user
gets. Read it off the ask:

| The ask | The user gets | Stages |
|---|---|---|
| a question; "find out why" | findings, with evidence and what stays unknown | 2, 5, 6 |
| "how should we"; "make a plan" | a plan with the alternatives rejected, to approve | 2, 3, 6 |
| a fix, feature, refactor, docs | a change, verified, in the form the project takes changes | all |
| work to run: a migration, a batch, an audit | the work done and its result checked | all |

Stages are cut to the ask. A research ask never turns into a change. If two
readings of the ask would produce different work, ask the user; otherwise take
the cheaper one and say so.

## Roles

A role is a job, not a headcount. Where you can start subagents, give the role
to a fresh one with a brief; where you cannot, take it yourself in a separate
pass that starts again from the written artifact alone. Where you can pick a
model per role, read and edit on a mid-tier one, and keep the plan and the final
judgement on the strongest.

- **Researcher.** Gets the question, where to look and what the answer is for.
  Returns findings with their evidence — file and line, source, command output —
  and what it could not establish. It reads and never edits. Areas that can be
  investigated apart go to researchers in parallel; their reading stays in their
  context and only conclusions come back.
- **Planner.** You, from the findings; for a big task, a planner subagent whose
  plan you then read critically.
- **Builder.** Follows the plan and verifies. In a repository other agents may
  share, it works in a worktree or branch of its own, so no one's files change
  under them.
- **Reviewer.** A fresh agent that has not seen anyone's reasoning. Gets the ask
  and the artifact — findings, plan or result — and says what to hunt: a wrong
  cause, a missed caller, a claim with no evidence, a simpler way, scope creep, a
  test that would not catch the bug. It reports and does not edit or publish.
  A change to security, concurrency, data migrations or performance deserves a
  reviewer briefed for that.
- **Advisor.** If you can consult a stronger model, do so before committing to a
  plan, when the same failure comes back a second time, and before calling a long
  task done. It has read the whole session and so shares your assumptions: it
  does not replace the reviewer, and the reviewer does not replace it.

Every stage ends in something written down, and the next role starts from that
and the ask, not from the last role's conversation. Write it where the user will
find it: in the reply, a file in the working folder, or the thread the task came
from.

## 2. Research

Read before deciding. Read the project's own rules before its code. For a bug,
reproduce it first, ideally as a failing test, and find the cause rather than the
place it shows. For a question, find the evidence that would settle it and the
evidence that would overturn it.

## 3. Plan, and have the plan reviewed

A good build will not rescue a bad plan, and a mistake in a plan is far cheaper
to see than one in a diff. Write it briefly:

- what changes, and where;
- why this approach, and which alternatives you rejected;
- how you will know it works;
- what is out of scope;
- what you could not settle.

A plan for work that cannot be undone says how to undo it, or how to check before
doing it. Have a reviewer read the plan and revise until it would approve.

Some decisions are the user's: scope the task leaves open, behaviour its users
will see, breaking changes, new dependencies, spend, anything that leaves the
machine. Ask, and wait. If nobody is there to answer, deliver what can be
delivered and list the questions. Decide everything else yourself.

## 4. Build and verify

Follow the plan. When the work shows the plan to be wrong, go back to step 3 and
fix the plan rather than patching around it. Check the behaviour the ask
describes, not only the tests. Keep to the ask: unrelated problems you find are a
note in the delivery, not a detour.

## 5. Have the result reviewed

Read the result yourself first, then give a reviewer the ask, the plan and the
result. For findings, the reviewer checks each claim against its evidence.
Answer every finding by fixing it or by replying with a reason, and verify a
finding before acting on it: reviewers are wrong too. Have the reviewer read each
round of fixes.

**Seek approval, not perfection.** The loop ends when the reviewer approves, not
when it runs out of things to say. Fix what is wrong: the ask not met, a bug, a
broken test, a claim without evidence. Take a cheap improvement. Decline the rest
with a reason, or note it as a follow-up. After three rounds without approval,
deliver with what is still open named, or ask.

## 6. Deliver

Lead with the result. Then what was found or changed, the decisions the user
should know about and the alternatives rejected, how it was checked, what is
still open, and where the written artifacts are. Say plainly what was not done
or not verified.

Merging, publishing, sending, deploying and deleting are the user's to say.
Hand the work over ready for them.

## When you keep returning to the same problem

Stop and step back. Ask why you keep making the same mistake.

- **The same kind of finding comes back in a different place**: it is one design
  error paid for site by site. Name the rule being broken, fix it where it is
  decided, and check the other sites against it.
- **A fix keeps failing**: hand the problem, stated crisply, to a fresh agent.
  It does not share the assumption you are stuck on.
- **Your context is long**: it degrades your judgement. Compact it, then carry on
  from what is written down.
- **The plan no longer fits**: go back to step 3.
- **None of that works**: ask the user, with what you tried and why it failed.
