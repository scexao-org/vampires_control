def get_dominant_filter(main_filter, diff_filter):
    # check if Halpha or SII filters are in
    if "HA" in diff_filter.upper():
        return "Halpha"
    elif "SII" in diff_filter.upper():
        return "SII"
    # otherwise use the main filter
    return main_filter


class Palette:
    red = "#721817"
    gold = "#FA9F42"
    orange = "#e85d04"
    blue = "#2B4162"
    green = "#0B6E4F"
    white = "#E0E0E2"
    gray = "#A3A3A3"


def color_to_rgb(color):
    r = int(color[1:3], 16)
    g = int(color[3:5], 16)
    b = int(color[5:7], 16)
    return r, g, b
