"""Stable contracts for CFSA.

Only contracts are imported by the core engine. Concrete software integrations
must live outside the core and satisfy these protocols.
"""

from .base import CapabilityProvider, WorkloadRunner, MetricCollector, Evaluator, EvidenceStore

__all__ = [
    "CapabilityProvider",
    "WorkloadRunner",
    "MetricCollector",
    "Evaluator",
    "EvidenceStore",
]
