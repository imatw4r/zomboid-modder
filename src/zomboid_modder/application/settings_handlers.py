from __future__ import annotations

from zomboid_modder.application.state import SessionState
from zomboid_modder.core.bus import MessageBus
from zomboid_modder.core.commands import LoadSettings, SetSetting
from zomboid_modder.core.events import (
    ErrorOccurred,
    PendingChangesUpdated,
    SettingChanged,
    SettingEntry,
    SettingsLoaded,
)

HIDDEN = {"Mods", "WorkshopItems"}


class LoadSettingsHandler:
    def __init__(self, bus: MessageBus, state: SessionState) -> None:
        self._bus = bus
        self._state = state

    async def __call__(self, cmd: LoadSettings) -> None:
        try:
            if self._state.ini is None:
                raise RuntimeError("no profile connected")
            entries = [
                SettingEntry(key=k, value=v)
                for k, v in self._state.ini.items()
                if k not in HIDDEN
            ]
            await self._bus.publish(SettingsLoaded(entries))
        except Exception as e:
            await self._bus.publish(ErrorOccurred("LoadSettings", str(e)))


class SetSettingHandler:
    def __init__(self, bus: MessageBus, state: SessionState) -> None:
        self._bus = bus
        self._state = state

    async def __call__(self, cmd: SetSetting) -> None:
        try:
            if self._state.ini is None:
                raise RuntimeError("no profile connected")
            self._state.ini.set(cmd.key, cmd.value)
            self._state.dirty = True
            await self._bus.publish(SettingChanged(cmd.key, cmd.value))
            await self._bus.publish(PendingChangesUpdated(True))
        except Exception as e:
            await self._bus.publish(ErrorOccurred("SetSetting", str(e)))
