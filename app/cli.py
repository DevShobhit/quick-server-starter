import typer
from app.config import load_config, save_config, add_server, get_server, update_server, delete_server, ServerConfig
from app.server import manager

app = typer.Typer(help="Manage server scripts")


@app.command()
def list():
    """List all configured servers and their status."""
    for s in manager.list_servers():
        typer.echo(
            f"{s['server_name']}: running={s['running']} pid={s['pid']} port={s['port']} "
            f"cmd='{s['start_command']}' path='{s['server_path']}'"
        )


@app.command()
def add(
    server_name: str,
    start_command: str,
    server_path: str,
):
    """Add a new server config."""
    try:
        add_server(ServerConfig(server_name=server_name, start_command=start_command, server_path=server_path))
        typer.echo(f"Added server '{server_name}'")
    except ValueError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1)


@app.command()
def start(server_name: str):
    """Start a server."""
    if not get_server(server_name):
        typer.echo(f"Server '{server_name}' not found", err=True)
        raise typer.Exit(1)
    status = manager.start(server_name)
    typer.echo(f"Started '{server_name}' pid={status['pid']} port={status['port']}")


@app.command()
def stop(server_name: str):
    """Stop a server."""
    if not get_server(server_name):
        typer.echo(f"Server '{server_name}' not found", err=True)
        raise typer.Exit(1)
    manager.stop(server_name)
    typer.echo(f"Stopped '{server_name}'")


@app.command()
def status(server_name: str):
    """Show status of a server."""
    cfg = get_server(server_name)
    if not cfg:
        typer.echo(f"Server '{server_name}' not found", err=True)
        raise typer.Exit(1)
    s = manager._status(cfg)
    typer.echo(
        f"{s['server_name']}: running={s['running']} pid={s['pid']} port={s['port']}"
    )


@app.command()
def remove(server_name: str):
    """Remove a server config."""
    if not get_server(server_name):
        typer.echo(f"Server '{server_name}' not found", err=True)
        raise typer.Exit(1)
    manager.delete(server_name)
    typer.echo(f"Removed '{server_name}'")


@app.command()
def update(
    server_name: str,
    start_command: str,
    server_path: str,
):
    """Update a server config."""
    if not get_server(server_name):
        typer.echo(f"Server '{server_name}' not found", err=True)
        raise typer.Exit(1)
    update_server(server_name, ServerConfig(server_name=server_name, start_command=start_command, server_path=server_path))
    typer.echo(f"Updated '{server_name}'")


if __name__ == "__main__":
    app()
