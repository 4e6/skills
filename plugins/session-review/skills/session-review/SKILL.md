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
  ~/.claude/projects (or under CLAUDE_CONFIG_DIR). Its script needs Python 3;
  without it nothing can be condensed and the skill stops and says so. Best
  where it can start subagents; without them each pass is done by the same agent.
metadata:
  author: 4e6
  version: "1.1.0"
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
- [ ] 6  check the strongest suggestions
- [ ] 7  report
```

The script is `${CLAUDE_SKILL_DIR}/scripts/condense.py`; run it with `python3`.
Without Python 3 it cannot run: stop and tell the user, as nothing else reads
the transcripts safely.

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
`--exclude ${CLAUDE_SESSION_ID}`. Show the user the count and the token estimate (an estimate: it counts a continued session's repeated history, which step 3 leaves out). When the scope is
large, more than about 30 sessions or 500,000 tokens, say what it will cost and
ask which to narrow before going on. The check in step 6 adds about ten subagents
on the strongest model. For a theme, choose sessions by title or
`--grep`.

## 3. Condense

```
python3 ${CLAUDE_SKILL_DIR}/scripts/condense.py condense SESSION_ID... --out DIR
```

Give the whole scope in one call: sessions are written oldest first, and a
continued session shows only what its parent did not. `DIR` is a new scratch
folder outside every project. `--subagents` adds each
subagent's own work; leave it off unless the theme is about subagents.

## 4. Observe

Give each condensed file to a fresh subagent on the smallest model, a batch of
small ones to one subagent within its context. Its brief names the files and
says to read `${CLAUDE_SKILL_DIR}/references/observer.md` (give the full path, as the
subagent does not start in this folder) and follow it.
Without subagents, do one pass per batch yourself, from that file. Collect the
observations.

## 5. Group

Do this on the strongest model, alone or in a subagent. Merge observations
that are the same thing across sessions. A thing seen in more than one session
is a **suggestion**; one seen once is a **note**. Keep each suggestion's
observations with it: their lines, quotes and evidence. Count its sessions, not
the observers' counts added up. Rank by sessions, then by the number of
`correction` observations and interruptions among its observations. Give each
suggestion one route:

- a change to a skill, as a pull request;
- a preference, as a line for the user's global instructions file;
- project knowledge, for that project's wiki;
- a new script, hook or skill;
- a permission allowlist entry, or `/fewer-permission-prompts` where the host has it.

Drop what no one can act on.

## 6. Check

Check the strongest suggestions, about ten. Give each to a fresh subagent on the
strongest model, as that judges whether a rule already covers the case. Its brief
has the suggestion with its observations, its route and the condensed files' paths,
and says to read `${CLAUDE_SKILL_DIR}/references/checker.md` (give the full path) and
follow it. Without subagents, follow that file yourself, one suggestion at a time.
The rest stay one line each.

## 7. Report

In this order:

1. **Checked suggestions**, strongest first, each in the four parts the checker
   returns, with its route, sessions and evidence.
2. **Other suggestions**, one line each: the change, its route, sessions, evidence.
3. **Already addressed**, including likely addressed: one line each, with where.
4. **Notes**, one line each, with evidence.
5. What was read and what was skipped, with the counts.

Then ask which suggestions to act on. Delete the scratch folder now, not before
step 6 is done.
