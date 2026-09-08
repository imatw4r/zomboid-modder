from dataclasses import dataclass

from zomboid_modder.application.mod_handlers import (
    AddModHandler,
    LoadModsHandler,
    RemoveModHandler,
)
from zomboid_modder.application.profile_handlers import ConnectProfileHandler
from zomboid_modder.application.save_handlers import SaveChangesHandler
from zomboid_modder.application.settings_handlers import (
    LoadSettingsHandler,
    SetSettingHandler,
)
from zomboid_modder.application.state import SessionState
from zomboid_modder.core.bus import MessageBus
from zomboid_modder.core.commands import (
    AddMod,
    ConnectProfile,
    LoadMods,
    LoadSettings,
    RemoveMod,
    SaveChanges,
    SetSetting,
)
from zomboid_modder.core.events import (
    ModAdded,
    ModsLoaded,
    PendingChangesUpdated,
    ProfileConnected,
    SaveCompleted,
    SettingsLoaded,
)
from zomboid_modder.domain.mod import Mod


class InMemorySource:
    def __init__(self, files: dict[str, str] | None = None) -> None:
        self.files = dict(files or {})

    async def read_text(self, relpath: str) -> str:
        return self.files[relpath]

    async def write_text(self, relpath: str, content: str) -> None:
        self.files[relpath] = content

    async def list_dir(self, relpath: str) -> list[str]:
        prefix = relpath.rstrip("/") + "/"
        seen: set[str] = set()
        for k in self.files:
            if k.startswith(prefix):
                seen.add(k[len(prefix) :].split("/", 1)[0])
        return sorted(seen)

    async def exists(self, relpath: str) -> bool:
        if relpath in self.files:
            return True
        prefix = relpath.rstrip("/") + "/"
        return any(k.startswith(prefix) for k in self.files)

    async def run(self, cmd: list[str]) -> tuple[int, str, str]:
        return 0, "", ""

    async def close(self) -> None:
        return None


@dataclass
class FakeSteam:
    def __init__(self, resolved: Mod) -> None:
        self._resolved = resolved

    async def download(self, workshop_id: str):
        yield f"pretend-download {workshop_id}"

    async def resolve(self, workshop_id: str) -> Mod:
        return self._resolved


def _seed_source() -> InMemorySource:
    return InMemorySource(
        {
            "servertest.ini": "PVP=true\nMods=Foo\nWorkshopItems=111\n",
        }
    )


async def _connect(bus: MessageBus, state: SessionState, source: InMemorySource):
    bus.register(ConnectProfile, ConnectProfileHandler(bus, state, source))
    await bus.send(ConnectProfile("test"))


async def test_connect_publishes_profile_connected():
    bus = MessageBus()
    state = SessionState()
    source = _seed_source()
    events = []
    async def cap(e):
        events.append(e)

    bus.subscribe(ProfileConnected, cap)
    await _connect(bus, state, source)
    assert state.ini is not None
    assert events == [ProfileConnected("test")]


async def test_load_mods_emits_current_mods():
    bus = MessageBus()
    state = SessionState()
    source = _seed_source()
    await _connect(bus, state, source)
    bus.register(LoadMods, LoadModsHandler(bus, state))
    seen: list[ModsLoaded] = []

    async def cap(e):
        seen.append(e)

    bus.subscribe(ModsLoaded, cap)
    await bus.send(LoadMods())
    assert len(seen) == 1
    assert [m.id for m in seen[0].mods] == ["Foo"]


async def test_add_mod_updates_state_and_publishes_events():
    bus = MessageBus()
    state = SessionState()
    source = _seed_source()
    await _connect(bus, state, source)
    steam = FakeSteam(Mod(id="Baz", workshop_id="333", name="Baz"))
    bus.register(AddMod, AddModHandler(bus, state, steam))
    added: list[ModAdded] = []
    dirty: list[PendingChangesUpdated] = []

    async def cap_added(e):
        added.append(e)

    async def cap_dirty(e):
        dirty.append(e)

    bus.subscribe(ModAdded, cap_added)
    bus.subscribe(PendingChangesUpdated, cap_dirty)
    await bus.send(AddMod(workshop_id="333"))
    assert added and added[0].mod.id == "Baz"
    assert dirty and dirty[-1].dirty is True
    assert state.dirty is True
    assert [m.id for m in state.mod_list.list()] == ["Foo", "Baz"]


async def test_remove_mod_updates_state():
    bus = MessageBus()
    state = SessionState()
    source = _seed_source()
    await _connect(bus, state, source)
    bus.register(RemoveMod, RemoveModHandler(bus, state))
    await bus.send(RemoveMod("Foo"))
    assert state.mod_list.list() == []


async def test_set_setting_marks_dirty():
    bus = MessageBus()
    state = SessionState()
    source = _seed_source()
    await _connect(bus, state, source)
    bus.register(SetSetting, SetSettingHandler(bus, state))
    await bus.send(SetSetting(key="PVP", value="false"))
    assert state.ini.get("PVP") == "false"
    assert state.dirty is True


async def test_load_settings_hides_mod_keys():
    bus = MessageBus()
    state = SessionState()
    source = _seed_source()
    await _connect(bus, state, source)
    bus.register(LoadSettings, LoadSettingsHandler(bus, state))
    seen: list[SettingsLoaded] = []

    async def cap(e):
        seen.append(e)

    bus.subscribe(SettingsLoaded, cap)
    await bus.send(LoadSettings())
    keys = [e.key for e in seen[0].entries]
    assert "PVP" in keys
    assert "Mods" not in keys
    assert "WorkshopItems" not in keys


async def test_save_writes_ini_and_backup():
    bus = MessageBus()
    state = SessionState()
    source = _seed_source()
    await _connect(bus, state, source)
    bus.register(SetSetting, SetSettingHandler(bus, state))
    bus.register(SaveChanges, SaveChangesHandler(bus, state, source))
    saved: list[SaveCompleted] = []

    async def cap_saved(e):
        saved.append(e)

    bus.subscribe(SaveCompleted, cap_saved)
    await bus.send(SetSetting(key="PVP", value="false"))
    await bus.send(SaveChanges())
    assert saved and "servertest.ini" in saved[0].files
    assert "PVP=false" in source.files["servertest.ini"]
    assert "servertest.ini.bak" in source.files
    assert state.dirty is False
