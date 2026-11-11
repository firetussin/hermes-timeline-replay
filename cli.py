"""Offline entrypoint: python cli.py demo --timezone UTC (no Hermes needed)."""
import importlib.util
import sys
from pathlib import Path

if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    spec = importlib.util.spec_from_file_location("timeline_replay_local", root / "__init__.py", submodule_search_locations=[str(root)])
    package = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = package
    spec.loader.exec_module(package)
    from timeline_replay_local.service import parser, cli_handler
    cli_handler(parser().parse_args())
