from __future__ import annotations

import os
import tomllib
from pathlib import Path
from typing import Literal

import tomli_w
from pydantic import BaseModel, Field


class LocalProfile(BaseModel):
    name: str
    type: Literal["local"] = "local"
    server_dir: str
    server_name: str = "servertest"
    restart_cmd: str = ""
    steamcmd_path: str = "steamcmd"
    steamcmd_dir: str = "~/Steam"


class SshProfile(BaseModel):
    name: str
    type: Literal["ssh"] = "ssh"
    host: str
    port: int = 22
    user: str
    key: str | None = None
    password: str | None = None
    server_dir: str
    server_name: str = "servertest"
    restart_cmd: str = ""
    steamcmd_path: str = "steamcmd"
    steamcmd_dir: str = "~/Steam"


Profile = LocalProfile | SshProfile


class Config(BaseModel):
    default_profile: str | None = None
    profile: list[Profile] = Field(default_factory=list)

    def get(self, name: str) -> Profile | None:
        for p in self.profile:
            if p.name == name:
                return p
        return None


def default_config_path() -> Path:
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / "zomboid-modder" / "config.toml"


def load_config(path: Path | None = None) -> Config:
    path = path or default_config_path()
    if not path.exists():
        return Config()
    with path.open("rb") as f:
        raw = tomllib.load(f)
    return Config.model_validate(raw)


def save_config(config: Config, path: Path | None = None) -> None:
    path = path or default_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    data = config.model_dump(exclude_none=True)
    with path.open("wb") as f:
        tomli_w.dump(data, f)
