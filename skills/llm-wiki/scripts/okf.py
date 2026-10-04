#!/usr/bin/env python3
"""Tooling for Open Knowledge Format (OKF) v0.2 bundles used as LLM-wikis.

Subcommands
-----------
  lint    Conformance (OKF v0.2 §11) plus link, orphan and index checks.
  stale   Git-derived staleness of concepts, and coverage gaps in the repo.
  index   Regenerate index.md files from concept frontmatter.
  pin     Record the digest of a page's sources, once its sources have been read.
  prune   Candidates for retirement: pages whose subject is gone.
  upgrade Rewrite a v0.1 bundle's frontmatter to v0.2: `sources` and `status`.

Everything the model cannot reliably eyeball lives here; everything requiring
judgement (what a concept should say) stays in SKILL.md.

Exit codes: 0 = clean, 1 = errors (or warnings under --strict), 2 = bad usage.
S004 coverage gaps are advisory — whether a gap deserves a page is a judgement
call — so `stale` reports them but they never affect the exit code.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import pathspec
import yaml

# OKF §3.1 — reserved at any level of the hierarchy.
RESERVED = {"index.md", "log.md"}

# Agent instruction files, which a bundle carries so that the rules for editing
# it arrive with the directory rather than having to be sought out. Claude Code
# loads a nested CLAUDE.md on demand when it reads a file in that directory, and
# other agents read AGENTS.md the same way — so an agent that opens a page it was
# about to edit has been told to load this skill before it does.
#
# They are instructions, not knowledge: never concepts, never indexed, never
# reported stale. The trade is that nothing here checks their links either.
AGENT_INSTRUCTIONS = {"claude.md", "claude.local.md", "agents.md"}


def is_agent_instructions(name: str) -> bool:
    """Case-insensitively, is this an agent instruction file?

    Matched on the casefolded name because the hosts that read these files are
    doing so on case-insensitive filesystems: a file written as `claude.md` on
    macOS or Windows *is* `CLAUDE.md` to the agent that loads it. An exact-case
    check would call the same file instructions in one place and a malformed
    concept in the other, and the mismatch shows up on the path A5 is most
    likely to hit — an existing bundle whose files this skill did not write.
    """
    return name.casefold() in AGENT_INSTRUCTIONS


def is_concept_file(name: str) -> bool:
    """Every `.md` that is neither OKF-reserved nor an instruction file."""
    return name not in RESERVED and not is_agent_instructions(name)

# An index.md containing this marker is hand-curated: `index --write` leaves it
# alone, and lint treats its links as deliberate (they count against W011).
MANUAL_MARKER = "<!-- okf:manual -->"

# The version a new bundle declares, and the one `lint` reports. A bundle that
# declares another keeps what it declared: `index --write` does not upgrade it.
OKF_VERSION = "0.2"

# v0.2 §5.4. The statuses a v0.1 bundle used are mapped onto these by `upgrade`;
# `None` means the key goes, since absent means `stable`.
V02_STATUS = {"draft", "stable", "deprecated"}
LEGACY_STATUS = {
    "proposed": "draft",
    "accepted": "stable",
    "amended": "stable",
    "superseded": "deprecated",
    "answered": "deprecated",
    "open": None,
}

# L0 is a scan line: every index entry is read on the way to any single page, so
# its cost is paid by every query and not just the relevant one. The ceiling is a
# character budget rather than a sentence count because what costs a reader is
# length — a rambling one-sentence L0 is worse than two crisp ones.
#
# The floor catches truncation, which is silent and does not look like an error.
# An unquoted `#` opens a YAML comment and an unquoted `: ` breaks the mapping,
# so `description: White on #0091d9 measures 3.47:1` parses as "White on" and
# every check downstream passes on the two words that are left.
L0_MAX_CHARS = 250
L0_MIN_CHARS = 40

# Statuses meaning "still a true record, no longer the live answer". `index`
# sinks these to a trailing section so a scan meets what governs first, and only
# reads history if it keeps going. They are never deleted — a Decision is an
# event, and the reasoning in a superseded one routinely outlives the choice.
#
# `amended` is deliberately absent: an amended decision still governs in part,
# so demoting it would hide a live answer. Its L0 says what amended it instead.
RETIRED_STATUS = {"deprecated", "superseded", "answered"}
RETIRED_HEADING = "No longer current"

# A `Decision` records a fork somebody might re-litigate, so it is only worth a
# page of its own when it names the alternatives that were turned down. The
# check is on the shape of the section, not on its truth: it cannot tell a real
# alternative from a strawman, but it does stop the page that has none, which is
# the page an agent writes when it files a plain description under `decisions/`.
DECISION_TYPE = "decision"
ALTERNATIVES_HEADING_RE = re.compile(r"^#{1,6}\s+alternatives considered\s*$", re.I)
HEADING_RE = re.compile(r"^#{1,6}\s")
# Top-level bullets only: a sub-bullet elaborates an alternative, it is not another.
BULLET_RE = re.compile(r"^ {0,1}(?:[*+-]|\d+[.)])\s+\S")
FENCE_LINE_RE = re.compile(r"^\s*(```|~~~)")
MIN_ALTERNATIVES = 2
# Past this share of the concepts (and at least three), Decision pages are the
# default type rather than the exception.
DECISION_SHARE = 0.2
DECISION_SHARE_MIN = 3

# A page's pin is a digest of its sources' content, not a commit. A commit is a
# name for history, and history is what a squash merge, a rebase and a shallow
# clone each rewrite or cut off; the content of the files is the same on the other
# side of all three. Sixteen hex characters of SHA-256 is far more than telling
# "unchanged" from "changed" needs, and short enough to read in a frontmatter line.
DIGEST_KEY = "sources_digest"
DIGEST_LEN = 16
# How many commits that touched a page's sources are tried when looking for the
# one the pin was taken at, so a stale page can say what changed since.
BASELINE_SEARCH = 50

# Paths that never warrant a wiki concept. Overridable via <bundle>/.okfignore.
# Prose and dotfiles are excluded outright: the wiki *is* the prose layer, and a
# coverage report that nags about README.md teaches you to ignore it.
#
# Deliberately NOT merged with the project's .gitignore, for two reasons:
#
#   1. It would be a no-op. Coverage runs over `git ls-files`, i.e. *tracked*
#      files. Anything .gitignore excludes was never added, so it is already
#      invisible here. That is why this list contains no node_modules/, dist/ or
#      .venv/ — those can never reach us. Every entry below is a file that is
#      normally committed.
#   2. It would be wrong. Git's rule is "tracked beats ignored": a file that was
#      committed and *later* added to .gitignore stays tracked, and git does not
#      ignore it. Applying .gitignore here would silently drop such a file from
#      the S004 coverage report — making the wiki look complete when it is not.
#
# Reimplementing .gitignore is also a trap: nested files, `!` negation ordering,
# core.excludesFile and .git/info/exclude. `git ls-files` already gets all of
# that right. Let it.
DEFAULT_IGNORE = [
    ".*",
    "**/.*",
    "**/*.md",
    "**/*.rst",
    "**/*.txt",
    "**/__snapshots__/**",
    "**/testdata/**",
    "**/*.lock",
    "**/*.min.*",
    "**/*_test.*",
    "**/*.test.*",
    "**/*.spec.*",
    "**/test_*.py",
    "tests/**",
    "test/**",
    "spec/**",
    "docs/**",
    "vendor/**",
    "third_party/**",
    "**/LICENSE*",
]

FRONTMATTER_RE = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.S)
# Inline markdown links, excluding images (leading `!`).
LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(\s*<?([^)>\s]+)>?")
SCHEME_RE = re.compile(r"\A[a-zA-Z][a-zA-Z0-9+.\-]*:")
LOG_DATE_RE = re.compile(r"\A##\s+(\d{4}-\d{2}-\d{2})\s*\Z")
GLOB_CHARS = re.compile(r"[*?\[\]]")


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def git(repo: Path, *args: str) -> tuple[int, str]:
    """Run git in `repo`. Returns (returncode, stdout).

    Only the trailing newline is stripped: `git status --porcelain` encodes the
    status in columns 0-1, so a leading space is significant.
    """
    # Paths verbatim: with git's default quoting a non-ASCII file name arrives
    # as an escaped string that matches no file on disk.
    proc = subprocess.run(
        ["git", "-C", str(repo), "-c", "core.quotePath=false", *args],
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout.rstrip("\n")


def porcelain_paths(output: str) -> list[str]:
    """Extract paths from `git status --porcelain` lines (`XY path`, `R  old -> new`)."""
    paths = []
    for line in output.splitlines():
        if len(line) < 4:
            continue
        path = line[3:]
        if " -> " in path:  # rename/copy: report the destination
            path = path.split(" -> ", 1)[1]
        paths.append(path.strip('"'))
    return paths


def read_digest(doc: "Doc") -> str:
    """`sources_digest` as written. YAML would read 16 digits as a number, and an
    octal one when it starts with 0, so the line is read as text."""
    match = re.search(rf"^{DIGEST_KEY}:[ \t]*[\"']?([0-9A-Za-z]+)", doc.raw_frontmatter or "", re.M)
    return match.group(1) if match else ""


def is_decision(doc: "Doc") -> bool:
    return doc.type.casefold() == DECISION_TYPE


def count_alternatives(body: str) -> int:
    """Bullets under a `# Alternatives considered` heading, up to the next heading."""
    inside = False
    fenced = False
    count = 0
    for line in body.splitlines():
        if FENCE_LINE_RE.match(line):
            fenced = not fenced
        elif fenced:
            continue
        elif HEADING_RE.match(line):
            inside = bool(ALTERNATIVES_HEADING_RE.match(line.strip()))
        elif inside and BULLET_RE.match(line):
            count += 1
    return count


def split_frontmatter(text: str) -> tuple[str | None, str]:
    """Return (raw_yaml_or_None, body)."""
    match = FRONTMATTER_RE.match(text)
    if not match:
        return None, text
    return match.group(1), text[match.end() :]


def derive_title(path: Path) -> str:
    return path.stem.replace("-", " ").replace("_", " ").strip().title()


def has_concepts(directory: Path) -> bool:
    """True if any concept (non-reserved, non-hidden .md) lives under `directory`.

    A directory holding only an index.md, a log.md or an agent instruction file
    carries no knowledge of its own, so indexes neither list it nor expect it to
    have an index.
    """
    return any(
        is_concept_file(p.name)
        and not any(part.startswith(".") for part in p.relative_to(directory).parts)
        for p in directory.rglob("*.md")
    )


def resolve_link(target: str, doc: Path, bundle: Path) -> Path | None:
    """Resolve an in-bundle markdown link to a filesystem path, or None if external."""
    if SCHEME_RE.match(target) or target.startswith("#"):
        return None
    target = target.split("#", 1)[0]
    if not target:
        return None
    base = bundle / target.lstrip("/") if target.startswith("/") else doc.parent / target
    resolved = Path(os.path.normpath(base))
    if target.endswith("/") or resolved.is_dir():
        resolved = resolved / "index.md"
    return resolved


def normalize_sources(patterns: list[str], repo: Path, gitlinks: frozenset[str] = frozenset()) -> list[str]:
    """A bare directory means 'everything under it'. Globs pass through.

    A submodule is the exception: `git ls-files` reports it as a single gitlink
    entry at the bare directory path, and none of its files are tracked by the
    parent repo. Expanding it to `sub/**` would match nothing. Left alone, it
    matches exactly — and a pointer bump shows up as a normal diff, which is the
    only thing about a submodule the parent can observe.
    """
    out = []
    for raw in patterns:
        pattern = str(raw).strip()
        # A leading slash anchors a pattern to the root in gitignore syntax.
        anchored = pattern.startswith("/")
        pattern = pattern.strip("/")
        if not pattern:
            continue
        if pattern in gitlinks:
            out.append(pattern)
            continue
        if not GLOB_CHARS.search(pattern) and (repo / pattern).is_dir():
            pattern = f"{pattern}/**"
        elif "/" not in pattern and anchored:
            # Kept, since a slash-less pattern without it matches at any depth.
            # A pattern with a slash inside is anchored either way.
            pattern = f"/{pattern}"
        elif "/" not in pattern:
            # gitignore syntax matches a slash-less pattern (`Makefile`,
            # `*.sql`) at any depth, but git's `:(glob)` pathspec anchors it to
            # the root — coverage and diffing would disagree. A leading `**/`
            # means "in all directories, including the root" in both dialects.
            pattern = f"**/{pattern}"
        out.append(pattern)
    return out


def source_entries(raw) -> list[tuple[str | None, bool]]:
    """A `sources` value as (resource, is_plain_string) pairs.

    v0.2 §5.1 makes each entry a mapping with a `resource`; a v0.1 bundle wrote
    bare strings, still read here. A mapping with no `resource` comes back as
    `None`, which `lint` reports.
    """
    if raw is None or raw == "":
        return []
    items = raw if isinstance(raw, list) else [raw]
    out: list[tuple[str | None, bool]] = []
    for item in items:
        if isinstance(item, dict):
            resource = item.get("resource")
            out.append((str(resource).strip() if resource else None, False))
        elif item is not None:
            out.append((str(item).strip(), True))
    return out


def code_sources(raw) -> list[str]:
    """The entries of `sources` that name files in this repository.

    `sources` is also where a page cites what is not code: a URL, or a scope
    descriptor in words (§5.1). A repo path or glob has no scheme and no spaces,
    which is the whole of the test, so those other entries never reach `git`.
    """
    return [
        resource
        for resource, _ in source_entries(raw)
        if resource and not SCHEME_RE.match(resource) and not re.search(r"\s", resource)
    ]


# ---------------------------------------------------------------------------
# bundle model
# ---------------------------------------------------------------------------


@dataclass
class Doc:
    path: Path
    rel: str
    meta: dict
    body: str
    raw_frontmatter: str | None
    yaml_error: str | None = None

    @property
    def concept_id(self) -> str:
        return self.rel[: -len(".md")]

    @property
    def title(self) -> str:
        return str(self.meta.get("title") or derive_title(self.path))

    @property
    def description(self) -> str:
        return str(self.meta.get("description") or "").strip()

    @property
    def type(self) -> str:
        return str(self.meta.get("type") or "").strip()


@dataclass
class Bundle:
    root: Path
    repo: Path
    concepts: list[Doc] = field(default_factory=list)
    indexes: list[Doc] = field(default_factory=list)
    logs: list[Doc] = field(default_factory=list)

    @property
    def all_docs(self) -> list[Doc]:
        return [*self.concepts, *self.indexes, *self.logs]


def load_doc(path: Path, bundle_root: Path) -> Doc:
    text = path.read_text(encoding="utf-8")
    raw, body = split_frontmatter(text)
    meta: dict = {}
    err = None
    if raw is not None:
        try:
            parsed = yaml.safe_load(raw)
            if parsed is None:
                meta = {}
            elif isinstance(parsed, dict):
                meta = parsed
            else:
                err = f"frontmatter is {type(parsed).__name__}, expected a mapping"
        except yaml.YAMLError as exc:
            err = str(exc).splitlines()[0]
    return Doc(
        path=path,
        rel=str(path.relative_to(bundle_root)).replace(os.sep, "/"),
        meta=meta,
        body=body,
        raw_frontmatter=raw,
        yaml_error=err,
    )


def load_bundle(root: Path, repo: Path) -> Bundle:
    bundle = Bundle(root=root, repo=repo)
    for path in sorted(root.rglob("*.md")):
        if any(part.startswith(".") for part in path.relative_to(root).parts):
            continue
        if is_agent_instructions(path.name):
            continue
        doc = load_doc(path, root)
        if path.name == "index.md":
            bundle.indexes.append(doc)
        elif path.name == "log.md":
            bundle.logs.append(doc)
        else:
            bundle.concepts.append(doc)
    return bundle


def doc_links(doc: Doc, bundle: Bundle) -> list[tuple[str, Path | None]]:
    return [(t, resolve_link(t, doc.path, bundle.root)) for t in LINK_RE.findall(doc.body)]


# ---------------------------------------------------------------------------
# lint
# ---------------------------------------------------------------------------


def lint(bundle: Bundle) -> tuple[list[dict], list[dict]]:
    errors: list[dict] = []
    warnings: list[dict] = []

    def err(code, rel, msg):
        errors.append({"code": code, "file": rel, "message": msg})

    def warn(code, rel, msg):
        warnings.append({"code": code, "file": rel, "message": msg})

    # An instruction file that carries frontmatter is almost certainly a concept
    # that has been masked: `load_bundle` skips these names, so such a page drops
    # out of the count, out of `stale`, and — silently, at exit 0 — out of its
    # index on the next `index --write`. The frontmatter is the tell, because a
    # real instruction file has none.
    for path in sorted(bundle.root.rglob("*.md")):
        rel_parts = path.relative_to(bundle.root).parts
        if any(part.startswith(".") for part in rel_parts):
            continue
        if not is_agent_instructions(path.name):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            # These names are otherwise never read, so a directory called
            # CLAUDE.md or a file that is not UTF-8 would take lint down with a
            # traceback. Neither is a concept in hiding.
            continue
        raw, _ = split_frontmatter(text)
        if raw is None:
            continue
        # A `---` opening a horizontal rule is not frontmatter, and an
        # instruction file is prose that may well start with one. Only a block
        # that parses as a mapping is evidence of a masked concept.
        try:
            meta = yaml.safe_load(raw)
        except yaml.YAMLError:
            meta = None
        if not isinstance(meta, dict):
            continue
        warn(
            "W018",
            "/".join(rel_parts),
            "agent instruction file has YAML frontmatter — if this is a concept, "
            "rename it and fix its inbound links; nothing else here reports it",
        )

    # §11 — concept conformance.
    for doc in bundle.concepts:
        if doc.raw_frontmatter is None:
            err("E001", doc.rel, "no YAML frontmatter block")
            continue
        if doc.yaml_error:
            err("E002", doc.rel, f"unparseable frontmatter: {doc.yaml_error}")
            continue
        if not doc.type:
            err("E003", doc.rel, "frontmatter has no non-empty `type` field")
        if not doc.description:
            warn("W013", doc.rel, "no `description` (index entries and previews use it)")
        elif len(doc.description) > L0_MAX_CHARS:
            warn(
                "W017",
                doc.rel,
                f"`description` is {len(doc.description)} chars; L0 is a scan line read on "
                f"the way to every page, so budget {L0_MAX_CHARS}. Move the detail into the body",
            )
        elif len(doc.description) < L0_MIN_CHARS:
            warn(
                "W017",
                doc.rel,
                f"`description` is only {len(doc.description)} chars — a stub, or truncated by "
                "an unquoted `#` starting a YAML comment. Quote it and check it reads whole",
            )
        if doc.meta.get("source_commit") and not read_digest(doc) and not is_decision(doc):
            warn(
                "W022",
                doc.rel,
                f"pinned by `source_commit`, which a squash merge or a rebase invalidates; "
                f"`okf.py pin --migrate` converts the pages that are current, and one that is "
                f"not is read and pinned by name for `{DIGEST_KEY}`",
            )
        tags = doc.meta.get("tags")
        if tags is not None and not isinstance(tags, list):
            warn("W015", doc.rel, "`tags` should be a YAML list")
        status = doc.meta.get("status")
        if status is not None and str(status).strip().lower() not in V02_STATUS:
            hint = LEGACY_STATUS.get(str(status).strip().lower(), "stable")
            warn(
                "W023",
                doc.rel,
                f"`status: {status}` is not one of draft | stable | deprecated (§5.4); "
                f"`okf.py upgrade` maps it to " + (f"`{hint}`" if hint else "no key, since absent means stable"),
            )
        entries = source_entries(doc.meta.get("sources"))
        if any(plain for _, plain in entries):
            warn(
                "W024",
                doc.rel,
                "`sources` holds plain strings; v0.2 §5.1 makes each entry a mapping with a "
                "`resource`. `okf.py upgrade` rewrites a list of only strings; a mixed one is edited by hand",
            )
        if any(resource is None for resource, _ in entries):
            warn("W025", doc.rel, "a `sources` entry has no `resource`, which §5.1 requires")
        if is_decision(doc):
            if count_alternatives(doc.body) < MIN_ALTERNATIVES:
                warn(
                    "W019",
                    doc.rel,
                    f"Decision names fewer than {MIN_ALTERNATIVES} rejected alternatives under "
                    "`# Alternatives considered`. With no live alternative nobody can "
                    "re-litigate, it is not a decision: write it as a section of the page "
                    "that owns the thing",
                )
            if not code_sources(doc.meta.get("sources")):
                warn(
                    "W020",
                    doc.rel,
                    "Decision has no `sources`, so `prune` cannot tell when its subject is "
                    "gone. Name the code the choice shaped",
                )

    decisions = [d for d in bundle.concepts if d.raw_frontmatter is not None and is_decision(d)]
    if len(decisions) >= DECISION_SHARE_MIN and len(decisions) > DECISION_SHARE * len(bundle.concepts):
        warn(
            "W021",
            ".",
            f"{len(decisions)} of {len(bundle.concepts)} concepts are Decisions. Most forks "
            "belong in the Module or Invariant that owns them; review the newest for demotion",
        )

    # §8 — index files carry no frontmatter, except okf_version at bundle root.
    for doc in bundle.indexes:
        is_root = doc.path.parent == bundle.root
        if doc.raw_frontmatter is None:
            if is_root:
                warn("W005", doc.rel, f'root index.md should declare okf_version: "{OKF_VERSION}"')
        elif not is_root:
            err("E004", doc.rel, "non-root index.md must not have frontmatter (§8)")
        elif doc.yaml_error:
            err("E002", doc.rel, f"unparseable frontmatter: {doc.yaml_error}")
        elif "okf_version" not in doc.meta:
            warn("W005", doc.rel, f'root index.md should declare okf_version: "{OKF_VERSION}"')

    # §9 — log entries are ISO-dated, newest first.
    for doc in bundle.logs:
        if doc.raw_frontmatter is not None:
            err("E004", doc.rel, "log.md must not have frontmatter (§9)")
        dates = [m.group(1) for line in doc.body.splitlines() if (m := LOG_DATE_RE.match(line.strip()))]
        headings = [l for l in doc.body.splitlines() if l.strip().startswith("## ")]
        if len(dates) != len(headings):
            err("E006", doc.rel, "every `## ` heading must be an ISO 8601 YYYY-MM-DD date (§9)")
        if dates != sorted(dates, reverse=True):
            err("E007", doc.rel, "log entries must be newest-first")

    # §6.1 — broken links are tolerated by consumers, but usually a typo here.
    # Inbound links (for W011) are counted only from concepts, logs and
    # hand-curated (`okf:manual`) indexes: `index --write` links every concept
    # from its directory's index, so auto-generated indexes would satisfy the
    # orphan check by construction and it could never fire.
    known = {d.path.resolve() for d in bundle.all_docs}
    inbound: set[Path] = set()
    for doc in bundle.all_docs:
        curated = doc.path.name != "index.md" or MANUAL_MARKER in doc.body
        for target, resolved in doc_links(doc, bundle):
            if resolved is None:
                continue
            rp = resolved.resolve()
            if rp in known:
                if curated and rp != doc.path.resolve():
                    inbound.add(rp)
            elif resolved.suffix == ".md" and not resolved.exists():
                warn("W010", doc.rel, f"link target does not exist: {target}")

    # Orphans: unreachable concepts are invisible to progressive disclosure.
    for doc in bundle.concepts:
        if doc.path.resolve() not in inbound:
            warn("W011", doc.rel, "orphan — no concept, log or curated index links to it")

    # Index coverage: every concept/subdir listed in its directory's index.md.
    for index_doc in bundle.indexes:
        directory = index_doc.path.parent
        linked = {r.resolve() for _, r in doc_links(index_doc, bundle) if r is not None}
        for child in sorted(directory.iterdir()):
            if child.is_dir():
                if child.name.startswith("."):
                    continue
                if not has_concepts(child):
                    continue
                expected = (child / "index.md").resolve()
                if expected not in linked:
                    warn("W012", index_doc.rel, f"does not link subdirectory `{child.name}/`")
            elif child.suffix == ".md" and is_concept_file(child.name):
                if child.resolve() not in linked:
                    warn("W012", index_doc.rel, f"does not link concept `{child.name}`")

    for directory in {d.path.parent for d in bundle.concepts}:
        if not (directory / "index.md").exists():
            rel = str(directory.relative_to(bundle.root)).replace(os.sep, "/")
            warn("W016", rel or ".", "directory has concepts but no index.md")

    return errors, warnings


# ---------------------------------------------------------------------------
# stale
# ---------------------------------------------------------------------------


def tracked_files(repo: Path) -> list[str]:
    code, out = git(repo, "ls-files")
    if code != 0:
        return []
    return [line for line in out.splitlines() if line]


def gitlink_paths(repo: Path) -> frozenset[str]:
    """Submodule paths, which `git ls-files` reports as mode-160000 entries."""
    code, out = git(repo, "ls-files", "--stage")
    if code != 0:
        return frozenset()
    paths = set()
    for line in out.splitlines():
        if line.startswith("160000 ") and "\t" in line:
            paths.add(line.split("\t", 1)[1])
    return frozenset(paths)


def page_in_repo(doc: Doc, repo: Path) -> str | None:
    """The concept's own file, as git names it, or None when it is outside the repo."""
    try:
        return str(doc.path.resolve().relative_to(repo.resolve())).replace(os.sep, "/")
    except ValueError:
        return None


# Starts each commit's header in `git log` output; file names follow it.
_COMMIT = "\x1e"


def unread_commits(
    repo: Path, since: str, pathspecs: list[str], page: str | None, branch_start: str | None = None
):
    """The commits after `since` that changed the sources and not the page.

    A commit that changes the page together with its sources is the page
    describing its own change, so it needs no pin of its own. That is what lets
    a change ship as one squashed commit: the pin can only name a commit that
    exists before the merge, and a squash gives the change a hash nobody could
    have written into the page beforehand. A commit that touches the page for
    another reason covers only itself, never an earlier commit that changed the
    sources and left the page alone.

    A merge commit is judged by its diff against its first parent, the change
    it brought in, and the commits of the branch it merged are not walked: the
    same rule a squash applies.

    With `branch_start`, the commits after it are judged as main will see them
    once the branch is squashed: as one change, which covers the page if the
    branch's net diff touches it. An edit made on the branch and then reverted
    covers nothing.

    Returns (commits as `<short hash> <subject>`, the source files they changed).
    """
    specs = list(pathspecs) + ([f":(literal){page}"] if page else [])
    # Paths verbatim, so a page named in another script still matches its own name.
    quiet = ("-c", "core.quotePath=false")
    _, out = git(
        repo, *quiet, "log", "--first-parent", "-m", f"--format={_COMMIT}%H %h %s", "--name-only",
        f"{since}..HEAD", "--", *specs,
    )
    on_branch: set[str] = set()
    branch_covers = False
    if branch_start:
        _, listed = git(repo, "rev-list", f"{branch_start}..HEAD")
        on_branch = set(listed.split())
        if page is not None:
            _, net = git(repo, *quiet, "diff", "--name-only", branch_start, "HEAD", "--", f":(literal){page}")
            branch_covers = bool(net)
    commits: list[str] = []
    files: list[str] = []
    for entry in out.split(_COMMIT)[1:]:
        lines = [line for line in entry.splitlines() if line]
        full, _, header = lines[0].partition(" ")
        names = lines[1:]
        sources = [name for name in names if name != page]
        if not sources:
            continue
        if full in on_branch:
            if branch_covers:
                continue
        elif page is not None and page in names:
            continue
        commits.append(header)
        files.extend(name for name in sources if name not in files)
    return commits, files


def worktree_files(repo: Path) -> list[str]:
    """Tracked files plus untracked ones git does not ignore.

    A page is pinned before the change is committed, and a file the change adds is
    untracked until it is staged. Left out of the digest it would flip the page to
    stale the moment it is added, so the digest sees what `git add .` would.
    """
    code, out = git(repo, "ls-files", "--cached", "--others", "--exclude-standard")
    return sorted(set(line for line in out.splitlines() if line)) if code == 0 else []


def digest_of(entries: list[tuple[str, str, str]]) -> str:
    """Digest of (mode, blob id, path) entries: the shape of a tree listing."""
    h = hashlib.sha256()
    for mode, oid, path in sorted(entries, key=lambda e: e[2]):
        h.update(f"{mode} {oid} {path}\n".encode())
    return h.hexdigest()[:DIGEST_LEN]


def working_entries(repo: Path, matched: list[str]) -> list[tuple[str, str, str]]:
    """The matched files as they are on disk now, as (mode, blob id, path).

    Regular files are hashed from the working tree through `git hash-object`,
    which applies the same clean filters as `git add`, so a clean checkout
    digests the same as the commit it is at whatever its line endings. A symlink
    or a submodule keeps the id the index records, and a file deleted from the
    working tree counts as a change. Reading the disk and not the commit is what
    lets a page be pinned before the change is committed.
    """
    _, staged = git(repo, "ls-files", "--stage")
    index: dict[str, tuple[str, str]] = {}
    for line in staged.splitlines():
        meta, _, path = line.partition("\t")
        mode, oid, _stage = meta.split()
        index.setdefault(path, (mode, oid))
    entries: list[tuple[str, str, str]] = []
    regular: list[str] = []
    for path in matched:
        default_mode = "100755" if os.access(repo / path, os.X_OK) and (repo / path).is_file() else "100644"
        mode, oid = index.get(path, (default_mode, ""))
        if mode in ("120000", "160000"):
            entries.append((mode, oid, path))
        elif (repo / path).is_file():
            regular.append(path)
            entries.append((mode, "", path))
        else:
            entries.append((mode, "deleted", path))
    if regular:
        proc = subprocess.run(
            ["git", "-C", str(repo), "hash-object", "--stdin-paths"],
            input="\n".join(regular) + "\n", capture_output=True, text=True,
        )
        hashes = iter(proc.stdout.split())
        entries = [(m, next(hashes) if o == "" else o, p) for m, o, p in entries]
    return entries


def commit_entries(
    repo: Path, commit: str, patterns: list[str]
) -> list[tuple[str, str, str]]:
    """The files `patterns` match in `commit`'s tree, as (mode, blob id, path)."""
    prefixes: set[str] = set()
    for pattern in patterns:
        literal = GLOB_CHARS.split(pattern.lstrip("/"), 1)[0]
        prefixes.add(literal if literal == pattern.lstrip("/") else literal.rpartition("/")[0])
    # A pattern with no directory in front of its first wildcard needs the whole tree.
    narrow = [p for p in sorted(prefixes) if p] if "" not in prefixes else []
    _, out = git(repo, "-c", "core.quotePath=false", "ls-tree", "-r", commit, "--", *narrow)
    spec = pathspec.PathSpec.from_lines("gitwildmatch", patterns)
    entries = []
    for line in out.splitlines():
        meta, _, path = line.partition("\t")
        mode, kind, oid = meta.split()
        if kind in ("blob", "commit") and spec.match_file(path):
            entries.append((mode, oid, path))
    return entries


def pin_baseline(repo: Path, recorded: str, patterns: list[str], pathspecs: list[str]) -> dict:
    """The newest commit whose sources digest to `recorded`, and what changed since.

    The digest says *that* the sources changed and nothing about how. The commit
    that has them as they were when the page was read is the base for the diff the
    reader has to look at, and it is found by digesting the commits that touched
    the sources, newest first. It is not always there: a squash merge leaves no
    commit with the branch's intermediate state, and a shallow clone cuts the walk
    short. The answer is then only "changed", which is still true.
    """
    quiet = ("-c", "core.quotePath=false")
    _, listed = git(
        repo, "log", "--first-parent", f"-n{BASELINE_SEARCH}", "--format=%H", "--", *pathspecs
    )
    for commit in listed.split():
        if digest_of(commit_entries(repo, commit, patterns)) == recorded:
            _, subjects = git(
                repo, *quiet, "log", "--first-parent", "--format=%h %s", f"{commit}..HEAD", "--", *pathspecs
            )
            _, names = git(repo, *quiet, "diff", "--name-only", commit, "HEAD", "--", *pathspecs)
            return {
                "baseline": commit[:12],
                "commits": subjects.splitlines()[:10],
                "files": names.splitlines()[:20],
            }
    return {}


def matched_sources(
    doc: Doc, repo: Path, tracked: list[str], gitlinks: frozenset[str]
) -> tuple[list[str], list[str]]:
    """A concept's normalized `sources` patterns, and the tracked files they match."""
    raw_sources = code_sources(doc.meta.get("sources"))
    if not raw_sources:
        return [], []
    patterns = normalize_sources(raw_sources, repo, gitlinks)
    if not patterns:
        return [], []
    spec = pathspec.PathSpec.from_lines("gitwildmatch", patterns)
    return patterns, [f for f in tracked if spec.match_file(f)]


def stale(bundle: Bundle, base: str | None = None) -> dict:
    repo = bundle.repo
    findings: list[dict] = []
    tracked = tracked_files(repo)
    gitlinks = gitlink_paths(repo)
    covered: set[str] = set()

    code, _ = git(repo, "rev-parse", "--verify", "HEAD")
    has_head = code == 0
    branch_start = None
    if base and has_head:
        code, out = git(repo, "merge-base", "HEAD", base)
        if code != 0:
            print(f"error: no merge base between HEAD and {base}", file=sys.stderr)
            raise SystemExit(2)
        branch_start = out.strip()

    for doc in bundle.concepts:
        patterns, matched = matched_sources(doc, repo, tracked, gitlinks)
        if not patterns:
            continue
        covered.update(matched)

        if not matched:
            message = f"`sources` matches no tracked file: {patterns}"
            if is_decision(doc):
                message += " — the subject may be gone: a retirement candidate (A6)"
            findings.append({"code": "S005", "concept": doc.rel, "message": message})
            continue

        # A Decision is an event: the code it shaped changing later does not make
        # it false, so only its subject vanishing (S005) says anything about it.
        if is_decision(doc):
            continue

        # git reads a leading slash as the filesystem root, not the repository's.
        pathspecs = [f":(glob){p.lstrip('/')}" for p in patterns]
        recorded = str(doc.meta.get("source_commit") or "").strip()
        digest = read_digest(doc)

        if digest:
            # The current form: compare content, so there is no history to be
            # rewritten, and a dirty working tree is simply judged as it is.
            spec = pathspec.PathSpec.from_lines("gitwildmatch", patterns)
            current = digest_of(working_entries(repo, [f for f in worktree_files(repo) if spec.match_file(f)]))
            if current != digest:
                finding = {
                    "code": "S001",
                    "concept": doc.rel,
                    "message": f"sources changed since the page was pinned ({digest} -> {current})",
                }
                if has_head:
                    baseline = pin_baseline(repo, digest, patterns, pathspecs)
                    if baseline:
                        finding["message"] += (
                            f"; read `git diff {baseline['baseline']} -- <sources>`"
                        )
                        finding.update(baseline)
                findings.append(finding)
            continue

        # Uncommitted edits in the concept's sources.
        _, dirty = git(repo, "status", "--porcelain", "--", *pathspecs)
        if dirty:
            findings.append(
                {
                    "code": "S002",
                    "concept": doc.rel,
                    "message": "sources have uncommitted changes",
                    "files": porcelain_paths(dirty)[:20],
                }
            )

        if not has_head:
            continue

        if not recorded:
            findings.append(
                {
                    "code": "S003",
                    "concept": doc.rel,
                    "message": f"has `sources` but no `{DIGEST_KEY}`; cannot tell if it is current",
                }
            )
            continue

        code, _ = git(repo, "cat-file", "-e", f"{recorded}^{{commit}}")
        if code != 0:
            findings.append(
                {
                    "code": "S006",
                    "concept": doc.rel,
                    "message": f"`source_commit` {recorded[:12]} is not in this repo "
                    "(history rewritten?) — re-review against HEAD",
                }
            )
            continue

        code, _ = git(repo, "merge-base", "--is-ancestor", recorded, "HEAD")
        if code != 0:
            findings.append(
                {
                    "code": "S006",
                    "concept": doc.rel,
                    "message": f"`source_commit` {recorded[:12]} is not an ancestor of HEAD "
                    "— re-review against HEAD",
                }
            )
            continue

        unread, changed = unread_commits(
            repo, recorded, pathspecs, page_in_repo(doc, repo), branch_start
        )
        if unread:
            findings.append(
                {
                    "code": "S001",
                    "concept": doc.rel,
                    "message": f"sources changed in {len(unread)} commit(s) since "
                    f"{recorded[:12]} that left the page alone",
                    "files": changed[:20],
                    "commits": unread[:10],
                }
            )

    # Coverage: tracked source files no concept claims.
    ignore_file = bundle.root / ".okfignore"
    patterns = list(DEFAULT_IGNORE)
    if ignore_file.exists():
        # A user-supplied .okfignore replaces the defaults; it does not extend them.
        patterns = [
            line.strip()
            for line in ignore_file.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]

    standalone = False
    try:
        bundle_rel = str(bundle.root.resolve().relative_to(repo.resolve())).replace(os.sep, "/")
        if bundle_rel == ".":
            # The bundle *is* the repo — there is no separate code to cover.
            standalone = True
        else:
            patterns.append(f"{bundle_rel}/**")
    except ValueError:
        pass
    ignore = pathspec.PathSpec.from_lines("gitwildmatch", patterns)

    gaps: dict[str, list[str]] = {}
    for f in [] if standalone else tracked:
        if f in covered or ignore.match_file(f):
            continue
        # A gitlink is a whole vendored repo, not a file at the tree root —
        # report it under its own name rather than bucketing it into ".".
        if f in gitlinks:
            top = f
        elif "/" in f:
            top = f.split("/")[0]
        else:
            top = "."
        gaps.setdefault(top, []).append(f)

    return {
        "findings": findings,
        "coverage_gaps": [
            {"code": "S004", "path": k, "count": len(v), "sample": sorted(v)[:8]}
            for k, v in sorted(gaps.items())
        ],
    }


# ---------------------------------------------------------------------------
# pin
# ---------------------------------------------------------------------------

PIN_KEYS = ("source_commit", DIGEST_KEY)


def sources_block_end(lines: list[str]) -> int | None:
    """Index just past the `sources:` entry in a frontmatter's lines, or None."""
    for i, line in enumerate(lines):
        if not line.startswith("sources:"):
            continue
        value = line[len("sources:") :].strip()
        j = i + 1
        if value.startswith("[") and "]" not in value:
            while j < len(lines) and "]" not in lines[j - 1]:
                j += 1
        elif not value:
            # A block sequence: indented lines, or `- ` at the key's own indent.
            while j < len(lines) and (lines[j].startswith((" ", "\t")) or lines[j].startswith("- ")):
                j += 1
        return j
    return None


def write_pin(doc: Doc, digest: str) -> None:
    """Set `sources_digest` in the page's frontmatter and drop `source_commit`.

    A text edit and not a YAML round trip, so the rest of the frontmatter keeps
    its order, comments and quoting. The line goes straight after `sources`.
    """
    # newline="" keeps a CRLF page CRLF: the edit adds one line and nothing else.
    with open(doc.path, encoding="utf-8", newline="") as handle:
        text = handle.read()
    match = FRONTMATTER_RE.match(text)
    assert match is not None
    eol = "\r\n" if "\r\n" in match.group(1) else "\n"
    lines = match.group(1).split(eol)
    lines = [l for l in lines if not l.startswith("source_commit:")]
    pin_line = f"{DIGEST_KEY}: {digest}"
    existing = [i for i, l in enumerate(lines) if l.startswith(f"{DIGEST_KEY}:")]
    if existing:
        lines[existing[0]] = pin_line
    else:
        end = sources_block_end(lines)
        lines.insert(len(lines) if end is None else end, pin_line)
    with open(doc.path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text[: match.start(1)] + eol.join(lines) + text[match.end(1) :])


def resolve_pages(bundle: Bundle, names: list[str]) -> tuple[list[Doc], list[str]]:
    """Concepts named by path (from here or from the bundle) or by concept id."""
    docs, unknown = [], []
    for name in names:
        wanted = {Path(name).expanduser().resolve(), (bundle.root / name).resolve(),
                  (bundle.root / f"{name}.md").resolve()}
        hit = next((d for d in bundle.concepts if d.path.resolve() in wanted), None)
        if hit is None:
            same_name = [d for d in bundle.concepts if d.path.stem == name]
            hit = same_name[0] if len(same_name) == 1 else None
        if hit is None:
            unknown.append(name)
        elif hit not in docs:
            docs.append(hit)
    return docs, unknown


def pin(bundle: Bundle, names: list[str], migrate: bool) -> dict:
    """Pin pages to the content of their sources as it is now.

    Pinning is the act of saying *I have read these sources and the page is right
    about them*, so it takes pages by name and never defaults to all of them. The
    one bulk form, `--migrate`, only converts pages that are current under the old
    commit pin, which changes how a page is pinned and vouches for nothing new.
    """
    repo = bundle.repo
    tracked = tracked_files(repo)
    gitlinks = gitlink_paths(repo)
    pinned: list[dict] = []
    skipped: list[dict] = []

    if migrate:
        blocked = {f["concept"] for f in stale(bundle)["findings"]}
        docs = [
            d for d in bundle.concepts
            if d.meta.get("source_commit") and not read_digest(d) and not is_decision(d)
        ]
        names_skipped = {d.rel for d in docs if d.rel in blocked}
        skipped += [
            {"concept": r, "reason": "not current under its `source_commit`; read what changed, then pin it by name"}
            for r in sorted(names_skipped)
        ]
        docs = [d for d in docs if d.rel not in names_skipped]
    else:
        docs, unknown = resolve_pages(bundle, names)
        skipped += [{"concept": n, "reason": "no such concept in the bundle"} for n in unknown]

    for doc in docs:
        patterns, matched = matched_sources(doc, repo, tracked, gitlinks)
        if is_decision(doc):
            skipped.append({"concept": doc.rel, "reason": "a Decision records an event and is not pinned"})
        elif not patterns:
            skipped.append({"concept": doc.rel, "reason": "no `sources`"})
        elif not matched:
            skipped.append({"concept": doc.rel, "reason": "`sources` matches no tracked file (S005)"})
        else:
            spec = pathspec.PathSpec.from_lines("gitwildmatch", patterns)
            counted = [f for f in worktree_files(repo) if spec.match_file(f)]
            digest = digest_of(working_entries(repo, counted))
            write_pin(doc, digest)
            item = {"concept": doc.rel, DIGEST_KEY: digest}
            # A file git has not been told about is counted, so a new file does not
            # flip the page when it is added. A stray one is counted too, quietly
            # baked into the pin, so the pin says which it took.
            untracked = [f for f in counted if f not in set(tracked)]
            if untracked:
                item["untracked"] = untracked[:PRUNE_PATHS_SHOWN]
            pinned.append(item)
    return {"pinned": pinned, "skipped": skipped}


# ---------------------------------------------------------------------------
# upgrade
# ---------------------------------------------------------------------------


def yaml_scalar(value: str) -> str:
    """`value` as a YAML scalar, quoted only where a plain one would not parse.

    A glob that starts with `*` is an alias in YAML, so `**/Makefile` has to be
    quoted; `src/auth/**` does not.
    """
    plain = (
        value
        and value != "~"
        and value[0] not in "*&!|>%@`'\"{[,#?:"
        and not value.startswith("- ")
        and ":" not in value
        and not re.search(r"\s", value)
    )
    return value if plain else json.dumps(value)


def upgrade_frontmatter(lines: list[str], meta: dict) -> tuple[list[str], list[str]]:
    """v0.1 frontmatter lines as v0.2, and a note for each change made."""
    notes: list[str] = []
    entries = source_entries(meta.get("sources"))
    if entries and all(plain and resource for resource, plain in entries):
        start = next(i for i, l in enumerate(lines) if l.startswith("sources:"))
        end = sources_block_end(lines) or start + 1
        block = ["sources:"] + [f"  - resource: {yaml_scalar(r)}" for r, _ in entries if r]
        lines = lines[:start] + block + lines[end:]
        notes.append(f"`sources`: {len(entries)} plain string(s) -> `resource` mappings")
    status = str(meta.get("status") or "").strip().lower()
    if status in LEGACY_STATUS:
        target = LEGACY_STATUS[status]
        idx = next(i for i, l in enumerate(lines) if l.startswith("status:"))
        if target is None:
            del lines[idx]
            notes.append(f"`status: {status}` -> removed (absent means stable)")
        else:
            lines[idx] = f"status: {target}"
            notes.append(f"`status: {status}` -> `{target}`")
    return lines, notes


def upgrade(bundle: Bundle, write: bool) -> list[dict]:
    """Rewrite v0.1 frontmatter as v0.2, as text edits that leave the rest alone.

    A `sources` list that mixes strings and mappings is left for a person: there
    is no telling which of the strings was meant as a path. `timestamp` stays; it is
    a legacy key v0.2 still reads, and `lint` no longer asks for it.
    """
    changes: list[dict] = []

    def rewrite(doc: Doc, transform) -> None:
        with open(doc.path, encoding="utf-8", newline="") as handle:
            text = handle.read()
        match = FRONTMATTER_RE.match(text)
        if match is None:
            return
        eol = "\r\n" if "\r\n" in match.group(1) else "\n"
        lines, notes = transform(match.group(1).split(eol))
        if not notes:
            return
        changes.append({"file": doc.rel, "changes": notes})
        if write:
            with open(doc.path, "w", encoding="utf-8", newline="") as handle:
                handle.write(text[: match.start(1)] + eol.join(lines) + text[match.end(1) :])

    for doc in bundle.concepts:
        if doc.raw_frontmatter is not None and not doc.yaml_error:
            rewrite(doc, lambda lines, d=doc: upgrade_frontmatter(lines, d.meta))
    for doc in bundle.indexes:
        if doc.path.parent == bundle.root and doc.meta.get("okf_version") not in (None, OKF_VERSION):
            def bump(lines, old=doc.meta["okf_version"]):
                lines = [f'okf_version: "{OKF_VERSION}"' if l.startswith("okf_version:") else l for l in lines]
                return lines, [f'`okf_version: "{old}"` -> `"{OKF_VERSION}"`']
            rewrite(doc, bump)
    return changes


# ---------------------------------------------------------------------------
# prune
# ---------------------------------------------------------------------------

FENCE_RE = re.compile(r"^(```|~~~).*?^\1[ \t]*$", re.S | re.M)
CODE_SPAN_RE = re.compile(r"`([^`\n]+)`")
PATH_SHAPE_RE = re.compile(r"\A[\w.@+-]+(?:/[\w.@+-]+)+/?\Z")
PRUNE_PATHS_SHOWN = 5


def is_retired(doc: Doc) -> bool:
    return str(doc.meta.get("status", "")).lower() in RETIRED_STATUS


def named_missing_paths(doc: Doc, tracked: list[str], gitlinks: frozenset[str] = frozenset()) -> list[str]:
    """Repo paths a page's code spans name that no tracked file has.

    Only a span that reads as a path into this repo counts: it has a slash, and
    its first segment is a file or directory at the repo root. That leaves out
    `.venv/bin/python`, URLs, and paths in somebody else's tree, which are most
    of what a page names that is not here. A directory counts when any tracked
    file is under it.
    """
    roots = {f.split("/", 1)[0] for f in tracked}
    files = set(tracked)
    missing: list[str] = []
    for span in CODE_SPAN_RE.findall(FENCE_RE.sub("", doc.body)):
        span = span.strip()
        if not PATH_SHAPE_RE.match(span):
            continue
        path = span.rstrip("/")
        segments = path.split("/")
        if segments[0] not in roots or path in files:
            continue
        # A dot-directory (`.venv`, `.git`) is the environment, not the project,
        # and nothing inside a submodule is tracked here.
        if any(seg.startswith(".") and seg not in ("..",) for seg in segments[1:]) or any(
            path.startswith(link + "/") for link in gitlinks
        ):
            continue
        if any(f.startswith(path + "/") for f in tracked):
            continue
        if path not in missing:
            missing.append(path)
    return missing


def prune(bundle: Bundle) -> list[dict]:
    """Retirement candidates. Advisory: each one is a prompt to look, never a verdict.

    Nothing here reads a date. A page does not go false by getting old, so age
    is the one signal this leaves out; each of these says the world moved.
    """
    repo = bundle.repo
    tracked = tracked_files(repo)
    gitlinks = gitlink_paths(repo)
    candidates: list[dict] = []

    def add(code: str, doc: Doc, message: str, **extra) -> None:
        candidates.append({"code": code, "concept": doc.rel, "message": message, **extra})

    # Who links to whom, among concepts only: an index lists every page and a log
    # names whatever changed, so neither says a page is still relied on.
    live_inbound: set[Path] = set()
    for doc in bundle.concepts:
        if is_retired(doc):
            continue
        for _, resolved in doc_links(doc, bundle):
            if resolved is not None and resolved.resolve() != doc.path.resolve():
                live_inbound.add(resolved.resolve())

    for doc in bundle.concepts:
        patterns, matched = matched_sources(doc, repo, tracked, gitlinks)
        if patterns and not matched:
            add("P001", doc, f"`sources` matches no tracked file: {patterns}. The code it described is gone")
        if is_retired(doc) and doc.path.resolve() not in live_inbound:
            add(
                "P002",
                doc,
                f"status `{doc.meta.get('status')}` and no live page links to it, so nothing relies on it",
            )
        missing = named_missing_paths(doc, tracked, gitlinks)
        if missing:
            add(
                "P003",
                doc,
                f"names {len(missing)} repo path(s) no tracked file has — renamed, removed, or an example",
                paths=missing[:PRUNE_PATHS_SHOWN],
            )
    return candidates


# ---------------------------------------------------------------------------
# index
# ---------------------------------------------------------------------------

INDEX_ENTRY_RE = re.compile(r"^\*\s+\[[^\]]*\]\(\s*([^)\s]+)\s*\)\s*(?:-\s*(.*))?$")


def existing_descriptions(index_path: Path) -> dict[str, str]:
    """Preserve hand-written descriptions for entries we cannot derive (subdirs)."""
    if not index_path.exists():
        return {}
    out = {}
    for line in index_path.read_text(encoding="utf-8").splitlines():
        m = INDEX_ENTRY_RE.match(line.strip())
        if m and m.group(2):
            out[m.group(1)] = m.group(2).strip()
    return out


def directory_contents(directory: Path, bundle: Bundle) -> tuple[list[Doc], list[Path]]:
    concepts = [d for d in bundle.concepts if d.path.parent == directory]
    subdirs = [
        c
        for c in sorted(directory.iterdir())
        if c.is_dir() and not c.name.startswith(".") and has_concepts(c)
    ]
    return concepts, subdirs


def render_index(directory: Path, bundle: Bundle) -> str:
    is_root = directory == bundle.root
    kept = existing_descriptions(directory / "index.md")
    concepts, subdirs = directory_contents(directory, bundle)

    groups: dict[str, list[Doc]] = {}
    for doc in concepts:
        groups.setdefault(doc.type or "Concept", []).append(doc)

    lines: list[str] = []
    if is_root:
        declared = next(
            (d.meta.get("okf_version") for d in bundle.indexes if d.path == directory / "index.md"), None
        )
        lines += ["---", f'okf_version: "{declared or OKF_VERSION}"', "---", ""]

    def entry_for(doc: Doc) -> str:
        entry = f"* [{doc.title}]({doc.path.name})"
        desc = doc.description or kept.get(doc.path.name, "")
        return f"{entry} - {desc}" if desc else entry

    for type_name in sorted(groups):
        by_title = sorted(groups[type_name], key=lambda d: d.title.lower())
        live = [d for d in by_title if str(d.meta.get("status", "")).lower() not in RETIRED_STATUS]
        retired = [d for d in by_title if d not in live]

        lines.append(f"# {type_name}")
        lines.append("")
        lines += [entry_for(doc) for doc in live]
        lines.append("")
        if retired:
            lines.append(f"## {RETIRED_HEADING}")
            lines.append("")
            lines += [entry_for(doc) for doc in retired]
            lines.append("")

    if subdirs:
        lines.append("# Subdirectories")
        lines.append("")
        for child in subdirs:
            target = f"{child.name}/"
            entry = f"* [{derive_title(child)}]({target})"
            desc = kept.get(target) or kept.get(f"{child.name}/index.md", "")
            if desc:
                entry += f" - {desc}"
            lines.append(entry)
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def index_dirs(bundle: Bundle) -> list[Path]:
    """Every directory that needs an index: concept/index dirs and all their
    ancestors up to the root, so an intermediate directory with only
    subdirectories still gets the index.md its parent's index links to."""
    dirs = {bundle.root}
    for doc in [*bundle.concepts, *bundle.indexes]:
        directory = doc.path.parent
        while directory != bundle.root:
            dirs.add(directory)
            directory = directory.parent
    return sorted(dirs)


def run_index(bundle: Bundle, write: bool) -> list[dict]:
    changes = []
    for directory in index_dirs(bundle):
        target = directory / "index.md"
        current = target.read_text(encoding="utf-8") if target.exists() else None
        if current is not None and MANUAL_MARKER in current:
            continue
        concepts, subdirs = directory_contents(directory, bundle)
        if not concepts and not subdirs and directory != bundle.root:
            # Nothing to render. Never truncate an existing index to an empty file.
            continue
        desired = render_index(directory, bundle)
        if current == desired:
            continue
        rel = str(target.relative_to(bundle.root)).replace(os.sep, "/")
        changes.append({"file": rel, "action": "create" if current is None else "update"})
        if write:
            target.write_text(desired, encoding="utf-8")
    return changes


# ---------------------------------------------------------------------------
# cli
# ---------------------------------------------------------------------------


def emit(payload: dict, as_json: bool, human) -> None:
    if as_json:
        json.dump(payload, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        human(payload)


def main() -> int:
    # Shared flags are accepted on either side of the subcommand: `okf.py --json
    # stale` and `okf.py stale --json` both work. SUPPRESS keeps the subparser
    # from clobbering a value already set before the subcommand.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--bundle", default=argparse.SUPPRESS, help="bundle root (default: ./wiki)")
    common.add_argument("--repo", default=argparse.SUPPRESS, help="repo the wiki documents")
    common.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help="machine-readable output")

    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--bundle", default="wiki", help="bundle root (default: ./wiki)")
    parser.add_argument("--repo", default=None, help="repo the wiki documents (default: git root of bundle)")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_lint = sub.add_parser("lint", parents=[common], help="conformance, links, orphans, index coverage")
    p_lint.add_argument("--strict", action="store_true", help="treat warnings as errors")

    p_stale = sub.add_parser("stale", parents=[common], help="git-derived staleness and coverage gaps")
    p_stale.add_argument(
        "--base",
        default=None,
        help="on a branch: judge its commits as one, as the default branch will see them "
        "once the branch is squashed (e.g. --base origin/main)",
    )

    p_pin = sub.add_parser(
        "pin", parents=[common], help="record the digest of the sources a page was written from"
    )
    p_pin.add_argument("pages", nargs="*", help="concept paths or ids; pin only pages whose sources you have read")
    p_pin.add_argument(
        "--migrate",
        action="store_true",
        help="convert every page that is current under its old `source_commit`",
    )

    sub.add_parser("prune", parents=[common], help="retirement candidates (advisory, read-only)")

    p_up = sub.add_parser("upgrade", parents=[common], help="rewrite v0.1 frontmatter as OKF v0.2")
    p_up.add_argument("--write", action="store_true", help="write changes (default: dry run)")

    p_index = sub.add_parser("index", parents=[common], help="regenerate index.md files")
    p_index.add_argument("--write", action="store_true", help="write changes (default: dry run)")

    args = parser.parse_args()

    root = Path(args.bundle).expanduser().resolve()
    if not root.is_dir():
        print(f"error: bundle root not found: {root}", file=sys.stderr)
        return 2

    if args.repo:
        repo = Path(args.repo).expanduser().resolve()
    else:
        code, out = git(root, "rev-parse", "--show-toplevel")
        repo = Path(out) if code == 0 else root

    bundle = load_bundle(root, repo)

    if args.cmd == "lint":
        errors, warnings = lint(bundle)

        def human(_):
            for item in errors:
                print(f"ERROR  {item['code']}  {item['file']}: {item['message']}")
            for item in warnings:
                print(f"warn   {item['code']}  {item['file']}: {item['message']}")
            print(
                f"\n{len(bundle.concepts)} concepts, {len(errors)} error(s), {len(warnings)} warning(s)"
            )
            if not errors:
                declared = next(
                    (d.meta.get("okf_version") for d in bundle.indexes if d.path.parent == bundle.root), None
                )
                print(f"conformant with OKF v{declared or OKF_VERSION}")

        emit({"errors": errors, "warnings": warnings}, args.json, human)
        return 1 if errors or (args.strict and warnings) else 0

    if args.cmd == "stale":
        result = stale(bundle, args.base)

        def human(res):
            for item in res["findings"]:
                print(f"{item['code']}  {item['concept']}: {item['message']}")
                for f in item.get("files", []):
                    print(f"        ~ {f}")
                for c in item.get("commits", []):
                    print(f"        · {c}")
            for gap in res["coverage_gaps"]:
                print(f"S004  {gap['path']}: {gap['count']} tracked file(s) no concept claims")
                for f in gap["sample"]:
                    print(f"        ? {f}")
            if not res["findings"] and not res["coverage_gaps"]:
                print("wiki is in sync with the repo")

        emit(result, args.json, human)
        return 1 if result["findings"] else 0

    if args.cmd == "pin":
        if bool(args.pages) == bool(args.migrate):
            print("error: name the pages to pin, or pass --migrate (not both)", file=sys.stderr)
            return 2
        result = pin(bundle, args.pages, args.migrate)

        def human(res):
            for item in res["pinned"]:
                print(f"pinned  {item['concept']}  {DIGEST_KEY}: {item[DIGEST_KEY]}")
                for f in item.get("untracked", []):
                    print(f"        counted untracked: {f}")
            for item in res["skipped"]:
                print(f"skipped {item['concept']}: {item['reason']}")
            if not res["pinned"] and not res["skipped"]:
                print("nothing to pin")

        emit(result, args.json, human)
        return 1 if result["skipped"] and not args.migrate else 0

    if args.cmd == "upgrade":
        changes = upgrade(bundle, write=args.write)

        def human(res):
            verb = "wrote" if args.write else "would change"
            for change in res["changes"]:
                print(f"{verb}: {change['file']}")
                for note in change["changes"]:
                    print(f"        {note}")
            if not res["changes"]:
                print("nothing to upgrade")

        emit({"changes": changes}, args.json, human)
        return 0 if args.write or not changes else 1

    if args.cmd == "prune":
        candidates = prune(bundle)

        def human(res):
            for item in res["candidates"]:
                print(f"{item['code']}  {item['concept']}: {item['message']}")
                for p in item.get("paths", []):
                    print(f"        ? {p}")
            if not res["candidates"]:
                print("no retirement candidates")

        emit({"candidates": candidates}, args.json, human)
        return 0

    if args.cmd == "index":
        changes = run_index(bundle, write=args.write)

        def human(res):
            for change in res["changes"]:
                verb = "wrote" if args.write else "would " + change["action"]
                print(f"{verb}: {change['file']}")
            if not res["changes"]:
                print("all index.md files up to date")

        emit({"changes": changes}, args.json, human)
        return 0 if args.write or not changes else 1

    return 2


if __name__ == "__main__":
    sys.exit(main())
