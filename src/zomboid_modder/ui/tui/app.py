from __future__ import annotations

from pathlib import Path

from textual.app import App

from zomboid_modder.bootstrap import AppContext, build_context
from zomboid_modder.infrastructure.config import Config, load_config
from zomboid_modder.ui.tui.screens.main import MainScreen
from zomboid_modder.ui.tui.screens.profile_picker import ProfilePickerScreen


class ZomboidModderApp(App):
    CSS = """
    Screen { background: $surface; }
    #header-bar { dock: top; height: 1; background: $primary; color: $text; padding: 0 1; }
    #footer-bar { dock: bottom; height: 1; background: $panel; color: $text; padding: 0 1; }
    .dirty { color: $warning; }
    """

    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
    ]

    def __init__(self, profile_name: str | None = None, config_path: str | None = None) -> None:
        super().__init__()
        self._profile_name = profile_name
        self._config_path = Path(config_path) if config_path else None
        self._config: Config = load_config(self._config_path)
        self._app_context: AppContext | None = None

    def on_mount(self) -> None:
        if self._profile_name:
            profile = self._config.get(self._profile_name)
            if profile:
                self._app_context = build_context(profile)
                self.push_screen(MainScreen(self._app_context))
                return
        self.push_screen(
            ProfilePickerScreen(self._config, self._on_profile_selected)
        )

    def _on_profile_selected(self, profile_name: str) -> None:
        profile = self._config.get(profile_name)
        if profile is None:
            return
        self._app_context = build_context(profile)
        self.push_screen(MainScreen(self._app_context))
