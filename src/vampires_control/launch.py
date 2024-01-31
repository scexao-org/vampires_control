from pathlib import Path

import click
from swmain.infra.tmux import find_or_create, kill_running, send_keys

from vampires_control import conf_dir


@click.option(
    "-c",
    "--config",
    default=conf_dir / "daemons" / "vampires_mprocs.yml",
    type=click.Path(exists=True, readable=True, path_type=Path),
)
@click.command("launch_daemons")
def main(config):
    # Device control daemon
    print(f"Initializing mprocs server from {config}")
    name = "daemons"
    session = find_or_create(name)
    kill_running(session)
    command = f"mprocs --config {config.absolute()}"
    # print(command)
    send_keys(session, command)
    print(f"mprocs server launching in tmux session `{name}`.")
    print("Use localhost:8702 to access remote server")


if __name__ == "__main__":
    main()
