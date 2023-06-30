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
