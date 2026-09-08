from __future__ import annotations

import asyncio
import os
from pathlib import Path


class LocalSource:
    def __init__(self, root: str) -> None:
        self._root = Path(os.path.expanduser(root)).resolve()

    def _abs(self, relpath: str) -> Path:
        return (self._root / relpath).resolve()

    async def read_text(self, relpath: str) -> str:
        return await asyncio.to_thread(self._abs(relpath).read_text, encoding="utf-8")

    async def write_text(self, relpath: str, content: str) -> None:
        path = self._abs(relpath)
        await asyncio.to_thread(path.parent.mkdir, parents=True, exist_ok=True)
        await asyncio.to_thread(path.write_text, content, encoding="utf-8")

    async def list_dir(self, relpath: str) -> list[str]:
        path = self._abs(relpath)
        return await asyncio.to_thread(lambda: [p.name for p in path.iterdir()])

    async def exists(self, relpath: str) -> bool:
        return await asyncio.to_thread(self._abs(relpath).exists)

    async def run(self, cmd: list[str]) -> tuple[int, str, str]:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        return proc.returncode or 0, stdout.decode("utf-8", "replace"), stderr.decode("utf-8", "replace")

    async def close(self) -> None:
        return None
