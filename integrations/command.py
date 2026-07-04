"""Safe command execution helpers used by integrations only."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass


@dataclass(slots=True)
class CommandResult:
    command: list[str]
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


def run_command(command: list[str], timeout: int = 30) -> CommandResult:
    try:
        proc = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
        return CommandResult(command=command, returncode=proc.returncode, stdout=proc.stdout, stderr=proc.stderr)
    except FileNotFoundError as exc:
        return CommandResult(command=command, returncode=127, stdout="", stderr=str(exc))
    except subprocess.TimeoutExpired as exc:
        return CommandResult(command=command, returncode=124, stdout=exc.stdout or "", stderr=exc.stderr or "timeout")
