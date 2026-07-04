"""Small HTTP JSON client for integrations."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class JsonResponse:
    ok: bool
    status_code: int
    elapsed_seconds: float
    data: Any = None
    error: str = ""


def get_json(url: str, timeout: int = 10) -> JsonResponse:
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            payload = response.read().decode("utf-8", errors="replace")
            return JsonResponse(True, response.status, time.perf_counter() - start, json.loads(payload or "{}"))
    except Exception as exc:
        status = exc.code if isinstance(exc, urllib.error.HTTPError) else 0
        return JsonResponse(False, status, time.perf_counter() - start, error=str(exc))


def post_json(url: str, payload: dict[str, Any], timeout: int = 120) -> JsonResponse:
    start = time.perf_counter()
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            return JsonResponse(True, response.status, time.perf_counter() - start, json.loads(body or "{}"))
    except Exception as exc:
        status = exc.code if isinstance(exc, urllib.error.HTTPError) else 0
        return JsonResponse(False, status, time.perf_counter() - start, error=str(exc))
