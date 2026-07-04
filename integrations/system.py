"""System capability provider."""

from __future__ import annotations

import os
import platform
import shutil
import socket

from lab.models import Capability


class SystemProvider:
    name = "system"

    def detect(self) -> list[Capability]:
        caps = [
            Capability("system.local", True, self.facts(), self.name),
            Capability("python.available", True, {"version": platform.python_version()}, self.name),
        ]
        for tool in ["docker", "fio", "ollama", "vllm", "nvidia-smi"]:
            caps.append(Capability(f"tool.{tool}", shutil.which(tool) is not None, {"path": shutil.which(tool)}, self.name))
        return caps

    def facts(self) -> dict[str, object]:
        return {
            "hostname": socket.gethostname(),
            "os": platform.platform(),
            "system": platform.system(),
            "machine": platform.machine(),
            "python": platform.python_version(),
            "cwd": os.getcwd(),
        }

    def failed_capability(self, message: str) -> Capability:
        return Capability("system.local", False, {"error": message}, self.name)
