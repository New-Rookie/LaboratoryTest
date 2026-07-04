"""Explicit registry for providers, runners, collectors, and evaluators."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Registry:
    capability_providers: dict[str, Any] = field(default_factory=dict)
    runners: dict[str, Any] = field(default_factory=dict)
    collectors: dict[str, Any] = field(default_factory=dict)
    evaluators: dict[str, Any] = field(default_factory=dict)

    def add_provider(self, provider: Any) -> None:
        self.capability_providers[provider.name] = provider

    def add_runner(self, runner: Any) -> None:
        self.runners[runner.name] = runner

    def add_collector(self, collector: Any) -> None:
        self.collectors[collector.name] = collector

    def add_evaluator(self, evaluator: Any) -> None:
        self.evaluators[evaluator.name] = evaluator

    def require_runner(self, name: str) -> Any:
        if name not in self.runners:
            raise KeyError(f"Runner not registered: {name}")
        return self.runners[name]

    def require_collector(self, name: str) -> Any:
        if name not in self.collectors:
            raise KeyError(f"Collector not registered: {name}")
        return self.collectors[name]

    def require_evaluator(self, name: str) -> Any:
        if name not in self.evaluators:
            raise KeyError(f"Evaluator not registered: {name}")
        return self.evaluators[name]
