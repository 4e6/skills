"""Tests for the session-review condenser, on a transcript built here.

    python3 -m unittest discover -s evals/session-review

The condenser reads a file format that Claude Code does not document and
changes between versions, so its rules are only as good as the records they were
written from. These tests write a small transcript of those records, one for
each rule, and check what comes out. The records are the shapes seen in real
transcripts (Claude Code 2.1.236 to 2.1.296), cut to the fields the condenser
reads.

Nothing secret-shaped is written in this file. The strings the redaction tests
need are put together at run time, so a secret scanner has nothing to find.

The tests live here, outside the skill, because anything inside a skill's folder
ships with it.
"""

import datetime
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(
    HERE, "..", "..", "plugins", "session-review", "skills", "session-review", "scripts", "condense.py"
)

_spec = importlib.util.spec_from_file_location("condense", SCRIPT)
condense = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(condense)

SESSION = "aaaaaaaa-0000-4000-8000-000000000001"
CWD = "/Users/me/work/app"
FOLDER = "-Users-me-work-app"


def secrets():
    """One secret of each shape, built so that no whole one is in this file."""
    return {
        "openai": "s" + "k-" + "A1b2C3d4" * 4,
        "github": "gh" + "p_" + "A1b2C3d4E5" * 4,
        "github fine-grained": "github" + "_pat_" + "A1b2C3d4E5" * 3,
        "aws": "AK" + "IA" + "ABCDEFGH12345678",
        "google": "AI" + "za" + "A1b2C3d4E5" * 3 + "A1b2C",
        "slack": "xo" + "xb-" + "1234567890-" + "abcdefghij",
        "gitlab": "gl" + "pat-" + "A1b2C3d4E5" * 2,
        "npm": "np" + "m_" + "A1b2C3d4E5" * 4,
        "jwt": "ey" + "J" + "hbGciOi" * 2 + "." + "ey" + "J" + "zdWIiOi" * 2 + "." + "c2lnbmF0dXJl",
        "bearer": "Bea" + "rer " + "abcdefghijklmnopqrstuv",
        "url": "https://" + "alice" + ":" + "hunter2hunter2" + "@example.com/repo.git",
        "assignment": "pass" + "word" + "=" + "correcthorsebattery",
        "json assignment": '"api' + '_key": "' + "zyxwvutsrqponm" + '"',
        "pem": "-----BEGIN RSA PRIV" + "ATE KEY-----\nMIIBOgIBAAJBAKj34GkxFhD90vcNLYLInFEX6Ppy1tPf9Cnzj4p4WGeKLs1Pt8Qu\n-----END RSA PRIV" + "ATE KEY-----",
    }


def risky():
    """Secrets in the shapes a first pass missed, with what must not survive."""
    key = "api" + "_key"
    word = "pass" + "word"
    return {
        "escaped json": ('{\\"' + key + '\\": \\"zyxwvutsrqponm\\"}', "zyxwvutsrqponm"),
        "flag with a space": ("deploy --" + word + " hunter2hunter2 --now", "hunter2hunter2"),
        "docker login": ("docker login -u me -p hunter2hunter2 registry.example.com", "hunter2hunter2"),
        "curl user": ("curl -u alice:hunter2hunter2 https://example.com", "hunter2hunter2"),
        "authorization token": ('-H "Authorization: tok' + 'en ghx1234567890"', "ghx1234567890"),
        "pass phrase": (word + ": correct horse battery staple", "horse battery"),
        "quoted pass phrase": (word + '="correct horse battery"', "horse battery"),
        "digits": ("sec" + "ret_key=1234567890123", "1234567890123"),
        "pem cut off": ("-----BEGIN PRIV" + "ATE KEY-----\nMIIBOgIBAAJBAKj34GkxFhD90vcNLYLI", "MIIBOgIBAAJBAKj34GkxFhD90vcNLYLI"),
    }


class Transcript:
    """Writes records the way Claude Code does: one JSON object per line."""

    def __init__(self, path, session=SESSION, cwd=CWD, entrypoint="cli", sidechain=False):
        self.path = path
        self.session = session
        self.cwd = cwd
        self.entrypoint = entrypoint
        self.sidechain = sidechain
        self.n = 0
        self.lines = []
        self.clock = datetime.datetime(2026, 10, 6, 10, 0, tzinfo=datetime.timezone.utc)

    def stamp(self, minutes):
        self.clock += datetime.timedelta(minutes=minutes)
        return self.clock.strftime("%Y-%m-%dT%H:%M:%S.000Z")

    def raw(self, line):
        self.lines.append(line)

    def add(self, rec, minutes=1, uuid=True, **extra):
        self.n += 1
        base = {
            "isSidechain": self.sidechain,
            "timestamp": self.stamp(minutes),
            "sessionId": self.session,
            "cwd": self.cwd,
            "entrypoint": self.entrypoint,
            "version": "2.1.291",
            "gitBranch": "main",
        }
        if uuid is True:
            base["uuid"] = "%s-u%03d" % (self.session[:8], self.n)
        elif uuid:
            base["uuid"] = uuid
        base.update(rec)
        base.update(extra)
        self.lines.append(json.dumps(base))
        return base

    def user(self, content, **extra):
        return self.add({"type": "user", "message": {"role": "user", "content": content}}, **extra)

    def meta(self, content, **extra):
        return self.user(content, isMeta=True, **extra)

    def queued(self, prompt, kind=None, **extra):
        attachment = {"type": "queued_command", "prompt": prompt}
        if kind:
            attachment["origin"] = {"kind": kind}
        return self.add({"type": "attachment", "attachment": attachment}, **extra)

    def assistant(self, blocks, message_id, model="claude-sonnet-5-5", **extra):
        message = {"id": message_id, "role": "assistant", "model": model, "content": blocks}
        return self.add({"type": "assistant", "message": message}, **extra)

    def call(self, message_id, call_id, name, tool_input, **extra):
        block = {"type": "tool_use", "id": call_id, "name": name, "input": tool_input}
        return self.assistant([block], message_id, **extra)

    def result(self, call_id, content, error=False, **extra):
        item = {"type": "tool_result", "tool_use_id": call_id, "content": content}
        if error:
            item["is_error"] = True
        return self.user([item], **extra)

    def write(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as handle:
            handle.write("\n".join(self.lines) + "\n")


def build_main(path, subagent_id="sub1"):
    """The session that carries every rule once."""
    t = Transcript(path)
    t.add({"type": "ai-title", "aiTitle": "First title"}, uuid=False)
    t.add({"type": "agent-name", "agentName": "Agent name"}, uuid=False)
    t.add({"type": "last-prompt", "lastPrompt": "Last prompt"}, uuid=False)
    t.add({"type": "mode", "mode": "normal"}, uuid=False)  # bookkeeping

    # Human prompts: a string, a list of text items, and one typed mid-turn.
    prompt = t.user("Fix the build please")
    t.user([{"type": "text", "text": "Second prompt in a list"}])
    t.queued("Also check the lint", kind="human")
    t.queued("<agent-message from=\"x\">PEER MESSAGE</agent-message>", kind="peer")
    t.queued("<task-notification>TASK NOTICE</task-notification>")
    t.user("<command-name>/review</command-name>\n<command-message>review</command-message>\n<command-args>12</command-args>")

    # Meta messages: a skill body is a marker, a reminder is nothing.
    t.meta("Base directory for this skill: /Users/me/.claude/skills/my-skill\n\n# SKILL BODY TEXT")
    t.meta("<system-reminder>META REMINDER</system-reminder>")
    t.add({"type": "attachment", "attachment": {"type": "total_tokens_reminder", "text": "TOKENS LEFT"}})

    # One assistant message in three records, a result between, a block repeated.
    t.assistant([{"type": "thinking", "thinking": "", "signature": "SIGNATURE"}], "msg_1")
    t.assistant([{"type": "text", "text": "Looking at the build now."}], "msg_1")
    t.assistant([{"type": "text", "text": "Looking at the build now."}], "msg_1")  # same block, new uuid
    t.call("msg_1", "t1", "Read", {"file_path": "/work/app/build.sh"})
    t.call("msg_1", "t2", "Bash", {"command": "ls", "description": "list"})
    t.result("t2", "file-a\nfile-b")  # results arrive in the other order
    t.result("t1", "x" * 2000)
    t.assistant([{"type": "thinking", "thinking": "Considering two options.", "signature": "S"}], "msg_2")

    # A permission rule denies a write; the person refuses an edit and says why.
    t.call("msg_2", "t3", "Write", {"file_path": "/work/app/a.txt", "content": "c"})
    t.result("t3", "Permission to use Write has been denied.", error=True, toolDenialKind="permission-rule")
    t.call("msg_3", "t4", "Edit", {"file_path": "/work/app/b.txt", "old_string": "a", "new_string": "b"})
    t.result(
        "t4",
        "The user doesn't want to proceed with this tool use. BOILERPLATE",
        error=True,
        toolDenialKind="user-rejected",
        userFeedback="use tabs, not spaces",
    )
    t.user([{"type": "text", "text": "[Request interrupted by user for tool use]"}])

    # Large output, an image, a failure with no denial.
    t.call("msg_4", "t5", "Bash", {"command": "cat big"})
    t.result("t5", "<persisted-output>\nOutput too large (78.9KB). Full output saved to: /x\n\nPreview (first 2KB):\nthe preview head\n</persisted-output>")
    t.call("msg_4", "t6", "mcp__browser__screenshot", {})
    t.result("t6", [{"type": "image", "source": {}}, {"type": "text", "text": "captured"}])
    t.call("msg_4", "t7", "Bash", {"command": "false"})
    t.result("t7", "exit 1: it broke", error=True)

    # Compaction: the boundary stays, the summary goes.
    t.add(
        {
            "type": "system",
            "subtype": "compact_boundary",
            "content": "Conversation compacted",
            "compactMetadata": {"trigger": "manual", "preTokens": 250131},
        }
    )
    t.user("SUMMARY MARKER this session is being continued", isCompactSummary=True)

    # The API gave up.
    t.assistant(
        [{"type": "text", "text": "API Error: 529 overloaded"}], "msg_5", model="<synthetic>", isApiErrorMessage=True
    )

    # A subagent, found through the id its result reports.
    t.call("msg_6", "t8", "Agent", {"description": "Look around", "subagent_type": "Explore", "prompt": "Find the build script"})
    t.result("t8", "Found it.", toolUseResult={"agentId": subagent_id, "status": "completed"})

    # Secrets in a tool input, in a result, in assistant text, and in a prompt.
    for i, (name, value) in enumerate(sorted(secrets().items())):
        t.call("msg_s%d" % i, "s%d" % i, "Bash", {"command": "echo " + value})
        t.result("s%d" % i, "output " + value)
        t.assistant([{"type": "text", "text": "I saw " + value + " in the log"}], "msg_s%d" % i)
        t.user("my %s is %s" % (name, value))

    # Damaged input: a repeat of an earlier record, a record type from the
    # future, and a last line cut off mid-write.
    t.lines.append(t.lines[4])  # the first prompt again, same uuid
    t.raw(json.dumps({"type": "future-thing", "uuid": "zzz", "payload": {"deep": [1, 2]}}))
    t.raw('{"type": "user", "message": {"role": "user", "content": "TRUNCA')
    t.write()
    return prompt


def build_subagent(path, session_id, agent_id):
    t = Transcript(path, session=session_id, sidechain=True)
    t.user("Find the build script in the repo")
    t.call("sub_msg_1", "u1", "Glob", {"pattern": "**/build*"})
    t.result("u1", "build.sh")
    t.assistant([{"type": "text", "text": "SUBAGENT ANSWER build.sh"}], "sub_msg_2")
    t.write()


def build_simple(path, session, title_records, prompt="Do the thing", calls=12, entrypoint="cli", cwd=CWD, days_ago=2):
    """A session with `calls` tool calls, last written `days_ago` days ago."""
    t = Transcript(path, session=session, cwd=cwd, entrypoint=entrypoint)
    now = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days_ago, hours=1)
    t.clock = now
    for rec in title_records:
        t.add(rec, uuid=False)
    t.user(prompt)
    for i in range(calls):
        t.call("m%d" % i, "c%d" % i, "Bash", {"command": "true"})
        t.result("c%d" % i, "ok")
    t.write()
    when = (now + datetime.timedelta(minutes=calls * 2)).timestamp()
    os.utime(path, (when, when))


def run(*args, cwd=None, expect=0):
    env = dict(os.environ, TZ="UTC")
    env.pop("CLAUDE_CONFIG_DIR", None)
    done = subprocess.run(
        [sys.executable, "-I", SCRIPT] + list(args), capture_output=True, text=True, env=env, cwd=cwd
    )
    assert done.returncode == expect, "exit %s: %s" % (done.returncode, done.stderr)
    return done.stdout


class CondenseTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="condense-test-")
        self.addCleanup(shutil.rmtree, self.root, True)
        self.projects = os.path.join(self.root, "projects")
        self.main = os.path.join(self.projects, FOLDER, SESSION + ".jsonl")
        build_main(self.main)
        build_subagent(
            os.path.join(self.projects, FOLDER, SESSION, "subagents", "agent-sub1.jsonl"), SESSION, "sub1"
        )
        self.text = self.condense()

    def condense(self, *extra):
        out = os.path.join(self.root, "out%d" % len(os.listdir(self.root)))
        run("condense", SESSION, "--projects-dir", self.projects, "--out", out, *extra)
        with open(os.path.join(out, SESSION + ".txt"), encoding="utf-8") as handle:
            return handle.read()

    def lines(self):
        return self.text.split("\n")

    def has(self, line):
        self.assertIn(line, self.lines())

    def test_header(self):
        self.assertIn("# session " + SESSION, self.text)
        self.assertIn("project: " + CWD, self.text)
        self.assertIn("branch: main", self.text)
        self.assertIn("models: claude-sonnet-5-5", self.text)
        self.assertIn("2026-10-06 10:05", self.text)

    def test_human_prompts_in_both_shapes(self):
        self.has("[10:05] USER: Fix the build please")
        self.assertIn("] USER: Second prompt in a list", self.text)

    def test_queued_prompt_from_a_human_is_kept_and_peers_are_dropped(self):
        self.assertIn("] USER: Also check the lint", self.text)
        self.assertNotIn("PEER MESSAGE", self.text)
        self.assertNotIn("TASK NOTICE", self.text)

    def test_slash_command(self):
        self.assertIn("] /review 12", self.text)

    def test_skill_body_becomes_a_marker(self):
        self.assertIn("] [skill my-skill loaded]", self.text)
        self.assertNotIn("SKILL BODY TEXT", self.text)

    def test_reminders_and_bookkeeping_are_dropped(self):
        self.assertNotIn("META REMINDER", self.text)
        self.assertNotIn("TOKENS LEFT", self.text)

    def test_a_message_split_across_records_is_written_once(self):
        self.assertEqual(self.text.count("Looking at the build now."), 1)

    def test_empty_thinking_is_dropped_and_real_thinking_kept(self):
        self.assertNotIn("SIGNATURE", self.text)
        self.assertEqual(self.text.count("THINK:"), 1)
        self.assertIn("THINK: Considering two options.", self.text)

    def test_results_pair_with_their_calls_in_any_order(self):
        lines = self.lines()
        read = next(i for i, l in enumerate(lines) if "TOOL Read#1:" in l)
        bash = next(i for i, l in enumerate(lines) if "TOOL Bash#2:" in l)
        self.assertTrue(lines[read + 1].startswith("  -> ok (2.0KB): xxx"))
        self.assertIn("[+1700 chars]", lines[read + 1])  # cut to 300
        self.assertEqual(lines[bash + 1], "  -> ok (13B): file-a ⏎ file-b")

    def test_denied_by_a_rule(self):
        self.assertIn("  -> ERROR(permission-rule): Permission to use Write has been denied.", self.text)

    def test_refusal_keeps_the_feedback_and_not_the_boilerplate(self):
        self.assertIn("  -> REJECTED: use tabs, not spaces", self.text)
        self.assertNotIn("BOILERPLATE", self.text)

    def test_plain_error(self):
        self.assertIn("  -> ERROR: exit 1: it broke", self.text)

    def test_interrupt(self):
        self.assertIn("] INTERRUPTED (for tool use)", self.text)

    def test_compaction_marked_and_summary_dropped(self):
        self.assertIn("] COMPACTED (manual, 250k tokens before)", self.text)
        self.assertNotIn("SUMMARY MARKER", self.text)

    def test_persisted_output_and_image(self):
        self.assertIn("  -> ok [persisted 78.9KB] (", self.text)
        self.assertIn("the preview head", self.text)
        self.assertIn("[image] ⏎ captured", self.text)

    def test_api_error(self):
        self.assertIn("] API ERROR: API Error: 529 overloaded", self.text)

    def test_counts(self):
        # 4 prompts above the secrets + one per secret shape; calls counted once each.
        shapes = len(secrets())
        self.assertIn("%d prompts" % (4 + shapes), self.text)
        self.assertIn("%d tool calls" % (8 + shapes), self.text)
        self.assertIn("3 errors (2 denied)", self.text)
        self.assertIn("1 interrupts, 1 compactions, 1 api errors", self.text)

    def test_every_secret_shape_is_redacted_everywhere(self):
        for name, value in secrets().items():
            # The distinctive middle of each, as a whole secret is also checked.
            for piece in (value, value.split("\n")[1] if "\n" in value else value[8:-4]):
                self.assertNotIn(piece, self.text, name)
        self.assertGreaterEqual(self.text.count("[REDACTED]"), len(secrets()) * 4)

    def test_redact_alone_catches_the_shapes_a_first_pass_missed(self):
        for name, (text, secret) in risky().items():
            out = condense.redact(text)
            self.assertNotIn(secret, out, name)
            self.assertIn("[REDACTED]", out, name)
            self.assertEqual(condense.redact(out), out, name)  # idempotent

    def test_redact_alone_covers_every_shape(self):
        for name, value in secrets().items():
            self.assertNotIn(value.split("\n")[-2] if "\n" in value else value[8:-4], condense.redact("x " + value + " y"), name)

    def test_ordinary_text_is_left_alone(self):
        for text in (
            '"max_tokens": 4096',
            "max_tokens: 123456789",
            '"total_tokens": 12345678',
            "--max-tokens 4096",
            "docker login --pass" + "word-stdin registry.example.com",
            "the header -----BEGIN PRIV" + "ATE KEY----- is shown, then prose",
            "pass" + "word: $SECRET_VALUE and more words",
            "Authorization: required for this endpoint",
        ):
            self.assertEqual(condense.redact(text), text)

    def test_a_non_string_id_does_not_crash(self):
        t = Transcript(os.path.join(self.projects, "-odd", "odd.jsonl"), session="odd")
        t.user("hello")
        t.assistant([{"type": "tool_use", "id": ["x"], "name": "Bash", "input": {}}], ["m"], uuid=["u"])
        t.add({"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": {"a": 1}, "content": "r"}]}}, uuid={"b": 1})
        t.write()
        out = run("condense", t.path, "--out", "-")
        self.assertIn("TOOL Bash#1", out)
        self.assertIn("(call not in this file)", out)

    def test_every_line_has_a_day(self):
        lines = self.lines()
        first = next(i for i, l in enumerate(lines) if l.startswith("["))
        self.assertEqual(lines[first - 1], "--- 2026-10-06 ---")
        self.assertIn("cite a line as %s@YYYY-MM-DD HH:MM" % SESSION, self.text)

    def test_a_duplicate_uuid_is_written_once(self):
        self.assertEqual(self.text.count("Fix the build please"), 1)

    def test_a_cut_off_last_line_and_an_unknown_type_are_skipped(self):
        self.assertNotIn("TRUNCA", self.text)
        self.assertNotIn("future-thing", self.text)

    def test_subagent_only_on_request(self):
        self.assertNotIn("SUBAGENT ANSWER", self.text)
        self.assertIn("TOOL Agent#", self.text)
        with_sub = self.condense("--subagents")
        self.assertIn("=== subagent sub1", with_sub)
        self.assertIn("SUBAGENT ANSWER build.sh", with_sub)
        self.assertIn("] BRIEF: Find the build script in the repo", with_sub)

    def test_title_precedence(self):
        def title_of(records):
            path = os.path.join(self.projects, "-t", "t.jsonl")
            build_simple(path, "t", records, prompt="First words of the prompt")
            out = run("condense", path, "--out", "-")
            return next(l for l in out.split("\n") if l.startswith("title: "))[len("title: "):]

        ai = {"type": "ai-title", "aiTitle": "AI one"}
        self.assertEqual(title_of([ai, {"type": "ai-title", "aiTitle": "AI two"}]), "AI two")
        self.assertEqual(title_of([ai, {"type": "agent-name", "agentName": "Named"}]), "AI one")
        self.assertEqual(title_of([{"type": "agent-name", "agentName": "Named"}, {"type": "last-prompt", "lastPrompt": "LP"}]), "Named")
        self.assertEqual(title_of([{"type": "last-prompt", "lastPrompt": "LP"}]), "LP")
        self.assertEqual(title_of([]), "First words of the prompt")

    def test_a_continued_session_does_not_repeat_the_history_of_the_first(self):
        copy = os.path.join(self.projects, FOLDER, "bbbbbbbb-0000-4000-8000-000000000002.jsonl")
        shutil.copy(self.main, copy)
        out = os.path.join(self.root, "pair")
        run("condense", SESSION, "bbbbbbbb-0000-4000-8000-000000000002", "--projects-dir", self.projects, "--out", out)
        with open(os.path.join(out, "bbbbbbbb-0000-4000-8000-000000000002.txt"), encoding="utf-8") as handle:
            second = handle.read()
        self.assertNotIn("Looking at the build now.", second)
        self.assertIn("were already shown earlier in this run", second)

    def test_the_oldest_session_keeps_the_history_whatever_the_order_given(self):
        other = "bbbbbbbb-0000-4000-8000-000000000002"
        copy = os.path.join(self.projects, FOLDER, other + ".jsonl")
        shutil.copy(self.main, copy)
        later = os.path.getmtime(self.main) + 100
        os.utime(copy, (later, later))
        out = os.path.join(self.root, "reversed")
        run("condense", other, SESSION, "--projects-dir", self.projects, "--out", out)
        with open(os.path.join(out, SESSION + ".txt"), encoding="utf-8") as handle:
            self.assertIn("Looking at the build now.", handle.read())
        with open(os.path.join(out, other + ".txt"), encoding="utf-8") as handle:
            self.assertNotIn("Looking at the build now.", handle.read())


class ListTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="condense-list-")
        self.addCleanup(shutil.rmtree, self.root, True)
        self.projects = os.path.join(self.root, "projects")

        def make(folder, session, **kw):
            build_simple(os.path.join(self.projects, folder, session + ".jsonl"), session, [{"type": "ai-title", "aiTitle": session}], **kw)

        make(FOLDER, "active", prompt="Refactor the parser")
        make(FOLDER, "headless", entrypoint="sdk-cli")
        make(FOLDER, "quiet", calls=3)
        make(FOLDER, "old", days_ago=60, prompt="Ancient history")
        make(FOLDER + "2", "sibling", cwd=CWD + "2")
        make("-Users-me-other", "elsewhere", cwd="/Users/me/other")
        # A subagent file is not a session.
        build_subagent(os.path.join(self.projects, FOLDER, "active", "subagents", "agent-x.jsonl"), "active", "x")

    def ids(self, *args, cwd=None):
        out = run("list", "--projects-dir", self.projects, *args, cwd=cwd)
        return sorted(l.split("\t")[0] for l in out.split("\n") if l and not l.startswith("TOTAL"))

    def test_default_hides_headless_and_quiet_sessions(self):
        self.assertEqual(self.ids("--project", CWD), ["active", "old", "sibling"])

    def test_flags_bring_them_back(self):
        self.assertIn("headless", self.ids("--project", CWD, "--include-headless"))
        self.assertIn("quiet", self.ids("--project", CWD, "--min-tool-calls", "1"))

    def test_project_is_a_prefix_match_and_all_is_everything(self):
        self.assertEqual(self.ids("--project", "/Users/me/other"), ["elsewhere"])
        self.assertEqual(self.ids("--project", "/Users/me/work/app/"), ["active", "old", "sibling"])
        self.assertEqual(self.ids("--all"), ["active", "elsewhere", "old", "sibling"])

    def test_default_project_is_the_working_directory(self):
        work = os.path.realpath(os.path.join(self.root, "my work.dir"))
        os.makedirs(work)
        folder = "".join(c if c.isalnum() else "-" for c in work)
        build_simple(os.path.join(self.projects, folder, "here.jsonl"), "here", [], cwd=work)
        self.assertEqual(self.ids(cwd=work), ["here"])

    def test_exclude(self):
        self.assertEqual(self.ids("--project", CWD, "--exclude", "active", "sibling"), ["old"])

    def test_since_and_until(self):
        self.assertEqual(self.ids("--project", CWD, "--since", "30d"), ["active", "sibling"])
        recent = (datetime.date.today() - datetime.timedelta(days=10)).isoformat()
        self.assertEqual(self.ids("--project", CWD, "--since", recent), ["active", "sibling"])
        self.assertEqual(self.ids("--project", CWD, "--until", recent), ["old"])

    def test_grep_matches_prompts_and_titles_ignoring_case(self):
        self.assertEqual(self.ids("--project", CWD, "--grep", "REFACTOR"), ["active"])
        self.assertEqual(self.ids("--project", CWD, "--grep", "sibling"), ["sibling"])

    def test_a_secret_in_a_prompt_does_not_reach_the_listing(self):
        secret = "pass" + "word" + "=" + "correcthorsebattery"
        build_simple(os.path.join(self.projects, FOLDER, "leaky.jsonl"), "leaky", [], prompt="log in with " + secret)
        for args in (["--json"], []):
            out = run("list", "--projects-dir", self.projects, "--project", CWD, *args)
            self.assertNotIn("correcthorsebattery", out)
            self.assertIn("log in with", out)

    def test_line_and_json_shape(self):
        out = run("list", "--projects-dir", self.projects, "--project", "/Users/me/other")
        row, total = out.strip().split("\n")
        fields = row.split("\t")
        self.assertEqual(fields[0], "elsewhere")
        self.assertEqual(fields[2:7], ["/Users/me/other", "cli", "1", "12", "0"])
        self.assertTrue(fields[7].isdigit())
        self.assertEqual(fields[8], "elsewhere")
        self.assertTrue(total.startswith("TOTAL\t1 sessions"))
        data = json.loads(run("list", "--projects-dir", self.projects, "--all", "--json"))
        self.assertEqual(len(data), 4)
        self.assertEqual(data, sorted(data, key=lambda r: r["last"], reverse=True))
        self.assertEqual({r["id"] for r in data}, {"active", "elsewhere", "old", "sibling"})


if __name__ == "__main__":
    unittest.main()
