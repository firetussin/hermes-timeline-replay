"""Read-only readiness checks and a reviewable host-local setup request."""
import json
import os
import shutil
import subprocess
import secrets
from pathlib import Path

from .core import data_dir

VERSION = "0.9.23"  # The tested CLI, never a floating runtime download.


def settings(home=None):
    path = data_dir(home) / "renderer.json"
    if not path.is_file():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else {}


def configure(hyperframes=None, browser=None, home=None, workers=None):
    values = settings(home)
    if workers is not None:
        if not isinstance(workers, int) or isinstance(workers, bool) or not 0 <= workers <= 16:
            raise ValueError("workers must be 1-16, or 0 for automatic")
        if workers:
            values["workers"] = workers
        else:
            values.pop("workers", None)
    for key, value in (("hyperframes", hyperframes), ("browser", browser)):
        if value:
            path = Path(value).expanduser().resolve()
            if not path.is_file():
                raise ValueError(f"{key}: select an existing file on this Hermes host")
            values[key] = str(path)
    folder = data_dir(home)
    folder.mkdir(parents=True, exist_ok=True)
    temporary=folder / ("renderer-"+secrets.token_hex(8)+".tmp")
    temporary.write_text(json.dumps(values, indent=2), encoding="utf-8")
    os.replace(temporary,folder/"renderer.json")
    return values


def browser_path(home=None):
    config = settings(home)
    explicit = config.get("browser") or os.environ.get("HYPERFRAMES_BROWSER_PATH")
    if explicit and Path(explicit).is_file():
        return str(Path(explicit).resolve())
    candidates = []
    for exe in ("chromium", "chromium-browser", "google-chrome", "chrome", "msedge"):
        found = shutil.which(exe)
        if found:
            candidates.append(Path(found))
    for key, suffix in (("PROGRAMFILES", "Google/Chrome/Application/chrome.exe"), ("PROGRAMFILES(X86)", "Microsoft/Edge/Application/msedge.exe"), ("LOCALAPPDATA", "Google/Chrome/Application/chrome.exe")):
        if os.environ.get(key):
            candidates.append(Path(os.environ[key]) / suffix)
    candidates.extend([Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"), Path("/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge")])
    # Only known renderer/browser cache locations, with bounded directory depth.
    for base in (Path.home()/".cache/hyperframes/chrome", Path.home()/".cache/puppeteer/chrome-headless-shell"):
        if base.is_dir():
            for pattern in ("*/*/chrome-headless-shell", "*/*/chrome-headless-shell.exe", "*/*/*/chrome-headless-shell.exe", "*/*/*/chrome-headless-shell"):
                candidates.extend(base.glob(pattern))
    return next((str(p.resolve()) for p in candidates if p.is_file()), None)


def inspect(home=None):
    from .rendering import renderer_command
    node = shutil.which("node")
    node_version, node_ok = "Not found", False
    if node:
        try:
            r = subprocess.run([node, "--version"], capture_output=True, text=True, timeout=3, check=True)
            node_version = r.stdout.strip()
            node_ok = int(node_version.lstrip("v").split(".")[0]) >= 22
        except (OSError, ValueError, subprocess.SubprocessError):
            node_version = "Could not check version"
    try:
        renderer_command(home)
        cli_ok = True
    except ValueError:
        cli_ok = False
    hf_version = hyperframes_version(home) if cli_ok else None
    browser = browser_path(home)
    items = [
        dict(id="node", label="Node.js 22+", ready=node_ok, detail=node_version),
        dict(id="hyperframes", label="HyperFrames", ready=cli_ok, detail=(f"{hf_version} (tested: {VERSION})" if hf_version and hf_version != VERSION else hf_version or "Configured") if cli_ok else "Not configured"),
        dict(id="ffmpeg", label="FFmpeg", ready=bool(shutil.which("ffmpeg")), detail="On PATH" if shutil.which("ffmpeg") else "Not found"),
        dict(id="ffprobe", label="ffprobe", ready=bool(shutil.which("ffprobe")), detail="On PATH" if shutil.which("ffprobe") else "Not found"),
        dict(id="browser", label="Chrome / Chromium", ready=bool(browser), detail="Detected" if browser else "Choose an installed browser or complete setup"),
    ]
    notes = performance_notes()
    if hf_version and hf_version != VERSION:
        notes.append(f"HyperFrames {hf_version} is installed; Timeline Replay is tested with {VERSION}. Exports should still work, but timings, progress and checks may differ.")
    return dict(ready=all(x["ready"] for x in items), items=items, performance=notes, host=host_notes(home), hyperframes=hf_version,
                note="HTML previews need none of these. Status checks never download software.")


LOW_MEMORY_MB = 8192  # HyperFrames 0.9.23 LOW_MEMORY_TOTAL_MB_THRESHOLD (inclusive)


def memory_total_mb():
    """Memory this process can use: /proc/meminfo, lowered by a cgroup limit when one is set
    (a container's limit is what counts, not the physical host). None when unknown."""
    total = None
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemTotal:"):
                total = int(line.split()[1]) // 1024
                break
    except (OSError, ValueError, IndexError):
        pass
    for limit_file in ("/sys/fs/cgroup/memory.max", "/sys/fs/cgroup/memory/memory.limit_in_bytes"):
        try:
            raw = Path(limit_file).read_text().strip()
            if raw.isdigit() and int(raw) < 1 << 60:
                limit = int(raw) // (1024*1024)
                total = min(total, limit) if total else limit
        except OSError:
            pass
    if total is None:
        try:
            total = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") // (1024*1024)
        except (AttributeError, ValueError, OSError):
            return None
    return total


_HF_VERSIONS = {}


def hyperframes_version(home=None):
    """The configured HyperFrames CLI's version (read-only `--version`), cached per command; None when unknown."""
    from .rendering import renderer_command
    try:
        command = tuple(renderer_command(home))
    except ValueError:
        return None
    if command not in _HF_VERSIONS:
        try:
            r = subprocess.run([*command, "--version"], capture_output=True, text=True, timeout=20, check=True,
                               env={**{k: os.environ[k] for k in ("PATH", "HOME", "USERPROFILE", "LOCALAPPDATA", "APPDATA", "TEMP", "TMP", "SystemRoot", "WINDIR", "LANG") if k in os.environ},
                                    "HYPERFRAMES_NO_TELEMETRY": "1", "HYPERFRAMES_NO_UPDATE_CHECK": "1", "DO_NOT_TRACK": "1"})
            text = (r.stdout or "").strip().splitlines()
            _HF_VERSIONS[command] = text[-1].strip().lstrip("v") if text else None
        except (OSError, subprocess.SubprocessError):
            _HF_VERSIONS[command] = None
    return _HF_VERSIONS[command]


def host_notes(home=None):
    """Setup problems outside video export that Hermes itself only logs."""
    notes = []
    pages = data_dir(home).parents[1] / "desktop-plugins"
    if pages.is_dir() and not os.access(pages, os.W_OK | os.X_OK):
        notes.append(f"Hermes can't write {pages}, so the Webapp can't install or update this plugin's page (Hermes only logs 'Permission denied'). "
                     f"Make that folder owned by the user Hermes runs as, for example: chown <user>:<user> {pages}")
    return notes


def performance_notes():
    """Non-blocking hints about export speed on this host."""
    notes = []
    total = memory_total_mb()
    if total is not None and total <= LOW_MEMORY_MB:
        notes.append(f"This host has {total / 1024:.1f} GiB RAM: HyperFrames uses its low-memory profile (screenshot capture, no worker calibration), so exports are slower. More than 8 GiB is recommended.")
    if os.name != "nt" and not Path("/dev/dri").exists():
        notes.append("No GPU device (/dev/dri): the renderer uses software GL. Exports work, at CPU speed.")
    return notes


def setup_request(home=None):
    report = inspect(home)
    missing = ", ".join(x["label"] for x in report["items"] if not x["ready"])
    tools = data_dir(home) / "tools"
    prompt = (
        "Set up local video export for my Timeline Replay plugin on this connected Hermes host. "
        "First inspect the current dependencies using timeline_replay(action='dependencies'). "
        f"The latest check reports missing or unconfigured: {missing or 'none; verify the configured paths'}. "
        "Reuse existing installations. Install only missing dependencies on this Hermes host; "
        "do not install or render on another computer, use cloud services, or spend API credits. "
        f"For HyperFrames use the tested version {VERSION}, installed under the plugin's private tools directory: {tools}. "
        "Use npm with --prefix, --no-audit and --no-fund; do not make a global npm install. "
        "Node.js 22+, FFmpeg, ffprobe and a compatible Chrome/Chromium are required. "
        "Ask before any administrator-level or system-wide installation. "
        "The browser setup command is 'hyperframes browser ensure', and may download a browser. "
        "On Linux ARM prefer an existing Chromium and ask before elevated package installation. "
        "Use 'hermes replay setup --hyperframes <absolute CLI .mjs path> --browser <absolute browser path>' "
        "to persist already-installed paths in the plugin settings when needed. "
        "If the CLI subcommand is unavailable under host isolation, use the package's cli.py with HERMES_HOME set to this profile. "
        "Finish by rechecking dependencies. Do not start a video render yet."
    )
    return dict(ok=True, dependencies=report, prompt=prompt,
                note="This is an install request for you to review and send. Opening setup does not install anything.")
