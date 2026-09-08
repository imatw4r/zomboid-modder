from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widget import Widget
from textual.widgets import Static, TextArea

from zomboid_modder.bootstrap import AppContext
from zomboid_modder.core.events import SpawnRegionsLoaded


class SpawnTab(Widget):
    DEFAULT_CSS = """
    SpawnTab { height: 1fr; }
    SpawnTab Vertical { height: 1fr; }
    SpawnTab TextArea { height: 1fr; }
    """

    def __init__(self, context: AppContext) -> None:
        super().__init__()
        self._ctx = context

    def compose(self) -> ComposeResult:
        yield Vertical(
            Static("spawnregions.lua (read-only view):"),
            TextArea("", id="spawn-view", read_only=True, language="lua"),
        )

    def on_mount(self) -> None:
        self._ctx.bus.subscribe(SpawnRegionsLoaded, self._on_loaded)

    async def _on_loaded(self, event: SpawnRegionsLoaded) -> None:
        area = self.query_one("#spawn-view", TextArea)
        area.load_text(event.text or "(no spawnregions.lua present)")
