---
name: session-review
description: >-
  Reads the user's past Claude Code sessions and suggests how to improve their
  everyday work, with evidence from the sessions: skills to fix, habits to
  automate, preferences to write down, permissions to allow. Applies nothing.
  Use when the user asks to review, analyse or learn from their past sessions
  or history, to find what keeps going wrong or repeating, or to improve their
  skills, instructions or setup from how they actually work. Works only in
  Claude Code, which keeps the transcripts it reads.
license: MIT
compatibility: >-
  Claude Code only: reads the session transcripts Claude Code keeps in
  ~/.claude/projects (or under CLAUDE_CONFIG_DIR). Its script needs Python 3.
  Best where it can start subagents; without them each pass is done by the same
  agent.
metadata:
  author: 4e6
  version: "1.0.0"
---

# Session review

This skill works only in Claude Code: it reads the transcripts Claude Code keeps
of past sessions. It finds what could be better in how the user works with
agents, and suggests changes. **It applies nothing**, and posts nothing anywhere.
Transcripts can hold secrets and private work: the condensed text stays on this
machine and goes only to subagents of this session.

```
- [ ] 1  settle the scope
- [ ] 2  list the sessions
- [ ] 3  condense them
- [ ] 4  observe each
- [ ] 5  group the observations
- [ ] 6  report
```

The script is `${CLAUDE_SKILL_DIR}/scripts/condense.py`; run it with `python3`.

## 1. Settle the scope

Projects, a date range, particular sessions, or a theme such as one skill's
runs. Unless the user says otherwise: the current project, the last 30 days.
Claude Code deletes transcripts after 30 days by default, so older ones may be gone.

## 2. List the sessions

```
python3 ${CLAUDE_SKILL_DIR}/scripts/condense.py list [--project PATH ...] [--all] [--since 30d|YYYY-MM-DD] [--until DATE] [--min-prompts N] [--min-tool-calls N] [--include-headless] [--exclude SESSION_ID ...] [--grep TEXT] [--json]
```

By default it takes the current directory's project, and skips headless runs and
sessions with fewer than 10 tool calls. Leave out this session with
`--exclude ${CLAUDE_SESSION_ID}`. Show the user the count and the token estimate. When the scope is
large, more than about 30 sessions or 500,000 tokens, say what it will cost and
ask which to narrow before going on. For a theme, choose sessions by title or
`--grep`.

## 3. Condense

```
python3 ${CLAUDE_SKILL_DIR}/scripts/condense.py condense SESSION_ID... --out DIR
```

`DIR` is a new scratch folder outside every project. `--subagents` adds each
subagent's own work; leave it off unless the theme is about subagents.

## 4. Observe

Give each condensed file to a fresh subagent on the smallest model, a batch of
small ones to one subagent within its context. Its brief names the files and
says to read [references/observer.md](references/observer.md) and follow it.
Without subagents, do one pass per batch yourself, from that file. Collect the
observations.

## 5. Group

Do this on the strongest model, alone or in a subagent. Merge observations
that are the same thing across sessions. A thing seen in more than one session
is a **suggestion**; one seen once is a **note**. Give each suggestion one route:

- a change to a skill, as a pull request;
- a preference, as a line for the user's global instructions file;
- project knowledge, for that project's wiki;
- a new script, hook or skill;
- a permission allowlist entry, or `/fewer-permission-prompts` where the host has it.

Drop what no one can act on.

## 6. Report

In this order:

1. **Suggestions**, strongest first: the change in a line or two, its route, how
   many times and in how many sessions, and the evidence as `session@HH:MM`.
2. **Notes**, one line each, with evidence.
3. What was read and what was skipped, with the counts.

Then ask which suggestions to act on. Delete the scratch folder.
