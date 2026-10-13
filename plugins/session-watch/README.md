# session-watch

A [Claude Code](https://code.claude.com) plugin that watches your session while
you work. When the session goes quiet, a small model (Haiku) reads the new part
of the conversation and tells you, in a line in your terminal, what could be
improved in how the work is set up: where the agent circled, where you had to
correct it, where a permission got in the way. It applies nothing, and Claude
never sees what it shows.

It is the live counterpart of [session-review](../session-review/skills/session-review/),
and reads with the same prompt (`observer.md` here is a link to that file, so
the two cannot drift). It works **only in Claude Code**, and **only in an
interactive session**: with `claude -p` nobody is there to see it, so it makes
no call.

## Off by default

Installing it does not turn it on:

```
/plugin marketplace add 4e6/skills
/plugin install session-watch@4e6
/plugin enable session-watch@4e6
```

or in a terminal, choosing where it is remembered:

```
claude plugin enable session-watch@4e6 --scope local     # this project, only you
claude plugin enable session-watch@4e6 --scope project   # this project, everyone who shares its settings
claude plugin enable session-watch@4e6 --scope user      # every project of yours
```

Enabling is not "for this session". It is stored in that scope's settings, so it
runs in every new interactive session there until you turn it off:

```
/plugin disable session-watch@4e6
```

Whether enabling takes effect in a session already running, or only in the next
one, is not verified; restart to be sure.

## What it does

- After each of the session's own turns it waits 20 seconds. If you send
  something before then, it waits again; it only ever looks while the session is
  idle, so it never slows a turn.
- It looks once at least 3 turns, or 2 tool calls that failed or were denied,
  have passed since the last look. It reads at most the last 40 entries of the
  conversation, cut short, 24 000 characters in all.
- It makes one call to Haiku (low effort, at most 1 000 tokens out) with the observer
  prompt and that slice. The debug log (`claude --debug`) gets one line per look
  with the messages read, the observations and the tokens used.
- Each observation is one line in the terminal, `session-watch: <category>: <line>`
  (Claude Code puts the plugin's name in front). If the same category and tool or skill was seen earlier in the
  session, it also draws a toast: once is a note, a repeat is worth a look.
- Anything that goes wrong (the session ends, the model is blocked by your
  organization, the call is slow) is silent. The one exception is a missing
  `observer.md` (see Requirements): then it says so once per session.

## What it costs

One Haiku call per look, on the plan or key the session already uses. About a
tenth of a cent per look at the cap. That is an estimate: at Haiku 5.5's list
price (USD 0.10 per million input tokens, 0.50 per million output), the
24 000-character cap may be 7 000 to 8 000 tokens with its tokenizer, plus about
1 500 for the prompt, and at most 1 000 tokens come back, so a look costs at most
about 0.14 cent. Most looks read less than the cap, and quiet sessions look rarely.
Each look writes the tokens it actually used to the debug log, so you can check.
No prompt caching is claimed: the prompt is probably below the minimum length that
gets cached, and nothing showed it being cached.

## Where it shows, and that Claude never sees it

Each line is written to the terminal as a system notice, which Claude Code does not
send to the model, and a repeat is also shown as a toast. The mod never submits a
prompt, runs a command or appends to the conversation.

This rests on three things. On Claude Code 2.1.296, in an interactive session,
Claude, asked, had not seen any such line. The API says `$.ui.log` shows a line
to the user and it is "not sent to the model". And the line is saved as a record
of type `system`, subtype `informational`, which session-review's condenser drops
(`condense.py` keeps `system` records only for `compact_boundary`, lines 482 and
522). Whether a line is also absent after `--resume` is not shown here.

**Each shown line is also saved in the session's transcript file on disk**, and the
debug log (`claude --debug`) has it too. So it is a record for you, not input for
Claude, but it is not unwritten.

## Privacy

The slice goes to the same provider the session already talks to, under the same
terms; it was in the session's context already. The mod writes no files of its
own (the host saves the lines it shows, as above), and keeps its counters in memory only: ending the session or reloading
plugins resets them, at worst one extra look and a repeat toasting afresh.

## Requirements and limits

- Tested on Claude Code 2.1.296; mods need 2.1.287 or later. The plugin API it uses (mods) is early access and
  may change between releases.
- `observer.md` is a symlink to a file in the `session-review` plugin. A marketplace
  install from GitHub brings the file along; a local folder added as a
  marketplace, or a checkout without symlinks (Windows without them), may not
  resolve it. Then the plugin logs that once to the debug log, shows one line
(`observer.md missing — session-watch is idle; reinstall the plugin`) and makes
no checks.
- Saved only as a system notice in the session's transcript, which session-review's
  condenser skips; the mod stores nothing of its own, so `session-review` does not
  see the observations.

## For testing

Two environment variables shorten it: `SESSION_WATCH_IDLE_MS` (at least 2000) and
`SESSION_WATCH_EVERY` (turns between looks, at least 1). `SESSION_WATCH_TEST_OBSERVATION=1`
adds one fixed line after the next look, to check that lines are drawn. They are
for trying it out, not for daily use.

## Licence

MIT, see [LICENSE](LICENSE).
