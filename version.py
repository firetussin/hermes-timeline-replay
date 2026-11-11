"""Single source for the loaded plugin version and request-compatibility level."""
import re
from pathlib import Path

VERSION = "0.2.18"
# Bump API only for breaking request/response changes between Desktop and backend.
API = 1


def installed_version():
    """Version of the code on disk now (plugin.yaml), which may be newer than the loaded module."""
    try:
        text = (Path(__file__).resolve().parent / "plugin.yaml").read_text(encoding="utf-8")
        m = re.search(r'^version:\s*["\']?([\w.\-]+)', text, re.M)
        return m.group(1) if m else None
    except OSError:
        return None


def check_client(args):
    """Reject requests from an incompatible (stale) page with a clear reload message.
    Pages from before client_api existed (0.2.0-0.2.2) used API 1 and are accepted."""
    client = args.get("client_api", API)
    if client != API:
        raise ValueError(f"This Timeline Replay page is out of date (page API {client}, host API {API}). Reload the page.")
