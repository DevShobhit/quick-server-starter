from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path

from app.config import (
    add_server,
    get_server,
    update_server,
    ServerConfig,
)
from app.server import manager

router = APIRouter()

WEB_DIR = Path(__file__).parent / "web"


@router.get("/")
async def index():
    return FileResponse(WEB_DIR / "index.html")


@router.get("/api/servers")
async def list_servers():
    return manager.list_servers()


@router.post("/api/servers")
async def create_server(server: ServerConfig):
    try:
        # Write directly to configured file
        add_server(server) 
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return manager._status(server)


@router.get("/api/servers/{server_name}")
async def get_server_endpoint(server_name: str):
    status = manager._status(get_server(server_name)) if get_server(server_name) else None
    if not status:
        raise HTTPException(status_code=404, detail="Server not found")
    return status


@router.put("/api/servers/{server_name}")
async def update_server_endpoint(server_name: str, server: ServerConfig):
    if server.server_name != server_name:
        raise HTTPException(status_code=400, detail="server_name mismatch")
    if not get_server(server_name):
        raise HTTPException(status_code=404, detail="Server not found")
    update_server(server_name, server)
    return manager._status(server)


@router.delete("/api/servers/{server_name}")
async def delete_server_endpoint(server_name: str):
    if not get_server(server_name):
        raise HTTPException(status_code=404, detail="Server not found")
    manager.delete(server_name)
    return {"detail": "deleted"}


@router.post("/api/servers/{server_name}/start")
async def start_server(server_name: str):
    if not get_server(server_name):
        raise HTTPException(status_code=404, detail="Server not found")
    return manager.start(server_name)


@router.post("/api/servers/{server_name}/stop")
async def stop_server(server_name: str):
    if not get_server(server_name):
        raise HTTPException(status_code=404, detail="Server not found")
    return manager.stop(server_name)
