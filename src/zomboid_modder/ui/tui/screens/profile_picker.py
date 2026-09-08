from __future__ import annotations

from collections.abc import Callable

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, ListItem, ListView, Static

from zomboid_modder.infrastructure.config import Config


class ProfilePickerScreen(Screen):
    BINDINGS = [
        ("enter", "connect", "Connect"),
        ("c", "connect", "Connect"),
    ]

    def __init__(self, config: Config, on_selected: Callable[[str], None]) -> None:
        super().__init__()
        self._config = config
        self._on_selected = on_selected

    def compose(self) -> ComposeResult:
        yield Header()
        if not self._config.profile:
            yield Vertical(
                Static("No profiles configured."),
                Static(f"Create one at: {_config_hint()}"),
                Button("Quit", id="quit"),
            )
        else:
            items = [
                ListItem(Static(f"{p.name}  [{p.type}]  {_summary(p)}"), id=f"profile-{p.name}")
                for p in self._config.profile
            ]
            yield Vertical(
                Static("Arrow keys to highlight, then press 'c' or click Connect:"),
                ListView(*items, id="profile-list"),
                Button("Connect", variant="primary", id="connect-btn"),
            )
        yield Footer()

    def on_mount(self) -> None:
        if self._config.profile:
            self.query_one("#profile-list", ListView).focus()

    def action_connect(self) -> None:
        listview = self.query_one("#profile-list", ListView)
        if listview.highlighted_child is None:
            self.notify("nothing highlighted", severity="warning")
            return
        item_id = listview.highlighted_child.id
        if item_id and item_id.startswith("profile-"):
            name = item_id.removeprefix("profile-")
            self.notify(f"connecting to {name}...")
            self._on_selected(name)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.item.id and event.item.id.startswith("profile-"):
            name = event.item.id.removeprefix("profile-")
            self.notify(f"connecting to {name}...")
            self._on_selected(name)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "quit":
            self.app.exit()
        elif event.button.id == "connect-btn":
            self.action_connect()


def _summary(profile) -> str:
    if profile.type == "local":
        return profile.server_dir
    return f"{profile.user}@{profile.host}:{profile.server_dir}"


def _config_hint() -> str:
    from zomboid_modder.infrastructure.config import default_config_path
    return str(default_config_path())
