from __future__ import annotations

from zomboid_modder.application.state import SessionState
from zomboid_modder.core.bus import MessageBus
from zomboid_modder.core.commands import AddMod, LoadMods, RemoveMod, ReorderMod
from zomboid_modder.core.events import (
    ErrorOccurred,
    ModAdded,
    ModRemoved,
    ModReordered,
    ModResolutionFailed,
    ModResolutionProgress,
    ModResolutionStarted,
    ModsLoaded,
    PendingChangesUpdated,
)
from zomboid_modder.infrastructure.steamcmd import ResolutionError, SteamCmd, parse_workshop_input


def _require_mod_list(state: SessionState):
    if state.mod_list is None:
        raise RuntimeError("no profile connected")
    return state.mod_list


class LoadModsHandler:
    def __init__(self, bus: MessageBus, state: SessionState) -> None:
        self._bus = bus
        self._state = state

    async def __call__(self, cmd: LoadMods) -> None:
        try:
            mod_list = _require_mod_list(self._state)
            await self._bus.publish(ModsLoaded(mod_list.list()))
        except Exception as e:
            await self._bus.publish(ErrorOccurred("LoadMods", str(e)))


class AddModHandler:
    def __init__(self, bus: MessageBus, state: SessionState, steamcmd: SteamCmd) -> None:
        self._bus = bus
        self._state = state
        self._steamcmd = steamcmd

    async def __call__(self, cmd: AddMod) -> None:
        try:
            workshop_id = parse_workshop_input(cmd.workshop_id)
        except ValueError as e:
            await self._bus.publish(ModResolutionFailed(cmd.workshop_id, str(e)))
            return
        await self._bus.publish(ModResolutionStarted(workshop_id))
        try:
            async for msg in self._steamcmd.download(workshop_id):
                await self._bus.publish(ModResolutionProgress(workshop_id, msg))
            await self._bus.publish(ModResolutionProgress(workshop_id, "resolving mod id..."))
            mod = await self._steamcmd.resolve(workshop_id)
            await self._bus.publish(ModResolutionProgress(workshop_id, f"resolved: id={mod.id}"))
        except ResolutionError as e:
            if cmd.mod_id_override:
                from zomboid_modder.domain.mod import Mod

                mod = Mod(id=cmd.mod_id_override, workshop_id=workshop_id)
            else:
                await self._bus.publish(ModResolutionFailed(workshop_id, str(e)))
                return
        except Exception as e:
            await self._bus.publish(ModResolutionFailed(workshop_id, str(e)))
            return
        try:
            mod_list = _require_mod_list(self._state)
            mod_list.add(mod)
            self._state.dirty = True
            await self._bus.publish(ModResolutionProgress(workshop_id, f"added to list: id={mod.id!r} ws={mod.workshop_id!r}"))
            await self._bus.publish(ModAdded(mod))
            await self._bus.publish(PendingChangesUpdated(True))
        except Exception as e:
            await self._bus.publish(ErrorOccurred("AddMod", str(e)))


class RemoveModHandler:
    def __init__(self, bus: MessageBus, state: SessionState) -> None:
        self._bus = bus
        self._state = state

    async def __call__(self, cmd: RemoveMod) -> None:
        try:
            mod_list = _require_mod_list(self._state)
            mod_list.remove(cmd.mod_id)
            self._state.dirty = True
            await self._bus.publish(ModRemoved(cmd.mod_id))
            await self._bus.publish(PendingChangesUpdated(True))
        except Exception as e:
            await self._bus.publish(ErrorOccurred("RemoveMod", str(e)))


class ReorderModHandler:
    def __init__(self, bus: MessageBus, state: SessionState) -> None:
        self._bus = bus
        self._state = state

    async def __call__(self, cmd: ReorderMod) -> None:
        try:
            mod_list = _require_mod_list(self._state)
            mod_list.reorder(cmd.mod_id, cmd.new_index)
            self._state.dirty = True
            await self._bus.publish(ModReordered(cmd.mod_id, cmd.new_index))
            await self._bus.publish(PendingChangesUpdated(True))
        except Exception as e:
            await self._bus.publish(ErrorOccurred("ReorderMod", str(e)))
