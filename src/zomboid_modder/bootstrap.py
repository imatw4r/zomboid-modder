from __future__ import annotations

from dataclasses import dataclass

from zomboid_modder.application.mod_handlers import (
    AddModHandler,
    LoadModsHandler,
    RemoveModHandler,
    ReorderModHandler,
)
from zomboid_modder.application.profile_handlers import (
    ConnectProfileHandler,
    DisconnectHandler,
)
from zomboid_modder.application.restart_handlers import RestartServerHandler
from zomboid_modder.application.sandbox_handlers import (
    LoadSandboxHandler,
    LoadSpawnRegionsHandler,
    SetSandboxVarHandler,
)
from zomboid_modder.application.save_handlers import (
    DiscardChangesHandler,
    SaveChangesHandler,
)
from zomboid_modder.application.settings_handlers import (
    LoadSettingsHandler,
    SetSettingHandler,
)
from zomboid_modder.application.state import SessionState
from zomboid_modder.core.bus import MessageBus
from zomboid_modder.core.commands import (
    AddMod,
    ConnectProfile,
    DiscardChanges,
    Disconnect,
    LoadMods,
    LoadSandbox,
    LoadSettings,
    LoadSpawnRegions,
    RemoveMod,
    ReorderMod,
    RestartServer,
    SaveChanges,
    SetSandboxVar,
    SetSetting,
)
from zomboid_modder.infrastructure.config import LocalProfile, Profile, SshProfile
from zomboid_modder.infrastructure.sources.base import ConfigSource
from zomboid_modder.infrastructure.sources.local import LocalSource
from zomboid_modder.infrastructure.sources.ssh import SshSource
from zomboid_modder.infrastructure.steamcmd import SteamCmd


@dataclass
class AppContext:
    bus: MessageBus
    state: SessionState
    source: ConfigSource
    profile: Profile


def build_source(profile: Profile) -> ConfigSource:
    if isinstance(profile, LocalProfile):
        return LocalSource(profile.server_dir)
    if isinstance(profile, SshProfile):
        return SshSource(profile)
    raise ValueError(f"unknown profile type: {profile}")


def build_context(profile: Profile) -> AppContext:
    bus = MessageBus()
    state = SessionState(server_name=profile.server_name)
    source = build_source(profile)
    steamcmd = SteamCmd(source, profile.steamcmd_path, profile.steamcmd_dir)

    bus.register(ConnectProfile, ConnectProfileHandler(bus, state, source))
    bus.register(Disconnect, DisconnectHandler(bus, state, source))
    bus.register(LoadMods, LoadModsHandler(bus, state))
    bus.register(AddMod, AddModHandler(bus, state, steamcmd))
    bus.register(RemoveMod, RemoveModHandler(bus, state))
    bus.register(ReorderMod, ReorderModHandler(bus, state))
    bus.register(LoadSettings, LoadSettingsHandler(bus, state))
    bus.register(SetSetting, SetSettingHandler(bus, state))
    bus.register(LoadSandbox, LoadSandboxHandler(bus, state, source))
    bus.register(SetSandboxVar, SetSandboxVarHandler(bus, state))
    bus.register(LoadSpawnRegions, LoadSpawnRegionsHandler(bus, state, source))
    bus.register(SaveChanges, SaveChangesHandler(bus, state, source))
    bus.register(DiscardChanges, DiscardChangesHandler(bus, state, source))
    bus.register(RestartServer, RestartServerHandler(bus, source, profile.restart_cmd))

    return AppContext(bus=bus, state=state, source=source, profile=profile)
