"""Agents a skill's evals run on, each driven headless from the command line.

An adapter does three things: puts a copy of a skill where its agent finds
skills, runs one athlete message in a folder (and resumes it once if asked),
and answers a judge's questions. The skills here are written for any agent, so
nothing else in the evals knows which agent ran.

**Each run sees the skill under test and as little of the machine as it can.**
Claude Code is started in a fresh folder outside any checkout, with only the
project's settings (so neither the user's skills, memory nor CLAUDE.md), no MCP
servers (a meal-plan server or a training calendar would answer the athlete
instead of the skill), and a fixed set of tools: no publishing, no web, no
menus, since nobody is there to pick from one. The file tools work only inside
the run's folder, and the shell runs in Claude Code's sandbox: it writes only
there, reads nothing in the home folder, never reaches the network, and in the
temporary folder every run shares touches no file it could have named itself.
Anything else is refused, not asked about, so a run never waits on a person and
never opens a browser on the machine running it. What it cannot avoid is
Claude Code keeping each run's session under `~/.claude/projects/`, which the
nudge needs to resume it.

Python 3.9, standard library only.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Turn:
    """What one headless invocation did."""

    reply: str
    is_error: bool
    finished: bool
    session_id: str | None
    cost_usd: float
    tools: list = field(default_factory=list)
    skills: list = field(default_factory=list)
    reads: list = field(default_factory=list)
    listed: list = field(default_factory=list)
    models: list = field(default_factory=list)
    api_error: object = None
    denied: list = field(default_factory=list)
    timed_out: bool = False


def _target(given: dict) -> str:
    """What a refused call was after: its path or its command, whole, since the
    `open` that explains a refusal is often the last thing in a long command."""
    return str(given.get("file_path") or given.get("path") or given.get("command") or "")


def _text(output) -> str:
    """What a timed-out process had printed, which arrives as bytes or nothing."""
    if output is None:
        return ""
    return output.decode("utf-8", "replace") if isinstance(output, bytes) else output


def _named_in_shared_tmp() -> list:
    """Every file with a dot in its name, at any depth of the sandbox's `$TMPDIR`.

    The sandbox gives every run's shell the same temporary folder,
    `/tmp/claude-<uid>`, whatever `TMPDIR` the command line is started with.
    Agents write their plan's generator there, `$TMPDIR/build.py`, and one run
    patched and ran another's, so its folder held a plan of Pune for an athlete
    in Osaka; any other session on the machine leaves its own files there too.
    Refusing the whole folder breaks the shell: zsh writes each heredoc there,
    and Claude Code a file after each command saying where it ended, both named
    with no dot (`zshAbC123`, `cwd-4d81`). An agent names its files with one
    (`build.py`, `parts.json`), so reading or writing those is refused and it
    works in its own folder. A name with no dot still gets through, which is
    why `run.py` also sets aside a run that shared a file with another.
    """
    folder = "/tmp/claude-%d" % os.getuid()
    spellings = sorted({folder, str(Path(folder).resolve())})
    return [path + "/**/*.*" for path in spellings]


class ClaudeCode:
    name = "claude-code"

    # The tools a host offers; Skill is how the skill is found, by its
    # description, as it would be in use.
    TOOLS = "Read,Write,Edit,Glob,Grep,Bash,Skill"
    # The file tools only inside the run's folder: bare `Read` or `Write` reach
    # anywhere, and one run wrote a script to /tmp, where the next could find it.
    # Edit's rule covers Write, and Read's covers what Glob and Grep may list.
    ALLOWED = ["Read(./**)", "Edit(./**)", "Glob(./**)", "Grep(./**)", "Skill", "Bash"]
    ISOLATED = ["--setting-sources", "project", "--strict-mcp-config"]
    # Every shell command runs, inside Claude Code's sandbox: writes only in the
    # run's folder, reads nothing in the home folder nor anything named in the
    # shared temporary folder, and no network. An allowlist of commands was
    # tried first and refused `cd <folder> && python3 ...`, and one refusal was
    # enough for an agent to decide there was no Python and hand over an
    # unchecked plan; the sandbox's own auto-allow still refused heredocs.
    SANDBOX = json.dumps({"sandbox": {"enabled": True, "autoAllowBashIfSandboxed": True,
                                      "allowUnsandboxedCommands": False,
                                      "filesystem": {"denyRead": ["~/", *_named_in_shared_tmp()],
                                                     "denyWrite": _named_in_shared_tmp()}}})
    # The skill's last step opens the page; on this machine nobody is looking.
    DENIED = ["Bash(open *)", "Bash(xdg-open *)", "Bash(start *)"]
    # Where Claude Code keeps a run's own temporary files, its commands' output
    # among them, which would otherwise go to the shared folder under names
    # the sandbox now refuses to read. Inside the run's folder, so the shell and
    # the file tools may use it, a resumed run finds it, and it goes with the
    # folder. Agents refused `$TMPDIR` find it and write their scripts there,
    # so it is not under `.claude/`, where Claude Code refuses every Write.
    OWN_TMP = ".tmp"

    def __init__(self, model=None, max_budget_usd=8.0, timeout=2400, binary="claude"):
        self.model = model
        self.max_budget_usd = max_budget_usd
        self.timeout = timeout
        self.binary = binary

    def install_skill(self, workdir: Path, skill: Path, name: str) -> Path:
        # The folder's name is the skill's name to Claude Code, whatever the
        # frontmatter says, so it is named here rather than taken from `skill`.
        target = workdir / ".claude" / "skills" / name
        shutil.copytree(skill, target)
        return target

    @staticmethod
    def folder_rules(workdir: Path) -> list:
        """The file tools' rules for the run's folder by its absolute path, in each spelling.

        `./**` alone let a relative path through and refused the absolute one
        hosts mostly write: `/private/var/...` on macOS, where a temporary
        folder is also `/var/...`. Five of seven runs had their plan's Write
        refused.
        """
        real = str(Path(workdir).resolve())
        spellings = {real}
        if real.startswith("/private/"):
            spellings.add(real[len("/private"):])
        return [tool + "(/" + path + "/**)" for path in sorted(spellings) for tool in ("Read", "Edit")]

    def run(self, workdir: Path, prompt: str, transcript: Path, resume: str | None = None) -> Turn:
        own_tmp = Path(workdir).resolve() / self.OWN_TMP
        own_tmp.mkdir(parents=True, exist_ok=True)
        args = [self.binary, "-p", prompt, *self.ISOLATED, "--tools", self.TOOLS,
                "--permission-mode", "dontAsk", "--settings", self.SANDBOX,
                "--allowedTools", *self.ALLOWED, *self.folder_rules(workdir),
                "--disallowedTools", *self.DENIED,
                "--output-format", "stream-json", "--verbose",
                "--max-budget-usd", str(self.max_budget_usd)]
        if self.model:
            args += ["--model", self.model]
        if resume:
            args += ["--resume", resume]
        env = dict(os.environ, CLAUDE_CODE_TMPDIR=str(own_tmp))
        try:
            done = subprocess.run(args, cwd=workdir, env=env, capture_output=True, text=True,
                                  timeout=self.timeout, stdin=subprocess.DEVNULL)
            stdout, stderr, timed_out = done.stdout, done.stderr, False
        except subprocess.TimeoutExpired as expired:
            stdout, stderr, timed_out = _text(expired.stdout), _text(expired.stderr), True
        with transcript.open("a") as out:
            out.write(stdout)
            if stderr:
                out.write(json.dumps({"type": "stderr", "text": stderr}) + "\n")
            if timed_out:
                out.write(json.dumps({"type": "timeout", "seconds": self.timeout}) + "\n")
        turn = self._turn(stdout)
        turn.timed_out = timed_out
        return turn

    @staticmethod
    def _turn(stream: str) -> Turn:
        turn = Turn(reply="", is_error=True, finished=False, session_id=None, cost_usd=0.0)
        for line in stream.splitlines():
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if event.get("type") == "system" and event.get("subtype") == "init":
                turn.listed = event.get("skills") or []
            elif event.get("type") == "assistant":
                for part in event.get("message", {}).get("content", []):
                    if part.get("type") != "tool_use":
                        continue
                    name, given = part.get("name"), part.get("input", {})
                    turn.tools.append(name)
                    if name == "Skill":
                        turn.skills.append(given.get("skill"))
                    elif name == "Read":
                        turn.reads.append(given.get("file_path"))
            elif event.get("type") == "result":
                turn.finished = True
                turn.reply = event.get("result") or ""
                turn.is_error = bool(event.get("is_error"))
                turn.session_id = event.get("session_id")
                turn.cost_usd = event.get("total_cost_usd") or 0.0
                turn.denied = [
                    "%s %s" % (d.get("tool_name"), _target(d.get("tool_input") or {}))
                    for d in event.get("permission_denials", [])
                ]
                turn.models = sorted(event.get("modelUsage") or {})
                turn.api_error = event.get("api_error_status")
        return turn

    def judge(self, workdir: Path, prompt: str, schema: dict, model: str | None) -> tuple:
        """The judge's structured answer and what it cost. No tools: it reads, it does not look."""
        args = [self.binary, "-p", prompt, *self.ISOLATED, "--tools", "",
                "--disable-slash-commands", "--no-session-persistence",
                "--output-format", "json", "--json-schema", json.dumps(schema)]
        if model:
            args += ["--model", model]
        done = subprocess.run(args, cwd=workdir, capture_output=True, text=True,
                              timeout=self.timeout, stdin=subprocess.DEVNULL)
        try:
            result = json.loads(done.stdout)
        except ValueError:
            raise RuntimeError("judge failed: " + (done.stderr or done.stdout)[:500])
        if result.get("is_error") or "structured_output" not in result:
            raise RuntimeError("judge failed: " + (result.get("result") or done.stderr)[:500])
        return result["structured_output"], result.get("total_cost_usd") or 0.0


AGENTS = {ClaudeCode.name: ClaudeCode}
