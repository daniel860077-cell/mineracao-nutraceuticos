from __future__ import annotations

import re
from typing import Optional


def parse_int(value) -> Optional[int]:
    """Extrai inteiro de strings como '+1.000 vendidos', '2,3 mil', 'R$ 50'."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    s = str(value).lower().strip()

    mult = 1
    if "mil" in s or s.endswith("k"):
        mult = 1000
    if "mi" in s.replace("mil", "") or s.endswith("m"):
        mult = 1_000_000

    s = s.replace(".", "").replace(",", ".")
    m = re.search(r"\d+(?:\.\d+)?", s)
    if not m:
        return None
    return int(float(m.group()) * mult)
