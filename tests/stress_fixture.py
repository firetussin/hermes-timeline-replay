"""Synthetic, real-shaped stress fixtures for the export layout gate.

Shapes mirror the CT114 failures reported on 2026-11-10 (counts only, no real data):
  medium: 7 profiles, ~1,160 events, ~1,030 tool calls over 7 days, >32 sessions
  large:  10 profiles, ~8,060 events, ~7,400 tool calls over 7 days
Profile names include long labels so lane labels hit the width limit. Every event is
fabricated and the model is flagged demo=True.

Usage: python tests/stress_fixture.py OUT_DIR [medium|large] [social|balanced|linear|orbit|galaxy|skyline|river|pulse|clock|neural|rain|ridgelines] [seconds]
Writes OUT_DIR/index.html (export composition) and OUT_DIR/replay.html (interactive).
"""
import importlib.util
import random
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("timeline_stress", root / "__init__.py", submodule_search_locations=[str(root)])
package = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = package
spec.loader.exec_module(package)
from timeline_stress import core, visuals  # noqa: E402

SHAPES = {
    "medium": dict(profiles=["Researchbot", "Researcher", "YouTube", "current", "Builder", "Reviewer", "Ops"], events=1159, tool_share=.889),
    "large": dict(profiles=["Researchbot", "Researcher", "YouTube", "current", "Builder", "Reviewer", "Ops",
                            "Longer-Profile-Name", "Scheduler", "Archivist"], events=8064, tool_share=.917),
    # Sparse all-time shape (CT114 a0659dc2): weeks of silence between bursts, three chapters.
    "alltime": dict(profiles=["Researchbot", "Researcher", "YouTube", "current", "Builder", "Reviewer", "Ops",
                              "EVE", "Scout", "Library", "Sonny"], events=20000, tool_share=.93, days=72, bursts=40),
}


MODELS = [("hermes-4-405b", "nous"), ("deepseek/deepseek-v4-0324-extended-context", "openrouter"), ("qwen3-coder", "local-llama-server"), ("hermes-4-70b", "nous")]


def make(shape="medium", seed=7):
    cfg = SHAPES[shape]
    rng = random.Random(seed)
    start = 1794175200  # fixed fixture epoch, not the current clock
    span = cfg.get("days", 7) * 86400
    events = []
    # Bursty activity: a few dense working sessions per profile, quiet nights.
    bursts = [(rng.choice(cfg["profiles"]), rng.uniform(0, span - 3600)) for _ in range(cfg.get("bursts", 60))]
    for i in range(cfg["events"]):
        profile, center = bursts[i % len(bursts)] if i else (cfg["profiles"][0], 0.0)
        t = start + max(0.0, min(span, center + rng.expovariate(1 / 600)))
        session = f"s{profile[:3].lower()}{int(center) // 3600:04d}"
        if i == cfg["events"] - 1:
            t = start + span  # pin the end so the last tick has a nearby event
        if rng.random() < cfg["tool_share"]:
            raw = dict(kind="tool", tool=rng.choice(["web_search", "read_file", "terminal", "write_file", "browser_open"]),
                       status=rng.choice(["success"] * 8 + ["error", "unknown"]), duration_ms=rng.randint(200, 90000))
        else:
            raw = dict(kind=rng.choice(["model", "turn_start", "turn_end"]), tokens=rng.randint(100, 4000))
            if raw["kind"] == "model":
                # Each burst uses one model, so lanes show recorded switches between bursts.
                name, provider = MODELS[(i % len(bursts) + len(profile)) % len(MODELS)]
                raw.update(model=name, provider=provider)
        raw.update(time=t, session=session, id=f"stress-{i}")
        events.append(core.normalize(raw, profile, "demo"))
    return core.replay(events, "Stress fixture", "America/Chicago",
                       ["SYNTHETIC STRESS FIXTURE: fabricated real-shaped events for layout checks."], demo=True)


if __name__ == "__main__":
    out = Path(sys.argv[1])
    shape = sys.argv[2] if len(sys.argv) > 2 else "medium"
    pace = sys.argv[3] if len(sys.argv) > 3 else "social"
    seconds = int(sys.argv[4]) if len(sys.argv) > 4 else 34
    lanes = sys.argv[5] if len(sys.argv) > 5 else "auto"
    resolution = sys.argv[6] if len(sys.argv) > 6 else "1080p"
    out.mkdir(parents=True, exist_ok=True)
    model = make(shape)
    (out / "index.html").write_text(visuals.html(model, seconds, interactive=False, pace=pace, lanes=lanes, resolution=resolution), encoding="utf-8")
    (out / "replay.html").write_text(visuals.html(model, seconds, interactive=True, pace=pace, lanes=lanes), encoding="utf-8")
    tools = sum(e["kind"] == "tool" for e in model["events"])
    print(f"{shape}/{pace}/{seconds}s: {len(model['events'])} events, {tools} tools, {len(model['profiles'])} profiles, {len(model['lanes'])} lanes")
