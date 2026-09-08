from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widget import Widget
from textual.widgets import DataTable, Static

from zomboid_modder.bootstrap import AppContext
from zomboid_modder.core.commands import LoadMods, RemoveMod
from zomboid_modder.core.events import ModAdded, ModRemoved, ModsLoaded
from zomboid_modder.ui.tui.screens.modals import AddModModal


class ModsTab(Widget):
    DEFAULT_CSS = """
    ModsTab { height: 1fr; }
    ModsTab Vertical { height: 1fr; }
    ModsTab DataTable { height: 1fr; }
    """
    BINDINGS = [
        ("a", "add", "Add"),
        ("d", "remove", "Remove"),
        ("r", "refresh", "Refresh"),
    ]

    def __init__(self, context: AppContext) -> None:
        super().__init__()
        self._ctx = context

    def compose(self) -> ComposeResult:
        yield Vertical(
            Static("[a] add   [d] remove   [r] refresh"),
            DataTable(id="mods-table", cursor_type="row", zebra_stripes=True),
        )

    def on_mount(self) -> None:
        table = self.query_one("#mods-table", DataTable)
        table.add_columns("#", "Mod ID", "Workshop ID", "Name")
        table.focus()
        bus = self._ctx.bus
        bus.subscribe(ModsLoaded, self._on_loaded)
        bus.subscribe(ModAdded, self._on_change)
        bus.subscribe(ModRemoved, self._on_change)

    async def _on_loaded(self, event: ModsLoaded) -> None:
        table = self.query_one("#mods-table", DataTable)
        table.clear()
        for i, mod in enumerate(event.mods):
            table.add_row(str(i + 1), mod.id, mod.workshop_id, mod.name or "-", key=mod.id)
        if table.row_count:
            table.focus()

    async def _on_change(self, _event) -> None:
        await self._ctx.bus.send(LoadMods())

    def action_add(self) -> None:
        self.app.push_screen(AddModModal(self._ctx))

    def action_remove(self) -> None:
        table = self.query_one("#mods-table", DataTable)
        if table.cursor_row is None or table.row_count == 0:
            return
        row_key = table.coordinate_to_cell_key((table.cursor_row, 0)).row_key
        if row_key.value is None:
            return
        self.run_worker(self._ctx.bus.send(RemoveMod(str(row_key.value))), exclusive=False)

    def action_refresh(self) -> None:
        self.run_worker(self._ctx.bus.send(LoadMods()), exclusive=False)
