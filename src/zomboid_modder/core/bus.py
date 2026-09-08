from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

log = logging.getLogger(__name__)

CommandHandler = Callable[[Any], Awaitable[None]]
EventListener = Callable[[Any], Awaitable[None]]
Unsubscribe = Callable[[], None]


class MessageBus:
    def __init__(self) -> None:
        self._handlers: dict[type, CommandHandler] = {}
        self._listeners: dict[type, list[EventListener]] = {}

    def register(self, cmd_type: type, handler: CommandHandler) -> None:
        if cmd_type in self._handlers:
            raise RuntimeError(f"Handler already registered for {cmd_type.__name__}")
        self._handlers[cmd_type] = handler

    def subscribe(self, event_type: type, listener: EventListener) -> Unsubscribe:
        self._listeners.setdefault(event_type, []).append(listener)

        def _unsub() -> None:
            listeners = self._listeners.get(event_type, [])
            if listener in listeners:
                listeners.remove(listener)

        return _unsub

    async def send(self, command: Any) -> None:
        handler = self._handlers.get(type(command))
        if handler is None:
            raise RuntimeError(f"No handler registered for {type(command).__name__}")
        await handler(command)

    async def publish(self, event: Any) -> None:
        for listener in list(self._listeners.get(type(event), [])):
            try:
                await listener(event)
            except Exception:
                log.exception("Event listener failed for %s", type(event).__name__)
