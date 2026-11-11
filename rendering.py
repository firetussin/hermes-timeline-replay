"""Explicit, bounded local render jobs. No npx, downloads or shell execution."""
from __future__ import annotations
import json
import os
import re
import shutil
import subprocess
import threading
import time
from pathlib import Path

from .core import data_dir

_lock = threading.Lock()
_running = set()


def _acquire(folder):
    """One render per profile home, including separate tool/backend processes."""
    folder.mkdir(parents=True, exist_ok=True)
    lock = (folder / "render.lock").open("a+b")
    try:
        lock.seek(0, 2)
        if lock.tell() == 0:
            lock.write(b"0")
            lock.flush()
        lock.seek(0)
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return lock
    except OSError:
        lock.close()
        raise ValueError("Another render is running for this profile home") from None


def renderer_command(home=None):
    from .dependencies import settings
    explicit = os.environ.get("TIMELINE_REPLAY_HYPERFRAMES") or settings(home).get("hyperframes")
    managed = data_dir(home) / "tools" / "node_modules" / "hyperframes" / "bin" / "hyperframes.mjs"
    if not explicit and managed.is_file():
        explicit = str(managed)
    if explicit:
        path = Path(explicit).expanduser().resolve()
        if not path.is_file():
            raise ValueError("Configured HyperFrames executable does not exist")
        if path.suffix in (".js", ".mjs"):
            node = shutil.which("node")
            if not node:
                raise ValueError("Node.js is required for the configured HyperFrames CLI")
            return [node, str(path)]
        if path.suffix.lower() in (".cmd", ".bat", ".ps1"):
            raise ValueError("Point TIMELINE_REPLAY_HYPERFRAMES to the CLI .mjs entrypoint on Windows")
        return [str(path)]
    executable = shutil.which("hyperframes")
    if executable:
        path = Path(executable)
        # npm's Windows shims cannot be launched safely with shell=False. Resolve
        # the conventional sibling entrypoint instead of executing a shell shim.
        if path.suffix.lower() in (".cmd", ".bat", ".ps1"):
            sibling = path.parent / "node_modules/hyperframes/bin/hyperframes.mjs"
            if sibling.is_file() and shutil.which("node"):
                return [shutil.which("node"), str(sibling)]
        else:
            return [str(path)]
    raise ValueError("Install HyperFrames on this Hermes host first; set TIMELINE_REPLAY_HYPERFRAMES to its CLI entrypoint. Nothing was downloaded.")


def bundle_path(bundle, home=None):
    if not isinstance(bundle, str) or not re.fullmatch(r"[a-f0-9]{16}", bundle):
        raise ValueError("Invalid bundle ID")
    root = data_dir(home).resolve() / "renders"
    path = (root / bundle).resolve()
    if path.parent != root or not path.is_dir():
        raise ValueError("Bundle not found")
    return path


def render_workers(home=None):
    """Configured worker count, else automatic: half the cores, at least 1, at most 4."""
    from .dependencies import settings
    raw = os.environ.get("TIMELINE_REPLAY_WORKERS") or settings(home).get("workers")
    try:
        value = int(raw)
        if 1 <= value <= 16:
            return value
    except (TypeError, ValueError):
        pass
    return max(1, min(4, (os.cpu_count() or 2)//2))


def _render_lock_free(home=None):
    """True when no process holds the profile-home render lock (probe, then release)."""
    try:
        _acquire(data_dir(home)).close()
        return True
    except (OSError, ValueError):
        return False


def status(home=None):
    root = data_dir(home) / "renders"
    jobs = []
    if root.is_dir():
        lock_free = None
        for path in sorted(root.glob("*/job.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:30]:
            try:
                job = json.loads(path.read_text())
                # A worker in this process is live. Otherwise the OS render lock tells
                # us whether any process still holds it; a free lock means the job died.
                if job.get("state") == "running":
                    with _lock:
                        live_here = job.get("id") in _running
                    if not live_here:
                        if lock_free is None:
                            with _lock:
                                lock_free = False if _running else _render_lock_free(home)
                        if lock_free:
                            job["state"] = "interrupted"
                # Human-readable row: title, created time and resolution come from the bundle.
                try:
                    info = json.loads((path.parent / "bundle.json").read_text())
                    job.setdefault("title", info.get("title"))
                    job.setdefault("created", info.get("created"))
                    job.setdefault("resolution", info.get("resolution", "1080p"))
                except (OSError, ValueError):
                    pass
                if job.get("state") == "complete" and (path.parent / "timeline.mp4").is_file():
                    # Absolute path on this Hermes host, for Desktop's MEDIA player and file download.
                    job["video_path"] = str((path.parent / "timeline.mp4").resolve())
                jobs.append(job)
            except (OSError, ValueError):
                continue
    return jobs


def check_summary(report_path, limit=5):
    """Compact, local-only summary of a `hyperframes check --json` report."""
    try:
        report = json.loads(Path(report_path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    sections = {k: dict(errors=v.get("errorCount", 0), warnings=v.get("warningCount", 0))
                for k, v in report.items() if isinstance(v, dict) and "errorCount" in v}
    findings = []
    for name, section in report.items():
        if not isinstance(section, dict):
            continue
        for f in section.get("findings", []):
            if f.get("severity") == "error" and len(findings) < limit:
                findings.append(dict(section=name, code=f.get("code"), selector=str(f.get("selector", ""))[-120:],
                                     text=str(f.get("text") or f.get("message") or "")[:80], times=(f.get("times") or [])[:5]))
    return dict(ok=bool(report.get("ok")), sections=sections, first_errors=findings, report=str(report_path))


CHECK_STEP = re.compile(r"check: samples (\d+)/(\d+)")
# HyperFrames prints "Streaming frame N/M" with one worker and
# "Capturing frame N/M (K workers)" with several; the leading percent is optional.
RENDER_FRAME = re.compile(r"(?:Streaming|Capturing) frames? (\d+)\s*/\s*(\d+)")
AFTER_CAPTURE = re.compile(r"(Encoding|Muxing|Finaliz|Assembl|Writing|Verifying|Render complete)[^\r\n]{0,60}", re.I)
RENDER_PERCENT = re.compile(r"(\d{1,3})%\s+([A-Za-z][^\r\n]{0,60})")


HF_PROGRESS = re.compile(r"@hf-progress\s+(\{.*\})")
PHASE_LABELS = {"encode": "Encoding video", "assemble": "Assembling video", "compile": "Compiling composition"}


WARMUP_SHARE, WARMUP_SECONDS = .05, 5


def _frames(state, frame, frames):
    """Frame progress. The first frames are slow (browser and encoder warm-up), so the frame
    rate is measured only after max(5% of frames, 5 s); until then no rate-based ETA is
    claimed (the learned estimate covers it, see save())."""
    now = time.monotonic()
    state.setdefault("_start", now)
    state.update(percent=min(99, round(100*frame/frames)), frame=frame, frames=frames, label=f"Rendering frame {frame}/{frames}", _at=now)
    if "_warm" not in state:
        if frame >= max(5, frames*WARMUP_SHARE) and now-state["_start"] >= WARMUP_SECONDS:
            state["_warm"] = (now, frame)
        state.pop("fps", None)
        state.pop("eta_seconds", None)
        return
    t0, f0 = state["_warm"]
    if frame > f0 and now > t0:
        rate = (frame-f0)/(now-t0)
        state.update(fps=round(rate, 2), eta_seconds=round((frames-frame)/rate))


def parse_progress(text, stage, state):
    """Update `state` from one HyperFrames progress fragment; True when it changed.
    Prefers the machine-readable `@hf-progress {json}` lines over human wording."""
    m = HF_PROGRESS.search(text)
    if m and stage == "rendering":
        try:
            data = json.loads(m.group(1))
            code, done, total = data.get("code"), data.get("done"), data.get("total")
        except (ValueError, AttributeError):
            data, code = None, None
        if code == "capture" and isinstance(done, int) and isinstance(total, int) and total > 0:
            _frames(state, done, total)
            return True
        if code in PHASE_LABELS and "frame" in state:
            state.update(label=PHASE_LABELS[code], percent=99)
            state.pop("eta_seconds", None)
            state.pop("fps", None)
            return True
        if data is not None:
            return False
    if stage == "checking":
        m = CHECK_STEP.search(text)
        if m:
            step, total = int(m.group(1)), max(1, int(m.group(2)))
            now = time.monotonic()
            state.setdefault("_first", (now, step))
            t0, s0 = state["_first"]
            state.update(step=step, steps=total, label=f"Checking layout {step}/{total}" if step < total else "Analysing layout results")
            state.pop("eta_seconds", None)
            return True
        return False
    m = RENDER_FRAME.search(text)
    if m:
        _frames(state, int(m.group(1)), max(1, int(m.group(2))))
        return True
    m = AFTER_CAPTURE.search(text)
    if m and "frame" in state:
        # Frames are captured; encoding/finishing has no frame count, so no ETA is claimed.
        state.update(label=m.group(0).strip(), percent=99)
        state.pop("eta_seconds", None)
        state.pop("fps", None)
        return True
    m = RENDER_PERCENT.search(text)
    if m and "frame" not in state:
        # Before frames stream (compiling, browser start) there is no frame-based %.
        state.update(label=m.group(2).strip())
        return True
    return False


def _stream(argv, cwd, env, log, on_text, stdout=None, timeout=3600):
    """Run without a shell; mirror progress output to the log and pass each \r/\n fragment to on_text."""
    process = subprocess.Popen(argv, cwd=cwd, env=env, shell=False, stdin=subprocess.DEVNULL,
                               stdout=stdout if stdout is not None else subprocess.PIPE,
                               stderr=subprocess.PIPE if stdout is not None else subprocess.STDOUT)
    pipe = process.stderr if stdout is not None else process.stdout

    def pump():
        pending = ""
        while True:
            chunk = pipe.read1(4096) if hasattr(pipe, "read1") else pipe.read(4096)
            if not chunk:
                break
            text = chunk.decode("utf-8", "replace")
            log.write(text)
            log.flush()
            parts = re.split(r"[\r\n]", pending + text)
            pending = parts.pop()
            for part in parts:
                if part.strip():
                    on_text(part)
        if pending.strip():
            on_text(pending)
    reader = threading.Thread(target=pump, daemon=True)
    reader.start()
    try:
        code = process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
        raise RuntimeError("renderer timed out")
    reader.join(5)
    return code


STATS = "render-stats.json"


def family_of(pace):
    """Canvas paces check far faster than lane paces (one canvas against thousands of elements)."""
    from .canvas_views import CANVAS_PACES
    return "canvas" if pace in CANVAS_PACES else "lanes"


def _record_stats(home_dir, video_seconds, wall_seconds, check_seconds=None, events=None, workers=None, screen_lanes=None, height=None, family=None):
    path = Path(home_dir) / STATS
    try:
        rows = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else []
    except (OSError, ValueError):
        rows = []
    row = dict(video=round(video_seconds, 2), wall=round(wall_seconds, 1), at=round(time.time()))
    if check_seconds is not None and events:
        row.update(check=round(check_seconds, 1), events=int(events))
    if workers:
        row["workers"] = int(workers)
    if screen_lanes:
        row["screen_lanes"] = int(screen_lanes)
    if height:
        row["height"] = int(height)
    row["layout"] = LAYOUT
    if family:
        row["family"] = family
    # Keep enough history that a run of small test exports doesn't evict the large ones.
    rows = (rows + [row])[-50:]
    try:
        path.write_text(json.dumps(rows), encoding="utf-8")
    except OSError:
        pass


# Composition layout generation recorded with each export. 2 = stacked lanes (0.2.13+);
# rows without it may come from the older chapter layout, whose check cost differed.
LAYOUT = 2


def _check_rows(all_rows, workers, screen_lanes, family=None):
    """Rows to learn layout-check time from, narrowed step by step to the most comparable
    exports: current layout, same worker count, same lane-density band. A step that would
    leave nothing is skipped."""
    rows = [r for r in all_rows if r.get("events") and r.get("check")]
    keeps = [lambda r: r.get("family", "lanes") == (family or "lanes"), lambda r: r.get("layout") == LAYOUT, lambda r: r.get("workers", 1) == workers]
    if screen_lanes:
        keeps.append(lambda r: lanes_band(r.get("screen_lanes")) == lanes_band(screen_lanes))
    for keep in keeps:
        rows = [r for r in rows if keep(r)] or rows
    return rows


def lanes_band(n):
    """Screen density bands for estimates: ≤4 lanes, 5–8, 9+ (more lanes, more DOM per frame)."""
    return 0 if not n else 1 if n <= 4 else 2 if n <= 8 else 3


def estimate(video_seconds, home=None, events=None, workers=None, screen_lanes=None, height=None, family=None):
    """Wall-clock estimate learned from this host's completed exports; None before the first one.
    The layout check scales with event count and encoding with video length, so when
    both were recorded they are estimated separately."""
    path = data_dir(home) / STATS
    med = lambda xs: sorted(xs)[len(xs)//2]
    try:
        rows = [r for r in json.loads(path.read_text(encoding="utf-8")) if r.get("video", 0) > 0]
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        return None
    if not rows:
        return None
    all_rows = rows
    workers = workers or render_workers(home)
    # Encoding speed depends on the worker count; prefer exports made with the same count.
    # Lane and canvas paces check at very different speeds; prefer the same family when known.
    rows = [r for r in rows if r.get("family", "lanes") == (family or "lanes")] or rows
    same = [r for r in rows if r.get("workers", 1) == workers]
    rows = same or rows
    if height:
        # Pixels per frame differ by resolution; older rows were all 1080p.
        res = [r for r in rows if r.get("height", 1080) == height]
        if res:
            rows = res
        elif height != 1080:
            # CT114: render time grows ~pixels^0.7 (720p 0.6x, 1440p 1.45x, 4K 2.7x of 1080p).
            scale = ((height / 1080) ** 2) ** 0.7
            rows = [dict(r, wall=r["check"] + (r["wall"] - r["check"]) * scale) if r.get("check") is not None else dict(r, wall=r["wall"] * scale) for r in rows]
    if screen_lanes:
        # Prefer exports with a similar number of lanes on screen (layout cost differs).
        dense = [r for r in rows if lanes_band(r.get("screen_lanes")) == lanes_band(screen_lanes)]
        rows = dense or rows
    split = [r for r in rows if r.get("events") and r.get("check") is not None]
    checks = _check_rows(all_rows, workers, screen_lanes, family)
    basis = f"{len(rows)} previous export(s) on this host"
    if events and split and checks:
        check = check_time(checks, events)
        per_second = render_rate(split, events) or med([(r["wall"]-r["check"])/r["video"] for r in split])
        return dict(seconds=round(check + per_second*video_seconds), check_seconds=round(check),
                    render_seconds=round(per_second*video_seconds), workers=workers, basis=basis + ("" if same else "; different worker count"))
    return dict(seconds=round(med([r["wall"]/r["video"] for r in rows])*video_seconds), basis=basis)


def _power_fit(points, x, default_b, lo, hi):
    """y = a*x^b fitted in log space when points span different sizes, else b=default_b."""
    import math
    pts = [(math.log(px), math.log(py)) for px, py in points if px > 0 and py > 0]
    if not pts:
        return None
    xs = [p for p, _ in pts]
    if len(pts) >= 2 and max(xs) - min(xs) > 0.5:
        mx, my = sum(xs)/len(xs), sum(y for _, y in pts)/len(pts)
        b = max(lo, min(hi, sum((p-mx)*(y-my) for p, y in pts) / sum((p-mx)**2 for p in xs)))
    else:
        b = default_b
    a = sorted(math.exp(y - b*p) for p, y in pts)[len(pts)//2]
    return a * x**b


def check_time(rows, events):
    """Layout-check time grows sublinearly with events (CT114: 52 s at 1.1k, 190 s at 20k,
    exponent ~0.45). Exports within ±15% of the requested event count answer directly
    (median of the newest three, scaled by that exponent); the fit is only used for sizes
    this host hasn't exported yet, and only over its newest rows, so a run of small or
    old exports can't drag a large estimate down."""
    rows = sorted(rows, key=lambda r: r.get("at", 0))
    close = [r for r in rows if abs(r["events"] / events - 1) <= .15][-3:]
    if close:
        return sorted(r["check"] * (events / r["events"]) ** .45 for r in close)[len(close)//2]
    return _power_fit([(r["events"], r["check"]) for r in rows[-12:]], events, .45, .2, 1.0)


def render_rate(rows, events):
    """Render seconds per video second rise mildly with composition weight (CT114, 2 workers:
    ~13.7 fps at 1.1k events, ~11.5 fps at 20k, exponent ~0.1)."""
    return _power_fit([(r["events"], (r["wall"]-r["check"])/r["video"]) for r in rows if r.get("events")], events, .1, 0, .6)


def _busy_message(home=None):
    for job in status(home):
        if job.get("state") == "running":
            p = job.get("progress") or {}
            bits = [f"{p['percent']}%" if "percent" in p else job.get("stage", "running")]
            if p.get("eta_seconds") is not None:
                bits.append(f"about {max(1, round(p['eta_seconds']/60))} min left")
            return "Another export is rendering (" + ", ".join(bits) + "). Exports refreshes automatically; start this one when it finishes."
    return "Another export is rendering. Exports refreshes automatically; start this one when it finishes."


def start(bundle, home=None):
    path = bundle_path(bundle, home)
    command = renderer_command(home)
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise ValueError("FFmpeg and ffprobe must be installed on this Hermes host")
    busy = False
    with _lock:
        if (path / "timeline.mp4").exists():
            raise ValueError("This bundle already has a video; build a new bundle to render again")
        if _running:
            busy = True
        else:
            try:
                process_lock = _acquire(path.parent.parent)
            except ValueError:
                busy = True
        if not busy:
            _running.add(bundle)
    if busy:
        # Built outside _lock: status() takes the same non-reentrant lock.
        raise ValueError(_busy_message(home))
    with _lock:
        from .version import VERSION, API
        from .dependencies import hyperframes_version
        job = dict(id=bundle, state="running", pid=os.getpid(), started=time.time(), stage="checking", version=VERSION, api=API, hyperframes=hyperframes_version(home))
        try:
            info = json.loads((path / "bundle.json").read_text())
            job.update(title=info.get("title"), created=info.get("created"), resolution=info.get("resolution", "1080p"))
        except (OSError, ValueError):
            pass
        try:
            (path / "job.json").write_text(json.dumps(job), encoding="utf-8")
        except OSError:
            _running.discard(bundle)
            process_lock.close()
            raise
    threading.Thread(target=_worker, args=(bundle, path, command, job, process_lock), daemon=True, name="timeline-replay-render").start()
    return job


def _worker(bundle, path, command, job, process_lock):
    env = {k: os.environ[k] for k in ("PATH", "HOME", "USERPROFILE", "LOCALAPPDATA", "APPDATA", "TEMP", "TMP", "SystemRoot", "WINDIR", "LANG") if k in os.environ}
    env.update(HYPERFRAMES_NO_TELEMETRY="1", HYPERFRAMES_NO_UPDATE_CHECK="1", DO_NOT_TRACK="1")
    began = time.monotonic()
    ticker_stop, ticker = threading.Event(), None
    try:
        from .dependencies import browser_path
        selected_browser = browser_path(path.parents[3])
        if selected_browser:
            env["HYPERFRAMES_BROWSER_PATH"] = selected_browser
        report = path / "check.json"
        workers = render_workers(path.parents[3])
        job["workers"] = workers
        try:
            bundle_info = json.loads((path / "bundle.json").read_text())
            plan = estimate(bundle_info["duration"], path.parents[3], events=bundle_info["totals"]["events"], workers=workers, screen_lanes=bundle_info.get("screen_lanes"), height=bundle_info.get("height"), family=family_of(bundle_info.get("pace"))) or {}
        except (OSError, ValueError, KeyError):
            plan = {}
        progress, write_lock, last = {}, threading.Lock(), [0.0]
        stage_began = [time.monotonic()]

        def save(force=False):
            now = time.monotonic()
            if not force and now-last[0] < 1:
                return
            last[0] = now
            with write_lock:
                view = {k: v for k, v in progress.items() if not k.startswith("_")} | dict(elapsed=round(now-began))
                view.setdefault("label", "Checking layout" if job["stage"] == "checking" else "Starting render")
                if job["stage"] == "rendering" and not progress.get("fps") and plan.get("render_seconds"):
                    # Warm-up: count down from the learned render time instead of a misleading early rate.
                    left = plan["render_seconds"] - (now-stage_began[0])
                    if left > 0:
                        view["eta_seconds"] = round(left)
                if job["stage"] == "rendering" and progress.get("fps") and "_at" in progress:
                    # Count down between output lines from the last measured frame rate.
                    left = (progress["frames"]-progress["frame"])/progress["fps"] - (now-progress["_at"])
                    if left > 0:
                        view["eta_seconds"] = round(left)
                    else:
                        view.pop("eta_seconds", None)
                if job["stage"] == "checking" and plan.get("check_seconds") is not None:
                    left = plan["check_seconds"] - (now-stage_began[0])
                    # Past the learned check time: say "finishing", never a fake "0 s left".
                    if left > 0:
                        view["eta_seconds"] = round(left + plan.get("render_seconds", 0))
                    view["percent"] = max(0, min(99, round(100*(now-stage_began[0])/max(1, plan["check_seconds"]))))
                job["progress"] = view
                (path / "job.json").write_text(json.dumps(job), encoding="utf-8")

        def on_text(text, stage):
            if parse_progress(text, stage, progress):
                save()

        def tick():
            while not ticker_stop.wait(2.5):
                if job.get("state") == "running":
                    save(True)
        ticker = threading.Thread(target=tick, daemon=True, name="timeline-replay-progress")
        ticker.start()
        with (path / "render.log").open("w", encoding="utf-8") as log:
            job["stage"] = "checking"
            save(True)
            with report.open("w", encoding="utf-8") as out:
                checked = _stream(command+["check", str(path), "--json"], cwd=path, env=env, log=log, on_text=lambda t: on_text(t, "checking"), stdout=out)
            job["check"] = check_summary(report)
            check_seconds = time.monotonic()-began
            if checked:
                counts = ", ".join(f"{k} {v['errors']}" for k, v in (job["check"] or {}).get("sections", {}).items() if v["errors"])
                raise RuntimeError("composition check failed" + (f" ({counts} errors)" if counts else "") + "; see check.json")
            job["stage"] = "rendering"
            stage_began[0] = time.monotonic()
            progress.clear()
            save(True)
            rendered = _stream(command+["render", str(path), "--output", str(path / "timeline.mp4"), "--fps", "30", "--quality", "looks", "--workers", str(workers)],
                               cwd=path, env=env, log=log, on_text=lambda t: on_text(t, "rendering"))
            if rendered:
                raise RuntimeError("renderer exited with an error; see render.log")
        probe = subprocess.run([shutil.which("ffprobe"), "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height,r_frame_rate", "-of", "json", str(path / "timeline.mp4")], capture_output=True, text=True, timeout=30, check=True, env=env)
        meta = json.loads(probe.stdout)
        expected = json.loads((path / "bundle.json").read_text())["duration"]
        if abs(float(meta["format"]["duration"])-expected) > 0.25:
            raise ValueError("Encoded duration differs from replay duration")
        video = next(s for s in meta["streams"] if s["codec_type"] == "video")
        info = json.loads((path / "bundle.json").read_text())
        want = (int(info.get("width", 1920)), int(info.get("height", 1080)))
        if (video["width"], video["height"]) != want:
            raise ValueError(f"Encoded dimensions differ from {want[0]}x{want[1]}")
        numerator, denominator = video["r_frame_rate"].split("/")
        if abs(float(numerator)/float(denominator)-30) > .001:
            raise ValueError("Encoded frame rate differs from 30 fps")
        if (path / "timeline.mp4").stat().st_size == 0:
            raise ValueError("Empty video")
        job.update(state="complete", stage="verified", video="timeline.mp4", duration=float(meta["format"]["duration"]))
        job.pop("progress", None)
        try:
            info = json.loads((path / "bundle.json").read_text())
            events, screen_lanes, height, family = info["totals"]["events"], info.get("screen_lanes"), info.get("height"), family_of(info.get("pace"))
        except (OSError, ValueError, KeyError):
            events = screen_lanes = height = family = None
        _record_stats(path.parent.parent, float(meta["format"]["duration"]), time.monotonic()-began, check_seconds, events, workers, screen_lanes, height, family)
    except Exception as exc:
        detail = str(exc) if isinstance(exc, (RuntimeError, ValueError)) else "render/check failed; inspect the local render.log"
        job.update(state="failed", error=type(exc).__name__+": "+detail)
    finally:
        ticker_stop.set()
        if ticker is not None:
            ticker.join(5)
        job["finished"] = time.time()
        try:
            (path / "job.json").write_text(json.dumps(job), encoding="utf-8")
        finally:
            process_lock.close()
            with _lock:
                _running.discard(bundle)
