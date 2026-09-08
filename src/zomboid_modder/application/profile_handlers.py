from __future__ import annotations

from zomboid_modder.application.state import SessionState
from zomboid_modder.core.bus import MessageBus
from zomboid_modder.core.commands import ConnectProfile, Disconnect
from zomboid_modder.core.events import (
    ConnectionFailed,
    ErrorOccurred,
    ProfileConnected,
    ProfileDisconnected,
)
from zomboid_modder.domain.ini import PzIni
from zomboid_modder.domain.mod_list import ModList
from zomboid_modder.infrastructure.sources.base import ConfigSource


class ConnectProfileHandler:
    def __init__(self, bus: MessageBus, state: SessionState, source: ConfigSource) -> None:
        self._bus = bus
        self._state = state
        self._source = source

    async def __call__(self, cmd: ConnectProfile) -> None:
        try:
            if not await self._source.exists(self._state.ini_relpath()):
                await self._bus.publish(
                    ConnectionFailed(f"{self._state.ini_relpath()} not found in server dir")
                )
                return
            text = await self._source.read_text(self._state.ini_relpath())
            ini = PzIni.parse(text)
            self._state.ini = ini
            self._state.mod_list = ModList(ini, self._state.mod_names)
            self._state.dirty = False
            await self._bus.publish(ProfileConnected(cmd.name))
        except Exception as e:
            await self._bus.publish(ConnectionFailed(str(e)))
            await self._bus.publish(ErrorOccurred("ConnectProfile", str(e)))


class DisconnectHandler:
    def __init__(self, bus: MessageBus, state: SessionState, source: ConfigSource) -> None:
        self._bus = bus
        self._state = state
        self._source = source

    async def __call__(self, cmd: Disconnect) -> None:
        await self._source.close()
        self._state.ini = None
        self._state.mod_list = None
        self._state.sandbox = None
        self._state.spawn_text = None
        self._state.dirty = False
        await self._bus.publish(ProfileDisconnected())
