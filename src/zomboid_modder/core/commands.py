from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Command:
    pass


@dataclass(frozen=True)
class ConnectProfile(Command):
    name: str


@dataclass(frozen=True)
class Disconnect(Command):
    pass


@dataclass(frozen=True)
class LoadMods(Command):
    pass


@dataclass(frozen=True)
class AddMod(Command):
    workshop_id: str
    mod_id_override: str | None = None


@dataclass(frozen=True)
class RemoveMod(Command):
    mod_id: str


@dataclass(frozen=True)
class ReorderMod(Command):
    mod_id: str
    new_index: int


@dataclass(frozen=True)
class LoadSettings(Command):
    pass


@dataclass(frozen=True)
class SetSetting(Command):
    key: str
    value: str


@dataclass(frozen=True)
class LoadSandbox(Command):
    pass


@dataclass(frozen=True)
class SetSandboxVar(Command):
    dotted_key: str
    value: Any


@dataclass(frozen=True)
class LoadSpawnRegions(Command):
    pass


@dataclass(frozen=True)
class SaveChanges(Command):
    pass


@dataclass(frozen=True)
class DiscardChanges(Command):
    pass


@dataclass(frozen=True)
class RestartServer(Command):
    pass
