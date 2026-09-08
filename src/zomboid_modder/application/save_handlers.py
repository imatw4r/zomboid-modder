from __future__ import annotations

from zomboid_modder.application.state import SessionState
from zomboid_modder.core.bus import MessageBus
from zomboid_modder.core.commands import DiscardChanges, SaveChanges
from zomboid_modder.core.events import (
    PendingChangesUpdated,
    SaveCompleted,
    SaveFailed,
    SaveStarted,
)
from zomboid_modder.infrastructure.sources.base import ConfigSource


class SaveChangesHandler:
    def __init__(self, bus: MessageBus, state: SessionState, source: ConfigSource) -> None:
        self._bus = bus
        self._state = state
        self._source = source

    async def __call__(self, cmd: SaveChanges) -> None:
        await self._bus.publish(SaveStarted())
        written: list[str] = []
        try:
            if self._state.ini is not None:
                path = self._state.ini_relpath()
                await self._backup(path)
                await self._source.write_text(path, self._state.ini.serialize())
                written.append(path)
            if self._state.sandbox is not None:
                path = self._state.sandbox_relpath()
                await self._backup(path)
                await self._source.write_text(path, self._state.sandbox.serialize())
                written.append(path)
            self._state.dirty = False
            await self._bus.publish(SaveCompleted(written))
            await self._bus.publish(PendingChangesUpdated(False))
        except Exception as e:
            await self._bus.publish(SaveFailed(str(e)))

    async def _backup(self, relpath: str) -> None:
        if not await self._source.exists(relpath):
            return
        content = await self._source.read_text(relpath)
        await self._source.write_text(f"{relpath}.bak", content)


class DiscardChangesHandler:
    """Reloads ini + sandbox from disk, dropping in-memory edits."""

    def __init__(self, bus: MessageBus, state: SessionState, source: ConfigSource) -> None:
        self._bus = bus
        self._state = state
        self._source = source

    async def __call__(self, cmd: DiscardChanges) -> None:
        from zomboid_modder.domain.ini import PzIni
        from zomboid_modder.domain.mod_list import ModList
        from zomboid_modder.domain.sandbox import SandboxVars

        try:
            if await self._source.exists(self._state.ini_relpath()):
                text = await self._source.read_text(self._state.ini_relpath())
                self._state.ini = PzIni.parse(text)
                self._state.mod_list = ModList(self._state.ini, self._state.mod_names)
            if await self._source.exists(self._state.sandbox_relpath()):
                text = await self._source.read_text(self._state.sandbox_relpath())
                self._state.sandbox = SandboxVars.parse(text)
            self._state.dirty = False
            await self._bus.publish(PendingChangesUpdated(False))
        except Exception as e:
            await self._bus.publish(SaveFailed(str(e)))
