from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import json
import os

CONFIG_PATH = Path(os.environ.get("SERVERS_CONFIG", "servers.json"))


class ServerConfig(BaseModel):
    server_name: str
    start_command: str
    server_path: str


class ServerStatus(BaseModel):
    server_name: str
    start_command: str
    server_path: str
    running: bool = False
    pid: Optional[int] = None
    port: Optional[str] = None


def _load_raw():
    if not CONFIG_PATH.exists():
        return []
    text = CONFIG_PATH.read_text().strip()
    if not text:
        return []
    if CONFIG_PATH.suffix.lower() in (".yaml", ".yml"):
        import yaml
        return yaml.safe_load(text) or []
    return json.loads(text)


def _save_raw(data):
    if CONFIG_PATH.suffix.lower() in (".yaml", ".yml"):
        import yaml
        CONFIG_PATH.write_text(yaml.safe_dump(data, sort_keys=False))
    else:
        CONFIG_PATH.write_text(json.dumps(data, indent=2))


def load_config() -> list[ServerConfig]:
    raw = _load_raw()
    return [ServerConfig(**item) for item in raw]


def save_config(servers: list[ServerConfig]):
    _save_raw([s.model_dump() for s in servers])


def add_server(server: ServerConfig):
    servers = load_config()
    if any(s.server_name == server.server_name for s in servers):
        raise ValueError(f"Server '{server.server_name}' already exists")
    servers.append(server)
    save_config(servers)


def get_server(server_name: str) -> ServerConfig | None:
    for s in load_config():
        if s.server_name == server_name:
            return s
    return None


def update_server(server_name: str, server: ServerConfig):
    servers = load_config()
    for i, s in enumerate(servers):
        if s.server_name == server_name:
            servers[i] = server
            save_config(servers)
            return
    raise ValueError(f"Server '{server_name}' not found")


def delete_server(server_name: str):
    servers = load_config()
    servers = [s for s in servers if s.server_name != server_name]
    save_config(servers)
