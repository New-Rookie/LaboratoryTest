"""Short aging runner.

This first implementation performs a conservative repeated workload loop by
reusing an existing runner name. It is safe by default and intended for smoke
stability validation, not full production burn-in.
"""

from __future__ import annotations

import time
from typing import Any

from lab.models import ExperimentRun, ExperimentSpec
from lab.registry import Registry


class AgingRunner:
    name = "aging_short"

    def __init__(self, registry: Registry) -> None:
        self.registry = registry

    def run(self, spec: ExperimentSpec, run: ExperimentRun) -> dict[str, Any]:
        params = spec.params
        delegate_runner = str(params.get("delegate_runner", "ollama"))
        iterations = int(params.get("iterations", 3))
        sleep_seconds = float(params.get("sleep_seconds", 1))
        delegate = self.registry.require_runner(delegate_runner)
        child_spec = ExperimentSpec(
            name=f"{spec.name}-delegate",
            kind="llm_benchmark",
            runner=delegate_runner,
            params=dict(params.get("delegate_params", {})),
            thresholds=dict(spec.thresholds),
        )
        results = []
        success = 0
        for index in range(iterations):
            metrics = delegate.run(child_spec, run)
            llm = metrics.get("llm", {}) if isinstance(metrics, dict) else {}
            ok = float(llm.get("success_rate") or 0) >= 1.0
            success += 1 if ok else 0
            results.append({"iteration": index + 1, "ok": ok, "metrics": metrics})
            if sleep_seconds > 0:
                time.sleep(sleep_seconds)
        return {
            "aging": {
                "delegate_runner": delegate_runner,
                "iterations": iterations,
                "success_iterations": success,
                "success_rate": round(success / max(iterations, 1), 4),
                "results": results,
            }
        }
