"""Parse Prometheus text exposition format into a flat dict of metric_name → float."""
from __future__ import annotations
import re

_METRIC_RE = re.compile(r'^([a-zA-Z_:][a-zA-Z0-9_:]*)(?:\{[^}]*\})?\s+([\d.+\-eE]+)')


def parse_prometheus_text(text: str) -> dict[str, float]:
    """Return {metric_name: float} for every metric line.
    When the same metric name appears multiple times (different labels),
    the first occurrence is kept.
    """
    result: dict[str, float] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        m = _METRIC_RE.match(line)
        if not m:
            continue
        name = m.group(1)
        if name not in result:
            try:
                result[name] = float(m.group(2))
            except ValueError:
                pass
    return result
