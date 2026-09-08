from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from zomboid_modder.domain.mod import Mod


@dataclass(frozen=True)
class Event:
    pass


@dataclass(frozen=True)
class ProfileConnected(Event):
    name: str


@dataclass(frozen=True)
class ProfileDisconnected(Event):
    pass


@dataclass(frozen=True)
class ConnectionFailed(Event):
    reason: str


@dataclass(frozen=True)
class ModsLoaded(Event):
    mods: list["Mod"] = field(default_factory=list)


@dataclass(frozen=True)
class ModAdded(Event):
    mod: "Mod"


@dataclass(frozen=True)
class ModRemoved(Event):
    mod_id: str


@dataclass(frozen=True)
class ModReordered(Event):
    mod_id: str
    new_index: int


@dataclass(frozen=True)
class ModResolutionStarted(Event):
    workshop_id: str


@dataclass(frozen=True)
class ModResolutionProgress(Event):
    workshop_id: str
    message: str


@dataclass(frozen=True)
class ModResolutionFailed(Event):
    workshop_id: str
    reason: str


@dataclass(frozen=True)
class SettingEntry:
    key: str
    value: str


@dataclass(frozen=True)
class SettingsLoaded(Event):
    entries: list[SettingEntry] = field(default_factory=list)


@dataclass(frozen=True)
class SettingChanged(Event):
    key: str
    value: str


@dataclass(frozen=True)
class SandboxEntry:
    dotted_key: str
    value: Any
    value_type: str


@dataclass(frozen=True)
class SandboxLoaded(Event):
    entries: list[SandboxEntry] = field(default_factory=list)


@dataclass(frozen=True)
class SandboxVarChanged(Event):
    dotted_key: str
    value: Any


@dataclass(frozen=True)
class SpawnRegionsLoaded(Event):
    text: str


@dataclass(frozen=True)
class PendingChangesUpdated(Event):
    dirty: bool


@dataclass(frozen=True)
class SaveStarted(Event):
    pass


@dataclass(frozen=True)
class SaveCompleted(Event):
    files: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SaveFailed(Event):
    reason: str


@dataclass(frozen=True)
class RestartStarted(Event):
    pass


@dataclass(frozen=True)
class RestartOutput(Event):
    line: str


@dataclass(frozen=True)
class RestartCompleted(Event):
    exit_code: int


@dataclass(frozen=True)
class ErrorOccurred(Event):
    source: str
    message: str
