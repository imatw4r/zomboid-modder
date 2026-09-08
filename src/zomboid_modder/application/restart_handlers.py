from __future__ import annotations

import shlex

from zomboid_modder.core.bus import MessageBus
from zomboid_modder.core.commands import RestartServer
from zomboid_modder.core.events import ErrorOccurred, RestartCompleted, RestartOutput, RestartStarted
from zomboid_modder.infrastructure.sources.base import ConfigSource


class RestartServerHandler:
    def __init__(self, bus: MessageBus, source: ConfigSource, restart_cmd: str) -> None:
        self._bus = bus
        self._source = source
        self._restart_cmd = restart_cmd

    async def __call__(self, cmd: RestartServer) -> None:
        if not self._restart_cmd.strip():
            await self._bus.publish(ErrorOccurred("RestartServer", "no restart_cmd configured for profile"))
            return
        await self._bus.publish(RestartStarted())
        try:
            parts = shlex.split(self._restart_cmd)
            rc, stdout, stderr = await self._source.run(parts)
            for line in stdout.splitlines():
                await self._bus.publish(RestartOutput(line))
            for line in stderr.splitlines():
                await self._bus.publish(RestartOutput(f"[err] {line}"))
            await self._bus.publish(RestartCompleted(rc))
        except Exception as e:
            await self._bus.publish(ErrorOccurred("RestartServer", str(e)))
            await self._bus.publish(RestartCompleted(-1))
