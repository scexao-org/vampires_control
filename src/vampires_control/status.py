from rich.live import Live
from rich.table import Table
from rich.text import Text
from rich.rule import Rule
from time import sleep
from swmain.redis import get_values
import numpy as np
import click


class Palette:
    red = "#721817"
    gold = "#FA9F42"
    blue = "#2B4162"
    green = "#0B6E4F"
    white = "#E0E0E2"
    gray = "#A9A9A9"


default_style = f"{Palette.white} on default"
unknown_style = f"default on {Palette.gold}"
active_style = f"{Palette.white} on {Palette.green}"
blue_style = f"{Palette.white} on {Palette.blue}"
danger_style = f"{Palette.white} on {Palette.red}"
inactive_style = f"{Palette.gray} on default"


def get_table():
    title = Rule(Text("VAMPIRES status", style="italic"), style=f"bold {Palette.gold}")
    caption = Text.assemble(
        "",
        (" ACTIVE ", active_style),
        "/",
        (" ACTIVE ", blue_style),
        " | ",
        (" WARNING ", danger_style),
        " | ",
        (" UNKNOWN ", unknown_style),
        " | ",
        (" NOT READY ", inactive_style),
        "",
    )
    table = Table(title=title, style=f"bold {Palette.gold}", caption=caption)

    table.add_column("Name")
    table.add_column("Status")
    table.add_column("Position")

    status_dict = get_values(
        [
            "P_RTAGL1",
            "P_STGPS1",
            "P_STGPS2",
            "D_IMRMOD",
            "D_IMRANG",
            "X_POLAR",
            "X_POLARP",
            "U_QWPMOD",
            "U_QWP1",
            "U_QWP1TH",
            "U_QWP2",
            "U_QWP2TH",
            "U_FLDSTP",
            "U_FLDSTX",
            "U_FLDSTY",
            "X_FIRPKO",
            "X_FIRPKP",
            "U_BENTMP",
            "U_FLCEN",
            "U_FLCTMP",
            "U_FLCST",
            "U_FLCSTP",
            "U_MASK",
            "U_MASKTH",
            "U_MASKX",
            "U_MASKY",
            "U_FILTER",
            "U_FILTTH",
            "U_MBI",
            "U_MBITH",
            "U_PUPST",
            "U_FCS",
            "U_FCSF",
            "U_BS",
            "U_BSTH",
            "U_DIFFL1",
            "U_DIFFL2",
            "U_DIFFTH",
            "U_CAMFCS",
            "U_CAMFCF",
            "EXTTRIG",
            "U_TRIGPW",
            "U_FLCOFF",
            "U_VLOG1",
            "U_VLOG2",
            "U_VLOGP",
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
    table.add_row("HWP", status, f"θ={status_dict['P_RTAGL1']:.3f} deg", style=style)

    ## Image rotator
    table.add_row(
        "Image rotator",
        status_dict["D_IMRMOD"],
        f"θ={status_dict['D_IMRANG']:.3f} deg",
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
        f"θ={status_dict['X_POLARP']:.3f} deg",
        style=style,
    )
    ## QWP
    table.add_row("QWP mode", str(status_dict["U_QWPMOD"]), "", style=inactive_style)
    table.add_row(
        "QWP 1",
        f"θ={status_dict['U_QWP1']:.3f} deg",
        f"θ={status_dict['U_QWP1TH']:.3f} deg",
        style=default_style,
    )
    table.add_row(
        "QWP 2",
        f"θ={status_dict['U_QWP2']:.3f} deg",
        f"θ={status_dict['U_QWP2TH']:.3f} deg",
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
        f"x={status_dict['U_FLDSTX']:.3f} mm, y={status_dict['U_FLDSTY']:.3f} mm",
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
        f"p={status_dict['X_FIRPKP']:.3f} mm",
        style=style,
    )

    ## FLC
    if np.abs(status_dict["U_FLCTMP"] - 45) > 1:
        style = unknown_style
    elif status_dict["U_FLCEN"] == "ON":
        style = active_style
    else:
        style = default_style
    style = inactive_style  # override
    temp_text = Text(
        f"T(AFLC)={status_dict['U_FLCTMP']:.01f} °C | T(bench)={status_dict['U_BENTMP']:.01f} °C",
        style=style,
    )
    table.add_row("AFLC", str(status_dict["U_FLCEN"]), temp_text, style=style)
    if status_dict["U_FLCST"].strip() == "IN":
        style = active_style
    elif status_dict["U_FLCST"].strip() == "OUT":
        style = default_style
    else:
        style = unknown_style
    style = inactive_style  # override
    table.add_row(
        "AFLC Stage",
        str(status_dict["U_FLCST"]),
        f"p={status_dict['U_FLCSTP']:.3f} mm",
        style=style,
    )
    ## Pupil mask
    if status_dict["U_MASK"].lower() != "open":
        style = active_style
    elif status_dict["U_MASK"].lower() == "unknown":
        style = unknown_style
    else:
        style = default_style
    table.add_row(
        "Mask wheel",
        str(status_dict["U_MASK"]),
        f"θ={status_dict['U_MASKTH']:.3f} deg, x={status_dict['U_MASKX']:.3f} mm, y={status_dict['U_MASKY']:.3f} mm",
        style=style,
    )

    ## filter
    table.add_row(
        "Filter", str(status_dict["U_FILTER"]), f"{status_dict['U_FILTTH']:.0f}"
    )

    ## MBI
    if status_dict["U_MBI"] == "IN":
        style = active_style
    elif status_dict["U_MBI"] == "OUT":
        style = default_style
    else:
        style = unknown_style
    style = inactive_style  # override
    table.add_row(
        "MBI",
        str(status_dict["U_MBI"]),
        f"θ={status_dict['U_MBITH']:.3f} deg",
        style=style,
    )

    ## Pupil lens
    if status_dict["U_PUPST"].strip() == "OUT":
        style = default_style
    elif status_dict["U_PUPST"].strip() == "IN":
        style = active_style
    else:
        style = unknown_style
    style = inactive_style  # override
    table.add_row("Pupil lens", status_dict["U_PUPST"], "", style=style)

    ## Focusing lens
    style = default_style
    if status_dict["U_FCS"].lower() == "unknown":
        style = unknown_style
    table.add_row(
        "Focus",
        str(status_dict["U_FCS"]),
        f"f={status_dict['U_FCSF']:.3f} mm",
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
        f"θ={status_dict['U_BSTH']:.3f} deg",
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
        style = blue_style
    table.add_row(
        "Diff. wheel",
        f"{str(status_dict['U_DIFFL1'])} / {str(status_dict['U_DIFFL2'])}",
        f"θ={status_dict['U_DIFFTH']:.3f} deg",
        style=style,
    )

    ## Camera focus
    style = default_style
    table.add_row(
        "Cam focus",
        str(status_dict["U_CAMFCS"]),
        f"f={status_dict['U_CAMFCF']:.3f} mm",
        style=style,
    )

    ## Trigger
    if status_dict["EXTTRIG"]:
        style = default_style
    else:
        style = danger_style
    style = inactive_style  # override
    table.add_row(
        "Trigger",
        "ENABLED" if status_dict["EXTTRIG"] else "DISABLED",
        f"pw={status_dict['U_TRIGPW']} us, off={status_dict['U_FLCOFF']} us",
        style=style,
    )

    table.add_section()
    logging_cam1 = status_dict["U_VLOG1"].strip() == "ON"
    logging_cam2 = status_dict["U_VLOG2"].strip() == "ON"
    logging_pupil = status_dict["U_VLOGP"].strip() == "ON"
    styles = {
        "OFF": inactive_style,  # override
        # "OFF": default_style,
        "ON": active_style,
    }
    table.add_row(
        "CAM 1",
        "Logging" if logging_cam1 else "",
        "",
        style=styles[status_dict["U_VLOG1"]],
    )
    table.add_row(
        "CAM 2",
        "Logging" if logging_cam2 else "",
        "",
        style=styles[status_dict["U_VLOG1"]],
    )
    table.add_row(
        "Pupil Cam",
        "Logging" if logging_pupil else "",
        "",
        style=styles[status_dict["U_VLOGP"]],
    )

    style = inactive_style  # override
    table.add_row("Gen2 Status", "", "", style=style)

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
