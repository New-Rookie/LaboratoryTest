"""Thin experiment engine."""

from __future__ import annotations

import traceback

from lab.models import DeviceProfile, ExperimentRun, ExperimentSpec, Verdict
from lab.registry import Registry
from lab.report import write_markdown_report
from lab.store import SQLiteEvidenceStore


class ExperimentEngine:
    def __init__(self, registry: Registry, store: SQLiteEvidenceStore | None = None) -> None:
        self.registry = registry
        self.store = store or SQLiteEvidenceStore()

    def discover_device(self, device_id: str = "local") -> DeviceProfile:
        capabilities = []
        facts: dict[str, object] = {}
        hostname = "unknown"
        for provider in self.registry.capability_providers.values():
            try:
                detected = provider.detect()
                capabilities.extend(detected)
                if hasattr(provider, "facts"):
                    provider_facts = provider.facts()
                    facts[provider.name] = provider_facts
                    hostname = str(provider_facts.get("hostname", hostname))
            except Exception as exc:
                capabilities.append(
                    provider.failed_capability(str(exc))
                    if hasattr(provider, "failed_capability")
                    else _failed_capability(provider.name, str(exc))
                )
        return DeviceProfile(device_id=device_id, hostname=hostname, capabilities=capabilities, facts=facts)

    def run_experiment(self, spec: ExperimentSpec) -> ExperimentRun:
        run = ExperimentRun.start(spec)
        profile = self.discover_device()
        run.device_profile = profile.to_dict()

        missing = profile.missing(spec.requires)
        if missing:
            run.errors.append(f"Missing required capabilities: {', '.join(missing)}")
            run.verdict = Verdict(
                status="invalid",
                summary="实验前置检查未通过。",
                reasons=[f"缺失能力：{name}" for name in missing],
                suggestions=["先在设备能力页检查软件、硬件和服务是否可用。"],
                reliability_score=20,
            )
            run.finish("blocked")
            self._archive(run)
            return run

        collectors = []
        try:
            collectors = [self.registry.require_collector(name) for name in spec.collectors]
            runner = self.registry.require_runner(spec.runner)
            evaluator_name = spec.evaluator or spec.kind
            evaluator = self.registry.require_evaluator(evaluator_name)
        except Exception as exc:
            run.errors.append(str(exc))
            run.verdict = Verdict(status="invalid", summary="实验组件未注册。", reasons=[str(exc)], reliability_score=10)
            run.finish("invalid")
            self._archive(run)
            return run

        try:
            for collector in collectors:
                collector.start(run)

            workload_metrics = runner.run(spec, run)
            run.metrics.update(workload_metrics or {})

            for collector in collectors:
                run.metrics.update(collector.stop(run) or {})

            run.verdict = evaluator.evaluate(run, profile)
            run.finish("success" if run.verdict.status in {"pass", "warning"} else "failed")
        except Exception as exc:
            run.errors.append(str(exc))
            run.logs.append(traceback.format_exc())
            run.verdict = Verdict(
                status="fail",
                summary="实验执行失败。",
                reasons=[str(exc)],
                suggestions=["查看日志并确认外部服务或命令是否可用。"],
                reliability_score=10,
            )
            run.finish("failed")
        finally:
            self._archive(run)
        return run

    def _archive(self, run: ExperimentRun) -> None:
        report_path = write_markdown_report(run)
        run.artifacts["markdown_report"] = report_path
        self.store.save_run(run)


def _failed_capability(source: str, message: str):
    from lab.models import Capability

    return Capability(name=f"provider.{source}", available=False, source=source, details={"error": message})
