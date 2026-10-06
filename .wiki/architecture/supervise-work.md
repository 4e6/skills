---
type: Module
title: Supervise work
description: "One skill for any task: research, plan, build, review and deliver, run unattended or supervised by a user who steers, and with GitHub as a reference. Why it is one skill, why supervised is opt-in, and the reason behind each rule."
tags: [architecture, process, agents, github]
sources:
  - resource: skills/supervise-work/**
sources_digest: aeb28726078a07ea
---

# Why one skill, and why this shape

The loop began inside a skill that took a GitHub issue and ended in a pull
request. A task given in a prompt has no issue: it may be a question to answer, a
choice to make, or work to run, so the loop became a skill that asks nothing of
the task but a finish line, and the issue skill became that loop with GitHub in
and a merged pull request out.

Two skills could not stay one loop. The format has no way for one skill to depend
on another, and an install of one does not bring the other, so the issue skill
carried a paragraph of the loop to work alone. A copy is the price of that, and it
went unpaid once: the loop's delivery rules moved on and the copy kept handing
over an open pull request, asking and waiting, so the two gave opposite
instructions to the same agent. A supervisor skill beside the loop would have been
a third copy. So there is one skill, and what only some tasks need sits in
`references/`, which a host loads when the instructions point there:

- **`supervised.md`**: the user is at the keyboard and steers.
- **`github.md`**: the task names an issue or a pull request, or its change is
  delivered as one.

It is a pure [payload](/architecture/the-payload.md) in `SKILL.md`: no script, no
network of its own, and no host's tools named. `github.md` names GitHub and `gh`
because they are its subject, and the network use is `gh`'s. Anything Claude
Code-specific — agent definitions with a model and tool list per role, an advisor
setting — would be an adapter beside it, not part of it
([what is not built](#rejected-alternatives)).

It guides a capable agent and does not fence it. A list of bans has to foresee
every spelling of every act and spends a stranger's context on situations that
never arise; an agent that knows why a step exists handles the case nobody wrote
down. So each rule below has its reason, and no command is given to copy: the
agent knows `git` and `gh`, and a copied command is followed even where it does
not fit. A tool's behaviour is named only where an agent would otherwise get it
wrong.

# Why each rule is there

- **The finish line is named first, and stages are cut to the ask.** The failure
  is not skipping a stage but adding one nobody asked for: a research question
  that comes back as a diff. Naming what the user gets, and which stages lead to
  it, is what stops that. A task of one step skips the loop, because a loop on a
  typo costs more than the typo.
- **The work starts where it stands.** A task arrives part done: a conversation
  that reached a plan, an issue thread with findings, a branch someone began. A
  loop that always starts at research redoes what exists, or builds a plan nobody
  reviewed. The rule is read off the artifacts: the first stage whose output is
  not written down, or, for a plan or a result, not read by someone who did not
  write it. Checking whether work on an issue had started was the same rule for
  one source; the loop now states it for all.
- **Unattended is the default, and supervised is asked for.** A task handed over
  has nobody at the keyboard, and an agent that stops to ask waits for nothing.
  Subagents and headless runs have no user to talk to at all. Making supervision
  the default would break both, so it is a mode the user names ("supervise",
  "schedule", "keep me in the loop"), and the one rule it lifts — do not ask — is
  lifted in `supervised.md` alone.
- **A supervisor stays available, and the backlog is its state.** A session
  where the agent does each stage's work in the conversation cannot be steered:
  the user types into a silence. So roles run in the background where the host
  allows, the supervisor reports as they finish, and the stage list becomes a
  written backlog that the user's messages edit. It is the progress list made
  visible, in the reply or a file, so the skill still keeps no state of its own.
- **Supervised is not an approval gate.** The user steers; they are not asked to
  approve each stage, and their presence is not approval of a merge. The
  delivery conditions are the same in both modes, so a watched run is not a
  looser one.
- **"Schedule work on" means the backlog, not a clock.** The user says it for work
  to be queued with a supervisor. A host's scheduler skill answers a time or a
  repeat, so the `description` gives the one phrase to this skill and sends a time
  or a repeat away, and `supervised.md` repeats the line for the moment a message
  carries one.
- **Roles are jobs, not headcount.** Hosts differ in whether they can start a
  subagent. The fallback — the same agent, in a separate pass that starts again
  from the written artifact — works because the artifact is all the next pass
  gets.
- **A builder step may be split, but only along independent steps.** Researchers
  already fanned out; a plan with steps on separate files was still built by one
  agent, one step after another. The plan marks which steps are independent, so
  the split is read off it and not judged mid-build. Each parallel builder has a
  worktree of its own for the reason every task does, and one agent merges and
  verifies the whole, because a pass in each part says nothing about their sum.
- **Every stage ends in something written down.** A subagent's context and a
  session's reasoning die with them; the next role, and the user, have only the
  artifact. It is written where the user will find it, because the skill keeps no
  state of its own.
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
  another comment. A task with no pull request has no CI and no maintainer to end
  the loop either, so the cap is there to make it end. Three is a guess, not a
  measurement.
- **A change ends delivered: merged, and deployed where the project has a path.**
  Earlier versions handed over a verified diff, then an open pull request, and
  left the merge to a second instruction, which the user typed after every run.
  Handing the task over is the authority for that path, so the skill carries it
  through merge, deploy and clean-up, and "draft" or "don't merge" in the ask
  stops it where they say. What the handover does not cover — deleting data the
  work did not make, rotating credentials, changing what other people consume,
  spending — is left out and listed. A step the permission layer or the project
  refuses is not tried another way: the run stops and says what would unlock it.
- **A worktree on every task, read-only ones included.** The first version asked
  for one only of the builder, and only "in a repository other agents may share":
  a condition the agent judged for itself, and judged as not met, so research and
  review ran in the main checkout. A branch switched or a file edited there by a
  parallel agent changes what a researcher reads as surely as what a builder
  builds, and the finding is then wrong with no error. An unconditional rule
  leaves nothing to judge. It sits before the stage list because it applies to
  all of them.
- **A subagent stops what it starts, and every wait has a deadline.** A
  background process a subagent leaves running is in no report, so nobody knows to
  stop it. The brief says so, and delivery lists and stops what is left. A wait
  that matches its own command line never ends, which is why the skill names it.
- **Work that cannot be undone says how to undo it, or how to check first.** A
  change can be reverted from git; a migration or a batch cannot, and a plan
  that does not say so is a plan nobody reviewed for it.

## What is about GitHub

`github.md` holds only what an agent would otherwise get wrong, or not think to
do:

- **The plan is left on the issue.** A session's reasoning dies with it, and a
  pull request is found only by someone who already knows to look for it; the
  issue is where the next person to work on or investigate that code starts.
- **The user is not asked, and decides afterwards.** What is theirs — scope the
  issue leaves open, visible behaviour, breaking changes — is settled by the
  smallest reversible option, named in the plan on the issue, where the user will
  see it. An issue too thin to state is a stop: there is nothing to build, so the
  question goes on the issue. So is a closed issue, and so is a refusal.
- **Approval is the agent's reviewer's, not a maintainer's.** A maintainer may
  take days: an agent told to wait for one waits, or polls, with nothing to do. A
  project that requires one to merge refuses the merge, and the rule for a refusal
  applies.
- **The reviewer's verdict goes on the pull request, with the commit SHA.** It is
  what the merge condition reads, and what a maintainer or the next agent can
  check without the session. A push after it makes it a verdict on an older
  commit, so it is asked for again.
- **The merge is the agent's, and so is the clean-up after it.** Worktrees and
  branches pile up in a clone that several agents share, each one a question for
  the next agent about whose it is and whether it is still live. The run that made
  them is the only one that knows, so it removes them when it merges, and touches
  nothing it did not make. It names the squash merge because that is where an
  agent goes wrong: git calls a squashed branch unmerged, and the safe-looking
  delete fails, inviting a force without the check that makes it safe.
- **A fork's remote has a name of its own.** By default `gh` renames the clone's
  `origin` to make room for the fork, and remotes are shared by every worktree of
  the clone.

# Rejected alternatives

- **A separate supervisor skill that delegates to the loop.** It would give
  "supervise" a name of its own, but the loop would be written twice, which is the
  cost already paid once above. The supervised mode is an opt-in layer on one
  loop, not a different loop.
- **A generic supervisor over any workflow.** Clean, but there is one workflow
  today. Extract it when a second one needs supervising.
- **Keep the issue skill, thin.** A stub that points at this skill is the soft
  dependency again, and fails where only the stub is installed. Neither old skill
  had a release, a tag or a zip, so deleting both stranded no uploaded copy.
- **Supervised as the default.** Breaks subagents and headless runs, which have
  nobody to steer them.
- **Agent definitions shipped here.** Subagent definitions live in
  `.claude/agents/` or a plugin, not in a skill folder, and only one host reads
  them. They are the second half of the design, and not built: a plugin beside the
  skills, with a `researcher`, a `worker` and a `reviewer`, would need its own
  place in the repository and its own release path
  ([the zip release](/architecture/the-zip-release.md)).
- **Agent teams or a workflow script for the loop.** The loop is sequential, and
  the parallel parts — researchers, reviewers with different lenses, builders on
  independent steps — are what subagents do. A script that runs the loop belongs
  to a host that has one.

# Not measured

Nothing here has an eval. Four things are open: whether the `description`
triggers on the tasks it should and stays quiet on a one-step edit, which a skill
cannot guarantee for a user who wants the loop on every task, who is better served
by a line in their own instructions file; whether "schedule work on" reaches this
skill rather than a host's scheduler, which the wording asks for and cannot make
happen; whether background subagents keep a supervised conversation open enough to
steer, which depends on the host; and whether three rounds is the right cap. The
GitHub rules come from running issues to pull requests by hand, and none has been
tested on Sonnet or Haiku.
