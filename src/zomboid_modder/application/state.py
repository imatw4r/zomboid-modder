from __future__ import annotations

from dataclasses import dataclass, field

from zomboid_modder.domain.ini import PzIni
from zomboid_modder.domain.mod_list import ModList
from zomboid_modder.domain.sandbox import SandboxVars


@dataclass
class SessionState:
    server_name: str = "servertest"
    ini: PzIni | None = None
    mod_list: ModList | None = None
    sandbox: SandboxVars | None = None
    spawn_text: str | None = None
    mod_names: dict[str, str] = field(default_factory=dict)
    dirty: bool = False

    def ini_relpath(self) -> str:
        return f"{self.server_name}.ini"

    def sandbox_relpath(self) -> str:
        return f"{self.server_name}_SandboxVars.lua"

    def spawn_relpath(self) -> str:
        return f"{self.server_name}_spawnregions.lua"
