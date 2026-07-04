"""Experiment spec loading."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from lab.models import ExperimentSpec


def list_spec_files(spec_dir: str | Path = "specs") -> list[Path]:
    root = Path(spec_dir)
    if not root.exists():
        return []
    return sorted(root.glob("*.yaml"))


def load_spec(path: str | Path) -> ExperimentSpec:
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    return ExperimentSpec.from_dict(payload)


def load_spec_payload(path: str | Path) -> dict[str, Any]:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
