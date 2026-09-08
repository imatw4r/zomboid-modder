from __future__ import annotations

from collections.abc import Callable

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Log, Static

from zomboid_modder.bootstrap import AppContext
from zomboid_modder.core.commands import AddMod, RestartServer
from zomboid_modder.core.events import (
    ModAdded,
    ModResolutionFailed,
    ModResolutionProgress,
    ModResolutionStarted,
    RestartCompleted,
    RestartOutput,
    RestartStarted,
)


class EditValueModal(ModalScreen):
    BINDINGS = [("escape", "cancel", "Cancel")]

    def __init__(self, key: str, current: str, on_submit: Callable[[str], None]) -> None:
        super().__init__()
        self._key = key
        self._current = current
        self._on_submit = on_submit

    def compose(self) -> ComposeResult:
        yield Vertical(
            Static(f"Edit: {self._key}"),
            Input(value=self._current, id="edit-input"),
            Horizontal(
                Button("Save", variant="primary", id="save"),
                Button("Cancel", id="cancel"),
            ),
            id="edit-modal",
        )

    def on_mount(self) -> None:
        self.query_one("#edit-input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            self._submit()
        else:
            self.dismiss()

    def on_input_submitted(self, _event: Input.Submitted) -> None:
        self._submit()

    def _submit(self) -> None:
        value = self.query_one("#edit-input", Input).value
        self._on_submit(value)
        self.dismiss()

    def action_cancel(self) -> None:
        self.dismiss()


class AddModModal(ModalScreen):
    BINDINGS = [("escape", "cancel", "Cancel")]

    def __init__(self, context: AppContext) -> None:
        super().__init__()
        self._ctx = context
        self._unsubs: list = []
        self._added = False

    def compose(self) -> ComposeResult:
        yield Vertical(
            Static("Add mod: paste Workshop ID or URL"),
            Input(placeholder="e.g. 2392709985 or full workshop URL", id="workshop-input"),
            Horizontal(
                Button("Add", variant="primary", id="add"),
                Button("Cancel", id="cancel"),
            ),
            Log(id="add-log", highlight=False),
            id="add-modal",
        )

    def on_mount(self) -> None:
        self.query_one("#workshop-input", Input).focus()
        bus = self._ctx.bus
        self._unsubs = [
            bus.subscribe(ModResolutionStarted, self._on_started),
            bus.subscribe(ModResolutionProgress, self._on_progress),
            bus.subscribe(ModResolutionFailed, self._on_failed),
            bus.subscribe(ModAdded, self._on_added),
        ]

    def on_unmount(self) -> None:
        for u in self._unsubs:
            u()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "add":
            self._submit()
        else:
            self.dismiss()

    def on_input_submitted(self, _event: Input.Submitted) -> None:
        if self._added:
            self.dismiss()
            return
        self._submit()

    def _submit(self) -> None:
        value = self.query_one("#workshop-input", Input).value.strip()
        if not value:
            return
        log = self.query_one("#add-log", Log)
        log.write_line(f"submitting {value}")
        self.run_worker(self._ctx.bus.send(AddMod(workshop_id=value)), exclusive=False)

    async def _on_started(self, event: ModResolutionStarted) -> None:
        self.query_one("#add-log", Log).write_line(f"resolving {event.workshop_id}...")

    async def _on_progress(self, event: ModResolutionProgress) -> None:
        self.query_one("#add-log", Log).write_line(event.message)

    async def _on_failed(self, event: ModResolutionFailed) -> None:
        self.query_one("#add-log", Log).write_line(f"failed: {event.reason}")

    async def _on_added(self, event: ModAdded) -> None:
        log = self.query_one("#add-log", Log)
        log.write_line(f"added: {event.mod.id}")
        log.write_line("press Enter to close")
        self._added = True

    def action_cancel(self) -> None:
        self.dismiss()


class RestartModal(ModalScreen):
    BINDINGS = [("escape", "cancel", "Cancel")]

    def __init__(self, context: AppContext) -> None:
        super().__init__()
        self._ctx = context
        self._unsubs: list = []

    def compose(self) -> ComposeResult:
        yield Vertical(
            Static("Restart server? Runs the profile's restart_cmd."),
            Horizontal(
                Button("Restart", variant="warning", id="go"),
                Button("Cancel", id="cancel"),
            ),
            Log(id="restart-log", highlight=False),
            id="restart-modal",
        )

    def on_mount(self) -> None:
        bus = self._ctx.bus
        self._unsubs = [
            bus.subscribe(RestartStarted, self._on_started),
            bus.subscribe(RestartOutput, self._on_output),
            bus.subscribe(RestartCompleted, self._on_done),
        ]

    def on_unmount(self) -> None:
        for u in self._unsubs:
            u()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "go":
            self.run_worker(self._ctx.bus.send(RestartServer()), exclusive=False)
        else:
            self.dismiss()

    async def _on_started(self, _event: RestartStarted) -> None:
        self.query_one("#restart-log", Log).write_line("restart started")

    async def _on_output(self, event: RestartOutput) -> None:
        self.query_one("#restart-log", Log).write_line(event.line)

    async def _on_done(self, event: RestartCompleted) -> None:
        self.query_one("#restart-log", Log).write_line(f"exit {event.exit_code}")

    def action_cancel(self) -> None:
        self.dismiss()
