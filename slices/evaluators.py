"""Default evaluators for vertical slices."""

from __future__ import annotations

from lab.models import DeviceProfile, ExperimentRun, Verdict


class DeviceDiscoveryEvaluator:
    name = "device_discovery"

    def evaluate(self, run: ExperimentRun, profile: DeviceProfile) -> Verdict:
        available = sorted(profile.capability_names())
        score = 60 + min(len(available) * 3, 40)
        return Verdict(
            status="pass" if available else "warning",
            summary=f"识别到 {len(available)} 项可用能力。",
            reasons=[f"可用能力：{', '.join(available) if available else '无'}"],
            suggestions=["缺失能力不会阻止平台运行，但会影响可执行实验模板。"],
            reliability_score=min(score, 100),
        )


class LLMBenchmarkEvaluator:
    name = "llm_benchmark"

    def evaluate(self, run: ExperimentRun, profile: DeviceProfile) -> Verdict:
        llm = run.metrics.get("llm", {})
        success_rate = float(llm.get("success_rate") or 0)
        avg_latency = llm.get("avg_latency_seconds")
        thresholds = run.spec.thresholds
        min_success = float(thresholds.get("success_rate_min", 0.95))
        max_latency = thresholds.get("avg_latency_max_seconds")

        reasons = [f"成功率：{success_rate:.2%}"]
        if avg_latency is not None:
            reasons.append(f"平均延迟：{avg_latency}s")

        if success_rate < min_success:
            return Verdict(
                status="fail",
                summary="模型服务请求成功率低于阈值。",
                reasons=reasons,
                suggestions=["检查模型服务状态、显存占用、并发设置和请求超时。"],
                reliability_score=70,
            )
        if max_latency is not None and avg_latency is not None and avg_latency > float(max_latency):
            return Verdict(
                status="warning",
                summary="模型服务可用，但平均延迟偏高。",
                reasons=reasons,
                suggestions=["降低并发、减少 max_tokens、缩短上下文或切换更合适的推理后端。"],
                reliability_score=80,
            )
        return Verdict(
            status="pass",
            summary="模型服务测试通过。",
            reasons=reasons,
            suggestions=["可继续运行参数组合实验或更长时间稳定性测试。"],
            reliability_score=85,
        )


class StorageEvaluator:
    name = "storage_benchmark"

    def evaluate(self, run: ExperimentRun, profile: DeviceProfile) -> Verdict:
        storage = run.metrics.get("storage", {})
        if not storage.get("ok"):
            return Verdict(
                status="fail",
                summary="存储测试未通过。",
                reasons=[storage.get("stderr", "fio 执行失败")],
                suggestions=["检查 fio 是否安装、目标目录权限和磁盘剩余空间。"],
                reliability_score=60,
            )
        return Verdict(
            status="pass",
            summary="存储 smoke 测试通过。",
            reasons=[f"摘要指标：{storage.get('summary', {})}"],
            suggestions=["后续可增加更长 runtime、更大文件和多 numjobs 测试。"],
            reliability_score=80,
        )


class GenericSmokeEvaluator:
    name = "generic_smoke"

    def evaluate(self, run: ExperimentRun, profile: DeviceProfile) -> Verdict:
        if run.errors:
            return Verdict(status="fail", summary="Smoke 测试失败。", reasons=run.errors, reliability_score=50)
        return Verdict(status="pass", summary="Smoke 测试完成。", reasons=["未发现执行错误。"], reliability_score=75)
