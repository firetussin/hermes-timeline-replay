"""Bounded monotonic real-time to video-time mapping for shareable replays."""


def finale(pace):
    return {"social": 4, "balanced": 6, "linear": 8}[pace]


def split(total, pace):
    """Requested seconds are the whole video. The finale comes out of that total and
    never takes more than 30% of it."""
    end = min(finale(pace), round(total * .3, 2))
    return round(total - end, 2), end


def anchors(model, pace):
    if pace not in ("social", "balanced", "linear"):
        raise ValueError("Unknown pacing mode")
    span = model["span"]
    times = sorted({0.0, span, *(max(0.0, min(span, e["offset"])) for e in model["events"])})
    if len(times) > 512:
        times = [times[round(i*(len(times)-1)/511)] for i in range(512)]
    exponent = {"social": .28, "balanced": .65, "linear": 1.0}[pace]
    weights = [(b-a)**exponent for a,b in zip(times,times[1:])]
    total = sum(weights) or 1
    result = [{"real": times[0], "screen": 0.0}]
    accumulated = 0.0
    for t, weight in zip(times[1:],weights):
        accumulated += weight
        result.append({"real":t,"screen":accumulated/total})
    result[-1]["screen"] = 1.0
    return result
