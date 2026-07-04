"""TensorRT smoke integration.

The first version is intentionally conservative: detect command availability and
record environment evidence. Actual engine building should be added as a slice
only after a target model format is confirmed.
"""

from __future__ import annotations

from integrations.command import run_command
from lab.models import Capability, ExperimentRun, ExperimentSpec


class TensorRTProvider:
    name = "tensorrt"

    def detect(self) -> list[Capability]:
        result = run_command(["trtexec", "--version"], timeout=5)
        return [Capability("model.tensorrt", result.ok, {"stdout": result.stdout.strip(), "stderr": result.stderr.strip()}, self.name)]

    def failed_capability(self, message: str) -> Capability:
        return Capability("model.tensorrt", False, {"error": message}, self.name)


class TensorRTSmokeRunner:
    name = "tensorrt_smoke"

    def run(self, spec: ExperimentSpec, run: ExperimentRun) -> dict[str, object]:
        result = run_command(["trtexec", "--version"], timeout=5)
        return {
            "tensorrt": {
                "ok": result.ok,
                "returncode": result.returncode,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
            }
        }
