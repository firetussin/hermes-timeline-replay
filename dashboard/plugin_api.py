"""Hermes authenticates the shared backend namespace; no standalone server."""
import importlib.util
import json
import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

# Dashboard modules can be loaded outside the agent plugin's Python package.
_root = Path(__file__).resolve().parents[1]
_name = "hermes_timeline_replay_backend"
if _name not in sys.modules:
    _spec = importlib.util.spec_from_file_location(_name, _root / "__init__.py", submodule_search_locations=[str(_root)])
    _module = importlib.util.module_from_spec(_spec)
    sys.modules[_name] = _module
    _spec.loader.exec_module(_module)
from hermes_timeline_replay_backend import service, rendering, visuals
from hermes_timeline_replay_backend.demo import make_demo

router = APIRouter()


@router.get("/demo-preview")
def demo_preview():
    # Pure sample: no profile reads and no render-bundle writes on page open.
    return {"html": visuals.html(make_demo("UTC"), seconds=30, pace="social"), "demo": True}


@router.get("/status")
def status():
    return service.run({"action": "status"})


@router.post("/action")
def action(body: dict):
    try:
        # Neither arbitrary paths nor profile enrollment are remotely exposed.
        return service.run(body)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from None
    except OSError:
        raise HTTPException(500, "Local replay data is unavailable") from None


@router.get("/preview/{bundle}")
def preview(bundle: str):
    try:
        path = rendering.bundle_path(bundle)
        return {"html": (path / "replay.html").read_text(encoding="utf-8")}
    except (ValueError, OSError):
        raise HTTPException(404, "Replay not found") from None


@router.get("/download/{bundle}/{kind}")
def download(bundle: str, kind: str):
    names = {"html": ("replay.html", "text/html"), "video": ("timeline.mp4", "video/mp4"), "data": ("events.json", "application/json")}
    try:
        if kind not in names:
            raise ValueError()
        path = rendering.bundle_path(bundle)
        name, mime = names[kind]
        file = path / name
        if not file.is_file():
            raise ValueError()
        if kind == "video" and json.loads((path / "job.json").read_text()).get("state") != "complete":
            raise ValueError()
        return FileResponse(file, media_type=mime, filename=name)
    except (ValueError, OSError):
        raise HTTPException(404, "Export not found") from None
