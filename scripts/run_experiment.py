"""CLI runner for a YAML experiment spec.

Usage:
    python scripts/run_experiment.py specs/device_discovery.yaml
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lab.bootstrap import build_engine  # noqa: E402
from lab.spec_loader import load_spec  # noqa: E402


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/run_experiment.py <spec.yaml>")
        return 2
    spec_path = Path(sys.argv[1])
    if not spec_path.exists():
        print(f"Spec not found: {spec_path}")
        return 2
    engine = build_engine()
    run = engine.run_experiment(load_spec(spec_path))
    print(json.dumps(run.to_dict(), ensure_ascii=False, indent=2))
    return 0 if run.status in {"success", "blocked", "invalid"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
