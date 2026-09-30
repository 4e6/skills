#!/usr/bin/env python3
"""Z-Image Turbo on an Apple Silicon Mac: check the machine, set it up, draw images.

    python3 z_image_turbo.py check
    python3 z_image_turbo.py setup
    python3 z_image_turbo.py generate --prompt "..." --out picture.jpg
    python3 z_image_turbo.py generate --jobs jobs.json --out-dir images/

One model, mflux-community/z-image-turbo-mflux-q8 at a pinned revision, run by
mflux on the Mac's GPU. `check` and `setup` run on any Python 3.9 or newer,
standard library only. `generate` validates its input there too, then re-runs
itself under the Python 3.10+ environment `setup` built, which is where mflux is.

Only `setup` uses the network: it installs mflux into its own environment and
downloads the model into the Hugging Face cache. `generate` loads the model from
that cache with the hub switched to offline, so it never downloads anything.

Exit status:
    check     0 ready; 1 this Mac can run it, but `setup` has work to do;
              3 this machine cannot run it.
    setup     0 ready; 1 an install or download step failed (re-run resumes);
              3 this machine cannot run it.
    generate  0 every job has its image; 1 some jobs have none (failed,
              interrupted, or stopped on low battery) and a re-run resumes;
              2 the command or the jobs file is wrong, nothing was drawn;
              3 it cannot run: not set up, or the model would not load.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
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
MFLUX_VERSION = "0.19.0"  # keep equal to the pin in requirements.txt

# Measured: the installed environment is ~1.2 GB; the pip download is smaller.
PACKAGES_BYTES = 1_200_000_000
# The model holds ~12-14 GB of unified memory while it draws; below 16 GB the
# Mac swaps hard enough that an image takes many minutes.
MIN_MEMORY_BYTES = 16 * 1024**3
# mflux's own floor is 3.10; 3.14 is the newest this pin has been run on.
MIN_PYTHON = (3, 10)
PYTHON_CANDIDATES = [f"python3.{m}" for m in range(14, 9, -1)] + ["python3"]
HOMEBREW_BIN = Path("/opt/homebrew/bin")

GB = 1000**3
EXIT_OK, EXIT_PARTIAL, EXIT_USAGE, EXIT_CANNOT = 0, 1, 2, 3

sys.dont_write_bytecode = True


# --- where things live ------------------------------------------------------


def venv_dir() -> Path:
    """The environment `setup` builds. Outside the skill's folder on purpose:
    reinstalling or updating the skill replaces that folder, and a 1.2 GB
    environment inside it would be rebuilt every time."""
    override = os.environ.get("Z_IMAGE_TURBO_VENV")
    if override:
        return Path(override).expanduser()
    cache = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return Path(cache) / "z-image-turbo-macos" / "venv"


def venv_python() -> Path:
    return venv_dir() / "bin" / "python"


def hf_hub_cache() -> Path:
    """The Hugging Face hub cache, resolved the way huggingface_hub does."""
    if os.environ.get("HF_HUB_CACHE"):
        return Path(os.environ["HF_HUB_CACHE"]).expanduser()
    if os.environ.get("HF_HOME"):
        return Path(os.environ["HF_HOME"]).expanduser() / "hub"
    cache = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return Path(cache) / "huggingface" / "hub"


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


def platform_problem() -> str | None:
    """Why this machine cannot run the model at all, or None."""
    if platform.system() != "Darwin":
        return f"this is {platform.system() or 'an unknown system'}, and the model runs only on macOS"
    # hw.optional.arm64 is 1 on Apple Silicon even when this Python runs under
    # Rosetta, where platform.machine() would say x86_64.
    if sysctl("hw.optional.arm64") != "1":
        return "this Mac has an Intel processor, and the model runs only on Apple Silicon (M1 or later)"
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
        out = subprocess.run([exe, "-c", code], capture_output=True, text=True, timeout=20, check=True)
        major, minor, machine = out.stdout.split()
        return (int(major), int(minor)), machine
    except (OSError, subprocess.SubprocessError, ValueError):
        return None


def find_python() -> tuple[str, tuple[int, int]] | None:
    """The newest native arm64 Python 3.10+ on this Mac. An x86_64 one (an
    Intel Homebrew under /usr/local) would install packages MLX has no build for."""
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
            if probed and probed[0] >= MIN_PYTHON and probed[1] == "arm64":
                found.append((probed[0], exe))
    if not found:
        return None
    version, exe = max(found)
    return exe, version


# --- what is installed ------------------------------------------------------


def packages_ready() -> bool:
    py = venv_python()
    if not py.exists():
        return False
    code = "import importlib.metadata as m; print(m.version('mflux'))"
    try:
        out = subprocess.run([str(py), "-c", code], capture_output=True, text=True, timeout=60, check=True)
    except (OSError, subprocess.SubprocessError):
        return False
    return out.stdout.strip() == MFLUX_VERSION


def model_missing_bytes() -> int:
    """Bytes of the model not yet in the cache at the pinned revision; 0 when
    it is complete. A file of the wrong size counts as missing."""
    snap = model_snapshot()
    missing = 0
    for rel, size in MODEL_FILES.items():
        path = snap / rel
        try:
            if path.stat().st_size == size:
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


# --- check ------------------------------------------------------------------


def row(label: str, state: str, detail: str) -> None:
    print(f"{label:<9} {state:<8} {detail}", flush=True)


def cmd_check(_args: argparse.Namespace) -> int:
    problem = platform_problem()
    if problem:
        row("platform", "no", problem)
        print("cannot run here: this skill works only on an Apple Silicon Mac")
        return EXIT_CANNOT
    row("platform", "ok", describe_mac())

    mem = memory_bytes()
    if mem and mem < MIN_MEMORY_BYTES:
        row("memory", "low", f"{mem / 1024**3:.0f} GB; the model holds 12-14 GB while it draws, so expect heavy swapping")
    else:
        row("memory", "ok", f"{mem / 1024**3:.0f} GB" if mem else "unknown")

    needs = 0
    if packages_ready():
        row("packages", "ready", f"mflux {MFLUX_VERSION} in {venv_dir()}")
    else:
        py = find_python()
        if py is None:
            row("python", "no", "no native Python 3.10 or newer found; install one (for example `brew install python`) and check again")
            print("cannot run here until a Python 3.10 or newer is installed")
            return EXIT_CANNOT
        row("python", "ok", f"{py[0]} ({py[1][0]}.{py[1][1]})")
        row("packages", "missing", f"setup installs mflux {MFLUX_VERSION} into {venv_dir()} (about {gb(PACKAGES_BYTES)})")
        needs += PACKAGES_BYTES

    missing = model_missing_bytes()
    if missing == 0:
        row("model", "ready", f"{MODEL_REPO} ({gb(MODEL_BYTES)})")
    else:
        row("model", "missing", f"setup downloads {gb(missing)} of {MODEL_REPO} into {hf_hub_cache()}")
        needs += missing

    if needs:
        free = min(free_bytes(venv_dir()), free_bytes(hf_hub_cache()))
        state = "ok" if free > needs + GB else "short"
        row("disk", state, f"{gb(free)} free, setup needs {gb(needs)}")
        if state == "short":
            print("cannot set up: free some disk space first")
            return EXIT_CANNOT
        print(f"setup needed: `setup` downloads about {gb(needs)}, once")
        return EXIT_PARTIAL

    print("ready")
    return EXIT_OK


# --- setup ------------------------------------------------------------------


def cmd_setup(args: argparse.Namespace) -> int:
    problem = platform_problem()
    if problem:
        print(f"cannot run here: {problem}", file=sys.stderr)
        return EXIT_CANNOT

    if not packages_ready():
        py = find_python()
        if py is None:
            print("cannot set up: no native Python 3.10 or newer found; install one (for example "
                  "`brew install python`) and run setup again", file=sys.stderr)
            return EXIT_CANNOT
        venv = venv_dir()
        print(f"[setup] building {venv} with {py[0]}", flush=True)
        if venv.exists():
            shutil.rmtree(venv)  # ours alone; a half-built one is not worth repairing
        venv.parent.mkdir(parents=True, exist_ok=True)
        steps = [
            [py[0], "-m", "venv", str(venv)],
            [str(venv_python()), "-m", "pip", "install", "--disable-pip-version-check", "-r", str(REQUIREMENTS)],
        ]
        for step in steps:
            if subprocess.run(step).returncode != 0:
                print(f"[setup] failed: {' '.join(step)}", file=sys.stderr)
                return EXIT_PARTIAL
        if not packages_ready():
            print(f"[setup] failed: mflux {MFLUX_VERSION} is not importable in {venv}", file=sys.stderr)
            return EXIT_PARTIAL
        print(f"[setup] mflux {MFLUX_VERSION} installed", flush=True)

    missing = model_missing_bytes()
    if missing:
        print(f"[setup] downloading {gb(missing)} of {MODEL_REPO} into {hf_hub_cache()}; "
              "this is the long part, and a re-run resumes it", flush=True)
        code = subprocess.run([str(venv_python()), str(Path(__file__).resolve()), "_download"]).returncode
        if code != 0 or model_missing_bytes():
            print("[setup] failed: the model download did not complete; run setup again to resume", file=sys.stderr)
            return EXIT_PARTIAL
    print("ready")
    return EXIT_OK


def cmd_download(_args: argparse.Namespace) -> int:
    """Runs inside the environment, where huggingface_hub is. Not for callers."""
    from huggingface_hub import snapshot_download

    snapshot_download(repo_id=MODEL_REPO, revision=MODEL_REVISION, allow_patterns=list(MODEL_FILES))
    return EXIT_OK


# --- generate: input --------------------------------------------------------

SUFFIXES = {".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG", ".webp": "WEBP"}
# Z-Image's VAE downsamples by 8 and its transformer takes 2x2 patches, so a
# side must be a multiple of 16. The bounds are the range this skill has run:
# the model is trained around one megapixel, and time and memory grow with area.
SIDE_STEP, SIDE_MIN, SIDE_MAX = 16, 256, 2048


class UsageError(Exception):
    pass


def parse_size(text: str, flag: str, check_model_side: bool) -> tuple[int, int]:
    try:
        w, h = (int(p) for p in text.lower().split("x"))
    except ValueError:
        raise UsageError(f"{flag} takes WIDTHxHEIGHT, like 1024x1024 (got {text!r})")
    if w <= 0 or h <= 0:
        raise UsageError(f"{flag} must be positive (got {text})")
    if check_model_side:
        for side in (w, h):
            if side % SIDE_STEP or not SIDE_MIN <= side <= SIDE_MAX:
                raise UsageError(
                    f"{flag} sides must be multiples of {SIDE_STEP} between {SIDE_MIN} and {SIDE_MAX} "
                    f"(got {text}); for another final size, draw near it and add --resize"
                )
    return w, h


def prompt_seed(prompt: str) -> int:
    """A seed that follows the prompt rather than its place in the list, so
    reordering jobs changes nothing and the same prompt redraws the same image."""
    return int.from_bytes(hashlib.sha256(prompt.encode("utf-8")).digest()[:4], "big")


def load_jobs(args: argparse.Namespace) -> list[dict]:
    if args.jobs:
        try:
            raw = json.loads(Path(args.jobs).read_text(encoding="utf-8"))
        except OSError as exc:
            raise UsageError(f"cannot read {args.jobs}: {exc.strerror}")
        except json.JSONDecodeError as exc:
            raise UsageError(f"{args.jobs} is not valid JSON: {exc}")
        if not isinstance(raw, list) or not raw:
            raise UsageError(f"{args.jobs} must hold a non-empty JSON list of jobs")
    else:
        raw = [{"prompt": args.prompt, "out": args.out}]
        if args.seed is not None:
            raw[0]["seed"] = args.seed

    out_dir = Path(args.out_dir).expanduser()
    jobs, seen = [], {}
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
        out = job.get("out")
        if not isinstance(out, str) or not out.strip():
            raise UsageError(f"{where} needs an \"out\" path")
        path = Path(out).expanduser()
        path = (path if path.is_absolute() else out_dir / path).resolve()
        if path.suffix.lower() not in SUFFIXES:
            raise UsageError(f"{where}: \"out\" must end in .jpg, .jpeg, .png or .webp (got {out!r})")
        if path in seen:
            raise UsageError(f"{where} writes {path}, which job {seen[path]} already writes")
        seen[path] = i
        seed = job.get("seed")
        if seed is None:
            seed = prompt_seed(prompt.strip())
        elif not isinstance(seed, int) or isinstance(seed, bool) or seed < 0:
            raise UsageError(f"{where}: \"seed\" must be a non-negative integer")
        jobs.append({"prompt": prompt.strip(), "path": path, "seed": seed})
    return jobs


def show(path: Path) -> str:
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)


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
    path.parent.mkdir(parents=True, exist_ok=True)
    # Written aside and renamed, so an interrupted save never leaves a partial
    # file that the next run would take for a finished image.
    partial = path.with_name(f".{path.name}.partial")
    image.convert("RGB").save(partial, fmt, **options)
    os.replace(partial, path)


def draw(jobs: list[dict], args: argparse.Namespace) -> int:
    # Before mflux is imported: huggingface_hub reads this once, at import.
    os.environ["HF_HUB_OFFLINE"] = "1"
    # mflux draws a progress bar per step; the made/fail lines below are the
    # progress a caller reads, and the bars would only bury them.
    os.environ["TQDM_DISABLE"] = "1"
    import mlx.core as mx
    from mflux.callbacks.instances.battery_saver import BatterySaver
    from mflux.models.common.config.model_config import ModelConfig
    from mflux.models.z_image import ZImage
    from mflux.utils.exceptions import StopImageGenerationException

    size = parse_size(args.size, "--size", True)
    resize = parse_size(args.resize, "--resize", False) if args.resize else None

    print(f"[gen] loading {MODEL_REPO}", flush=True)
    t0 = time.monotonic()
    try:
        model = ZImage(model_path=str(model_snapshot()), model_config=ModelConfig.z_image_turbo())
    except Exception as exc:  # the model's own errors are many and unexported
        print(f"cannot run: the model would not load: {exc}", file=sys.stderr)
        return EXIT_CANNOT
    # Stops before the next image once a MacBook on battery reaches 10%; what
    # is already drawn is kept, and a re-run on power resumes.
    model.callbacks.register(BatterySaver(battery_percentage_stop_limit=10))
    print(f"[gen] model loaded in {time.monotonic() - t0:.0f}s", flush=True)

    made = failed = 0
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
        except Exception as exc:
            failed += 1
            print(f"fail  {show(job['path'])}: {exc}", flush=True)
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
        parse_size(args.size, "--size", True)
        if args.resize:
            parse_size(args.resize, "--resize", False)
        if not 1 <= args.quality <= 100:
            raise UsageError("--quality must be between 1 and 100")
        if not 1 <= args.steps <= 50:
            raise UsageError("--steps must be between 1 and 50")
        jobs = load_jobs(args)
    except UsageError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_USAGE

    pending = [j for j in jobs if args.force or not j["path"].exists()]
    for job in jobs:
        if job not in pending:
            print(f"have  {show(job['path'])}", flush=True)
    if args.dry_run or not pending:
        for job in pending:
            print(f"draw  {show(job['path'])}  seed={job['seed']}  {job['prompt'][:90]}")
        return EXIT_OK

    problem = platform_problem()
    if problem:
        print(f"cannot run here: {problem}", file=sys.stderr)
        return EXIT_CANNOT
    if model_missing_bytes():
        print("cannot run: the model is not downloaded; run `check`, then `setup`", file=sys.stderr)
        return EXIT_CANNOT

    try:
        import mflux  # noqa: F401
    except ImportError:
        # Not inside the environment yet: become its Python, once.
        if os.environ.get("_Z_IMAGE_TURBO_REEXEC") or not packages_ready():
            print("cannot run: mflux is not installed; run `check`, then `setup`", file=sys.stderr)
            return EXIT_CANNOT
        os.environ["_Z_IMAGE_TURBO_REEXEC"] = "1"
        py = str(venv_python())
        os.execv(py, [py, str(Path(__file__).resolve()), *sys.argv[1:]])

    return draw(pending, args)


# --- command line -----------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True, metavar="{check,setup,generate}")
    sub.add_parser("check", help="say whether this Mac can run the model, and what setup would download")
    sub.add_parser("setup", help="install mflux and download the model (network, about 12 GB, once)")
    sub.add_parser("_download", help=argparse.SUPPRESS)

    g = sub.add_parser("generate", help="draw images from prompts, offline")
    g.add_argument("--prompt", help="one image: its prompt")
    g.add_argument("--out", help="one image: where to write it (.jpg, .jpeg, .png or .webp)")
    g.add_argument("--seed", type=int, help="one image: its seed (default: derived from the prompt)")
    g.add_argument("--jobs", help="many images: a JSON list of {\"prompt\", \"out\", optional \"seed\"}")
    g.add_argument("--out-dir", default=".", help="where relative \"out\" paths land (default: here)")
    g.add_argument("--size", default="1024x1024", help="size the model draws at (default: 1024x1024)")
    g.add_argument("--resize", help="centre-crop and scale each image to WIDTHxHEIGHT before saving")
    g.add_argument("--quality", type=int, default=85, help="JPEG and WebP quality (default: 85)")
    # Z-Image Turbo is distilled for 8 denoising passes, which 9 steps give.
    g.add_argument("--steps", type=int, default=9, help="denoising steps (default: 9, what the model is tuned for)")
    g.add_argument("--force", action="store_true", help="redraw images that already exist")
    g.add_argument("--dry-run", action="store_true", help="validate and list what would be drawn")

    args = ap.parse_args()
    return {"check": cmd_check, "setup": cmd_setup, "_download": cmd_download,
            "generate": cmd_generate}[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
