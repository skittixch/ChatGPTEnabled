from __future__ import annotations

import re
import uuid
from typing import Iterable, List


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value)
    return value.strip("-") or str(uuid.uuid4())


def generate_node_id(prefix: str, *parts: Iterable[str]) -> str:
    extra: List[str] = []
    for part in parts:
        if isinstance(part, str) and part:
            extra.append(slugify(part))
        elif isinstance(part, Iterable):
            extra.extend(slugify(p) for p in part if p)
    suffix = "-".join(filter(None, extra))
    base = f"{prefix}-{slugify(str(uuid.uuid4())[:8])}"
    return f"{base}-{suffix}" if suffix else base
