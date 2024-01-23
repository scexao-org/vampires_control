from time import sleep

import click
from rich.live import Live
from rich.rule import Rule
from rich.table import Table
from rich.text import Text
from swmain.redis import get_values


class Palette:
    red = "#721817"
    gold = "#FA9F42"
    orange = "#e85d04"
    blue = "#2B4162"
    green = "#0B6E4F"
    white = "#E0E0E2"
    gray = "#A3A3A3"


default_style = f"{Palette.white} on default"
unknown_style = f"{Palette.white} on {Palette.blue}"
active_style = f"{Palette.white} on {Palette.green}"
danger_style = f"{Palette.white} on {Palette.red}"
inactive_style = f"{Palette.gray} on #111111"

REDIS_KEYS = ["DATA", "EXPO", "FRATE", "LGSTP", "TEMP", "TRIG"]

REDIS_CAM_KEYS = {"VCAM1": "u_V", "VCAM2": "u_W"}


def get_table():
    title = Rule(Text("SCExAO Cam Status", style="italic"), style=f"bold {Palette.gold}")
    table = Table(title=title, style=f"bold {Palette.gold}")

    table.add_column("Name")
    table.add_column("Logging")
    table.add_column("Status")

    status_dict = {}
    for cam, pre in REDIS_CAM_KEYS.items():
        keys = []
        for key in REDIS_KEYS:
            keys.append(pre + key)
        status_dict[cam] = get_values(keys)

    for cam, results in status_dict.items():
        pre = REDIS_CAM_KEYS[cam]
        logging = results[pre + "LGSTP"] != -1
        details = ", ".join(
            [
                f"texp={results[pre + 'EXPO']:9.7f} s",
                f"f={results[pre + 'FRATE']:6.1f} Hz",
                f"T={results[pre + 'TEMP']:5.1f} K",
                f"trig={'on' if results[pre + 'TRIG'] else 'off'}",
            ]
        )
        table.add_row(
            cam,
            Text("logging" if logging else "", style=active_style if logging else default_style),
            details,
        )

    return table


@click.command("cam_status")
@click.option("-p", "--poll", default=0.2, type=float, help="Polling time, in seconds")
@click.option("-r", "--refresh", default=5, type=float, help="Refresh rate, in Hz")
def main(poll: float, refresh: float):
    min_poll = 1 / refresh
    if poll < min_poll:
        poll = min_poll
        click.echo(
            f"Increasing poll time ({poll:.01f} s -> {min_poll:.01f} s) to match refresh rate ({refresh} Hz)"
        )
    with Live(get_table(), refresh_per_second=refresh) as live:
        while True:
            sleep(poll)
            live.update(get_table())


if __name__ == "__main__":
    main()
