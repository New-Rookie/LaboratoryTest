"""Application bootstrap.

This is the only place that wires concrete integrations into the stable engine.
"""

from __future__ import annotations

from integrations.fio import FioProvider, FioRunner
from integrations.nvidia_smi import NvidiaSmiCollector, NvidiaSmiProvider
from integrations.ollama import OllamaProvider, OllamaRunner
from integrations.prometheus import PrometheusCollector, PrometheusProvider
from integrations.system import SystemProvider
from integrations.tensorrt import TensorRTProvider, TensorRTSmokeRunner
from integrations.vllm import VLLMProvider, VLLMRunner
from lab.engine import ExperimentEngine
from lab.registry import Registry
from lab.store import SQLiteEvidenceStore
from slices.aging import AgingRunner
from slices.device_discovery import DeviceDiscoveryRunner
from slices.evaluators import DeviceDiscoveryEvaluator, GenericSmokeEvaluator, LLMBenchmarkEvaluator, StorageEvaluator


def build_registry() -> Registry:
    registry = Registry()

    for provider in [
        SystemProvider(),
        NvidiaSmiProvider(),
        OllamaProvider(),
        VLLMProvider(),
        PrometheusProvider(),
        FioProvider(),
        TensorRTProvider(),
    ]:
        registry.add_provider(provider)

    for collector in [NvidiaSmiCollector(), PrometheusCollector()]:
        registry.add_collector(collector)

    for runner in [
        DeviceDiscoveryRunner(),
        OllamaRunner(),
        VLLMRunner(),
        FioRunner(),
        TensorRTSmokeRunner(),
    ]:
        registry.add_runner(runner)

    registry.add_runner(AgingRunner(registry))

    for evaluator in [
        DeviceDiscoveryEvaluator(),
        LLMBenchmarkEvaluator(),
        StorageEvaluator(),
        GenericSmokeEvaluator(),
    ]:
        registry.add_evaluator(evaluator)

    return registry


def build_engine() -> ExperimentEngine:
    return ExperimentEngine(build_registry(), SQLiteEvidenceStore())
