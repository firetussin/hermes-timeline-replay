"""Live terminal HUD; read-only metadata, no renderer or inference required."""
import json
import sys
import time
from collections import Counter
from datetime import datetime

from . import core


def snapshot(profiles, minutes=60, home=None):
    if not .1 <= minutes <= 43200:
        raise ValueError("minutes must be between 0.1 and 43200")
    now=time.time()
    events,warnings=core.collect(profiles,now-minutes*60,now,False,home)
    lanes=[]
    for name in profiles:
        own=sorted((e for e in events if e["profile"]==name),key=lambda e:e["time"])
        bins=[0]*24
        for e in own:
            if e["kind"]=="tool":
                i=min(23,max(0,int((e["time"]-(now-minutes*60))/(minutes*60)*24)))
                bins[i]+=1
        top=max(bins) or 1
        glyphs=" .:-=+*#%@"
        lanes.append(dict(profile=name,tools=sum(e["kind"]=="tool" for e in own),errors=sum(e["status"]=="error" for e in own),spark="".join(glyphs[round(v/top*(len(glyphs)-1))] for v in bins),recent=(own[-1].get("tool") or own[-1]["kind"]) if own else "No captured activity"))
    return dict(ok=True,time=now,profiles=lanes,warnings=warnings,note="Live metadata only. Use replay build/render for animated HTML and MP4.")


def watch(profiles, minutes=60, once=False):
    tty=sys.stdout.isatty()
    try:
        while True:
            data=snapshot(profiles,minutes)
            if once or not tty:
                print(json.dumps(data,indent=2))
                return
            rows=["\x1b[2J\x1b[H\x1b[1;36mHERMES / TIMELINE LIVE\x1b[0m",datetime.now().strftime("%H:%M:%S")+f"  Last {minutes:g} minutes  ·  Ctrl+C to leave","",f"{'PROFILE':18} {'TOOLS':>7} {'ERRORS':>7}   ACTIVITY                  LATEST"]
            for lane in data["profiles"]:
                rows.append(f"{lane['profile'][:18]:18} {lane['tools']:7} {lane['errors']:7}   \x1b[36m{lane['spark']}\x1b[0m  {lane['recent']}")
            rows.extend(["","Captured metadata; unknown outcomes are not successes."]+data["warnings"])
            print("\n".join(rows),end="\n",flush=True)
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nTimeline watch stopped.")
