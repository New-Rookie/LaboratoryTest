"""vLLM OpenAI-compatible integration."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from statistics import mean
from typing import Any

from integrations.http_json import get_json, post_json
from lab.models import Capability, ExperimentRun, ExperimentSpec


class VLLMProvider:
    name = "vllm"

    def __init__(self, base_url: str = "http://localhost:8000/v1") -> None:
        self.base_url = base_url.rstrip("/")

    def detect(self) -> list[Capability]:
        resp = get_json(f"{self.base_url}/models", timeout=5)
        models = resp.data.get("data", []) if resp.ok and isinstance(resp.data, dict) else []
        return [Capability("llm.vllm", resp.ok, {"base_url": self.base_url, "models": models, "status_code": resp.status_code}, self.name)]

    def failed_capability(self, message: str) -> Capability:
        return Capability("llm.vllm", False, {"error": message}, self.name)


class VLLMRunner:
    name = "vllm"

    def run(self, spec: ExperimentSpec, run: ExperimentRun) -> dict[str, Any]:
        params = spec.params
        base_url = str(params.get("base_url", "http://localhost:8000/v1")).rstrip("/")
        model = str(params.get("model", "default"))
        prompt = str(params.get("prompt", "请用一句话说明当前模型服务是否可用。"))
        concurrency = int(params.get("concurrency", 1))
        total_requests = int(params.get("total_requests", concurrency))
        max_tokens = int(params.get("max_tokens", 256))
        temperature = float(params.get("temperature", 0.3))

        def one_request(index: int) -> dict[str, Any]:
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            resp = post_json(f"{base_url}/chat/completions", payload, timeout=int(params.get("timeout", 180)))
            content = ""
            if resp.ok and isinstance(resp.data, dict):
                choices = resp.data.get("choices", [])
                if choices:
                    content = choices[0].get("message", {}).get("content", "")
            return {
                "index": index,
                "ok": resp.ok,
                "status_code": resp.status_code,
                "latency_seconds": round(resp.elapsed_seconds, 4),
                "response_chars": len(content),
                "error": resp.error,
            }

        results = []
        with ThreadPoolExecutor(max_workers=max(1, concurrency)) as pool:
            futures = [pool.submit(one_request, i) for i in range(total_requests)]
            for future in as_completed(futures):
                results.append(future.result())

        latencies = [item["latency_seconds"] for item in results if item["ok"]]
        success_count = sum(1 for item in results if item["ok"])
        return {
            "llm": {
                "backend": "vllm",
                "model": model,
                "concurrency": concurrency,
                "total_requests": total_requests,
                "success_count": success_count,
                "success_rate": round(success_count / max(total_requests, 1), 4),
                "avg_latency_seconds": round(mean(latencies), 4) if latencies else None,
                "max_latency_seconds": max(latencies) if latencies else None,
                "requests": results,
            }
        }
