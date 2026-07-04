"""Contract definitions.

These protocols are the boundary between the stable experiment core and the
changing outside world: hardware, model services, shell tools, monitoring
systems, and UI frameworks.
"""

from __future__ import annotations

from typing import Any, Protocol

from lab.models import Capability, DeviceProfile, ExperimentRun, ExperimentSpec, Verdict


class CapabilityProvider(Protocol):
    name: str

    def detect(self) -> list[Capability]:
        """Return available or unavailable capabilities discovered by this provider."""


class WorkloadRunner(Protocol):
    name: str

    def run(self, spec: ExperimentSpec, run: ExperimentRun) -> dict[str, Any]:
        """Execute the workload and return workload metrics/artifacts."""


class MetricCollector(Protocol):
    name: str

    def start(self, run: ExperimentRun) -> None:
        """Start metric collection before the workload runs."""

    def stop(self, run: ExperimentRun) -> dict[str, Any]:
        """Stop metric collection and return metrics."""


class Evaluator(Protocol):
    name: str

    def evaluate(self, run: ExperimentRun, profile: DeviceProfile) -> Verdict:
        """Evaluate a run and return a standard verdict."""


class EvidenceStore(Protocol):
    def save_run(self, run: ExperimentRun) -> None:
        """Persist an experiment run."""

    def list_runs(self, limit: int = 100) -> list[dict[str, Any]]:
        """Return recent run summaries."""
