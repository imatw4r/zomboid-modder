# zomboid-modder

Terminal UI for managing Project Zomboid dedicated server mods and settings.

## What it does

Textual-based TUI to administer a remote (or local) Project Zomboid dedicated server without editing INI files by hand. Wraps mod installation, sandbox tuning, and server restart flows behind a keyboard-driven interface.

## Features

- Browse and toggle installed Workshop mods
- Edit server INI settings and Sandbox vars with validation
- Manage multiple server profiles (dev, prod, testing)
- Trigger `steamcmd` mod downloads
- SSH into remote hosts for file sync and server restart
- Save/load config snapshots

## Requirements

- Python >= 3.11
- [uv](https://github.com/astral-sh/uv)
- `steamcmd` on host running the server
- SSH access to remote server (if not local)

## Install

```
uv sync
```

## Run

```
make run
```

Or directly:

```
uv run zomboid-modder
```

Flags:

- `--profile NAME` - load profile on startup
- `--config PATH` - override default config.toml path

## Project layout

- `domain/` - mod list, sandbox, INI models
- `application/` - command/event handlers (mods, profiles, sandbox, save, restart)
- `infrastructure/` - config loader, steamcmd, remote sources
- `ui/tui/` - Textual screens and widgets
- `core/` - command bus, events

## License

MIT
