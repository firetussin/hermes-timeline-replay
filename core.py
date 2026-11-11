"""Metadata-only events, profile-local storage and deterministic replay models."""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sqlite3
import time
from collections import Counter
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

NAME = "timeline-replay"
MAX_EVENTS = 20000  # capture retention per profile, and the default replay cap
EVENT_LIMITS = (20000, 50000, 100000)  # replay caps offered in Settings
KINDS = {"session_start", "session_end", "turn_start", "turn_end", "tool", "model", "delegate_start", "delegate_end", "milestone"}
STATUSES = {"success", "error", "blocked", "cancelled", "interrupted", "unknown", "completed"}


def active_home() -> Path:
    # Resolve at call time: Hermes can run several profiles in one process.
    try:
        from hermes_cli.config import get_hermes_home
        return Path(get_hermes_home()).resolve()
    except ImportError:
        return Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes")).expanduser().resolve()


def profile_label(home: Path | None = None) -> str:
    """The Hermes profile this backend serves: <root>/profiles/<name>, else "default"."""
    home = home or active_home()
    return home.name if home.parent.name == "profiles" else "default"


def profile_display_name(home: Path) -> str:
    """What viewers should see for a profile home: Hermes' presentation display_name from
    profile.yaml when set, else the profile name ("Default" for the root profile)."""
    try:
        text = (Path(home) / "profile.yaml").read_text(encoding="utf-8")
        m = re.search(r"^display_name:\s*['\"]?([^'\"\n#]+?)['\"]?\s*$", text, re.M)
        if m and label(m.group(1).strip(), ""):
            return label(m.group(1).strip(), "")
    except OSError:
        pass
    name = profile_label(Path(home))
    return "Default" if name == "default" else label(name, "Profile")


def data_dir(home: Path | None = None) -> Path:
    return (home or active_home()) / "plugin-data" / NAME


def label(value, fallback="unknown", limit=48):
    """No paths, URLs, arbitrary prose or inline credentials in metadata labels."""
    text = str(value or "")
    if not re.fullmatch(r"[\w .:@+\-]{1,80}", text, flags=re.UNICODE):
        return fallback
    if re.search(r"(?i)(sk-|ghp_|bearer|token=|secret|password|api.key)", text):
        return fallback
    return text[:limit]


def opaque(value):
    if not value:
        return "unknown"
    return hashlib.sha256(str(value).encode()).hexdigest()[:12]


def timestamp(value):
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        result = float(value)
    elif isinstance(value, str):
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            raise ValueError("Timestamps must include a timezone")
        result = dt.timestamp()
    else:
        raise ValueError("Missing or invalid timestamp")
    if not math.isfinite(result) or result < 0 or result > 253402300799:
        raise ValueError("Timestamp out of range")
    return result


def number(value, default=0, maximum=10**12):
    try:
        n = float(value)
        return min(maximum, max(0, n)) if math.isfinite(n) else default
    except (TypeError, ValueError):
        return default


def normalize(raw, profile="default", origin="import"):
    """Strict projection: never retain arbitrary user-provided fields."""
    if not isinstance(raw, dict) or raw.get("kind") not in KINDS:
        raise ValueError("Unsupported event kind")
    t = timestamp(raw.get("time"))
    duration = raw.get("duration_ms")
    duration = number(duration) / 1000 if duration is not None else None
    status = str(raw.get("status", "unknown"))
    event = dict(
        time=t, kind=raw["kind"], profile=label(profile, "profile"),
        session=opaque(raw.get("session")), parent=opaque(raw.get("parent")),
        tool=label(raw.get("tool"), "tool", 64) if raw.get("tool") else "",
        model=label(str(raw.get("model")).strip().split("/")[-1], "", 64) if raw.get("model") else "",
        status=status if status in STATUSES else "unknown",
        duration=duration, tokens=int(number(raw.get("tokens"))),
        origin=label(origin),
    )
    # Milestone copy is not accepted from arbitrary free text. Fixed labels only.
    if event["kind"] == "milestone":
        event["tool"] = "Recorded milestone"
    identity = {**event, "correlation": opaque(raw.get("id"))}
    event["id"] = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()[:24]
    # Provider is display metadata added in 0.2.2. It stays out of the identity hash
    # so ids, and capture/history deduplication, match earlier versions. A short
    # label only: endpoint URLs/base_url are never stored.
    event["provider"] = label(raw.get("provider"), "", 40) if raw.get("provider") else ""
    return event


def append(raw, profile, home=None):
    path = data_dir(home)
    path.mkdir(parents=True, exist_ok=True)
    event = normalize(raw, profile, "hook")
    with closing(sqlite3.connect(path / "events.db", timeout=0.15)) as db:
        db.execute("CREATE TABLE IF NOT EXISTS events (id TEXT PRIMARY KEY, time REAL NOT NULL, payload TEXT NOT NULL)")
        db.execute("INSERT OR IGNORE INTO events VALUES (?, ?, ?)", (event["id"], event["time"], json.dumps(event)))
        # Bounded retention on the plugin's database only, never on Hermes state.
        db.execute("DELETE FROM events WHERE time < ?", (time.time() - 30 * 86400,))
        db.execute("DELETE FROM events WHERE id IN (SELECT id FROM events ORDER BY time DESC LIMIT -1 OFFSET ?)", (MAX_EVENTS,))
        db.commit()


def read_store(home, since, until, limit=MAX_EVENTS):
    path = data_dir(home) / "events.db"
    if not path.is_file():
        return [], []
    with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=0.5)) as db:
        db.execute("PRAGMA query_only=ON")
        rows = db.execute("SELECT payload FROM events WHERE time BETWEEN ? AND ? ORDER BY time DESC LIMIT ?", (since, until, limit + 1)).fetchall()
    warnings = ["Capture limit reached; narrow the time range."] if len(rows) > limit else []
    return [json.loads(row[0]) for row in rows[:limit]], warnings


def read_history(home, profile, since, until, limit=MAX_EVENTS):
    """Selected Hermes state.db only; never SELECT transcript or command fields."""
    session_cap = max(2000, limit // 10)  # session rows scale with the chosen event cap
    path = home / "state.db"
    if not path.is_file():
        return [], [f"{profile}: no state.db; no history imported."]
    events, warnings = [], []
    with closing(sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True, timeout=0.5)) as db:
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA query_only=ON")
        db.execute("BEGIN")
        cols = {r[1] for r in db.execute("PRAGMA table_info(sessions)")}
        if not {"id", "started_at"} <= cols:
            return [], [f"{profile}: unsupported session schema."]
        optional = [c for c in ("ended_at", "parent_session_id", "model", "billing_provider", "input_tokens", "output_tokens") if c in cols]
        projection = ",".join(["id", "started_at"] + optional)
        rows = db.execute(f"SELECT {projection} FROM sessions WHERE started_at <= ? AND (" + ("ended_at IS NULL OR ended_at >= ?" if "ended_at" in cols else "started_at >= ?") + ") ORDER BY started_at DESC LIMIT ?", (until, since, 2001)).fetchall()
        if len(rows) > session_cap:
            warnings.append(f"{profile}: session limit reached; narrow range.")
        ids = []
        for row in rows[:session_cap]:
            s = dict(row)
            ids.append(s["id"])
            base = dict(session=s["id"], parent=s.get("parent_session_id"), model=s.get("model"), provider=s.get("billing_provider"))
            # Session token totals are stored once per session; count them at the
            # session end (or start, for a session still open) - never twice.
            tokens = number(s.get("input_tokens")) + number(s.get("output_tokens"))
            ended = s.get("ended_at") is not None and since <= s["ended_at"] <= until
            if since <= s["started_at"] <= until:
                events.append(normalize(dict(base, kind="session_start", time=s["started_at"], id=f"start:{s['id']}", tokens=0 if ended else tokens), profile, "history"))
            if ended:
                # Ended session does not imply task success.
                events.append(normalize(dict(base, kind="session_end", time=s["ended_at"], id=f"end:{s['id']}", tokens=tokens), profile, "history"))
        mc = {r[1] for r in db.execute("PRAGMA table_info(messages)")}
        if not {"id", "session_id", "timestamp", "role", "tool_name"} <= mc:
            warnings.append(f"{profile}: tool history unavailable in this schema.")
        elif ids:
            # Tool result rows give the stored timestamp and name, not a reliable
            # execution start, duration or success. Never read content/tool_calls.
            query = "SELECT id,session_id,timestamp,tool_name FROM messages WHERE role='tool' AND timestamp BETWEEN ? AND ?"
            if "active" in mc:
                query += " AND active=1"
            query += " AND session_id IN ("+",".join("?" for _ in ids)+") ORDER BY timestamp DESC LIMIT ?"
            messages = db.execute(query, (since, until, *ids, limit + 1)).fetchall()
            selected = set(ids)
            for row in messages[:limit]:
                if row["session_id"] in selected:
                    events.append(normalize(dict(kind="tool", time=row["timestamp"], session=row["session_id"], tool=row["tool_name"], id=f"message:{row['id']}"), profile, "history"))
            if len(messages) > limit:
                warnings.append(f"{profile}: tool limit reached; narrow range.")
        warnings.append(f"{profile}: history tool timestamps are stored message times; duration and result status are unknown.")
        if "input_tokens" in cols:
            warnings.append(f"{profile}: history token totals are per session and counted when each session ends.")
    return events, warnings


def sources(home=None):
    home = home or active_home()
    result = {"current": home}
    path = data_dir(home) / "sources.json"
    if path.is_file():
        for name, value in json.loads(path.read_text(encoding="utf-8")).items():
            result[name] = Path(value).expanduser().resolve()
    return result


def enroll(name, path, home=None):
    if label(name, "") != name or name == "current":
        raise ValueError("Use a short profile label other than current")
    root = Path(path).expanduser().resolve()
    if not root.is_dir() or not ((root / "state.db").is_file() or (data_dir(root) / "events.db").is_file()):
        raise ValueError("Source needs state.db or timeline-replay capture data")
    home = home or active_home()
    current = sources(home)
    current.pop("current", None)
    current[name] = root
    folder = data_dir(home)
    folder.mkdir(parents=True, exist_ok=True)
    # Enrollment is an operator CLI action, never an agent tool or HTTP route.
    (folder / "sources.json").write_text(json.dumps({k: str(v) for k, v in current.items()}, indent=2), encoding="utf-8")


def collect(selected, since, until, history=False, home=None, limit=MAX_EVENTS):
    if limit not in EVENT_LIMITS:
        raise ValueError("Event limit must be one of " + ", ".join(f"{x:,}" for x in EVENT_LIMITS))
    allowed = sources(home)
    if not selected:
        selected = ["current"]
    if len(selected) > 16 or any(name not in allowed for name in selected):
        raise ValueError("Choose at most 16 explicitly enrolled profile labels")
    all_events, warnings = [], []
    for name in dict.fromkeys(selected):
        root = allowed[name]
        try:
            captured, warn = read_store(root, since, until, limit)
            # "current" is only the internal key for this backend's own home; viewers see
            # the profile's real (display) name in lanes, cards, captions and the finale.
            shown = profile_display_name(root) if name == "current" else name
            for event in captured:
                event["profile"] = shown
            warnings.extend(warn)
            all_events.extend(captured)
            if history:
                historical, warn = read_history(root, shown, since, until, limit)
                warnings.extend(warn)
                # Never double-count one session from capture and history.
                live_sessions = {x["session"] for x in captured}
                all_events.extend(x for x in historical if x["session"] not in live_sessions)
                if live_sessions:
                    warnings.append(f"{name}: history omitted for captured sessions to avoid duplicate counts; earlier activity in those sessions may be absent.")
        except (OSError, sqlite3.Error, ValueError, KeyError):
            warnings.append(f"{name}: source unavailable; no fabricated replacement events.")
    if len(all_events) > limit:
        warnings.append(f"Selection exceeded {limit:,} events. Showing the newest {limit:,}; older events were omitted. Raise the event limit in Settings or narrow the range for complete coverage.")
        all_events = sorted(all_events, key=lambda e:e["time"], reverse=True)[:limit]
    return all_events, warnings


def replay(events, title="Hermes activity", timezone_name="America/Chicago", warnings=(), demo=False, limit=MAX_EVENTS):
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
    try:
        ZoneInfo(timezone_name)
    except (ZoneInfoNotFoundError, ValueError):
        raise ValueError("Timezone unavailable; install tzdata or use UTC")
    events = sorted({(e["profile"], e["id"]): e for e in events}.values(), key=lambda e: (e["time"], e["id"]))
    if not events:
        raise ValueError("No recorded activity in this selection. Try demo, a wider range, or explicit history import.")
    if len(events) > max(limit, MAX_EVENTS):
        raise ValueError("Too many events; select a shorter range or fewer profiles")
    profiles = sorted({e["profile"] for e in events})
    lane_keys = sorted({(e["profile"], e["session"]) for e in events})
    # Bound visual complexity. Long histories collapse sessions into profile lanes.
    grouped = len(lane_keys) > 32
    if grouped:
        lane_keys = [(p, "all") for p in profiles]
    lanes = [{"id": i, "profile": p, "session": s, "label": f"{p} / {'all agents' if s == 'all' else s[:6]}"} for i, (p, s) in enumerate(lane_keys)]
    lookup = {(p, s): i for i, (p, s) in enumerate(lane_keys)}
    start = min(e["time"] - (e["duration"] or 0) for e in events)
    end = max(e["time"] for e in events)
    span = max(1.0, end - start)
    safe_events = [dict(e, provider=e.get("provider", ""), lane=lookup[(e["profile"], "all" if grouped else e["session"])], offset=e["time"]-start) for e in events]
    kinds = Counter(e["kind"] for e in events)
    return {"schema": "hermes.timeline-replay.v1", "title": label(title, "Hermes activity", 64), "timezone": timezone_name,
            "demo": bool(demo), "start": start, "end": end, "span": span, "profiles": profiles, "lanes": lanes,
            "events": safe_events, "warnings": list(warnings) + (["More than 32 sessions: visual lanes grouped by profile; all events retained."] if grouped else []),
            "totals": {"events": len(events), "profiles": len(profiles), "sessions": len({(e["profile"], e["session"]) for e in events}),
                       "tools": kinds["tool"], "errors": sum(e["status"] == "error" for e in events),
                       "tokens": sum(e["tokens"] for e in events), "unknown_status": sum(e["status"] == "unknown" for e in events)}}
