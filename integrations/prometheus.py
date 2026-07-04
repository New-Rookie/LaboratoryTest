"""Prometheus integration."""

from __future__ import annotations

from urllib.parse import urlencode

from integrations.http_json import get_json
from lab.models import Capability, ExperimentRun


class PrometheusProvider:
    name = "prometheus"

    def __init__(self, base_url: str = "http://localhost:9090") -> None:
        self.base_url = base_url.rstrip("/")

    def detect(self) -> list[Capability]:
        url = f"{self.base_url}/api/v1/query?{urlencode({'query': 'up'})}"
        resp = get_json(url, timeout=5)
        return [Capability("monitor.prometheus", resp.ok, {"base_url": self.base_url, "status_code": resp.status_code}, self.name)]

    def failed_capability(self, message: str) -> Capability:
        return Capability("monitor.prometheus", False, {"error": message}, self.name)


class PrometheusCollector:
    name = "prometheus"

    def __init__(self, base_url: str = "http://localhost:9090") -> None:
        self.base_url = base_url.rstrip("/")

    def start(self, run: ExperimentRun) -> None:
        return None

    def stop(self, run: ExperimentRun) -> dict[str, object]:
        queries = run.spec.params.get("prometheus_queries", {})
        metrics = {}
        for key, query in queries.items():
            url = f"{self.base_url}/api/v1/query?{urlencode({'query': str(query)})}"
            resp = get_json(url, timeout=10)
            metrics[key] = {"ok": resp.ok, "data": resp.data if resp.ok else None, "error": resp.error}
        return {"prometheus": metrics} if metrics else {}
