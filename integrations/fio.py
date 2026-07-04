"""fio storage benchmark integration."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from integrations.command import run_command
from lab.models import Capability, ExperimentRun, ExperimentSpec


class FioProvider:
    name = "fio"

    def detect(self) -> list[Capability]:
        result = run_command(["fio", "--version"], timeout=5)
        return [Capability("storage.fio", result.ok, {"version": result.stdout.strip(), "error": result.stderr.strip()}, self.name)]

    def failed_capability(self, message: str) -> Capability:
        return Capability("storage.fio", False, {"error": message}, self.name)


class FioRunner:
    name = "fio"

    def run(self, spec: ExperimentSpec, run: ExperimentRun) -> dict[str, Any]:
        params = spec.params
        target_dir = Path(str(params.get("target_dir", "artifacts/fio")))
        target_dir.mkdir(parents=True, exist_ok=True)
        size = str(params.get("size", "128M"))
        runtime = int(params.get("runtime", 10))
        rw = str(params.get("rw", "readwrite"))
        bs = str(params.get("bs", "4k"))
        iodepth = str(params.get("iodepth", 1))
        filename = target_dir / f"fio-{run.run_id}.dat"

        cmd = [
            "fio",
            "--name=lab-storage-smoke",
            f"--filename={filename}",
            f"--size={size}",
            f"--runtime={runtime}",
            "--time_based",
            f"--rw={rw}",
            f"--bs={bs}",
            f"--iodepth={iodepth}",
            "--direct=0",
            "--output-format=json",
        ]
        result = run_command(cmd, timeout=runtime + 30)
        artifact = Path("artifacts") / f"{run.run_id}-fio.json"
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text(result.stdout or result.stderr, encoding="utf-8")
        run.artifacts["fio_raw"] = str(artifact)

        parsed: dict[str, Any] = {}
        if result.ok:
            try:
                parsed = json.loads(result.stdout)
            except json.JSONDecodeError:
                parsed = {"parse_error": "fio returned non-json output"}
        return {
            "storage": {
                "backend": "fio",
                "ok": result.ok,
                "returncode": result.returncode,
                "params": {"size": size, "runtime": runtime, "rw": rw, "bs": bs, "iodepth": iodepth},
                "summary": _summarize(parsed),
                "stderr": result.stderr.strip(),
            }
        }


def _summarize(payload: dict[str, Any]) -> dict[str, Any]:
    jobs = payload.get("jobs", []) if isinstance(payload, dict) else []
    if not jobs:
        return {}
    job = jobs[0]
    read = job.get("read", {})
    write = job.get("write", {})
    return {
        "read_bw_kib": read.get("bw"),
        "write_bw_kib": write.get("bw"),
        "read_iops": read.get("iops"),
        "write_iops": write.get("iops"),
    }
