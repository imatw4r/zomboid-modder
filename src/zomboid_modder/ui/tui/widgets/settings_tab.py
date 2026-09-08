from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widget import Widget
from textual.widgets import DataTable, Input, Static

from zomboid_modder.bootstrap import AppContext
from zomboid_modder.core.commands import LoadSettings
from zomboid_modder.core.events import SettingChanged, SettingEntry, SettingsLoaded
from zomboid_modder.ui.tui.screens.modals import EditValueModal


class SettingsTab(Widget):
    DEFAULT_CSS = """
    SettingsTab { height: 1fr; }
    SettingsTab Vertical { height: 1fr; }
    SettingsTab DataTable { height: 1fr; }
    """

    def __init__(self, context: AppContext) -> None:
        super().__init__()
        self._ctx = context
        self._entries: list[SettingEntry] = []
        self._filter = ""

    def compose(self) -> ComposeResult:
        yield Vertical(
            Static("Search (type to filter, Enter on row to edit):"),
            Input(placeholder="filter...", id="settings-filter"),
            DataTable(id="settings-table", cursor_type="row", zebra_stripes=True),
        )

    def on_mount(self) -> None:
        table = self.query_one("#settings-table", DataTable)
        table.add_columns("Key", "Value")
        bus = self._ctx.bus
        bus.subscribe(SettingsLoaded, self._on_loaded)
        bus.subscribe(SettingChanged, self._on_changed)

    async def _on_loaded(self, event: SettingsLoaded) -> None:
        self._entries = list(event.entries)
        self._refresh_table()

    async def _on_changed(self, _event: SettingChanged) -> None:
        await self._ctx.bus.send(LoadSettings())

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "settings-filter":
            self._filter = event.value.lower()
            self._refresh_table()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        key = str(event.row_key.value) if event.row_key.value else None
        if not key:
            return
        entry = next((e for e in self._entries if e.key == key), None)
        if entry is None:
            return

        def _submit(new_value: str) -> None:
            from zomboid_modder.core.commands import SetSetting
            self.run_worker(
                self._ctx.bus.send(SetSetting(key=entry.key, value=new_value)),
                exclusive=False,
            )

        self.app.push_screen(EditValueModal(entry.key, entry.value, _submit))

    def _refresh_table(self) -> None:
        table = self.query_one("#settings-table", DataTable)
        table.clear()
        for entry in self._entries:
            if self._filter and self._filter not in entry.key.lower():
                continue
            table.add_row(entry.key, entry.value, key=entry.key)
