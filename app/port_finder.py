import psutil
from typing import Optional


class PortFinder:
    """Finds listening TCP ports by walking a process hierarchy."""

    def __init__(self, pid: int):
        self.pid = pid
        self.processes: list[psutil.Process] = []

    def build_hierarchy(self) -> bool:
        """Collect the parent process and all descendant processes."""
        try:
            parent = psutil.Process(self.pid)
        except psutil.NoSuchProcess:
            return False

        self.processes = [parent]
        try:
            self.processes.extend(parent.children(recursive=True))
        except psutil.NoSuchProcess:
            pass
        return len(self.processes) > 0

    def find_listening_port(self) -> Optional[str]:
        """Return the first listening port found across the hierarchy."""
        for proc in self.processes:
            try:
                for conn in proc.connections(kind="inet"):
                    if conn.status == psutil.CONN_LISTEN:
                        return str(conn.laddr.port)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return None

    def detect_port(self) -> Optional[str]:
        """Build hierarchy and find listening port in one call."""
        if not self.build_hierarchy():
            return None
        return self.find_listening_port()
