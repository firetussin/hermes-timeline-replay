"""Shared operations for the Hermes tool, slash command, CLI and Desktop."""
import argparse
import json
import shlex
import time
from pathlib import Path

from . import core, rendering, visuals, dependencies
from .version import VERSION, API, installed_version, check_client
from .demo import make_demo
from .canvas_views import PACES


def run(args, home=None):
    result = _run(args, home)
    if isinstance(result, dict):
        result.setdefault("version", VERSION)
        result.setdefault("api", API)
    return result


def _run(args, home=None):
    if not isinstance(args, dict):
        raise ValueError("Expected an argument object")
    check_client(args)
    action = args.get("action", "status")
    if action == "status":
        deps = dependencies.inspect(home)
        installed = installed_version()
        return dict(ok=True, version=VERSION, installed_version=installed, api=API, restart_required=bool(installed and installed != VERSION),
                    serving_profile=core.profile_label(home), has_data=core.data_dir(home).is_dir(), profiles=list(core.sources(home)),
                    source_names={k: (core.profile_display_name(v) if k == "current" else k) for k, v in core.sources(home).items()},
                    event_limits=list(core.EVENT_LIMITS), resolutions=list(visuals.RESOLUTIONS), workers=rendering.render_workers(home),
                    workers_setting=dependencies.settings(home).get("workers", 0), renderer_ready=deps["ready"], dependencies=deps,
                    note="Profile enrollment is CLI-only. No live inference or transcript capture. Enable capture in each profile for future events; history=true reads selected state.db metadata.")
    if action == "dependencies":
        return dict(ok=True, dependencies=dependencies.inspect(home))
    if action == "setup":
        return dependencies.setup_request(home)
    if action == "settings":
        # Desktop Settings → Export: persist the render worker count (0 = automatic) on this host.
        workers = args.get("workers")
        if not isinstance(workers, int) or isinstance(workers, bool):
            raise ValueError("workers must be an integer")
        dependencies.configure(workers=workers, home=home)
        return dict(ok=True, workers=rendering.render_workers(home), workers_setting=workers)
    if action == "jobs":
        return dict(ok=True, jobs=rendering.status(home))
    if action == "render":
        job = rendering.start(args.get("bundle"), home)
        return dict(ok=True, job=job, note="Local render started on this Hermes host. Poll jobs for completion; no video is claimed until verified.")
    if action not in ("demo", "build"):
        raise ValueError("Unknown action")
    seconds = args.get("seconds", 60)
    if isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or not 10 <= seconds <= 180:
        raise ValueError("seconds must be between 10 and 180")
    zone = args.get("timezone", "America/Chicago")
    if not isinstance(zone, str):
        raise ValueError("timezone must be an IANA timezone name")
    pace = args.get("pace", "social")
    if pace not in PACES:
        raise ValueError("pace must be social, balanced or linear")
    models = args.get("models", True)
    if not isinstance(models, bool):
        raise ValueError("models must be true or false")
    lanes = str(args.get("lanes", "auto"))
    if lanes not in ("auto", "4", "all"):
        raise ValueError("lanes must be auto, 4 or all")
    resolution = str(args.get("resolution", "1080p"))
    resolution = {"4k": "2160p", "uhd": "2160p", "720": "720p", "1080": "1080p", "1440": "1440p", "2160": "2160p"}.get(resolution.lower(), resolution)
    if resolution not in visuals.RESOLUTIONS:
        raise ValueError("resolution must be one of " + ", ".join(visuals.RESOLUTIONS))
    limit = args.get("events_limit", core.MAX_EVENTS)
    if isinstance(limit, bool) or limit not in core.EVENT_LIMITS:
        raise ValueError("events_limit must be one of " + ", ".join(str(x) for x in core.EVENT_LIMITS))
    range_label = "Synthetic demo"
    if action == "demo":
        model = make_demo(zone)
    else:
        hours = args.get("hours")
        if hours is None:
            hours = 24
        if args.get("days") is not None:
            days = args["days"]
            if isinstance(days, bool) or not isinstance(days, (int,float)) or not .1 <= days <= 3650:
                raise ValueError("days must be between 0.1 and 3650")
            hours = days * 24
        range_name = args.get("range")
        if range_name:
            if range_name not in ("24h", "7d", "30d", "all", "custom"):
                raise ValueError("Unknown time range")
            if range_name in ("24h", "7d", "30d"):
                hours = {"24h":24,"7d":168,"30d":720}[range_name]
        if not isinstance(args.get("all_time",False),bool):
            raise ValueError("all_time must be true or false")
        all_time = args.get("all_time",False) or range_name == "all"
        if isinstance(hours, bool) or not isinstance(hours, (int, float)) or not .1 <= hours <= 87600:
            raise ValueError("hours must be between 0.1 and 87600")
        selected = args.get("profiles", ["current"])
        if not isinstance(selected, list) or any(not isinstance(x, str) for x in selected):
            raise ValueError("profiles must be a list of enrolled labels")
        if not selected:
            raise ValueError("Select at least one enrolled profile")
        if not isinstance(args.get("history", False), bool):
            raise ValueError("history must be true or false")
        now = time.time()
        events, warnings = core.collect(selected, 0 if all_time else max(0,now-hours*3600), now, bool(args.get("history", False)), home, limit)
        range_label = "All available" if all_time else {24: "Last 24 hours", 168: "Last 7 days", 720: "Last 30 days"}.get(hours) or (f"Last {hours/24:g} days" if hours >= 24 else f"Last {hours:g} hours")
        if all_time:
            warnings.append("All available history requested. Capture retains 30 days; older activity depends on saved session metadata. Per-source and total event limits still apply.")
        model = core.replay(events, args.get("title", "Hermes activity"), zone, warnings, limit=limit)
    result = visuals.bundle(model, seconds, home, pace=pace, models=models, lanes=lanes, resolution=resolution, meta=dict(range_label=range_label))
    per_screen = 4 if lanes == "4" else 16
    result["estimate"] = rendering.estimate(result["duration"], home, events=result["totals"]["events"], screen_lanes=min(len(model["lanes"]), per_screen), height=visuals.RESOLUTIONS[resolution][1], family=rendering.family_of(pace))
    return result


def tool(args, **kwargs):
    try:
        return json.dumps(run(args))
    except (ValueError, OSError, KeyError) as exc:
        # No raw path-bearing OS errors in the conversation.
        return json.dumps({"ok": False, "error": str(exc) if isinstance(exc, ValueError) else "Replay data could not be read or written; inspect local permissions."})


def parser():
    p = argparse.ArgumentParser(prog="hermes replay")
    setup_cli(p)
    return p


def setup_cli(p):
    sub = p.add_subparsers(dest="action")
    sub.add_parser("status")
    sub.add_parser("jobs")
    sub.add_parser("dependencies", help="Check all video prerequisites without downloading anything")
    setup = sub.add_parser("setup", help="Review installation steps or persist existing renderer/browser paths")
    setup.add_argument("--hyperframes")
    setup.add_argument("--browser")
    setup.add_argument("--workers", type=int, help="Render workers (browser processes); 0 = automatic (half the cores, max 4)")
    for name in ("demo", "build"):
        q = sub.add_parser(name)
        q.add_argument("--seconds", type=float, default=30, help="Total video length, finale included")
        q.add_argument("--no-models", dest="models", action="store_false", help="Hide model/provider readouts and switch markers")
        q.add_argument("--lanes", choices=["auto", "4", "all"], default="auto", help="Lanes per screen: auto/all stack up to 16 in every pace, 4 = chapter look")
        q.add_argument("--resolution", choices=["720p", "1080p", "1440p", "2160p"], default="1080p", help="MP4 size; larger is much slower on software GL")
        q.add_argument("--events-limit", dest="events_limit", type=int, choices=[20000, 50000, 100000], default=20000, help="Replay event cap; higher means longer checks and larger previews")
        q.add_argument("--timezone", default="America/Chicago")
        q.add_argument("--pace", choices=list(PACES), default="social")
        if name == "build":
            q.add_argument("--profiles", nargs="+", default=["current"])
            group = q.add_mutually_exclusive_group()
            group.add_argument("--hours", type=float)
            group.add_argument("--days", type=float)
            group.add_argument("--all-time", action="store_true")
            q.add_argument("--history", action="store_true")
            q.add_argument("--title", default="Hermes activity")
    q = sub.add_parser("render")
    q.add_argument("bundle")
    q = sub.add_parser("enroll", help="Operator-only: add an explicit profile home as a replay source")
    q.add_argument("name")
    q.add_argument("path")
    q = sub.add_parser("import", help="Operator-only: explicit JSON metadata file to standalone replay")
    q.add_argument("path")
    q.add_argument("--seconds", type=float, default=60)
    q.add_argument("--timezone", default="America/Chicago")
    q.add_argument("--pace", choices=list(PACES), default="social")
    q.add_argument("--no-models", dest="models", action="store_false")
    q = sub.add_parser("watch", help="Live terminal activity HUD from captured metadata; Ctrl+C to stop")
    q.add_argument("--profiles",nargs="+",default=["current"])
    q.add_argument("--minutes",type=float,default=60)
    q.add_argument("--once",action="store_true")
    p.set_defaults(func=cli_handler)


def cli_handler(ns):
    try:
        args = vars(ns)
        if ns.action == "setup":
            if ns.hyperframes or ns.browser or ns.workers is not None:
                dependencies.configure(ns.hyperframes,ns.browser,workers=ns.workers)
            result = dependencies.setup_request()
        elif ns.action == "watch":
            from .terminal import watch
            return watch(ns.profiles,ns.minutes,once=ns.once)
        elif ns.action == "enroll":
            core.enroll(ns.name, ns.path)
            result = dict(ok=True, profile=ns.name, note="Source enrolled read-only. Its capture plugin is not automatically installed or enabled.")
        elif ns.action == "import":
            p = Path(ns.path).expanduser().resolve()
            if p.stat().st_size > 20_000_000:
                raise ValueError("Import must be smaller than 20 MB")
            payload = json.loads(p.read_text(encoding="utf-8"))
            events = payload.get("events") if isinstance(payload, dict) else payload
            if not isinstance(events, list) or not events or len(events) > core.MAX_EVENTS or any(not isinstance(e, dict) for e in events):
                raise ValueError("Import needs 1–20000 metadata events")
            normalized = [core.normalize(e, e.get("profile", "imported"), "import") for e in events]
            model = core.replay(normalized, "Imported Hermes activity", ns.timezone, ["Explicit JSON import: provenance and timestamps are supplied by the operator."])
            result = visuals.bundle(model, ns.seconds, pace=ns.pace, models=ns.models)
        else:
            result = run(args)
        print(json.dumps(result, indent=2))
        # The worker is in-process; keep a terminal render command alive until it ends.
        if ns.action == "render":
            while ns.bundle in rendering._running:
                time.sleep(.25)
            job = next(j for j in rendering.status() if j["id"] == ns.bundle)
            print(json.dumps(job, indent=2))
            if job["state"] != "complete":
                raise SystemExit(1)
    except (ValueError, OSError, KeyError) as exc:
        print(json.dumps({"ok": False, "error": str(exc) if isinstance(exc, ValueError) else "Local replay operation failed; check source files and permissions."}))
        raise SystemExit(1)


def slash(raw_args="", **kwargs):
    try:
        parts = shlex.split(raw_args or "status")
        if parts and parts[0] == "watch":
            return "The live HUD runs in a terminal: hermes replay watch --profiles current. Chat can build and render the same animated HTML/MP4 with /replay build and /replay render."
        if parts and parts[0] == "setup" and len(parts)>1:
            return "Renderer paths are configured in the operator terminal with hermes replay setup. Use /replay setup to prepare an install request."
        if parts and parts[0] in ("enroll", "import"):
            return "Profile enrollment and file imports are terminal-only: hermes replay enroll / import."
        p = parser()
        ns = p.parse_args(parts)
        result = run(vars(ns))
        if result.get("bundle"):
            eta = result.get("estimate")
            eta_text = f" Export takes about {max(1, round(eta['seconds']/60))} min on this host." if eta else ""
            return f"Replay {result['bundle']} prepared ({result['duration']:g}s video).{eta_text} HTML: {result['html']}\nPreview it in Timeline Replay, then /replay render {result['bundle']} for MP4 on this Hermes host."
        if ns.action == "jobs":
            jobs = result["jobs"]
            completed = [j for j in jobs if j["state"] == "complete"]
            text = json.dumps(result, indent=2)
            if completed:
                path = rendering.bundle_path(completed[0]["id"]) / "timeline.mp4"
                text += "\nMEDIA:"+str(path)
            return text
        return json.dumps(result, indent=2)
    except SystemExit:
        return "Usage: /replay demo | build --hours 24 --history --profiles current | render BUNDLE_ID | jobs | status"
    except (ValueError, OSError, KeyError) as exc:
        return str(exc) if isinstance(exc, ValueError) else "Replay operation failed; check local permissions."
