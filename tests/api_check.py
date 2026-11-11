"""In-process route smoke test; use the Hermes Python environment for FastAPI."""
import importlib.util
import os
import sys
import tempfile
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

root = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as tmp:
    os.environ["HERMES_HOME"] = tmp
    spec = importlib.util.spec_from_file_location("timeline_routes_test", root / "dashboard" / "plugin_api.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    app = FastAPI()
    app.include_router(module.router, prefix="/api/plugins/timeline-replay")
    client = TestClient(app)
    base = "/api/plugins/timeline-replay"
    assert client.get(base+"/status").json()["profiles"] == ["current"]
    assert client.get(base+'/demo-preview').json()['demo'] is True
    assert not (Path(tmp)/'plugin-data').exists(), 'Opening the sample must not write a render bundle'
    setup=client.post(base+'/action',json={'action':'setup'}).json()
    assert 'prompt' in setup and 'only missing' in setup['prompt']
    deps=client.post(base+'/action',json={'action':'dependencies'}).json()['dependencies']
    assert len(deps['items'])==5
    result = client.post(base+"/action", json={"action":"demo","timezone":"UTC"})
    assert result.status_code == 200, result.text
    bundle = result.json()["bundle"]
    html = client.get(base+"/preview/"+bundle).json()["html"]
    assert "SYNTHETIC" in html
    assert client.get(base+"/download/"+bundle+"/html").status_code == 200
    assert client.get(base+"/download/"+bundle+"/video").status_code == 404
    assert client.get(base+"/download/"+bundle+"/secrets").status_code == 404
    assert client.post(base+"/action",json={"action":"enroll","path":"/arbitrary"}).status_code == 400
    assert client.post(base+"/action",json={"action":"build","profiles":["unapproved"]}).status_code == 400
    assert client.get(base+"/preview/not-a-bundle").status_code == 404
    print("API routes: status, demo, preview, exports, unapproved-source and enrollment boundaries passed.")
