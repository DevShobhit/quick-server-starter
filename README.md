# Quick Commands Starter

A FastAPI application for managing configured scripts as "servers." Configure scripts with a start command and folder path, then control them (CRUD, start, stop) from web UI or CLI. Server configs are stored in plain JSON (or YAML) — no database.

## Features

- **Web UI** — minimal interface listing servers with status, PID, and running port. Add/delete configs and start/stop servers.
- **CLI** — full parity with the web UI via Typer (`python -m app.cli ...`).
- **Config file** — `servers.json` (plain JSON; YAML supported via `SERVERS_CONFIG` env var). Fields: `server_name`, `start_command`, `server_path`.
- **Process management** — commands run in `bash` with `start_new_session`. Logs go to `/dev/null` by default; set `PERSIST_LOGS=1` to write logs to `logs/<server_name>/<server_name>.log`.
- **Status** — reports `running`, `pid`, and detected listening `port` for each server. Port detection uses **psutil** to walk the process hierarchy (no external `ss`/`lsof` tools required).

## Requirements

- Python 3.14+
- Virtual environment at `.venv` (managed with `uv`)

## Setup

```bash
# Activate the venv
source .venv/bin/activate

# Install dependencies
uv sync
```

## Run the API server

```bash
source .venv/bin/activate
python main.py
```

The web UI is served at `http://localhost:8000/`. The API is available under `/api/servers`.

## CLI usage

```bash
source .venv/bin/activate

# List all servers with status
python -m app.cli list

# Add a server config
python -m app.cli add my-api "python3 app.py" /path/to/my/project

# Start a server
python -m app.cli start my-api

# Check status (running, pid, port)
python -m app.cli status my-api

# Stop a server
python -m app.cli stop my-api

# Update a server config
python -m app.cli update my-api "python3 app.py --port 8080" /path/to/my/project

# Remove a server config (stops it first)
python -m app.cli remove my-api
```

## Configuration

Server configs live in `servers.json`:

```json
[
  {
    "server_name": "my-api",
    "start_command": "python3 app.py",
    "server_path": "/path/to/my/project"
  }
]
```

To use YAML instead, set the `SERVERS_CONFIG` env var to a `.yaml`/`.yml` path:

```bash
export SERVERS_CONFIG=servers.yaml
```

## Environment variables

| Variable | Description |
|---|---|
| `SERVERS_CONFIG` | Path to the config file (default `servers.json`; `.yaml`/`.yml` supported) |
| `PERSIST_LOGS` | If set, command logs are written to `logs/<server_name>/<server_name>.log` |

## Port detection

The running port of each server is detected by walking the process hierarchy with **psutil** (parent PID + all descendants via `children(recursive=True)`), checking each process's TCP connections for `LISTEN` state. This works even when the start command spawns child processes (e.g. `bash -c 'exec python3 app.py'`).

No external tools (`ss`, `lsof`, `netstat`) are required — port detection relies solely on the `psutil` Python package, which is listed in `pyproject.toml` and installed via `uv sync`.

## Project layout

```
app/
  config.py   # Load/save server configs (JSON or YAML)
  server.py   # Process manager (start/stop/status, PID + port detection)
  port_finder.py  # Process hierarchy walker + TCP port detection via psutil
  api.py      # FastAPI routes + web UI
  cli.py      # Typer CLI
  web/
    index.html  # Modern minimal web UI
main.py       # Uvicorn entry point
```

## Design rationale

- **Plain JSON/YAML config, no database** — Server configs are stored in `servers.json` (or `.yaml`/`.yml`) for easy manual editing and version control. No migration scripts or database server required.
- **`bash -c 'exec <command>'` with `start_new_session=True`** — Runs commands in their own process group so `stop` can kill the entire group (`SIGTERM` → `SIGKILL` fallback) without leaking orphaned children. `exec` replaces the shell so the tracked PID is the actual server process, not a lingering `bash` parent.
- **psutil for port detection** — `PortFinder` walks the process hierarchy (`parent.children(recursive=True)`) and inspects each process's TCP connections for `LISTEN` state. This avoids depending on external tools like `ss` or `lsof`, and correctly finds ports even when the server spawns child processes.
- **In-memory process state + persisted PID file** — Running processes are tracked in memory (`.servers_state.json` persists PIDs across CLI invocations), so `status` works whether the server was started via the web UI or CLI.
- **Logs off by default** — Command output goes to `/dev/null` unless `PERSIST_LOGS=1` is set, keeping stdout clean. When enabled, logs are written to `logs/<server_name>/<server_name>.log`.
- **CLI and web UI share the same backend** — Both use `ServerManager` and the same config file, so a server added via CLI appears in the web UI and vice versa.

Generated runtime files (`servers.json`, `.servers_state.json`, `logs/`, `__pycache__/`) are gitignored.
