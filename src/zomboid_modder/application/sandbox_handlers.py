from __future__ import annotations

from zomboid_modder.application.state import SessionState
from zomboid_modder.core.bus import MessageBus
from zomboid_modder.core.commands import LoadSandbox, LoadSpawnRegions, SetSandboxVar
from zomboid_modder.core.events import (
    ErrorOccurred,
    PendingChangesUpdated,
    SandboxEntry,
    SandboxLoaded,
    SandboxVarChanged,
    SpawnRegionsLoaded,
)
from zomboid_modder.domain.sandbox import SandboxVars
from zomboid_modder.infrastructure.sources.base import ConfigSource


class LoadSandboxHandler:
    def __init__(self, bus: MessageBus, state: SessionState, source: ConfigSource) -> None:
        self._bus = bus
        self._state = state
        self._source = source

    async def __call__(self, cmd: LoadSandbox) -> None:
        try:
            if not await self._source.exists(self._state.sandbox_relpath()):
                await self._bus.publish(SandboxLoaded([]))
                return
            text = await self._source.read_text(self._state.sandbox_relpath())
            sandbox = SandboxVars.parse(text)
            self._state.sandbox = sandbox
            entries = [
                SandboxEntry(
                    dotted_key=k,
                    value=sandbox.get(k),
                    value_type=type(sandbox.get(k)).__name__,
                )
                for k in sandbox.flat_keys()
            ]
            await self._bus.publish(SandboxLoaded(entries))
        except Exception as e:
            await self._bus.publish(ErrorOccurred("LoadSandbox", str(e)))


class SetSandboxVarHandler:
    def __init__(self, bus: MessageBus, state: SessionState) -> None:
        self._bus = bus
        self._state = state

    async def __call__(self, cmd: SetSandboxVar) -> None:
        try:
            if self._state.sandbox is None:
                raise RuntimeError("sandbox not loaded")
            current = self._state.sandbox.get(cmd.dotted_key)
            coerced = _coerce(cmd.value, current)
            self._state.sandbox.set(cmd.dotted_key, coerced)
            self._state.dirty = True
            await self._bus.publish(SandboxVarChanged(cmd.dotted_key, coerced))
            await self._bus.publish(PendingChangesUpdated(True))
        except Exception as e:
            await self._bus.publish(ErrorOccurred("SetSandboxVar", str(e)))


class LoadSpawnRegionsHandler:
    def __init__(self, bus: MessageBus, state: SessionState, source: ConfigSource) -> None:
        self._bus = bus
        self._state = state
        self._source = source

    async def __call__(self, cmd: LoadSpawnRegions) -> None:
        try:
            if not await self._source.exists(self._state.spawn_relpath()):
                await self._bus.publish(SpawnRegionsLoaded(""))
                return
            text = await self._source.read_text(self._state.spawn_relpath())
            self._state.spawn_text = text
            await self._bus.publish(SpawnRegionsLoaded(text))
        except Exception as e:
            await self._bus.publish(ErrorOccurred("LoadSpawnRegions", str(e)))


def _coerce(raw, current):
    if isinstance(current, bool):
        if isinstance(raw, bool):
            return raw
        s = str(raw).strip().lower()
        return s in ("true", "1", "yes", "on")
    if isinstance(current, int) and not isinstance(current, bool):
        return int(raw)
    if isinstance(current, float):
        return float(raw)
    return str(raw)
