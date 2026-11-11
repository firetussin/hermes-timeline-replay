"""Explicit synthetic fixture, never presented as observed Hermes history."""
from .core import normalize, replay


def make_demo(timezone="America/Chicago"):
    start = 1794175200  # Fixed fixture, not the current clock.
    events = []
    def add(offset, kind, profile, session, **kw):
        events.append(normalize(dict(time=start+offset, kind=kind, session=session, id=f"demo-{len(events)}", **kw), profile, "demo"))
    add(0, "session_start", "Coordinator", "chief")
    add(10, "turn_start", "Coordinator", "chief", model="local-planner")
    for i, profile in enumerate(("Research", "Builder", "Reviewer")):
        sid = "worker-"+str(i)
        add(80+i*90, "delegate_start", profile, sid, parent="chief")
        add(90+i*90, "turn_start", profile, sid)
        for j in range(7):
            t = 150+i*300+j*480
            add(t, "tool", profile, sid, tool=("web_search", "write_file", "terminal")[i], duration_ms=(20+j*5)*1000, status="error" if i == 1 and j == 3 else "success")
            add(t+40, "model", profile, sid, model=("local-research", "local-code", "local-review")[i], tokens=900+150*j)
        add(3600+i*450, "turn_end", profile, sid, duration_ms=3000000)
        add(3700+i*450, "delegate_end", profile, sid, parent="chief", status="completed")
    add(4700, "tool", "Coordinator", "chief", tool="read_file", status="success", duration_ms=800)
    add(4800, "turn_end", "Coordinator", "chief", duration_ms=4790000)
    return replay(events, "Hermes timeline demo", timezone, ["SYNTHETIC DEMO: all events are fabricated fixtures for testing; no real profiles were read."], demo=True)
