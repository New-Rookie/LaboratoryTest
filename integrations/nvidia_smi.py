"""NVIDIA GPU integration through nvidia-smi structured CSV output."""

from __future__ import annotations

import csv
from io import StringIO
from time import perf_counter

from integrations.command import run_command
from lab.models import Capability, ExperimentRun


class NvidiaSmiProvider:
    name = "nvidia_smi"

    def detect(self) -> list[Capability]:
        result = run_command(["nvidia-smi", "--query-gpu=index,name,memory.total,driver_version", "--format=csv,noheader,nounits"], timeout=10)
        if not result.ok:
            return [Capability("gpu.nvidia", False, {"error": result.stderr}, self.name)]
        rows = _parse_csv(result.stdout)
        return [
            Capability("gpu.nvidia", bool(rows), {"count": len(rows), "gpus": rows}, self.name),
            Capability("gpu.multi_card", len(rows) > 1, {"count": len(rows)}, self.name),
        ]

    def failed_capability(self, message: str) -> Capability:
        return Capability("gpu.nvidia", False, {"error": message}, self.name)


class NvidiaSmiCollector:
    name = "nvidia_smi"

    def __init__(self) -> None:
        self._start_snapshot: list[dict[str, str]] = []
        self._start_time = 0.0

    def start(self, run: ExperimentRun) -> None:
        self._start_time = perf_counter()
        self._start_snapshot = self._query()

    def stop(self, run: ExperimentRun) -> dict[str, object]:
        end_snapshot = self._query()
        return {
            "gpu": {
                "sample_seconds": round(perf_counter() - self._start_time, 3),
                "start": self._start_snapshot,
                "end": end_snapshot,
                "summary": _summarize(end_snapshot),
            }
        }

    def _query(self) -> list[dict[str, str]]:
        cmd = [
            "nvidia-smi",
            "--query-gpu=index,name,utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw",
            "--format=csv,noheader,nounits",
        ]
        result = run_command(cmd, timeout=10)
        if not result.ok:
            return [{"error": result.stderr.strip() or "nvidia-smi failed"}]
        return _parse_csv(result.stdout, ["index", "name", "gpu_util", "mem_used", "mem_total", "temp", "power"])


def _parse_csv(text: str, headers: list[str] | None = None) -> list[dict[str, str]]:
    reader = csv.reader(StringIO(text.strip()))
    rows = []
    for row in reader:
        values = [cell.strip() for cell in row]
        if not values or values == [""]:
            continue
        if headers:
            rows.append(dict(zip(headers, values)))
        else:
            rows.append({str(i): value for i, value in enumerate(values)})
    return rows


def _summarize(rows: list[dict[str, str]]) -> dict[str, object]:
    if not rows or "error" in rows[0]:
        return {"available": False, "reason": rows[0].get("error", "no gpu rows") if rows else "no gpu rows"}
    temps = [_to_float(row.get("temp")) for row in rows]
    mem_used = [_to_float(row.get("mem_used")) for row in rows]
    return {
        "available": True,
        "gpu_count": len(rows),
        "max_temp": max(temps) if temps else None,
        "max_mem_used_mb": max(mem_used) if mem_used else None,
    }


def _to_float(value: str | None) -> float:
    try:
        return float(value or 0)
    except ValueError:
        return 0.0
