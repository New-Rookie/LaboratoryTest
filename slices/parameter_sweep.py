"""Parameter sweep runner.

Runs a delegate runner across a Cartesian product of parameter values and returns
a compact comparison table. This is the platform's first real '调参-看指标'
workflow.
"""

from __future__ import annotations

from itertools import product
from typing import Any

from lab.models import ExperimentRun, ExperimentSpec
from lab.registry import Registry


class ParameterSweepRunner:
    name = "parameter_sweep"

    def __init__(self, registry: Registry) -> None:
        self.registry = registry

    def run(self, spec: ExperimentSpec, run: ExperimentRun) -> dict[str, Any]:
        params = spec.params
        delegate_runner = str(params.get("delegate_runner", "ollama"))
        base_params = dict(params.get("base_params", {}))
        grid = dict(params.get("grid", {}))
        max_trials = int(params.get("max_trials", 32))
        delegate = self.registry.require_runner(delegate_runner)

        keys = list(grid.keys())
        values = [list(grid[key]) for key in keys]
        trials = []
        for index, combo in enumerate(product(*values), start=1):
            if index > max_trials:
                break
            trial_params = dict(base_params)
            trial_params.update(dict(zip(keys, combo)))
            child_spec = ExperimentSpec(
                name=f"{spec.name}-trial-{index}",
                kind="llm_benchmark",
                runner=delegate_runner,
                params=trial_params,
                thresholds=dict(spec.thresholds),
            )
            metrics = delegate.run(child_spec, run)
            llm = metrics.get("llm", {}) if isinstance(metrics, dict) else {}
            trials.append({
                "trial": index,
                "params": trial_params,
                "success_rate": llm.get("success_rate"),
                "avg_latency_seconds": llm.get("avg_latency_seconds"),
                "max_latency_seconds": llm.get("max_latency_seconds"),
                "metrics": metrics,
            })
        recommended = _select_recommended(trials)
        return {"parameter_sweep": {"delegate_runner": delegate_runner, "trial_count": len(trials), "trials": trials, "recommended": recommended}}


def _select_recommended(trials: list[dict[str, Any]]) -> dict[str, Any] | None:
    valid = [item for item in trials if float(item.get("success_rate") or 0) >= 0.95]
    if not valid:
        return None
    return sorted(valid, key=lambda item: item.get("avg_latency_seconds") if item.get("avg_latency_seconds") is not None else 10**9)[0]
