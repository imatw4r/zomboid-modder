from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widget import Widget
from textual.widgets import DataTable, Input, Static

from zomboid_modder.bootstrap import AppContext
from zomboid_modder.core.commands import LoadSandbox, SetSandboxVar
from zomboid_modder.core.events import SandboxEntry, SandboxLoaded, SandboxVarChanged
from zomboid_modder.ui.tui.screens.modals import EditValueModal


class SandboxTab(Widget):
    DEFAULT_CSS = """
    SandboxTab { height: 1fr; }
    SandboxTab Vertical { height: 1fr; }
    SandboxTab DataTable { height: 1fr; }
    """

    def __init__(self, context: AppContext) -> None:
        super().__init__()
        self._ctx = context
        self._entries: list[SandboxEntry] = []
        self._filter = ""

    def compose(self) -> ComposeResult:
        yield Vertical(
            Static("Search (Enter on row to edit):"),
            Input(placeholder="filter (e.g. ZombieLore.Speed)...", id="sandbox-filter"),
            DataTable(id="sandbox-table", cursor_type="row", zebra_stripes=True),
        )

    def on_mount(self) -> None:
        table = self.query_one("#sandbox-table", DataTable)
        table.add_columns("Key", "Value", "Type")
        bus = self._ctx.bus
        bus.subscribe(SandboxLoaded, self._on_loaded)
        bus.subscribe(SandboxVarChanged, self._on_changed)

    async def _on_loaded(self, event: SandboxLoaded) -> None:
        self._entries = list(event.entries)
        self._refresh_table()

    async def _on_changed(self, _event: SandboxVarChanged) -> None:
        await self._ctx.bus.send(LoadSandbox())

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "sandbox-filter":
            self._filter = event.value.lower()
            self._refresh_table()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        key = str(event.row_key.value) if event.row_key.value else None
        if not key:
            return
        entry = next((e for e in self._entries if e.dotted_key == key), None)
        if entry is None:
            return

        def _submit(new_value: str) -> None:
            self.run_worker(
                self._ctx.bus.send(SetSandboxVar(dotted_key=entry.dotted_key, value=new_value)),
                exclusive=False,
            )

        self.app.push_screen(EditValueModal(entry.dotted_key, str(entry.value), _submit))

    def _refresh_table(self) -> None:
        table = self.query_one("#sandbox-table", DataTable)
        table.clear()
        for entry in self._entries:
            if self._filter and self._filter not in entry.dotted_key.lower():
                continue
            table.add_row(entry.dotted_key, str(entry.value), entry.value_type, key=entry.dotted_key)
