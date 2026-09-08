from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Static, TabbedContent, TabPane

from zomboid_modder.bootstrap import AppContext
from zomboid_modder.core.commands import (
    ConnectProfile,
    LoadMods,
    LoadSandbox,
    LoadSettings,
    LoadSpawnRegions,
    RestartServer,
    SaveChanges,
)
from zomboid_modder.core.events import (
    ConnectionFailed,
    ErrorOccurred,
    ModsLoaded,
    PendingChangesUpdated,
    ProfileConnected,
    SaveCompleted,
    SaveFailed,
)
from zomboid_modder.core.commands import RemoveMod
from zomboid_modder.ui.tui.screens.modals import AddModModal, RestartModal
from zomboid_modder.ui.tui.widgets.mods_tab import ModsTab
from zomboid_modder.ui.tui.widgets.sandbox_tab import SandboxTab
from zomboid_modder.ui.tui.widgets.settings_tab import SettingsTab
from zomboid_modder.ui.tui.widgets.spawn_tab import SpawnTab


class MainScreen(Screen):
    CSS = """
    #status-bar { dock: top; height: 1; background: $primary; color: $text; padding: 0 1; }
    #log-panel { dock: bottom; height: 8; border-top: solid $primary; background: $panel; padding: 0 1; }
    #log { height: 100%; }
    """

    BINDINGS = [
        ("A", "add_mod", "Add mod"),
        ("D", "remove_mod", "Remove mod"),
        Binding("left", "prev_tab", "Prev tab", priority=True),
        Binding("right", "next_tab", "Next tab", priority=True),
        ("ctrl+s", "save", "Save"),
        ("ctrl+r", "restart", "Restart"),
        ("ctrl+p", "switch_profile", "Profiles"),
    ]

    def __init__(self, context: AppContext) -> None:
        super().__init__()
        self._ctx = context
        self._dirty = False
        self._connecting = False
        self._log_lines: list[str] = []

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(self._status_text(), id="status-bar")
        with TabbedContent(initial="mods"):
            with TabPane("Mods", id="mods"):
                yield ModsTab(self._ctx)
            with TabPane("Settings", id="settings"):
                yield SettingsTab(self._ctx)
            with TabPane("Sandbox", id="sandbox"):
                yield SandboxTab(self._ctx)
            with TabPane("Spawn", id="spawn"):
                yield SpawnTab(self._ctx)
        yield Vertical(Static("", id="log"), id="log-panel")
        yield Footer()

    def on_mount(self) -> None:
        bus = self._ctx.bus
        bus.subscribe(ProfileConnected, self._on_connected)
        bus.subscribe(ConnectionFailed, self._on_conn_failed)
        bus.subscribe(PendingChangesUpdated, self._on_dirty)
        bus.subscribe(SaveCompleted, self._on_save_ok)
        bus.subscribe(SaveFailed, self._on_save_fail)
        bus.subscribe(ErrorOccurred, self._on_error)
        bus.subscribe(ModsLoaded, self._on_mods_loaded)
        self._connecting = True
        self._refresh_status()
        self._log(f"connecting to {self._ctx.profile.name}...")
        self.run_worker(self._kick_connect(), exclusive=False)

    async def _kick_connect(self) -> None:
        try:
            await self._ctx.bus.send(ConnectProfile(self._ctx.profile.name))
        except Exception as e:
            await self._ctx.bus.publish(ErrorOccurred("MainScreen.on_mount", repr(e)))

    async def _on_connected(self, event: ProfileConnected) -> None:
        self._connecting = False
        self._log(f"connected: {event.name}")
        self._refresh_status()
        bus = self._ctx.bus
        await bus.send(LoadMods())
        await bus.send(LoadSettings())
        await bus.send(LoadSandbox())
        await bus.send(LoadSpawnRegions())

    async def _on_conn_failed(self, event: ConnectionFailed) -> None:
        self._connecting = False
        self._log(f"connection failed: {event.reason}")
        self._refresh_status()

    async def _on_dirty(self, event: PendingChangesUpdated) -> None:
        self._dirty = event.dirty
        self._refresh_status()

    async def _on_save_ok(self, event: SaveCompleted) -> None:
        self._log(f"saved: {', '.join(event.files)}")

    async def _on_save_fail(self, event: SaveFailed) -> None:
        self._log(f"save failed: {event.reason}")

    async def _on_error(self, event: ErrorOccurred) -> None:
        self._log(f"[{event.source}] {event.message}")

    async def _on_mods_loaded(self, event: ModsLoaded) -> None:
        try:
            tabs = self.query_one(TabbedContent)
            tabs.get_tab("mods").label = f"Mods ({len(event.mods)})"
        except Exception:
            pass

    def action_add_mod(self) -> None:
        self.app.push_screen(AddModModal(self._ctx))

    def action_remove_mod(self) -> None:
        from textual.widgets import DataTable
        try:
            table = self.query_one("#mods-table", DataTable)
        except Exception:
            return
        if table.cursor_row is None or table.row_count == 0:
            return
        row_key = table.coordinate_to_cell_key((table.cursor_row, 0)).row_key
        if row_key.value is None:
            return
        self.run_worker(self._ctx.bus.send(RemoveMod(str(row_key.value))), exclusive=False)

    def action_refresh(self) -> None:
        self.run_worker(self._ctx.bus.send(LoadMods()), exclusive=False)

    def action_save(self) -> None:
        self.run_worker(self._ctx.bus.send(SaveChanges()), exclusive=False)

    def action_restart(self) -> None:
        self.app.push_screen(RestartModal(self._ctx))

    def action_switch_profile(self) -> None:
        self.app.pop_screen()

    def _cycle_tab(self, delta: int) -> None:
        tabs = self.query_one(TabbedContent)
        ids = ["mods", "settings", "sandbox", "spawn"]
        try:
            i = ids.index(tabs.active)
        except ValueError:
            i = 0
        tabs.active = ids[(i + delta) % len(ids)]

    def action_prev_tab(self) -> None:
        self._cycle_tab(-1)

    def action_next_tab(self) -> None:
        self._cycle_tab(1)

    def _status_text(self) -> str:
        p = self._ctx.profile
        dot = " *" if self._dirty else ""
        conn = " ... connecting" if self._connecting else ""
        return f"profile: {p.name} [{p.type}]  server: {p.server_name}{dot}{conn}"

    def _refresh_status(self) -> None:
        self.query_one("#status-bar", Static).update(self._status_text())

    def _log(self, msg: str) -> None:
        self._log_lines.append(msg)
        self._log_lines = self._log_lines[-5:]
        self.query_one("#log", Static).update("\n".join(self._log_lines))
