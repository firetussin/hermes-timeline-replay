"""Native Hermes registration; no I/O, services or model calls at import time."""
import json
import logging
import threading
import time
from pathlib import Path

from . import core

log = logging.getLogger(__name__)


class Recorder:
    def __init__(self, ctx):
        self.ctx = ctx
        self.starts = {}
        self.lock = threading.Lock()

    def hook(self, name, **kw):
        try:
            if not self.ctx.get_config("capture", True):
                return
            if str(kw.get("tool_name", "")).startswith("timeline_replay"):
                return
            home = core.active_home()
            profile = self.ctx.get_config("profile_label", "") or (home.name if home.parent.name == "profiles" else "default")
            now = time.time()
            kind = {"on_session_start": "session_start", "pre_llm_call": "turn_start", "post_llm_call": "turn_end", "on_session_end": "turn_end", "post_tool_call": "tool", "post_api_request": "model", "subagent_start": "delegate_start", "subagent_stop": "delegate_end"}[name]
            if name == "on_session_end" and not kw.get("interrupted"):
                return  # post_llm_call already records a successful turn, not task success.
            sid = kw.get("child_session_id") if name.startswith("subagent_") else kw.get("session_id")
            parent = kw.get("parent_session_id")
            status = kw.get("status", kw.get("child_status", "unknown"))
            status = {"ok": "success", "failed": "error", "complete": "completed"}.get(status, status)
            duration_ms = kw.get("duration_ms")
            if name == "on_session_end":
                status = "interrupted"
            key = (str(home), str(sid), str(kw.get("turn_id", "")))
            with self.lock:
                if kind == "turn_start":
                    self.starts[key] = now
                    # Never leak memory in a gateway that runs indefinitely.
                    self.starts = {k: t for k, t in self.starts.items() if now-t < 86400}
                elif kind == "turn_end":
                    started = self.starts.pop(key, None)
                    if started is not None:
                        duration_ms = max(0, now-started)*1000
            usage = kw.get("usage") or {}
            if not isinstance(usage, dict):
                usage = {}
            tokens = usage.get("total_tokens")
            if tokens is None:
                tokens = core.number(usage.get("input_tokens", usage.get("prompt_tokens"))) + core.number(usage.get("output_tokens", usage.get("completion_tokens")))
            raw = dict(kind=kind, time=now, session=sid, parent=parent, tool=kw.get("tool_name"),
                       model=str(kw.get("response_model") or kw.get("model") or "").split("/")[-1], status=status,
                       provider=kw.get("provider") if kind == "model" else None,
                       duration_ms=duration_ms, tokens=tokens,
                       id=kw.get("tool_call_id") or kw.get("api_request_id") or kw.get("turn_id"))
            if kind == "model" and kw.get("api_duration") is not None:
                raw["duration_ms"] = core.number(kw["api_duration"])*1000
            core.append(raw, profile, home)
        except Exception:
            # Capture is observational. Never return a directive or affect tools.
            log.warning("Timeline Replay skipped a metadata event", exc_info=False)


def register(ctx):
    from .service import tool, slash, setup_cli, cli_handler
    recorder = Recorder(ctx)
    for name in ("on_session_start", "on_session_end", "pre_llm_call", "post_llm_call", "post_tool_call", "post_api_request", "subagent_start", "subagent_stop"):
        def callback(_name=name, **kwargs):
            recorder.hook(_name, **kwargs)
        ctx.register_hook(name, callback)
    ctx.register_tool(name="timeline_replay", toolset="timeline_replay", schema={
        "name": "timeline_replay",
        "description": "Build a private, metadata-only animated replay across explicitly selected Hermes profiles. Creates HTML and a local render bundle. Render mode runs preinstalled HyperFrames/FFmpeg on this Hermes host. No publication or network downloads. Select demo for synthetic test data, build for real activity, jobs/status for progress.",
        "parameters": {"type": "object", "properties": {
            "action": {"type": "string", "enum": ["status", "dependencies", "setup", "demo", "build", "render", "jobs"]},
            "profiles": {"type": "array", "items": {"type": "string"}},
            "hours": {"type": "number", "minimum": 0.1, "maximum": 87600},
            "days": {"type": "number", "minimum": 0.1, "maximum": 3650},
            "all_time": {"type": "boolean"},
            "range": {"type": "string", "enum": ["24h","7d","30d","all","custom"]},
            "pace": {"type": "string", "enum": ["social","balanced","linear"]},
            "history": {"type": "boolean", "description": "Also read metadata from selected profiles' state.db; historical outcomes/durations are unknown."},
            "seconds": {"type": "number", "minimum": 10, "maximum": 180},
            "timezone": {"type": "string"}, "title": {"type": "string"},
            "bundle": {"type": "string", "description": "Existing bundle ID to render; use the HTML preview first."}
        }, "required": ["action"], "additionalProperties": False}}, handler=tool)
    ctx.register_command("replay", handler=slash, description="Animated Hermes activity timeline and video export", args_hint="demo | build | status | render ID | jobs")
    ctx.register_cli_command(name="replay", help="Private activity replays and local video export", setup_fn=setup_cli, handler_fn=cli_handler)
