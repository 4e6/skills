---
type: Module
title: Session watch
description: The opt-in live watcher, a mod in a second plugin. Why a mod and a second plugin, what it shows and where it lands, what was verified on 2.1.296, the shared observer.md and its version rule, how to test it, and what is still open.
tags: [architecture, plugin, claude-code, mod]
sources:
  - resource: plugins/session-watch/**
  - resource: tools/release.py
  - resource: .claude-plugin/marketplace.json
sources_digest: 49bf8b52ff824fbf
---

# What it is, and what it refuses to be

`session-watch` is part 2 of [issue #48](https://github.com/4e6/skills/issues/48),
the live counterpart of [session-review](/architecture/session-review.md). It is a
Claude Code *mod* (a hooks module, `hooks/register.ts`), not a skill. While an
interactive session works it counts main-loop turns; when the session has been
idle, it has Haiku read the new part of the conversation with the observer prompt
and shows what it finds to the user. It applies nothing, saves nothing of its own,
and works only in an interactive session (`$.session.surfaces()` is empty under
`-p`, so it makes no call).

# Why a mod, and why a second plugin

- **A second plugin** because enablement is per plugin and persists: inside
  `session-review` the watcher would be on whenever the skill is. The owner asked
  for `/plugin enable`, so the plugin is `defaultEnabled: false`.
- **Enabling persists per scope**: `claude plugin enable session-watch@4e6 --scope
  user|project|local`. It is not "for this session"; it runs in every new
  interactive session of that scope until `/plugin disable`.
- **A mod and no API key path.** A command hook running `claude -p --bare` accepts
  only `ANTHROPIC_API_KEY`, which is ruled out. `$.model.complete` resolves on the
  session's own login.
- **Rejected for 1.0.0:** a `/watch on|off` command (the owner asked for
  `/plugin enable`); an above-prompt band with Keep and Dismiss (more state; a
  follow-up); `$.ui.status` and `$.prompt.suggest` (the second reaches Claude when
  accepted); checking mid-turn (more calls, interleaves with the work); saving the
  observations for session-review (it has no reader for them yet); `userConfig`
  knobs (the thresholds are guesses until used).

# Triggers: idle only

On a main-loop `turn.complete` it counts the turn and arms a 20 s timer; a
`turn.start` cancels it, so a check never competes with a turn. A check is due at 3
turns, or 2 errored tool uses (a denied call is one) in the new part. It reads at
most 40 entries, cut, 24 000 characters in all, and makes one call. A cursor (the
last `tool_use_id` seen plus the messages after it) says what is new. With no anchor
(a session without tool use) or one not found, it starts after the message count of
the previous check, unless the conversation shrank below it; then the last 40. Model
text is cleaned before it is drawn (control characters and ESC stripped; line cut to
300 characters, category to 40). The call asks for low effort and at most 1000 tokens,
and the debug line records the tokens used or the reason it was not answered. Any
failure is silent, except a missing `observer.md`, which shows one visible line per
session. The renderer follows `observer.md`'s grammar, and
every line carries the time of the check, since messages carry none. A reply line
that is not a JSON object with a category and a line is dropped.

# What is shown, and where it lands

Each observation is a `$.ui.log` line; a repeat of a category and tool is also a
toast; identical lines are shown once. The host puts the plugin's name before a
transcript line (the mod's own prefix showed up doubled in the first interactive
run, so it writes none) and over a toast; the debug sink gets `[session-watch]` the
same way.

What was verified on 2.1.296 (interactive, expect-driven):

- The idle check fires in a real session; the Haiku call is answered in about a
  second.
- Claude, asked in the same session, had not seen a line. The claim that a line is
  not sent to the model rests on that, on the `$.ui.log` contract ("not sent to the
  model"), and on the record type below, which session-review's condenser drops
  (`condense.py` lines 482 and 522: `system` records count only for
  `compact_boundary`). The earlier `--resume` evidence was invalid (the question
  held the marker's prefix, and earlier turns held the marker), so no resume claim
  is made.
- **But each shown line is saved in the session's transcript JSONL** as
  `{"type":"system","subtype":"informational","content":…,"level":"notice"}`. The
  READMEs say so. "The mod writes no files of its own" is the accurate claim.
- The `cache: true` mark was dropped (no caching was shown). The README's cost,
  about a tenth of a cent per check at the cap, is an estimate from the window cap
  and Haiku 5.5's list price (USD 0.10 / 0.50 per million tokens); the debug line
  now records the tokens each call used.

# The shared prompt, and the version rule

`plugins/session-watch/observer.md` is a relative symlink to session-review's
`observer.md`, so the two cannot drift. It is read with `$.fs.read`, and must begin
`# Observer` or the mod logs once to the debug log, shows one visible line, and makes
no checks. An installed
copy keeps its version, so editing the prompt reaches nobody unless every linking
plugin is bumped: `tools/release.py check` fails a symlink whose target's last commit
is newer than the last commit that changed the plugin's `version`
([the zip release](/architecture/the-zip-release.md)). The rule lists symlinks from
HEAD's tree (a directory link counts), faults on a target no longer in HEAD, and
faults in a shallow clone, which lacks the history it needs. A plugin with no skill is
allowed; its version must still be MAJOR.MINOR.PATCH.

# Testing it

- `claude plugin validate --strict plugins/session-watch` and `.`; `claude plugin
  test plugins/session-watch` runs `test/*.test.ts` with a mock clock and stubbed
  `$` calls. The validator wants helpers that take `$` to be top-level functions.
- `--plugin-dir` does not load a `defaultEnabled: false` plugin unless given
  `--settings '{"enabledPlugins":{"session-watch@inline":true}}'`.
- Knobs, for tests: `SESSION_WATCH_IDLE_MS` (at least 2000), `SESSION_WATCH_EVERY`
  (at least 1), `SESSION_WATCH_TEST_OBSERVATION=1` (one fixed line after a real call).
- The interactive proof drives the TUI with `expect` in a pty. The workspace-trust
  prompt defaults to No, so the script must answer it; unset the inherited
  `CLAUDE_CODE_*` session variables first. Grep the transcript JSONL before any
  prompt that mentions the marker.
- Prompt quality on a synthetic window (circling, a user correction, a denial) came
  back as clean JSON lines under `permission`, `circling` and `missing-context`
  (no `correction`); a control window gave no output. Real sessions are untested.

# Facts and state

Spike facts are from 2026-10-13 on Claude Code 2.1.296: a model call from a timer
resolves on the session's login; `-p` does not wait for timers, and a timer can fire
after the session is unbound, so the whole callback sits in one try. Module state
(counters, cursor, seen set, timer) is in memory: a reload resets it, at worst one
extra check and repeats toasting afresh; every `session.end`, whatever its reason,
resets it too.

# Open

- Does `/plugin enable` take effect without a restart? (A real install writes
  `~/.claude`.)
- Does a Git install dereference the shared symlink? The docs say so; a local
  `--plugin-dir` confirmed it.
- Where an organization's model allowlist blocks Haiku, the call rejects and the mod
  stays silent.
- Prompt quality on real sessions.
