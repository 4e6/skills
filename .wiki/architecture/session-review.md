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
sources_digest: 60961fe03d478fc5
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
2.1.236 to 2.1.296, 2026-09-12 to 10-13), a snapshot taken on 2026-10-13; every figure below is from it. **The format is internal and changes
between versions**, which is why the parser skips unknown record types and unparseable lines (a live file can end mid-line) and stays in one file.

| Rule | The fact behind it |
|---|---|
| Queued prompts are read from `queued_command` attachments | At least 29 of 33 queued prompts in the survey existed nowhere else (a second count found all 33) |
| Assistant records are merged by `message.id`, each block emitted once | one message is written as several records |
| A tool result is paired with its call by `tool_use_id` | results arrive as later user records |
| Records are deduped by `uuid` across a run | a continued session copies the history |
| Sessions are condensed oldest first, in one call | the first one given keeps the shared history, so it must be the original; a continuation then shows only what is new |
| Every line is cited with its day | a session can span days, and `[HH:MM]` alone repeats; the condenser writes a `--- day ---` line before the first line |
| Thinking is kept only if non-empty | 97.6% of it is empty |
| Tool output is cut to a head, errors kept longer | tool output is about 46% of the bytes |
| Secrets are redacted in every emitted string | transcripts hold them, and the text goes to subagents |

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

# Measurements

Not yet measured. The quality of the suggestions has no eval; the acceptance run's
counts will be added here.

[^hank]: The sentinel is `sentinels/implementation-observer.json` in that example.
