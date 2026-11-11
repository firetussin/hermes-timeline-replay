"""Write only explicitly labeled synthetic demo files under this package."""
import importlib.util
import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("timeline_fixture", root / "__init__.py", submodule_search_locations=[str(root)])
package = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = package
spec.loader.exec_module(package)
from timeline_fixture import core, visuals
from timeline_fixture.demo import make_demo

folder = root / "demo"
folder.mkdir(exist_ok=True)
model = make_demo("America/Chicago")
(folder / "replay.html").write_text(visuals.html(model,seconds=30,pace='social'), encoding="utf-8")
(folder / "index.html").write_text(visuals.html(model,seconds=30,interactive=False,pace='social'), encoding="utf-8")
(folder / "linear.html").write_text(visuals.html(model,seconds=30,pace='linear'),encoding='utf-8')
(folder / "events.json").write_text(json.dumps(model, indent=2), encoding="utf-8")
events = [core.normalize(dict(kind="tool", tool="read_file", time=1794175200+i*60, session=f"session-{i}"),f"Profile {i+1:02}","demo") for i in range(12)]
many = core.replay(events,"Multi profile fixture","UTC",["SYNTHETIC DEMO: twelve fabricated profile lanes."],demo=True)
(folder / "multi-profile.html").write_text(visuals.html(many,seconds=30),encoding="utf-8")
print("Generated synthetic single- and multi-chapter fixtures; no profiles read.")
