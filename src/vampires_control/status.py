from time import sleep

import click
import numpy as np
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


def get_table():
    title = Rule(Text("VAMPIRES status", style="italic"), style=f"bold {Palette.gold}")
    caption = Text.assemble(
        "",
        (" ACTIVE ", active_style),
        (" | ", f"bold {Palette.gold}"),
        (" UNKNOWN ", unknown_style),
        (" | ", f"bold {Palette.gold}"),
        (" WARNING ", danger_style),
        " ",
    )
    table = Table(title=title, style=f"bold {Palette.gold}", caption=caption)

    table.add_column("Name")
    table.add_column("Status")
    table.add_column("Position")

    status_dict = get_values(
        [
            "D_IMRANG",
            "D_IMRMOD",
            "P_RTAGL1",
            "P_STGPS1",
            "P_STGPS2",
            "U_BS",
            "U_BSTH",
            "U_CAMFCF",
            "U_CAMFCS",
            "U_DIFFL1",
            "U_DIFFL2",
            "U_DIFFTH",
            "U_FCS",
            "U_FCSF",
            "U_FILTER",
            "U_FILTTH",
            "U_FLCEN",
            "U_FLCOFF",
            "U_FLCST",
            "U_FLCSTP",
            "U_FLCTMP",
            "U_FLDSTP",
            "U_FLDSTX",
            "U_FLDSTY",
            "U_MASK",
            "U_MASKTH",
            "U_MASKX",
            "U_MASKY",
            "U_MBI",
            "U_MBITH",
            "U_PUPST",
            "U_QWP1",
            "U_QWP1TH",
            "U_QWP2",
            "U_QWP2TH",
            "U_QWPMOD",
            "U_TRIGDL",
            "U_TRIGEN",
            "U_TRIGPW",
            "U_VLOG1",
            "U_VLOG2",
            "U_VLOGP",
            "X_FIRPKO",
            "X_FIRPKP",
            "X_NPS11",
            "X_NPS14",
            "X_POLAR",
            "X_POLARP",
        ]
    )
    ## AO188 LP
    if status_dict["P_STGPS1"] == 0:
        status = "OUT"
        style = default_style
    elif status_dict["P_STGPS1"] == 55.2:
        status = "WireGrid(TIR)"
        style = active_style
    elif status_dict["P_STGPS1"] == 90:
        status = "WireGrid(NIR)"
        style = active_style
    else:
        status = "UNKNOWN"
        unknown_style

    table.add_row("LP", status, "", style=style)

    ## HWP
    style = default_style
    if status_dict["P_STGPS2"] == 56:
        status = "IN"
        style = active_style
    elif status_dict["P_STGPS2"] == 0:
        status = "OUT"
    else:
        status = "UNKNOWN"
        style = unknown_style
    table.add_row("HWP", status, f"θ={status_dict['P_RTAGL1']:6.02f} deg", style=style)

    ## Image rotator
    table.add_row(
        "Image rotator",
        status_dict["D_IMRMOD"],
        f"θ={status_dict['D_IMRANG']:6.02f} deg",
        style=default_style,
    )

    ## AO188 -> SCExAO
    table.add_section()

    ## LP
    if status_dict["X_POLAR"].strip() == "OUT":
        style = default_style
    elif status_dict["X_POLAR"].strip() == "IN":
        style = active_style
    table.add_row(
        "LP",
        status_dict["X_POLAR"],
        f"θ={status_dict['X_POLARP']:6.02f} deg",
        style=style,
    )
    ## QWP
    style = active_style if status_dict["U_QWPMOD"] != "NONE" else default_style
    table.add_row("QWP mode", status_dict["U_QWPMOD"], "", style=style)
    table.add_row(
        "QWP 1",
        f"θ={status_dict['U_QWP1']:6.02f} deg",
        f"θ={status_dict['U_QWP1TH']:6.02f} deg",
        style=default_style,
    )
    table.add_row(
        "QWP 2",
        f"θ={status_dict['U_QWP2']:6.02f} deg",
        f"θ={status_dict['U_QWP2TH']:6.02f} deg",
        style=default_style,
    )

    ## SCExAO -> Vis
    table.add_section()

    ## Fieldstop
    if "open" in status_dict["U_FLDSTP"].lower():
        style = active_style
    elif status_dict["U_FLDSTP"].lower() == "unknown":
        style = unknown_style
    else:
        style = default_style
    table.add_row(
        "Fieldstop",
        str(status_dict["U_FLDSTP"]),
        f"x={status_dict['U_FLDSTX']:6.03f} mm, y={status_dict['U_FLDSTY']:6.03f} mm",
        style=default_style,
    )

    ## First pickoff
    if status_dict["X_FIRPKO"].strip() == "IN":
        style = active_style
    elif status_dict["X_FIRPKO"].strip() == "OUT":
        style = default_style
    else:
        style = unknown_style
    table.add_row(
        "FIRST pickoff",
        status_dict["X_FIRPKO"],
        f"p={status_dict['X_FIRPKP']:5.02f} mm",
        style=style,
    )

    ## FLC
    if np.abs(status_dict["U_FLCTMP"] - 45) > 1:
        style = danger_style
    elif status_dict["U_FLCEN"] == "True":
        style = active_style
    else:
        style = default_style
    temp_text = Text(
        f"T(AFLC)={status_dict['U_FLCTMP']:4.01f} °C",
        style=style,
    )
    status = "ENABLED" if status_dict["U_FLCEN"] == "True" else "DISABLED"
    table.add_row("AFLC", status, temp_text, style=style)
    if status_dict["U_FLCST"].strip() == "IN":
        style = active_style
    elif status_dict["U_FLCST"].strip() == "OUT":
        style = default_style
    else:
        style = unknown_style
    table.add_row(
        "AFLC Stage",
        str(status_dict["U_FLCST"]),
        f"p={status_dict['U_FLCSTP']:5.02f} mm",
        style=style,
    )
    ## Pupil mask
    if status_dict["U_MASK"].strip() == "Open":
        style = default_style
    elif status_dict["U_MASK"].strip() == "Unknown":
        style = unknown_style
    else:
        style = active_style
    table.add_row(
        "Mask wheel",
        str(status_dict["U_MASK"]),
        f"θ={status_dict['U_MASKTH']:6.02f} deg, x={status_dict['U_MASKX']:6.03f} mm, y={status_dict['U_MASKY']:6.03f} mm",
        style=style,
    )

    ## filter
    table.add_row(
        "Filter",
        str(status_dict["U_FILTER"]),
        f"{status_dict['U_FILTTH']:.0f}",
        style=default_style,
    )

    ## MBI
    if status_dict["U_MBI"] == "IN":
        style = active_style
    elif status_dict["U_MBI"] == "OUT":
        style = default_style
    else:
        style = unknown_style
    table.add_row(
        "MBI",
        str(status_dict["U_MBI"]),
        f"θ={status_dict['U_MBITH']:6.02f} deg",
        style=style,
    )

    ## Pupil lens
    if status_dict["U_PUPST"].strip() == "OUT":
        style = default_style
    elif status_dict["U_PUPST"].strip() == "IN":
        style = active_style
    else:
        style = unknown_style
    table.add_row("Pupil lens", status_dict["U_PUPST"], "", style=style)

    ## Focusing lens
    style = default_style
    if status_dict["U_FCS"].lower() == "unknown":
        style = unknown_style
    table.add_row(
        "Focus",
        str(status_dict["U_FCS"]),
        f"f={status_dict['U_FCSF']:5.02f} mm",
        style=style,
    )

    ## Beamsplitter
    if status_dict["U_BS"].lower() == "open":
        style = active_style
    elif status_dict["U_BS"].lower() == "unknown":
        style = unknown_style
    else:
        style = default_style
    table.add_row(
        "Beamsplitter",
        str(status_dict["U_BS"]),
        f"θ={status_dict['U_BSTH']:6.02f} deg",
        style=style,
    )

    ## Differential filter wheel
    style = default_style
    if (
        status_dict["U_DIFFL1"].lower() == "unknown"
        or status_dict["U_DIFFL2"].lower() == "unknown"
    ):
        style = unknown_style
    elif "Ha" in status_dict["U_DIFFL1"] or "Ha" in status_dict["U_DIFFL2"]:
        style = active_style
    elif "SII" in status_dict["U_DIFFL1"] or "SII" in status_dict["U_DIFFL2"]:
        style = active_style
    table.add_row(
        "Diff. wheel",
        f"{str(status_dict['U_DIFFL1'])} / {str(status_dict['U_DIFFL2'])}",
        f"θ={status_dict['U_DIFFTH']:6.02f} deg",
        style=style,
    )

    ## Camera focus
    style = default_style
    table.add_row(
        "Cam focus",
        str(status_dict["U_CAMFCS"]),
        f"f={status_dict['U_CAMFCF']:5.02f} mm",
        style=style,
    )

    ## Trigger
    if status_dict["U_TRIGEN"] == "True":
        style = default_style
    else:
        style = danger_style
    table.add_row(
        "Trigger",
        "ENABLED" if status_dict["U_TRIGEN"] == "True" else "DISABLED",
        f"dl={status_dict['U_TRIGDL']:3d} us, pw={status_dict['U_TRIGPW']:3d} us, off={status_dict['U_FLCOFF']:3d} us",
        style=style,
    )

    table.add_section()
    logging_cam1 = status_dict["U_VLOG1"].strip() == "ON"
    logging_cam2 = status_dict["U_VLOG2"].strip() == "ON"
    logging_pupil = status_dict["U_VLOGP"].strip() == "ON"
    styles = {
        "OFF": default_style,
        "ON": active_style,
    }
    power_style = {"ON": default_style, "OFF": danger_style}
    power_status = Text(
        f"Power: {status_dict['X_NPS11']}", style=power_style[status_dict["X_NPS11"]]
    )
    table.add_row(
        "CAM 1",
        "Logging" if logging_cam1 else "",
        power_status,
        style=styles[status_dict["U_VLOG1"]],
    )
    power_status = Text(
        f"Power: {status_dict['X_NPS14']}", style=power_style[status_dict["X_NPS14"]]
    )
    table.add_row(
        "CAM 2",
        "Logging" if logging_cam2 else "",
        power_status,
        style=styles[status_dict["U_VLOG2"]],
    )
    table.add_row(
        "Pupil Cam",
        "Logging" if logging_pupil else "",
        "",
        style=styles[status_dict["U_VLOGP"]],
    )

    return table


@click.command("vampires_status")
@click.option("-p", "--poll", default=1, type=float, help="Polling time, in seconds")
@click.option("-r", "--refresh", default=1, type=float, help="Refresh rate, in Hz")
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
