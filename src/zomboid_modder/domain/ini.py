from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class _Line:
    raw: str
    key: str | None = None
    value: str | None = None

    @property
    def is_setting(self) -> bool:
        return self.key is not None


@dataclass
class PzIni:
    """Parser for Project Zomboid server .ini format.

    PZ .ini has no section headers, only Key=Value lines interleaved with
    comments (# ...) and blank lines. Round-trip preserves order, comments,
    blank lines, and unknown lines.
    """

    _lines: list[_Line] = field(default_factory=list)
    _index: dict[str, int] = field(default_factory=dict)

    @classmethod
    def parse(cls, text: str) -> PzIni:
        ini = cls()
        for raw in text.splitlines():
            stripped = raw.strip()
            if not stripped or stripped.startswith("#"):
                ini._lines.append(_Line(raw=raw))
                continue
            if "=" not in stripped:
                ini._lines.append(_Line(raw=raw))
                continue
            key, _, value = stripped.partition("=")
            key = key.strip()
            value = value.rstrip()
            ini._index[key] = len(ini._lines)
            ini._lines.append(_Line(raw=raw, key=key, value=value))
        return ini

    def get(self, key: str) -> str | None:
        idx = self._index.get(key)
        if idx is None:
            return None
        return self._lines[idx].value

    def set(self, key: str, value: str) -> None:
        idx = self._index.get(key)
        if idx is None:
            self._index[key] = len(self._lines)
            self._lines.append(_Line(raw=f"{key}={value}", key=key, value=value))
            return
        line = self._lines[idx]
        line.value = value
        line.raw = f"{key}={value}"

    def keys(self) -> list[str]:
        return [line.key for line in self._lines if line.is_setting]

    def items(self) -> list[tuple[str, str]]:
        return [(line.key, line.value) for line in self._lines if line.is_setting]

    def has(self, key: str) -> bool:
        return key in self._index

    def serialize(self) -> str:
        return "\n".join(line.raw for line in self._lines) + ("\n" if self._lines else "")
