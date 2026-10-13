---
type: Module
title: Session review
description: The one plugin here, and the one skill that works only in Claude Code. Why it is a plugin, why its name omits the host, the transcript facts behind the condenser, where the observer prompt came from, and the watcher that is not built.
tags: [architecture, plugin, claude-code, distribution]
sources:
  - resource: plugins/**
  - resource: .claude-plugin/**
  - resource: evals/session-review/**
  - id: hank
    resource: https://github.com/SouthBridgeAI/hankweave-runtime/tree/release/alpha/learning/examples/plan-gen-v2-general
    title: hankweave example plan-gen-v2-general
sources_digest: 8b023868b68fd5ab
---

# What it is, and what it refuses to be

`session-review` reads the Claude Code transcripts a user picks and returns
suggestions for improving their everyday work, each with evidence
(`<session>@YYYY-MM-DD HH:MM`): a skill to fix, a habit to automate, a preference to write
down, a permission to allow. It is part 1 of
[issue #48](https://github.com/4e6/skills/issues/48); the watcher is part 2, and
not built (below).

- **Claude Code only.** The transcripts are Claude Code's own files, so there is
  nothing to read elsewhere. Like [Z-Image Turbo on macOS](/architecture/z-image-turbo-macos.md)
  it says so rather than offering a fallback.
- **It applies nothing and posts nothing.** Transcripts hold secrets and private
  work. The condensed text stays on the machine and goes only to subagents of the
  same session; acting on a suggestion is a separate step the user asks for.

# Why a plugin, and where it lives

The issue's option A: skill and watcher in one plugin, with one observer prompt
in one file, so the two cannot drift. The skill sits inside the plugin
(`plugins/session-review/skills/session-review/`) and not in `skills/`, because a
copy in both places is the drift the issue warns of.

- **Installed** by `/plugin marketplace add 4e6/skills` and
  `/plugin install session-review@4e6`. The marketplace is
  `.claude-plugin/marketplace.json` at the repository root, named `4e6`.
- **Also listed by `npx skills`**, as a plain skill, which works in Claude Code
  because nothing in it needs the plugin. Its `description` says Claude Code
  only, so a host that cannot read the transcripts has been told.
- **Not covered by `ln -s skills/*`**, the README's symlink route, which links
  `skills/` only.
- **No zip.** A web host cannot run it: it has no `~/.claude/projects`. Same
  reason as `z-image-turbo-macos` and `llm-wiki`
  ([the zip release](/architecture/the-zip-release.md)).

# The name does not carry the host

Anthropic's guidance reserves "claude" and "anthropic" in skill names, and plugin
names may not start `claude-` or `cc-plugin-`. The repository's own naming rule
(say the narrowness in the name) is about one model or one kind of machine, and a
host is arguably neither. So the restriction is stated in the `description`, the
`compatibility` and the first paragraph, and the name is `session-review`,
invoked as `/session-review:session-review`.

# Versioning: the plugin's number is the skill's

`plugin.json`'s `version` equals the skill's `metadata.version`, and
`tools/release.py check` fails when they differ, zip or no zip. The reason: a set
`version` pins installed copies, so a skill fixed without the plugin's number
raised reaches nobody. Auto-update is off by default for third-party
marketplaces, so users still run `/plugin update` for a version that did move.

# The condenser, and the transcript facts behind it

`scripts/condense.py` is one stdlib Python file with no model in it: cheaper and
deterministic. Its rules rest on a survey of 1962 local transcripts (Claude Code
2.1.236 to 2.1.296, 2026-09-12 to 10-13), a snapshot taken on 2026-10-13; the survey figures below are from it (the robustness and acceptance measurements were taken the same day, at different times). **The format is internal and changes
between versions**, which is why the parser skips unknown record types and unparseable lines (a live file can end mid-line) and stays in one file.

| Rule | The fact behind it |
|---|---|
| Queued prompts are read from `queued_command` attachments | At least 29 of 33 queued prompts in the survey existed nowhere else (a second count found all 33) |
| Assistant records are merged by `message.id`, each block emitted once | one message is written as several records |
| A tool result is paired with its call by `tool_use_id` | results arrive as later user records |
| Records are deduped by `uuid` across a run | a continued session copies the history |
| Sessions are condensed oldest first, in one call | the oldest keeps the shared history, whatever the order given; a continuation then shows only what is new |
| Every line is cited with its day | a session can span days, and `[HH:MM]` alone repeats; the condenser writes a `--- day ---` line before the first line |
| Thinking is kept only if non-empty | 97.6% of it is empty |
| Tool output is cut to a head, errors kept longer | tool output is about 46% of the bytes |
| Secrets are redacted in every emitted string, and redaction fails safe | transcripts hold them, and the text goes to subagents. A pattern is never narrowed to spare a false positive if that opens a leak: twice in review, a narrowing meant to keep ordinary text readable let real secrets through (a private key in escaped JSON, a password holding a bracket), and the tests now hold both shapes |

- **Headless runs are skipped by default** (`entrypoint` `sdk-*`): 222 of 365
  sessions in the 4e6 projects. They are scripted work, not how the user works.
- **The activity floor is 10 tool calls, not a prompt count.** A supervised run
  is one prompt and hours of work.
- **Caps**: a tool's input 500 characters, a brief handed to a subagent 1000 (what
  a person told a subagent is worth more than a shell script), human and assistant
  text 10,000. Chosen to keep what a reviewer cites and drop what only costs
  tokens; not tuned against suggestion quality.
- **Measured** (counted at a different time from the survey, so the file count
  differs): 1949 files, 0 crashes, 1.6 GB in and 77 MB out (ratio 0.047).
- **Tests** are `evals/session-review/`, outside the skill because whatever is in
  it ships. A synthetic fixture covers each rule, and secret-shaped strings are
  built at run time, never committed whole (push protection, public repo).

# The observer prompt

`references/observer.md` is the prompt and taxonomy a reviewing agent applies to a
condensed session. It comes from the sentinel in Southbridge's hankweave example
`plan-gen-v2-general`:[^hank] its ten categories reworded, plus four of ours (user
corrections, skill friction, repeated manual sequences, permission prompts and
denials), and its output rules (actionable only, terse, repeats consolidated,
silence when there is nothing). It is **one file** so the watcher can reuse it
unchanged on a window of events instead of a whole session.

# Why `${CLAUDE_SKILL_DIR}` and `${CLAUDE_SESSION_ID}`

The skill runs its script as `${CLAUDE_SKILL_DIR}/scripts/condense.py`. Claude
Code substitutes it for a plugin skill and a plain skill alike. A relative path
depends on the working directory; `${CLAUDE_PLUGIN_ROOT}` is not in Bash's
environment and would break the plain install. Both variables were checked on a
real host, 2.1.296: `claude -p --plugin-dir`, and as a project skill.

# Part 2, not built: the watcher

The owner's comment on the issue asks to switch it with `/plugin enable`.
Enabling is per plugin and persists in a settings scope, so a watcher in this
plugin would be on whenever the skill is. The likelier shape is a **second
plugin** with `defaultEnabled: false`, sharing `observer.md` by a symlink inside
the marketplace. The docs say a symlink is dereferenced on a Git install and
skipped for local-path installs; no real install has verified it. `claude -p
--bare` accepts only `ANTHROPIC_API_KEY`, so a hooks module calling
`$.model.complete` and showing `$.ui.toast` or `$.ui.status` is the likelier
route than a headless child. **Open for the user**, who judges the skill's
suggestions first.

# The report's shape: a suggestion a reader can judge

1.0.0 reported each suggestion as a line, a count and `session@time` references.
The owner's feedback on the first run was that a suggestion without context was
hard to judge: reading it meant reopening the cited sessions and rebuilding the
story. Two faults sat behind that.

- **It never looked at the file it wanted changed.** One suggestion, that a push
  after approval needs a fresh review, is already a rule in this repository's
  `supervise-work` (step 6). The report could not tell that apart from a rule
  that is in place and still broken, and the two call for different actions: the
  first needs nothing, the second needs the rule reworded.
- **"Seen N times" summed the observers' own counts.** An observer counting per
  tool call made a pattern look heavier than one counted per session, so it
  measured how the logging went, not the weight. Grouping now counts sessions
  and ranks by them, then by corrections and interruptions among the
  observations. A continued session has its own id and counts as a second one.

So grouping keeps each suggestion's observations, and step 6 hands the strongest
ten to a checker each, on the strongest model, because it judges whether a rule
covers a case. The checker reads one or two cited places and the target as it is
today, dates a rule against the incidents where git allows, and writes four
parts: what happened, one instance, status now, the change. The rest stay one
line. The brief is `references/checker.md`, a file like `observer.md`, so a host
without subagents follows it itself.

- **Cost is an estimate, not a measurement.** About ten strongest-model
  subagents, each reading a few hundred lines of condensed text and a target
  file, on top of the observers.
- **Status is dated only where git reaches.** A commit date is when the source
  changed, not when an installed copy got it, so a pinned copy is "likely
  addressed". Git is never run in the plugin cache or a marketplace clone.
- **Rejected:** richer observer lines (an observer sees one session, and context
  needs the cross-session view and the target); checking every suggestion (cost
  follows the long tail); checking on the smallest model (it is a judgement).

# Measurements

The issue's first check, on 2026-10-13, ran 1.0.0 as shipped: a real headless host
(`claude -p --plugin-dir`, Claude Code 2.1.296) over every project under one
prefix of the author's, last 30 days, default filters. It read 114 sessions (about
4.8M condensed tokens; 222 headless runs and 30 under the activity floor left out)
in 44 observer batches on Haiku, collected 737 observations, and grouped them into
24 suggestions and 25 notes, for USD 15.76. The suggestions named the file or rule
to change, and the routes covered every kind the skill lists. The report stays with
its owner: it names private projects.

What it does not show:

- **No eval.** Whether a suggestion is worth acting on was judged by reading, once,
  by the author's agent; nothing scores it.
- **Counts were loose.** 1.0.0's "seen N times" summed the observers' own counts, so a
  pattern that one observer counted per tool call looked bigger than one counted per
  session. 1.1.0 counts sessions.
- **One user, one machine, one model mix.** Smaller observers than Haiku, or another
  grouping model, were not tried.

**1.1.0 is not measured**: there was no run of it, by the owner's choice, and the new report shape is untested on real data.

The run predates the fixes of the first code review (the observer path became
`${CLAUDE_SKILL_DIR}`-absolute, session order oldest first, day-stamped citations);
the host already passed observers an absolute path.

[^hank]: The sentinel is `sentinels/implementation-observer.json` in that example.
