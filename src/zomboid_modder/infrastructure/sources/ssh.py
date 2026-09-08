from __future__ import annotations

import asyncio
import logging
import os
import posixpath
import shlex
from typing import TYPE_CHECKING

import asyncssh

log = logging.getLogger(__name__)

if TYPE_CHECKING:
    from zomboid_modder.infrastructure.config import SshProfile


class SshSource:
    def __init__(self, profile: SshProfile) -> None:
        self._profile = profile
        self._root = profile.server_dir.rstrip("/")
        self._conn: asyncssh.SSHClientConnection | None = None
        self._sftp: asyncssh.SFTPClient | None = None

    def _abs(self, relpath: str) -> str:
        return posixpath.join(self._root, relpath)

    async def _connect(self) -> asyncssh.SSHClientConnection:
        if self._conn is not None:
            return self._conn
        kwargs: dict = {
            "host": self._profile.host,
            "port": self._profile.port,
            "username": self._profile.user,
            "known_hosts": None,
        }
        if self._profile.key:
            kwargs["client_keys"] = [os.path.expanduser(self._profile.key)]
        if self._profile.password:
            kwargs["password"] = self._profile.password
        log.info(
            "ssh connecting host=%s port=%s user=%s key=%s",
            kwargs["host"], kwargs["port"], kwargs["username"], kwargs.get("client_keys"),
        )
        self._conn = await asyncio.wait_for(asyncssh.connect(**kwargs), timeout=15)
        log.info("ssh connected")
        self._sftp = await self._conn.start_sftp_client()
        log.info("sftp started")
        return self._conn

    async def read_text(self, relpath: str) -> str:
        await self._connect()
        assert self._sftp is not None
        async with self._sftp.open(self._abs(relpath), "r") as f:
            return await f.read()

    async def write_text(self, relpath: str, content: str) -> None:
        await self._connect()
        assert self._sftp is not None
        path = self._abs(relpath)
        parent = posixpath.dirname(path)
        try:
            await self._sftp.makedirs(parent, exist_ok=True)
        except Exception:
            pass
        async with self._sftp.open(path, "w") as f:
            await f.write(content)

    async def list_dir(self, relpath: str) -> list[str]:
        await self._connect()
        assert self._sftp is not None
        return await self._sftp.listdir(self._abs(relpath))

    async def exists(self, relpath: str) -> bool:
        await self._connect()
        assert self._sftp is not None
        try:
            await self._sftp.stat(self._abs(relpath))
            return True
        except (OSError, asyncssh.SFTPError):
            return False

    async def run(self, cmd: list[str]) -> tuple[int, str, str]:
        conn = await self._connect()
        cmd_str = " ".join(shlex.quote(c) for c in cmd)
        result = await conn.run(cmd_str, check=False)
        return int(result.exit_status or 0), str(result.stdout or ""), str(result.stderr or "")

    async def close(self) -> None:
        if self._sftp is not None:
            self._sftp.exit()
            self._sftp = None
        if self._conn is not None:
            self._conn.close()
            await self._conn.wait_closed()
            self._conn = None
