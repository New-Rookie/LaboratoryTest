"""Device discovery runner."""

from __future__ import annotations

from lab.models import ExperimentRun, ExperimentSpec


class DeviceDiscoveryRunner:
    name = "device_discovery"

    def run(self, spec: ExperimentSpec, run: ExperimentRun) -> dict[str, object]:
        capabilities = []
        if run.device_profile:
            capabilities = run.device_profile.get("capabilities", [])
        return {
            "device": {
                "capability_count": len([cap for cap in capabilities if cap.get("available")]),
                "capabilities": capabilities,
            }
        }
