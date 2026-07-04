"""Core typed models.

The core models are deliberately small. Every experiment enters the system as an
ExperimentSpec and leaves as an ExperimentRun. Integrations may change, but these
models should remain stable.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

RunStatus = Literal["pending", "running", "success", "failed", "invalid", "blocked"]
VerdictStatus = Literal["pass", "warning", "fail", "invalid"]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_id(prefix: str) -> str:
    return f"{prefix}-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid4().hex[:8]}"


@dataclass(slots=True)
class Capability:
    name: str
    available: bool
    details: dict[str, Any] = field(default_factory=dict)
    source: str = "unknown"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class DeviceProfile:
    device_id: str
    hostname: str
    capabilities: list[Capability] = field(default_factory=list)
    facts: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now_iso)

    def capability_names(self) -> set[str]:
        return {cap.name for cap in self.capabilities if cap.available}

    def missing(self, required: list[str]) -> list[str]:
        available = self.capability_names()
        return [name for name in required if name not in available]

    def to_dict(self) -> dict[str, Any]:
        return {
            "device_id": self.device_id,
            "hostname": self.hostname,
            "capabilities": [cap.to_dict() for cap in self.capabilities],
            "facts": self.facts,
            "created_at": self.created_at,
        }


@dataclass(slots=True)
class ExperimentSpec:
    name: str
    kind: str
    runner: str
    collectors: list[str] = field(default_factory=list)
    requires: list[str] = field(default_factory=list)
    evaluator: str | None = None
    params: dict[str, Any] = field(default_factory=dict)
    thresholds: dict[str, Any] = field(default_factory=dict)
    description: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExperimentSpec":
        return cls(
            name=str(data["name"]),
            kind=str(data["kind"]),
            runner=str(data["runner"]),
            collectors=list(data.get("collectors", [])),
            requires=list(data.get("requires", [])),
            evaluator=data.get("evaluator"),
            params=dict(data.get("params", {})),
            thresholds=dict(data.get("thresholds", {})),
            description=str(data.get("description", "")),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Verdict:
    status: VerdictStatus
    summary: str
    reasons: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    reliability_score: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ExperimentRun:
    run_id: str
    spec: ExperimentSpec
    status: RunStatus
    started_at: str
    ended_at: str | None = None
    metrics: dict[str, Any] = field(default_factory=dict)
    artifacts: dict[str, str] = field(default_factory=dict)
    logs: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    device_profile: dict[str, Any] | None = None
    verdict: Verdict | None = None

    @classmethod
    def start(cls, spec: ExperimentSpec) -> "ExperimentRun":
        return cls(run_id=new_id("run"), spec=spec, status="running", started_at=utc_now_iso())

    def finish(self, status: RunStatus) -> None:
        self.status = status
        self.ended_at = utc_now_iso()

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "spec": self.spec.to_dict(),
            "status": self.status,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "metrics": self.metrics,
            "artifacts": self.artifacts,
            "logs": self.logs,
            "errors": self.errors,
            "device_profile": self.device_profile,
            "verdict": self.verdict.to_dict() if self.verdict else None,
        }
