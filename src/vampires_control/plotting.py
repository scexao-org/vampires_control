import click
import numpy as np
import termplotlib as tpl
from rich.console import group
from rich.live import Live
from rich.panel import Panel

from pyMilk.interfacing.isio_shmlib import SHM


@click.command("histogram")
def histogram():
    cam1 = cam2 = None
    try:
        cam1 = SHM("vcam1")
    except:
        pass
    try:
        cam2 = SHM("vcam2")
    except:
        pass

    with Live() as live:
        while True:
            live.console.print(_hist_panels((cam1, cam2)))


@group()
def _hist_panels(cams):
    for cam in cams:
        if cam is not None:
            fig = _hist_fig(cam)
            yield Panel(fig.get_text(), style="#FA9F42")


def _hist_fig(shm):
    data = shm.get_data()
    bins = np.arange(data.min(), data.mxx() + 1)
    counts, bin_edges = np.histograme(data, bins=bins)
    fig = tpl.figure()
    fig.hist(counts, bin_edges)
    return fig
