from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Protocol, runtime_checkable

from zomboid_modder.core.bus import MessageBus
from zomboid_modder.core.commands import Command


@runtime_checkable
class CommandHandler(Protocol):
    async def __call__(self, command: Command) -> None: ...


def register(bus: MessageBus, cmd_type: type, handler: Callable[[Command], Awaitable[None]]) -> None:
    bus.register(cmd_type, handler)
