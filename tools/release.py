#!/usr/bin/env python3
"""Zips of the skills for hosts that install a skill by upload, and their releases.

    python3 tools/release.py check            exit 1 on any fault, with each named
    python3 tools/release.py pending          one "SKILL TAG" line per release due
    python3 tools/release.py build SKILL      writes dist/SKILL.zip, prints its path
    python3 tools/release.py notes SKILL      the release notes, on stdout

**Which skills get a zip is whatever README.md links to**, as
`.../releases/download/SKILL-vVERSION/SKILL.zip`. The link is the one thing a
reader follows, so it is also the list: a skill is offered by adding its link,
and a link cannot name a version the skill does not carry, because `check`
fails when it differs from the skill's `metadata.version`.

**A skill is released when its version changes.** Each is released on its own,
under the tag `SKILL-vVERSION`, since a web host's copy updates only when its
owner uploads it again, and a release that changed nothing would ask them to.
`pending` names every linked skill whose tag does not exist yet.

**The zip is built from the last commit, never from the folder on disk.** A
skill's folder collects files git ignores -- a plan and its photos from a run
made inside the checkout -- and `git archive` takes only what is tracked. Every
file is stamped with the time of the last commit that touched the skill, since
archiving a folder rather than a commit stamps the time it was built instead;
so an unchanged skill rebuilds to the same bytes. That needs `--mtime`, which
arrived in git 2.45. Zip keeps that time in the builder's local zone, so the
build runs in UTC, as CI does, and a zip made on a laptop matches the release.

Python 3.9, standard library only. It runs git, and writes only under dist/.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import zipfile

LINK = re.compile(
    r"/releases/download/(?P<skill>[a-z0-9-]+?)-v(?P<version>[0-9][0-9A-Za-z.-]*)"
    r"/(?P<file>[a-z0-9-]+)\.zip"
)
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)
NAME = re.compile(r"^name:\s*(\S+)\s*$", re.M)
METADATA = re.compile(r"^metadata:[ \t]*\n((?:[ \t]+.*\n?)+)", re.M)
VERSION = re.compile(r"^[ \t]+version:\s*[\"']?([^\"'\s]+)[\"']?\s*$", re.M)
MTIME_GIT = (2, 45)


def git(*args: str, env: dict[str, str] | None = None) -> str:
    return subprocess.run(
        ["git", *args], check=True, capture_output=True, text=True,
        env={**os.environ, **env} if env else None,
    ).stdout.strip()


def has_ref(ref: str) -> bool:
    return subprocess.run(
        ["git", "rev-parse", "-q", "--verify", ref], capture_output=True
    ).returncode == 0


def tag(skill: str, version: str) -> str:
    return f"{skill}-v{version}"


def linked() -> dict[str, str]:
    """Each skill README.md offers as a zip, and the version its link names."""
    with open("README.md", encoding="utf-8") as f:
        text = f.read()
    found: dict[str, str] = {}
    for m in LINK.finditer(text):
        skill, version = m["skill"], m["version"]
        if m["file"] != skill:
            sys.exit(f"README.md: {m[0]} names {m['file']}.zip under {skill}'s tag")
        if found.get(skill, version) != version:
            sys.exit(f"README.md: {skill} is linked at {found[skill]} and at {version}")
        found[skill] = version
    return found


def frontmatter(skill: str) -> tuple[str | None, str | None]:
    """The skill's name and metadata.version, as HEAD has them."""
    path = f"skills/{skill}/SKILL.md"
    if not has_ref(f"HEAD:{path}"):
        return None, None
    m = FRONTMATTER.match(git("show", f"HEAD:{path}") + "\n")
    if not m:
        return None, None
    name = NAME.search(m[1])
    block = METADATA.search(m[1])
    version = VERSION.search(block[1]) if block else None
    return (name[1] if name else None), (version[1] if version else None)


def git_version() -> tuple[int, ...]:
    m = re.search(r"(\d+)\.(\d+)", git("version"))
    return (int(m[1]), int(m[2])) if m else (0, 0)


def build(skill: str) -> str:
    if git_version() < MTIME_GIT:
        sys.exit(f"git {'.'.join(map(str, MTIME_GIT))} or newer is needed for --mtime")
    os.makedirs("dist", exist_ok=True)
    out = f"dist/{skill}.zip"
    mtime = git("log", "-1", "--format=%cI", "HEAD", "--", f"skills/{skill}")
    git(
        "-c", "core.autocrlf=false",
        "archive", "--format=zip", f"--prefix={skill}/", f"--mtime={mtime}",
        "-o", out, f"HEAD:skills/{skill}",
        env={"TZ": "UTC"},
    )
    return out


def layout_faults(skill: str, path: str) -> list[str]:
    """Where the zip is not the tracked folder, under a folder of the skill's name."""
    with zipfile.ZipFile(path) as z:
        files = {n for n in z.namelist() if not n.endswith("/")}
    tracked = {
        f"{skill}/{p}"
        for p in git("ls-tree", "-r", "--name-only", f"HEAD:skills/{skill}").splitlines()
    }
    faults = [f"{path}: {n} is not in the commit" for n in sorted(files - tracked)]
    faults += [f"{path}: {n} is missing" for n in sorted(tracked - files)]
    if f"{skill}/SKILL.md" not in files:
        faults.append(f"{path}: no {skill}/SKILL.md at the top")
    return faults


def notice(message: str) -> None:
    if os.environ.get("GITHUB_ACTIONS") == "true":
        print(f"::notice::{message}")
    else:
        print(f"note: {message}")


def check() -> int:
    offered = linked()
    if not offered:
        print("README.md links no skill zip")
    faults: list[str] = []
    for skill, version in sorted(offered.items()):
        name, own = frontmatter(skill)
        if name is None:
            faults.append(f"README.md links {skill}, which has no skills/{skill}/SKILL.md")
            continue
        if name != skill:
            faults.append(f"skills/{skill}/SKILL.md is named {name}")
        if own is None:
            faults.append(f"skills/{skill}/SKILL.md has no metadata.version")
        elif own != version:
            faults.append(f"README.md links {skill} v{version}; the skill is v{own}")
        faults += layout_faults(skill, build(skill))
        released = tag(skill, version)
        if has_ref(f"refs/tags/{released}") and (
            git("rev-parse", f"{released}:skills/{skill}")
            != git("rev-parse", f"HEAD:skills/{skill}")
        ):
            notice(
                f"{skill} changed since {released} and kept its version: the change "
                f"reaches the zip only when the version does"
            )
    for fault in faults:
        print(fault, file=sys.stderr)
    if not faults:
        print(f"ok: {', '.join(f'{s} v{v}' for s, v in sorted(offered.items()))}")
    return 1 if faults else 0


def pending() -> int:
    for skill, version in sorted(linked().items()):
        if not has_ref(f"refs/tags/{tag(skill, version)}"):
            print(skill, tag(skill, version))
    return 0


def notes(skill: str) -> int:
    version = linked().get(skill)
    if version is None:
        sys.exit(f"README.md links no zip for {skill}")
    lines = [f"`{skill}.zip` below is {skill} v{version}, to upload to a host that "
             f"installs a skill from a zip: README.md says how."]
    # The glob alone would also take foo-viewer-v1.0 as one of foo's tags.
    own = re.compile(re.escape(skill) + r"-v[0-9][0-9A-Za-z.-]*")
    previous = next(
        (t for t in git("tag", "--merged", "HEAD", "--sort=-creatordate",
                        "--list", f"{skill}-v*").splitlines()
         if own.fullmatch(t)),
        "",
    )
    if previous:
        changes = git("log", "--format=- %s", f"{previous}..HEAD", "--", f"skills/{skill}")
        lines += ["", f"Changed since {previous}:", "", changes or "- nothing in the skill's files"]
    else:
        lines += ["", "The first release of this skill as a zip."]
    print("\n".join(lines))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check")
    sub.add_parser("pending")
    for command in ("build", "notes"):
        sub.add_parser(command).add_argument("skill")
    args = parser.parse_args()
    os.chdir(git("rev-parse", "--show-toplevel"))
    if args.command == "check":
        return check()
    if args.command == "pending":
        return pending()
    if args.command == "build":
        print(build(args.skill))
        return 0
    return notes(args.skill)


if __name__ == "__main__":
    sys.exit(main())
