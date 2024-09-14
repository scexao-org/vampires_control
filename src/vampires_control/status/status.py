from time import sleep

import click
import numpy as np
from rich.live import Live
from rich.rule import Rule
from rich.table import Table
from rich.text import Text
from swmain.redis import get_values

from vampires_control.helpers import Palette, get_dominant_filter

default_style = f"{Palette.white} on default"
unknown_style = f"{Palette.white} on {Palette.blue}"
active_style = f"{Palette.white} on {Palette.green}"
danger_style = f"{Palette.white} on {Palette.red}"
inactive_style = f"{Palette.gray} on #111111"

REDIS_KEYS = [
    "D_IMRANG",
    "D_IMRPAD",
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
    "U_FLCST",
    "U_FLCSTP",
    "U_FLCTMP",
    "U_FLDSTP",
    "U_FLDSTF",
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
    "U_TRIGEN",
    "U_TRIGJT",
    "U_TRIGOF",
    "U_TRIGPW",
    "u_VTRIG",
    "u_WTRIG",
    "U_VLOG1",
    "U_VLOG2",
    "U_VLOGP",
    "X_FIRPKO",
    "X_FIRPKP",
    "X_GRDAMP",
    "X_GRDMOD",
    "X_GRDSEP",
    "X_GRDST",
    "X_INTSPH",
    "X_NPS14",
    "X_NPS216",
    "X_POLAR",
    "X_POLARP",
    "X_PYWPKO",
    "X_PYWPKP",
    "X_SRCFFT",
    "X_SRCND1",
    "X_SRCND2",
    "X_SRCND3",
    "X_SRCEN",
    "X_SRCFLX",
    "X_SRCSEL",
    "X_VISBLK",
    "X_VPLPKO",
    "X_VPLPKT",
    "u_VOBMOD",
    "u_WOBMOD",
    "u_VDATA",
    "u_WDATA",
    "u_VDETMD",
    "u_WDETMD",
    "u_VTEMP",
    "u_WTEMP",
]


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

    status_dict = get_values(REDIS_KEYS)

    # normalize all inputs into UPPERCASE
    for k, v in status_dict.items():
        if isinstance(status_dict[k], str):
            status_dict[k] = v.strip()

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
        status = "Unknown"
        style = unknown_style

    table.add_row("LP", status, "", style=style)

    ## HWP
    style = default_style
    if status_dict["P_STGPS2"] == 56:
        status = "IN"
        style = active_style
    elif status_dict["P_STGPS2"] == 0:
        status = "OUT"
    else:
        status = "Unknown"
        style = unknown_style
    table.add_row("HWP", status, f"θ={status_dict['P_RTAGL1']:6.02f}°", style=style)

    ## Image rotator
    table.add_row(
        "Image rotator",
        status_dict["D_IMRMOD"],
        f"θ={status_dict['D_IMRANG']:6.02f}°, PA={status_dict['D_IMRPAD']:6.02f}°",
        style=default_style,
    )

    ## AO188 -> SCExAO

    ## source
    table.add_section()
    style = default_style
    if status_dict["X_SRCEN"].upper() == "ON":
        style = active_style
    info = f"ND1={status_dict['X_SRCND1'].replace(' ', '')}, ND2={status_dict['X_SRCND2'].replace(' ', '')}, ND3={status_dict['X_SRCND3'].replace(' ', '')}, Flt={status_dict['X_SRCFFT'].replace(' ', '')}, flux={status_dict['X_SRCFLX']:.01f}%"
    table.add_row("Source", status_dict["X_SRCSEL"], info, style=style)

    ## integrating sphere
    style = default_style
    if status_dict["X_INTSPH"].upper() == "IN":
        style = active_style
    table.add_row("Int Sphere", status_dict["X_INTSPH"], style=style)

    ## astrogrid
    style = default_style
    if status_dict["X_GRDST"].upper() != "OFF":
        style = active_style
    info = f"r={status_dict['X_GRDSEP']} λ/D, a={status_dict['X_GRDAMP']} um, f={status_dict['X_GRDMOD']} Hz"
    table.add_row("Astrogrid", status_dict["X_GRDST"], info, style=style)

    ## LP
    if status_dict["X_POLAR"].upper() == "OUT":
        style = default_style
    elif status_dict["X_POLAR"].upper() == "IN":
        style = active_style
    table.add_row("LP", status_dict["X_POLAR"], f"θ={status_dict['X_POLARP']:6.02f}°", style=style)
    ## QWPs
    style = active_style if status_dict["U_QWPMOD"] != "None" else default_style
    table.add_row("QWP mode", status_dict["U_QWPMOD"], "", style=style)
    table.add_row(
        "QWP 1",
        f"{status_dict['U_QWP1']:6.02f}°",
        f"θ={status_dict['U_QWP1TH']:6.02f}°",
        style=default_style,
    )
    table.add_row(
        "QWP 2",
        f"{status_dict['U_QWP2']:6.02f}°",
        f"θ={status_dict['U_QWP2TH']:6.02f}°",
        style=default_style,
    )

    ## SCExAO -> Vis
    table.add_section()

    ## PyWFS pickoff
    style = default_style
    if is_pywfs_pickoff_interfering(
        status_dict["X_PYWPKO"], status_dict["U_FILTER"], status_dict["U_DIFFL1"]
    ):
        style = danger_style

    table.add_row(
        "PyWFS Pickoff", status_dict["X_PYWPKO"], f"θ={status_dict['X_PYWPKP']:6.02f}°", style=style
    )

    ## Fieldstop
    if status_dict["U_FLDSTP"].upper() == "FIELDSTOP":
        style = default_style
    elif status_dict["U_FLDSTP"].upper() == "UNKNOWN":
        style = unknown_style
    else:
        style = active_style
    table.add_row(
        "Fieldstop",
        str(status_dict["U_FLDSTP"]),
        f"x={status_dict['U_FLDSTX']:6.03f} mm, y={status_dict['U_FLDSTY']:6.03f} mm, f={status_dict['U_FLDSTF']:6.03f} mm",
        style=style,
    )

    ## Block
    if status_dict["X_VISBLK"].upper() == "IN":
        style = danger_style
    elif status_dict["X_VISBLK"].upper() == "OUT":
        style = default_style
    else:
        style = unknown_style
    table.add_row("Vis Block", str(status_dict["X_VISBLK"]), "", style=style)

    ## First pickoff
    if status_dict["X_FIRPKO"].upper() == "IN":
        style = active_style
    elif status_dict["X_FIRPKO"].upper() == "OUT":
        style = default_style
    else:
        style = unknown_style
    table.add_row(
        "FIRST pickoff",
        status_dict["X_FIRPKO"],
        f"p={status_dict['X_FIRPKP']:5.02f} mm",
        style=style,
    )

    ## Visible Photonics pickoff
    if status_dict["X_VPLPKO"].upper() == "OPEN":
        style = default_style
    elif status_dict["X_VPLPKO"].upper() == "UNKNOWN":
        style = unknown_style
    else:
        style = active_style
    table.add_row(
        "VPL pickoff", status_dict["X_VPLPKO"], f"θ={status_dict['X_VPLPKT']:6.02f}°", style=style
    )

    ## FLC
    # check if FLC temperature is wildly out of spec (45 degC)
    if np.abs(status_dict["U_FLCTMP"] - 45) > 5:
        style = danger_style
    # is FLC stage in?
    flc_stage = status_dict["U_FLCST"].upper() == "IN"
    # is FLC trigger on?
    flc_trig = status_dict["U_FLCEN"]
    if flc_stage == flc_trig and flc_trig:
        style = active_style
    elif flc_stage != flc_trig:
        style = danger_style
    else:
        style = default_style
    temp_text = Text(f"T(AFLC)={status_dict['U_FLCTMP']:4.01f} °C", style=style)
    status = "Enabled" if flc_trig else "Disabled"
    table.add_row("AFLC", status, temp_text, style=style)

    if flc_stage:
        style = active_style
    elif status_dict["U_FLCST"].upper() == "OUT":
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
    if status_dict["U_MASK"].upper() == "OPEN":
        style = default_style
    elif status_dict["U_MASK"].upper() == "UNKNOWN":
        style = unknown_style
    else:
        style = active_style
    table.add_row(
        "Mask wheel",
        str(status_dict["U_MASK"]),
        f"θ={status_dict['U_MASKTH']:6.02f}°, x={status_dict['U_MASKX']:6.03f} mm, y={status_dict['U_MASKY']:6.03f} mm",
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
    if status_dict["U_MBI"].upper() == "DICHROICS":
        style = active_style
    elif status_dict["U_MBI"].upper() == "MIRROR":
        style = default_style
    else:
        style = unknown_style
    table.add_row(
        "MBI", str(status_dict["U_MBI"]), f"θ={status_dict['U_MBITH']:6.02f}°", style=style
    )

    ## Pupil lens
    if status_dict["U_PUPST"].upper() == "OUT":
        style = default_style
    elif status_dict["U_PUPST"].upper() == "IN":
        style = active_style
    else:
        style = unknown_style
    table.add_row("Pupil lens", status_dict["U_PUPST"], "", style=style)

    ## Focusing lens
    style = default_style
    if status_dict["U_FCS"].upper() == "UNKNOWN":
        style = unknown_style
    table.add_row(
        "Focus", str(status_dict["U_FCS"]), f"f={status_dict['U_FCSF']:5.02f} mm", style=style
    )

    ## Beamsplitter
    if status_dict["U_BS"].upper() == "OPEN":
        style = active_style
    elif status_dict["U_BS"].upper() == "UNKNOWN":
        style = unknown_style
    else:
        style = default_style
    table.add_row(
        "Beamsplitter", str(status_dict["U_BS"]), f"θ={status_dict['U_BSTH']:6.02f}°", style=style
    )

    ## Differential filter wheel
    style = default_style
    if status_dict["U_DIFFL1"].upper() == "UNKNOWN" or status_dict["U_DIFFL2"].upper() == "UNKNOWN":
        style = unknown_style
    elif any(
        status_dict[key].upper() in ("HA", "SII", "BLOCK") for key in ("U_DIFFL1", "U_DIFFL2")
    ):
        style = active_style
    table.add_row(
        "Diff wheel",
        f"{str(status_dict['U_DIFFL1'])} / {str(status_dict['U_DIFFL2'])}",
        f"θ={status_dict['U_DIFFTH']:6.02f}°",
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
    cam1_trig = status_dict["u_VTRIG"]
    cam2_trig = status_dict["u_WTRIG"]
    need_trig = cam1_trig or cam2_trig
    if status_dict["U_TRIGEN"] and need_trig:
        style = active_style
    elif status_dict["U_TRIGEN"] ^ need_trig:  # xor
        style = danger_style
    else:
        style = default_style
    table.add_row(
        "Trigger",
        "Enabled" if status_dict["U_TRIGEN"] else "Disabled",
        f"off={status_dict['U_TRIGOF']:2d} us, jt={status_dict['U_TRIGJT']:2d} us, pw={status_dict['U_TRIGPW']:2d} us",
        style=style,
    )

    table.add_section()
    logging_cam1 = status_dict["U_VLOG1"]
    logging_cam2 = status_dict["U_VLOG2"]
    logging_pupil = status_dict["U_VLOGP"]

    # cam 1
    style = default_style
    if status_dict["X_NPS14"].upper() == "OFF":
        style = danger_style
    elif logging_cam1:
        style = active_style
    cam_str = "T={:.0f}°C, {}, {}, {}"
    table.add_row(
        f"CAM 1 ({status_dict['X_NPS14']})",
        "Logging" if logging_cam1 else "",
        cam_str.format(
            status_dict["u_VTEMP"] - 273.15,  # convert to C
            status_dict["u_VOBMOD"],
            status_dict["u_VDETMD"],
            status_dict["u_VDATA"],
        ),
        style=style,
    )
    # cam 2
    style = default_style
    if status_dict["X_NPS216"].upper() == "OFF":
        style = danger_style
    elif logging_cam2:
        style = active_style
    table.add_row(
        f"CAM 2 ({status_dict['X_NPS216']})",
        "Logging" if logging_cam2 else "",
        cam_str.format(
            status_dict["u_WTEMP"] - 273.15,  # convert to C
            status_dict["u_WOBMOD"],
            status_dict["u_WDETMD"],
            status_dict["u_WDATA"],
        ),
        style=style,
    )
    # pup_cam
    style = default_style
    if logging_pupil:
        style = active_style
    table.add_row("Pupil Cam", "Logging" if logging_pupil else "", "", style=style)

    return table


PYWFS_PICKOFF_SETS = {
    "700 nm SP": ("SII", "675-50", "725-50", "750-50", "775-50", "Open"),
    "750 nm SP": ("725-50", "750-50", "775-50", "Open"),
    "800 nm SP (dflt)": ("775-50"),
    "750 nm LP": ("Halpha", "SII", "625-50", "675-50", "725-50", "750-50", "Open"),
}


def is_pywfs_pickoff_interfering(pywfs_pickoff, vamp_filter, vamp_diff_filter):
    # these pickoffs do not cut off any wavelengths of VAMPIRES
    if pywfs_pickoff in ("Open", "50/50 spt", "850 nm sp"):
        return False
    # these pickoffs always cut off VAMPIRES
    if pywfs_pickoff in ("Silver mirror", "650 nm SP", "800 nm LP", "850 nm LP"):
        return True
    # otherwise, determine based on the filters used in VAMPIRES
    curr_filter = get_dominant_filter(vamp_filter, vamp_diff_filter)
    if pywfs_pickoff in PYWFS_PICKOFF_SETS:
        allowed_filters = PYWFS_PICKOFF_SETS[pywfs_pickoff]
        return curr_filter in allowed_filters
    else:
        return True  # somethings wrong if we've gotten here


@click.command("vampires_status")
@click.option("-p", "--poll", default=0.25, type=float, help="Polling time, in seconds")
@click.option("-r", "--refresh", default=4, type=float, help="Refresh rate, in Hz")
def main(poll: float, refresh: float):
    min_poll = 1 / refresh
    if poll < min_poll:
        poll = min_poll
        click.echo(
            f"Increasing poll time ({poll:.01f} s -> {min_poll:.01f} s) to match refresh rate ({refresh} Hz)"
        )
    with Live(get_table(), refresh_per_second=refresh, screen=True, transient=True) as live:
        while True:
            sleep(poll)
            live.update(get_table())


if __name__ == "__main__":
    main()
