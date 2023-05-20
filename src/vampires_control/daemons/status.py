from rich.live import Live
from rich.table import Table
from rich.console import Console
from time import sleep
from swmain.redis import get_values


def get_table():
    table = Table(title="VAMPIRES status")

    table.add_column("Name")
    table.add_column("Status")
    table.add_column("Position")

    status_dict = get_values(
        [
            "U_QWPMOD",
            "U_QWP1",
            "U_QWP1TH",
            "U_QWP2",
            "U_QWP2TH",
            "U_FLDSTP",
            "U_FLDSTX",
            "U_FLDSTY",
            "U_FLCEN",
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
        ]
    )
    ## QWP
    table.add_row("QWP tracking", str(status_dict["U_QWPMOD"]), "")
    table.add_row("QWP 1", str(status_dict["U_QWP1"]), str(status_dict["U_QWP1TH"]))
    table.add_row("QWP 2", str(status_dict["U_QWP2"]), str(status_dict["U_QWP2TH"]))

    ## Fieldstop
    table.add_row(
        "Fieldstop",
        str(status_dict["U_FLDSTP"]),
        ", ".join((str(status_dict["U_FLDSTX"]), str(status_dict["U_FLDSTY"]))),
    )

    ## FLC
    table.add_row("FLC", str(status_dict["U_FLCEN"]), "")
    table.add_row(
        "FLC Stage", str(status_dict["U_FLCST"]), str(status_dict["U_FLCSTP"])
    )

    ## Pupil mask
    table.add_row(
        "Pupil wheel",
        str(status_dict["U_MASK"]),
        ", ".join(
            (
                str(status_dict["U_MASKTH"]),
                str(status_dict["U_MASKX"]),
                str(status_dict["U_MASKY"]),
            )
        ),
    )

    ## filter
    table.add_row("Filter", str(status_dict["U_FILTER"]), str(status_dict["U_FILTTH"]))

    ## MBI
    table.add_row("MBI", str(status_dict["U_MBI"]), str(status_dict["U_MBITH"]))

    ## Pupil lens
    table.add_row("Pupil lens", str(status_dict["U_PUPST"]), "")

    ## Focusing lens
    table.add_row("Focus", str(status_dict["U_FCS"]), str(status_dict["U_FCSF"]))

    ## Beamsplitter
    table.add_row("Beamsplitter", str(status_dict["U_BS"]), str(status_dict["U_BSTH"]))

    ## Differential filter wheel
    table.add_row(
        "Diff. wheel",
        f"{str(status_dict['U_DIFFL1'])} / {str(status_dict['U_DIFFL2'])}",
        str(status_dict["U_DIFFTH"]),
    )

    ## Camera focus
    table.add_row(
        "Cam focus", str(status_dict["U_CAMFCS"]), str(status_dict["U_CAMFCF"])
    )
    return table


def main():
    with Live(get_table(), refresh_per_second=1) as live:
        while True:
            sleep(0.1)


if __name__ == "__main__":
    main()
