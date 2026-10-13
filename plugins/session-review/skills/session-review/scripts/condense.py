#!/usr/bin/env python3
"""Claude Code session transcripts, condensed to what a reviewer needs to read.

A transcript is a JSONL file of everything the harness recorded: the human's
prompts, the model's text, every tool call and its full output, plus a great
deal of bookkeeping (system reminders, file snapshots, token counts, signatures
of thinking blocks that are empty). A long session is tens of megabytes, of
which the part that says how the work went is a few percent. Reading it raw
would cost more than the review is worth, so this script keeps the part that
shows how the work went and drops the rest. It uses no model, so the same file
always condenses to the same text.

    python3 condense.py list [--project PATH ...] [--all] [--since 30d]
    python3 condense.py condense SESSION... [--out DIR] [--subagents]

`list` prints one line per session, newest first, so a person or an agent can
choose what to read. `condense` writes one text file per session, and prints
each path with its size.

What a condensed line is (each line is addressable as <session-id>@HH:MM):

    [HH:MM] USER: what the human typed          also queued mid-turn, and /cmd args
    [HH:MM] ASSISTANT: what the model said      THINK: its thinking, when kept
    [HH:MM] TOOL Bash#4: {"command": "..."}     numbered per session
      -> ok (1.2KB): the first 300 characters
      -> ERROR(permission-rule): ...            ERROR when the tool failed
      -> REJECTED: what the human said          the human refused the call
    [HH:MM] INTERRUPTED / COMPACTED / API ERROR

The transcript format is internal to Claude Code and changes between versions
(this was written against 2.1.236 to 2.1.296), so the parser is deliberately
forgiving: a line that does not parse, and a record type it does not know, are
skipped, never an error. A session still being written can end in a half line.

Every string that is written out passes through `redact` first, so a key or a
password a session printed does not travel into a review. This is a net with
holes (it knows the common shapes, not every secret): the condensed text stays
on this machine, and nothing here sends it anywhere.

Python 3.9, standard library only, no network. It reads transcripts and writes
only the files `condense` is asked for.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys
import tempfile

# How much of each thing is kept. A tool's input and a long answer are cut at
# a size where the shape is still visible; the human's words and the human's
# refusals are cut only far enough to stop a pasted log from filling a file.
INPUT_STRING_MAX = 500
BRIEF_MAX = 1000  # what a person told a subagent is worth more than a shell script
BRIEF_TOOLS = ("Agent", "Task", "SendMessage")
RESULT_OK_MAX = 300
RESULT_ERROR_MAX = 600
HUMAN_TEXT_MAX = 10000
ASSISTANT_TEXT_MAX = 10000
THINK_MAX = 3000
FEEDBACK_MAX = 4000
TITLE_MAX = 100

# Characters per token, for the estimate `list` prints. English prose with code
# in it lands near four; the estimate only has to rank sessions and size a batch.
CHARS_PER_TOKEN = 4

# --- secrets ---------------------------------------------------------------
#
# The shapes of secrets that turn up in a terminal session. Patterns are not
# written out as literal examples here or in the tests, so that no file in the
# repository looks like a leak to a scanner.

REDACTED = "[REDACTED]"

SECRET_PATTERNS = [
    # PEM private keys, whole block; and a block cut off before its end line.
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S), REDACTED),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*", re.S), REDACTED),
    (re.compile(r"\bsk-[A-Za-z0-9_\-]{20,}"), REDACTED),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}"), REDACTED),
    (re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}"), REDACTED),
    (re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"), REDACTED),
    (re.compile(r"\bAIza[0-9A-Za-z_\-]{35}"), REDACTED),
    (re.compile(r"\bxox[abprso]-[A-Za-z0-9\-]{10,}"), REDACTED),
    (re.compile(r"\bglpat-[A-Za-z0-9_\-]{20,}"), REDACTED),
    (re.compile(r"\bnpm_[A-Za-z0-9]{30,}"), REDACTED),
    # A JSON web token: header.payload.signature, the first two base64url JSON.
    (re.compile(r"\beyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]*"), REDACTED),
    # Authorization headers keep their scheme so the line still reads.
    (re.compile(r"\b(Bearer|Basic)(\s+)[A-Za-z0-9._~+/=\-]{16,}"), r"\1\2" + REDACTED),
    # Credentials inside a URL: scheme://user:password@host.
    (re.compile(r"\b([a-z][a-z0-9+.\-]*://)[^\s/:@]+:[^\s/@]+@"), r"\1" + REDACTED + "@"),
]

# NAME=value or "name": "value", where the name says it is a secret. A value
# shorter than eight characters, all digits, or a reference ($VAR, <placeholder>)
# is not a secret worth hiding, and hiding it would also eat "max_tokens": 4096.
KEY_VALUE = re.compile(
    r"""(?ix)
    ([A-Za-z0-9_.\-]{0,40}(?:password|passwd|secret|token|api[_\-]?key|apikey)[A-Za-z0-9_.\-]{0,40})
    (["']?\s*[=:]\s*["']?)
    ([^\s"'&,;]{8,})
    """
)


def _key_value(m: re.Match) -> str:
    value = m.group(3)
    if value.isdigit() or value[0] in "$<{(%[":
        return m.group(0)
    return m.group(1) + m.group(2) + REDACTED


def redact(text: str) -> str:
    """Replace anything shaped like a secret. Idempotent."""
    for pattern, replacement in SECRET_PATTERNS:
        text = pattern.sub(replacement, text)
    return KEY_VALUE.sub(_key_value, text)


# --- small text helpers ----------------------------------------------------


def clip(text: str, limit: int) -> str:
    """Cut to `limit` characters and say how many were left out."""
    if len(text) <= limit:
        return text
    return text[:limit] + "...[+%d chars]" % (len(text) - limit)


def one_line(text: str) -> str:
    return re.sub(r"\s*\n\s*", " ⏎ ", text.strip())


def size_label(n: int) -> str:
    if n < 1024:
        return "%dB" % n
    if n < 1024 * 1024:
        return "%.1fKB" % (n / 1024)
    return "%.1fMB" % (n / (1024 * 1024))


SYSTEM_REMINDER = re.compile(r"<system-reminder>.*?</system-reminder>", re.S)
COMMAND_NAME = re.compile(r"<command-name>\s*(.*?)\s*</command-name>", re.S)
COMMAND_ARGS = re.compile(r"<command-args>(.*?)</command-args>", re.S)
BASH_INPUT = re.compile(r"<bash-input>(.*?)</bash-input>", re.S)

# What the harness sends as a "user" message that no human wrote.
NOT_HUMAN_PREFIXES = (
    "<task-notification",
    "<local-command-",
    "<bash-stdout",
    "<bash-stderr",
    "<agent-message",
)


def parse_time(stamp):
    """An ISO timestamp as an aware datetime in the local zone, or None."""
    if not isinstance(stamp, str):
        return None
    try:
        parsed = datetime.datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=datetime.timezone.utc)
    return parsed.astimezone()


# --- parsing one transcript ------------------------------------------------


class Session:
    """What one transcript file holds, as a list of events plus counts."""

    def __init__(self, path: str, subagent: bool = False):
        self.path = path
        self.id = os.path.splitext(os.path.basename(path))[0]
        self.subagent = subagent
        self.events = []
        self.cwd = ""
        self.entrypoint = ""
        self.version = ""
        self.branches = []
        self.models = []
        self.first = None
        self.last = None
        self.ai_title = ""
        self.agent_name = ""
        self.last_prompt = ""
        self.skipped_seen = 0
        self.prompts = 0
        self.tool_calls = 0
        self.errors = 0
        self.denials = 0
        self.interrupts = 0
        self.compactions = 0
        self.api_errors = 0

    @property
    def human_texts(self):
        return [e["text"] for e in self.events if e["kind"] in ("user", "cmd")]

    @property
    def title(self) -> str:
        if self.ai_title:
            return self.ai_title
        if self.agent_name:
            return self.agent_name
        if self.last_prompt:
            return one_line(self.last_prompt)
        for event in self.events:
            if event["kind"] == "user":
                return one_line(event["text"])
        return ""

    @property
    def headless(self) -> bool:
        return self.entrypoint.startswith("sdk")


def result_text(content) -> str:
    """A tool result's content as text. Images become a marker."""
    if isinstance(content, str):
        return content
    parts = []
    if isinstance(content, list):
        for item in content:
            if not isinstance(item, dict):
                continue
            if item.get("type") == "text" and isinstance(item.get("text"), str):
                parts.append(item["text"])
            elif item.get("type") == "image":
                parts.append("[image]")
    return "\n".join(parts)


def walk_strings(value, limit=INPUT_STRING_MAX):
    """A tool input with every string redacted and cut, shape kept."""
    if isinstance(value, str):
        return clip(redact(value), limit)
    if isinstance(value, list):
        return [walk_strings(v, limit) for v in value]
    if isinstance(value, dict):
        return {k: walk_strings(v, limit) for k, v in value.items()}
    return value


def parse(path: str, seen: set, subagent: bool = False) -> Session:
    """Read one transcript into a Session. `seen` holds uuids already taken."""
    session = Session(path, subagent)
    calls = {}  # tool_use id -> its event, so a result finds its call
    shown = set()  # (message id, block key): a block is written once
    state = {"tool_n": 0}

    def add(kind, rec, **fields):
        event = {"kind": kind, "time": parse_time(rec.get("timestamp")), "text": ""}
        event.update(fields)
        session.events.append(event)
        return event

    def human(rec, text):
        """Classify text a human (or the harness posing as one) sent."""
        text = SYSTEM_REMINDER.sub("", text).strip()
        if not text:
            return
        if text.startswith("[Request interrupted by user"):
            session.interrupts += 1
            add("interrupt", rec, text=text.strip("[]").replace("Request interrupted by user", "").strip())
            return
        if text.startswith(NOT_HUMAN_PREFIXES):
            return
        name = COMMAND_NAME.search(text)
        if name:
            args = COMMAND_ARGS.search(text)
            command = (name.group(1) + " " + (args.group(1).strip() if args else "")).strip()
            session.prompts += 1
            add("cmd", rec, text=clip(redact(command), HUMAN_TEXT_MAX))
            return
        bash = BASH_INPUT.search(text)
        if bash:
            session.prompts += 1
            add("user", rec, text=clip(redact("! " + bash.group(1).strip()), HUMAN_TEXT_MAX))
            return
        if subagent:
            add("brief", rec, text=clip(redact(text), BRIEF_MAX))
            return
        session.prompts += 1
        add("user", rec, text=clip(redact(text), HUMAN_TEXT_MAX))

    def tool_result(rec, item):
        call = calls.get(item.get("tool_use_id"))
        content = result_text(item.get("content"))
        kind = rec.get("toolDenialKind")
        feedback = rec.get("userFeedback")
        result = {"size": len(content), "error": bool(item.get("is_error"))}
        if result["error"]:
            session.errors += 1
            if kind:
                session.denials += 1
            if kind == "user-rejected":
                result["label"] = "REJECTED"
                if isinstance(feedback, str) and feedback.strip():
                    result["text"] = clip(redact(feedback.strip()), FEEDBACK_MAX)
                else:
                    result["text"] = ""  # the rest is the harness's stock wording
            else:
                result["label"] = "ERROR(%s)" % kind if kind else "ERROR"
                if kind:
                    content = content.split(" IMPORTANT:")[0]  # drop the stock advice after the reason
                result["text"] = clip(redact(one_line(content)), RESULT_ERROR_MAX)
        else:
            result["label"] = "ok"
            persisted = re.search(r"Output too large \(([^)]+)\)", content) if "<persisted-output>" in content else None
            if persisted:
                result["label"] = "ok [persisted %s]" % persisted.group(1)
                content = content.split("Preview (first", 1)[-1].split("\n", 1)[-1].replace("</persisted-output>", "")
            result["text"] = clip(redact(one_line(content)), RESULT_OK_MAX)
        tool_use_result = rec.get("toolUseResult")
        agent = tool_use_result.get("agentId") if isinstance(tool_use_result, dict) else None
        if not agent:
            found = re.search(r"agentId: ([A-Za-z0-9]+)", content)
            agent = found.group(1) if found else None
        if call is None:
            # The call was in a part of the history this file does not hold.
            add("orphan", rec, result=result)
        elif "result" not in call:
            call["result"] = result
            call["agent"] = agent

    def on_user(rec):
        if rec.get("isCompactSummary"):
            return
        message = rec.get("message")
        content = message.get("content") if isinstance(message, dict) else None
        items = [{"type": "text", "text": content}] if isinstance(content, str) else content
        if not isinstance(items, list):
            return
        texts = []
        for item in items:
            if not isinstance(item, dict):
                continue
            if item.get("type") == "tool_result":
                tool_result(rec, item)
            elif item.get("type") == "text" and isinstance(item.get("text"), str):
                texts.append(item["text"])
            elif item.get("type") == "image":
                texts.append("[image]")
        if not texts:
            return
        joined = "\n".join(texts)
        if rec.get("isMeta"):
            # A skill's body is loaded as a meta message; nothing else meta is
            # something a person said or did.
            first = joined.strip().split("\n", 1)[0]
            if first.startswith("Base directory for this skill:"):
                name = os.path.basename(first.split(":", 1)[1].strip().rstrip("/"))
                add("skill", rec, text=name)
            return
        human(rec, joined)

    def on_assistant(rec):
        message = rec.get("message")
        if not isinstance(message, dict):
            return
        key = message.get("id") or rec.get("uuid")
        model = message.get("model")
        synthetic = model == "<synthetic>" or bool(rec.get("isApiErrorMessage"))
        if model and model != "<synthetic>" and model not in session.models:
            session.models.append(model)
        content = message.get("content")
        if isinstance(content, str):
            content = [{"type": "text", "text": content}]
        if not isinstance(content, list):
            return
        for block in content:
            if not isinstance(block, dict):
                continue
            kind = block.get("type")
            if kind == "text":
                text = block.get("text")
                if not isinstance(text, str) or not text.strip():
                    continue
                mark = (key, "text", text)
                if mark in shown:
                    continue
                shown.add(mark)
                if synthetic:
                    session.api_errors += 1
                    add("apierror", rec, text=clip(redact(one_line(text)), RESULT_ERROR_MAX))
                else:
                    add("assistant", rec, text=clip(redact(text.strip()), ASSISTANT_TEXT_MAX))
            elif kind == "thinking":
                text = block.get("thinking")
                if not isinstance(text, str) or not text.strip():
                    continue  # the thinking is not kept in the file, only a signature
                mark = (key, "think", text)
                if mark in shown:
                    continue
                shown.add(mark)
                add("think", rec, text=clip(redact(text.strip()), THINK_MAX))
            elif kind == "tool_use":
                call_id = block.get("id")
                if call_id is not None and call_id in calls:
                    continue
                state["tool_n"] += 1
                session.tool_calls += 1
                name = str(block.get("name") or "?")
                payload = walk_strings(block.get("input"), BRIEF_MAX if name in BRIEF_TOOLS else INPUT_STRING_MAX)
                text = redact(json.dumps(payload, ensure_ascii=False))
                event = add(
                    "tool", rec, name=name, n=state["tool_n"], text=text
                )
                if call_id is not None:
                    calls[call_id] = event

    for raw in open(path, encoding="utf-8", errors="replace"):
        raw = raw.strip()
        if not raw:
            continue
        try:
            rec = json.loads(raw)
        except ValueError:
            continue  # a live file can end in half a line
        if not isinstance(rec, dict):
            continue
        kind = rec.get("type")
        if kind == "ai-title":
            session.ai_title = clip(redact(str(rec.get("aiTitle") or "")), TITLE_MAX)
        elif kind == "agent-name":
            session.agent_name = clip(redact(str(rec.get("agentName") or "")), TITLE_MAX)
        elif kind == "last-prompt":
            session.last_prompt = clip(redact(str(rec.get("lastPrompt") or "")), TITLE_MAX)
        if kind not in ("user", "assistant", "attachment", "system"):
            continue  # bookkeeping, and any record type this script has not met
        uuid = rec.get("uuid")
        if uuid:
            if uuid in seen:
                session.skipped_seen += 1
                continue
            seen.add(uuid)
        # Session-wide facts ride on every conversation record.
        if rec.get("cwd") and not session.cwd:
            session.cwd = str(rec["cwd"])
        if rec.get("entrypoint") and not session.entrypoint:
            session.entrypoint = str(rec["entrypoint"])
        if rec.get("version"):
            session.version = str(rec["version"])
        branch = rec.get("gitBranch")
        if branch and branch not in session.branches:
            session.branches.append(str(branch))
        when = parse_time(rec.get("timestamp"))
        if when:
            if session.first is None or when < session.first:
                session.first = when
            if session.last is None or when > session.last:
                session.last = when
        if kind == "user":
            on_user(rec)
        elif kind == "assistant":
            on_assistant(rec)
        elif kind == "attachment":
            attachment = rec.get("attachment")
            if isinstance(attachment, dict) and attachment.get("type") == "queued_command":
                # A prompt typed while the model was working. Only a human's
                # counts; the rest is peers and background-task notices.
                origin = attachment.get("origin")
                if isinstance(origin, dict) and origin.get("kind") == "human":
                    prompt = attachment.get("prompt")
                    if isinstance(prompt, list):
                        prompt = result_text(prompt)
                    if isinstance(prompt, str):
                        human(rec, prompt)
        elif kind == "system" and rec.get("subtype") == "compact_boundary":
            meta = rec.get("compactMetadata") if isinstance(rec.get("compactMetadata"), dict) else {}
            session.compactions += 1
            detail = str(meta.get("trigger") or "")
            if isinstance(meta.get("preTokens"), int):
                detail = (detail + ", %dk tokens before" % (meta["preTokens"] // 1000)).lstrip(", ")
            add("compact", rec, text=detail)
    return session


# --- writing the text ------------------------------------------------------


def clock(when) -> str:
    return when.strftime("%H:%M") if when else "--:--"


def body_lines(session: Session, subagents: bool, indent: str = "", start_day=None, depth: int = 0):
    """The condensed lines of a session, without the header."""
    lines = []
    day = start_day
    last_time = None
    for event in session.events:
        when = event["time"] or last_time
        last_time = when
        if when and when.date() != day:
            day = when.date()
            lines.append("--- %s ---" % day.isoformat())
        stamp = "[%s] " % clock(when)
        kind = event["kind"]
        text = event.get("text", "")
        if kind in ("user", "assistant", "think", "brief"):
            label = {"user": "USER", "assistant": "ASSISTANT", "think": "THINK", "brief": "BRIEF"}[kind]
            lines.append(stamp + label + ": " + text.replace("\n", "\n  "))
        elif kind == "cmd":
            lines.append(stamp + text)
        elif kind == "skill":
            lines.append(stamp + "[skill %s loaded]" % text)
        elif kind == "interrupt":
            lines.append(stamp + "INTERRUPTED" + (" (%s)" % text if text else ""))
        elif kind == "compact":
            lines.append(stamp + "COMPACTED" + (" (%s)" % text if text else ""))
        elif kind == "apierror":
            lines.append(stamp + "API ERROR: " + text)
        elif kind == "tool":
            lines.append(stamp + "TOOL %s#%d: %s" % (event["name"], event["n"], text))
            lines.extend(result_lines(event.get("result")))
            if subagents and event.get("agent") and depth == 0:
                lines.extend(subagent_lines(session, event["agent"], day))
        elif kind == "orphan":
            lines.extend(result_lines(event["result"], "  -> (call not in this file) "))
    return [indent + line.replace("\n", "\n" + indent) for line in lines] if indent else lines


def result_lines(result, prefix: str = "  -> "):
    if result is None:
        return ["  -> (no result recorded)"]
    label = result["label"]
    text = result["text"]
    if label.startswith("ok"):
        return [prefix + "%s (%s)%s" % (label, size_label(result["size"]), ": " + text if text else "")]
    return [prefix + label + (": " + text if text else "")]


def subagent_lines(session: Session, agent_id: str, day):
    """A subagent's condensed body, found next to the session file."""
    root = os.path.join(os.path.dirname(session.path), session.id, "subagents")
    path = os.path.join(root, "agent-%s.jsonl" % agent_id)
    if not os.path.isfile(path):
        return ["    (subagent %s: transcript not found)" % agent_id]
    sub = parse(path, set(), subagent=True)
    out = ["    === subagent %s (%d tool calls) ===" % (agent_id, sub.tool_calls)]
    out.extend(body_lines(sub, False, indent="    ", start_day=day, depth=1))
    out.append("    === end subagent %s ===" % agent_id)
    return out


def header_lines(session: Session):
    span = ""
    if session.first and session.last:
        span = "%s - %s (UTC%s)" % (
            session.first.strftime("%Y-%m-%d %H:%M"),
            session.last.strftime("%Y-%m-%d %H:%M") if session.last.date() != session.first.date() else session.last.strftime("%H:%M"),
            session.first.strftime("%z"),
        )
    lines = [
        "# session %s%s" % (session.id, " (subagent)" if session.subagent else ""),
        "title: %s" % (session.title or "(none)"),
        "project: %s" % (session.cwd or "(unknown)"),
        "branch: %s" % (", ".join(session.branches[:3]) or "(none)"),
        "span: %s" % (span or "(unknown)"),
        "models: %s" % (", ".join(session.models) or "(none)"),
        "entrypoint: %s%s" % (session.entrypoint or "?", " (Claude Code %s)" % session.version if session.version else ""),
        "counts: %d prompts, %d tool calls, %d errors (%d denied), %d interrupts, %d compactions, %d api errors"
        % (session.prompts, session.tool_calls, session.errors, session.denials, session.interrupts, session.compactions, session.api_errors),
    ]
    if session.skipped_seen:
        lines.append("note: %d records were already shown earlier in this run (a continued session copies its history) and are left out" % session.skipped_seen)
    lines.append("cite a line as %s@HH:MM" % session.id)
    return lines


def render(session: Session, subagents: bool = False) -> str:
    start = session.first.date() if session.first else None
    lines = header_lines(session) + [""] + body_lines(session, subagents, start_day=start)
    # One last pass over everything written, in case a rule above missed a path.
    return redact("\n".join(lines)) + "\n"


# --- finding transcripts ---------------------------------------------------


def projects_dir(given):
    if given:
        return os.path.expanduser(given)
    base = os.environ.get("CLAUDE_CONFIG_DIR")
    return os.path.join(os.path.expanduser(base) if base else os.path.expanduser("~/.claude"), "projects")


def encode_path(path: str) -> str:
    """Claude Code names a project folder after the working directory, with
    every character that is not a letter or digit written as a dash."""
    path = os.path.abspath(os.path.expanduser(path)).rstrip("/")
    return re.sub(r"[^A-Za-z0-9]", "-", path)


def session_files(root: str, prefixes):
    """(project folder, path) of every main session file; subagent files are
    one folder deeper and are not listed. `prefixes` None means every project."""
    try:
        folders = sorted(os.listdir(root))
    except OSError:
        return []
    found = []
    for folder in folders:
        if prefixes is not None and not any(folder.startswith(p) for p in prefixes):
            continue
        full = os.path.join(root, folder)
        if not os.path.isdir(full):
            continue
        for name in os.listdir(full):
            if name.endswith(".jsonl") and os.path.isfile(os.path.join(full, name)):
                found.append((folder, os.path.join(full, name)))
    return found


def parse_since(value: str):
    """'30d' or 'YYYY-MM-DD' as an aware local datetime."""
    match = re.fullmatch(r"(\d+)d", value)
    if match:
        return datetime.datetime.now().astimezone() - datetime.timedelta(days=int(match.group(1)))
    try:
        return datetime.datetime.strptime(value, "%Y-%m-%d").astimezone()
    except ValueError:
        raise SystemExit("--since takes 30d or YYYY-MM-DD, not %r" % value)


def parse_until(value: str):
    try:
        day = datetime.datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise SystemExit("--until takes YYYY-MM-DD, not %r" % value)
    return (day + datetime.timedelta(days=1)).astimezone()  # the whole day counts


def find_session(root: str, ref: str) -> str:
    if ref.endswith(".jsonl") or os.path.sep in ref:
        path = os.path.expanduser(ref)
        if not os.path.isfile(path):
            raise SystemExit("no such file: %s" % ref)
        return path
    hits = [p for _, p in session_files(root, None) if os.path.basename(p) == ref + ".jsonl"]
    if not hits:
        hits = [p for _, p in session_files(root, None) if os.path.basename(p).startswith(ref) and len(ref) >= 8]
    if not hits:
        raise SystemExit("no session %s under %s" % (ref, root))
    if len(hits) > 1:
        raise SystemExit("%s matches %d sessions; give more of the id" % (ref, len(hits)))
    return hits[0]


# --- commands --------------------------------------------------------------


def cmd_list(args) -> int:
    root = projects_dir(args.projects_dir)
    if args.all:
        prefixes = None
    elif args.project:
        prefixes = [encode_path(p) for p in args.project]
    else:
        prefixes = [encode_path(os.getcwd())]
    since = parse_since(args.since) if args.since else None
    until = parse_until(args.until) if args.until else None
    needle = args.grep.lower() if args.grep else None
    excluded = set(args.exclude or [])
    rows = []
    dropped = {"headless": 0, "quiet": 0}
    for _, path in session_files(root, prefixes):
        session_id = os.path.basename(path)[: -len(".jsonl")]
        if session_id in excluded:
            continue
        if since and datetime.datetime.fromtimestamp(os.path.getmtime(path)).astimezone() < since:
            continue  # the last record cannot be later than the file was written
        session = parse(path, set())
        if session.last is None:
            continue
        if (since and session.last < since) or (until and session.last >= until):
            continue
        if session.headless and not args.include_headless:
            dropped["headless"] += 1
            continue
        if session.prompts < args.min_prompts or session.tool_calls < args.min_tool_calls:
            dropped["quiet"] += 1
            continue
        if needle and needle not in " ".join([session.title] + session.human_texts).lower():
            continue
        tokens = len(render(session)) // CHARS_PER_TOKEN
        rows.append(
            {
                "id": session.id,
                "date": session.last.strftime("%Y-%m-%d"),
                "last": session.last.isoformat(),
                "project": session.cwd,
                "entrypoint": session.entrypoint,
                "prompts": session.prompts,
                "tool_calls": session.tool_calls,
                "errors": session.errors,
                "tokens": tokens,
                "title": session.title,
                "path": path,
            }
        )
    rows.sort(key=lambda r: r["last"], reverse=True)
    total = sum(r["tokens"] for r in rows)
    if args.json:
        json.dump(rows, sys.stdout, ensure_ascii=False, indent=1)
        sys.stdout.write("\n")
        return 0
    for r in rows:
        print("\t".join([r["id"], r["date"], r["project"], r["entrypoint"], str(r["prompts"]), str(r["tool_calls"]), str(r["errors"]), str(r["tokens"]), r["title"]]))
    print(
        "TOTAL\t%d sessions\t~%d tokens condensed\t(left out: %d headless, %d under the activity floor)"
        % (len(rows), total, dropped["headless"], dropped["quiet"])
    )
    return 0


def cmd_condense(args) -> int:
    root = projects_dir(args.projects_dir)
    paths = [find_session(root, ref) for ref in args.sessions]
    if args.out == "-":
        if len(paths) != 1:
            raise SystemExit("--out - takes exactly one session")
        sys.stdout.write(render(parse(paths[0], set()), args.subagents))
        return 0
    out = args.out or tempfile.mkdtemp(prefix="condensed-")
    os.makedirs(out, exist_ok=True)
    seen = set()  # a continued session repeats its parent's records; show each once
    for path in paths:
        session = parse(path, seen)
        target = os.path.join(out, session.id + ".txt")
        with open(target, "w", encoding="utf-8") as handle:
            handle.write(render(session, args.subagents))
        print("%s\t%s" % (target, size_label(os.path.getsize(target))))
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="List and condense Claude Code session transcripts.")
    sub = parser.add_subparsers(dest="command", required=True)

    lister = sub.add_parser("list", help="one line per session, newest first")
    lister.add_argument("--projects-dir", help="default: $CLAUDE_CONFIG_DIR/projects, else ~/.claude/projects")
    lister.add_argument("--project", action="append", metavar="PATH", help="a working directory; matches every project folder whose name starts with its encoding (repeatable)")
    lister.add_argument("--all", action="store_true", help="every project")
    lister.add_argument("--since", help="30d, or YYYY-MM-DD")
    lister.add_argument("--until", help="YYYY-MM-DD, inclusive")
    lister.add_argument("--min-prompts", type=int, default=1)
    lister.add_argument("--min-tool-calls", type=int, default=10)
    lister.add_argument("--include-headless", action="store_true", help="also sessions run by a script or the SDK")
    lister.add_argument("--exclude", nargs="+", metavar="SESSION_ID", help="sessions to leave out, such as the one running this")
    lister.add_argument("--grep", help="keep sessions whose title or prompts contain this text, ignoring case")
    lister.add_argument("--json", action="store_true")
    lister.set_defaults(run=cmd_list)

    condenser = sub.add_parser("condense", help="write one text file per session")
    condenser.add_argument("sessions", nargs="+", metavar="SESSION", help="a session id, or the path of a .jsonl file")
    condenser.add_argument("--projects-dir", help="where ids are looked up")
    condenser.add_argument("--out", help="directory for the files (default: a new temp directory); '-' prints one session")
    condenser.add_argument("--subagents", action="store_true", help="append the transcript of each subagent a session started")
    condenser.set_defaults(run=cmd_condense)

    args = parser.parse_args(argv)
    return args.run(args)


if __name__ == "__main__":
    sys.exit(main())
