from __future__ import annotations

from zomboid_modder.domain.ini import PzIni
from zomboid_modder.domain.mod import Mod


class ModListError(Exception):
    pass


class ModList:
    """Mutations against a PzIni. Keeps Mods= and WorkshopItems= index-aligned.

    Mod names are not stored in the .ini; they are attached at load time from
    an external cache (e.g. workshop metadata) when available.
    """

    MODS_KEY = "Mods"
    WORKSHOP_KEY = "WorkshopItems"

    def __init__(self, ini: PzIni, names: dict[str, str] | None = None) -> None:
        self._ini = ini
        self._names = names or {}
        self._mod_ids = self._split(ini.get(self.MODS_KEY) or "")
        self._workshop_ids = self._split(ini.get(self.WORKSHOP_KEY) or "")

    @staticmethod
    def _split(raw: str) -> list[str]:
        return [p.strip() for p in raw.split(";") if p.strip()]

    @staticmethod
    def _join(items: list[str]) -> str:
        return ";".join(items)

    def _flush(self) -> None:
        self._ini.set(self.MODS_KEY, self._join(self._mod_ids))
        self._ini.set(self.WORKSHOP_KEY, self._join(self._workshop_ids))

    def list(self) -> list[Mod]:
        mods: list[Mod] = []
        pairs = zip(self._mod_ids, self._workshop_ids, strict=False)
        for mod_id, workshop_id in pairs:
            mods.append(Mod(id=mod_id, workshop_id=workshop_id, name=self._names.get(mod_id)))
        return mods

    def add(self, mod: Mod) -> None:
        if mod.id in self._mod_ids:
            raise ModListError(f"Mod already present: {mod.id}")
        self._mod_ids.append(mod.id)
        self._workshop_ids.append(mod.workshop_id)
        if mod.name:
            self._names[mod.id] = mod.name
        self._flush()

    def remove(self, mod_id: str) -> None:
        if mod_id not in self._mod_ids:
            raise ModListError(f"Mod not found: {mod_id}")
        idx = self._mod_ids.index(mod_id)
        self._mod_ids.pop(idx)
        if idx < len(self._workshop_ids):
            self._workshop_ids.pop(idx)
        self._names.pop(mod_id, None)
        self._flush()

    def reorder(self, mod_id: str, new_index: int) -> None:
        if mod_id not in self._mod_ids:
            raise ModListError(f"Mod not found: {mod_id}")
        old = self._mod_ids.index(mod_id)
        new_index = max(0, min(new_index, len(self._mod_ids) - 1))
        self._mod_ids.insert(new_index, self._mod_ids.pop(old))
        if old < len(self._workshop_ids):
            self._workshop_ids.insert(new_index, self._workshop_ids.pop(old))
        self._flush()
