#!/usr/bin/env python3
"""Z-Image Turbo on an Apple Silicon Mac: check the machine, set it up, generate images.

    python3 z_image_turbo.py check
    python3 z_image_turbo.py setup
    python3 z_image_turbo.py generate --prompt '...' --out picture.jpg
    python3 z_image_turbo.py generate --jobs jobs.json --out-dir images

One model, mflux-community/z-image-turbo-mflux-q8 at a pinned revision, run by
mflux on the Mac's GPU. `check` and `setup` run on any Python 3.9 or newer,
standard library only. `generate` validates its input there too, then re-runs
itself under the Python 3.12-3.14 environment `setup` built, where mflux is.

Only `setup` uses the network: it installs mflux and its pinned dependencies
into its own environment and downloads the model into the Hugging Face cache.
`generate` loads the model with the hub switched offline, so it never downloads.

Exit status:
    check     0 ready; 1 this Mac can run it, and `setup` has work to do;
              3 this machine cannot run it, or cannot until something is fixed.
    setup     0 ready; 1 a step failed, and a re-run resumes; 2 run without
              --yes, so nothing was downloaded; 3 this machine cannot run it,
              or setup refuses to go on.
    generate  0 every job has its image; 1 some have none (failed, interrupted,
              stopped on low battery or a full disk), and a re-run draws only
              those; 2 the command or the jobs file is wrong, nothing was drawn;
              3 it cannot run: not set up, or the model would not load.
    any       4 an unexpected error: a fault in this script, not worth a retry.
"""

from __future__ import annotations

import argparse
import errno
import hashlib
import json
import math
import os
import platform
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

MODEL_REPO = "mflux-community/z-image-turbo-mflux-q8"
MODEL_REVISION = "4430e72e37bf2bc7bc889a42d306ae1b8d3b22de"

# Every file mflux loads, with its size at MODEL_REVISION. The revision is
# pinned, so the sizes are too, and a complete download can be told from a
# partial one with the standard library alone.
MODEL_FILES = {
    "text_encoder/0.safetensors": 2145936704,
    "text_encoder/1.safetensors": 2128216857,
    "text_encoder/model.safetensors.index.json": 51332,
    "tokenizer/chat_template.jinja": 4168,
    "tokenizer/tokenizer_config.json": 692,
    "tokenizer/tokenizer.json": 11422650,
    "transformer/0.safetensors": 2134613189,
    "transformer/1.safetensors": 2146080675,
    "transformer/2.safetensors": 2130413997,
    "transformer/3.safetensors": 129578808,
    "transformer/model.safetensors.index.json": 61606,
    "vae/0.safetensors": 165702761,
    "vae/model.safetensors.index.json": 17378,
}
MODEL_BYTES = sum(MODEL_FILES.values())

HERE = Path(__file__).resolve().parent
REQUIREMENTS = HERE / "requirements.txt"
CONSTRAINTS = HERE / "constraints.txt"
MFLUX_VERSION = "0.19.0"  # keep equal to the pin in requirements.txt

# Measured: the built environment takes 1.42 GB; what pip downloads is less.
PACKAGES_BYTES = 1_400_000_000
# Room on top of what is downloaded, for pip's unpacking and the cache's own files.
DISK_HEADROOM = 1_000_000_000
# Generating one megapixel peaks at about 18 GB of unified memory (measured,
# with MLX_CACHE_LIMIT). Below 24 GB, with macOS's own share, the Mac swaps.
MIN_MEMORY_BYTES = 24 * 1024**3
MLX_CACHE_LIMIT = 1000**3
# The pinned packages have wheels for these Pythons only (constraints.txt), and
# MLX's wheels need macOS 14 or later.
MIN_PYTHON, MAX_PYTHON = (3, 12), (3, 14)
MIN_MACOS = 14
PYTHON_CANDIDATES = [f"python3.{m}" for m in range(MAX_PYTHON[1], MIN_PYTHON[1] - 1, -1)] + ["python3"]
# Where Homebrew puts a native arm64 Python; a host's PATH often lacks it.
HOMEBREW_BIN = Path("/opt/homebrew/bin")
# Written into the environment by `setup` before anything else, holding a hash
# of the pins it was built from: the only folder setup will ever delete, and the
# way it tells an environment built from older pins, which it rebuilds.
VENV_MARKER = ".z-image-turbo-macos"
# Probing an interpreter is instant; a first run after an update can take a few
# seconds to compile. Past these, the interpreter is treated as unusable.
PROBE_TIMEOUT, VENV_PROBE_TIMEOUT = 20, 60

GB = 1000**3
EXIT_OK, EXIT_PARTIAL, EXIT_USAGE, EXIT_CANNOT, EXIT_UNEXPECTED = 0, 1, 2, 3, 4

sys.dont_write_bytecode = True


# --- where things live ------------------------------------------------------


def env_path(name: str) -> Path | None:
    value = os.environ.get(name)
    return Path(os.path.expandvars(value)).expanduser() if value else None


def cache_home() -> Path:
    return env_path("XDG_CACHE_HOME") or Path.home() / ".cache"


def skill_cache() -> Path:
    return cache_home() / "z-image-turbo-macos"


def venv_dir() -> Path:
    """The environment `setup` builds. Outside the skill's folder on purpose:
    reinstalling or updating the skill replaces that folder, and a 1.4 GB
    environment inside it would be rebuilt every time."""
    return env_path("Z_IMAGE_TURBO_VENV") or skill_cache() / "venv"


def pins_hash() -> str:
    """What the environment should be built from; kept in its marker."""
    digest = hashlib.sha256(REQUIREMENTS.read_bytes() + b"\0" + CONSTRAINTS.read_bytes())
    return digest.hexdigest()


def marker_hash() -> str | None:
    try:
        return (venv_dir() / VENV_MARKER).read_text().split()[0]
    except (OSError, IndexError):
        return None


def venv_python() -> Path:
    return venv_dir() / "bin" / "python"


def hf_hub_cache() -> Path:
    """The Hugging Face hub cache, resolved the way huggingface_hub does."""
    for name in ("HF_HUB_CACHE", "HUGGINGFACE_HUB_CACHE"):
        path = env_path(name)
        if path:
            return path
    home = env_path("HF_HOME")
    return home / "hub" if home else cache_home() / "huggingface" / "hub"


def model_snapshot() -> Path:
    name = "models--" + MODEL_REPO.replace("/", "--")
    return hf_hub_cache() / name / "snapshots" / MODEL_REVISION


# --- the machine ------------------------------------------------------------


def sysctl(name: str) -> str:
    try:
        out = subprocess.run(["sysctl", "-n", name], capture_output=True, text=True, check=True)
        return out.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def macos_major() -> int | None:
    try:
        return int(platform.mac_ver()[0].split(".")[0])
    except ValueError:
        return None


def platform_problem() -> str | None:
    """Why this machine cannot run the model at all, or None."""
    if platform.system() != "Darwin":
        return f"this is {platform.system() or 'an unknown system'}, and the model runs only on macOS"
    # hw.optional.arm64 is 1 on Apple Silicon even when this Python runs under
    # Rosetta, where platform.machine() would say x86_64.
    if sysctl("hw.optional.arm64") != "1":
        return "this Mac has an Intel processor, and the model runs only on Apple Silicon (M1 or later)"
    major = macos_major()
    if major is not None and major < MIN_MACOS:
        return f"this Mac runs macOS {platform.mac_ver()[0]}, and the model needs macOS {MIN_MACOS} or later"
    return None


def describe_mac() -> str:
    chip = sysctl("machdep.cpu.brand_string") or "Apple Silicon"
    return f"macOS {platform.mac_ver()[0] or '?'}, {chip}"


def memory_bytes() -> int:
    try:
        return int(sysctl("hw.memsize"))
    except ValueError:
        return 0


def probe_python(exe: str) -> tuple[tuple[int, int], str] | None:
    """(major, minor) and machine of an interpreter, or None if it won't run."""
    code = "import sys, platform; print(sys.version_info[0], sys.version_info[1], platform.machine())"
    try:
        out = subprocess.run([exe, "-c", code], capture_output=True, text=True,
                             timeout=PROBE_TIMEOUT, check=True)
        major, minor, machine = out.stdout.split()
        return (int(major), int(minor)), machine
    except (OSError, subprocess.SubprocessError, ValueError):
        return None


def find_python() -> tuple[str, tuple[int, int]] | None:
    """The newest native arm64 Python in the supported range. An x86_64 one (an
    Intel Homebrew under /usr/local) would install packages MLX has no build for,
    and one outside the range has no wheels for the pinned packages."""
    seen = set()
    found = []
    for name in PYTHON_CANDIDATES:
        for exe in (shutil.which(name), str(HOMEBREW_BIN / name)):
            if not exe or not os.access(exe, os.X_OK):
                continue
            real = os.path.realpath(exe)
            if real in seen:
                continue
            seen.add(real)
            probed = probe_python(exe)
            if probed and MIN_PYTHON <= probed[0] <= MAX_PYTHON and probed[1] == "arm64":
                found.append((probed[0], exe))
    if not found:
        return None
    version, exe = max(found)
    return exe, version


def python_range() -> str:
    return f"{MIN_PYTHON[0]}.{MIN_PYTHON[1]} to {MAX_PYTHON[0]}.{MAX_PYTHON[1]}"


# --- what is installed ------------------------------------------------------


def packages_ready(deep: bool = False) -> bool:
    """Whether the environment was built from the current pins and has mflux.
    `deep` also imports MLX and mflux, which catches a broken install at the
    cost of a few seconds; `generate` skips it and reports a failed load instead."""
    py = venv_python()
    if not py.exists() or marker_hash() != pins_hash():
        return False
    code = "import importlib.metadata as m; print(m.version('mflux'))"
    if deep:
        code = "import mlx.core, mflux; " + code
    try:
        out = subprocess.run([str(py), "-c", code], capture_output=True, text=True,
                             timeout=VENV_PROBE_TIMEOUT, check=True)
    except (OSError, subprocess.SubprocessError):
        return False
    return out.stdout.strip() == MFLUX_VERSION


def model_missing_bytes() -> int:
    """Bytes of the model not yet in the cache at the pinned revision; 0 when
    it is complete. A file of the wrong size counts as missing."""
    snap = model_snapshot()
    missing = 0
    for rel, size in MODEL_FILES.items():
        try:
            if (snap / rel).stat().st_size == size:
                continue
        except OSError:
            pass
        missing += size
    return missing


def free_bytes(path: Path) -> int:
    probe = path
    while not probe.exists() and probe != probe.parent:
        probe = probe.parent
    return shutil.disk_usage(probe).free


def gb(n: int) -> str:
    return f"{n / GB:.1f} GB"


def venv_refusal() -> str | None:
    """Why `setup` must not replace what is at the environment's path, or None.
    It deletes only a folder it made itself, so a path the user pointed
    Z_IMAGE_TURBO_VENV at by mistake is never emptied."""
    venv = venv_dir()
    if not venv.is_absolute():
        return f"Z_IMAGE_TURBO_VENV is {venv}; make it an absolute path"
    if venv.is_symlink():
        return f"{venv} is a link; point Z_IMAGE_TURBO_VENV at a real folder"
    if not venv.exists() or (venv / VENV_MARKER).exists():
        return None
    if venv.is_dir() and not any(venv.iterdir()):
        return None
    return f"{venv} already exists and setup did not make it; point Z_IMAGE_TURBO_VENV at a new folder"


# --- check ------------------------------------------------------------------


def writable_ancestor(path: Path) -> bool:
    """Whether `path`, or the nearest folder above it that exists, can be written."""
    probe = path
    while not probe.exists() and probe != probe.parent:
        probe = probe.parent
    return os.access(probe, os.W_OK)


def survey() -> tuple[int, int, list[tuple[str, str, str]]]:
    """Look at the machine and what is installed, once. Returns the exit code,
    the bytes setup still needs, and one (label, state, detail) row per finding."""
    rows = []

    problem = platform_problem()
    if problem:
        rows.append(("platform", "no", problem))
        return EXIT_CANNOT, 0, rows
    rows.append(("platform", "ok", describe_mac()))

    mem = memory_bytes()
    if mem and mem < MIN_MEMORY_BYTES:
        rows.append(("memory", "low", f"{mem / 1024**3:.0f} GB; generating peaks at about 18 GB, "
                                      "so expect swapping and much slower images"))
    else:
        rows.append(("memory", "ok", f"{mem / 1024**3:.0f} GB" if mem else "unknown"))

    needs = 0
    if packages_ready(deep=True):
        rows.append(("packages", "ready", f"mflux {MFLUX_VERSION} in {venv_dir()}"))
    else:
        refusal = venv_refusal()
        if refusal is None and not writable_ancestor(venv_dir()):
            refusal = f"cannot write to {venv_dir()} or the folder above it"
        if refusal:
            rows.append(("packages", "no", refusal))
            return EXIT_CANNOT, 0, rows
        py = find_python()
        if py is None:
            rows.append(("python", "no", f"no native Python {python_range()} found; install one "
                                         "(Homebrew's `brew install python` is one way) and check again"))
            return EXIT_CANNOT, 0, rows
        rows.append(("python", "ok", f"{py[0]} ({py[1][0]}.{py[1][1]})"))
        rows.append(("packages", "missing", f"setup installs mflux {MFLUX_VERSION} into {venv_dir()} "
                                            f"(about {gb(PACKAGES_BYTES)} on disk)"))
        needs += PACKAGES_BYTES

    missing = model_missing_bytes()
    if missing == 0:
        rows.append(("model", "ready", f"{MODEL_REPO} ({gb(MODEL_BYTES)})"))
    elif not writable_ancestor(hf_hub_cache()):
        rows.append(("model", "no", f"cannot write to {hf_hub_cache()}, where the model goes"))
        return EXIT_CANNOT, 0, rows
    else:
        rows.append(("model", "missing", f"setup downloads {gb(missing)} of {MODEL_REPO} into {hf_hub_cache()}"))
        needs += missing

    if needs:
        free = min(free_bytes(venv_dir()), free_bytes(hf_hub_cache()))
        state = "ok" if free >= needs + DISK_HEADROOM else "short"
        rows.append(("disk", state, f"{gb(free)} free, setup needs {gb(needs + DISK_HEADROOM)}"))
        return (EXIT_PARTIAL if state == "ok" else EXIT_CANNOT), needs, rows
    return EXIT_OK, 0, rows


def print_rows(rows, stream=sys.stdout) -> None:
    for label, state, detail in rows:
        print(f"{label:<9} {state:<8} {detail}", file=stream, flush=True)


def cmd_check(_args: argparse.Namespace) -> int:
    code, needs, rows = survey()
    print_rows(rows)
    if code == EXIT_CANNOT:
        print("cannot run here: see the line marked no or short")
    elif code == EXIT_PARTIAL:
        print(f"setup needed: it downloads up to {gb(needs)}, once; "
              "ask the user, then run `setup --yes`")
    else:
        print("ready")
    return code


# --- setup ------------------------------------------------------------------


def cmd_setup(args: argparse.Namespace) -> int:
    code, needs, rows = survey()
    if code == EXIT_CANNOT:
        print_rows(rows, sys.stderr)
        print("cannot set up: see the line marked no or short", file=sys.stderr)
        return EXIT_CANNOT
    if code == EXIT_OK:
        print("ready")
        return EXIT_OK
    if not args.yes:
        # The download is the user's to agree to, and the flag is how the host
        # says it asked: without it, setup only says what it would fetch.
        print(f"error: setup downloads up to {gb(needs)}; ask the user first, "
              "then run `setup --yes`", file=sys.stderr)
        return EXIT_USAGE

    import fcntl

    venv = venv_dir()
    try:
        skill_cache().mkdir(parents=True, exist_ok=True)
        lock = open(skill_cache() / "setup.lock", "w")
    except OSError as exc:
        print(f"cannot set up: cannot write to {skill_cache()}: {exc.strerror}", file=sys.stderr)
        return EXIT_CANNOT
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print("[setup] another setup is already running; wait for it to finish", file=sys.stderr)
        return EXIT_PARTIAL

    if not packages_ready(deep=True):
        py = find_python()
        assert py is not None  # survey() returned EXIT_CANNOT otherwise
        print(f"[setup] building {venv} with {py[0]}", flush=True)
        try:
            if (venv / VENV_MARKER).exists():
                shutil.rmtree(venv)  # ours: half-built, broken, or from older pins
            # The marker goes in first, so an environment interrupted while it
            # is built is still recognisably setup's, and is rebuilt next time.
            venv.mkdir(parents=True, exist_ok=True)
            (venv / VENV_MARKER).write_text(f"{pins_hash()}\nmade by z_image_turbo.py setup; safe to delete\n")
            if subprocess.run([py[0], "-m", "venv", str(venv)]).returncode != 0:
                raise OSError(errno.EIO, "python -m venv failed")
        except OSError as exc:
            print(f"[setup] failed: could not build {venv}: {exc.strerror or exc}", file=sys.stderr)
            return EXIT_PARTIAL
        pip = [str(venv_python()), "-m", "pip", "install", "--disable-pip-version-check",
               # A package with no wheel for this Mac fails here in seconds,
               # rather than after a long, doomed build from source.
               "--only-binary=:all:", "-r", str(REQUIREMENTS), "-c", str(CONSTRAINTS)]
        if subprocess.run(pip).returncode != 0 or not packages_ready(deep=True):
            print("[setup] failed: the packages did not install; the lines above say why", file=sys.stderr)
            return EXIT_PARTIAL
        print(f"[setup] mflux {MFLUX_VERSION} installed", flush=True)

    missing = model_missing_bytes()
    if missing:
        print(f"[setup] downloading {gb(missing)} of {MODEL_REPO} into {hf_hub_cache()}; "
              "this is the long part, and a re-run resumes it", flush=True)
        code = subprocess.run([str(venv_python()), str(Path(__file__).resolve()), "_download"]).returncode
        if code != 0 or model_missing_bytes():
            print("[setup] failed: the model download did not complete; the line above says why",
                  file=sys.stderr)
            return EXIT_PARTIAL
    print("ready")
    return EXIT_OK


def cmd_download(_args: argparse.Namespace) -> int:
    """Runs inside the environment, where huggingface_hub is. Not for callers."""
    from huggingface_hub import snapshot_download

    try:
        snapshot_download(repo_id=MODEL_REPO, revision=MODEL_REVISION, allow_patterns=list(MODEL_FILES))
    except KeyboardInterrupt:
        print("[setup] download interrupted", file=sys.stderr)
        return EXIT_PARTIAL
    except Exception as exc:  # network, disk and hub errors come from several libraries
        if isinstance(exc, OSError) and exc.errno == errno.ENOSPC:
            reason = "the disk is full"
        else:
            reason = f"{type(exc).__name__}: {str(exc).splitlines()[0] if str(exc) else 'no detail'}"
        print(f"[setup] download failed: {reason}", file=sys.stderr)
        return EXIT_PARTIAL
    return EXIT_OK


# --- generate: input --------------------------------------------------------

SUFFIXES = {".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG", ".webp": "WEBP"}
# Z-Image's VAE downsamples by 8 and its transformer takes 2x2 patches, so a
# side must be a multiple of 16. The model is trained around one megapixel; the
# bounds are the smallest and largest sizes this skill has run, and a smaller or
# larger final image comes from --resize.
SIDE_STEP, SIDE_MIN, SIDE_MAX = 16, 256, 1536
# Past four times the largest drawing, --resize only enlarges blur, and a typo
# such as 100000x100000 would ask Pillow for tens of gigabytes per image.
RESIZE_MAX = 4 * SIDE_MAX
DEFAULT_PIXELS = 1024 * 1024
# Seeds are 32-bit: what the prompt hash gives, and far below MLX's own limit.
SEED_MAX = 2**32 - 1
# The turbo model is tuned for single-digit step counts; the bound catches typos.
STEPS_MAX = 50


class UsageError(Exception):
    pass


def parse_size(text: str, flag: str, model_side: bool) -> tuple[int, int]:
    try:
        w, h = (int(p) for p in text.lower().split("x"))
    except ValueError:
        raise UsageError(f"{flag} takes WIDTHxHEIGHT, like 1024x1024 (got {text!r})")
    if w <= 0 or h <= 0:
        raise UsageError(f"{flag} must be positive (got {text})")
    if not model_side and max(w, h) > RESIZE_MAX:
        raise UsageError(f"{flag} sides can be at most {RESIZE_MAX} (got {text})")
    if model_side:
        for side in (w, h):
            if side % SIDE_STEP or not SIDE_MIN <= side <= SIDE_MAX:
                raise UsageError(
                    f"{flag} sides must be multiples of {SIDE_STEP} between {SIDE_MIN} and {SIDE_MAX} "
                    f"(got {text}); leave --size out and give --resize to get another final size"
                )
    return w, h


def size_for(shape: tuple[int, int]) -> tuple[int, int]:
    """About one megapixel in the given shape, each side a multiple of 16: what
    the model draws best, so that --resize crops away as little as it can."""
    ratio = shape[0] / shape[1]
    def side(x: float) -> int:
        return min(SIDE_MAX, max(SIDE_MIN, SIDE_STEP * round(x / SIDE_STEP)))
    w, h = math.sqrt(DEFAULT_PIXELS * ratio), math.sqrt(DEFAULT_PIXELS / ratio)
    # Clamp the long side first and derive the short one from it, so an extreme
    # shape keeps as much of its ratio as the bounds allow.
    if w >= h:
        w = side(w)
        return w, side(w / ratio)
    h = side(h)
    return side(h * ratio), h


def upscale(size: tuple[int, int], resize: tuple[int, int]) -> float:
    """How much --resize enlarges the part of the drawing it keeps."""
    kept_w = min(size[0], size[1] * resize[0] / resize[1])
    return resize[0] / kept_w


def default_seed(prompt: str, out: str) -> int:
    """A seed from the prompt and `out` as written, not the job's place in the
    list: reordering jobs changes nothing, the same job redraws the same image,
    and two files with one prompt get two different images. `out` as written,
    not resolved, so the same jobs file gives the same images from any folder."""
    digest = hashlib.sha256(f"{prompt}\n{out}".encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big")


def load_jobs(args: argparse.Namespace) -> list[dict]:
    if args.jobs:
        try:
            raw = json.loads(Path(args.jobs).expanduser().read_text(encoding="utf-8"))
        except OSError as exc:
            raise UsageError(f"cannot read {args.jobs}: {exc.strerror}")
        except UnicodeDecodeError:
            raise UsageError(f"{args.jobs} is not UTF-8 text")
        except json.JSONDecodeError as exc:
            raise UsageError(f"{args.jobs} is not valid JSON: {exc}")
        if not isinstance(raw, list) or not raw:
            raise UsageError(f"{args.jobs} must hold a non-empty JSON list of jobs")
    else:
        raw = [{"prompt": args.prompt, "out": args.out}]
        if args.seed is not None:
            raw[0]["seed"] = args.seed

    out_dir = Path(args.out_dir).expanduser()
    if out_dir.exists() and not out_dir.is_dir():
        raise UsageError(f"--out-dir {args.out_dir} is a file, not a folder")
    jobs, seen_paths, seen_images = [], {}, {}
    for i, job in enumerate(raw, 1):
        where = f"job {i}" if args.jobs else "the command"
        if not isinstance(job, dict):
            raise UsageError(f"{where} must be an object with \"prompt\" and \"out\"")
        unknown = set(job) - {"prompt", "out", "seed"}
        if unknown:
            raise UsageError(f"{where} has unknown key(s) {sorted(unknown)}; allowed: prompt, out, seed")
        prompt = job.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            raise UsageError(f"{where} needs a non-empty \"prompt\"")
        prompt = prompt.strip()
        try:
            prompt.encode("utf-8")
        except UnicodeEncodeError:
            raise UsageError(f"{where}: the prompt holds characters that are not valid text")
        out = job.get("out")
        if not isinstance(out, str) or not out.strip():
            raise UsageError(f"{where} needs an \"out\" path")
        path = Path(out).expanduser()
        path = (path if path.is_absolute() else out_dir / path).resolve()
        if path.suffix.lower() not in SUFFIXES:
            raise UsageError(f"{where}: \"out\" must end in .jpg, .jpeg, .png or .webp (got {out!r})")
        if path.is_dir():
            raise UsageError(f"{where}: \"out\" {out!r} is a folder")
        key = str(path).casefold()  # the Mac's disks ignore case: X.jpg is x.jpg
        if key in seen_paths:
            raise UsageError(f"{where} writes {path}, which job {seen_paths[key]} already writes")
        seen_paths[key] = i
        seed = job.get("seed")
        if seed is None:
            seed = default_seed(prompt, out.strip())
        elif not isinstance(seed, int) or isinstance(seed, bool) or not 0 <= seed <= SEED_MAX:
            raise UsageError(f"{where}: \"seed\" must be a whole number from 0 to {SEED_MAX}")
        if (prompt, seed) in seen_images:
            raise UsageError(f"{where} would draw the same image as job {seen_images[(prompt, seed)]}: "
                             "same prompt, same seed; give one of them another seed")
        seen_images[(prompt, seed)] = i
        jobs.append({"prompt": prompt, "path": path, "seed": seed})
    return jobs


def finished(path: Path) -> bool:
    """An image already there: a JPEG, PNG or WebP by its first bytes. Anything
    else at the path, empty or not an image, is generated over."""
    try:
        with open(path, "rb") as f:
            head = f.read(12)
    except OSError:
        return False
    return (head[:3] == b"\xff\xd8\xff" or head[:8] == b"\x89PNG\r\n\x1a\n"
            or (head[:4] == b"RIFF" and head[8:12] == b"WEBP"))


def show(path: Path) -> str:
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)


def in_environment() -> bool:
    try:
        return Path(sys.prefix).resolve() == venv_dir().resolve()
    except OSError:
        return False


def prepare_folders(jobs: list[dict]) -> None:
    """Make every output's folder and confirm it can be written, before the
    model spends a minute on an image that could not be saved."""
    for folder in sorted({j["path"].parent for j in jobs}):
        try:
            folder.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise UsageError(f"cannot make {folder}: {exc.strerror}")
        if not os.access(folder, os.W_OK):
            raise UsageError(f"cannot write to {folder}")


# --- generate: drawing ------------------------------------------------------


def fit(image, size: tuple[int, int]):
    """Centre-crop to the target's shape, then scale to it."""
    from PIL import Image

    tw, th = size
    w, h = image.size
    if w * th > h * tw:
        cw = round(h * tw / th)
        image = image.crop(((w - cw) // 2, 0, (w - cw) // 2 + cw, h))
    elif w * th < h * tw:
        ch = round(w * th / tw)
        image = image.crop((0, (h - ch) // 2, w, (h - ch) // 2 + ch))
    return image.resize(size, Image.LANCZOS) if image.size != size else image


def save(image, path: Path, quality: int) -> None:
    fmt = SUFFIXES[path.suffix.lower()]
    options = {"PNG": {"optimize": True},
               "JPEG": {"quality": quality, "optimize": True, "progressive": True},
               "WEBP": {"quality": quality, "method": 6}}[fmt]
    # Written aside, flushed to disk and renamed, so neither an interrupt nor a
    # power cut leaves a file the next run would take for a finished image.
    partial = path.with_name(f".{path.name}.partial")
    try:
        with open(partial, "wb") as f:
            image.convert("RGB").save(f, fmt, **options)
            f.flush()
            os.fsync(f.fileno())
        os.replace(partial, path)
    finally:
        if partial.exists():
            partial.unlink()


def draw(jobs: list[dict], size: tuple[int, int], args: argparse.Namespace) -> int:
    t0 = time.monotonic()
    print(f"[gen] loading {MODEL_REPO}", flush=True)
    try:
        import mlx.core as mx
        from mflux.callbacks.instances.battery_saver import BatterySaver
        from mflux.models.common.config.model_config import ModelConfig
        from mflux.models.z_image import ZImage
        from mflux.utils.exceptions import StopImageGenerationException

        # MLX otherwise keeps freed buffers for reuse until memory runs short:
        # measured at one megapixel, the peak footprint was 34 GB uncapped and
        # 18 GB with this cap, at the same speed. 1 GB is mflux's own low-RAM value.
        mx.set_cache_limit(MLX_CACHE_LIMIT)
        model = ZImage(model_path=str(model_snapshot()), model_config=ModelConfig.z_image_turbo())
        # Stops before the next image once a MacBook on battery reaches 10%;
        # what is finished is kept, and a re-run on power resumes. Twice mflux's
        # own 5%, because a batch runs unattended and the user still has to
        # find it stopped and plug in.
        model.callbacks.register(BatterySaver(battery_percentage_stop_limit=10))
    except KeyboardInterrupt:
        print("[gen] interrupted while loading the model; nothing was generated", flush=True)
        return EXIT_PARTIAL
    except Exception as exc:  # import and load errors come from mlx, mflux and safetensors
        print(f"cannot run: the model would not load: {type(exc).__name__}: {exc}", file=sys.stderr)
        return EXIT_CANNOT
    print(f"[gen] model loaded in {time.monotonic() - t0:.0f}s", flush=True)

    resize = parse_size(args.resize, "--resize", False) if args.resize else None
    made = 0
    stopped = None
    for n, job in enumerate(jobs, 1):
        if stopped:
            print(f"stop  {show(job['path'])}: not started, the batch stopped", flush=True)
            continue
        t = time.monotonic()
        try:
            result = model.generate_image(seed=job["seed"], prompt=job["prompt"],
                                          num_inference_steps=args.steps, width=size[0], height=size[1])
            image = result.image
            save(fit(image, resize) if resize else image, job["path"], args.quality)
        except (StopImageGenerationException, KeyboardInterrupt) as exc:
            stopped = str(exc) or "interrupted"
            print(f"stop  {show(job['path'])}: {stopped}", flush=True)
            continue
        except OSError as exc:
            if exc.errno == errno.ENOSPC:
                stopped = "the disk is full"
                print(f"stop  {show(job['path'])}: {stopped}", flush=True)
                continue
            print(f"fail  {show(job['path'])}: {exc}", flush=True)
        except Exception as exc:
            print(f"fail  {show(job['path'])}: {type(exc).__name__}: {exc}", flush=True)
        else:
            made += 1
            kb = job["path"].stat().st_size / 1024
            print(f"made  {show(job['path'])}  ({kb:.0f} KB, {time.monotonic() - t:.0f}s, "
                  f"{n}/{len(jobs)})", flush=True)
        # Without this, peak memory creeps up over a long batch.
        mx.clear_cache()

    missing = len(jobs) - made
    print(f"[gen] {made} made, {missing} without an image, in {time.monotonic() - t0:.0f}s", flush=True)
    return EXIT_OK if missing == 0 else EXIT_PARTIAL


def cmd_generate(args: argparse.Namespace) -> int:
    try:
        if bool(args.jobs) == bool(args.prompt):
            raise UsageError("give either --jobs FILE, or --prompt TEXT with --out PATH")
        if args.prompt and not args.out:
            raise UsageError("--prompt needs --out PATH")
        if args.jobs and (args.out or args.seed is not None):
            raise UsageError("with --jobs, put \"out\" and \"seed\" in each job instead")
        resize = parse_size(args.resize, "--resize", False) if args.resize else None
        if args.size:
            size = parse_size(args.size, "--size", True)
        else:
            size = size_for(resize) if resize else size_for((1, 1))
        if not 1 <= args.quality <= 100:
            raise UsageError("--quality must be from 1 to 100")
        if not 1 <= args.steps <= STEPS_MAX:
            raise UsageError(f"--steps must be from 1 to {STEPS_MAX}")
        jobs = load_jobs(args)
    except UsageError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_USAGE

    if resize and upscale(size, resize) > 1.05:
        print(f"note: --resize {resize[0]}x{resize[1]} enlarges the drawing {upscale(size, resize):.1f}x, "
              "so the images will be soft", file=sys.stderr)
    pending = [j for j in jobs if args.force or not finished(j["path"])]
    if args.dry_run or not pending:
        for job in jobs:
            if job in pending:
                print(f"draw  {show(job['path'])}  {size[0]}x{size[1]}  seed={job['seed']}  "
                      f"{job['prompt'][:80]}")
            else:
                print(f"have  {show(job['path'])}")
        return EXIT_OK

    problem = platform_problem()
    if problem:
        print(f"cannot run here: {problem}", file=sys.stderr)
        return EXIT_CANNOT
    if model_missing_bytes():
        print("cannot run: the model is not downloaded; run `check`, then `setup`", file=sys.stderr)
        return EXIT_CANNOT

    # Before mflux is imported, in this process or the one it becomes:
    # huggingface_hub reads the first once, at import, and the second silences
    # mflux's per-step progress bars, which would bury the per-image lines.
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TQDM_DISABLE"] = "1"
    if not in_environment():
        # Become the environment's Python, once; it validates everything again.
        if os.environ.get("_Z_IMAGE_TURBO_REEXEC") or not packages_ready():
            print("cannot run: mflux is not installed; run `check`, then `setup`", file=sys.stderr)
            return EXIT_CANNOT
        os.environ["_Z_IMAGE_TURBO_REEXEC"] = "1"
        py = str(venv_python())
        os.execv(py, [py, str(Path(__file__).resolve()), *sys.argv[1:]])

    try:
        prepare_folders(pending)
    except UsageError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_USAGE
    for job in jobs:
        if job not in pending:
            print(f"have  {show(job['path'])}", flush=True)
    return draw(pending, size, args)


# --- command line -----------------------------------------------------------


def on_sigterm(_signum, _frame):
    # A host stopping a background run sends SIGTERM; treat it as Ctrl-C, so the
    # batch stops cleanly and keeps what is finished.
    raise KeyboardInterrupt


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True, metavar="{check,setup,generate}")
    sub.add_parser("check", help="say whether this Mac can run the model, and what setup would download")
    s = sub.add_parser("setup", help="install mflux and download the model (network, about 12 GB, once)")
    s.add_argument("--yes", action="store_true", help="the user has agreed to the download")
    sub.add_parser("_download", help=argparse.SUPPRESS)

    g = sub.add_parser("generate", help="generate images from prompts, offline")
    g.add_argument("--prompt", help="one image: its prompt")
    g.add_argument("--out", help="one image: where to write it (.jpg, .jpeg, .png or .webp)")
    g.add_argument("--seed", type=int, help="one image: its seed (default: from the prompt and file name)")
    g.add_argument("--jobs", help="many images: a JSON list of {\"prompt\", \"out\", optional \"seed\"}")
    g.add_argument("--out-dir", default=".", help="where relative \"out\" paths land (default: here)")
    g.add_argument("--size", help="size the model draws at (default: about 1 megapixel, "
                                  "in the shape of --resize if given, else 1024x1024)")
    g.add_argument("--resize", help="centre-crop and scale each image to WIDTHxHEIGHT before saving")
    g.add_argument("--quality", type=int, default=85, help="JPEG and WebP quality (default: 85)")
    # mflux's own default for this model, and what its publishers recommend.
    g.add_argument("--steps", type=int, default=9, help="denoising steps (default: 9, what the model is tuned for)")
    g.add_argument("--force", action="store_true", help="redraw images that already exist")
    g.add_argument("--dry-run", action="store_true", help="validate and list what would be generated")

    args = ap.parse_args()
    signal.signal(signal.SIGTERM, on_sigterm)
    handler = {"check": cmd_check, "setup": cmd_setup, "_download": cmd_download,
               "generate": cmd_generate}[args.command]
    try:
        return handler(args)
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        return EXIT_PARTIAL
    except Exception as exc:
        print(f"unexpected error, a fault in this script: {type(exc).__name__}: {exc}", file=sys.stderr)
        return EXIT_UNEXPECTED


if __name__ == "__main__":
    sys.exit(main())
