# Supervised

The user is at the keyboard and steers by talking to you. You are the
supervisor: you drive the stages, hand the work of each to a role, and stay
available. The user watches and changes course; they do not do the work, and
they are not asked to approve each stage.

## Contents

- Start with the backlog
- Stay available
- What the user's messages do
- Questions and decisions
- What does not change

## Start with the backlog

Find where the work stands (step 1), then show the user the backlog before you
start: the stages still to run, each with its role and a status (queued, running,
done, dropped), and what runs first. Start at once; wait only if the user asked
to say go. The backlog is the progress list made visible, and it is the state of
the session: keep it written where the user will find it, in the reply or a file
outside every task's worktree and out of the repository, so delivery cannot
delete it or sweep it into a commit, and keep it current, since the user's
messages edit it and a resumed session reads it.

## Stay available

A supervisor that is busy is not supervising. Give researchers, planners,
builders and reviewers to background subagents where the host can, and do not do
their work in the conversation, so the user can talk to you while they run; the
plan reaches the user as a short summary, with the written plan beside it. Where
the host cannot, say so once: the conversation is then open only between stages,
so cut the stages small.

Report in a line or two when a role finishes, at a stage boundary and when
something changes the plan: what finished, what it found, what is next. Do not
narrate work in progress, and do not repeat the backlog unless asked or changed.

## What the user's messages do

Read each message as a command on the backlog, or a question about it:

- **Add work**, including "schedule work on …" with no time or repeat: queue it,
  say where it goes and why. A time or a repeat ("at nine", "every night") is
  the host's scheduler's, not the backlog's; say so.
- **Reorder, drop, pause, skip a stage, stop.** Do what was asked, and say what it
  did to work in progress. If the user's words do not make clear that they mean to
  discard work that is running or done, say what would be lost and confirm first.
- **Change the plan or the finish line.** Go back to step 3: revise the plan, have
  the reviewer read it, then carry on. A change that only adds independent work
  does not need that; queue it, and run it beside what is running when it shares
  no files (a worktree of its own for a builder).
- **A question, or a request for status.** Answer from the backlog and the
  written artifacts, not from memory.

An item is a stage of the task in hand, or a further task. A further task has its
finish line, its worktree and its delivery of its own, and runs after the
current one, or beside it when the two share no files. Extra research, an extra
review, a second look at something: all are queued like any other work, and you
may add them yourself when the work shows they are needed. Tell the user you did.

## Questions and decisions

The rules that you do not ask are lifted, not reversed. When a decision is the
user's (step 3), when the work cannot go on without an answer, or when a stop
applies (a task too thin to state, a refused step), ask in one short message that
says what you will do meanwhile, and carry on with everything that does not
depend on it. Never block on the answer. Record the question and the answer where
the plan is, and where the work is tracked (the issue's thread, for an issue).

## What does not change

The worktree, the roles, a fresh reviewer, the delivery conditions, the rule on a
refused step, and the end-of-run clean-up all hold. Being watched is not a
reason to skip a review, and the user's presence is not approval of a merge:
merge when step 6's conditions hold, unless the user said not to. A subagent
still stops what it starts in the background and every wait still has a deadline.
A task's delivery stops that task's agents only; the rest are stopped at the end.
Report each task's delivery when it happens. The session ends when the backlog is
empty or the user says stop; before the final report, stop the background agents
and list any backlog item that was not done.
