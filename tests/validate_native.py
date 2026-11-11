"""Optional native validator, using an explicitly selected local Hermes checkout."""
import json
import sys
from pathlib import Path

if len(sys.argv) != 2:
    raise SystemExit("Pass a local Hermes source checkout; run in its Python environment with an isolated HERMES_HOME")
sys.path.insert(0, str(Path(sys.argv[1]).resolve()))
from hermes_cli.plugin_validate import validate_plugin_dir

report = validate_plugin_dir(Path(__file__).resolve().parents[1])
out = Path(__file__).resolve().parents[1] / "test-output"
out.mkdir(exist_ok=True)
(out / "hermes-validation.json").write_text(json.dumps(report.__dict__, indent=2, default=str), encoding="utf-8")
bad = [name for name, okay, detail in report.checks if not okay]
print(f"Hermes admission checks: {len(report.checks)-len(bad)}/{len(report.checks)} passed; warnings: {len(report.warnings)}")
if bad:
    raise SystemExit("Failed checks: "+", ".join(bad))
