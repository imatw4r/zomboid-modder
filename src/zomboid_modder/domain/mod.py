from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Mod:
    id: str
    workshop_id: str
    name: str | None = None
