import os
import signal
import subprocess
import json
from pathlib import Path

from app.config import ServerConfig, get_server
from app.port_finder import PortFinder

STATE_PATH = Path(".servers_state.json")


def _load_state():
    if not STATE_PATH.exists():
        return {}
    try:
        return json.loads(STATE_PATH.read_text())
    except Exception:
        return {}


def _save_state(state):
    STATE_PATH.write_text(json.dumps(state, indent=2))


def _is_alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except Exception:
        return False


class ServerManager:
    def __init__(self):
        self._processes: dict[str, dict] = {}

    def list_servers(self):
        from app.config import load_config
        return [self.status(cfg) for cfg in load_config()]

    def status(self, cfg: ServerConfig) -> dict:
        info = self._processes.get(cfg.server_name)
        pid = info["proc"].pid if info else _load_state().get(cfg.server_name)
        running = pid is not None and _is_alive(pid)

        if info and info["proc"].poll() is not None:
            running = False

        if not running:
            self._processes.pop(cfg.server_name, None)
            state = _load_state()
            state.pop(cfg.server_name, None)
            _save_state(state)
            return {
                "server_name": cfg.server_name,
                "start_command": cfg.start_command,
                "server_path": cfg.server_path,
                "running": False,
                "pid": None,
                "port": None,
            }

        port = PortFinder(pid).detect_port()
        return {
            "server_name": cfg.server_name,
            "start_command": cfg.start_command,
            "server_path": cfg.server_path,
            "running": True,
            "pid": pid,
            "port": port,
        }

    def start(self, server_name: str) -> dict:
        cfg = get_server(server_name)
        if not cfg:
            raise ValueError(f"Server '{server_name}' not found")

        proc = self._processes.get(server_name, {}).get("proc")
        if proc and proc.poll() is None:
            return self.status(cfg)
        self._processes.pop(server_name, None)

        log_dir = None
        if os.environ.get("PERSIST_LOGS"):
            log_dir = Path("logs") / server_name
            log_dir.mkdir(parents=True, exist_ok=True)
            stdout = open(log_dir / f"{server_name}.log", "ab")
            stderr = stdout
        else:
            stdout = subprocess.DEVNULL
            stderr = subprocess.DEVNULL

        cmd = f"cd {cfg.server_path} && exec {cfg.start_command}"
        proc = subprocess.Popen(
            ["bash", "-c", cmd],
            stdout=stdout,
            stderr=stderr,
            start_new_session=True,
        )
        self._processes[server_name] = {"proc": proc, "log_file": stdout if log_dir else None}

        state = _load_state()
        state[server_name] = proc.pid
        _save_state(state)
        return self.status(cfg)

    def stop(self, server_name: str) -> dict:
        cfg = get_server(server_name)
        if not cfg:
            raise ValueError(f"Server '{server_name}' not found")

        info = self._processes.pop(server_name, None)
        proc = info["proc"] if info else None
        log_file = info.get("log_file") if info else None

        state = _load_state()
        pid = state.get(server_name)
        if proc:
            pid = proc.pid

        if pid:
            try:
                os.killpg(os.getpgid(pid), signal.SIGTERM)
                if proc:
                    proc.wait(timeout=5)
                else:
                    import time

                    time.sleep(0.6)
            except ProcessLookupError:
                pass
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(os.getpgid(pid), signal.SIGKILL)
                except ProcessLookupError:
                    pass
                if proc:
                    proc.wait(timeout=5)

        if log_file and not log_file.closed:
            log_file.close()
        state.pop(server_name, None)
        _save_state(state)
        return self.status(cfg)

    def delete(self, server_name: str):
        self.stop(server_name)
        from app.config import delete_server

        delete_server(server_name)


manager = ServerManager()
