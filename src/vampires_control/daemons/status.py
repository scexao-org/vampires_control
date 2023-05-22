from rich.live import Live
from rich.table import Table
from rich.text import Text
from rich.rule import Rule
from time import sleep
from swmain.redis import get_values
import numpy as np

color_palette = [
    "#721817",  # red
    "#FA9F42",  # gold
    "#2B4162",  # blue
    "#0B6E4F",  # green
    "#E0E0E2",  # white
]


def get_table():
    title = Rule(Text("VAMPIRES status", style="italic"), style="bold #2B4162")
    table = Table(title=title, style="bold #2B4162")

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
    style = None
    if status_dict["P_STGPS1"] == 0:
        status = "OUT"
        style = "#721817 on default"
    elif status_dict["P_STGPS1"] == 56:
        status = "WiregGrid(TIR)"
        style = "#E0E0E2 on #0B6E4F"
    elif status_dict["P_STGPS1"] == 90:
        status = "WiregGrid(NIR)"
        style = "#E0E0E2 on #0B6E4F"
    table.add_row("LP", status, f"θ= deg", style=style)

    ## HWP
    if status_dict["P_STGPS2"] > 0:
        style = "#E0E0E2 on #0B6E4F"
    else:
        style = "#721817 on default"
    table.add_row("HWP", "OUT", f"θ={status_dict['P_RTAGL1']:.3f} deg", style=style)

    ## Image rotator
    table.add_row(
        "Image rotator", status_dict["D_IMRMOD"], f"θ={status_dict['D_IMRANG']:.3f} deg"
    )

    ## AO188 -> SCExAO
    table.add_section()

    ## LP
    if status_dict["X_POLAR"].strip() == "OUT":
        style = "#721817 on default"
    elif status_dict["X_POLAR"].strip() == "IN":
        style = "#E0E0E2 on #0B6E4F"
    table.add_row(
        "LP",
        status_dict["X_POLAR"],
        f"θ={status_dict['X_POLARP']:.3f} deg",
        style=style,
    )
    ## QWP
    table.add_row("QWP mode", str(status_dict["U_QWPMOD"]), "")
    table.add_row(
        "QWP 1",
        f"θ={status_dict['U_QWP1']:.3f} deg",
        f"θ={status_dict['U_QWP1TH']:.3f} deg",
    )
    table.add_row(
        "QWP 2",
        f"θ={status_dict['U_QWP2']:.3f} deg",
        f"θ={status_dict['U_QWP2TH']:.3f} deg",
    )

    ## SCExAO -> Vis
    table.add_section()

    ## Fieldstop
    table.add_row(
        "Fieldstop",
        str(status_dict["U_FLDSTP"]),
        f"x={status_dict['U_FLDSTX']:.3f} mm, y={status_dict['U_FLDSTY']:.3f} mm",
    )

    ## First pickoff
    style = None
    if status_dict["X_FIRPKO"].strip() == "IN":
        style = "#E0E0E2 on #721817"
    else:
        style = "#721817 on default"
    table.add_row(
        "FIRST pickoff",
        status_dict["X_FIRPKO"],
        f"p={status_dict['X_FIRPKP']:.3f} mm",
        style=style,
    )

    ## FLC
    if np.abs(status_dict["U_FLCTMP"] - 45) > 1:
        temp_style = f"#E0E0E2 on #721817"
    else:
        temp_style = None
    temp_text = Text(f"T={status_dict['U_FLCTMP']:.3f} deg C", style=temp_style)
    table.add_row("FLC", str(status_dict["U_FLCEN"]), temp_text)
    table.add_row(
        "FLC Stage", str(status_dict["U_FLCST"]), f"p={status_dict['U_FLCSTP']:.3f} mm"
    )

    ## Pupil mask
    table.add_row(
        "Mask wheel",
        str(status_dict["U_MASK"]),
        f"θ={status_dict['U_MASKTH']:.3f} deg, x={status_dict['U_MASKX']:.3f} mm, y={status_dict['U_MASKY']:.3f} mm",
    )

    ## filter
    table.add_row(
        "Filter", str(status_dict["U_FILTER"]), f"{status_dict['U_FILTTH']:.0f}"
    )

    ## MBI
    table.add_row(
        "MBI", str(status_dict["U_MBI"]), f"θ={status_dict['U_MBITH']:.3f} deg"
    )

    ## Pupil lens
    if status_dict["U_PUPST"].strip() == "OUT":
        style = "#721817 on default"
    elif status_dict["U_PUPST"].strip() == "IN":
        style = "#E0E0E2 on #0B6E4F"
    style = "#721817 on default"
    table.add_row("Pupil lens", status_dict["U_PUPST"], "", style=style)

    ## Focusing lens
    table.add_row(
        "Focus", str(status_dict["U_FCS"]), f"f={status_dict['U_FCSF']:.3f} mm"
    )

    ## Beamsplitter
    table.add_row(
        "Beamsplitter", str(status_dict["U_BS"]), f"θ={status_dict['U_BSTH']:.3f} deg"
    )

    ## Differential filter wheel
    table.add_row(
        "Diff. wheel",
        f"{str(status_dict['U_DIFFL1'])} / {str(status_dict['U_DIFFL2'])}",
        f"θ={status_dict['U_DIFFTH']:.3f} deg",
    )

    ## Camera focus
    table.add_row(
        "Cam focus", str(status_dict["U_CAMFCS"]), f"f={status_dict['U_CAMFCF']:.3f} mm"
    )

    ## Trigger
    if status_dict["EXTTRIG"]:
        style = "#0B6E4F on default"
    else:
        style = "#721817 on default"
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
    styles = (
        "#721817 on default",
        "#E0E0E2 on #0B6E4F",
    )
    table.add_row(
        "CAM 1", "Logging" if logging_cam1 else "", "", style=styles[int(logging_cam1)]
    )
    table.add_row(
        "CAM 2", "Logging" if logging_cam2 else "", "", style=styles[int(logging_cam2)]
    )
    table.add_row(
        "Pupil Cam",
        "Logging" if logging_pupil else "",
        "",
        style=styles[int(logging_pupil)],
    )
    table.add_row("Gen2 Status", "", "", style=styles[0])

    return table


def main():
    with Live(get_table(), refresh_per_second=1) as live:
        while True:
            sleep(0.1)
            live.update(get_table())


if __name__ == "__main__":
    main()
