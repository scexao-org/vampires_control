from swmain.infra.tmux import find_or_create, kill_running, send_keys
from vampires_control import conf_dir
import click
from pathlib import Path

@click.option("-c", "--config", default=conf_dir / "daemons" / "vampires_mprocs.yml", type=click.Path(exists=True, readable=True, path_type=Path))
@click.option("-p", "--port", default="127.0.0.1:8792")
@click.command("launch_daemons")
def main(port, config):
    # Device control daemon
    print(f"Initializing mprocs server from {config}")
    name = "daemons"
    session = find_or_create(name)
    kill_running(session)
    command = f"mrpocs --server {port} --config {config.absolute()}"
    # print(command)
    send_keys(session, command)
    print(f"mprocs server launching in tmux session `{name}`.")


if __name__ == "__main__":
    main()
