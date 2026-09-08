from __future__ import annotations

import re
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING

import httpx

from zomboid_modder.domain.mod import Mod

if TYPE_CHECKING:
    from zomboid_modder.infrastructure.sources.base import ConfigSource

PZ_APP_ID = "108600"
WORKSHOP_URL = "https://steamcommunity.com/sharedfiles/filedetails/?id={id}"

MOD_ID_RE = re.compile(r"Mod\s*ID\s*:\s*([A-Za-z0-9_.\-]+)", re.IGNORECASE)
NAME_RE = re.compile(r"<title>Steam Workshop::\s*(.+?)</title>", re.IGNORECASE | re.DOTALL)


class ResolutionError(Exception):
    pass


class SteamCmd:
    def __init__(
        self,
        source: ConfigSource,
        steamcmd_path: str = "steamcmd",
        steamcmd_dir: str = "~/Steam",
    ) -> None:
        self._source = source
        self._path = steamcmd_path
        self._dir = steamcmd_dir

    async def download(self, workshop_id: str) -> AsyncIterator[str]:
        yield f"downloading workshop item {workshop_id} via steamcmd (dir={self._dir})"
        rc, stdout, stderr = await self._source.run(
            [
                "sh", "-lc",
                f"mkdir -p {self._dir} && cd {self._dir} && "
                f"{self._path} +login anonymous "
                f"+workshop_download_item {PZ_APP_ID} {workshop_id} +quit",
            ]
        )
        if rc != 0:
            yield f"steamcmd exit {rc}: {stderr[:200] or stdout[-200:]}"
            return
        yield "steamcmd finished; reading mod.info"

    async def resolve(self, workshop_id: str) -> Mod:
        try:
            mod = await self._resolve_from_steamcmd(workshop_id)
            if mod is not None:
                return mod
        except Exception:
            pass
        mod = await self._resolve_from_web(workshop_id)
        if mod is None:
            raise ResolutionError(f"could not resolve workshop id {workshop_id}")
        return mod

    async def _resolve_from_steamcmd(self, workshop_id: str) -> Mod | None:
        base = f"{self._dir}/steamapps/workshop/content/{PZ_APP_ID}/{workshop_id}/mods"
        rc, stdout, _ = await self._source.run(
            ["sh", "-lc", f"ls {base} 2>/dev/null"]
        )  # base contains ~; unquoted so sh expands
        if rc != 0 or not stdout.strip():
            return None
        for entry in stdout.split():
            info_path = f"{base}/{entry}/mod.info"
            rc2, text, _ = await self._source.run(
                ["sh", "-lc", f"cat {info_path} 2>/dev/null"]
            )
            if rc2 != 0 or not text:
                continue
            mod_id = None
            name = None
            for line in text.splitlines():
                if line.startswith("id="):
                    mod_id = line.split("=", 1)[1].strip()
                elif line.startswith("name="):
                    name = line.split("=", 1)[1].strip()
            if mod_id:
                return Mod(id=mod_id, workshop_id=workshop_id, name=name)
        return None

    async def _resolve_from_web(self, workshop_id: str) -> Mod | None:
        url = WORKSHOP_URL.format(id=workshop_id)
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url)
        if resp.status_code != 200:
            return None
        body = resp.text
        m = MOD_ID_RE.search(body)
        if not m:
            return None
        mod_id = m.group(1)
        name_match = NAME_RE.search(body)
        name = name_match.group(1).strip() if name_match else None
        return Mod(id=mod_id, workshop_id=workshop_id, name=name)


def parse_workshop_input(text: str) -> str:
    text = text.strip()
    m = re.search(r"[?&]id=(\d+)", text)
    if m:
        return m.group(1)
    if text.isdigit():
        return text
    raise ValueError(f"could not extract workshop id from: {text}")
