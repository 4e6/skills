# supervise-work

An [Agent Skill](https://agentskills.io) that supervises a task through
research, plan, build and review, and delivers whatever the task asked for:
findings, a plan, a merged change, or work run. Ask your assistant to
investigate, decide, fix, build or audit something, or give it a GitHub issue
(`#123`, `owner/repo#123` or a link). No issue or ticket is needed. Say "don't
merge" to keep the merge yours.

By default it runs to the end without asking you anything. Say **"supervise work
on …"** or **"schedule work on …"** and it becomes a supervisor you talk to
instead: it keeps a backlog, runs the stages in the background, reports as roles
finish, and takes your messages as commands, so you can add work, reorder it,
change the plan or stop. It starts from where the work stands: a plan you
reached in conversation is written down and reviewed, then built, and one already
reviewed goes straight to the build.

"Schedule" here means putting work on the supervisor's backlog. A time or a
repeat ("at nine", "every night") is for your assistant's scheduler.

It works best where the assistant can start subagents, which do the reading and
the reviewing in a context of their own, and run them in the background for a
supervised session. Without them, each role is a separate pass by the same
assistant.

## Requirements

None for most tasks. For a GitHub issue or pull request: `git`, and the
[GitHub CLI](https://cli.github.com) (`gh`) signed in with access to the
repository.

## Replaces

`research-plan-build-review` and `work-on-github-issue`, which it folds into one
skill. Remove those two from your skills folder.
